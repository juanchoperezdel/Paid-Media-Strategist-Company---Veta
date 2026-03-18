"""Cliente para lectura/escritura de Google Sheets."""

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import yaml
import os

from src.utils.logger import get_logger

logger = get_logger("veta.sheets")


class SheetsClient:
    """Maneja la conexión y operaciones con Google Sheets."""

    def __init__(self, credentials_file: str):
        self.credentials_file = credentials_file
        self._client = None

    @property
    def client(self) -> gspread.Client:
        if self._client is None:
            scopes = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive",
            ]
            creds = Credentials.from_service_account_file(
                self.credentials_file, scopes=scopes
            )
            self._client = gspread.authorize(creds)
            logger.info("Conectado a Google Sheets")
        return self._client

    def read_tab(self, sheet_id: str, tab_name: str) -> pd.DataFrame:
        """Lee una pestaña de un spreadsheet y retorna un DataFrame."""
        try:
            spreadsheet = self.client.open_by_key(sheet_id)
            worksheet = spreadsheet.worksheet(tab_name)
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
            logger.info(f"Leídas {len(df)} filas de '{tab_name}' en sheet {sheet_id[:8]}...")
            return df
        except gspread.exceptions.SpreadsheetNotFound:
            logger.error(f"Spreadsheet no encontrado: {sheet_id}")
            raise
        except gspread.exceptions.WorksheetNotFound:
            logger.error(f"Tab no encontrada: '{tab_name}' en sheet {sheet_id[:8]}...")
            raise

    def read_all_tabs(self, sheet_id: str, tabs: dict[str, str]) -> dict[str, pd.DataFrame]:
        """Lee múltiples tabs de un spreadsheet.

        Args:
            sheet_id: ID del spreadsheet
            tabs: dict de {nombre_lógico: nombre_tab_real}

        Returns:
            dict de {nombre_lógico: DataFrame}
        """
        results = {}
        for key, tab_name in tabs.items():
            try:
                results[key] = self.read_tab(sheet_id, tab_name)
            except Exception as e:
                logger.warning(f"No se pudo leer tab '{tab_name}': {e}")
                results[key] = pd.DataFrame()
        return results

    def write_tab(self, sheet_id: str, tab_name: str, df: pd.DataFrame, clear_first: bool = True):
        """Escribe un DataFrame a una pestaña de un spreadsheet."""
        try:
            spreadsheet = self.client.open_by_key(sheet_id)
            try:
                worksheet = spreadsheet.worksheet(tab_name)
            except gspread.exceptions.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(
                    title=tab_name, rows=len(df) + 1, cols=len(df.columns)
                )

            if clear_first:
                worksheet.clear()

            headers = df.columns.tolist()
            values = df.fillna("").values.tolist()
            worksheet.update([headers] + values)
            logger.info(f"Escritas {len(df)} filas en '{tab_name}'")
        except Exception as e:
            logger.error(f"Error escribiendo a '{tab_name}': {e}")
            raise

    def load_client_data(self, client_config: dict) -> dict[str, dict[str, pd.DataFrame]]:
        """Carga toda la data de un cliente desde sus sheets configurados.

        Retorna estructura:
        {
            "google_ads": {"campaigns": df, "ads": df, ...},
            "meta_ads": {"campaigns": df, "ads": df, ...},
            "ga4": {"traffic": df, "conversions": df, ...},
        }
        """
        all_data = {}
        sheets_config = client_config.get("sheets", {})

        for platform, config in sheets_config.items():
            sheet_id = config.get("sheet_id", "")
            tabs = config.get("tabs", {})

            if not sheet_id or sheet_id.startswith("TU_"):
                logger.warning(f"Sheet ID no configurado para {platform}, saltando...")
                continue

            logger.info(f"Cargando data de {platform}...")
            all_data[platform] = self.read_all_tabs(sheet_id, tabs)

        return all_data
