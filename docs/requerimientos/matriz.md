# Matriz de trazabilidad

Une cada [requerimiento](requerimientos.md) con el criterio de evaluación, el área responsable y la evidencia que lo demuestra. Se actualiza a medida que avanzamos.

**Para qué sirve:** ver de un vistazo qué criterio no tiene evidencia todavía. **Estados:** Pendiente, En curso, Listo.

**Dueño único:** cada requerimiento tiene un área dueña, la primera de la columna Área; las demás colaboran.

Áreas: [ai](../construir/areas/ai.md) · [ml](../construir/areas/ml.md) · [datos](../construir/areas/datos.md) · [análisis](../construir/areas/analisis.md)

| ID | Requerimiento | P | Criterio | Área | Evidencia | Estado |
|---|---|---|---|---|---|---|
| R-01 | Contexto de la conversación | P0 | AI Engineering | ai | Demo | Pendiente |
| R-02 | Aclarar o abstenerse | P0 | AI Engineering | ai | Demo caso ambiguo | Pendiente |
| R-03 | Solo registros verificados | P0 | AI Engineering | ai | Demo + logs | Pendiente |
| R-04 | Herramientas seguras | P0 | AI Engineering | ai | Contratos de herramientas | Pendiente |
| R-05 | Solo acciones verificadas | P0 | AI Engineering | ai | Prueba de falla de herramienta | Pendiente |
| R-06 | Reglas de autonomía | P0 | Fundamento | ai | [Conversación](../construir/conversacion.md) | Pendiente |
| R-07 | Permisos en código | P0 | AI Engineering | ai | Código + prueba adversarial | Pendiente |
| R-08 | Handoff JSON | P0 | AI Engineering | ai | Esquema + ejemplo | Pendiente |
| R-09 | Demo caso normal | P0 | AI Engineering | ai | Demo + video | Pendiente |
| R-10 | Demo caso ambiguo | P0 | AI Engineering | ai | Demo + video | Pendiente |
| R-11 | Demo caso humano | P0 | AI Engineering | ai | Demo + video | Pendiente |
| R-12 | ES y PT robustos | P0 | AI Engineering / ML | ai, ml | Demo PT + métricas por idioma | Pendiente |
| R-13 | Limitaciones de datos e idiomas | P0 | Fundamento | analisis | Sección de limitaciones | Pendiente |
| R-14 | Problema respaldado por datos | P0 | Data Analytics | analisis | Análisis reproducible | Pendiente |
| R-15 | Pipeline con contratos | P0 | Data Engineering | datos | Pipeline + reporte de calidad | Pendiente |
| R-16 | Componente aprendido vs línea base | P0 | Machine Learning | ml | Tabla de resultados | Pendiente |
| R-17 | Etiquetas válidas, sin fuga | P0 | Machine Learning | ml | Descripción de la división | Pendiente |
| R-18 | Incremental real o fixture | P1 | Data Engineering | datos | Fixture de actualización | Pendiente |
| R-19 | Tracking de experimentos | P1 | Machine Learning | ml | Registro de experimentos | Pendiente |
| R-20 | Held-out realista | P0 | Machine Learning | ml | Descripción de los sets | Pendiente |
| R-21 | Pruebas de fallas | P0 | Machine Learning | ml (dueño); ai aporta los casos de seguridad | Resultados del set adversarial | Pendiente |
| R-22 | Métricas con n y versiones | P0 | Data Analytics | analisis | Reporte de métricas | Pendiente |
| R-23 | Validación del LLM juez | P2 | Machine Learning | ml | Rúbrica + muestra validada | Pendiente |
| R-24 | Desglose por idioma, país y segmento | P1 | Data Analytics | analisis | Reporte de métricas | Pendiente |
| R-25 | Observabilidad | P1 | AI Engineering | ai | Trazas y logs | Pendiente |
| R-26 | Reintentos, fallback, idempotencia | P1 | AI Engineering | ai | Prueba de falla de herramienta | Pendiente |
| R-27 | Autenticación, acceso, retención | P0 | AI Engineering | ai, datos | Sesión de prueba + política | Pendiente |
| R-28 | Reproducibilidad | P0 | Fundamento | todos | README de instalación | Pendiente |
| R-29 | Explicaciones basadas en logs | P1 | AI Engineering | ai | Logs de auditoría | Pendiente |
| R-30 | Declarar lo que falta | P0 | Fundamento | todos | Sección de limitaciones | Pendiente |
| R-31 | Datos aprobados y etiquetados | P0 | Data Engineering | datos | Inventario de fuentes | Pendiente |
| R-32 | Mocks documentados | P1 | AI Engineering | ai | Contratos de herramientas | Pendiente |
| R-33 | Separación en crédito (si aplica) | P0 | AI Engineering / ML | ai, ml | Arquitectura | Pendiente |
| R-34 | Repositorio público | P0 | Fundamento | todos | Link al repo | Pendiente |
| R-35 | Herramienta desplegada | P0 | AI Engineering | ai | Link | Pendiente |
| R-36 | Presentación | P0 | Fundamento | todos | [Guion](../construir/entrega/presentacion.md) | Pendiente |
| R-37 | Video | P0 | Fundamento | todos | [Guion](../construir/entrega/video.md) | Pendiente |
| R-38 | Frontend simple | P0 | AI Engineering | ai | Demo | Pendiente |
| R-39 | Declarar frescura | P0 | AI Engineering | ai, datos | Demo + herramientas con "actualizado hasta" | Pendiente |
| R-40 | Pedido de hablar con una persona | P0 | AI Engineering | ai | Demo caso humano | Pendiente |
| R-41 | Moneda original; idioma según cliente | P0 | AI Engineering | ai | Demo PT | Pendiente |
| R-42 | Reclamo con transacciones candidatas | P1 | AI Engineering | ai | Demo | Pendiente |
| R-43 | Revisar Pending / Reversed | P1 | AI Engineering | ai | Demo | Pendiente |
| R-44 | Español neutro, siglas explicadas | P1 | AI Engineering | ai | Demo | Pendiente |
| R-45 | Contexto de errores de la app | P2 | AI Engineering | ai | Demo | Pendiente |
| R-46 | Enrutamiento del handoff | P2 | AI Engineering | ai | Ejemplo de handoff | Pendiente |
| R-47 | LLM sin identificadores | P0 | AI Engineering | ai | Código + prueba adversarial | Pendiente |
| R-48 | Orden de decisión | P0 | Fundamento | ai, ml | [Arquitectura](../entender/arquitectura.md) | Pendiente |
| R-49 | País como configuración | P2 | Fundamento | ai | Archivo de configuración | Pendiente |
| R-50 | Monitoreo por país | P1 | Data Analytics | analisis | Reporte por país | Pendiente |

## Cobertura por criterio

| Criterio | Requerimientos |
|---|---|
| Fundamento y documentación | R-06, R-13, R-28, R-30, R-34, R-36, R-37, R-48, R-49 + [decisiones](../construir/decisiones/) |
| AI Engineering | R-01 a R-12, R-25 a R-27, R-29, R-32, R-33, R-35, R-38 a R-47 |
| Data Analytics | R-14, R-22, R-24, R-50 |
| Data Engineering | R-15, R-18, R-27, R-31, R-39 |
| Machine Learning | R-12, R-16, R-17, R-19 a R-21, R-23, R-33, R-48 |
