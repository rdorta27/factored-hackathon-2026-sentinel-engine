# Dataset

Referencia del dataset LATAM Bank: qué hay, qué columna sirve para qué y qué cuidados tener.

**Para qué sirve:** consultar tablas y columnas sin abrir el diccionario oficial. **Relacionados:** [área de datos](../construir/areas/datos.md) (pipeline), [ML](../construir/areas/ml.md) (etiquetas y variables), [glosario](glosario.md).

Fuentes: *resumen del dataset*, *diccionario de datos*.

## Contenido

- [El dataset](#el-dataset-resumen-oficial) · [Tablas](#tablas) · [Clientes y productos](#diccionario-clientes-y-productos) · [Dimensiones de apoyo](#diccionario-dimensiones-de-apoyo) · [Transacciones](#diccionario-transacciones) · [Contacto con el cliente](#diccionario-contacto-con-el-cliente) · [Reclamos](#diccionario-reclamos) · [Canales digitales](#diccionario-canales-digitales-y-campañas) · [Relaciones](#relaciones-entre-tablas) · [Cuidados](#cuidados-generales)

## El dataset (resumen oficial)

- LATAM Bank v1.0.0: ~19 millones de registros, 13 tablas, **100 % sintético**.
- Países: México, Colombia, Argentina. Periodo: 2023-06-17 a 2026-06-17.
- Monedas: MXN, COP, ARS y USD (tipos de cambio diarios).
- Texto solo en **español** (acentos mexicano, colombiano y argentino).

### Problemas de calidad intencionales

| Problema | Tasa | Qué implica |
|---|---|---|
| Duplicados | ~2 % | Deduplicación documentada y medida |
| Nulos | ~5 % | En campos no obligatorios; el contrato define cuáles pueden ser nulos |
| Llegadas tardías | Sí | Procesamiento **incremental** y política de frescura reales, no solo un fixture |
| Evolución de esquema | Sí | Contratos versionados |

Son una prueba de ingeniería de datos: se manejan, se documentan y se miden; no se borran en silencio.

## Tablas

| Tipo | Tabla | Filas | Uso probable |
|---|---|---|---|
| Dimensión | customers | 150.000 | Clientes; base del aislamiento por cliente |
| Dimensión | products | 400.000 | Productos financieros activos |
| Dimensión | branches | 350 | Sucursales |
| Dimensión | service_agents | 1.200 | Asesores del call center |
| Dimensión | marketing_campaigns | 200 | Campañas |
| Hechos | transactions | 5.000.000 | Movimientos; consultas y reclamos por cargos |
| Hechos | call_center_interactions | 800.000 | Motivos de contacto, resolución, escalamiento |
| Hechos | call_transcripts | 200.000 | Texto para intención (cubre ~25 % de las interacciones: revisar sesgo) |
| Hechos | satisfaction_surveys | 250.000 | CSAT y NPS |
| Hechos | digital_events | 10.000.000 | App y web; muestrear |
| Hechos | complaints | 80.000 | PQR |
| Hechos | campaign_sends | 2.000.000 | Envíos de campañas |
| Referencia | daily_exchange_rates | 3.000 | Tipos de cambio diarios |

Enfoque: explorar primero las tablas ligadas al flujo elegido y muestrear las grandes; procesar a escala solo lo que el sistema necesita.

## Diccionario: clientes y productos

| Tabla | Partición | Columnas clave | Cuidado |
|---|---|---|---|
| customers | Foto mensual | customer_id, country, detected_accent (incluye "neutral"), **segment** (Premium, Plus, Basic, Student), credit_score, estimated_monthly_income, customer_status, last_updated | Datos personales (documento, nombre, email, teléfono, dirección): nunca al LLM |
| products | Foto mensual | product_id, customer_id, product_type, currency, **current_balance**, credit_limit, product_status (Active, Blocked, Closed, Suspended), days_past_due, last_transaction_date | El saldo es el de la última foto: calcularlo con transacciones posteriores o informar la fecha de corte |

- Para variables de ML, usar la **última foto anterior a la fecha del caso** (nunca la más reciente).

## Diccionario: dimensiones de apoyo

| Tabla | Partición | Columnas clave | Uso probable |
|---|---|---|---|
| branches | Foto completa | branch_type, dirección, opening_time / closing_time, has_atms, branch_status | Si el flujo deriva a una sucursal: horarios y estado |
| service_agents | Foto mensual | native_accent, agent_type, experience_level, **languages**, **specialty**, avg_csat, total_monthly_interactions, agent_status | **Enrutar el handoff** (simulado): asesor que hable el idioma del cliente y tenga la especialidad del flujo |
| marketing_campaigns | Foto completa | campaign_type, campaign_objective, promoted_product, target_segment, target_country, start_date / end_date | Explicar picos de demanda por fecha y país |

- `avg_csat` y `total_monthly_interactions` son del último mes e incluyen los casos de ese mes: como variables, usar la **foto del mes anterior** al caso.
- Datos personales de asesores (nombre, email, teléfono): no se exponen al cliente ni al LLM.

## Diccionario: transacciones

| Tabla | Partición | Columnas clave |
|---|---|---|
| transactions | Diaria (`process_date`) | transaction_id, **transaction_date**, **process_date**, product_id, customer_id, transaction_type, amount, currency, amount_usd (puede ser nulo), channel, merchant_name, transaction_country, **transaction_status** (Approved, Declined, Pending, Reversed), **is_fraud**, **fraud_score** (0-100) |
| daily_exchange_rates | Diaria | date, source_currency, target_currency, exchange_rate, buy_rate, sell_rate |

- **Dos fechas:** `process_date` para el pipeline (qué particiones leer, watermark); `transaction_date` para responder al cliente y para la división por tiempo. La diferencia entre ambas mide las llegadas tardías.
- `amount_usd` nulo: recalcular con `daily_exchange_rates` de la fecha de la transacción, o dejarlo nulo y contarlo; no inventarlo.
- `product_status = Blocked` es el estado que modificaría una acción de bloqueo de tarjeta.

## Diccionario: contacto con el cliente

| Tabla | Partición | Columnas clave |
|---|---|---|
| call_center_interactions | Diaria | interaction_date, customer_id, agent_id, interaction_type, channel, **contact_reason**, **reason_category** (Transactional, Product, Technical, Commercial, Complaint), duration_seconds, wait_time_seconds, **was_resolved** (FCR), **requires_followup**, detected_sentiment, **was_escalated** (a supervisor), has_transcript |
| call_transcripts | Diaria | interaction_id, full_text, **customer_text**, agent_text, detected_language, detected_accent, detected_keywords, mentioned_entities (JSON), **detected_intents**, main_topics, transcription_model, audio_quality |
| satisfaction_surveys | Diaria | survey_date, interaction_id, survey_type (CSAT, NPS, CES), main_score, nps_category, open_comments, **response_time_hours** |

- Motivos de contacto y su categoría: base del análisis que justifica el flujo.
- Las encuestas llegan después de la interacción: son métricas de resultado, no variables.

## Diccionario: reclamos

| Tabla | Partición | Columnas clave |
|---|---|---|
| complaints | Diaria | creation_date, customer_id, **case_type** (Complaint = queja, Claim = reclamo, Request = petición, Suggestion = sugerencia), category, subcategory, reception_channel (incluye Regulator), affected_product_id, **origin_interaction_id**, description, claimed_amount, currency, priority, **status** (Open, In Process, Escalated, Resolved, Closed, Rejected), fechas de asignación, primera respuesta, resolución y cierre, **sla_breached**, resolution_days, resolution, compensation_granted, resolution_satisfaction, **is_repeat_complainer** (reclamos en los últimos 90 días) |

- **Campos de apertura** (los completa el asistente): case_type, category, affected_product_id, description, claimed_amount, currency, reception_channel, origin_interaction_id. **Campos de ciclo de vida y resultado** (los define el banco después): status, asignación, fechas, resolución, compensación, satisfacción.
- Como variables de ML, los campos de resultado son información del futuro.
- `is_repeat_complainer`: verificar si se calculó con los 90 días previos a cada caso; si no se puede confirmar, recalcularlo con reclamos anteriores.
- `origin_interaction_id` une el reclamo con la llamada que lo originó.

## Diccionario: canales digitales y campañas

| Tabla | Partición | Columnas clave |
|---|---|---|
| digital_events | Diaria | event_date, customer_id (**puede ser nulo**: eventos antes del login), session_id, **event_type** (PageView, Click, FormSubmit, Login, Logout, **Error**, Purchase), event_category, channel, platform, app_version, page_url, action, product_id, **ip_address**, **ip_country**, ip_city, UTM |
| campaign_sends | Diaria | send_date, campaign_id, customer_id, send_channel, send_status, was_delivered, was_opened, was_clicked, **had_conversion**, conversion_value, **send_cost** |

- **Errores de la app:** suelen preceder a una llamada o reclamo. Cruzarlos por cliente y fecha para el análisis de demanda y para dar contexto en la conversación.
- **IP:** dato personal. No va al LLM, se enmascara en los logs y se usa solo en código.
- **País de la IP distinto del país de la cuenta:** señal de riesgo, no veredicto (viaje, familia, VPN). Sirve para el componente de fraude o para pedir verificación extra en acciones sensibles; nunca bloquear ni discriminar por origen.
- Tabla de 10 millones de filas: muestrear para explorar.

## Relaciones entre tablas

- `customer_id` enlaza 8 tablas con `customers`. Es el **filtro obligatorio** de toda herramienta que lea datos de clientes: siempre el de la sesión autenticada, nunca elegido por el LLM.
- Cadena de atención: `call_center_interactions` → `call_transcripts` y `satisfaction_surveys` (por `interaction_id`) → `complaints` (por `origin_interaction_id`).
- **Nulo no es huérfano:** un `customer_id` nulo en `digital_events` es válido (evento antes del login); un `customer_id` que no existe en `customers` es huérfano y va a cuarentena. El contrato los distingue.

## Cuidados generales

- Montos siempre con su moneda. Al cliente se le muestra la **moneda original** de la transacción (casi siempre la local; puede ser USD). El monto en USD es para análisis entre países.
- **Registros huérfanos** (ej.: transacción de un cliente inexistente): incluidos a propósito. Se detectan con el contrato, van a cuarentena, se cuentan y nunca se devuelven como datos de un cliente.
- Aunque los datos sean sintéticos, se aplican igual los controles de acceso y privacidad, y se declaran como sintéticos en el inventario.
- Pendiente de confirmar cuando lleguen los datos: si hay varias fotos mensuales y cómo se calculó `is_repeat_complainer`.
