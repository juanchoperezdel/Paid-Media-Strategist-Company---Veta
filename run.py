"""Veta Strategist AI — Entry Point.

Uso:
    python run.py                           # Análisis completo de todos los clientes
    python run.py --client ejemplo_cliente  # Análisis de un cliente específico
    python run.py --agents risk ads         # Solo correr agentes específicos
    python run.py --schedule                # Modo scheduler (ejecución recurrente)
"""

import argparse
import os
import sys
import time
import schedule

from src.orchestrator import VetaStrategist
from src.utils.logger import setup_logger


def run_single(strategist: VetaStrategist, client: str | None, agents: list[str] | None):
    """Ejecuta un análisis único."""
    if client:
        config_path = os.path.join("config", "clients", f"{client}.yaml")
        if not os.path.exists(config_path):
            print(f"Error: Config file not found: {config_path}")
            sys.exit(1)
        strategist.run_analysis(config_path, agents_to_run=agents)
    else:
        strategist.run_all_clients(agents_to_run=agents)


def run_scheduled(strategist: VetaStrategist, settings: dict):
    """Ejecuta el scheduler para análisis recurrentes."""
    logger = setup_logger("veta.scheduler", settings.get("logging", {}).get("file"))
    schedule_config = settings.get("schedule", {})

    # Risk detection — diario
    risk_hours = schedule_config.get("risk_detection", 24)
    schedule.every(risk_hours).hours.do(
        strategist.run_all_clients, agents_to_run=["risk"]
    )
    logger.info(f"Risk detection scheduled every {risk_hours}h")

    # Ads detector — cada 3 días
    ads_hours = schedule_config.get("ads_detector", 72)
    schedule.every(ads_hours).hours.do(
        strategist.run_all_clients, agents_to_run=["ads"]
    )
    logger.info(f"Ads detector scheduled every {ads_hours}h")

    # Full report — semanal
    full_hours = schedule_config.get("full_report", 168)
    schedule.every(full_hours).hours.do(strategist.run_all_clients)
    logger.info(f"Full report scheduled every {full_hours}h")

    logger.info("Scheduler started. Press Ctrl+C to stop.")

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped.")


def main():
    parser = argparse.ArgumentParser(description="Veta Strategist AI — Paid Media Analysis")
    parser.add_argument("--client", type=str, help="Client config name (without .yaml)")
    parser.add_argument("--agents", nargs="+", help="Specific agents to run",
                        choices=["historical", "ads", "risk", "creative", "data_audit", "tasks"])
    parser.add_argument("--schedule", action="store_true", help="Run in scheduler mode")
    parser.add_argument("--config", type=str, default="config/settings.yaml",
                        help="Path to settings file")

    args = parser.parse_args()

    logger = setup_logger("veta_strategist", "output/veta_strategist.log")
    logger.info("=== Veta Strategist AI Starting ===")

    strategist = VetaStrategist(args.config)

    if args.schedule:
        run_scheduled(strategist, strategist.settings)
    else:
        run_single(strategist, args.client, args.agents)

    logger.info("=== Veta Strategist AI Finished ===")


if __name__ == "__main__":
    main()
