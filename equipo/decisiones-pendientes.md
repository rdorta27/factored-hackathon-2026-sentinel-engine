# Decisiones pendientes

Lo que hay que decidir, con opciones y material de apoyo. Sirve con o sin reunión.

## Cómo decidimos (propuesta)

1. Cada uno lee el material de apoyo de cada decisión y anota su preferencia en su columna (o la escribe en el canal), antes del **lunes 28/9 a las 12:00**.
2. Si hay acuerdo, la decisión queda tomada. Si no, se discute en el canal o en una llamada corta.
3. Si al final del día sigue sin acuerdo: las decisiones de un área las toma su responsable; las demás, por mayoría.
4. Al tomarse, cada decisión se registra: producto y técnicas en [decisiones](../docs/construir/decisiones/) (un archivo por decisión, con la [plantilla](../docs/construir/decisiones/_plantilla.md)); equipo en el [plan](plan.md). Después se borra de esta lista.

## Lunes 28/9

Estas bloquean el esqueleto del martes.

| # | Decisión | Opciones o propuesta | Material de apoyo | Felix | Natalia | Rubén |
|---|---|---|---|---|---|---|
| 1 | Flujo | Cuentas o pagos, tarjetas, reclamos por cargos, crédito | [Opciones de flujo](../docs/construir/flujos/opciones.md), [resumen](../docs/entender/resumen.md) | | | |
| 2 | Componente aprendido | Predictor de escalamiento, clasificador de intención, detector de fraude. Depende del flujo | [ML](../docs/construir/areas/ml.md), [métricas](../docs/construir/metricas.md) | | | |
| 4 | Responsables por área | Quién toma dos de las 4 áreas | [Tabla del equipo](plan.md#equipo), [áreas](../docs/construir/areas/) | | | |
| 5 | Seguimiento diario | Reunión de 15 min o mensaje en el canal; hora | | | | |
| 6 | Herramienta de tareas | Propuesta: [tareas.md](tareas.md) en el repo | | | | |
| 7 | Flujo de código | Pull request obligatorio o push directo a `main`; quién revisa | | | | |
| 8 | Reuniones de hito | Cuándo revisamos juntos (ej.: miércoles, viernes y domingo) | [Cronograma](plan.md#cronograma-tentativo) | | | |
| 9 | Lenguaje y framework del backend | Propuesta: Python con FastAPI | [Arquitectura](../docs/entender/arquitectura.md#stack) | | | |
| 10 | LLM | a) Azure OpenAI; qué modelo. b) propuesta de Natalia (canal, 27/9): Llama 3 en Databricks para consultas frecuentes y GPT-4o para casos ambiguos, portugués, handoff y evaluación, con un enrutador entre ambos | [Decisión 001](../docs/construir/decisiones/001-plataforma-azure.md) | | | |
| 16 | Suscripción o créditos de Azure | Quién la pone; tope de gasto y alertas | [Decisión 001](../docs/construir/decisiones/001-plataforma-azure.md) | | | |
| 17 | Visibilidad del repositorio | Privado ahora y público al final, o público desde ya (hoy está público). Incluye si `equipo/` queda en la entrega o se borra antes | [Seguridad](../docs/construir/seguridad.md#repositorio-y-despliegue-públicos) | | | |
| 12 | Almacenamiento y pipeline de datos | a) Local con DuckDB. b) propuesta de Natalia (canal, 27/9): Databricks con capas Bronze, Silver y Gold en Delta Lake sobre ADLS; la API consulta Gold por SQL Warehouse. c) Bronze, Silver y Gold con DuckDB local: el mismo patrón, sin montaje ni costo en la nube. Define la arquitectura de datos | [Dataset](../docs/entender/dataset.md), [área de datos](../docs/construir/areas/datos.md) | | | |
| 18 | Idioma de las especificaciones de OpenSpec | Propuesta: inglés, porque se entregan | [Decisión 002](../docs/construir/decisiones/002-openspec.md) | | | |

## Más adelante

| # | Decisión | Opciones o propuesta | Para cuándo |
|---|---|---|---|
| 3 | Alcance de la demo | Qué acciones hace el asistente (consultar, bloquear, abrir reclamo…) y cuáles no | Mar 29/9 |
| 11 | Frontend | Chat simple: Streamlit, Gradio o web propia | Mar 29/9 |
| 13 | Servicios de Azure | Despliegue (Container Apps o App Service), secretos (Key Vault). Con la opción b de la decisión 12: ADLS, Databricks y Unity Catalog | Mar 29/9 |
| 15 | Casos de prueba en portugués | Traducidos, sintéticos o escritos por alguien que lea portugués | Mar 29/9 |
| 20 | Quién hace la presentación y el video | El guion empieza el miércoles | Mar 29/9 |
| 14 | Tracking de experimentos | MLflow (incluido en Databricks si se elige la opción b de la decisión 12), Azure ML u otro | Mié 30/9 |
| 19 | Idioma de `docs/` en la entrega | Dejarlos en español o traducir los principales | Jue 1/10 |
