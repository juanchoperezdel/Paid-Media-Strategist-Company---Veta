"""SQLite storage — un archivo .db por cliente para almacenar historial sin que explote.

Tablas:
- ad_daily: métricas diarias por ad (12 meses rolling)
- ad_metadata: fechas creación/modificación, status (siempre)
- lifecycle_snapshots: resultado del análisis semanal por ad (siempre)
- conclusions: resumen semanal en texto para el chat (siempre)
- rotation_history: evolución de la ventana óptima por campaña (siempre)
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta

import pandas as pd

from src.utils.logger import get_logger

logger = get_logger("veta.sqlite")


class SQLiteStore:
    """Storage SQLite por cliente. Un archivo, muchas tablas, consultas rápidas."""

    def __init__(self, client_name: str, base_dir: str = "output"):
        self.client_name = client_name
        client_dir = os.path.join(base_dir, client_name.lower().replace(" ", "_"))
        os.makedirs(client_dir, exist_ok=True)
        self.db_path = os.path.join(client_dir, "data.db")
        self._init_tables()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_tables(self):
        conn = self._connect()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS ad_daily (
                    ad_id TEXT NOT NULL,
                    ad_name TEXT,
                    campaign_id TEXT,
                    campaign_name TEXT,
                    date TEXT NOT NULL,
                    spend REAL,
                    impressions INTEGER,
                    clicks INTEGER,
                    ctr REAL,
                    cpc REAL,
                    frequency REAL,
                    conversions INTEGER,
                    cost_per_result REAL,
                    roas REAL,
                    PRIMARY KEY (ad_id, date)
                );

                CREATE TABLE IF NOT EXISTS ad_metadata (
                    ad_id TEXT PRIMARY KEY,
                    ad_name TEXT,
                    adset_id TEXT,
                    adset_name TEXT,
                    campaign_id TEXT,
                    campaign_name TEXT,
                    status TEXT,
                    created_time TEXT,
                    updated_time TEXT,
                    creative_id TEXT,
                    last_synced TEXT
                );

                CREATE TABLE IF NOT EXISTS lifecycle_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    campaign_id TEXT,
                    campaign_name TEXT,
                    total_ads INTEGER,
                    avg_decay_point REAL,
                    median_decay_point REAL,
                    rotation_days INTEGER,
                    confidence TEXT,
                    phase_distribution TEXT,
                    ads_detail TEXT,
                    UNIQUE(date, campaign_id)
                );

                CREATE TABLE IF NOT EXISTS conclusions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    campaign_id TEXT,
                    campaign_name TEXT,
                    summary TEXT NOT NULL,
                    vs_previous TEXT,
                    UNIQUE(date, campaign_id)
                );

                CREATE TABLE IF NOT EXISTS rotation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    campaign_id TEXT,
                    campaign_name TEXT,
                    recommended_days INTEGER,
                    avg_decay_day INTEGER,
                    confidence TEXT,
                    sample_size INTEGER,
                    UNIQUE(date, campaign_id)
                );

                CREATE INDEX IF NOT EXISTS idx_ad_daily_date ON ad_daily(date);
                CREATE INDEX IF NOT EXISTS idx_ad_daily_campaign ON ad_daily(campaign_id);
                CREATE INDEX IF NOT EXISTS idx_conclusions_date ON conclusions(date);
                CREATE INDEX IF NOT EXISTS idx_rotation_date ON rotation_history(date);
            """)
            conn.commit()
            logger.info(f"SQLite inicializado: {self.db_path}")
        finally:
            conn.close()

    # ─── Ad Daily ─────────────────────────────────────────────

    def save_ad_daily(self, df: pd.DataFrame):
        """Inserta métricas diarias por ad. Upsert por (ad_id, date)."""
        if df.empty:
            return

        conn = self._connect()
        try:
            for _, row in df.iterrows():
                conn.execute("""
                    INSERT OR REPLACE INTO ad_daily
                    (ad_id, ad_name, campaign_id, campaign_name, date,
                     spend, impressions, clicks, ctr, cpc, frequency,
                     conversions, cost_per_result, roas)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(row.get("ad_id", "")),
                    str(row.get("ad_name", "")),
                    str(row.get("campaign_id", "")),
                    str(row.get("campaign_name", "")),
                    str(row.get("date_start", row.get("date", ""))),
                    _float(row.get("spend")),
                    _int(row.get("impressions")),
                    _int(row.get("clicks")),
                    _float(row.get("ctr")),
                    _float(row.get("cpc")),
                    _float(row.get("frequency")),
                    _int(row.get("conversions", row.get("purchases"))),
                    _float(row.get("cost_per_result", row.get("cost_per_purchase"))),
                    _float(row.get("roas")),
                ))
            conn.commit()
            logger.info(f"Guardados {len(df)} registros diarios en SQLite")
        finally:
            conn.close()

    def get_ad_daily(
        self,
        campaign_id: str | None = None,
        ad_id: str | None = None,
        days: int = 90,
    ) -> pd.DataFrame:
        """Lee data diaria filtrada."""
        conn = self._connect()
        try:
            cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            query = "SELECT * FROM ad_daily WHERE date >= ?"
            params: list = [cutoff]

            if campaign_id:
                query += " AND campaign_id = ?"
                params.append(campaign_id)
            if ad_id:
                query += " AND ad_id = ?"
                params.append(ad_id)

            query += " ORDER BY date"
            df = pd.read_sql_query(query, conn, params=params)
            return df
        finally:
            conn.close()

    # ─── Ad Metadata ──────────────────────────────────────────

    def save_ad_metadata(self, df: pd.DataFrame):
        """Inserta metadata de ads. Upsert por ad_id."""
        if df.empty:
            return

        conn = self._connect()
        now = datetime.now().isoformat()
        try:
            for _, row in df.iterrows():
                conn.execute("""
                    INSERT OR REPLACE INTO ad_metadata
                    (ad_id, ad_name, adset_id, adset_name, campaign_id, campaign_name,
                     status, created_time, updated_time, creative_id, last_synced)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(row.get("ad_id", "")),
                    str(row.get("ad_name", "")),
                    str(row.get("adset_id", "")),
                    str(row.get("adset_name", "")),
                    str(row.get("campaign_id", "")),
                    str(row.get("campaign_name", "")),
                    str(row.get("ad_status", row.get("status", ""))),
                    str(row.get("ad_created", row.get("created_time", ""))),
                    str(row.get("ad_updated", row.get("updated_time", ""))),
                    str(row.get("creative_id", "")),
                    now,
                ))
            conn.commit()
            logger.info(f"Guardados {len(df)} registros de metadata en SQLite")
        finally:
            conn.close()

    def get_ad_metadata(self, campaign_id: str | None = None) -> pd.DataFrame:
        """Lee metadata de ads."""
        conn = self._connect()
        try:
            if campaign_id:
                return pd.read_sql_query(
                    "SELECT * FROM ad_metadata WHERE campaign_id = ?",
                    conn, params=[campaign_id]
                )
            return pd.read_sql_query("SELECT * FROM ad_metadata", conn)
        finally:
            conn.close()

    # ─── Lifecycle Snapshots ──────────────────────────────────

    def save_lifecycle_snapshot(self, date: str, campaign_id: str, campaign_name: str, results: dict):
        """Guarda resultado del análisis de lifecycle de una campaña."""
        conn = self._connect()
        try:
            rotation = results.get("optimal_rotation_window", {})
            conn.execute("""
                INSERT OR REPLACE INTO lifecycle_snapshots
                (date, campaign_id, campaign_name, total_ads, avg_decay_point,
                 median_decay_point, rotation_days, confidence, phase_distribution, ads_detail)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                date,
                campaign_id,
                campaign_name,
                results.get("total_ads_analyzed", 0),
                results.get("avg_decay_point"),
                results.get("median_decay_point"),
                rotation.get("recommended_days"),
                rotation.get("confidence", "low"),
                json.dumps(results.get("phase_distribution", {})),
                json.dumps([{
                    "ad_id": a["ad_id"],
                    "ad_name": a["ad_name"],
                    "phase": a["phase"],
                    "decay_point_day": a["decay_point_day"],
                    "fatigue_score": a["fatigue"]["score"],
                    "fatigue_level": a["fatigue"]["level"],
                    "recommendation": a["recommendation"],
                } for a in results.get("all_ads", [])]),
            ))
            conn.commit()
            logger.info(f"Lifecycle snapshot guardado: {campaign_name} ({date})")
        finally:
            conn.close()

    def get_lifecycle_snapshots(self, campaign_id: str | None = None, months: int = 6) -> list[dict]:
        """Lee snapshots de lifecycle."""
        conn = self._connect()
        try:
            cutoff = (datetime.now() - timedelta(days=months * 30)).strftime("%Y-%m-%d")
            query = "SELECT * FROM lifecycle_snapshots WHERE date >= ?"
            params: list = [cutoff]
            if campaign_id:
                query += " AND campaign_id = ?"
                params.append(campaign_id)
            query += " ORDER BY date DESC"

            rows = conn.execute(query, params).fetchall()
            results = []
            for row in rows:
                d = dict(row)
                d["phase_distribution"] = json.loads(d.get("phase_distribution", "{}"))
                d["ads_detail"] = json.loads(d.get("ads_detail", "[]"))
                results.append(d)
            return results
        finally:
            conn.close()

    # ─── Conclusions ──────────────────────────────────────────

    def save_conclusion(self, date: str, campaign_id: str, campaign_name: str, summary: str, vs_previous: str = ""):
        """Guarda resumen semanal en texto (lo que lee el chat)."""
        conn = self._connect()
        try:
            conn.execute("""
                INSERT OR REPLACE INTO conclusions
                (date, campaign_id, campaign_name, summary, vs_previous)
                VALUES (?, ?, ?, ?, ?)
            """, (date, campaign_id, campaign_name, summary, vs_previous))
            conn.commit()
            logger.info(f"Conclusión guardada: {campaign_name} ({date})")
        finally:
            conn.close()

    def get_conclusions(self, months: int = 6, campaign_id: str | None = None) -> list[dict]:
        """Lee últimas N meses de conclusiones para el chat."""
        conn = self._connect()
        try:
            cutoff = (datetime.now() - timedelta(days=months * 30)).strftime("%Y-%m-%d")
            query = "SELECT * FROM conclusions WHERE date >= ?"
            params: list = [cutoff]
            if campaign_id:
                query += " AND campaign_id = ?"
                params.append(campaign_id)
            query += " ORDER BY date DESC"

            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    # ─── Rotation History ─────────────────────────────────────

    def save_rotation(self, date: str, campaign_id: str, campaign_name: str, rotation: dict):
        """Guarda evolución de la ventana óptima de rotación."""
        conn = self._connect()
        try:
            conn.execute("""
                INSERT OR REPLACE INTO rotation_history
                (date, campaign_id, campaign_name, recommended_days,
                 avg_decay_day, confidence, sample_size)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                date,
                campaign_id,
                campaign_name,
                rotation.get("recommended_days"),
                rotation.get("average_decay_day"),
                rotation.get("confidence", "low"),
                rotation.get("sample_size", 0),
            ))
            conn.commit()
        finally:
            conn.close()

    def get_rotation_history(self, campaign_id: str | None = None) -> list[dict]:
        """Lee evolución histórica de la ventana de rotación."""
        conn = self._connect()
        try:
            query = "SELECT * FROM rotation_history"
            params: list = []
            if campaign_id:
                query += " WHERE campaign_id = ?"
                params.append(campaign_id)
            query += " ORDER BY date"

            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    # ─── Cleanup ──────────────────────────────────────────────

    def cleanup_old_data(self, months: int = 12):
        """Borra ad_daily de más de N meses (rolling window)."""
        conn = self._connect()
        try:
            cutoff = (datetime.now() - timedelta(days=months * 30)).strftime("%Y-%m-%d")
            result = conn.execute("DELETE FROM ad_daily WHERE date < ?", [cutoff])
            conn.commit()
            deleted = result.rowcount
            if deleted > 0:
                logger.info(f"Limpieza: {deleted} registros de ad_daily eliminados (anteriores a {cutoff})")
                conn.execute("VACUUM")
        finally:
            conn.close()

    # ─── Estadísticas ─────────────────────────────────────────

    def stats(self) -> dict:
        """Estadísticas del almacenamiento."""
        conn = self._connect()
        try:
            daily_count = conn.execute("SELECT COUNT(*) FROM ad_daily").fetchone()[0]
            meta_count = conn.execute("SELECT COUNT(*) FROM ad_metadata").fetchone()[0]
            snap_count = conn.execute("SELECT COUNT(*) FROM lifecycle_snapshots").fetchone()[0]
            conc_count = conn.execute("SELECT COUNT(*) FROM conclusions").fetchone()[0]

            date_range = conn.execute(
                "SELECT MIN(date), MAX(date) FROM ad_daily"
            ).fetchone()

            return {
                "db_path": self.db_path,
                "ad_daily_rows": daily_count,
                "ad_metadata_rows": meta_count,
                "lifecycle_snapshots": snap_count,
                "conclusions": conc_count,
                "date_range": {
                    "from": date_range[0] if date_range else None,
                    "to": date_range[1] if date_range else None,
                },
                "db_size_mb": round(os.path.getsize(self.db_path) / 1024 / 1024, 2),
            }
        finally:
            conn.close()


# ─── Helpers ──────────────────────────────────────────────

def _float(val) -> float | None:
    try:
        return float(val) if val is not None and str(val) not in ("", "nan", "None") else None
    except (ValueError, TypeError):
        return None


def _int(val) -> int | None:
    try:
        return int(float(val)) if val is not None and str(val) not in ("", "nan", "None") else None
    except (ValueError, TypeError):
        return None
