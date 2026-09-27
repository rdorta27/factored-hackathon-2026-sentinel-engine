# Tareas

Quién hace qué y para cuándo. Al tomar una tarea, poner el nombre; al terminarla, marcarla. Si la tarea cubre un requerimiento, citar su `REQ-####` y actualizar su estado en los [requerimientos](../docs/requerimientos/requerimientos.md).

**Estados:** Pendiente, En curso, Hecho.

## Para el lunes 28/9

| Tarea | Responsable | Estado |
|---|---|---|
| Completar la [tabla del equipo](plan.md#equipo): fortalezas y disponibilidad | Cada uno | Pendiente |
| Anotar la preferencia en las [decisiones pendientes](decisiones-pendientes.md) | Cada uno | Pendiente |
| Confirmar que las credenciales de S3 funcionan para los 3 (Natalia ya las probó) | Felix, Rubén | En curso |
| Subir al repo el script de ingesta (`scripts/ingest_s3_data.py`), sin credenciales: se leen de `.env` | Natalia | Pendiente |
| Documentar la fuente, el formato y las particiones de los datos en el [dataset](../docs/entender/dataset.md) | Natalia | Pendiente |
| Definir quién pone la suscripción de Azure, con tope de gasto y alertas | Por asignar | Pendiente |
| Primer vistazo a los datos: inventario de tablas, perfil de los motivos de contacto y contraste con el diccionario | Por asignar | Pendiente |

## Por averiguar

Necesitan información, no una decisión.

| Pregunta | Quién la averigua | Para cuándo | Estado |
|---|---|---|---|
| ¿Qué formato y qué particiones tienen los datos en S3? | Natalia | Lun 28/9 | En curso |
| ¿Los términos de uso permiten copiar los datos de S3 a Azure (ADLS)? | Canal de ayuda del hackathon | Lun 28/9 | Pendiente |
| ¿Cuánto cuesta tener Databricks (SQL Warehouse y, si se usa, el endpoint de Llama) encendido del 1/10 al 5/10? | Natalia | Lun 28/9 | Pendiente |
| ¿Hay términos de uso de los datos publicados? (el planteamiento los menciona) | Canal de ayuda del hackathon | Dom 27/9 | Pendiente |
| ¿Qué significa el asterisco de "public\*"? ¿El repo debe ser público desde el inicio? | Canal de ayuda del hackathon | Dom 27/9 | Pendiente |
| Hora límite del lunes 5/10 y duración máxima del video | Canal de ayuda del hackathon | Lun 28/9 | Pendiente |
| ¿El modelo de Azure OpenAI que queremos está disponible en nuestra región? | Quien ponga la suscripción | Lun 28/9 | Pendiente |
| ¿Hay varias fotos mensuales? ¿Cómo se calculó `is_repeat_complainer`? | Área de datos | Con la muestra de datos | Pendiente |
| ¿Cómo construimos las etiquetas de referencia (qué casos requieren humano)? | Área de ML | Mar 29/9 | Pendiente |
| Supuestos de costo (precio del LLM, costo de un asesor) | Área de análisis | Jue 1/10 | Pendiente |

## Hecho

- [x] Nombre del equipo: Sentinel Engine
- [x] Repositorio creado
- [x] Equipo completo en el canal del hackathon
- [x] Acceso de escritura al repositorio para Felix y Natalia
- [x] Acceso a los datos en S3 probado (Natalia)
