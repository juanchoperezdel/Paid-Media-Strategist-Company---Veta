# Veta Strategist AI — Project Memory

> **Instrucción:** Leer este archivo al inicio de cada conversación. Actualizarlo antes de terminar (ver sección Log de Sesiones).

---

## Quick Index
- [Qué es](#qué-es) — sistema multi-agente de paid media
- [Arquitectura](#arquitectura) — orchestrator + 6 agentes + skills
- [Slash Commands](#slash-commands) — `/veta-*` para usar en Claude Code
- [Clientes](#clientes) — data y hallazgos por cliente
- [Estado](#estado-actual) — qué está listo y qué falta
- [Log](#log-de-sesiones) — historial de cambios por sesión

---

## Qué es
Sistema multi-agente de Paid Media Strategy para la agencia **Veta**. Analiza cuentas de Google Ads y Meta Ads. Dos modos:
1. **Manual (ahora):** Slash commands en Claude Code + pegar data o URL de Sheets
2. **Automático (futuro):** Python + Anthropic API con scheduler

## Arquitectura

```
                    ┌─ Google Ads MCP (19 cuentas)
Data Sources ───────┤
                    └─ Meta Ads CLI (31 cuentas)
                              ↓
              ┌─ Sheets URL (manual, Claude Code)
Ingesta ──────┤
              └─ data_fetcher.py (automático, API directo)
                              ↓
              ┌─ Drive: Veta/{cliente}/data/ (CSV crudo)
Storage ──────┤
              └─ Drive: Veta/{cliente}/reportes/ (Google Docs)
                              ↓
              ┌─ Web App Streamlit (equipo, on-demand)
Interfaces ───┤─ Claude Code slash commands (manual)
              └─ Cron semanal (GitHub Actions, automático)
```

### Sub-agentes
| # | Agente | Skill | Python | Modelo |
|---|--------|-------|--------|--------|
| 1 | Historical Analyst | `market-historical.md` | `historical_analyst.py` | Sonnet |
| 2 | Ads Detector | `market-ads.md` | `ads_detector.py` | Sonnet |
| 3 | Creative Intel | `market-creative.md` | `creative_intel.py` | Opus |
| 4 | Data Auditor | `market-audit-data.md` | `data_auditor.py` | Sonnet |
| 5 | Risk Detector | `market-risk.md` | `risk_detector.py` | Sonnet |
| 6 | Task Generator | `market-tasks.md` | `task_generator.py` | Sonnet |
| 7 | Lifecycle Expert | `market-lifecycle.md` | `lifecycle_expert.py` | Sonnet |

Synthesizer usa `market.md` con Opus. Docs de referencia Meta en `skills/references/` (9 docs del repo `mathiaschu/meta-ads-analyzer`).

### Storage
- **SQLite** (`output/{cliente}/data.db`): tablas ad_daily, ad_metadata, lifecycle_snapshots, conclusions, rotation_history
- **CSVs** (`output/{cliente}/data/`): data cruda de APIs
- **Reportes** (`output/{cliente}/{plataforma}/{año}/`): análisis en markdown

## Slash Commands

| Comando | Qué hace | Acepta URL de Sheets |
|---------|----------|---------------------|
| `/veta-analyze` | Análisis completo | ✅ |
| `/veta-risk` | Chequeo rápido de riesgos | ✅ |
| `/veta-ads` | Ads ganadores/perdedores | ✅ |
| `/veta-creative` | Inteligencia creativa + ideas | ✅ |
| `/veta-audit` | Auditoría de data cross-platform | ✅ |
| `/veta-tasks` | Generar to-do list accionable | ✅ |

Los Sheets deben tener sharing "Cualquier persona con el link puede ver".

---

## Clientes

### Andesmar (turismo/viajes)
- **Plataforma:** Meta Ads
- **Moneda:** ARS
- **Gasto mensual:** ~ARS 2.5M
- **Data disponible:** Enero + Febrero 2026 (nivel campaña)
- **Sheets:**
  - Enero 2026: `17BYwdDx-sjYsNLCbYrwERZiMdq6E75fm`
  - Febrero 2026: `16dm38b8Wx7Dv5oWzDVBMgsrEe1L7md6G`
- **Formato columnas:** español (Meta Ads Manager export)
- **Hallazgos clave (Feb 2026):**
  - Frecuencia excesiva en Golondrina (4.75) y Destinos Nacionales (5.26)
  - ROAS cayó en 6/7 campañas de compras vs enero
  - Campañas Advantage chicas (Música, MZA_CL) mejorando — candidatas a escalar
  - No hay remarketing activo (oportunidad grande)
  - Attribution inconsistente entre campañas
  - ROAS reportado muy alto (60-140x) — verificar pixel/eventos duplicados
- **Acciones recomendadas:**
  1. Rotar creativos en Golondrina + Destinos Nacionales
  2. Redistribuir presupuesto hacia Advantage Música y MZA_CL
  3. Activar remarketing
  4. Estandarizar attribution a 7d clic + 1d vista
  5. Auditar pixel de compra

---

## Estado actual
- ✅ Estructura completa del proyecto
- ✅ 7 skills con prompts expertos + 9 docs referencia Meta
- ✅ 6 sub-agentes Python + synthesizer + reportes (MD + PDF)
- ✅ Slash commands funcionando en Claude Code con lectura de Sheets por URL
- ✅ CLAUDE.md con regla de auto-guardado de memory
- ✅ Primer análisis real ejecutado (Andesmar, Ene-Feb 2026)
- ✅ Web App Streamlit (app.py) con login, análisis, chat on-demand, reportes
- ✅ Google Drive client (drive_client.py) — carpetas por cliente, sube reportes como Docs
- ✅ Data Fetcher (data_fetcher.py) — baja data de Google Ads + Meta via API
- ✅ Cron semanal (cron_weekly.py) + GitHub Action (lunes 8am AR)
- ✅ Chat on-demand para preguntas del equipo sobre clientes
- ✅ Dependencias instaladas (pip install -r requirements.txt)
- ✅ Config Andesmar creada (google_ads_id + meta_ads_id)
- ✅ Chat usa OpenRouter con modelos gratis (Nemotron 120B)
- ✅ Chat lee reportes locales + CSVs como contexto
- ✅ Sección Data cruda en web (tablas, búsqueda, descarga CSV)
- ✅ Creative Lifecycle Analyzer — mide vida útil de ads, aprende con el tiempo
- ✅ Insights diarios por ad (frecuencia, CTR, CPA) para detección real de fatiga
- ✅ Sub-agente Lifecycle Expert — analiza decay, correlación ediciones, producción creativa
- ✅ SQLite storage — data.db por cliente (ad_daily, metadata, snapshots, conclusions, rotation)
- ✅ Correlación ediciones ↔ decay (detecta si decay fue por edición o fatiga orgánica)
- ✅ Conclusiones semanales comparativas (vs semana anterior, historial 6 meses)
- ✅ Chat lee conclusiones + rotación histórica de SQLite como contexto
- ✅ Web Lifecycle: muestra historial, gráfico de rotación, impacto de ediciones
- ⬜ Configurar Google credentials (service account con scope Drive + Docs)
- ⬜ Bajar primera tanda de data real via APIs (probar data_fetcher)
- ⬜ Configurar secrets en GitHub para el cron automático
- ⬜ Deploy Streamlit Cloud (opcional, ~$5/mes)

---

## Log de Sesiones

### 2026-03-16 — Sesión 1: Setup completo + primer análisis
- Creado proyecto desde cero: estructura, config, 6 agentes Python, 7 skills, reportes
- Incorporados 9 docs de referencia de Meta (repo mathiaschu/meta-ads-analyzer)
- Mejorados skills con Breakdown Effect, Learning Phase, fluctuaciones normales vs preocupantes
- Creados 6 slash commands (`/veta-*`) para uso manual en Claude Code
- Skills actualizados para leer Google Sheets directo por URL (WebFetch CSV)
- Primer análisis real: cliente Andesmar (turismo/viajes), Meta Ads Ene-Feb 2026
- Hallazgos principales: frecuencia excesiva, ROAS cayendo, campañas Advantage mejorando
- Creado CLAUDE.md con regla de auto-guardado de memory
- Reestructurado memory.md con índice, sección clientes, y log de sesiones

### 2026-03-17 — Sesión 2: Web App + Drive + Cron semanal
- **Decisiones:** Reportes en Google Docs, solo equipo interno, Google Ads + Meta
- **Archivos nuevos creados:**
  - `app.py` — Web app Streamlit (login, análisis, chat on-demand, reportes, data)
  - `src/data/drive_client.py` — Cliente Google Drive (carpetas, subir reportes como Docs, CSVs)
  - `src/data/data_fetcher.py` — Baja data de Google Ads (GAQL) y Meta Ads (CLI)
  - `src/web/auth.py` — Login simple con contraseña
  - `src/web/chat.py` — Chat on-demand con Claude usando data del cliente
  - `cron_weekly.py` — Script semanal: fetch → análisis → reporte en Drive
  - `.github/workflows/weekly-report.yml` — GitHub Action cada lunes 8am AR
  - `scripts/google_ads_query.py` — Helper para queries GAQL directas
- **Archivos modificados:**
  - `src/orchestrator.py` — Acepta `preloaded_data` (no solo Sheets)
  - `requirements.txt` — Agregado streamlit, google-api-python-client, google-auth-httplib2
  - `config/settings.yaml` — Agregada sección drive + web (password)
  - `config/clients/ejemplo_cliente.yaml` — Agregados google_ads_id y meta_ads_id
- **Pendiente:** Instalar deps, configurar credentials, test end-to-end

### 2026-03-17 — Sesión 3: Chat OpenRouter + Data cruda + Lifecycle
- **Chat:** Cambiado de Claude API a OpenRouter (gratis). Backend: nvidia/nemotron-3-super-120b-a12b:free
- **Chat contexto:** Ahora lee reportes locales de output/ + CSVs de data cruda. Fallback chain: openrouter → ollama → claude
- **Data cruda:** Nueva sección en web con tablas interactivas, búsqueda y descarga CSV
- **Andesmar config:** Creado config/clients/andesmar.yaml con IDs reales (Google: 3945728157, Meta: 160070906181703)
- **Creative Lifecycle Analyzer** (src/utils/lifecycle.py):
  - Mide vida útil de cada ad analizando curva de CTR, frecuencia y CPA diarios
  - Fases: ramp_up → peak → plateau → decline → exhausted
  - Calcula ventana óptima de rotación (percentil 25 de decay points)
  - Acumula historial en output/{cliente}/lifecycle/history.json — mejora con cada semana
  - Integrado en web app (sección "Lifecycle") y cron semanal
- **Data Fetcher:** Agregado fetch_meta_ad_daily_insights() — insights diarios por ad con frecuencia, CTR, CPA
- **Meta Expert skill:** Actualizado con lifecycle phases + optimal rotation window
- **Cron semanal:** Ahora guarda data local + corre lifecycle analysis automáticamente

### 2026-03-17 — Sesión 4: Sub-agente Lifecycle + SQLite + Correlación ediciones
- **Decisiones:** Solo Meta por ahora, 6 meses de conclusiones para chat, SQLite como storage
- **Archivos nuevos creados:**
  - `src/agents/lifecycle_expert.py` — Sub-agente que analiza lifecycle por campaña con LLM
  - `src/data/sqlite_store.py` — SQLite storage por cliente (5 tablas, rolling cleanup 12m)
  - `skills/market-lifecycle.md` — System prompt para lifecycle expert
- **Archivos modificados:**
  - `src/utils/lifecycle.py` — Agregado: `analyze_with_metadata()` (correlación ediciones ↔ decay), `to_conclusion()` (genera resumen textual comparativo), `to_vs_previous()` (delta vs semana anterior)
  - `src/orchestrator.py` — Fase 2.5: lifecycle_expert corre después de platform experts, antes de transversal
  - `cron_weekly.py` — Guarda en SQLite + pasa lifecycle data al orchestrator
  - `src/web/chat.py` — Lee conclusiones + rotation history de SQLite como contexto
  - `app.py` — Sección Lifecycle rediseñada: lee SQLite, muestra historial, gráfico rotación, impacto ediciones
  - `config/settings.yaml` — Agregada sección lifecycle (platform, retention, conclusions_months)
- **Test end-to-end con Andesmar/Estudiantes:**
  - 7 ads analizados, rotar cada 11d (confianza media)
  - Patrón clave: ads editados decaen día 9, no editados día 21
  - 5 en decline, 2 en peak
  - Data guardada en SQLite: 227 filas diarias, 14 ads metadata
- **Hallazgo importante:** Las ediciones de ads acortan la vida útil (reseteo de Learning Phase)
