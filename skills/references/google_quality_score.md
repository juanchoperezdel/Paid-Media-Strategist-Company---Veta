# Quality Score (Google Ads)

Quality Score es la estimación de Google sobre la calidad de tus anuncios, keywords y landing pages. Escala de 1 a 10, afecta directamente el Ad Rank y el CPC real que pagás.

## Componentes

| Componente | Mide | Impacto |
| :--- | :--- | :--- |
| **Expected CTR** | Probabilidad de que el ad reciba click dado que se muestra | Alto — indica relevancia del ad para la query |
| **Ad Relevance** | Qué tan bien el ad matchea la intención del keyword | Medio — asegura coherencia keyword-ad |
| **Landing Page Experience** | Utilidad, relevancia y velocidad de la landing | Alto — Google prioriza experiencia post-click |

## Cómo Impacta el Ad Rank

```
Ad Rank = Bid × Quality Score × Expected Impact of Extensions
```

- **Quality Score alto (7-10)**: Pagás menos por posiciones altas. CPC real puede ser significativamente menor al bid máximo.
- **Quality Score bajo (1-4)**: Pagás premium o directamente no entrás a la subasta. Google puede no mostrar tu ad aunque tengas bid alto.
- **Quality Score medio (5-6)**: Competitivo pero sin ventaja. Hay espacio de mejora claro.

## Diagnóstico por Componente

| Escenario | Problema Probable | Acción |
| :--- | :--- | :--- |
| Expected CTR bajo | Ad copy no compelling para la query | Mejorar headlines, incluir keyword en ad copy, usar CTAs más fuertes |
| Ad Relevance bajo | Keyword demasiado broad o ad genérico | Agrupar keywords por intención, crear ads específicos por ad group |
| Landing Page Experience bajo | Página lenta, no relevante, o mala UX mobile | Optimizar velocidad, alinear contenido landing-keyword, mejorar mobile |
| Los tres bajos | Mismatch estructural keyword-ad-landing | Reestructurar ad group: keywords tight → ad específico → landing dedicada |

## Umbrales de Acción

- **QS ≤ 3**: Acción urgente — el keyword está sangrando presupuesto por CPC inflado
- **QS 4-5**: Revisar componentes individuales, optimizar el más débil
- **QS 6**: Aceptable, pero optimizable — revisar si landing page puede mejorar
- **QS 7+**: Buen estado — mantener y monitorear

## Implicaciones para el Análisis

- Quality Score es un **indicador rezagado** — refleja performance histórica, no predicción
- No optimizar Quality Score directamente; optimizar sus componentes
- Un keyword con QS bajo pero conversiones altas puede merecer mantenerse (evaluar ROI neto)
- QS no aplica a campañas Performance Max ni Display (solo Search)
