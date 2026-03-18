"""Acceso centralizado a secrets — st.secrets (Streamlit Cloud) con fallback a settings.yaml + env vars (local)."""

import os

import yaml
import streamlit as st
from google.oauth2.service_account import Credentials


def _load_settings_yaml() -> dict:
    """Carga settings.yaml como fallback para desarrollo local."""
    try:
        with open("config/settings.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}


# ─── Web Password ─────────────────────────────────────────────

def get_web_password() -> str:
    """Contraseña de la web app."""
    try:
        return st.secrets["web"]["password"]
    except (KeyError, FileNotFoundError):
        settings = _load_settings_yaml()
        return settings.get("web", {}).get("password", "veta2026")


# ─── OpenRouter ───────────────────────────────────────────────

def get_openrouter_key() -> str | None:
    """API key de OpenRouter."""
    try:
        return st.secrets["chat"]["openrouter_api_key"]
    except (KeyError, FileNotFoundError):
        pass
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key
    settings = _load_settings_yaml()
    key = settings.get("chat", {}).get("openrouter_api_key", "")
    if key and not key.startswith("${"):
        return key
    return None


# ─── Anthropic ────────────────────────────────────────────────

def get_anthropic_key() -> str | None:
    """API key de Anthropic/Claude."""
    try:
        return st.secrets["anthropic"]["api_key"]
    except (KeyError, FileNotFoundError):
        pass
    return os.environ.get("ANTHROPIC_API_KEY")


# ─── Google Credentials (Drive + Sheets) ─────────────────────

def get_google_credentials() -> Credentials:
    """Credentials de Google (service account) para Drive y Sheets.

    En Streamlit Cloud: lee de st.secrets["google_credentials"].
    Local: lee del archivo JSON configurado en settings.yaml.
    """
    scopes = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/documents",
        "https://spreadsheets.google.com/feeds",
    ]

    # Streamlit Cloud
    try:
        creds_dict = dict(st.secrets["google_credentials"])
        return Credentials.from_service_account_info(creds_dict, scopes=scopes)
    except (KeyError, FileNotFoundError):
        pass

    # Local: archivo JSON
    settings = _load_settings_yaml()
    creds_file = settings.get("google_sheets", {}).get("credentials_file", "")
    if creds_file and os.path.exists(creds_file):
        return Credentials.from_service_account_file(creds_file, scopes=scopes)

    raise FileNotFoundError("No se encontraron credenciales de Google en st.secrets ni en archivos locales")


# ─── Google Ads ───────────────────────────────────────────────

def get_google_ads_credentials() -> dict:
    """Credenciales para Google Ads API.

    Retorna dict con: credentials (Credentials obj), developer_token, login_customer_id.
    """
    scopes = ["https://www.googleapis.com/auth/adwords"]

    # Credentials de service account
    try:
        creds_dict = dict(st.secrets["google_credentials"])
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    except (KeyError, FileNotFoundError):
        settings = _load_settings_yaml()
        creds_file = settings.get("google_sheets", {}).get("credentials_file", "")
        if creds_file and os.path.exists(creds_file):
            credentials = Credentials.from_service_account_file(creds_file, scopes=scopes)
        else:
            raise FileNotFoundError("No se encontraron credenciales de Google")

    # Developer token
    try:
        developer_token = st.secrets["google_ads"]["developer_token"]
    except (KeyError, FileNotFoundError):
        developer_token = os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN")
        if not developer_token:
            settings = _load_settings_yaml()
            developer_token = settings.get("google_ads", {}).get("developer_token", "")
            if developer_token.startswith("${"):
                developer_token = None

    # Login customer ID (MCC)
    try:
        login_customer_id = st.secrets["google_ads"]["login_customer_id"]
    except (KeyError, FileNotFoundError):
        settings = _load_settings_yaml()
        login_customer_id = settings.get("google_ads", {}).get("login_customer_id", "5971963548")

    return {
        "credentials": credentials,
        "developer_token": developer_token,
        "login_customer_id": str(login_customer_id),
    }


# ─── Meta Ads ─────────────────────────────────────────────────

def get_meta_access_token() -> str | None:
    """Access token de Meta Marketing API."""
    try:
        return st.secrets["meta_ads"]["access_token"]
    except (KeyError, FileNotFoundError):
        pass
    token = os.environ.get("META_ACCESS_TOKEN")
    if token:
        return token
    settings = _load_settings_yaml()
    token = settings.get("meta_ads", {}).get("access_token", "")
    if token and not token.startswith("${"):
        return token
    # Fallback: leer del .env del meta-ads-cli
    env_path = os.path.join("meta-ads-cli", ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith("META_ACCESS_TOKEN="):
                    return line.split("=", 1)[1].strip().strip('"')
    return None


def get_meta_api_version() -> str:
    """Versión de la Meta Marketing API."""
    try:
        return st.secrets["meta_ads"]["api_version"]
    except (KeyError, FileNotFoundError):
        pass
    settings = _load_settings_yaml()
    return settings.get("meta_ads", {}).get("api_version", "v21.0")
