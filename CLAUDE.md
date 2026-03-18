# Veta Strategist AI — Routing Index

## Identidad
Agencia Veta. Sistema multi-agente de Paid Media Strategy. Comunicar siempre en español.
Stack: Python + Anthropic SDK. Skills como system prompts.

## Antes de trabajar → Leé SOLO lo que necesitás según la tarea:

| Si te piden... | Leé este archivo |
|---|---|
| Analizar cuenta de Google Ads | `memory.md` (sección Arquitectura) + archivo de memoria `reference_google_ads_mcp.md` |
| Analizar cuenta de Meta Ads | `memory.md` (sección Arquitectura) + archivo de memoria `reference_meta_ads_cli.md` |
| Usar /veta-* commands | `memory.md` (sección Slash Commands) |
| Info de un cliente específico | `memory.md` (sección Clientes) |
| Entender cómo funciona todo el sistema | Archivo de memoria `reference_system_architecture.md` |
| Guardar o buscar reportes | `output/README.md` |
| Web app / Streamlit / Drive | `memory.md` (sección Estado actual) |
| Qué está pendiente / estado del proyecto | `memory.md` (sección Estado actual) |
| Historial de cambios | `memory.md` (sección Log de Sesiones) |
| Construir algo nuevo en el proyecto | `memory.md` completo (para contexto full) |

NO leas `memory.md` completo salvo que la tarea lo requiera. Usá las secciones específicas.

## Reglas fijas (siempre aplican)
- Reportes → `output/{cliente}/{plataforma}/{año}/{periodo}_{tipo}.md`. Leer `output/README.md` para convención exacta.
- Revisar reportes previos del mismo cliente como baseline antes de analizar.
- Nunca juzgar segmentos de Meta por CPA promedio solo (Breakdown Effect).
- Chequear Learning Phase antes de declarar ganadores/perdedores.
- Fluctuación normal: 20-30% diario. Preocupante: >50% sostenido.
- Docs de referencia de Meta en `skills/references/`.

## Regla de Memoria (OBLIGATORIO)
**Antes de terminar cada conversación**, actualizá `memory.md` con:
- Cambios realizados (archivos creados/modificados)
- Decisiones tomadas y por qué
- Data nueva analizada
- Problemas encontrados y soluciones
- Actualizar pendientes (⬜ → ✅)
Formato: agregar al final de `## Log de Sesiones` con fecha y resumen corto.

## Skills → `.claude/skills/veta-*.md`
## Docs referencia Meta → `skills/references/`
