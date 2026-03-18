# Conversion Tracking (Google Ads)

El tracking de conversiones es la base de toda optimización. Sin tracking preciso, Smart Bidding, reporting y decisiones operan sobre datos incorrectos.

## Tipos de Conversiones

| Tipo | Fuente | Uso Principal |
| :--- | :--- | :--- |
| **Website actions** | Google Tag / gtag.js en el sitio | Compras, formularios, signup |
| **Phone calls** | Call tracking (Google forwarding number) | Leads por llamada |
| **App installs/actions** | Firebase / SDK | Mobile apps |
| **Imported (offline)** | CRM → Google Ads upload | Ventas cerradas, leads calificados |
| **Enhanced conversions** | Datos first-party hasheados | Mejora atribución post-cookie |

## Ventanas de Conversión

| Ventana | Default | Rango Disponible |
| :--- | :--- | :--- |
| **Click-through** | 30 días | 1, 7, 14, 30, 60, 90 días |
| **View-through** | 1 día | 1 día (solo Display/Video) |
| **Engaged-view** | 3 días | Para Video ads (usuario vio >10s) |

La ventana correcta depende del ciclo de compra:
- E-commerce impulso: 7 días click-through
- B2B / alto ticket: 30-90 días click-through
- Awareness / Video: 1 día view-through, 3 días engaged-view

## Modelos de Atribución

| Modelo | Lógica | Recomendación |
| :--- | :--- | :--- |
| **Data-Driven (DDA)** | ML asigna crédito basado en datos reales | Recomendado por Google, requiere volumen |
| **Last Click** | 100% crédito al último click | Simple pero subestima upper funnel |

> Google ha migrado todas las cuentas a Data-Driven Attribution por defecto. Last Click disponible como fallback.

## Conteo de Conversiones

| Setting | Cuándo Usar |
| :--- | :--- |
| **Every** (Todas) | E-commerce: cada compra cuenta |
| **One** (Una) | Lead gen: solo la primera conversión por click (evita contar spam/duplicados) |

## Problemas Comunes de Tracking

| Problema | Síntomas | Diagnóstico |
| :--- | :--- | :--- |
| Tag no instalado/broken | 0 conversiones, Smart Bidding errático | Google Tag Assistant, Realtime report GA4 |
| Conversiones duplicadas | Conteo = "Every" en lead gen, o tag fires múltiples veces | Verificar conteo setting, revisar tag implementation |
| Discrepancia Google Ads vs GA4 | Números no coinciden | Diferente atribución, diferente ventana, diferente timezone |
| Enhanced Conversions no configurado | Pérdida de señal post-cookie, Smart Bidding degradado | Implementar hashing de email/phone en el tag |
| Conversion delay | Conversiones aparecen días después | Normal — Google atribuye al click date, no al conversion date |

## Offline Conversion Import

Para negocios con ciclo de venta largo (B2B, automotriz, real estate):
1. Capturar GCLID en el formulario
2. Cuando el lead se convierte en venta → subir conversión con GCLID al Google Ads
3. Smart Bidding aprende qué clicks generan ventas reales, no solo leads

## Implicaciones para el Análisis

- **Conversion delay**: Los últimos 3-7 días siempre tienen datos incompletos — no alarmarse por "caídas" recientes
- Discrepancias Google Ads vs GA4 son normales (diferente modelo de atribución) — usar una fuente como truth
- Sin Enhanced Conversions configurado, se pierde ~15-30% de señal en browsers con restricciones de cookies
- El conteo incorrecto (Every vs One) puede inflar artificialmente el volumen de conversiones en lead gen
- Smart Bidding es tan bueno como el tracking — garbage in, garbage out
