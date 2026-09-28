# Decisiones pendientes

Lo que nos falta decidir, con opciones y material de apoyo. Sirve con o sin reunión.

## Método

Es una propuesta:

1. Cada uno lee el material de apoyo y anota su preferencia en su columna (o en el canal) antes del **lunes 28/9**.
2. Si estamos de acuerdo, queda decidido. Si no, lo hablamos en el canal o en una llamada corta.
3. Si al final del día seguimos sin acuerdo, decide el responsable del área; lo demás, por mayoría.
4. Registramos cada decisión: las de producto y técnicas en [decisiones](../docs/construir/decisiones/) (un archivo por decisión, con la [plantilla](../docs/construir/decisiones/_plantilla.md)); las del equipo en el [plan](plan.md). Después la borramos de esta lista.

## Lunes 28/9

Estas frenan el esqueleto del martes. Las más urgentes: **4** (sin responsables no arranca el cronograma), **10** (frena el trabajo de AI), **12** (el pipeline empieza hoy) y **16** (el despliegue es el jueves).

| # | Decisión | Opciones o propuesta | Material de apoyo | Felix | Natalia | Rubén |
|---|---|---|---|---|---|---|
| 1 | Flujo | Propuesta: disputas de transacciones, provisional; lo confirmamos o lo cambiamos el martes 29/9 con criterios medibles. Alternativa: tarjetas | [Decisión 003 (propuesta)](../docs/construir/decisiones/003-flujo-disputas.md), [opciones de flujo](../docs/construir/flujos/opciones.md) | | | |
| 2 | Componente aprendido | Con el flujo de disputas: clasificador de categoría del reclamo (`description` / `customer_text`) frente a palabras clave, o predictor de escalamiento (`was_escalated`) con variables de apertura. Lo elegimos en la revisión del martes junto con la decisión 1 | [ML](../docs/construir/areas/ml.md), [métricas](../docs/construir/metricas.md) | | | |
| 4 | Responsables por área | Áreas: AI (backend, frontend, despliegue), ML, Datos, Análisis. Somos 3, así que alguien toma dos | [Áreas](../docs/construir/areas/) | | | |
| 5 | Seguimiento diario | Reunión de 15 min o mensaje en el canal; hora | | | | |
| 6 | Herramienta de tareas | Propuesta: [tareas.md](tareas.md) en el repo | | | | |
| 7 | Flujo de código | Pull request obligatorio o push directo a `main`; quién revisa | | | | |
| 8 | Reuniones de hito | Cuándo revisamos juntos (ej.: miércoles, viernes y domingo) | [Cronograma](plan.md#cronograma) | | | |
| 9 | Lenguaje y framework del backend | Propuesta: Python con FastAPI | [Arquitectura](../docs/entender/arquitectura.md#stack) | | | |
| 10 | LLM | a) Azure OpenAI; qué modelo. b) propuesta de Natalia (canal, 27/9): Llama 3 en Databricks para consultas frecuentes y GPT-4o para casos ambiguos, portugués, handoff y evaluación, con un enrutador entre ambos | [Decisión 001](../docs/construir/decisiones/001-plataforma-azure.md) | | | |
| 16 | Suscripción o créditos de Azure | Quién la pone; tope de gasto y alertas | [Decisión 001](../docs/construir/decisiones/001-plataforma-azure.md) | | | |
| 17 | Visibilidad del repositorio | Privado ahora y público al final, o público desde ya (hoy está público). Incluye si `team/` queda en la entrega o se borra antes | [Seguridad](../docs/construir/seguridad.md#repositorio-y-despliegue-públicos) | | | |
| 12 | Almacenamiento y pipeline de datos | a) Local con DuckDB. b) propuesta de Natalia (canal, 27/9): Databricks con capas Bronze, Silver y Gold en Delta Lake sobre ADLS; la API consulta Gold por SQL Warehouse. c) Bronze, Silver y Gold con DuckDB local: el mismo patrón, sin montaje ni costo en la nube. Define la arquitectura de datos | [Dataset](../docs/entender/dataset.md), [área de datos](../docs/construir/areas/datos.md) | | | |
| 18 | Idioma de las especificaciones de OpenSpec | Propuesta: inglés, porque se entregan | [Decisión 002](../docs/construir/decisiones/002-openspec.md) | | | |

## Más adelante

| # | Decisión | Opciones o propuesta | Para cuándo |
|---|---|---|---|
| 3 | Alcance de la demo | Qué acciones hace el asistente (consultar, bloquear, abrir reclamo…) y cuáles no | Mar 29/9 |
| 11 | Frontend | Chat simple: Streamlit, Gradio o web propia | Mar 29/9 |
| 13 | Servicios de Azure | Despliegue (Container Apps o App Service), secretos (Key Vault). Con la opción b de la decisión 12: ADLS, Databricks y Unity Catalog | Mar 29/9 |
| 15 | Casos de prueba en portugués | Traducidos, sintéticos o escritos por alguien que lea portugués. El dataset está solo en español: definir también quién los revisa | Mar 29/9 |
| 20 | Quién hace la presentación y el video | El guion empieza el miércoles | Mar 29/9 |
| 14 | Tracking de experimentos | MLflow (incluido en Databricks si se elige la opción b de la decisión 12), Azure ML u otro | Mié 30/9 |
| 19 | Idioma de `docs/` en la entrega | Dejarlos en español o traducir los principales | Jue 1/10 |
