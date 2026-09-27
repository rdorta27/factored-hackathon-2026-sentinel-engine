# Machine Learning

**Criterio de evaluación:** selección, optimización, implementación y tracking de modelos. **Responsable:** por definir.

**Requerimientos:** REQ-0012 (ES y PT robustos), REQ-0016 (componente vs línea base), REQ-0017 (sin fuga), REQ-0019 (tracking), REQ-0020 (held-out), REQ-0021 (pruebas de fallas), REQ-0023 (LLM juez), REQ-0033 (separación en crédito, si aplica), REQ-0048 (orden de decisión). Ver [requerimientos](../../requerimientos/requerimientos.md).

**Relacionados:** [dataset](../../entender/dataset.md) (etiquetas y columnas), [métricas](../metricas.md), [arquitectura](../../entender/arquitectura.md).

## Qué construye esta área

- Orquestación **LLM / RAG**.
- **Defensa contra prompt injection** (junto con el control de acceso de [seguridad](../seguridad.md)).
- Al menos un **componente aprendido** comparado contra una **línea base** sobre held-out.
- **Tracking de experimentos** (ej.: MLflow): versiones de modelos y prompts, parámetros, métricas.

## Componentes candidatos

| Componente | Métrica | Línea base |
|---|---|---|
| Clasificador de intención o motivo | accuracy, F1 por clase | Palabras clave, clase mayoritaria o `detected_intents` (intenciones que ya trae el dataset, generadas por otro modelo) |
| Retrieval de políticas (RAG) | recall@k, MRR | BM25 |
| Modelo de riesgo (solo crédito) | AUC, calibración | Regresión logística o regla fija |
| Detección de fraude (tarjetas o reclamos) | AUC, precisión y recall a un umbral | `fraud_score` existente del banco |

Intención: la entrada es `customer_text` (solo lo que dijo el cliente, que es lo único que el asistente tiene al empezar); la etiqueta es `contact_reason`. `agent_text` y `full_text` incluyen la respuesta del asesor y filtran la solución. Solo ~25 % de las interacciones tiene transcripción: revisar sesgo.

Fraude: `is_fraud` es la etiqueta (y nunca una variable: es la respuesta, y probablemente se marca después, por un reclamo). `fraud_score` es el modelo actual del banco: la línea base.

Sin entrenar un modelo, el rigor se demuestra con: selección de componentes, etiquetas de relevancia o intención, representaciones, prevención de fuga, evaluación held-out y análisis de errores.

## Candidato: predictor de escalamiento

Predice si un caso se resolverá sin escalar, a partir del historial de interacciones del call center (idea de resolución en el primer contacto, FCR).

- Línea base: reglas simples (ej.: escalar siempre si el motivo es X).
- Participa en el ciclo: ayuda a **decidir cuándo escalar**.
- Aplica a cualquier flujo.
- **Etiqueta:** `was_escalated` significa escalado **a un supervisor** (de un asesor humano a otro), no del asistente a un asesor. Es una **aproximación declarada**: combinarla con `was_resolved` (resuelto en el primer contacto) y `requires_followup`, y validar una muestra a mano.
- **Etiqueta complementaria:** "la llamada terminó en un reclamo" (`complaints.origin_interaction_id`). Es otra señal de que no se resolvió bien; como el reclamo ocurre después, es etiqueta, nunca variable.
- **Variables prohibidas:** todo lo que ocurre después o al final de la interacción (encuesta, duración, sentimiento final). De interacciones anteriores sirven solo las encuestas **respondidas antes** de la hora del caso (la tabla trae las horas entre la interacción y la respuesta).
- **Umbral:** decisión de negocio medida. Se elige en el set de desarrollo (nunca en el held-out), equilibrando transferencias omitidas (riesgo) e innecesarias (costo), y se registra en [decisiones](../decisiones/).
- No decide sobre los casos con regla de política (ej.: pedido explícito de un asesor); ver [conversación](../conversacion.md#cuando-el-cliente-pide-hablar-con-una-persona).

Descartado como componente aprendido: segmentación de clientes (sin etiquetas válidas para compararla contra una línea base, y no participa en la conversación). Sirve para análisis y equidad.

## Rigor

- **Fuga de datos**, tres formas de evitarla:
  1. **Por unidad:** un caso (una queja, una interacción con todos sus mensajes) queda entero de un solo lado; nunca partido.
  2. **Por tiempo:** entrenar con lo antiguo y probar con lo reciente (ej.: con la proporción ~70/30 de [métricas](../metricas.md), entrenar hasta mediados de 2025 y probar desde ahí hasta jun. 2026). Es la división principal: simula producción, donde el modelo aprende del pasado y predice lo que viene. Un mismo cliente puede tener casos antiguos en entrenamiento y recientes en prueba; eso es realista. Separar por cliente solo si queremos medir clientes nuevos.
  3. **Por variables:** cada variable se calcula solo con información anterior a la fecha y hora del caso (ej.: "¿escaló antes?" cuenta solo escalaciones previas).
- Una división aleatoria "ve el futuro" e infla la métrica (ej.: 94 % aleatoria frente a 81 % por tiempo). Es el mismo modelo: lo que cambia es la medición. Reportar la división por tiempo, junto a la línea base en la misma división. Más datos no corrigen una mala división.
- **Held-out:** se mide una sola vez al final; mejorar el sistema con el set de desarrollo.
- **Multilingüe:** el componente debe funcionar en PT sin datos de entrenamiento en PT (ver [idiomas](../idiomas.md)).
- **LLM juez:** rúbrica documentada y validada contra una muestra humana.

## Evidencia para la evaluación

- [ ] Tabla componente vs línea base sobre held-out, con n
- [ ] Análisis de errores
- [ ] Registro de experimentos
- [ ] Set adversarial y sus resultados (dueño: ML; los casos de seguridad los propone AI, ver [seguridad](../seguridad.md))

## Decisiones pendientes

- Qué componente aprendido evaluamos
- Herramienta de tracking
