# Ad Rank (Google Ads)

Ad Rank determina si tu anuncio se muestra y en qué posición. Se calcula en cada subasta en tiempo real.

## Fórmula

```
Ad Rank = Bid × Quality Score × Expected Impact of Extensions + Ad Rank Thresholds
```

## Factores

| Factor | Peso | Descripción |
| :--- | :--- | :--- |
| **Max CPC Bid** | Alto | Cuánto estás dispuesto a pagar por click (o bid automático de Smart Bidding) |
| **Quality Score** | Alto | Expected CTR + Ad Relevance + Landing Page Experience |
| **Expected Impact of Extensions** | Medio | Sitelinks, callouts, structured snippets, etc. mejoran Ad Rank |
| **Ad Rank Thresholds** | Variable | Mínimo de Ad Rank requerido para aparecer (varía por query, posición, dispositivo) |
| **Search Context** | Variable | Query, ubicación del usuario, dispositivo, hora, otros ads en la subasta |

## CPC Real vs. Max Bid

- No pagás tu Max CPC bid — pagás **el mínimo necesario para mantener tu posición**
- Fórmula: `CPC real = (Ad Rank del competidor debajo / Tu Quality Score) + $0.01`
- Quality Score alto → pagás significativamente menos que tu bid máximo
- Quality Score bajo → pagás cerca del máximo o ni entrás a la subasta

## Thresholds (Umbrales Mínimos)

Google requiere un Ad Rank mínimo para:
- Aparecer en la subasta (cualquier posición)
- Aparecer arriba de resultados orgánicos (top of page)
- Aparecer en la primera posición absoluta (absolute top)

Estos thresholds varían por:
- Competitividad de la query
- Dispositivo del usuario
- Ubicación geográfica
- Naturaleza de la búsqueda (comercial vs informacional)

## Diagnóstico

| Problema | Causa Probable | Acción Propuesta |
| :--- | :--- | :--- |
| Ad no aparece para keywords con bid alto | QS bajo o threshold alto para esa query | Revisar QS components, mejorar ad relevance |
| Posición cayendo sin cambio de bid | Competidores mejoraron su Ad Rank o thresholds subieron | Revisar Auction Insights, optimizar QS y extensions |
| CPC real muy cercano al Max bid | QS bajo fuerza a pagar más | Mejorar QS para bajar CPC real |
| Buena posición pero CTR bajo | Ad copy no compelling a pesar de buena posición | Mejorar headlines y descriptions |

## Impacto de Ad Extensions

Las extensions mejoran Ad Rank **sin costo adicional por impression**:
- **Sitelinks**: Links adicionales debajo del ad → +10-15% CTR estimado
- **Callouts**: Textos descriptivos (envío gratis, 24/7, etc.)
- **Structured Snippets**: Categorías de productos/servicios
- **Call Extension**: Botón de llamada directa
- **Location Extension**: Dirección física

> *Una cuenta sin extensions está compitiendo con desventaja estructural en Ad Rank.*

## Implicaciones para el Análisis

- Ad Rank es dinámico — cambia en cada subasta, no es un número fijo
- Mejorar Quality Score tiene mayor ROI a largo plazo que subir bids
- Extensions son "free Ad Rank" — siempre deben estar configuradas
- En subastas muy competitivas, los thresholds pueden ser tan altos que solo top advertisers participan
- Smart Bidding ajusta bids por subasta considerando Ad Rank expected — no micro-gestionar bids manualmente
