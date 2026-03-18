"""Creative Lifecycle Analyzer — mide la vida útil de ads/adsets/campañas.

Con cada semana de data, este módulo aprende:
1. Cuántos días tarda un ad en empezar a sub-performar (decay point)
2. Cuál es el período óptimo antes de rotar creativos
3. Qué tipo de ads duran más (carrusel vs reel vs estático, etc.)

El resultado es un "perfil de vida útil" por cliente que se refina con el tiempo.
"""

import os
import json
from datetime import datetime

import pandas as pd
import numpy as np

from src.utils.logger import get_logger

logger = get_logger("veta.lifecycle")

# Archivo donde se acumula el historial de lifecycles por cliente
LIFECYCLE_DIR = "output/{client}/lifecycle"

# Ventana de tolerancia para correlacionar edición con decay (±N días)
EDIT_DECAY_TOLERANCE_DAYS = 3


class CreativeLifecycleAnalyzer:
    """Analiza la curva de vida de creativos y aprende patrones óptimos."""

    def __init__(self, client_name: str):
        self.client_name = client_name
        self.lifecycle_dir = LIFECYCLE_DIR.format(client=client_name.lower())
        os.makedirs(self.lifecycle_dir, exist_ok=True)
        self._history = self._load_history()

    # ─── Análisis de un ad individual ───────────────────────────

    def analyze_ad(self, ad_daily: pd.DataFrame, ad_id: str) -> dict:
        """Analiza la curva de vida de un ad específico.

        Args:
            ad_daily: DataFrame con métricas diarias del ad
            ad_id: ID del ad a analizar

        Returns:
            dict con métricas de lifecycle
        """
        df = ad_daily[ad_daily["ad_id"] == str(ad_id)].copy() if "ad_id" in ad_daily.columns else ad_daily.copy()

        if df.empty or len(df) < 7:
            return {"status": "insufficient_data", "days": len(df)}

        df = df.sort_values("date")

        # Métricas base
        total_days = (df["date"].max() - df["date"].min()).days + 1
        ad_name = df["ad_name"].iloc[0] if "ad_name" in df.columns else ad_id

        # Calcular medias móviles de 7 días para suavizar
        if "ctr" in df.columns:
            df["ctr_ma7"] = df["ctr"].rolling(7, min_periods=3).mean()
        if "cost_per_result" in df.columns:
            df["cpa_ma7"] = df["cost_per_result"].rolling(7, min_periods=3).mean()
        if "frequency" in df.columns:
            df["freq_ma7"] = df["frequency"].rolling(7, min_periods=3).mean()

        # Detectar punto de decay (dónde empieza a sub-performar)
        decay_point = self._find_decay_point(df)

        # Detectar fatiga
        fatigue = self._detect_fatigue(df)

        # Calcular fase actual
        phase = self._determine_phase(df, decay_point, fatigue)

        # Diagnóstico de acción
        action_diag = self._diagnose_action(df, fatigue, phase)

        result = {
            "ad_id": str(ad_id),
            "ad_name": ad_name,
            "total_days_active": total_days,
            "data_points": len(df),
            "decay_point_day": decay_point,
            "phase": phase,
            "fatigue": fatigue,
            "action": action_diag["action"],
            "action_detail": action_diag["action_detail"],
            "metrics_summary": {
                "avg_ctr": float(df["ctr"].mean()) if "ctr" in df.columns else None,
                "avg_cpa": float(df["cost_per_result"].mean()) if "cost_per_result" in df.columns else None,
                "max_frequency": float(df["frequency"].max()) if "frequency" in df.columns else None,
                "total_spend": float(df["spend"].sum()) if "spend" in df.columns else None,
            },
            "recommendation": self._recommend(phase, fatigue, total_days, decay_point),
        }

        return result

    def _find_decay_point(self, df: pd.DataFrame) -> int | None:
        """Encuentra el día donde el performance empieza a decaer sostenidamente.

        Busca el punto donde CTR cae >15% respecto al pico Y se mantiene abajo por 7+ días.
        """
        if "ctr_ma7" not in df.columns or df["ctr_ma7"].isna().all():
            return None

        ctr = df["ctr_ma7"].dropna().values
        if len(ctr) < 14:
            return None

        peak_idx = np.argmax(ctr)
        peak_val = ctr[peak_idx]

        if peak_val == 0:
            return None

        threshold = peak_val * 0.85  # 15% debajo del pico

        # Buscar primer punto donde se mantiene debajo por 7 días consecutivos
        below_count = 0
        for i in range(peak_idx + 1, len(ctr)):
            if ctr[i] < threshold:
                below_count += 1
                if below_count >= 7:
                    decay_day = i - 6  # primer día de la racha
                    return int(decay_day)
            else:
                below_count = 0

        return None  # No se detectó decay

    def _detect_fatigue(self, df: pd.DataFrame) -> dict:
        """Detecta señales de fatiga creativa."""
        signals = []
        score = 0  # 0-100, donde 100 = fatiga total

        # 1. CTR cayendo >15% en últimos 14 días
        if "ctr" in df.columns and len(df) >= 14:
            recent = df.tail(14)
            first_half = recent.head(7)["ctr"].mean()
            second_half = recent.tail(7)["ctr"].mean()
            if first_half > 0:
                ctr_change = (second_half - first_half) / first_half
                if ctr_change < -0.15:
                    signals.append(f"CTR cayó {ctr_change:.0%} en últimos 14 días")
                    score += 30

        # 2. Frecuencia >3 y subiendo
        if "frequency" in df.columns and len(df) >= 7:
            recent_freq = df.tail(7)["frequency"].mean()
            if recent_freq > 3:
                signals.append(f"Frecuencia alta: {recent_freq:.1f}")
                score += 25
            prev_freq = df.tail(14).head(7)["frequency"].mean() if len(df) >= 14 else 0
            if prev_freq > 0 and recent_freq > prev_freq * 1.1:
                signals.append(f"Frecuencia subiendo: {prev_freq:.1f} → {recent_freq:.1f}")
                score += 15

        # 3. CPA subiendo mientras impresiones estables
        if "cost_per_result" in df.columns and "impressions" in df.columns and len(df) >= 14:
            recent = df.tail(14)
            first_half_cpa = recent.head(7)["cost_per_result"].mean()
            second_half_cpa = recent.tail(7)["cost_per_result"].mean()
            first_half_imp = recent.head(7)["impressions"].mean()
            second_half_imp = recent.tail(7)["impressions"].mean()

            if first_half_cpa > 0 and first_half_imp > 0:
                cpa_change = (second_half_cpa - first_half_cpa) / first_half_cpa
                imp_change = abs((second_half_imp - first_half_imp) / first_half_imp)

                if cpa_change > 0.20 and imp_change < 0.20:
                    signals.append(f"CPA subió {cpa_change:.0%} con impresiones estables")
                    score += 30

        level = "none"
        if score >= 60:
            level = "critical"
        elif score >= 30:
            level = "warning"
        elif score > 0:
            level = "early"

        return {
            "level": level,
            "score": min(score, 100),
            "signals": signals,
        }

    def _determine_phase(self, df: pd.DataFrame, decay_point: int | None, fatigue: dict) -> str:
        """Determina en qué fase del lifecycle está el ad.

        Fases:
        - ramp_up: Primeros 7 días, aprendiendo
        - peak: Performance estable/óptima
        - plateau: Aún funciona pero estancado
        - decline: Performance cayendo
        - exhausted: Fatiga confirmada, reemplazar
        """
        days = len(df)

        if days < 7:
            return "ramp_up"

        if fatigue["level"] == "critical":
            return "exhausted"

        if fatigue["level"] == "warning":
            return "decline"

        if decay_point is not None:
            return "decline"

        # Verificar si está en plateau (sin mejora ni caída en últimos 14 días)
        if "ctr" in df.columns and days >= 14:
            recent_ctr = df.tail(14)["ctr"]
            ctr_std = recent_ctr.std() / recent_ctr.mean() if recent_ctr.mean() > 0 else 0
            if ctr_std < 0.10:  # variación <10% = estancado
                return "plateau"

        return "peak"

    def _recommend(self, phase: str, fatigue: dict, days: int, decay_point: int | None) -> str:
        """Genera recomendación basada en la fase del lifecycle."""
        recommendations = {
            "ramp_up": "Dejar correr — aún en fase de aprendizaje. Evaluar en 7 días.",
            "peak": "Mantener activo — rendimiento óptimo. Preparar variaciones para cuando decaiga.",
            "plateau": f"Preparar reemplazo — lleva {days} días activo sin mejora. Testear nueva variación.",
            "decline": f"Rotar pronto — performance cayendo desde día ~{decay_point or '?'}. Lanzar reemplazo esta semana.",
            "exhausted": f"Reemplazar hoy — {days} días activo, fatiga confirmada: {', '.join(fatigue['signals'][:2])}",
        }
        return recommendations.get(phase, "Sin datos suficientes")

    def _diagnose_action(self, df: pd.DataFrame, fatigue: dict, phase: str, edit_info: dict | None = None) -> dict:
        """Diagnostica QUÉ cambiar en un ad basándose en la data.

        Returns:
            dict con "action" y "action_detail"
        """
        if phase in ("ramp_up", "peak"):
            return {"action": "no_editar", "action_detail": "Rendimiento óptimo, no tocar."}

        # Si editar empeoró las cosas, recomendar lanzar nuevo
        if edit_info and edit_info.get("was_edited"):
            if edit_info.get("decay_cause") == "edicion":
                return {
                    "action": "lanzar_nuevo",
                    "action_detail": (
                        f"Este ad ya fue editado ({edit_info.get('updated', '?')}) y decayó después. "
                        f"No editar de nuevo — lanzar uno nuevo manteniendo este como referencia."
                    ),
                }

        # Fatiga extrema → rotar todo
        if fatigue["score"] >= 60 or phase == "exhausted":
            return {
                "action": "rotar_completo",
                "action_detail": "Fatiga total confirmada. Crear creativo nuevo desde cero (nuevo copy + nueva imagen/video).",
            }

        # Diagnosticar copy vs visual
        ctr_dropping = any("CTR" in s for s in fatigue.get("signals", []))
        freq_high = any("Frecuencia" in s for s in fatigue.get("signals", []))
        cpa_rising = any("CPA" in s for s in fatigue.get("signals", []))

        if freq_high and ctr_dropping and not cpa_rising:
            # Frecuencia alta + CTR cae = la gente vio mucho el visual
            return {
                "action": "cambiar_visual",
                "action_detail": (
                    "La frecuencia es alta y el CTR cayó — la audiencia ya vio demasiado este visual. "
                    "Mantener el copy/oferta y cambiar la imagen o video."
                ),
            }

        if ctr_dropping and not freq_high:
            # CTR cae sin frecuencia alta = el mensaje se agotó
            return {
                "action": "cambiar_copy",
                "action_detail": (
                    "El CTR está cayendo pero la frecuencia no es excesiva. "
                    "El mensaje perdió impacto. Probar un nuevo ángulo de copy manteniendo el visual."
                ),
            }

        if cpa_rising and not ctr_dropping:
            # CPA sube pero CTR estable = problema post-clic, no del creativo
            return {
                "action": "no_editar",
                "action_detail": (
                    "El CPA subió pero el CTR se mantiene — el problema puede ser la landing page "
                    "o la audiencia, no el creativo. Revisar segmentación antes de cambiar el ad."
                ),
            }

        # Default para decline sin señales claras
        return {
            "action": "lanzar_nuevo",
            "action_detail": (
                "Performance cayendo sin señales claras de qué falla. "
                "Recomendación: lanzar un ad nuevo y dejar este correr con presupuesto mínimo para comparar."
            ),
        }

    # ─── Análisis masivo de todos los ads ───────────────────────

    def analyze_all_ads(self, ad_daily: pd.DataFrame) -> dict:
        """Analiza lifecycle de todos los ads en el DataFrame.

        Returns:
            dict con resumen + detalle por ad
        """
        if ad_daily.empty or "ad_id" not in ad_daily.columns:
            return {"error": "No hay data de ads diarios"}

        results = []
        for ad_id in ad_daily["ad_id"].unique():
            result = self.analyze_ad(ad_daily, ad_id)
            if result.get("status") != "insufficient_data":
                results.append(result)

        if not results:
            return {"error": "Ningún ad tiene suficiente data (mínimo 7 días)"}

        # Calcular promedios de vida útil
        decay_points = [r["decay_point_day"] for r in results if r["decay_point_day"] is not None]
        active_days = [r["total_days_active"] for r in results]

        # Contar por fase
        phase_counts = {}
        for r in results:
            phase = r["phase"]
            phase_counts[phase] = phase_counts.get(phase, 0) + 1

        # Ads que necesitan atención
        needs_action = [r for r in results if r["phase"] in ("decline", "exhausted")]
        needs_action.sort(key=lambda x: x["fatigue"]["score"], reverse=True)

        summary = {
            "total_ads_analyzed": len(results),
            "avg_active_days": float(np.mean(active_days)) if active_days else 0,
            "avg_decay_point": float(np.mean(decay_points)) if decay_points else None,
            "median_decay_point": float(np.median(decay_points)) if decay_points else None,
            "optimal_rotation_window": self._calc_optimal_rotation(decay_points),
            "phase_distribution": phase_counts,
            "ads_needing_action": len(needs_action),
            "action_required": needs_action[:10],  # top 10 más urgentes
            "all_ads": results,
        }

        # Guardar en historial para aprendizaje
        self._save_snapshot(summary)

        return summary

    def _calc_optimal_rotation(self, decay_points: list[float]) -> dict:
        """Calcula la ventana óptima de rotación de creativos."""
        if not decay_points or len(decay_points) < 3:
            return {
                "days": None,
                "confidence": "low",
                "note": "Necesita más data — mínimo 3 ads con decay detectado",
            }

        avg = float(np.mean(decay_points))
        median = float(np.median(decay_points))
        # Usar el percentil 25 como margen de seguridad (rotar ANTES de que decaiga)
        safe_window = float(np.percentile(decay_points, 25))

        # Combinar con historial si existe
        historical = self._get_historical_decay_points()
        if historical:
            all_points = decay_points + historical
            avg = float(np.mean(all_points))
            median = float(np.median(all_points))
            safe_window = float(np.percentile(all_points, 25))

        confidence = "low"
        if len(decay_points) >= 10:
            confidence = "high"
        elif len(decay_points) >= 5:
            confidence = "medium"

        return {
            "recommended_days": int(safe_window),
            "average_decay_day": int(avg),
            "median_decay_day": int(median),
            "confidence": confidence,
            "sample_size": len(decay_points) + len(historical),
            "interpretation": (
                f"Los creativos empiezan a decaer en promedio al día {int(avg)}. "
                f"Recomendación: preparar reemplazo al día {int(safe_window)} "
                f"(margen de seguridad del 25%). Confianza: {confidence}."
            ),
        }

    # ─── Historial (aprendizaje acumulativo) ────────────────────

    def _load_history(self) -> list[dict]:
        """Carga el historial de snapshots anteriores."""
        history_file = os.path.join(self.lifecycle_dir, "history.json")
        if os.path.exists(history_file):
            with open(history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save_snapshot(self, summary: dict):
        """Guarda un snapshot del análisis actual para aprendizaje futuro."""
        snapshot = {
            "date": datetime.now().isoformat(),
            "total_ads": summary["total_ads_analyzed"],
            "avg_decay_point": summary["avg_decay_point"],
            "median_decay_point": summary.get("median_decay_point"),
            "optimal_rotation": summary["optimal_rotation_window"],
            "phase_distribution": summary["phase_distribution"],
        }

        self._history.append(snapshot)

        # Guardar
        history_file = os.path.join(self.lifecycle_dir, "history.json")
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(self._history, f, indent=2, default=str)

        logger.info(f"Lifecycle snapshot guardado ({len(self._history)} total)")

    def _get_historical_decay_points(self) -> list[float]:
        """Extrae todos los decay points históricos para mejorar el cálculo."""
        points = []
        for snapshot in self._history:
            dp = snapshot.get("avg_decay_point")
            if dp is not None:
                points.append(dp)
        return points

    # ─── Análisis con metadata (ediciones) ─────────────────────

    def analyze_with_metadata(self, ad_daily: pd.DataFrame, ad_metadata: pd.DataFrame) -> dict:
        """Analiza lifecycle correlacionando con fechas de edición.

        Cruza updated_time con el timeline de performance para determinar
        si un decay fue causado por fatiga orgánica o por una edición.
        """
        results = self.analyze_all_ads(ad_daily)
        if "error" in results:
            return results

        # Enriquecer cada ad con metadata de ediciones
        for ad_result in results.get("all_ads", []):
            ad_id = str(ad_result["ad_id"])
            meta_row = ad_metadata[ad_metadata["ad_id"].astype(str) == ad_id]

            if meta_row.empty:
                ad_result["edit_correlation"] = {"was_edited": False, "note": "Sin metadata"}
                continue

            row = meta_row.iloc[0]
            created = pd.to_datetime(row.get("ad_created", row.get("created_time")), errors="coerce")
            updated = pd.to_datetime(row.get("ad_updated", row.get("updated_time")), errors="coerce")

            was_edited = (created is not None and updated is not None
                         and pd.notna(created) and pd.notna(updated)
                         and created.date() != updated.date())

            edit_info = {
                "was_edited": was_edited,
                "created": str(created.date()) if pd.notna(created) else None,
                "updated": str(updated.date()) if pd.notna(updated) else None,
                "status": str(row.get("ad_status", row.get("status", ""))),
            }

            # Correlacionar edición con decay
            if was_edited and ad_result.get("decay_point_day") is not None:
                # Calcular en qué fecha fue el decay
                ad_data = ad_daily[ad_daily["ad_id"].astype(str) == ad_id].sort_values("date")
                if not ad_data.empty:
                    first_date = pd.to_datetime(ad_data["date"].iloc[0]).tz_localize(None)
                    decay_date = first_date + pd.Timedelta(days=ad_result["decay_point_day"])
                    updated_naive = updated.tz_localize(None) if hasattr(updated, 'tz') and updated.tz else updated

                    days_between = abs((decay_date - updated_naive).days)
                    if days_between <= EDIT_DECAY_TOLERANCE_DAYS:
                        edit_info["decay_cause"] = "edicion"
                        edit_info["note"] = (
                            f"Decay al día {ad_result['decay_point_day']} coincide con edición "
                            f"del {updated.date()} (±{days_between}d). La edición probablemente "
                            f"reseteó Learning Phase."
                        )
                    else:
                        edit_info["decay_cause"] = "fatiga_organica"
                        edit_info["note"] = (
                            f"Decay al día {ad_result['decay_point_day']} no coincide con "
                            f"edición del {updated.date()} ({days_between}d de diferencia). "
                            f"Fatiga orgánica del creativo."
                        )
            elif was_edited:
                edit_info["decay_cause"] = "sin_decay"
                edit_info["note"] = "Fue editado pero no se detectó decay."
            elif ad_result.get("decay_point_day") is not None:
                edit_info["decay_cause"] = "fatiga_organica"
                edit_info["note"] = "Nunca fue editado. Decay es fatiga orgánica."

            ad_result["edit_correlation"] = edit_info

            # Re-diagnosticar acción con info de edición
            ad_data = ad_daily[ad_daily["ad_id"].astype(str) == ad_id]
            action_diag = self._diagnose_action(ad_data, ad_result["fatigue"], ad_result["phase"], edit_info)
            ad_result["action"] = action_diag["action"]
            ad_result["action_detail"] = action_diag["action_detail"]

        # Estadísticas de edición vs no edición
        edited_ads = [a for a in results["all_ads"] if a.get("edit_correlation", {}).get("was_edited")]
        unedited_ads = [a for a in results["all_ads"] if not a.get("edit_correlation", {}).get("was_edited")]

        edited_decays = [a["decay_point_day"] for a in edited_ads if a["decay_point_day"] is not None]
        unedited_decays = [a["decay_point_day"] for a in unedited_ads if a["decay_point_day"] is not None]

        results["edit_analysis"] = {
            "edited_count": len(edited_ads),
            "unedited_count": len(unedited_ads),
            "edited_avg_decay": float(np.mean(edited_decays)) if edited_decays else None,
            "unedited_avg_decay": float(np.mean(unedited_decays)) if unedited_decays else None,
            "pattern": self._edit_pattern_conclusion(edited_decays, unedited_decays),
        }

        return results

    def _edit_pattern_conclusion(self, edited_decays: list, unedited_decays: list) -> str:
        """Genera conclusión sobre el patrón edición vs no edición."""
        if not edited_decays and not unedited_decays:
            return "Insuficiente data para detectar patrón."
        if not edited_decays:
            return "Ningún ad editado tuvo decay. Solo se observa fatiga orgánica."
        if not unedited_decays:
            return "Solo hay ads editados con decay. No se puede comparar."

        avg_edited = np.mean(edited_decays)
        avg_unedited = np.mean(unedited_decays)

        if avg_edited < avg_unedited * 0.8:
            return (
                f"Ads editados decaen más rápido (día {avg_edited:.0f}) que los no editados "
                f"(día {avg_unedited:.0f}). Las ediciones acortan la vida útil — posiblemente "
                f"por reseteo de Learning Phase."
            )
        elif avg_edited > avg_unedited * 1.2:
            return (
                f"Ads editados duran más (día {avg_edited:.0f}) que los no editados "
                f"(día {avg_unedited:.0f}). Las ediciones parecen revitalizar el creativo."
            )
        else:
            return (
                f"No hay diferencia significativa entre ads editados (día {avg_edited:.0f}) "
                f"y no editados (día {avg_unedited:.0f})."
            )

    # ─── Generación de conclusiones (para SQLite) ─────────────

    def to_conclusion(self, results: dict, campaign_name: str, previous_conclusion: dict | None = None) -> str:
        """Genera resumen en texto de una sola corrida, comparando con la anterior.

        Este texto es lo que el chat lee para responder preguntas.
        """
        date = datetime.now().strftime("%Y-%m-%d")
        total = results.get("total_ads_analyzed", 0)
        rotation = results.get("optimal_rotation_window", {})
        phases = results.get("phase_distribution", {})
        edit_analysis = results.get("edit_analysis", {})

        lines = [f"Semana {date} — {campaign_name}: {total} ads analizados."]

        # Fases
        decline_count = phases.get("decline", 0) + phases.get("exhausted", 0)
        peak_count = phases.get("peak", 0)
        lines.append(f"Estado: {peak_count} en peak, {decline_count} en decline/agotado.")

        # Rotación
        if rotation.get("recommended_days"):
            lines.append(f"Rotar cada {rotation['recommended_days']} días (confianza: {rotation.get('confidence', 'low')}).")

        # Ads a reemplazar
        action = results.get("action_required", [])
        if action:
            names = [f"{a['ad_name']} ({a['total_days_active']}d)" for a in action[:5]]
            lines.append(f"Ads a reemplazar: {', '.join(names)}.")

        # Patrón ediciones
        if edit_analysis.get("pattern"):
            lines.append(f"Patrón ediciones: {edit_analysis['pattern']}")

        # Comparación con semana anterior
        if previous_conclusion:
            prev_text = previous_conclusion.get("summary", "")
            # Extraer rotación anterior si existe
            import re
            prev_match = re.search(r"Rotar cada (\d+) días", prev_text)
            curr_days = rotation.get("recommended_days")
            if prev_match and curr_days:
                prev_days = int(prev_match.group(1))
                diff = curr_days - prev_days
                if diff == 0:
                    lines.append(f"vs semana anterior: ventana de rotación estable ({curr_days}d).")
                elif diff > 0:
                    lines.append(f"vs semana anterior: ventana subió {prev_days}d → {curr_days}d (creativos duran más).")
                else:
                    lines.append(f"vs semana anterior: ventana bajó {prev_days}d → {curr_days}d (creativos se fatigan más rápido).")

        return " ".join(lines)

    def to_vs_previous(self, results: dict, previous_conclusion: dict | None = None) -> str:
        """Genera solo la comparación con la semana anterior."""
        if not previous_conclusion:
            return "Primera semana de análisis — sin comparación."

        rotation = results.get("optimal_rotation_window", {})
        curr_days = rotation.get("recommended_days")
        if not curr_days:
            return "Sin ventana de rotación calculada esta semana."

        import re
        prev_text = previous_conclusion.get("summary", "")
        prev_match = re.search(r"Rotar cada (\d+) días", prev_text)
        if not prev_match:
            return "Semana anterior sin ventana de rotación."

        prev_days = int(prev_match.group(1))
        diff = curr_days - prev_days
        if diff == 0:
            return f"Estable: {curr_days}d (sin cambio)."
        elif diff > 0:
            return f"Mejoró: {prev_days}d → {curr_days}d (+{diff}d de vida útil)."
        else:
            return f"Empeoró: {prev_days}d → {curr_days}d ({diff}d de vida útil)."

    def get_lifecycle_report(self) -> str:
        """Genera un reporte markdown del estado de lifecycle del cliente."""
        if not self._history:
            return "Sin datos de lifecycle todavía. Se necesita al menos 1 semana de data diaria por ad."

        latest = self._history[-1]
        rotation = latest.get("optimal_rotation", {})

        lines = [
            f"## Lifecycle Report — {self.client_name}",
            f"**Última actualización:** {latest['date'][:10]}",
            f"**Ads analizados:** {latest['total_ads']}",
            "",
        ]

        if rotation.get("recommended_days"):
            lines.extend([
                "### Ventana óptima de rotación",
                f"- **Rotar creativos cada:** {rotation['recommended_days']} días",
                f"- **Decay promedio al día:** {rotation.get('average_decay_day', '?')}",
                f"- **Confianza:** {rotation.get('confidence', 'low')}",
                f"- **Basado en:** {rotation.get('sample_size', 0)} ads analizados",
                "",
            ])

        phases = latest.get("phase_distribution", {})
        if phases:
            lines.append("### Estado actual de los ads")
            phase_labels = {
                "ramp_up": "En aprendizaje",
                "peak": "Rendimiento óptimo",
                "plateau": "Estancado",
                "decline": "Decayendo",
                "exhausted": "Agotado — reemplazar",
            }
            for phase, count in phases.items():
                label = phase_labels.get(phase, phase)
                lines.append(f"- {label}: {count} ads")

        # Tendencia histórica
        if len(self._history) > 1:
            lines.extend(["", "### Evolución histórica"])
            for snap in self._history[-5:]:
                dp = snap.get("avg_decay_point", "?")
                lines.append(f"- {snap['date'][:10]}: decay promedio día {dp}, {snap['total_ads']} ads")

        return "\n".join(lines)
