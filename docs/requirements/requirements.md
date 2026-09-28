# Requerimientos

Lo que tiene que cumplir el sistema. Cada requerimiento tiene un ID `REQ-####` que usamos en el resto de la documentación. Esta tabla también es la matriz de trazabilidad: cada requerimiento con su criterio de evaluación, área, evidencia y estado.

**Para qué sirve:** priorizar el trabajo y ver qué criterio no tiene evidencia todavía. **Relacionados:** [resumen del reto](../entender/resumen.md), [glosario](../entender/glosario.md).

## Clasificación

| Columna | Valores |
|---|---|
| **Tipo** | **F** = funcional (qué hace) · **NF** = no funcional (cómo: seguridad, confiabilidad, operación) · **DML** = datos y ML · **E** = entrega |
| **Prioridad** | **P0** = obligatorio, listo el vie 2/10 · **P1** = suma puntos, desde el jue 1/10 si el P0 va al día · **P2** = si sobra tiempo. El código se congela el vie 2/10 en la noche |
| **Flujo** | "Todos", o el flujo del que depende (propuesta: disputas de transacciones, ver [decisión 003](../construir/decisiones/003-flujo-disputas.md)) |
| **Criterio** | Criterio de evaluación del kickoff: Fundamento, AI Engineering, Data Engineering, Data Analytics, Machine Learning |
| **Área** | Áreas que trabajan en el requerimiento; la primera es la dueña y las demás colaboran: [ai](../construir/areas/ai.md) · [ml](../construir/areas/ml.md) · [datos](../construir/areas/datos.md) · [analisis](../construir/areas/analisis.md) |
| **Estado** | Pendiente, En curso, Listo. Lo actualizamos al cerrar cada tarea |
| **Fuente** | Documento oficial y sección (planteamiento) o página (kickoff), o **Propio** = decisión de diseño del equipo, con enlace a donde se explica |

Los documentos oficiales (planteamiento, kickoff, resumen del dataset y diccionario) no están en el repositorio: los citamos por sección o página.

## Resumen por prioridad

| Prioridad | Cantidad | Qué incluye |
|---|---|---|
| P0 | 36 | Los 3 casos de la demo, ES y PT, verificación, permisos en código, handoff, componente aprendido vs baseline, pipeline con contratos, pruebas de fallas, entregables, idioma de entrega |
| P1 | 11 | Tracking, incremental real, observabilidad, reintentos, desglose por idioma y país, reglas de conversación finas |
| P2 | 4 | País como configuración, contexto de errores de la app, enrutamiento del handoff, LLM juez |

## Funcionales (F)

| ID | Requerimiento | P | Flujo | Criterio | Área | Fuente | Evidencia | Estado |
|---|---|---|---|---|---|---|---|---|
| REQ-0001 | Mantener el contexto de la conversación | P0 | Todos | AI Engineering | ai | Planteamiento: What your solution should demonstrate 2 · Kickoff p. 11 | Demo | Pendiente |
| REQ-0002 | Aclarar solicitudes ambiguas o abstenerse ante las no soportadas | P0 | Todos | AI Engineering | ai | Planteamiento: Scope; What your solution should demonstrate 2 · Kickoff p. 11 | Demo caso ambiguo | Pendiente |
| REQ-0003 | Responder solo con registros verificados; si el dato no existe, decirlo | P0 | Todos | AI Engineering | ai | Planteamiento: What your solution should demonstrate 2 · Kickoff p. 13 | Demo + logs | Pendiente |
| REQ-0004 | Usar herramientas de forma segura para ejecutar el flujo | P0 | Todos | AI Engineering | ai | Planteamiento: What your solution should demonstrate 2 · Kickoff p. 11 | Contratos de herramientas | Pendiente |
| REQ-0006 | Definir qué responde solo, qué requiere confirmación y cuándo escalar | P0 | Todos | Fundamento | ai | Planteamiento: What your solution should demonstrate 3 · Kickoff p. 11 | [Conversación](../construir/conversacion.md) | Pendiente |
| REQ-0008 | Handoff estructurado en JSON: solicitud, hechos verificados, acciones, evidencia, preguntas abiertas; sin transcripción cruda | P0 | Todos | AI Engineering | ai | Planteamiento: What your solution should demonstrate 3 · Kickoff p. 11, 14 | Esquema + ejemplo | Pendiente |
| REQ-0009 | Demo: caso normal resuelto conforme a políticas | P0 | Todos | AI Engineering | ai | Planteamiento: Scope · Kickoff p. 11 | Demo + video | Pendiente |
| REQ-0010 | Demo: caso ambiguo o no soportado (aclara o se abstiene) | P0 | Todos | AI Engineering | ai | Planteamiento: Scope · Kickoff p. 11 | Demo + video | Pendiente |
| REQ-0011 | Demo: caso que requiere humano (escala con handoff) | P0 | Todos | AI Engineering | ai | Planteamiento: Scope · Kickoff p. 11 | Demo + video | Pendiente |
| REQ-0012 | Interacciones robustas en español y portugués | P0 | Todos | AI Engineering / ML | ai, ml | Planteamiento: Scope · Kickoff p. 10 | Demo PT + métricas por idioma | Pendiente |
| REQ-0033 | Separar conversación, riesgo y política de elegibilidad; el LLM no aprueba ni inventa reglas | P0 | Crédito | AI Engineering / ML | ai, ml | Planteamiento: Data and execution boundaries | Arquitectura | Pendiente |
| REQ-0038 | Frontend simple para usar el sistema (ej.: chat); dashboard no obligatorio (decisión de alcance: sin dashboard) | P0 | Todos | AI Engineering | ai | Kickoff p. 20 | Demo | Pendiente |
| REQ-0039 | Declarar la frescura de los datos ("actualizado hasta…"); nunca afirmar algo más reciente | P0 | Todos | AI Engineering / Data Engineering | ai, datos | Propio: [conversación](../construir/conversacion.md#cuando-los-datos-no-están-al-día) | Demo + herramientas con "actualizado hasta" | Pendiente |
| REQ-0040 | Pedido de hablar con una persona: una sola oferta de resolver y, si insiste, escalar de inmediato | P0 | Todos | AI Engineering | ai | Propio: [conversación](../construir/conversacion.md#cuando-el-cliente-pide-hablar-con-una-persona) | Demo caso humano | Pendiente |
| REQ-0041 | Mostrar montos en la moneda original de la transacción; idioma según el cliente, moneda según la cuenta | P0 | Todos | AI Engineering | ai | Propio: [conversación](../construir/conversacion.md#lenguaje) | Demo PT | Pendiente |
| REQ-0042 | Abrir reclamos con el mínimo esfuerzo: mostrar transacciones candidatas en vez de pedir montos | P1 | Reclamos | AI Engineering | ai | Propio: [conversación](../construir/conversacion.md#al-abrir-un-reclamo) | Demo | Pendiente |
| REQ-0043 | Revisar el estado del cargo (Pending, Reversed) antes de abrir un reclamo | P1 | Reclamos, cuentas | AI Engineering | ai | Propio: [conversación](../construir/conversacion.md#al-abrir-un-reclamo) | Demo | Pendiente |
| REQ-0044 | Español neutro, con siglas y términos locales explicados; entender términos de otros países | P1 | Todos | AI Engineering | ai | Propio: [conversación](../construir/conversacion.md#lenguaje) | Demo | Pendiente |
| REQ-0045 | Ofrecer como pregunta el contexto de errores recientes de la app (contexto auxiliar, no flujo propio) | P2 | Todos | AI Engineering | ai | Propio: [conversación](../construir/conversacion.md#contexto-de-la-app) | Demo | Pendiente |
| REQ-0046 | Enrutar el handoff a un asesor con el idioma y la especialidad adecuados (simulado) | P2 | Todos | AI Engineering | ai | Propio: [AI](../construir/areas/ai.md#enrutamiento-simulado) | Ejemplo de handoff | Pendiente |

## No funcionales (NF)

| ID | Requerimiento | P | Flujo | Criterio | Área | Fuente | Evidencia | Estado |
|---|---|---|---|---|---|---|---|---|
| REQ-0005 | Reportar solo acciones verificadas (timeout no es éxito) | P0 | Todos | AI Engineering | ai | Planteamiento: What your solution should demonstrate 2 · Kickoff p. 11 | Prueba de falla de herramienta | Pendiente |
| REQ-0007 | Permisos y políticas en código, además del prompt | P0 | Todos | AI Engineering | ai | Planteamiento: What your solution should demonstrate 3; Data and execution boundaries · Kickoff p. 13 | Código + prueba adversarial | Pendiente |
| REQ-0021 | Pruebas de fallas: datos malos o faltantes, sesión expirada, acceso no autorizado, prompt injection, falla de herramienta, ambigüedad multilingüe | P0 | Todos | Machine Learning | ml, ai | Planteamiento: What your solution should demonstrate 5 · Kickoff p. 13 | Resultados del set adversarial | Pendiente |
| REQ-0027 | Autenticación con sesión de prueba, control de acceso por cliente, política de retención | P0 | Todos | AI Engineering / Data Engineering | ai, datos | Planteamiento: What your solution should demonstrate 6; Data and execution boundaries · Kickoff p. 15 | Sesión de prueba + política | Pendiente |
| REQ-0028 | Reproducibilidad: instalación, versionado, evaluación repetible | P0 | Todos | Fundamento | todos | Planteamiento: What your solution should demonstrate 6 · Kickoff p. 15 | README de instalación | Pendiente |
| REQ-0047 | El LLM no recibe identificadores ni datos personales; las herramientas filtran por el cliente de la sesión | P0 | Todos | AI Engineering | ai | Propio: [seguridad](../construir/seguridad.md#visibilidad-del-llm) | Código + prueba adversarial | Pendiente |
| REQ-0048 | Orden de decisión: política en código > predictor > LLM | P0 | Todos | Fundamento / ML | ai, ml | Propio: [arquitectura](../entender/arquitectura.md#prioridad-de-decisión) | [Arquitectura](../entender/arquitectura.md) | Pendiente |
| REQ-0025 | Observabilidad: trazas y registros de ejecución, con país e idioma | P1 | Todos | AI Engineering | ai | Planteamiento: What your solution should demonstrate 6 · Kickoff p. 15 | Trazas y logs | Pendiente |
| REQ-0026 | Reintentos acotados, fallback seguro; acciones idempotentes | P1 | Todos | AI Engineering | ai | Planteamiento: What your solution should demonstrate 6 · Kickoff p. 15 | Prueba de falla de herramienta | Pendiente |
| REQ-0029 | Explicaciones basadas en fuentes, reglas y logs; no en el razonamiento del modelo | P1 | Todos | AI Engineering | ai | Planteamiento: What your solution should demonstrate 6 | Logs de auditoría | Pendiente |
| REQ-0032 | Herramientas mock con contratos y limitaciones documentados | P1 | Todos | AI Engineering | ai | Planteamiento: Data and execution boundaries | Contratos de herramientas | Pendiente |
| REQ-0049 | El país es configuración, no código | P2 | Todos | Fundamento | ai | Propio: [AI](../construir/areas/ai.md#reglas-técnicas) | Archivo de configuración | Pendiente |

## Datos y ML (DML)

| ID | Requerimiento | P | Flujo | Criterio | Área | Fuente | Evidencia | Estado |
|---|---|---|---|---|---|---|---|---|
| REQ-0014 | Problema respaldado por datos, con análisis reproducible que justifica el flujo | P0 | Todos | Data Analytics | analisis | Planteamiento: What your solution should demonstrate 1 · Kickoff p. 13 | Análisis reproducible | Pendiente |
| REQ-0015 | Pipeline repetible con contratos estrictos, calidad, linaje y frescura | P0 | Todos | Data Engineering | datos | Planteamiento: What your solution should demonstrate 4 · Kickoff p. 12 | Pipeline + reporte de calidad | Pendiente |
| REQ-0016 | Al menos un componente aprendido comparado contra una baseline sobre held-out | P0 | Todos | Machine Learning | ml | Planteamiento: What your solution should demonstrate 4 · Kickoff p. 12 | Tabla de resultados | Pendiente |
| REQ-0017 | Etiquetas válidas y sin fuga de datos; justificar métricas, umbrales y divisiones | P0 | Todos | Machine Learning | ml | Planteamiento: What your solution should demonstrate 4 · Kickoff p. 12 | Descripción de la división | Pendiente |
| REQ-0020 | Baseline y sistema sobre el mismo held-out, con distribución realista | P0 | Todos | Machine Learning | ml | Planteamiento: Evaluation evidence · Kickoff p. 12 | Descripción de los sets | Pendiente |
| REQ-0022 | Métricas con n, mezcla de casos, versiones y variabilidad; incluir fallas | P0 | Todos | Data Analytics | analisis | Planteamiento: What your solution should demonstrate 5; Evaluation evidence | Reporte de métricas | Pendiente |
| REQ-0031 | Solo datos aprobados; etiquetar cada fuente (real, sintético, generado por el equipo) | P0 | Todos | Data Engineering | datos | Planteamiento: Data and execution boundaries | Inventario de fuentes | Pendiente |
| REQ-0018 | Procesamiento incremental real (llegadas tardías, duplicados, esquema cambiante) o, si los datos son estáticos, fixture etiquetado | P1 | Todos | Data Engineering | datos | Planteamiento: Architecture freedom | Fixture de actualización | Pendiente |
| REQ-0019 | Tracking de experimentos: versiones de modelos y prompts, parámetros, métricas | P1 | Todos | Machine Learning | ml | Kickoff p. 20 | Registro de experimentos | Pendiente |
| REQ-0024 | Desglose por idioma, país y segmento; separar offline, simulación y proyección | P1 | Todos | Data Analytics | analisis | Planteamiento: Evaluation evidence | Reporte de métricas | Pendiente |
| REQ-0050 | Monitoreo por país (latencia, fallas, escalamientos, quejas) | P1 | Todos | Data Analytics | analisis | Propio: [análisis](../construir/areas/analisis.md#monitoreo-por-país) | Reporte por país | Pendiente |
| REQ-0023 | Si hay LLM juez: rúbrica documentada y validada contra una muestra humana | P2 | Si aplica | Machine Learning | ml | Planteamiento: Evaluation evidence | Rúbrica + muestra validada | Pendiente |

## Entrega (E)

| ID | Requerimiento | P | Flujo | Criterio | Área | Fuente | Evidencia | Estado |
|---|---|---|---|---|---|---|---|---|
| REQ-0034 | Repositorio público `factored-hackathon-2026-[equipo]`, sin secretos ni datos restringidos | P0 | Todos | Fundamento | todos | Kickoff p. 18 | Link al repo | Pendiente |
| REQ-0035 | Link a la herramienta desplegada, con límites de uso y gasto | P0 | Todos | AI Engineering | ai | Kickoff p. 18 | Link | Pendiente |
| REQ-0036 | Presentación de 4 a 6 diapositivas | P0 | Todos | Fundamento | todos | Kickoff p. 18 | [Guion](../construir/entrega.md#presentación) | Pendiente |
| REQ-0037 | Video pitch corto: demo y decisiones de arquitectura | P0 | Todos | Fundamento | todos | Kickoff p. 18 | [Guion](../construir/entrega.md#video-pitch) | Pendiente |
| REQ-0051 | README del repo, presentación (4 a 6 diapositivas) y guion del video en inglés; `docs/` y `team/` se quedan en español | P0 | Todos | Fundamento | todos | Propio: [idioma](../construir/entrega.md#idioma) | [Revisión antes de enviar](../construir/entrega.md#idioma) | Pendiente |
| REQ-0013 | Reportar las limitaciones de datos y de cobertura de idiomas | P0 | Todos | Fundamento | analisis | Planteamiento: Scope · Kickoff p. 15 | Sección de limitaciones | Pendiente |
| REQ-0030 | Declarar lo que falta: capacidad, datos, idiomas, despliegue, riesgos | P0 | Todos | Fundamento | todos | Planteamiento: Scope; What your solution should demonstrate 6 · Kickoff p. 15 | Sección de limitaciones | Pendiente |

## Trabajo futuro (no son requerimientos)

- Expansión a otros países de Latinoamérica. El diseño lo facilita con REQ-0049 (país como configuración); requeriría datos, reglas, moneda y pruebas de cada país nuevo.
- Streaming: solo si un flujo necesita segundos de frescura.

## Preguntas abiertas

- ¿Qué flujo elegimos? (lunes 28/9). Con eso se confirman o descartan los requerimientos que dependen del flujo.
- ¿Cómo construimos las etiquetas de referencia para evaluar (qué casos requieren humano)?
