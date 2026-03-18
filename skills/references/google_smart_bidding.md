# Smart Bidding (Google Ads)

Smart Bidding son estrategias de puja automática que usan machine learning para optimizar conversiones o valor de conversión en cada subasta (auction-time bidding).

## Estrategias Disponibles

| Estrategia | Optimiza | Cuándo Usarla | Requisito Mínimo |
| :--- | :--- | :--- | :--- |
| **Maximize Conversions** | Volumen de conversiones | Querés máximo volumen sin target de costo | 15+ conversiones/mes |
| **Target CPA** | Conversiones a costo objetivo | Tenés CPA target claro y volumen suficiente | 30+ conversiones en 30 días |
| **Maximize Conversion Value** | Valor total de conversiones | Revenue/ROAS importa más que volumen | 15+ conversiones/mes con valores |
| **Target ROAS** | Valor a retorno objetivo | Tenés ROAS target y volumen con valores | 30+ conversiones en 30 días con valores |

## Learning Period

- Toda estrategia Smart Bidding necesita **~2 semanas** para estabilizar
- Durante el learning period, el performance puede ser volátil y los CPAs más altos
- Google necesita **mínimo 30 conversiones en 30 días** para que Target CPA/ROAS funcione bien
- Con menos de 30 conversiones, usar Maximize Conversions (sin target) como paso intermedio

## Señales que Usa Google

Smart Bidding evalúa señales en tiempo real por cada subasta:

- Device, ubicación, hora del día, día de la semana
- Query (para Search), remarketing lists, demographics
- Navegador, OS, idioma del dispositivo
- Señales de intención basadas en historial de búsqueda
- Contexto del ad (qué ad se mostraría, en qué posición)

## Errores Comunes

| Error | Consecuencia | Corrección |
| :--- | :--- | :--- |
| Target CPA demasiado bajo | Google no puede competir → delivery cae a cero | Setear target CPA al promedio histórico y bajar gradualmente (10-15% por semana) |
| Cambiar estrategia frecuentemente | Se reinicia el learning → nunca estabiliza | Dar mínimo 2 semanas entre cambios |
| Pocas conversiones con Target CPA | El algoritmo no tiene data suficiente → errático | Usar Maximize Conversions hasta acumular 30 conv/mes |
| Target ROAS en campañas con poco valor data | Algoritmo no puede optimizar por valor | Asegurar que el tracking de valor de conversión sea preciso |
| Subir presupuesto >20% de golpe | Disrumpe el modelo de pacing | Incrementos graduales de máximo 20% cada 5-7 días |

## Implicaciones para el Análisis

- No juzgar Smart Bidding en los primeros 14 días
- Evaluar performance en ventanas de 7+ días, nunca día a día
- Si el volumen de conversiones es bajo, el algoritmo puede ser errático — no es necesariamente un problema de configuración
- Comparar contra el período pre-Smart Bidding ajustando por estacionalidad
- Target CPA/ROAS son **metas, no garantías** — Google intenta promediar al target, pero habrá variación diaria
