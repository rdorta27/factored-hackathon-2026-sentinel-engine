# Tareas

Quién hace qué y para cuándo, ordenado por día. Al tomar una tarea, poner el nombre; al terminarla, marcarla. Si la tarea cubre un requerimiento, citar su `REQ-####` y actualizar su estado en los [requerimientos](../docs/requerimientos/requerimientos.md).

**Estados:** Pendiente, En curso, Hecho.

## Resumen

Metas e hitos de cada día en el [cronograma del plan](plan.md#cronograma-tentativo). Flujo de trabajo: disputes, provisional hasta la revisión del martes ([decisión 003](../docs/construir/decisiones/003-flujo-disputes.md)).

| Día | Hito | Tareas |
|---|---|---|
| Lun 28/9 | Decisiones registradas; primeras mediciones de datos | [Ver](#lun-289-decidir-y-medir) |
| Mar 29/9 | Flujo confirmado; el esqueleto responde de punta a punta | [Ver](#mar-299-confirmar-y-esqueleto) |
| Mié 30/9 | Un caso funciona completo | [Ver](#mié-309-caso-normal) |
| Jue 1/10 | 3 casos en ES y PT, link público | [Ver](#jue-110-casos-difíciles-y-despliegue) |
| Vie 2/10 | Listo para enviar | [Ver](#vie-210-evaluación-y-entrega) |
| Sáb 3/10 a lun 5/10 | Entregado | [Ver](#sáb-310-a-lun-510-margen) |

## Lun 28/9: decidir y medir

| Tarea | Responsable | Estado |
|---|---|---|
| Completar la [tabla del equipo](plan.md#equipo): fortalezas y disponibilidad | Cada uno | Pendiente |
| Anotar la preferencia en las [decisiones pendientes](decisiones-pendientes.md) | Cada uno | Pendiente |
| Confirmar que las credenciales de S3 funcionan para los 3 (Natalia ya las probó) | Felix, Rubén | En curso |
| Activar el hook de commits: `git config core.hooksPath .githooks` | Felix, Natalia | Pendiente |
| Subir al repo el script de ingesta (`scripts/ingest_s3_data.py`), sin credenciales: se leen de `.env` | Natalia | Pendiente |
| Documentar la fuente, el formato y las particiones de los datos en el [dataset](../docs/entender/dataset.md) | Natalia | Pendiente |
| Definir quién pone la suscripción de Azure, con tope de gasto y alertas | Por asignar | Pendiente |
| Primer vistazo a los datos: inventario de tablas y contraste con el diccionario | Por asignar | Pendiente |
| Medir el volumen de reclamos por cargos no reconocidos (`case_type = Claim` + categoría) y su peso en `contact_reason` | Por asignar | Pendiente |
| Medir qué % de reclamos tiene `origin_interaction_id` válido y qué % de esas interacciones tiene transcripción | Por asignar | Pendiente |
| Perfilar las etiquetas candidatas: `category` / `subcategory` y `was_escalated` (balance, consistencia, si parecen de plantilla) | Por asignar | Pendiente |
| Baseline de palabras clave para la categoría del reclamo, con división temporal | Por asignar | Pendiente |
| Listar los campos de apertura y de resultado de `complaints` para evitar fuga de datos | Por asignar | Pendiente |

## Mar 29/9: confirmar y esqueleto

| Tarea | Responsable | Estado |
|---|---|---|
| Revisión de la [decisión 003](../docs/construir/decisiones/003-flujo-disputes.md): confirmar disputes o cambiar a tarjetas, y fijar los umbrales | Equipo | Pendiente |
| Elegir el componente aprendido (decisión 2) | Equipo | Pendiente |
| Esquema JSON del handoff (pedido, hechos verificados, transacciones, acciones, evidencia, preguntas abiertas, motivo) | Por asignar | Pendiente |
| Definir el origen y quién revisa los casos de prueba en portugués (decisión 15) | Por asignar | Pendiente |
| Esqueleto del backend: orquestador y 2-3 herramientas mock con contratos fijos | Por asignar | Pendiente |
| Chat simple con login y sesión, conectado al backend | Por asignar | Pendiente |
| Pipeline mínimo: ingesta, deduplicación y chequeos de calidad | Por asignar | Pendiente |
| Análisis que respalda el flujo: motivos de contacto, demanda y calidad de datos | Por asignar | Pendiente |

## Mié 30/9: caso normal

| Tarea | Responsable | Estado |
|---|---|---|
| Caso normal de punta a punta con datos reales | Por asignar | Pendiente |
| Verificación de la acción: el reclamo existe después de crearlo | Por asignar | Pendiente |
| Handoff integrado al flujo | Por asignar | Pendiente |
| Componente aprendido frente al baseline | Por asignar | Pendiente |
| Primeros casos de evaluación | Por asignar | Pendiente |
| Empezar el guion de la presentación y el video | Por asignar | Pendiente |

## Jue 1/10: casos difíciles y despliegue

| Tarea | Responsable | Estado |
|---|---|---|
| Casos ambiguo y humano | Por asignar | Pendiente |
| Portugués | Por asignar | Pendiente |
| Manejo de fallos: herramientas caídas, sesión expirada, reintentos acotados | Por asignar | Pendiente |
| Set adversarial: inyección de prompts y acceso no autorizado | Por asignar | Pendiente |
| Despliegue en Azure con link público | Por asignar | Pendiente |

## Vie 2/10: evaluación y entrega

| Tarea | Responsable | Estado |
|---|---|---|
| Evaluación held-out y métricas (éxito, resultados inseguros, handoff, latencia, costo) | Por asignar | Pendiente |
| Análisis de fallos y limitaciones | Por asignar | Pendiente |
| README en inglés, presentación y video | Por asignar | Pendiente |
| Revisar el repo sin secretos ni datos; congelar el código | Por asignar | Pendiente |

## Sáb 3/10 a lun 5/10: margen

| Tarea | Responsable | Estado |
|---|---|---|
| Solo correcciones críticas | Equipo | Pendiente |
| Envío | Por asignar | Pendiente |

## Por averiguar

Necesitan información, no una decisión. Ordenado por fecha.

| Pregunta | Quién la averigua | Para cuándo | Estado |
|---|---|---|---|
| ¿Qué formato y qué particiones tienen los datos en S3? | Natalia | Dom 27/9 | En curso |
| ¿Hay términos de uso de los datos publicados? (el planteamiento los menciona) | Canal de ayuda del hackathon | Lun 28/9 | Pendiente |
| ¿Qué significa el asterisco de "public\*"? ¿El repo debe ser público desde el inicio? | Canal de ayuda del hackathon | Lun 28/9 | Pendiente |
| ¿Los términos de uso permiten copiar los datos de S3 a Azure (ADLS)? | Canal de ayuda del hackathon | Lun 28/9 | Pendiente |
| ¿Cuánto cuesta tener Databricks (SQL Warehouse y, si se usa, el endpoint de Llama) encendido del 1/10 al 5/10? | Natalia | Dom 27/9 | Pendiente |
| Hora límite del lunes 5/10 y duración máxima del video | Canal de ayuda del hackathon | Lun 28/9 | Pendiente |
| ¿El modelo de Azure OpenAI que queremos está disponible en nuestra región? | Quien ponga la suscripción | Lun 28/9 | Pendiente |
| ¿Hay varias fotos mensuales? ¿Cómo se calculó `is_repeat_complainer`? | Área de datos | Con la muestra de datos | Pendiente |
| ¿Cuántas llegadas tardías hay (diferencia entre `process_date` y `transaction_date`)? | Área de datos | Con la muestra de datos | Pendiente |
| ¿Cómo construimos las etiquetas de referencia (qué casos requieren humano)? | Área de ML | Mar 29/9 | Pendiente |
| Supuestos de costo (precio del LLM, costo de un asesor) | Área de análisis | Jue 1/10 | Pendiente |

## Hecho

| Tarea | Responsable | Fecha |
|---|---|---|
| Acceso a los datos en S3 probado | Natalia | Dom 27/9 |
| Acceso de escritura al repositorio para Felix y Natalia | Rubén | Dom 27/9 |
| Equipo completo en el canal del hackathon | Equipo | Dom 27/9 |
| Repositorio creado | Rubén | Dom 27/9 |
| Nombre del equipo: Sentinel Engine | Equipo | Dom 27/9 |
| Análisis de los documentos del reto (kickoff del datathon y planteamiento del hackathon); commit el domingo | Rubén | Sáb 26/9 |
