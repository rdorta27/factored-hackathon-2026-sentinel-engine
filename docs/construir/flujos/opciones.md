# Opciones de flujo

Cinco opciones de flujo para elegir el lunes 28/9, con un stack sugerido.

**Para qué sirve:** insumo para la decisión del flujo. **Estado:** propuesta escrita antes de leer el diccionario de datos; conviene revisarla con lo que aprendimos (etiquetas disponibles, `fraud_score` como línea base, predictor de escalamiento). **Relacionados:** [dataset](../../entender/dataset.md), [requerimientos](../../requerimientos/requerimientos.md), [ML](../areas/ml.md).

Fuentes: *planteamiento*, *resumen del dataset*, *diccionario*.

## Restricciones comunes

- **Equipo:** 3 personas durante ~7 días. Se elige **un** solo flujo; el planteamiento dice que implementar más flujos no suma puntos.
- **Backend pequeño y gratis (stack base sugerido):**
  - Datos: Parquet + **DuckDB** local. No hace falta servidor de base de datos, y los 19M de filas caben en una laptop.
  - API: **FastAPI** con herramientas mock del banco (contratos documentados) y sesión de prueba firmada (JWT) para la autenticación.
  - Retrieval: embeddings multilingües open source (`multilingual-e5-small`) guardados en DuckDB o FAISS.
  - LLM: modelo open-weights local vía **Ollama** (Qwen 2.5 7B o Llama 3.1 8B), o el free tier de Gemini/Groq, pero **solo** con datos sintéticos. El enunciado prohíbe mandar datos restringidos a modelos externos.
  - Deploy opcional: Hugging Face Spaces o Render free tier. Trazas en SQLite/JSONL o Langfuse self-hosted.
- **Requisitos del enunciado que aplican a todas las opciones:** camino de resolución normal, caso ambiguo o no soportado, caso con handoff humano, demo en **español y portugués**, al menos un componente aprendido evaluado contra una línea base, y conjunto de prueba held-out con casos de prompt injection, sesión expirada, acceso no autorizado y falla de herramienta.
- **Expansión a otros mercados:** cada opción aísla lo específico del país en configuración: moneda, tipo de documento (CURP/CC/DNI → CPF), políticas en YAML, idioma y regulador. Agregar Brasil, Chile o Perú significa agregar un archivo de configuración y documentos de política, no escribir código nuevo.

---

## 1. Consultas de transacciones: "no reconozco este cargo / ¿por qué se rechazó?"

**Problema:** Buena parte del volumen del call center es transaccional: pagos rechazados, pendientes o revertidos, y cargos no reconocidos. El asistente autentica al cliente, busca la transacción, explica el estado con los datos reales y, si el cliente no la reconoce, abre el reclamo o escala.

- **Datos:** `transactions` (status Approved/Declined/Pending/Reversed, merchant_category, channel), `call_center_interactions` (contact_reason, reason_category = Transactional), `complaints`.
- **Componente aprendido:** clasificador de intención (TF-IDF + regresión logística como línea base vs. embeddings multilingües) entrenado con `contact_reason` y transcripciones. La división es por tiempo, sin partir un caso y con variables que solo usen información anterior (ver [ML](../areas/ml.md#rigor)).
- **Controles deterministas:** la herramienta `get_transactions(customer_id)` valida la sesión; el LLM nunca decide montos ni estados.
- **Handoff:** fraude sospechado, monto mayor a un umbral o cliente que insiste → ticket con los hechos verificados.
- **Por qué cabe en 1 semana:** una tabla principal, 3–4 herramientas y un flujo corto.
- **Expansión:** los códigos de rechazo y las políticas por país van en configuración; el flujo es igual en cualquier banco.

## 2. Apertura y clasificación de reclamos (PQR)

**Problema:** Convertir una conversación libre en un reclamo bien estructurado (categoría, subcategoría, transacción vinculada, evidencia) y enrutarlo a la cola correcta con prioridad. Hoy los reclamos mal categorizados se reabren o se escalan al regulador.

- **Datos:** `complaints` (case_type, category, subcategory, reception_channel incluyendo *Regulator*, status Escalated/Rejected), `transactions`, `satisfaction_surveys`.
- **Componente aprendido:** clasificador de categoría y subcategoría, más un modelo de riesgo de escalamiento (probabilidad de que el caso termine en *Escalated* o llegue por el regulador). La línea base son reglas por palabras clave.
- **Controles deterministas:** plazos legales y campos obligatorios por país como reglas. El sistema **no** resuelve el reclamo: solo lo abre, lo clasifica y lo enruta.
- **Handoff:** el paquete para el agente (resumen, hechos verificados, evidencia y preguntas abiertas) es justamente el entregable principal.
- **Por qué cabe en 1 semana:** no mueve dinero, así que el riesgo es bajo y la métrica es clara (accuracy de enrutamiento y completitud).
- **Expansión:** las taxonomías de reclamos y los SLA regulatorios (Condusef, SFC, BCRA, Bacen) se mapean por país.

## 3. Soporte de tarjetas: bloqueo, desbloqueo y estado de la tarjeta

**Problema:** "Perdí mi tarjeta", "mi tarjeta está bloqueada" o "¿por qué no funciona?". Un flujo con acciones concretas que requieren confirmación explícita, ideal para mostrar automatización controlada.

- **Datos:** `products` (Credit/Debit Card, product_status Active/Blocked/Suspended), `transactions` (rechazos recientes), `digital_events` (errores de login o de transacción), `call_center_interactions`.
- **Componente aprendido:** clasificador de intención y detector de "urgencia o posible fraude" evaluado contra reglas.
- **Controles deterministas:** máquina de estados de la tarjeta; cada acción (`block_card`) exige sesión válida y confirmación del cliente, y se reporta como hecha solo si la herramienta la confirmó. El desbloqueo después de un fraude va siempre a un humano.
- **Handoff:** reposición de tarjeta, fraude o datos inconsistentes.
- **Por qué cabe en 1 semana:** pocas acciones, estados bien definidos y fáciles de testear.
- **Expansión:** la lógica de la tarjeta es universal; solo cambian los textos y la política de reposición de cada mercado.

## 4. Diagnóstico de problemas de la app y del acceso digital

**Problema:** Clientes que llaman porque no pueden hacer login, un pago falla en la app o les da error. El asistente cruza lo que dice el cliente con sus `digital_events` recientes para diagnosticar (error de autenticación, canal, versión) y guiar la solución o escalar a soporte técnico.

- **Datos:** `digital_events` (10M filas: event_type Error/Login, event_category Authentication, channel Android/iOS/Web), `call_center_interactions` (reason_category Technical).
- **Componente aprendido:** retrieval de artículos de ayuda (se escribe una KB sintética pequeña, etiquetada como tal) con relevance labels y evaluación recall@k contra BM25. Opcionalmente, un modelo que predice qué secuencias de eventos generan una llamada.
- **Controles deterministas:** el asistente nunca resetea credenciales; eso se deriva a un flujo seguro.
- **Handoff:** bugs nuevos o cuenta bloqueada por seguridad.
- **Por qué cabe en 1 semana:** es solo lectura, sin acciones riesgosas, y la historia de datos es muy visual (errores → llamadas).
- **Expansión:** la KB se traduce o regionaliza y los eventos digitales son iguales en cualquier mercado.

## 5. Información de productos de crédito y elegibilidad simulada

**Problema:** "¿Puedo sacar un préstamo o aumentar mi cupo?". El asistente explica los productos con fuentes de política, calcula una elegibilidad **simulada** con un servicio de reglas sintético y explica el porqué, sin aprobar crédito.

- **Datos:** `customers`, `products` (Personal Loan, Credit Card y sus saldos), `transactions` (ingresos y gastos), `marketing_campaigns`/`campaign_sends`.
- **Componente aprendido:** estimación de riesgo (gradient boosting) **separada** de la política de elegibilidad y del manejo de la conversación, como exige el enunciado. La línea base son reglas simples.
- **Controles deterministas:** el servicio de política (reglas YAML etiquetadas como sintéticas) produce el resultado; el LLM solo lo comunica. Los casos borderline o con datos faltantes van a revisión humana.
- **Riesgo:** es la opción con más requisitos (fairness por segmento, explicabilidad, incertidumbre) y la más ambiciosa para una semana.
- **Expansión:** la política por país vive en configuración y el modelo de riesgo se recalibra por mercado.

---

## Recomendación

| # | Opción | Esfuerzo | Riesgo de scope | Riqueza de datos | Demo |
|---|---|---|---|---|---|
| 1 | Transacciones | Bajo | Bajo | Alta | Buena |
| 2 | Reclamos (PQR) | Medio | Bajo | Alta | Muy buena |
| 3 | Tarjetas | Bajo | Bajo | Media | Muy buena |
| 4 | App/acceso digital | Medio | Medio | Muy alta | Buena |
| 5 | Crédito/elegibilidad | Alto | Alto | Media | Buena |

Para un equipo de 3 en una semana, recomendamos la **opción 1 o una combinación 1+2**: consultar la transacción y, si el cliente no la reconoce, abrir el reclamo. Es un solo flujo coherente con camino normal, caso ambiguo y handoff naturales.

Reparto sugerido:
- **Persona A:** pipeline de datos (DuckDB, quality checks, contratos, lineage).
- **Persona B:** clasificador y evaluación (línea base vs. modelo, set held-out, métricas).
- **Persona C:** API, herramientas, orquestación del LLM, guardrails y demo en ES/PT.
