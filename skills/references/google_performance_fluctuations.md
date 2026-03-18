# Performance Fluctuations (Google Ads)

El rendimiento en Google Ads fluctúa naturalmente. Entender las causas ayuda a distinguir variación normal de problemas reales.

## Causas Comunes

| Causa | Descripción | Acción |
| :--- | :--- | :--- |
| **Smart Bidding learning** | Cambios de estrategia o presupuesto causan volatilidad | Esperar 2 semanas para estabilización |
| **Estacionalidad** | Demanda de búsqueda cambia por temporada | Comparar vs mismo período año anterior |
| **Competencia** | Nuevos competidores o cambios en pujas ajenas | Revisar Auction Insights trends |
| **Limited by budget** | Presupuesto se agota antes del fin del día | Evaluar si vale la pena aumentar budget |
| **Quality Score changes** | Cambios en QS afectan Ad Rank y CPC | Monitorear QS components semanalmente |
| **External factors** | Noticias, clima, eventos, feriados | Contextualizar con factores externos |
| **Search demand shifts** | El volumen de búsqueda cambia por tendencias | Verificar con Google Trends |

## Normal vs. Preocupante

### Normal (no requiere acción inmediata)

- CPA varía ±15-25% día a día
- CPCs fluctúan por hora del día y día de la semana
- Volumen de impressions baja en fines de semana (B2B) o entre semana (ciertos B2C)
- Spend diario varía hasta 2x del presupuesto diario
- Performance menor en primeras 2 semanas de Smart Bidding nuevo

### Preocupante (investigar)

- CPA sube >40% sostenido por 5+ días sin cambios en la cuenta
- Impression share cae >20 puntos en una semana
- Conversiones caen a cero o near-zero repentinamente
- CPC sube >30% sin cambio en QS o competencia visible
- CTR cae >25% en keywords previamente estables

## Diferencias por Tipo de Campaña

| Tipo | Variación Típica | Nota |
| :--- | :--- | :--- |
| **Search** | CPA ±15-25%, CTR estable si ad copy no cambia | Más predecible — intención clara |
| **Performance Max** | CPA ±30-40%, especialmente en primeras semanas | PMax se autoajusta agresivamente |
| **Display** | CTR y conversion rate muy volátiles | Esperar alta variación por naturaleza del canal |
| **Video** | VTR estable, conversiones volátiles | Lower funnel metrics varían más |
| **Shopping** | ROAS ±20-30%, depende fuertemente de inventario y precios | Competencia de precio directa |

## Framework de Diagnóstico

Antes de actuar ante una fluctuación:

1. **¿Cuánto tiempo lleva?** — Menos de 5 días = probablemente normal
2. **¿Hubo cambios en la cuenta?** — Bid strategy, budget, ads, keywords → esperar learning
3. **¿Cambió la competencia?** — Revisar Auction Insights últimas 4 semanas
4. **¿Es estacional?** — Comparar con mismo período del año anterior
5. **¿El tracking funciona?** — Verificar que conversiones no estén sub-reportadas
6. **¿La muestra es suficiente?** — Menos de 100 clicks o 10 conversiones = noise, no signal

## Implicaciones para el Análisis

- Evaluar Search en ventanas de 7+ días; PMax y Display en 14+ días
- No reaccionar a fluctuaciones diarias cambiando bids o budgets — esto empeora la volatilidad
- El "conversion delay" de Google (atribuye al click date) hace que los últimos 3-7 días siempre parezcan peores de lo que son
- Comparar siempre contra baseline apropiado (mismo día de semana, mismo período, excluyendo anomalías)
- Stacking de cambios (múltiples edits en poco tiempo) amplifica la volatilidad — hacer un cambio a la vez
