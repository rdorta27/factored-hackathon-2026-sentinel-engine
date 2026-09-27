# Requerimientos

Qué debe cumplir el sistema. Cada requerimiento tiene un ID que se usa en la [matriz](matriz.md).

**Para qué sirve:** priorizar el trabajo y verificar que no falte nada. **Relacionados:** [resumen del reto](../entender/resumen.md), [matriz](matriz.md), [glosario](../entender/glosario.md).

## Cómo se clasifican

| Columna | Valores |
|---|---|
| **Tipo** | **F** = funcional (qué hace) · **NF** = no funcional (cómo: seguridad, confiabilidad, operación) · **DML** = datos y ML · **E** = entrega |
| **Prioridad** | **P0** = obligatorio, días 1 a 5 · **P1** = suma puntos, días 6 a 8 · **P2** = si sobra tiempo |
| **Flujo** | "Todos", o el flujo del que depende (se define el lunes 28/9) |
| **Fuente** | **Oficial** = planteamiento o kickoff · **Propio** = decisión de diseño del equipo |

Fuentes oficiales: *planteamiento*, *kickoff* (páginas 10 a 15 y 18 a 20).

## Resumen por prioridad

| Prioridad | Cantidad | Qué incluye |
|---|---|---|
| P0 | 35 | Los 3 casos de la demo, ES y PT, verificación, permisos en código, handoff, componente aprendido vs línea base, pipeline con contratos, pruebas de fallas, entregables |
| P1 | 11 | Tracking, incremental real, observabilidad, reintentos, desglose por idioma y país, reglas de conversación finas |
| P2 | 4 | País como configuración, enrutamiento del handoff, LLM juez |

## Funcionales (F)

| ID | Requerimiento | Prioridad | Flujo | Fuente |
|---|---|---|---|---|
| R-01 | Mantener el contexto de la conversación | P0 | Todos | Oficial |
| R-02 | Aclarar solicitudes ambiguas o abstenerse ante las no soportadas | P0 | Todos | Oficial |
| R-03 | Responder solo con registros verificados; si el dato no existe, decirlo | P0 | Todos | Oficial |
| R-04 | Usar herramientas de forma segura para ejecutar el flujo | P0 | Todos | Oficial |
| R-06 | Definir qué responde solo, qué requiere confirmación y cuándo escalar | P0 | Todos | Oficial |
| R-08 | Handoff estructurado en JSON: solicitud, hechos verificados, acciones, evidencia, preguntas abiertas; sin transcripción cruda | P0 | Todos | Oficial |
| R-09 | Demo: caso normal resuelto conforme a políticas | P0 | Todos | Oficial |
| R-10 | Demo: caso ambiguo o no soportado (aclara o se abstiene) | P0 | Todos | Oficial |
| R-11 | Demo: caso que requiere humano (escala con handoff) | P0 | Todos | Oficial |
| R-12 | Interacciones robustas en español y portugués | P0 | Todos | Oficial |
| R-33 | Separar conversación, riesgo y política de elegibilidad; el LLM no aprueba ni inventa reglas | P0 | Crédito | Oficial |
| R-38 | Frontend simple para usar el sistema (ej.: chat); sin dashboard | P0 | Todos | Oficial |
| R-39 | Declarar la frescura de los datos ("actualizado hasta…"); nunca afirmar algo más reciente | P0 | Todos | Propio |
| R-40 | Pedido de hablar con una persona: una sola oferta de resolver y, si insiste, escalar de inmediato | P0 | Todos | Propio |
| R-41 | Mostrar montos en la moneda original de la transacción; idioma según el cliente, moneda según la cuenta | P0 | Todos | Propio |
| R-42 | Abrir reclamos con el mínimo esfuerzo: mostrar transacciones candidatas en vez de pedir montos | P1 | Reclamos | Propio |
| R-43 | Revisar el estado del cargo (Pending, Reversed) antes de abrir un reclamo | P1 | Reclamos, cuentas | Propio |
| R-44 | Español neutro, con siglas y términos locales explicados; entender términos de otros países | P1 | Todos | Propio |
| R-45 | Ofrecer como pregunta el contexto de errores recientes de la app | P2 | Tarjetas, app | Propio |
| R-46 | Enrutar el handoff a un asesor con el idioma y la especialidad adecuados (simulado) | P2 | Todos | Propio |

## No funcionales (NF)

| ID | Requerimiento | Prioridad | Flujo | Fuente |
|---|---|---|---|---|
| R-05 | Reportar solo acciones verificadas (timeout no es éxito) | P0 | Todos | Oficial |
| R-07 | Permisos y políticas en código, además del prompt | P0 | Todos | Oficial |
| R-21 | Pruebas de fallas: datos malos o faltantes, sesión expirada, acceso no autorizado, prompt injection, falla de herramienta, ambigüedad multilingüe | P0 | Todos | Oficial |
| R-27 | Autenticación con sesión de prueba, control de acceso por cliente, política de retención | P0 | Todos | Oficial |
| R-28 | Reproducibilidad: instalación, versionado, evaluación repetible | P0 | Todos | Oficial |
| R-47 | El LLM no recibe identificadores ni datos personales; las herramientas filtran por el cliente de la sesión | P0 | Todos | Propio |
| R-48 | Orden de decisión: política en código > predictor > LLM | P0 | Todos | Propio |
| R-25 | Observabilidad: trazas y registros de ejecución, con país e idioma | P1 | Todos | Oficial |
| R-26 | Reintentos acotados, fallback seguro; acciones idempotentes | P1 | Todos | Oficial |
| R-29 | Explicaciones basadas en fuentes, reglas y logs; no en el razonamiento del modelo | P1 | Todos | Oficial |
| R-32 | Herramientas mock con contratos y limitaciones documentados | P1 | Todos | Oficial |
| R-49 | El país es configuración, no código | P2 | Todos | Propio |

## Datos y ML (DML)

| ID | Requerimiento | Prioridad | Flujo | Fuente |
|---|---|---|---|---|
| R-14 | Problema respaldado por datos, con análisis reproducible que justifica el flujo | P0 | Todos | Oficial |
| R-15 | Pipeline repetible con contratos estrictos, calidad, linaje y frescura | P0 | Todos | Oficial |
| R-16 | Al menos un componente aprendido comparado contra una línea base sobre held-out | P0 | Todos | Oficial |
| R-17 | Etiquetas válidas y sin fuga de datos; justificar métricas, umbrales y divisiones | P0 | Todos | Oficial |
| R-20 | Línea base y sistema sobre el mismo held-out, con distribución realista | P0 | Todos | Oficial |
| R-22 | Métricas con n, mezcla de casos, versiones y variabilidad; incluir fallas | P0 | Todos | Oficial |
| R-31 | Solo datos aprobados; etiquetar cada fuente (real, sintético, generado por el equipo) | P0 | Todos | Oficial |
| R-18 | Procesamiento incremental real (llegadas tardías, duplicados, esquema cambiante) o fixture etiquetado | P1 | Todos | Oficial |
| R-19 | Tracking de experimentos: versiones de modelos y prompts, parámetros, métricas | P1 | Todos | Oficial |
| R-24 | Desglose por idioma, país y segmento; separar offline, simulación y proyección | P1 | Todos | Oficial |
| R-50 | Monitoreo por país (latencia, fallas, escalamientos, quejas) | P1 | Todos | Propio |
| R-23 | Si hay LLM juez: rúbrica documentada y validada contra una muestra humana | P2 | Si aplica | Oficial |

## Entrega (E)

| ID | Requerimiento | Prioridad | Flujo | Fuente |
|---|---|---|---|---|
| R-34 | Repositorio público `factored-hackathon-2026-[equipo]`, sin secretos ni datos restringidos | P0 | Todos | Oficial |
| R-35 | Link a la herramienta desplegada, con límites de uso y gasto | P0 | Todos | Oficial |
| R-36 | Presentación de 4 a 6 diapositivas | P0 | Todos | Oficial |
| R-37 | Video pitch corto: demo y decisiones de arquitectura | P0 | Todos | Oficial |
| R-13 | Reportar las limitaciones de datos y de cobertura de idiomas | P0 | Todos | Oficial |
| R-30 | Declarar lo que falta: capacidad, datos, idiomas, despliegue, riesgos | P0 | Todos | Oficial |

## Trabajo futuro (no son requerimientos)

- Expansión a otros países de Latinoamérica. El diseño lo facilita con R-49 (país como configuración); requeriría datos, reglas, moneda y pruebas de cada país nuevo.
- Streaming: solo si un flujo necesita segundos de frescura.

## Preguntas abiertas

- ¿Qué flujo elegimos? (lunes 28/9). Con eso se confirman o descartan los requerimientos que dependen del flujo.
- ¿Cómo construimos las etiquetas de referencia para evaluar (qué casos requieren humano)?
