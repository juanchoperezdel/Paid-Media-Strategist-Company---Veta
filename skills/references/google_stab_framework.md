# Framework STAB — Auditoría y Optimización de Google Ads

Framework heurístico para diagnosticar y optimizar cuentas de Google Ads. Complementa el análisis de datos con revisiones de configuración que frecuentemente se pasan por alto.

## Diagnóstico Inicial: Tráfico vs. Landing

Antes de tocar la cuenta, determinar dónde está el problema:

| Tiempo de sesión | Diagnóstico | Acción |
| :--- | :--- | :--- |
| **< 30 segundos** | Problema de segmentación/Google Ads | Optimizar targeting, keywords, ads |
| **> 60 segundos** | Problema de oferta/Landing Page | Optimizar landing page, CRO, oferta |
| **30-60 segundos** | Zona gris | Evaluar ambos frentes |

## Auditoría de Semáforo

### Verde (Escalar lo que funciona)
- Identificar campañas/ad groups/keywords que **ya generan conversiones rentables**
- Aumentar presupuesto en lo verde primero — es la fruta más baja
- Validar que hay Impression Share disponible para capturar antes de escalar

### Amarillo (Importante, no urgente)
- Expansión a Demand Gen, Video, nuevas audiencias
- Tests de nuevos ad copy o landing pages
- Expansión geográfica o de horarios
- Configuraciones no óptimas que no están causando pérdida activa

### Rojo (Urgente, arreglar ya)
- Canibalización entre campañas (keywords compitiendo entre sí)
- Gasto significativo en productos/servicios sin retorno
- Configuraciones que causan pérdida activa de presupuesto
- Tracking roto o mal configurado

## Revisiones Críticas (Configuraciones Ocultas)

Estas configuraciones incorrectas son comunes y causan pérdida de presupuesto silenciosa:

| Configuración | Problema | Acción |
| :--- | :--- | :--- |
| **Auto-apply recommendations** | Google cambia pujas, keywords, y targeting sin supervisión | Desactivar SIEMPRE. Revisar recomendaciones manualmente |
| **Location targeting: "Presence or Interest"** | Muestra ads a personas "interesadas" en la ubicación pero que no están ahí | Cambiar a "Presence" (presencia física). Solo usar "Interest" si es campaña de turismo |
| **Conversion counting: "Every"** | En lead gen, cuenta múltiples envíos del mismo usuario como conversiones separadas | Cambiar a "One" para lead gen. Mantener "Every" solo para e-commerce |
| **PMax sin Brand Exclusions** | PMax toma crédito de búsquedas de marca que habrían convertido orgánicamente | Añadir exclusiones de marca a nivel cuenta |

## STAB: Las 4 Palancas

### S — Spending (Gasto y Segmentación)
- Aislar productos/servicios que consumen >20% del presupuesto sin generar conversiones
- Crear campañas separadas para forzar gasto en lo rentable
- Separar por ubicación geográfica si hay diferencias de rendimiento significativas
- No dejar que PMax "esconda" gasto ineficiente en segmentos no visibles

### T — Targeting (Segmentación)
- Revisar Search Terms report mínimo semanalmente
- Agregar negativas agresivamente para queries irrelevantes
- Desactivar "Optimized Targeting" en Video/Demand Gen cuando se usan audiencias específicas (ej: remarketing de carritos abandonados)
- Verificar que los match types sean apropiados para el presupuesto disponible

### A — Ads (Anuncios y Landing Pages)
- **CTR benchmark Search: ~10%**. Si CTR < 5%, el ad copy necesita mejora urgente
- Usar pre-cualificación agresiva en el ad copy (ej: "Desde $99", "Solo empresas B2B") para evitar clicks sin intención
- Alinear mensaje del ad con la landing page — coherencia keyword → ad → landing
- Mínimo 3 RSA (Responsive Search Ads) por ad group con pins estratégicos

### B — Bidding (Pujas)
- Asegurar mínimo 10-30 clicks diarios por campaña para que Smart Bidding tenga señal
- Smart Bidding necesita ~30 conversiones en 30 días para funcionar correctamente
- Si no hay volumen suficiente: usar Maximize Clicks o Manual CPC como paso intermedio
- No cambiar estrategia de puja y presupuesto al mismo tiempo — un cambio a la vez

## Escalamiento Rentable

### Checklist Pre-Escalamiento

1. **Search Impression Share < 50-65%**: Hay espacio para crecer verticalmente
2. **Campaña rentable**: ROAS o CPA dentro de target sostenido por 2+ semanas
3. **Conversiones estables**: Sin caídas ni picos anómalos recientes
4. **Tracking validado**: Conversiones reflejan realidad del negocio

### Reglas de Escalamiento

| Tipo | Método | Cuándo |
| :--- | :--- | :--- |
| **Vertical** | Aumentar budget máximo 20% cada 5-7 días | IS < 65% y campaña rentable |
| **Horizontal** | Crear campañas separadas por sub-categorías, geos, o audiencias | CPCs suben sin más conversiones (resistencia de CPC) |

## Implicaciones para el Análisis

- Siempre empezar por el diagnóstico tráfico vs landing antes de optimizar la cuenta
- Las configuraciones ocultas (auto-apply, location targeting, conversion counting) pueden explicar bajo rendimiento sin que el problema sea de keywords o bidding
- La auditoría de semáforo prioriza acciones: verde primero (más revenue), rojo segundo (detener pérdida), amarillo después
- El framework STAB es un ciclo, no un evento: revisar cada dimensión regularmente
