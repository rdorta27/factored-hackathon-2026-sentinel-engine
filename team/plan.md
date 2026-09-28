# Plan del equipo

Sentinel Engine · Factored AI & Data Hackathon 2026 · Entrega: **lunes 5/10** (hora por confirmar)

> Arrancamos el lunes 28/9. Las tareas del día están en [tareas](tareas.md) y lo que nos falta decidir, en [decisiones pendientes](decisiones-pendientes.md).

## Cronograma

Es tentativo: lo ajustamos si algo se atrasa.

| Día | Fecha | Meta | Hito |
|---|---|---|---|
| Dom | 27/9 | Preparar: acceso a los datos, repositorio, lecturas | Todos con acceso |
| Lun | 28/9 | **Decidir** flujo, stack, responsables y forma de trabajo. Primer vistazo a los datos | Decisiones registradas |
| Mar | 29/9 | Esqueleto: 2-3 herramientas mock, orquestador, chat simple, pipeline mínimo. Análisis que respalda el flujo | **El esqueleto responde de punta a punta** |
| Mié | 30/9 | Caso normal con datos reales, handoff JSON, componente aprendido vs baseline. Guion de presentación y video | **Un caso funciona completo** |
| Jue | 1/10 | Casos ambiguo y humano, portugués, set adversarial, despliegue. P1 si alcanza | **3 casos en ES y PT, link público** |
| Vie | 2/10 | Evaluación held-out y métricas. Presentación, video, README en inglés, limitaciones; revisar el repo sin secretos. Congelar el código en la noche | **Listo para enviar** |
| Sáb a lun | 3/10 a 5/10 | Margen: solo correcciones. Envío temprano | **Entregado** |

Queremos tener **todo listo el viernes 2/10** y usar el fin de semana de margen. Primero que funcione: si algo opcional estorba a lo obligatorio, va para después. Las prioridades están en los [requerimientos](../docs/requerimientos/requerimientos.md).

## Decisiones tomadas

| Decisión | Estado | Registro |
|---|---|---|
| Nombre del equipo: Sentinel Engine | Aceptada | — |
| Plataforma: Microsoft Azure | Aceptada | [001](../docs/construir/decisiones/001-plataforma-azure.md) |
| Especificaciones con OpenSpec | Aceptada | [002](../docs/construir/decisiones/002-openspec.md) |
| Responsables: Natalia, datos y análisis de datos · Rubén, IA, arquitectura y ML · Felix, full-stack | Aceptada | — |
| LLM híbrido con enrutador entre modelos (los modelos se eligen el martes) | Aceptada | — |
| Presupuesto de infraestructura: la estimación de Natalia (USD 20-58, dentro de los USD 200 de crédito de prueba de Azure) como supuesto | Aceptada | — |
| Flujo inicial: disputas de transacciones, hasta la revisión del martes 29/9 | Propuesta | [003](../docs/construir/decisiones/003-flujo-disputas.md) |

Las de producto y técnicas van en [decisiones](../docs/construir/decisiones/), un archivo por decisión. Las del equipo (forma de trabajo, responsables) las anotamos aquí.

## Forma de trabajo

| Tema | Cómo lo hacemos |
|---|---|
| Comunicación | Todo por el canal del equipo. Las dudas del reto, al canal de ayuda del hackathon |
| Seguimiento diario | 15 min o un mensaje en el canal: qué hice, qué haré, qué me bloquea. Formato y hora: decisión 5 |
| Tareas | En [tareas](tareas.md), con responsable, fecha y estado |
| Especificaciones | Con OpenSpec: proponemos cada cambio antes de implementarlo y citamos sus requerimientos |
| Código | Propuesta: rama por tarea y PR que revisa otro; `main` siempre funciona. Falta la decisión 7 |
| Decisiones | Las de producto y técnicas, en [decisiones](../docs/construir/decisiones/); las del equipo, aquí. Todas las avisamos en el canal |
| Avance | Al cerrar una tarea, actualizamos su estado en los [requerimientos](../docs/requerimientos/requerimientos.md) |
| Repositorio | Uno solo (`factored-hackathon-2026-sentinel-engine`), privado mientras trabajamos y público al final |

Dos reglas del hackathon que no se negocian: nada de secretos ni datos en el repo (las credenciales van en `.env` y las pasamos por mensaje directo), y la entrega va en inglés.

## Mocks

Arrancamos con mocks bien documentados y los cambiamos por lo real uno a uno, sin tocar sus contratos. Sirve para cualquier flujo.

- **Mar 29/9, esqueleto:** 2-3 herramientas mock en memoria con contratos fijos: 1-2 de lectura (por ejemplo, datos del cliente o sus movimientos), 1 de acción (abrir un reclamo o bloquear una tarjeta) y el handoff. Chat simple y orquestador Entender → Decidir → Actuar → Verificar → Escalar. La política vive en código y el handoff JSON está desde el esqueleto: el LLM entiende, redacta y elige qué herramienta pedir, pero no decide permisos ni confirma acciones.
- **Cuándo cambiamos cada mock:** cuando el hito del cronograma lo pide, sin cambiar el contrato.
  - Mié 30/9, caso normal: las lecturas pasan al almacenamiento que elijamos (decisión 12; propuesta: DuckDB), con la frescura declarada. La acción pide confirmación explícita.
  - Jue 1/10, casos ambiguo y humano, y despliegue: reintentos acotados, acción idempotente y pipeline con particiones, watermark y deduplicación.
  - Lo que no alcancemos queda como mock y lo contamos en las limitaciones.
- **Regla:** cada mock documenta su contrato y sus limitaciones, porque así lo pide el planteamiento (Data and execution boundaries): REQ-0004 (herramientas seguras), REQ-0007 (permisos en código), REQ-0032 (mocks documentados).
- **Componente aprendido:** donde hoy hay una regla fija, la dejamos como baseline y la comparamos con el componente en el mismo held-out (REQ-0016).
