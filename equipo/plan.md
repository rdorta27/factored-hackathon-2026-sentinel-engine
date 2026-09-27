# Plan del equipo

Sentinel Engine · Factored AI & Data Hackathon 2026 · Entrega: **lunes 5/10** (hora por confirmar) · Se actualiza a medida que decidimos.

> Este plan lo vamos construyendo juntos. Lo que dice **tentativo** o **propuesta** está abierto a cambios. Las decisiones que faltan están en [decisiones pendientes](decisiones-pendientes.md) y las tareas en [tareas](tareas.md).

## Equipo

| Nombre | Fuerte en | Área tentativa | Disponibilidad | No puede |
|---|---|---|---|---|
| Felix | | | | |
| Natalia | | | | |
| Rubén | | | | |

Áreas: AI (backend, frontend, despliegue) · ML (modelos y evaluación) · Datos (pipeline) · Análisis (métricas e insights). Somos 3 para 4 áreas, así que alguien tomará dos. Ninguno viene de contact centers; el [glosario](../docs/entender/glosario.md) ayuda con las siglas del negocio.

## Cronograma (tentativo)

| Día | Fecha | Meta | Hito |
|---|---|---|---|
| Dom | 27/9 | Preparar: acceso a los datos, repositorio, lecturas | Todos con acceso |
| Lun | 28/9 | **Decidir** flujo, stack, responsables y forma de trabajo | Decisiones registradas |
| Mar | 29/9 | Esqueleto: pipeline mínimo, 2-3 herramientas mock, chat simple | |
| Mié | 30/9 | Caso normal de punta a punta; línea base del componente aprendido | **Un caso funciona completo** |
| Jue | 1/10 | Casos ambiguo y humano, handoff, portugués, componente aprendido | **3 casos en ES y PT** |
| Vie | 2/10 | Despliegue, evaluación held-out, set adversarial | **Link público y métricas v1** (fin de P0) |
| Sáb | 3/10 | P1: incremental, tracking, observabilidad, desgloses. Congelar funcionalidades en la noche | **Sin cambios de código después** |
| Dom | 4/10 | Presentación, video, README en inglés, limitaciones; revisar el repo sin secretos | Material listo |
| Lun | 5/10 | Margen y envío temprano | **Entregado** |

Idea guía: **primero que funcione**. Si algo opcional pone en riesgo lo obligatorio, lo dejamos para después. Prioridades en [requerimientos](../docs/requerimientos/requerimientos.md).

## Estrategia de mocks (propuesta)

Sirve para cualquier flujo: se arma rápido con mocks bien documentados y después se reemplazan uno a uno sin cambiar sus contratos.

- **Mar 29/9 (esqueleto):** 2-3 herramientas mock en memoria con contratos fijos: 1-2 de lectura (ej.: consultar datos del cliente o sus movimientos), 1 de acción (ej.: abrir un reclamo o bloquear una tarjeta) y el handoff. Chat simple y orquestador Entender → Decidir → Actuar → Verificar → Escalar. Política en código y handoff JSON desde el esqueleto; el LLM entiende, redacta y elige qué herramienta pedir, pero no decide permisos ni confirma acciones.
- **Sustitución:** cada mock se reemplaza cuando el hito del cronograma lo necesita, sin cambiar el contrato:
  - Mié 30/9, caso normal: las lecturas pasan al almacenamiento elegido (decisión 12; propuesta: DuckDB), con frescura declarada.
  - Jue 1/10, casos ambiguo y humano: la acción, con confirmación explícita, reintentos acotados y acción idempotente.
  - Vie 2/10, despliegue: pipeline con particiones, watermark y deduplicación.
  - Lo que no llegue queda como mock y se declara en las limitaciones.
- **Regla:** cada mock documenta su contrato y sus limitaciones, como pide el planteamiento (Data and execution boundaries) para aceptarlo: REQ-0004 (herramientas seguras), REQ-0007 (permisos en código), REQ-0032 (mocks documentados).
- **Componente aprendido:** donde hoy hay una regla fija, la regla se conserva como línea base y se compara con el componente sobre el mismo held-out (REQ-0016, componente aprendido vs línea base).

## Cómo trabajar (propuesta)

| Qué | Propuesta |
|---|---|
| Comunicación | Canal del equipo. Dudas técnicas del reto: canal de ayuda del hackathon |
| Seguimiento diario | 15 min o mensaje en el canal: qué hice, qué haré, qué me bloquea |
| Tareas | Lista en [tareas](tareas.md): responsable, fecha y estado |
| Especificaciones | OpenSpec: cada cambio se propone antes de implementarlo y cita sus requerimientos |
| Código | Rama por tarea y pull request revisado por otra persona. `main` siempre funciona |
| Decisiones | Producto y técnicas: una por archivo en [decisiones](../docs/construir/decisiones/). Equipo: en este plan. Todas se anuncian en el canal |
| Avance | Al cerrar una tarea, actualizar su estado en los [requerimientos](../docs/requerimientos/requerimientos.md) |
| Repositorio | Uno solo (`factored-hackathon-2026-sentinel-engine`), privado durante el trabajo y público al final |

Dos cosas son obligatorias porque las pide el hackathon: no subir secretos ni datos al repositorio (las credenciales van en `.env` y se comparten por mensaje directo), y entregar en inglés.

## Decisiones tomadas

| Decisión | Registro |
|---|---|
| Plataforma: Microsoft Azure | [001](../docs/construir/decisiones/001-plataforma-azure.md) |
| Especificaciones con OpenSpec | [002](../docs/construir/decisiones/002-openspec.md) |
| Nombre del equipo: Sentinel Engine | — |

Las decisiones de producto y técnicas se registran en [decisiones](../docs/construir/decisiones/); las del equipo (forma de trabajo, responsables) se anotan en este archivo. Las pendientes están en [decisiones pendientes](decisiones-pendientes.md).
