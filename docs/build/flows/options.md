# Opciones de flujo

Las cuatro opciones del planteamiento original, con un stack sugerido. La propuesta actual es el flujo de disputas de transacciones: ver la [decisión 003](../decisiones/003-flujo-disputas.md).

**Para qué sirve:** insumo para la decisión del flujo. **Estado:** propuesta revisada contra el planteamiento original, el kickoff, el resumen del dataset y el diccionario. **Relacionados:** [dataset](../../entender/dataset.md), [requerimientos](../../requerimientos/requerimientos.md), [ML](../areas/ml.md).

Fuentes: *planteamiento* (Scope: account or payment inquiries, card-service support, transaction-dispute intake, credit-product information and eligibility support), *kickoff p. 10*, *resumen del dataset*, *diccionario*.

## Restricciones comunes

- **Equipo:** 3 personas, con entrega el lunes 5/10 (sprint oficial de 10 días desde el 25/9). Elegimos **un** flujo coherente; según el planteamiento, las opciones son ejemplos y no categorías separadas, e implementar más flujos no da bonificación automática.
- **Backend pequeño en Azure (stack base sugerido, alineado con la [decisión 001](../decisiones/001-plataforma-azure.md)):**
  - Datos: Parquet + **DuckDB** local para desarrollo; despliegue en Azure. Los 19M de filas caben en una laptop para explorar.
  - API: **FastAPI** con herramientas mock del banco (contratos documentados) y sesión de prueba firmada (JWT) para la autenticación.
  - Retrieval: embeddings multilingües open source (`multilingual-e5-small`) guardados en DuckDB o FAISS.
  - LLM: **Azure OpenAI** (verificar disponibilidad en la región y que no retiene datos ni los usa para entrenar). Solo datos sintéticos aprobados; nada restringido a modelos externos.
  - Despliegue: Azure Container Apps o App Service. Trazas en SQLite/JSONL.
- **Requisitos del enunciado que aplican a todas las opciones:** camino de resolución normal, caso ambiguo o no soportado, caso con handoff humano, demo en **español y portugués**, al menos un componente aprendido evaluado contra un baseline, y conjunto de prueba held-out con casos de prompt injection, sesión expirada, acceso no autorizado y falla de herramienta.
- **Expansión a otros mercados:** cada opción aísla lo específico del país en configuración: moneda, tipo de documento (CURP/CC/DNI → CPF), políticas en YAML, idioma y regulador. Agregar Brasil, Chile o Perú significa agregar un archivo de configuración y documentos de política, no escribir código nuevo.

---

## 1. Consultas de cuenta o pagos (account / payment inquiries)

**Problema:** volumen transaccional del call center: saldos, movimientos, pagos rechazados, pendientes o revertidos. El asistente autentica al cliente, consulta saldos y movimientos, explica el estado con datos reales y abre un reclamo solo si el cliente no reconoce un cargo.

- **Datos:** `products` (saldos, estado), `transactions` (status Approved/Declined/Pending/Reversed, merchant_category, channel), `call_center_interactions` (reason_category = Transactional).
- **Componente aprendido:** clasificador de intención (TF-IDF + regresión logística como baseline vs. embeddings multilingües) entrenado con `contact_reason` y transcripciones. La división es por tiempo, sin partir un caso y con variables que solo usen información anterior (ver [ML](../areas/ml.md#rigor)).
- **Controles deterministas:** la herramienta `get_transactions(customer_id)` valida la sesión; el LLM nunca decide montos ni estados.
- **Handoff:** monto mayor a un umbral o cliente que insiste → ticket con los hechos verificados.
- **Por qué cabe en el plazo:** una tabla principal, 3–4 herramientas y un flujo corto.
- **Expansión:** los códigos de rechazo y las políticas por país van en configuración; el flujo es igual en cualquier banco.

## 2. Disputas de transacciones (transaction-dispute intake)

**Problema:** el cliente no reconoce un cargo y pide revertirlo. Convertir la conversación libre en un reclamo bien estructurado (categoría, transacción vinculada, evidencia) y enrutarlo a la cola correcta. Hoy los reclamos mal categorizados se reabren o se escalan al regulador.

- **Datos:** `complaints` (case_type = Claim, category, subcategory, reception_channel incluyendo *Regulator*, status Escalated/Rejected), `transactions`, `satisfaction_surveys`.
- **Componente aprendido:** clasificador de categoría y subcategoría, más un modelo de riesgo de escalamiento (probabilidad de que el caso termine en *Escalated* o llegue por el regulador). El baseline son reglas por palabras clave.
- **Controles deterministas:** plazos legales y campos obligatorios por país como reglas. El sistema **no** resuelve el reclamo: solo lo abre, lo clasifica y lo enruta.
- **Handoff:** el paquete para el asesor (resumen, hechos verificados, evidencia y preguntas abiertas) es justamente el entregable principal.
- **Por qué cabe en el plazo:** no mueve dinero, así que el riesgo es bajo y la métrica es clara (accuracy de enrutamiento y completitud).
- **Expansión:** las taxonomías de reclamos y los plazos regulatorios (SLA, acuerdo de nivel de servicio) de cada país (Condusef y CNBV en MX, SFC en CO, BCRA en AR; Banco Central do Brasil si se expande) se mapean por país.

## 3. Soporte de tarjetas (card-service support)

**Problema:** "Perdí mi tarjeta", "mi tarjeta está bloqueada" o "¿por qué no funciona?". Un flujo con acciones concretas que requieren confirmación explícita, ideal para mostrar automatización controlada.

- **Datos:** `products` (Credit/Debit Card, product_status Active/Blocked/Suspended), `transactions` (rechazos recientes), `digital_events` (errores de login o de transacción), `call_center_interactions`.
- **Componente aprendido:** clasificador de intención y detector de "urgencia o posible fraude" evaluado contra reglas.
- **Controles deterministas:** máquina de estados de la tarjeta; cada acción (`block_card`) exige sesión válida y confirmación del cliente, y se reporta como hecha solo si la herramienta la confirmó. El desbloqueo después de un fraude va siempre a un humano.
- **Handoff:** reposición de tarjeta, fraude o datos inconsistentes.
- **Por qué cabe en el plazo:** pocas acciones, estados bien definidos y fáciles de probar.
- **Expansión:** la lógica de la tarjeta es universal; solo cambian los textos y la política de reposición de cada mercado.

## 4. Información de productos de crédito y elegibilidad simulada (credit-product info & eligibility support)

**Problema:** "¿Puedo sacar un préstamo o aumentar mi cupo?". El asistente explica los productos con fuentes de política, calcula una elegibilidad **simulada** con un servicio de reglas sintético y explica el porqué, sin aprobar crédito.

- **Datos:** `customers`, `products` (Personal Loan, Credit Card y sus saldos), `transactions` (ingresos y gastos), `marketing_campaigns`/`campaign_sends`.
- **Componente aprendido:** estimación de riesgo (gradient boosting) **separada** de la política de elegibilidad y del manejo de la conversación, como exige el enunciado. El baseline son reglas simples.
- **Controles deterministas:** el servicio de política (reglas YAML etiquetadas como sintéticas) produce el resultado; el LLM solo lo comunica. Los casos límite o con datos faltantes van a revisión humana.
- **Riesgo:** es la opción con más requisitos (equidad por segmento, explicabilidad, incertidumbre) y la más ambiciosa para el plazo.
- **Expansión:** la política por país vive en configuración y el modelo de riesgo se recalibra por mercado.

---

## Fuera de alcance: diagnóstico de app / acceso digital

La evaluamos como 5ª opción y la **descartamos**: no está entre los ejemplos del planteamiento original (account/payment, card, disputes, credit) y elegirla arriesga la evaluación. Los errores de `digital_events` los usamos solo como **contexto** dentro del flujo elegido (ej.: ofrecer como pregunta si la consulta tiene que ver con una falla reciente), no como flujo propio.

---

## Comparación

Estimación inicial para discutir; no es una recomendación.

| # | Opción (término oficial) | Esfuerzo | Riesgo de alcance | Riqueza de datos | Demo |
|---|---|---|---|---|---|
| 1 | Account / payment inquiries | Bajo | Bajo | Alta | Buena |
| 2 | Transaction disputes | Medio | Bajo | Alta | Muy buena |
| 3 | Card support | Bajo | Bajo | Media | Muy buena |
| 4 | Credit-product info & eligibility | Alto | Alto | Media | Buena |

El reparto de áreas lo decidimos aparte (ver [decisiones pendientes](../../../team/decisiones-pendientes.md)).
