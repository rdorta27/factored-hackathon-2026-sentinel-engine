# AI Engineering

**Criterio de evaluación:** backend, frontend y despliegue. **Responsable:** por definir.

**Requerimientos:** REQ-0001 a REQ-0012 (comportamiento y demo), REQ-0025 a REQ-0027 (operación y seguridad), REQ-0029 (explicaciones basadas en logs), REQ-0032 (mocks documentados), REQ-0033 (separación en crédito, si aplica), REQ-0035 (despliegue), REQ-0038 a REQ-0049 (frontend, conversación, diseño). Ver [requerimientos](../../requerimientos/requerimientos.md).

**Relacionados:** [arquitectura](../../entender/arquitectura.md), [conversación](../conversacion.md) (qué dice el asistente), [seguridad](../seguridad.md).

## Qué construye esta área

- **Orquestador:** el ciclo entender, decidir, actuar, verificar y escalar, con el orden de decisión política > predictor > LLM.
- **Herramientas** (mock) con contratos documentados, filtradas por el cliente de la sesión, que devuelven el dato y su fecha de actualización.
- **Políticas en código:** qué responde solo, qué requiere confirmación y cuándo escalar.
- **Handoff** en JSON con esquema validable.
- **Frontend simple** (chat). Sin dashboard.
- **Despliegue** con link público, límites de uso y tope de gasto.
- **Observabilidad:** trazas y registros de ejecución, con país e idioma en cada registro (para el [monitoreo por país](analisis.md#monitoreo-por-país)).

## Reglas técnicas

- Reintentos acotados; acciones idempotentes (repetirlas no las duplica).
- El país es configuración, no código: moneda, documentos, términos, regulador y plazos de cada país en archivos de configuración. Hoy MX, CO y AR.

## Handoff

### Esquema (borrador)

```json
{
  "solicitud": "",
  "idioma": "es | pt",
  "pais_cuenta": "MX | CO | AR",
  "hechos_verificados": [],
  "acciones_realizadas": [],
  "evidencia": [],
  "preguntas_abiertas": [],
  "motivo_escalamiento": ""
}
```

### Enrutamiento (simulado)

Con `service_agents`: elegir un asesor activo que hable el idioma del cliente y tenga la especialidad del flujo. Ver [dataset](../../entender/dataset.md#diccionario-dimensiones-de-apoyo).

## Evidencia para la evaluación

- [ ] Demo de los 3 casos (normal, ambiguo, humano) en ES y PT
- [ ] Link desplegado funcionando
- [ ] Logs de ejecución auditables
- [ ] Instrucciones de instalación reproducibles

## Decisiones pendientes

- Framework del backend y del frontend
- LLM a usar (propuesta: Azure OpenAI)
- Servicio de despliegue en Azure
