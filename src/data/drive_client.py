"""Cliente para Google Drive — sube reportes como Google Docs y maneja carpetas por cliente."""

import io
import os
from datetime import datetime

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from src.utils.logger import get_logger

logger = get_logger("veta.drive")

# Scopes necesarios para Drive + Docs
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
]


class DriveClient:
    """Maneja operaciones con Google Drive: carpetas, subida de reportes, lectura de data."""

    def __init__(self, credentials_file: str | None = None, root_folder_id: str | None = None, credentials=None):
        """
        Args:
            credentials_file: Ruta al JSON de service account (local)
            root_folder_id: ID de la carpeta raíz "Veta" en Drive (opcional, se crea si no existe)
            credentials: Objeto Credentials ya construido (para Streamlit Cloud)
        """
        self.credentials_file = credentials_file
        self.root_folder_id = root_folder_id
        self._credentials = credentials
        self._drive_service = None
        self._docs_service = None

    def _get_creds(self):
        """Obtiene credentials: usa objeto preconstruido o lee del archivo."""
        if self._credentials:
            return self._credentials
        return Credentials.from_service_account_file(
            self.credentials_file, scopes=SCOPES
        )

    @property
    def drive(self):
        if self._drive_service is None:
            creds = self._get_creds()
            self._drive_service = build("drive", "v3", credentials=creds)
            logger.info("Conectado a Google Drive")
        return self._drive_service

    @property
    def docs(self):
        if self._docs_service is None:
            creds = self._get_creds()
            self._docs_service = build("docs", "v1", credentials=creds)
            logger.info("Conectado a Google Docs")
        return self._docs_service

    # ─── Carpetas ───────────────────────────────────────────────

    def _find_folder(self, name: str, parent_id: str | None = None) -> str | None:
        """Busca una carpeta por nombre dentro de un parent. Retorna su ID o None."""
        query = f"name = '{name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        if parent_id:
            query += f" and '{parent_id}' in parents"

        results = self.drive.files().list(
            q=query, spaces="drive", fields="files(id, name)", pageSize=1
        ).execute()

        files = results.get("files", [])
        return files[0]["id"] if files else None

    def _create_folder(self, name: str, parent_id: str | None = None) -> str:
        """Crea una carpeta en Drive. Retorna su ID."""
        metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_id:
            metadata["parents"] = [parent_id]

        folder = self.drive.files().create(body=metadata, fields="id").execute()
        folder_id = folder["id"]
        logger.info(f"Carpeta creada: '{name}' (ID: {folder_id})")
        return folder_id

    def _get_or_create_folder(self, name: str, parent_id: str | None = None) -> str:
        """Busca una carpeta, si no existe la crea."""
        existing = self._find_folder(name, parent_id)
        if existing:
            return existing
        return self._create_folder(name, parent_id)

    def get_root_folder(self) -> str:
        """Obtiene o crea la carpeta raíz 'Veta' en Drive."""
        if self.root_folder_id:
            return self.root_folder_id
        self.root_folder_id = self._get_or_create_folder("Veta")
        return self.root_folder_id

    def create_client_folders(self, client_name: str) -> dict[str, str]:
        """Crea la estructura de carpetas para un cliente:
        Veta/
          {client_name}/
            data/
            reportes/

        Retorna dict con los folder IDs.
        """
        root_id = self.get_root_folder()
        client_id = self._get_or_create_folder(client_name, root_id)
        data_id = self._get_or_create_folder("data", client_id)
        reportes_id = self._get_or_create_folder("reportes", client_id)

        folders = {
            "client": client_id,
            "data": data_id,
            "reportes": reportes_id,
        }
        logger.info(f"Estructura de carpetas lista para '{client_name}'")
        return folders

    # ─── Subida de reportes ─────────────────────────────────────

    def upload_report_as_doc(
        self, client_name: str, content: str, title: str | None = None
    ) -> str:
        """Sube un reporte markdown como Google Doc en la carpeta del cliente.

        Args:
            client_name: Nombre del cliente
            content: Contenido del reporte en markdown
            title: Título del doc (default: auto-generado con fecha)

        Returns:
            URL del Google Doc creado
        """
        folders = self.create_client_folders(client_name)

        if not title:
            date_str = datetime.now().strftime("%Y-%m-%d")
            title = f"Veta Report — {client_name} — {date_str}"

        # Subir como archivo de texto que Google convierte a Doc
        media = MediaIoBaseUpload(
            io.BytesIO(content.encode("utf-8")),
            mimetype="text/plain",
            resumable=True,
        )

        file_metadata = {
            "name": title,
            "parents": [folders["reportes"]],
            "mimeType": "application/vnd.google-apps.document",
        }

        doc = self.drive.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, webViewLink",
        ).execute()

        doc_url = doc.get("webViewLink", f"https://docs.google.com/document/d/{doc['id']}")
        logger.info(f"Reporte subido como Google Doc: {doc_url}")
        return doc_url

    # ─── Data cruda (CSV) ──────────────────────────────────────

    def upload_data_csv(
        self, client_name: str, csv_content: str, filename: str
    ) -> str:
        """Sube un CSV con data cruda a la carpeta data/ del cliente.

        Returns:
            ID del archivo subido
        """
        folders = self.create_client_folders(client_name)

        media = MediaIoBaseUpload(
            io.BytesIO(csv_content.encode("utf-8")),
            mimetype="text/csv",
            resumable=True,
        )

        file_metadata = {
            "name": filename,
            "parents": [folders["data"]],
        }

        # Buscar si ya existe para actualizar
        existing = self._find_file(filename, folders["data"])
        if existing:
            updated = self.drive.files().update(
                fileId=existing,
                media_body=media,
            ).execute()
            logger.info(f"CSV actualizado: {filename}")
            return existing
        else:
            created = self.drive.files().create(
                body=file_metadata,
                media_body=media,
                fields="id",
            ).execute()
            logger.info(f"CSV subido: {filename}")
            return created["id"]

    def download_data_csv(self, client_name: str, filename: str) -> str | None:
        """Descarga un CSV de la carpeta data/ del cliente.

        Returns:
            Contenido del CSV como string, o None si no existe
        """
        folders = self.create_client_folders(client_name)
        file_id = self._find_file(filename, folders["data"])

        if not file_id:
            logger.warning(f"Archivo no encontrado: {filename}")
            return None

        content = self.drive.files().get_media(fileId=file_id).execute()
        return content.decode("utf-8")

    def _find_file(self, name: str, parent_id: str) -> str | None:
        """Busca un archivo por nombre en una carpeta."""
        query = (
            f"name = '{name}' and '{parent_id}' in parents "
            f"and mimeType != 'application/vnd.google-apps.folder' and trashed = false"
        )
        results = self.drive.files().list(
            q=query, spaces="drive", fields="files(id)", pageSize=1
        ).execute()
        files = results.get("files", [])
        return files[0]["id"] if files else None

    # ─── Listado de reportes ────────────────────────────────────

    def list_reports(self, client_name: str) -> list[dict]:
        """Lista todos los reportes de un cliente.

        Returns:
            Lista de dicts con {id, name, url, created_time}
        """
        folders = self.create_client_folders(client_name)

        results = self.drive.files().list(
            q=f"'{folders['reportes']}' in parents and trashed = false",
            spaces="drive",
            fields="files(id, name, webViewLink, createdTime)",
            orderBy="createdTime desc",
            pageSize=50,
        ).execute()

        reports = []
        for f in results.get("files", []):
            reports.append({
                "id": f["id"],
                "name": f["name"],
                "url": f.get("webViewLink", ""),
                "created_time": f.get("createdTime", ""),
            })

        logger.info(f"Encontrados {len(reports)} reportes para '{client_name}'")
        return reports

    def list_data_files(self, client_name: str) -> list[dict]:
        """Lista archivos de data cruda de un cliente."""
        folders = self.create_client_folders(client_name)

        results = self.drive.files().list(
            q=f"'{folders['data']}' in parents and trashed = false",
            spaces="drive",
            fields="files(id, name, createdTime, modifiedTime)",
            orderBy="modifiedTime desc",
            pageSize=100,
        ).execute()

        return [
            {
                "id": f["id"],
                "name": f["name"],
                "created_time": f.get("createdTime", ""),
                "modified_time": f.get("modifiedTime", ""),
            }
            for f in results.get("files", [])
        ]
