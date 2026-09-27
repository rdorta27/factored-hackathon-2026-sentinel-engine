# Requerimientos

Qué debe cumplir el sistema. Cada requerimiento tiene un ID con formato `REQ-####` que se usa en la [matriz](matriz.md) y en el resto de la documentación.

**Para qué sirve:** priorizar el trabajo y verificar que no falte nada. **Relacionados:** [resumen del reto](../entender/resumen.md), [matriz](matriz.md), [glosario](../entender/glosario.md).

## Cómo se clasifican

| Columna | Valores |
|---|---|
| **Tipo** | **F** = funcional (qué hace) · **NF** = no funcional (cómo: seguridad, confiabilidad, operación) · **DML** = datos y ML · **E** = entrega |
| **Prioridad** | **P0** = obligatorio, días 1 a 5 · **P1** = suma puntos, días 6 a 8 · **P2** = si sobra tiempo |
| **Flujo** | "Todos", o el flujo del que depende (se define el lunes 28/9) |
| **Fuente** | Documento oficial y sección (planteamiento) o página (kickoff), o **Propio** = decisión de diseño del equipo, con enlace a donde se explica |

Los documentos oficiales (planteamiento, kickoff, resumen del dataset y diccionario) no están en el repositorio: se citan por sección o página.

## Resumen por prioridad

| Prioridad | Cantidad | Qué incluye |
|---|---|---|
| P0 | 35 | Los 3 casos de la demo, ES y PT, verificación, permisos en código, handoff, componente aprendido vs línea base, pipeline con contratos, pruebas de fallas, entregables |
| P1 | 11 | Tracking, incremental real, observabilidad, reintentos, desglose por idioma y país, reglas de conversación finas |
| P2 | 4 | País como configuración, enrutamiento del handoff, LLM juez |

## Funcionales (F)

| ID | Requerimiento | Prioridad | Flujo | Fuente |
|---|---|---|---|---|
| REQ-0001 | Mantener el contexto de la conversación | P0 | Todos | Planteamiento: What your solution should demonstrate 2 · Kickoff p. 11 |
| REQ-0002 | Aclarar solicitudes ambiguas o abstenerse ante las no soportadas | P0 | Todos | Planteamiento: Scope; What your solution should demonstrate 2 · Kickoff p. 11 |
| REQ-0003 | Responder solo con registros verificados; si el dato no existe, decirlo | P0 | Todos | Planteamiento: What your solution should demonstrate 2 · Kickoff p. 13 |
| REQ-0004 | Usar herramientas de forma segura para ejecutar el flujo | P0 | Todos | Planteamiento: What your solution should demonstrate 2 · Kickoff p. 11 |
| REQ-0006 | Definir qué responde solo, qué requiere confirmación y cuándo escalar | P0 | Todos | Planteamiento: What your solution should demonstrate 3 · Kickoff p. 11 |
| REQ-0008 | Handoff estructurado en JSON: solicitud, hechos verificados, acciones, evidencia, preguntas abiertas; sin transcripción cruda | P0 | Todos | Planteamiento: What your solution should demonstrate 3 · Kickoff p. 11, 14 |
| REQ-0009 | Demo: caso normal resuelto conforme a políticas | P0 | Todos | Planteamiento: Scope · Kickoff p. 11 |
| REQ-0010 | Demo: caso ambiguo o no soportado (aclara o se abstiene) | P0 | Todos | Planteamiento: Scope · Kickoff p. 11 |
| REQ-0011 | Demo: caso que requiere humano (escala con handoff) | P0 | Todos | Planteamiento: Scope · Kickoff p. 11 |
| REQ-0012 | Interacciones robustas en español y portugués | P0 | Todos | Planteamiento: Scope · Kickoff p. 10 |
| REQ-0033 | Separar conversación, riesgo y política de elegibilidad; el LLM no aprueba ni inventa reglas | P0 | Crédito | Planteamiento: Data and execution boundaries |
| REQ-0038 | Frontend simple para usar el sistema (ej.: chat); sin dashboard | P0 | Todos | Kickoff p. 20 |
| REQ-0039 | Declarar la frescura de los datos ("actualizado hasta…"); nunca afirmar algo más reciente | P0 | Todos | Propio: [conversación](../construir/conversacion.md#cuando-los-datos-no-están-al-día) |
| REQ-0040 | Pedido de hablar con una persona: una sola oferta de resolver y, si insiste, escalar de inmediato | P0 | Todos | Propio: [conversación](../construir/conversacion.md#cuando-el-cliente-pide-hablar-con-una-persona) |
| REQ-0041 | Mostrar montos en la moneda original de la transacción; idioma según el cliente, moneda según la cuenta | P0 | Todos | Propio: [conversación](../construir/conversacion.md#lenguaje) |
| REQ-0042 | Abrir reclamos con el mínimo esfuerzo: mostrar transacciones candidatas en vez de pedir montos | P1 | Reclamos | Propio: [conversación](../construir/conversacion.md#al-abrir-un-reclamo) |
| REQ-0043 | Revisar el estado del cargo (Pending, Reversed) antes de abrir un reclamo | P1 | Reclamos, cuentas | Propio: [conversación](../construir/conversacion.md#al-abrir-un-reclamo) |
| REQ-0044 | Español neutro, con siglas y términos locales explicados; entender términos de otros países | P1 | Todos | Propio: [conversación](../construir/conversacion.md#lenguaje) |
| REQ-0045 | Ofrecer como pregunta el contexto de errores recientes de la app | P2 | Tarjetas, app | Propio: [conversación](../construir/conversacion.md#contexto-de-la-app) |
| REQ-0046 | Enrutar el handoff a un asesor con el idioma y la especialidad adecuados (simulado) | P2 | Todos | Propio: [AI](../construir/areas/ai.md#enrutamiento-simulado) |

## No funcionales (NF)

| ID | Requerimiento | Prioridad | Flujo | Fuente |
|---|---|---|---|---|
| REQ-0005 | Reportar solo acciones verificadas (timeout no es éxito) | P0 | Todos | Planteamiento: What your solution should demonstrate 2 · Kickoff p. 11 |
| REQ-0007 | Permisos y políticas en código, además del prompt | P0 | Todos | Planteamiento: What your solution should demonstrate 3; Data and execution boundaries · Kickoff p. 13 |
| REQ-0021 | Pruebas de fallas: datos malos o faltantes, sesión expirada, acceso no autorizado, prompt injection, falla de herramienta, ambigüedad multilingüe | P0 | Todos | Planteamiento: What your solution should demonstrate 5 · Kickoff p. 13 |
| REQ-0027 | Autenticación con sesión de prueba, control de acceso por cliente, política de retención | P0 | Todos | Planteamiento: What your solution should demonstrate 6; Data and execution boundaries · Kickoff p. 15 |
| REQ-0028 | Reproducibilidad: instalación, versionado, evaluación repetible | P0 | Todos | Planteamiento: What your solution should demonstrate 6 · Kickoff p. 15 |
| REQ-0047 | El LLM no recibe identificadores ni datos personales; las herramientas filtran por el cliente de la sesión | P0 | Todos | Propio: [seguridad](../construir/seguridad.md#qué-ve-el-llm) |
| REQ-0048 | Orden de decisión: política en código > predictor > LLM | P0 | Todos | Propio: [arquitectura](../entender/arquitectura.md#quién-decide-qué) |
| REQ-0025 | Observabilidad: trazas y registros de ejecución, con país e idioma | P1 | Todos | Planteamiento: What your solution should demonstrate 6 · Kickoff p. 15 |
| REQ-0026 | Reintentos acotados, fallback seguro; acciones idempotentes | P1 | Todos | Planteamiento: What your solution should demonstrate 6 · Kickoff p. 15 |
| REQ-0029 | Explicaciones basadas en fuentes, reglas y logs; no en el razonamiento del modelo | P1 | Todos | Planteamiento: What your solution should demonstrate 6 |
| REQ-0032 | Herramientas mock con contratos y limitaciones documentados | P1 | Todos | Planteamiento: Data and execution boundaries |
| REQ-0049 | El país es configuración, no código | P2 | Todos | Propio: [AI](../construir/areas/ai.md#reglas-técnicas) |

## Datos y ML (DML)

| ID | Requerimiento | Prioridad | Flujo | Fuente |
|---|---|---|---|---|
| REQ-0014 | Problema respaldado por datos, con análisis reproducible que justifica el flujo | P0 | Todos | Planteamiento: What your solution should demonstrate 1 · Kickoff p. 13 |
| REQ-0015 | Pipeline repetible con contratos estrictos, calidad, linaje y frescura | P0 | Todos | Planteamiento: What your solution should demonstrate 4 · Kickoff p. 12 |
| REQ-0016 | Al menos un componente aprendido comparado contra una línea base sobre held-out | P0 | Todos | Planteamiento: What your solution should demonstrate 4 · Kickoff p. 12 |
| REQ-0017 | Etiquetas válidas y sin fuga de datos; justificar métricas, umbrales y divisiones | P0 | Todos | Planteamiento: What your solution should demonstrate 4 · Kickoff p. 12 |
| REQ-0020 | Línea base y sistema sobre el mismo held-out, con distribución realista | P0 | Todos | Planteamiento: Evaluation evidence · Kickoff p. 12 |
| REQ-0022 | Métricas con n, mezcla de casos, versiones y variabilidad; incluir fallas | P0 | Todos | Planteamiento: What your solution should demonstrate 5; Evaluation evidence |
| REQ-0031 | Solo datos aprobados; etiquetar cada fuente (real, sintético, generado por el equipo) | P0 | Todos | Planteamiento: Data and execution boundaries |
| REQ-0018 | Procesamiento incremental real (llegadas tardías, duplicados, esquema cambiante) o fixture etiquetado | P1 | Todos | Planteamiento: Architecture freedom |
| REQ-0019 | Tracking de experimentos: versiones de modelos y prompts, parámetros, métricas | P1 | Todos | Kickoff p. 20 |
| REQ-0024 | Desglose por idioma, país y segmento; separar offline, simulación y proyección | P1 | Todos | Planteamiento: Evaluation evidence |
| REQ-0050 | Monitoreo por país (latencia, fallas, escalamientos, quejas) | P1 | Todos | Propio: [análisis](../construir/areas/analisis.md#monitoreo-por-país) |
| REQ-0023 | Si hay LLM juez: rúbrica documentada y validada contra una muestra humana | P2 | Si aplica | Planteamiento: Evaluation evidence |

## Entrega (E)

| ID | Requerimiento | Prioridad | Flujo | Fuente |
|---|---|---|---|---|
| REQ-0034 | Repositorio público `factored-hackathon-2026-[equipo]`, sin secretos ni datos restringidos | P0 | Todos | Kickoff p. 18 |
| REQ-0035 | Link a la herramienta desplegada, con límites de uso y gasto | P0 | Todos | Kickoff p. 18 |
| REQ-0036 | Presentación de 4 a 6 diapositivas | P0 | Todos | Kickoff p. 18 |
| REQ-0037 | Video pitch corto: demo y decisiones de arquitectura | P0 | Todos | Kickoff p. 18 |
| REQ-0013 | Reportar las limitaciones de datos y de cobertura de idiomas | P0 | Todos | Planteamiento: Scope · Kickoff p. 15 |
| REQ-0030 | Declarar lo que falta: capacidad, datos, idiomas, despliegue, riesgos | P0 | Todos | Planteamiento: Scope; What your solution should demonstrate 6 · Kickoff p. 15 |

## Trabajo futuro (no son requerimientos)

- Expansión a otros países de Latinoamérica. El diseño lo facilita con REQ-0049 (país como configuración); requeriría datos, reglas, moneda y pruebas de cada país nuevo.
- Streaming: solo si un flujo necesita segundos de frescura.

## Preguntas abiertas

- ¿Qué flujo elegimos? (lunes 28/9). Con eso se confirman o descartan los requerimientos que dependen del flujo.
- ¿Cómo construimos las etiquetas de referencia para evaluar (qué casos requieren humano)?
