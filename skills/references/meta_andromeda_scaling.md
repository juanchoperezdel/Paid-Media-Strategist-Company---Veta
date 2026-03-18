# Sistema Andromeda 1 — Escalamiento Avanzado de Meta Ads

Metodología de escalamiento para Meta Ads basada en el sistema de entrega Andromeda de Meta. Prioriza similitud sobre escala, GPT (Gross Profit per Transaction) sobre ROAS, y consolidación sobre fragmentación.

## Principio Fundamental

> *Meta Andromeda castiga el caos. Optimiza buscando miles de usuarios que se comporten igual (similitud). Lanzar "packs creativos" constantes fragmenta el aprendizaje. Dejá que los anuncios vivan y recojan datos.*

## Diagnóstico Pre-Escalamiento

### 1. Auditoría de Tracking Offline

- El ROAS y CAC nativos de Meta son engañosos — no reflejan la calidad real del cliente adquirido
- Validar si se usan herramientas de tracking offline (Ammeris/Aimerc, Zapier, Blot Out, Disruptor Tools)
- El dato clave es: **¿cuántos Nuevos Clientes vs. Recurrentes trae cada anuncio?**
- Sin este dato, se optimiza para vanity metrics

### 2. Auditoría de Flujo de Caja (Hero Products)

- Ignorar el margen de la primera compra
- Buscar los productos que generan la mayor **tasa de segunda compra** en el menor tiempo posible
- Estos son los "Hero Products" — los que alimentan el negocio a largo plazo
- Escalar adquisición de clientes que compran Hero Products, no los de mayor margen inmediato

## Estructura Andromeda 1

### Consolidación en 1 Campaña

| Adset | Rol | Contenido |
| :--- | :--- | :--- |
| **Adset 1 (Control)** | Anuncios estables y probados | Solo ads que han demostrado GPT positivo y atraen nuevos clientes |
| **Adset 2 (Test A)** | Test aislado | Un anuncio nuevo en formato 3:2:2 |
| **Adset 3 (Test B)** | Test aislado | Otro anuncio nuevo en formato 3:2:2 (opcional) |

### Formato 3:2:2

- **3 creativos** (variaciones visuales/video)
- **2 textos** (variaciones de copy primario)
- **2 titulares** (variaciones de headline)

Meta combina automáticamente para encontrar la mejor combinación.

## Pre-entrenamiento de la IA

- Configurar campañas de **engagement** (bajo presupuesto ~$2-5/día) para cada post orgánico de Instagram
- Esto enseña a Andromeda quién está interesado antes de pedir conversiones frías
- Reduce CPM y aumenta AOV cuando se escala la campaña de conversiones
- Es inversión en señal, no en resultados directos

## Reglas de Testing

### Test de Estrés (Control)

En el Adset 1 (Control):
1. Identificar anuncios que consumen presupuesto pero tienen GPT bajo
2. Identificar anuncios que atraen mayormente clientes recurrentes (no nuevos)
3. Apagar estos anuncios — están "comiendo" presupuesto sin generar crecimiento

### Evaluación de Tests (Regla de Hierro)

Un test NUNCA busca ganar la campaña ni validación a corto plazo. Evaluación binaria:

| Resultado | Veredicto | Acción |
| :--- | :--- | :--- |
| El nuevo ad **no logra gastar** presupuesto | FALLA | Meta no le encuentra audiencia. Apagar |
| El nuevo ad gasta pero **GPT total de la campaña baja** | FALLA | El ad atrae tráfico pero empeora la eficiencia global. Apagar inmediatamente |
| El nuevo ad gasta Y **GPT total de la campaña sube** | GANA | Mover al Control, apagar el peor ad del Control |

> *Se evalúa el macro (GPT total de campaña), no el micro (CPA del ad individual).*

## Gestión de Catálogos (Advantage+/DPA)

### Reglas Clave

- **NO separar creativos en diferentes adsets** — poner TODOS los creativos en todos los adsets relevantes para un test multivariante real
- Auditar entrega por **Product ID**: si un producto gasta >10% del presupuesto pero su landing page tiene mala conversión → excluir con Custom Labels
- Crear catálogos dedicados con Custom Labels para productos probados en adquisición de Nuevos Clientes

### Custom Labels

| Label | Uso |
| :--- | :--- |
| **Hero Products** | Productos con alta tasa de segunda compra |
| **New Customer Acquisition** | Productos que atraen nuevos clientes (no recurrentes) |
| **Exclude** | Productos con alto gasto y baja conversión en landing |

## Diagnóstico de Problemas de Escalamiento

| Problema | Causa Probable | Acción |
| :--- | :--- | :--- |
| ROAS colapsa al subir presupuesto | Demasiados adsets fragmentando el aprendizaje | Consolidar en Andromeda 1 |
| CPMs altos y crecientes | Fatiga publicitaria, demasiados ads activos | Reducir ads activos, dejar solo los de GPT positivo |
| Muchos clientes recurrentes vía ads | Ads apuntando a base existente en vez de nuevos | Usar tracking offline para separar nuevos vs recurrentes |
| Tests siempre "pierden" | Se evalúa CPA individual en vez de GPT campaña | Cambiar a evaluación macro con Regla de Hierro |

## Implicaciones para el Análisis

- **GPT sobre ROAS**: El ROAS no dice si estás creciendo o reciclando la base existente
- **Consolidación sobre fragmentación**: Menos campañas y adsets = más señal para Andromeda = mejor delivery
- **Nuevos Clientes como KPI**: Sin distinguir nuevos de recurrentes, toda métrica de eficiencia es potencialmente engañosa
- **Patience over action**: Andromeda necesita tiempo para encontrar similitud. Editar constantemente rompe el proceso
- **Pre-training works**: Las campañas de engagement son inversión en señal, no gasto
