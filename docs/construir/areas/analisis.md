# Data Analytics

**Criterio de evaluación:** calidad de datos e insights relevantes de la solución. **Responsable:** por definir.
**Requerimientos:** REQ-0013 (limitaciones), REQ-0014 (problema respaldado por datos), REQ-0022 (métricas), REQ-0024 (desgloses), REQ-0030 (lo que falta), REQ-0050 (monitoreo por país). Ver [requerimientos](../../requerimientos/requerimientos.md).
**Relacionados:** [dataset](../../entender/dataset.md), [métricas](../metricas.md), [opciones de flujo](../flujos/opciones.md).

## Qué construye esta área

- **Análisis que justifica el flujo**: motivos de contacto, patrones de demanda, calidad de datos, restricciones operativas. Debe ser reproducible (notebook o script que cualquiera re-ejecuta y obtiene las mismas cifras).
- **Línea base** y resultados esperados para cliente y negocio.
- **Reportes de métricas** generados con scripts sobre los logs (ver [métricas](../metricas.md)).
- **ROI del costo por resolución**, etiquetado como ahorro proyectado.
- **Desglose por idioma y segmento**, con investigación de disparidades.

## Fuentes para justificar el flujo

`call_center_interactions`, `call_transcripts`, `complaints` y `satisfaction_surveys`: por qué contactan los clientes, cómo se resuelve y qué tan satisfechos quedan. `transactions` da contexto para reclamos por cargos y fraude.

## Errores de la app y demanda

Cruzar eventos `Error` de `digital_events` con interacciones y reclamos (por cliente y fecha) para ver qué fallas generan contactos.

## Campañas y demanda

Las campañas (`marketing_campaigns`, `campaign_sends`) pueden explicar picos de contactos o reclamos por fecha, país y producto. Usarlas en el análisis que justifica el flujo.

## Monitoreo por país

**Este es el documento dueño del tema.** Se referencia desde [métricas](../metricas.md) (desglose), [AI](ai.md) (observabilidad) y la [matriz](../../requerimientos/matriz.md).

El banco opera en MX, CO y AR, con integraciones distintas por país. Desglosar latencia, fallas de herramientas, escalamientos y quejas por país permite detectar problemas de operación y sirve para el análisis de equidad. País y acento son atributos que ya vienen en los datos: no requieren un modelo.

## Límite en crédito

Un segmento aprendido (ej.: "premium") no puede cambiar las reglas de elegibilidad, que decide el servicio de políticas. Puede usarse para priorizar la atención, midiendo el efecto por segmento.

## Casos de uso del dataset aprovechables

El resumen propone casos de uso genéricos; se usan solo si aportan al flujo. Ejemplos: detección de fraude (para tarjetas o reclamos por cargos), clasificación de intención, resolución en el primer contacto, tendencias de sentimiento.

## Evidencia para la evaluación

- [ ] Análisis reproducible que justifica el flujo elegido
- [ ] Reporte final de métricas: línea base vs sistema
- [ ] Cálculo de ROI con supuestos declarados
- [ ] Sección de limitaciones

## Preguntas abiertas

- ¿Qué supuestos de costo usamos?
