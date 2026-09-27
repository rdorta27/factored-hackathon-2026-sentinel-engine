# Plan del equipo

Sentinel Engine · Factored AI & Data Hackathon 2026 · Entrega: **lunes 5/10** · Se actualiza a medida que decidimos.

> Este plan lo vamos construyendo juntos. Lo que dice **tentativo** o **propuesta** está abierto a cambios; las decisiones que nos faltan están [al final](#decisiones-pendientes).

## Equipo

| Nombre | Fuerte en | Área tentativa | Disponibilidad | No puede |
|---|---|---|---|---|
| Felix | | | | |
| Natalia | | | | |
| Rubén | | | | |

Áreas: AI (backend, frontend, despliegue) · ML (modelos y evaluación) · Datos (pipeline) · Análisis (métricas e insights). Somos 3 para 4 áreas, así que alguien tomará dos. Ninguno viene de contact centers; el [glosario](entender/glosario.md) ayuda con las siglas del negocio.

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

Idea guía: **primero que funcione**. Si algo opcional pone en riesgo lo obligatorio, lo dejamos para después. Prioridades en [requerimientos](requerimientos/requerimientos.md).

## Cómo trabajar (propuesta)

| Qué | Propuesta |
|---|---|
| Comunicación | Slack del equipo. Dudas técnicas del reto: `#technical-help` del hackathon |
| Seguimiento diario | 15 min o mensaje en Slack: qué hice, qué haré, qué me bloquea |
| Tareas | GitHub Issues con etiquetas de prioridad (P0, P1, P2) y de área; tablero Por hacer, En curso, Hecho |
| Especificaciones | OpenSpec: cada cambio se propone antes de implementarlo y cita sus requerimientos |
| Código | Rama por tarea y pull request revisado por otra persona. `main` siempre funciona |
| Decisiones | Una por archivo en [decisiones](construir/decisiones/), anunciada en Slack |
| Avance | Al cerrar una tarea, actualizar su estado en la [matriz](requerimientos/matriz.md) |
| Repositorio | Uno solo (`factored-hackathon-2026-sentinel-engine`), privado durante el trabajo y público al final |

Dos cosas son obligatorias porque las pide el hackathon: no subir secretos ni datos al repositorio (las credenciales van en `.env` y se comparten por mensaje directo), y entregar en inglés.

## Organización

- [x] Nombre del equipo: Sentinel Engine
- [x] Repositorio creado
- [ ] Los 3 con acceso al repositorio
- [ ] Acceso a los datos (credenciales) funcionando para los 3
- [ ] Todos en el Slack del hackathon

## Decisiones tomadas

| Decisión | Registro |
|---|---|
| Plataforma: Microsoft Azure | [001](construir/decisiones/001-plataforma-azure.md) |
| Especificaciones con OpenSpec | [002](construir/decisiones/002-openspec.md) |
| Nombre del equipo: Sentinel Engine | — |

## Decisiones pendientes

| # | Decisión | Opciones o propuesta | Para cuándo |
|---|---|---|---|
| **Producto** | | | |
| 1 | Flujo | Cuentas o pagos, tarjetas, reclamos por cargos, crédito. Ver [opciones de flujo](construir/flujos/opciones.md) | Lun 28/9 |
| 2 | Componente aprendido | Predictor de escalamiento, clasificador de intención, detector de fraude. Ver [ML](construir/areas/ml.md) | Lun 28/9 |
| 3 | Alcance de la demo | Qué acciones hace el asistente (consultar, bloquear, abrir reclamo…) y cuáles no | Mar 29/9 |
| **Equipo** | | | |
| 4 | Responsables por área | Quién toma dos áreas | Lun 28/9 |
| 5 | Seguimiento diario | Reunión de 15 min o mensaje en Slack; hora | Lun 28/9 |
| 6 | Herramienta de tareas | GitHub Issues y Projects, u otra | Lun 28/9 |
| 7 | Flujo de código | Pull request obligatorio o push directo a `main`; quién revisa | Lun 28/9 |
| 8 | Reuniones de hito | Cuándo revisamos juntos (ej.: miércoles, viernes y domingo) | Lun 28/9 |
| **Técnicas** | | | |
| 9 | Lenguaje y framework del backend | Propuesta: Python con FastAPI | Lun 28/9 |
| 10 | LLM | Propuesta: Azure OpenAI; qué modelo | Lun 28/9 |
| 11 | Frontend | Chat simple: Streamlit, Gradio o web propia | Mar 29/9 |
| 12 | Almacenamiento de datos | Local (DuckDB) o en Azure | Mar 29/9 |
| 13 | Servicios de Azure | Despliegue (Container Apps o App Service), secretos (Key Vault) | Mar 29/9 |
| 14 | Tracking de experimentos | MLflow, Azure ML u otro | Mié 30/9 |
| 15 | Casos de prueba en portugués | Traducidos, sintéticos o escritos por alguien que lea portugués | Mar 29/9 |
| **Recursos y entrega** | | | |
| 16 | Suscripción o créditos de Azure | Quién la pone; tope de gasto y alertas | Lun 28/9 |
| 17 | Visibilidad del repositorio | Privado ahora y público al final, o público desde ya (hoy está público) | Dom 27/9 |
| 18 | Idioma de las especificaciones de OpenSpec | Propuesta: inglés, porque se entregan | Lun 28/9 |
| 19 | Idioma de `docs/` en la entrega | Dejarlos en español o traducir los principales | Sáb 3/10 |
| 20 | Quién hace la presentación y el video | | Vie 2/10 |

## Preguntas abiertas

Necesitan información, no una decisión.

| Pregunta | Quién la averigua | Cuándo |
|---|---|---|
| ¿Cómo se accede a los datos y qué formato tienen? | Quien tenga las credenciales | Dom 27/9 |
| ¿Hay términos de uso de los datos publicados? (el planteamiento los menciona) | Preguntar en `#technical-help` | Dom 27/9 |
| ¿Qué significa el asterisco de "public\*"? ¿El repo debe ser público desde el inicio? | Preguntar en `#technical-help` | Dom 27/9 |
| Hora límite del lunes 5/10 y duración máxima del video | Preguntar en `#technical-help` | Lun 28/9 |
| ¿Hay varias fotos mensuales? ¿Cómo se calculó `is_repeat_complainer`? | Área de datos | Al recibir los datos |
| ¿Cómo construimos las etiquetas de referencia (qué casos requieren humano)? | Área de ML | Mar 29/9 |
| ¿El modelo de Azure OpenAI que queremos está disponible en nuestra región? | Quien ponga la suscripción | Lun 28/9 |
| Supuestos de costo (precio del LLM, costo de un asesor) | Área de análisis | Jue 1/10 |
| Términos de Venezuela y Ecuador en el glosario | Compañeros de esos países | Cuando puedan |
