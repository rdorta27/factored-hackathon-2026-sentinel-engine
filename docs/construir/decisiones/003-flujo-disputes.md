# 003 · Flujo inicial: reclamos por cargos no reconocidos

**Fecha:** 2026-09-28
**Estado:** Propuesta (provisional hasta la revisión del martes 29/9)
**Participantes:** Equipo

## Contexto

Hay que elegir un flujo para empezar a construir el martes, antes de haber perfilado los datos. La presentación del 28/9 (*decisiones-2*) propone disputes como punto de partida y deja abierto el cambio si el análisis de datos no lo respalda. Opciones y comparación en [opciones de flujo](../flujos/opciones.md).

El flujo tiene que servir para demostrar a la vez: análisis de datos, conversación con herramientas, acción confirmada y verificada, handoff con evidencia y un componente aprendido frente a un baseline.

## Opciones

1. **Reclamos por cargos no reconocidos (disputes):** acción visible (abrir el reclamo), handoff natural (fraude, monto alto, caso complejo), 80K reclamos y 5M transacciones con `is_fraud`. En contra: todavía no sabemos cuántos reclamos son realmente por cargos ni si las etiquetas sirven para ML.
2. **Cuentas o pagos:** el más fácil y de menor riesgo, pero casi todo es lectura; la acción y el handoff son débiles.
3. **Tarjetas:** acción clara (bloquear, confirmar y verificar), pero menos datos propios.
4. **Crédito:** riesgo alto de cruzar límites de política; demo más difícil de defender.

## Decisión

Empezamos con **disputes** como hipótesis de trabajo. Se confirma o se cambia el martes 29/9 según los criterios siguientes, medidos sobre los datos reales.

| Criterio | Cómo se mide | Sigue disputes si… |
|---|---|---|
| Volumen relevante | Reclamos con `case_type = Claim` y categoría de cargo no reconocido; su peso en `contact_reason` de `call_center_interactions` | Hay volumen suficiente para entrenar y evaluar (umbral a fijar al ver la distribución) |
| Relación entre fuentes | % de reclamos con `origin_interaction_id` válido; % de esas interacciones con transcripción | La cadena llamada → transcripción → reclamo cubre una parte útil de los casos |
| Etiquetas | Calidad y balance de `category` / `subcategory` y de `was_escalated` | Al menos una etiqueta es consistente y no es trivial |
| ML defendible | Baseline de palabras clave frente a un modelo simple, con división temporal | El modelo mejora al baseline y el baseline no está cerca del 100 % (señal de etiquetas generadas por plantilla) |
| Fuga de datos | Revisión de variables | Solo se usan campos de apertura; los de resultado (`status`, `resolution`, `sla_breached`, etc.) quedan fuera |

Si falla el volumen o el ML, la alternativa preferida es **tarjetas** (misma estructura: confirmar, actuar, verificar y handoff por fraude).

## Consecuencias

- **Alcance:** el asistente identifica la transacción, reúne los datos, muestra hechos verificados, confirma la intención, abre el reclamo, verifica que existe y entrega el número y el siguiente paso. **No decide el fraude ni el resultado del reclamo.**
- **Handoff:** por sospecha de fraude (`is_fraud` / `fraud_score`), monto alto, cliente reincidente, información insuficiente, límite de política o pedido del cliente. El paquete sigue la sección 8 de la presentación: pedido, hechos verificados, transacciones, acciones hechas, evidencia, preguntas abiertas y motivo.
- **Llegadas tardías:** si el cargo no aparece, se abre el reclamo como *pendiente de verificación* ([conversación](../conversacion.md)).
- **Portugués:** el dataset está solo en español; los casos de prueba en portugués se definen en la decisión 15, que conviene adelantar.
- **Pendiente:** fijar los umbrales numéricos al ver los datos; elegir el componente aprendido (decisión 2) en la misma revisión.
