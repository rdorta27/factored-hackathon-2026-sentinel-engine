# Matriz de trazabilidad

Une cada [requerimiento](requerimientos.md) con el criterio de evaluación, el área responsable y la evidencia que lo demuestra. Se actualiza a medida que avanzamos.

**Para qué sirve:** ver de un vistazo qué criterio no tiene evidencia todavía. **Estados:** Pendiente, En curso, Listo.

**Dueño único:** cada requerimiento tiene un área dueña, la primera de la columna Área; las demás colaboran.

Áreas: [ai](../construir/areas/ai.md) · [ml](../construir/areas/ml.md) · [datos](../construir/areas/datos.md) · [análisis](../construir/areas/analisis.md)

| ID | Requerimiento | P | Criterio | Área | Evidencia | Estado |
|---|---|---|---|---|---|---|
| REQ-0001 | Contexto de la conversación | P0 | AI Engineering | ai | Demo | Pendiente |
| REQ-0002 | Aclarar o abstenerse | P0 | AI Engineering | ai | Demo caso ambiguo | Pendiente |
| REQ-0003 | Solo registros verificados | P0 | AI Engineering | ai | Demo + logs | Pendiente |
| REQ-0004 | Herramientas seguras | P0 | AI Engineering | ai | Contratos de herramientas | Pendiente |
| REQ-0005 | Solo acciones verificadas | P0 | AI Engineering | ai | Prueba de falla de herramienta | Pendiente |
| REQ-0006 | Reglas de autonomía | P0 | Fundamento | ai | [Conversación](../construir/conversacion.md) | Pendiente |
| REQ-0007 | Permisos en código | P0 | AI Engineering | ai | Código + prueba adversarial | Pendiente |
| REQ-0008 | Handoff JSON | P0 | AI Engineering | ai | Esquema + ejemplo | Pendiente |
| REQ-0009 | Demo caso normal | P0 | AI Engineering | ai | Demo + video | Pendiente |
| REQ-0010 | Demo caso ambiguo | P0 | AI Engineering | ai | Demo + video | Pendiente |
| REQ-0011 | Demo caso humano | P0 | AI Engineering | ai | Demo + video | Pendiente |
| REQ-0012 | ES y PT robustos | P0 | AI Engineering / ML | ai, ml | Demo PT + métricas por idioma | Pendiente |
| REQ-0013 | Limitaciones de datos e idiomas | P0 | Fundamento | analisis | Sección de limitaciones | Pendiente |
| REQ-0014 | Problema respaldado por datos | P0 | Data Analytics | analisis | Análisis reproducible | Pendiente |
| REQ-0015 | Pipeline con contratos | P0 | Data Engineering | datos | Pipeline + reporte de calidad | Pendiente |
| REQ-0016 | Componente aprendido vs línea base | P0 | Machine Learning | ml | Tabla de resultados | Pendiente |
| REQ-0017 | Etiquetas válidas, sin fuga | P0 | Machine Learning | ml | Descripción de la división | Pendiente |
| REQ-0018 | Incremental real o fixture | P1 | Data Engineering | datos | Fixture de actualización | Pendiente |
| REQ-0019 | Tracking de experimentos | P1 | Machine Learning | ml | Registro de experimentos | Pendiente |
| REQ-0020 | Held-out realista | P0 | Machine Learning | ml | Descripción de los sets | Pendiente |
| REQ-0021 | Pruebas de fallas | P0 | Machine Learning | ml (dueño); ai aporta los casos de seguridad | Resultados del set adversarial | Pendiente |
| REQ-0022 | Métricas con n y versiones | P0 | Data Analytics | analisis | Reporte de métricas | Pendiente |
| REQ-0023 | Validación del LLM juez | P2 | Machine Learning | ml | Rúbrica + muestra validada | Pendiente |
| REQ-0024 | Desglose por idioma, país y segmento | P1 | Data Analytics | analisis | Reporte de métricas | Pendiente |
| REQ-0025 | Observabilidad | P1 | AI Engineering | ai | Trazas y logs | Pendiente |
| REQ-0026 | Reintentos, fallback, idempotencia | P1 | AI Engineering | ai | Prueba de falla de herramienta | Pendiente |
| REQ-0027 | Autenticación, acceso, retención | P0 | AI Engineering | ai, datos | Sesión de prueba + política | Pendiente |
| REQ-0028 | Reproducibilidad | P0 | Fundamento | todos | README de instalación | Pendiente |
| REQ-0029 | Explicaciones basadas en logs | P1 | AI Engineering | ai | Logs de auditoría | Pendiente |
| REQ-0030 | Declarar lo que falta | P0 | Fundamento | todos | Sección de limitaciones | Pendiente |
| REQ-0031 | Datos aprobados y etiquetados | P0 | Data Engineering | datos | Inventario de fuentes | Pendiente |
| REQ-0032 | Mocks documentados | P1 | AI Engineering | ai | Contratos de herramientas | Pendiente |
| REQ-0033 | Separación en crédito (si aplica) | P0 | AI Engineering / ML | ai, ml | Arquitectura | Pendiente |
| REQ-0034 | Repositorio público | P0 | Fundamento | todos | Link al repo | Pendiente |
| REQ-0035 | Herramienta desplegada | P0 | AI Engineering | ai | Link | Pendiente |
| REQ-0036 | Presentación | P0 | Fundamento | todos | [Guion](../construir/entrega/presentacion.md) | Pendiente |
| REQ-0037 | Video | P0 | Fundamento | todos | [Guion](../construir/entrega/video.md) | Pendiente |
| REQ-0038 | Frontend simple | P0 | AI Engineering | ai | Demo | Pendiente |
| REQ-0039 | Declarar frescura | P0 | AI Engineering | ai, datos | Demo + herramientas con "actualizado hasta" | Pendiente |
| REQ-0040 | Pedido de hablar con una persona | P0 | AI Engineering | ai | Demo caso humano | Pendiente |
| REQ-0041 | Moneda original; idioma según cliente | P0 | AI Engineering | ai | Demo PT | Pendiente |
| REQ-0042 | Reclamo con transacciones candidatas | P1 | AI Engineering | ai | Demo | Pendiente |
| REQ-0043 | Revisar Pending / Reversed | P1 | AI Engineering | ai | Demo | Pendiente |
| REQ-0044 | Español neutro, siglas explicadas | P1 | AI Engineering | ai | Demo | Pendiente |
| REQ-0045 | Contexto de errores de la app | P2 | AI Engineering | ai | Demo | Pendiente |
| REQ-0046 | Enrutamiento del handoff | P2 | AI Engineering | ai | Ejemplo de handoff | Pendiente |
| REQ-0047 | LLM sin identificadores | P0 | AI Engineering | ai | Código + prueba adversarial | Pendiente |
| REQ-0048 | Orden de decisión | P0 | Fundamento | ai, ml | [Arquitectura](../entender/arquitectura.md) | Pendiente |
| REQ-0049 | País como configuración | P2 | Fundamento | ai | Archivo de configuración | Pendiente |
| REQ-0050 | Monitoreo por país | P1 | Data Analytics | analisis | Reporte por país | Pendiente |

## Cobertura por criterio

| Criterio | Requerimientos |
|---|---|
| Fundamento y documentación | REQ-0006, REQ-0013, REQ-0028, REQ-0030, REQ-0034, REQ-0036, REQ-0037, REQ-0048, REQ-0049 + [decisiones](../construir/decisiones/) |
| AI Engineering | REQ-0001 a REQ-0012, REQ-0025 a REQ-0027, REQ-0029, REQ-0032, REQ-0033, REQ-0035, REQ-0038 a REQ-0047 |
| Data Analytics | REQ-0014, REQ-0022, REQ-0024, REQ-0050 |
| Data Engineering | REQ-0015, REQ-0018, REQ-0027, REQ-0031, REQ-0039 |
| Machine Learning | REQ-0012, REQ-0016, REQ-0017, REQ-0019 a REQ-0021, REQ-0023, REQ-0033, REQ-0048 |
