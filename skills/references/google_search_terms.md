# Search Terms & Match Types (Google Ads)

El informe de términos de búsqueda muestra las queries reales que activaron tus anuncios. Es la herramienta más importante para controlar relevancia y evitar gasto desperdiciado.

## Match Types

| Match Type | Símbolo | Comportamiento | Ejemplo (keyword: zapatos running) |
| :--- | :--- | :--- | :--- |
| **Broad Match** | keyword | Máximo alcance, Google interpreta intención | Activa: "mejores zapatillas para correr", "calzado deportivo" |
| **Phrase Match** | "keyword" | Query debe incluir el significado del keyword | Activa: "comprar zapatos running baratos", "zapatos running mujer" |
| **Exact Match** | [keyword] | Query debe tener la misma intención exacta | Activa: "zapatos running", "zapatos para running" (close variants) |

## Close Variants

Google expande TODOS los match types con close variants:
- Plurales, typos, sinónimos, reordenamiento de palabras
- En Exact Match, puede matchear queries con la **misma intención** aunque las palabras difieran
- Esto hace que la revisión de search terms sea obligatoria incluso con Exact Match

## Análisis del Search Terms Report

### Señales de Alerta

| Señal | Indica | Acción |
| :--- | :--- | :--- |
| Queries totalmente irrelevantes | Broad Match demasiado amplio | Agregar negativas, considerar Phrase/Exact |
| Queries informacionales (cómo, qué es) | Tráfico sin intención de compra | Agregar como negativa o crear campaña informacional separada |
| Queries de marca de competidores | Puede ser costoso e ineficiente | Evaluar ROI; si no convierte, agregar como negativa |
| Queries duplicadas entre campañas | Canibalización interna | Agregar negativas cruzadas entre campañas |
| >30% de queries sin conversión | Segmentación demasiado amplia | Restringir match types, expandir negativas |

### Proceso de Revisión

1. Filtrar search terms por los últimos 7-14 días
2. Ordenar por gasto (mayor a menor)
3. Identificar queries de alto gasto sin conversiones
4. Verificar relevancia de queries de alto volumen
5. Agregar negativas para queries irrelevantes
6. Identificar queries de alto rendimiento para agregar como keywords exactos

## Negative Keywords

| Nivel | Uso |
| :--- | :--- |
| **Campaign level** | Excluir queries irrelevantes para toda la campaña |
| **Ad group level** | Controlar qué ad group captura cada query (evitar canibalización) |
| **Negative keyword lists** | Listas compartidas entre campañas (ej: "gratis", "empleo", "tutorial") |

## Implicaciones para el Análisis

- Revisión de search terms debe ser **mínimo semanal** para campañas Broad Match
- El % de gasto en queries irrelevantes es un indicador clave de salud de campaña
- Campañas Performance Max no muestran search terms completos — solo insights limitados
- Close variants pueden expandirse de formas inesperadas; monitorear activamente
- Un keyword con buen QS pero search terms malos = problema de match type, no de keyword
