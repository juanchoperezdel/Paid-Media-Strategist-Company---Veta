# Auction Insights (Google Ads)

Auction Insights compara tu performance en subastas contra otros anunciantes que compiten por las mismas queries. Es la ventana principal a la dinámica competitiva.

## Métricas Disponibles

| Métrica | Qué Mide | Interpretación |
| :--- | :--- | :--- |
| **Impression Share** | % de impresiones que recibiste vs. las que podías recibir | Tu cuota del mercado visible |
| **Overlap Rate** | Frecuencia con que un competidor aparece cuando vos aparecés | Quién compite directamente contigo |
| **Position Above Rate** | Frecuencia con que un competidor aparece arriba tuyo | Quién te gana en posición |
| **Top of Page Rate** | % de veces que tu ad aparece arriba de resultados orgánicos | Visibilidad premium |
| **Abs. Top of Page Rate** | % de veces en la primera posición absoluta | Dominio de SERP |
| **Outranking Share** | % de veces que tu ad rankeó arriba del competidor o apareció cuando ellos no | Tu ventaja competitiva neta |

## Diagnóstico Competitivo

| Escenario | Indica | Acción Propuesta |
| :--- | :--- | :--- |
| Impression Share cayendo | Perdiendo visibilidad (presupuesto o rank) | Revisar IS lost by budget vs rank |
| Nuevo competidor con alto Overlap Rate | Entrada de competidor agresivo | Monitorear impacto en CPCs y conversion rates |
| Position Above Rate alto de un competidor | Te están superando consistentemente | Evaluar si conviene competir (ROI) o diferenciarse |
| Tu Top of Page Rate < 50% | Ads aparecen mayormente debajo | Revisar Ad Rank: Quality Score + bids |
| Outranking Share bajando | Perdiendo terreno competitivo | Análisis integral: QS + bid + extensions |

## Impression Share Breakdown

```
Total Impression Share = 100% - IS Lost (Budget) - IS Lost (Rank)
```

| Pérdida | Causa | Solución |
| :--- | :--- | :--- |
| **IS Lost (Budget)** | Presupuesto diario insuficiente para capturar toda la demanda | Aumentar presupuesto o reducir scope (geo, schedule, keywords) |
| **IS Lost (Rank)** | Ad Rank bajo (QS y/o bid insuficientes) | Mejorar Quality Score, ajustar bids, agregar extensions |

## Umbrales de Referencia

- **IS < 30%**: Estás perdiendo la mayoría del mercado — evaluar si el presupuesto es realista para el scope
- **IS 30-50%**: Hay margen significativo de crecimiento
- **IS 50-70%**: Buena presencia, escalamiento posible
- **IS > 70%**: Dominando el mercado — escalar puede tener rendimientos decrecientes
- **IS > 90%**: Saturación — considerar expansión horizontal (nuevos keywords, geos)

## Implicaciones para el Análisis

- Auction Insights es relativo — un competidor puede tener alto overlap por razones temporales
- Usar tendencias de 4+ semanas, no snapshots puntuales
- IS alto no garantiza conversiones — es una métrica de visibilidad, no de eficiencia
- En campañas con presupuesto limitado, un IS bajo es esperado y no necesariamente problemático
- Performance Max no ofrece Auction Insights — solo Search y Shopping
