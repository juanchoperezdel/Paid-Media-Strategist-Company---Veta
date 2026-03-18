"""Veta Strategist AI — Cron Semanal.

Ejecuta el ciclo completo para todos los clientes activos:
1. Baja data fresca de Google Ads + Meta Ads
2. Guarda data cruda en Google Drive
3. Corre análisis completo con todos los agentes
4. Sube reporte como Google Doc en Drive

Uso:
    python cron_weekly.py                    # Todos los clientes
    python cron_weekly.py --client andesmar  # Un cliente específico
    python cron_weekly.py --dry-run          # Solo baja data, no corre análisis
"""

import argparse
import os
import sys
import yaml
from datetime import datetime

from src.data.drive_client import DriveClient
from src.data.data_fetcher import DataFetcher
from src.orchestrator import VetaStrategist
from src.reports.markdown_report import MarkdownReportGenerator
from src.utils.logger import setup_logger, get_logger

logger = get_logger("veta.cron")


def load_settings(path: str = "config/settings.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_active_clients() -> list[dict]:
    """Retorna lista de clientes activos con su config."""
    clients = []
    clients_dir = "config/clients"

    if not os.path.exists(clients_dir):
        logger.error(f"Directorio de clientes no encontrado: {clients_dir}")
        return clients

    for filename in os.listdir(clients_dir):
        if not filename.endswith(".yaml") or filename.startswith("ejemplo"):
            continue

        filepath = os.path.join(clients_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if config and config.get("active", False):
            config["_config_path"] = filepath
            clients.append(config)

    return clients


def process_client(
    client_config: dict,
    drive: DriveClient,
    fetcher: DataFetcher,
    strategist: VetaStrategist,
    dry_run: bool = False,
):
    """Procesa un cliente: baja data → análisis → reporte en Drive."""
    client_name = client_config.get("client_name", "Unknown")
    config_path = client_config["_config_path"]

    logger.info(f"=== Procesando: {client_name} ===")

    # Paso 1: Bajar data fresca
    logger.info(f"[{client_name}] Bajando data de plataformas...")
    try:
        data = fetcher.fetch_all_client_data(client_config)

        if data:
            # Guardar localmente
            fetcher.save_local(client_name, data)
            logger.info(f"[{client_name}] Data guardada localmente")

            # Guardar en Drive
            try:
                fetcher.save_to_drive(drive, client_name, data)
                logger.info(f"[{client_name}] Data guardada en Drive")
            except Exception as e:
                logger.warning(f"[{client_name}] No se pudo subir a Drive: {e}")

            # Guardar en SQLite y preparar lifecycle data para el pipeline
            meta_daily = data.get("meta_ads", {}).get("ad_daily")
            meta_metadata = data.get("meta_ads", {}).get("ad_metadata")
            if meta_daily is not None and not meta_daily.empty:
                try:
                    from src.data.sqlite_store import SQLiteStore
                    store = SQLiteStore(client_name)
                    store.save_ad_daily(meta_daily)
                    if meta_metadata is not None and not meta_metadata.empty:
                        store.save_ad_metadata(meta_metadata)
                    logger.info(f"[{client_name}] Data guardada en SQLite ({store.stats()['ad_daily_rows']} filas)")
                    store.cleanup_old_data(months=12)

                    # Agregar lifecycle data al dict para que el orchestrator la use
                    data["meta_ads_lifecycle"] = {
                        "ad_daily": meta_daily,
                        "ad_metadata": meta_metadata,
                    }
                except Exception as e:
                    logger.warning(f"[{client_name}] SQLite/lifecycle error: {e}")

            # Resumen de lo bajado
            for platform, datasets in data.items():
                for name, df in datasets.items():
                    if hasattr(df, "empty") and not df.empty:
                        logger.info(f"  {platform}/{name}: {len(df)} filas")
        else:
            logger.warning(f"[{client_name}] No se pudo bajar data")

    except Exception as e:
        logger.error(f"[{client_name}] Error bajando data: {e}")

    if dry_run:
        logger.info(f"[{client_name}] Dry run — saltando análisis")
        return

    # Paso 2: Correr análisis
    logger.info(f"[{client_name}] Corriendo análisis...")
    try:
        result = strategist.run_analysis(config_path, preloaded_data=data if data else None)

        if "error" in result:
            logger.error(f"[{client_name}] Error en análisis: {result['error']}")
            return

        # Paso 3: Subir reporte a Drive
        logger.info(f"[{client_name}] Subiendo reporte a Drive...")
        gen = MarkdownReportGenerator()
        temp_path = f"output/temp_{client_name}.md"
        md_content = gen.generate(result, temp_path)

        date_str = datetime.now().strftime("%Y-%m-%d")
        title = f"Reporte Semanal — {client_name} — {date_str}"
        doc_url = drive.upload_report_as_doc(client_name, md_content, title)

        logger.info(f"[{client_name}] Reporte disponible: {doc_url}")

        # Limpiar temp
        if os.path.exists(temp_path):
            os.remove(temp_path)

    except Exception as e:
        logger.error(f"[{client_name}] Error en análisis/reporte: {e}")


def main():
    parser = argparse.ArgumentParser(description="Veta — Cron Semanal")
    parser.add_argument("--client", type=str, help="Nombre del cliente (sin .yaml)")
    parser.add_argument("--dry-run", action="store_true", help="Solo bajar data, no analizar")
    parser.add_argument("--config", type=str, default="config/settings.yaml")
    args = parser.parse_args()

    # Setup
    setup_logger("veta", "output/veta_cron.log")
    logger.info("=== Veta Cron Semanal Iniciando ===")
    logger.info(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    settings = load_settings(args.config)

    # Inicializar servicios
    drive = DriveClient(
        credentials_file=settings["google_sheets"]["credentials_file"],
        root_folder_id=settings.get("drive", {}).get("root_folder_id"),
    )
    fetcher = DataFetcher()
    strategist = VetaStrategist(args.config)

    # Obtener clientes
    if args.client:
        config_path = os.path.join("config", "clients", f"{args.client}.yaml")
        if not os.path.exists(config_path):
            logger.error(f"Config no encontrada: {config_path}")
            sys.exit(1)
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        config["_config_path"] = config_path
        clients = [config]
    else:
        clients = get_active_clients()

    if not clients:
        logger.warning("No hay clientes activos para procesar")
        return

    logger.info(f"Clientes a procesar: {len(clients)}")

    # Procesar cada cliente
    success = 0
    errors = 0
    for client_config in clients:
        try:
            process_client(client_config, drive, fetcher, strategist, args.dry_run)
            success += 1
        except Exception as e:
            logger.error(f"Error fatal con {client_config.get('client_name')}: {e}")
            errors += 1

    logger.info(f"=== Cron completado: {success} OK, {errors} errores ===")


if __name__ == "__main__":
    main()
