"""Data Fetcher — baja data de Google Ads y Meta Ads, la estructura en DataFrames.

Usa llamadas directas a las APIs (sin subprocess):
1. Google Ads: via google-ads Python SDK
2. Meta Ads: via HTTP requests a la Marketing API
"""

import json
import os
from datetime import datetime, timedelta

import pandas as pd
import requests

from src.utils.logger import get_logger

logger = get_logger("veta.data_fetcher")


class DataFetcher:
    """Baja data de las plataformas de ads y la estructura en DataFrames."""

    def __init__(self, google_ads_customer_id: str | None = None):
        self.google_ads_customer_id = google_ads_customer_id

    # ─── Google Ads ─────────────────────────────────────────────

    def fetch_google_ads_campaigns(
        self, customer_id: str, date_from: str | None = None, date_to: str | None = None
    ) -> pd.DataFrame:
        """Baja campañas de Google Ads con métricas."""
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not date_to:
            date_to = datetime.now().strftime("%Y-%m-%d")

        query = (
            "SELECT campaign.id, campaign.name, campaign.status, "
            "campaign.advertising_channel_type, campaign.bidding_strategy_type, "
            "metrics.impressions, metrics.clicks, metrics.cost_micros, "
            "metrics.conversions, metrics.conversions_value, "
            "metrics.ctr, metrics.average_cpc, metrics.cost_per_conversion "
            f"FROM campaign "
            f"WHERE segments.date BETWEEN '{date_from}' AND '{date_to}' "
            "AND campaign.status != 'REMOVED' "
            "ORDER BY metrics.cost_micros DESC"
        )

        data = self._run_google_ads_query(customer_id, query)
        if not data:
            return pd.DataFrame()

        return self._google_ads_to_dataframe(data, "campaigns")

    def fetch_google_ads_ad_groups(
        self, customer_id: str, date_from: str | None = None, date_to: str | None = None
    ) -> pd.DataFrame:
        """Baja ad groups de Google Ads con métricas."""
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not date_to:
            date_to = datetime.now().strftime("%Y-%m-%d")

        query = (
            "SELECT ad_group.id, ad_group.name, ad_group.status, "
            "ad_group.type, campaign.name, "
            "metrics.impressions, metrics.clicks, metrics.cost_micros, "
            "metrics.conversions, metrics.conversions_value, "
            "metrics.ctr, metrics.average_cpc "
            f"FROM ad_group "
            f"WHERE segments.date BETWEEN '{date_from}' AND '{date_to}' "
            "AND ad_group.status != 'REMOVED' "
            "ORDER BY metrics.cost_micros DESC"
        )

        data = self._run_google_ads_query(customer_id, query)
        if not data:
            return pd.DataFrame()

        return self._google_ads_to_dataframe(data, "ad_groups")

    def fetch_google_ads_daily(
        self, customer_id: str, date_from: str | None = None, date_to: str | None = None
    ) -> pd.DataFrame:
        """Baja métricas diarias de Google Ads."""
        if not date_from:
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not date_to:
            date_to = datetime.now().strftime("%Y-%m-%d")

        query = (
            "SELECT segments.date, campaign.name, "
            "metrics.impressions, metrics.clicks, metrics.cost_micros, "
            "metrics.conversions, metrics.conversions_value "
            f"FROM campaign "
            f"WHERE segments.date BETWEEN '{date_from}' AND '{date_to}' "
            "ORDER BY segments.date DESC"
        )

        data = self._run_google_ads_query(customer_id, query)
        if not data:
            return pd.DataFrame()

        return self._google_ads_to_dataframe(data, "daily")

    def _run_google_ads_query(self, customer_id: str, query: str) -> list[dict] | None:
        """Ejecuta una query GAQL contra Google Ads API usando el SDK de Python."""
        try:
            from google.ads.googleads.client import GoogleAdsClient
            from src.web.secrets_helper import get_google_ads_credentials

            creds = get_google_ads_credentials()
            if not creds.get("developer_token"):
                logger.warning("Google Ads developer token no configurado")
                return None

            client = GoogleAdsClient(
                credentials=creds["credentials"],
                developer_token=creds["developer_token"],
                login_customer_id=creds["login_customer_id"],
            )

            ga_service = client.get_service("GoogleAdsService")
            response = ga_service.search(customer_id=customer_id, query=query)

            results = []
            for row in response:
                row_dict = {}
                for field_name in row.__class__.__dict__:
                    if field_name.startswith("_"):
                        continue
                    try:
                        obj = getattr(row, field_name)
                        for attr_name in obj.__class__.__dict__:
                            if attr_name.startswith("_"):
                                continue
                            try:
                                val = getattr(obj, attr_name)
                                if callable(val):
                                    continue
                                key = f"{field_name}.{attr_name}"
                                if hasattr(val, "name"):
                                    row_dict[key] = val.name
                                else:
                                    row_dict[key] = val
                            except (AttributeError, TypeError):
                                pass
                    except (AttributeError, TypeError):
                        pass
                results.append(row_dict)

            return results

        except ImportError:
            logger.warning("google-ads SDK no instalado, Google Ads no disponible")
            return None
        except FileNotFoundError:
            logger.warning("Credenciales de Google Ads no encontradas")
            return None
        except Exception as e:
            logger.error(f"Google Ads query failed: {e}")
            return None

    def _google_ads_to_dataframe(self, data: list[dict], data_type: str) -> pd.DataFrame:
        """Convierte respuesta de Google Ads API a DataFrame limpio."""
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # Convertir cost_micros a moneda real
        if "metrics.cost_micros" in df.columns:
            df["cost"] = df["metrics.cost_micros"].astype(float) / 1_000_000
            df.drop(columns=["metrics.cost_micros"], inplace=True)

        # Renombrar columnas para consistencia
        df.columns = [col.replace("metrics.", "").replace("campaign.", "").replace("ad_group.", "").replace("segments.", "") for col in df.columns]

        return df

    # ─── Meta Ads (HTTP directo a Marketing API) ─────────────────

    def _meta_api_get(self, endpoint: str, params: dict | None = None) -> dict:
        """Llama a la Meta Marketing API."""
        from src.web.secrets_helper import get_meta_access_token, get_meta_api_version

        token = get_meta_access_token()
        if not token:
            raise ValueError("Meta access token no configurado")

        api_version = get_meta_api_version()
        base_url = f"https://graph.facebook.com/{api_version}"
        params = params or {}
        params["access_token"] = token

        response = requests.get(f"{base_url}{endpoint}", params=params, timeout=60)
        data = response.json()

        if "error" in data:
            raise Exception(f"Meta API: {data['error'].get('message', 'Unknown error')}")

        return data

    def _meta_api_paginate(self, endpoint: str, params: dict | None = None, limit: int = 500) -> list[dict]:
        """Llama a la Meta API con paginación automática."""
        from src.web.secrets_helper import get_meta_access_token, get_meta_api_version

        token = get_meta_access_token()
        if not token:
            raise ValueError("Meta access token no configurado")

        api_version = get_meta_api_version()
        base_url = f"https://graph.facebook.com/{api_version}"
        params = params or {}
        params["access_token"] = token
        params["limit"] = str(limit)

        all_data = []
        url = f"{base_url}{endpoint}"

        while url:
            response = requests.get(url, params=params if url.startswith("http") and "access_token" not in url else None, timeout=60)
            data = response.json()

            if "error" in data:
                raise Exception(f"Meta API: {data['error'].get('message', 'Unknown error')}")

            all_data.extend(data.get("data", []))
            url = data.get("paging", {}).get("next")
            params = None  # Las URLs de next ya incluyen los params

        return all_data

    def fetch_meta_campaigns(
        self, account_id: str, status: str = "ACTIVE"
    ) -> pd.DataFrame:
        """Baja campañas de Meta Ads."""
        try:
            params = {
                "fields": "id,name,status,objective,daily_budget,lifetime_budget,budget_remaining,start_time,stop_time",
            }
            if status:
                params["filtering"] = json.dumps([{"field": "status", "operator": "IN", "value": [status]}])

            data = self._meta_api_paginate(f"/act_{account_id}/campaigns", params)
            if not data:
                return pd.DataFrame()
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Meta campaigns error: {e}")
            return pd.DataFrame()

    def fetch_meta_adsets(self, account_id: str) -> pd.DataFrame:
        """Baja ad sets de Meta Ads."""
        try:
            params = {
                "fields": "id,name,status,daily_budget,lifetime_budget,targeting,optimization_goal,bid_strategy,start_time,end_time",
            }
            data = self._meta_api_paginate(f"/act_{account_id}/adsets", params)
            if not data:
                return pd.DataFrame()
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Meta adsets error: {e}")
            return pd.DataFrame()

    def fetch_meta_ads(self, account_id: str) -> pd.DataFrame:
        """Baja ads de Meta Ads."""
        try:
            params = {
                "fields": "id,name,status,creative{id,name,title,body,image_url,thumbnail_url,video_id},adset_id",
            }
            data = self._meta_api_paginate(f"/act_{account_id}/ads", params)
            if not data:
                return pd.DataFrame()
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Meta ads error: {e}")
            return pd.DataFrame()

    def fetch_meta_insights(
        self,
        account_id: str,
        level: str = "campaign",
        date_preset: str = "last_30d",
    ) -> pd.DataFrame:
        """Baja insights de Meta Ads."""
        try:
            params = {
                "fields": "campaign_name,adset_name,ad_name,spend,impressions,clicks,cpc,cpm,ctr,actions,cost_per_action_type,conversions,purchase_roas",
                "level": level,
                "date_preset": date_preset,
            }
            data = self._meta_api_paginate(f"/act_{account_id}/insights", params)
            if not data:
                return pd.DataFrame()
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Meta insights error: {e}")
            return pd.DataFrame()

    def fetch_meta_ad_daily_insights(
        self,
        account_id: str,
        date_preset: str = "last_90d",
    ) -> pd.DataFrame:
        """Baja insights DIARIOS por AD — clave para detectar fatiga y medir vida útil."""
        try:
            params = {
                "fields": "ad_id,ad_name,adset_name,campaign_name,spend,impressions,clicks,cpc,ctr,frequency,actions,cost_per_action_type,purchase_roas",
                "level": "ad",
                "date_preset": date_preset,
                "time_increment": "1",
            }
            data = self._meta_api_paginate(f"/act_{account_id}/insights", params)
            if not data:
                return pd.DataFrame()

            df = pd.DataFrame(data)

            # Asegurar tipos numéricos
            numeric_cols = ["impressions", "clicks", "spend", "frequency",
                           "ctr", "cpc", "conversions", "cost_per_result"]
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            # Parsear fecha
            if "date_start" in df.columns:
                df["date"] = pd.to_datetime(df["date_start"])
            elif "date" not in df.columns and "day" in df.columns:
                df["date"] = pd.to_datetime(df["day"])

            return df
        except Exception as e:
            logger.error(f"Meta ad daily insights error: {e}")
            return pd.DataFrame()

    # ─── Fetch completo por cliente ─────────────────────────────

    def fetch_all_client_data(
        self,
        client_config: dict,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict[str, dict[str, pd.DataFrame]]:
        """Baja toda la data de un cliente desde las APIs directamente.

        Retorna la misma estructura que SheetsClient.load_client_data():
        {
            "google_ads": {"campaigns": df, "ad_groups": df, "daily_metrics": df},
            "meta_ads": {"campaigns": df, "adsets": df, "ads": df, "insights": df},
        }
        """
        all_data = {}

        # Google Ads
        google_id = client_config.get("google_ads_id")
        if google_id:
            logger.info(f"Bajando data de Google Ads para cuenta {google_id}...")
            all_data["google_ads"] = {
                "campaigns": self.fetch_google_ads_campaigns(google_id, date_from, date_to),
                "ad_groups": self.fetch_google_ads_ad_groups(google_id, date_from, date_to),
                "daily_metrics": self.fetch_google_ads_daily(google_id, date_from, date_to),
            }

        # Meta Ads
        meta_id = client_config.get("meta_ads_id")
        if meta_id:
            logger.info(f"Bajando data de Meta Ads para cuenta {meta_id}...")
            all_data["meta_ads"] = {
                "campaigns": self.fetch_meta_campaigns(meta_id),
                "adsets": self.fetch_meta_adsets(meta_id),
                "ads": self.fetch_meta_ads(meta_id),
                "insights": self.fetch_meta_insights(meta_id),
                "ad_daily": self.fetch_meta_ad_daily_insights(meta_id),
            }

        return all_data

    def save_to_drive(
        self, drive_client, client_name: str, data: dict[str, dict[str, pd.DataFrame]]
    ):
        """Guarda toda la data bajada como CSVs en Drive."""
        date_str = datetime.now().strftime("%Y-%m-%d")

        for platform, datasets in data.items():
            for dataset_name, df in datasets.items():
                if df.empty:
                    continue

                filename = f"{platform}_{dataset_name}_{date_str}.csv"
                csv_content = df.to_csv(index=False)
                drive_client.upload_data_csv(client_name, csv_content, filename)

        logger.info(f"Data guardada en Drive para '{client_name}'")

    def save_local(
        self, client_name: str, data: dict[str, dict[str, pd.DataFrame]]
    ):
        """Guarda toda la data bajada como CSVs locales en output/{cliente}/data/."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        base_dir = os.path.join("output", client_name.lower(), "data")
        os.makedirs(base_dir, exist_ok=True)

        for platform, datasets in data.items():
            for dataset_name, df in datasets.items():
                if df.empty:
                    continue

                filename = f"{platform}_{dataset_name}_{date_str}.csv"
                filepath = os.path.join(base_dir, filename)
                df.to_csv(filepath, index=False)
                logger.info(f"CSV guardado: {filepath} ({len(df)} filas)")

        logger.info(f"Data local guardada para '{client_name}' en {base_dir}")

    @staticmethod
    def load_local_csvs(client_name: str) -> dict[str, pd.DataFrame]:
        """Lee todos los CSVs locales de un cliente."""
        base_dir = os.path.join("output", client_name.lower(), "data")
        if not os.path.exists(base_dir):
            return {}

        csvs = {}
        for f in sorted(os.listdir(base_dir), reverse=True):
            if not f.endswith(".csv"):
                continue
            parts = f.rsplit("_", 1)
            base_name = parts[0] if len(parts) > 1 else f.replace(".csv", "")

            if base_name not in csvs:
                filepath = os.path.join(base_dir, f)
                try:
                    csvs[base_name] = pd.read_csv(filepath)
                except Exception:
                    pass

        return csvs
