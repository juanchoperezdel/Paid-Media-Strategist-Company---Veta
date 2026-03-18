"""Cálculos de métricas de performance marketing."""

import pandas as pd
import numpy as np


def calculate_cpa(cost: float, conversions: int) -> float | None:
    """Cost Per Acquisition."""
    if conversions == 0:
        return None
    return cost / conversions


def calculate_roas(revenue: float, cost: float) -> float | None:
    """Return On Ad Spend."""
    if cost == 0:
        return None
    return revenue / cost


def calculate_ctr(clicks: int, impressions: int) -> float | None:
    """Click-Through Rate (%)."""
    if impressions == 0:
        return None
    return (clicks / impressions) * 100


def calculate_cpc(cost: float, clicks: int) -> float | None:
    """Cost Per Click."""
    if clicks == 0:
        return None
    return cost / clicks


def calculate_cvr(conversions: int, clicks: int) -> float | None:
    """Conversion Rate (%)."""
    if clicks == 0:
        return None
    return (conversions / clicks) * 100


def calculate_cpm(cost: float, impressions: int) -> float | None:
    """Cost Per Mille (1000 impressions)."""
    if impressions == 0:
        return None
    return (cost / impressions) * 1000


def pct_change(current: float, previous: float) -> float | None:
    """Cambio porcentual entre dos valores."""
    if previous == 0:
        return None
    return ((current - previous) / previous) * 100


def detect_anomaly(values: list[float], threshold_std: float = 2.0) -> list[dict]:
    """Detecta anomalías en una serie usando desviación estándar.

    Retorna lista de dicts con index, value, y deviation para cada anomalía.
    """
    if len(values) < 3:
        return []

    arr = np.array(values, dtype=float)
    mean = np.nanmean(arr)
    std = np.nanstd(arr)

    if std == 0:
        return []

    anomalies = []
    for i, val in enumerate(arr):
        if np.isnan(val):
            continue
        deviation = (val - mean) / std
        if abs(deviation) >= threshold_std:
            anomalies.append({
                "index": i,
                "value": float(val),
                "deviation": round(float(deviation), 2),
                "direction": "up" if deviation > 0 else "down",
            })

    return anomalies


def calculate_trend(values: list[float], periods: int = 7) -> str:
    """Calcula la tendencia de una serie: 'improving', 'declining', 'stable'."""
    if len(values) < periods:
        return "insufficient_data"

    recent = values[-periods:]
    previous = values[-periods * 2 : -periods] if len(values) >= periods * 2 else values[:periods]

    recent_avg = np.nanmean(recent)
    previous_avg = np.nanmean(previous)

    change = pct_change(recent_avg, previous_avg)
    if change is None:
        return "insufficient_data"

    if change > 5:
        return "improving"
    elif change < -5:
        return "declining"
    return "stable"


def enrich_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega columnas calculadas a un DataFrame de métricas.

    Espera columnas: cost, clicks, impressions, conversions, revenue (opcional).
    """
    enriched = df.copy()

    if "clicks" in df.columns and "impressions" in df.columns:
        enriched["ctr"] = df.apply(
            lambda r: calculate_ctr(r["clicks"], r["impressions"]), axis=1
        )

    if "cost" in df.columns and "clicks" in df.columns:
        enriched["cpc"] = df.apply(
            lambda r: calculate_cpc(r["cost"], r["clicks"]), axis=1
        )

    if "cost" in df.columns and "conversions" in df.columns:
        enriched["cpa"] = df.apply(
            lambda r: calculate_cpa(r["cost"], r["conversions"]), axis=1
        )

    if "conversions" in df.columns and "clicks" in df.columns:
        enriched["cvr"] = df.apply(
            lambda r: calculate_cvr(r["conversions"], r["clicks"]), axis=1
        )

    if "revenue" in df.columns and "cost" in df.columns:
        enriched["roas"] = df.apply(
            lambda r: calculate_roas(r["revenue"], r["cost"]), axis=1
        )

    if "cost" in df.columns and "impressions" in df.columns:
        enriched["cpm"] = df.apply(
            lambda r: calculate_cpm(r["cost"], r["impressions"]), axis=1
        )

    return enriched
