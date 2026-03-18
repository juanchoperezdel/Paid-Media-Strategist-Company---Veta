# Budget Optimization (Google Ads)

Cómo Google maneja presupuestos y cómo diagnosticar y resolver problemas de limitación presupuestaria.

## Mecánicas de Presupuesto

- Google puede gastar **hasta 2x el presupuesto diario** en un día dado si detecta oportunidades
- El gasto mensual nunca excede **30.4 × presupuesto diario** (promedio mensual)
- Esto significa que días de alto tráfico pueden tener spend significativamente mayor al daily budget

## Limited by Budget

Cuando una campaña tiene status "Limited by budget":
- La campaña está perdiendo impresiones porque el presupuesto se agota antes de que termine el día
- Google muestra una estimación de presupuesto necesario para capturar toda la demanda
- **No siempre es un problema** — puede ser intencional si el ROI no justifica más gasto

## Diagnóstico

| Señal | Análisis | Acción Propuesta |
| :--- | :--- | :--- |
| Limited by budget + ROAS positivo | Hay demanda rentable sin capturar | Aumentar presupuesto gradualmente (max 20% cada 5-7 días) |
| Limited by budget + ROAS negativo | Está gastando todo en tráfico no rentable | NO aumentar presupuesto. Primero optimizar targeting/keywords/ads |
| Limited by budget + IS Lost (Budget) > 40% | Perdiendo más del 40% del mercado por presupuesto | Evaluar si la oportunidad justifica la inversión |
| No limited + IS Lost (Rank) alto | El problema no es presupuesto sino Ad Rank | Trabajar Quality Score y bid strategy |
| Budget shared entre campañas | Campañas compiten por el mismo presupuesto | Considerar presupuestos individuales para campañas clave |

## Shared Budgets

- Shared budgets distribuyen presupuesto entre múltiples campañas automáticamente
- **Ventaja**: Google puede mover dinero hacia campañas con más oportunidad en el día
- **Riesgo**: Una campaña de bajo rendimiento puede consumir presupuesto de una rentable
- **Recomendación**: Usar shared budgets solo entre campañas con objetivos y rendimiento similares

## Reglas de Escalamiento

| Regla | Detalle |
| :--- | :--- |
| **Incremento máximo** | 20% del presupuesto diario cada 5-7 días |
| **Por qué gradual** | Cambios bruscos reinician el learning de Smart Bidding y pueden disparar CPAs |
| **Cuándo escalar** | IS < 50-65%, campaña rentable, conversiones estables |
| **Cuándo NO escalar** | IS > 80%, CPA en suba, learning period activo |
| **Escalamiento horizontal** | Si CPCs suben sin más conversiones, crear campañas separadas para sub-segmentos |

## Implicaciones para el Análisis

- "Limited by budget" no es automáticamente malo — evaluar siempre contra rentabilidad
- El over-delivery (2x diario) puede causar alarma en reportes diarios; evaluar mensualmente
- Shared budgets obscurecen el performance individual de campañas — analizar con cuidado
- Presupuesto es una palanca de volumen, no de eficiencia — aumentar budget sin mejorar fundamentals sube CPA
