# Métricas

Catálogo de métricas del sistema.

**Para qué sirve:** qué se mide y cómo se reporta. **Relacionados:** [ML](areas/ml.md), [análisis](areas/analisis.md).

Los objetivos numéricos quedan por definir cuando elijamos el flujo y revisemos los datos.

## Reglas para todas las métricas

- **Métricas principales** (destacadas en el kickoff): resolución automatizada segura, resultados inseguros y eficiencia de costo. El resto son de apoyo.
- Línea base y sistema propuesto se miden sobre el **mismo set held-out**.
- **Dos sets de evaluación**, reportados por separado:
  - Held-out realista: la mezcla real de casos. Da las métricas globales.
  - Set adversarial: injection, acceso no autorizado, sesiones expiradas, fallas de herramientas.
- **División de los datos:** ordenar por tiempo, sin partir un mismo caso entre los dos lados, y con variables calculadas solo con información anterior a cada caso (detalle en [ML](areas/ml.md#rigor)). Los primeros ~70 % van a desarrollo (se permite validación cruzada temporal por batches); los últimos ~30 % son el held-out, que se mide **una sola vez** al final. Ajustar el sistema mirando el held-out lo convierte en set de desarrollo.
- Cada resultado se reporta con: tamaño de muestra (n), mezcla de casos, versiones de modelos y prompts, y variabilidad entre ejecuciones.
- Desglose por **idioma** (ES / PT), por **país** (MX / CO / AR) y por **segmento** de cliente; señalar muestras pequeñas. El monitoreo por país está detallado en [análisis](areas/analisis.md#monitoreo-por-país).
- Etiquetar el tipo de medición: offline, simulación o ahorro proyectado. Nunca presentar lo offline como mejora en producción.
- Las métricas se generan con **scripts reproducibles sobre los logs** (script o CLI), sin dashboard.

## 1. Resultado

| Métrica | Fórmula | Nota |
|---|---|---|
| **Resolución automatizada segura** | casos resueltos correctamente y conforme a políticas, sin humano / todos los casos en alcance | Reportar también la proporción de casos donde se intentó automatizar |
| Contención | casos sin transferencia / todos los casos | No equivale a resolver; leer junto con la anterior |
| Transferencias omitidas | casos que requerían humano y no se escalaron / casos que requerían humano | Requiere etiquetas de referencia |
| Transferencias innecesarias | casos escalados que no lo requerían / casos escalados | Requiere etiquetas de referencia |
| Calidad del handoff | % de handoffs con solicitud, hechos verificados, acciones, evidencia y preguntas abiertas | Validable con el esquema JSON |
| **Resultados inseguros** | nº de divulgaciones o acciones no autorizadas, o resultados materialmente incorrectos / n | Siempre con denominador; 0 en muestra pequeña no es riesgo cero |
| Latencia p50 / p95 | percentiles 50 y 95 del tiempo de principio a fin por caso | No usar el promedio. p95 alto: abandonos, solicitudes repetidas, timeouts |
| **Costo por caso intentado** | costo total / casos intentados | Declarar supuestos |
| **Costo por resolución exitosa** | costo total / resoluciones automatizadas seguras | "No definido" si no hay resoluciones |

### Ejemplo de costo y ROI (ahorro proyectado, no medido)

> **EJEMPLO ILUSTRATIVO. No usar para decidir ni citar en la presentación.** Los valores (USD 0,05 y USD 2) son inventados para explicar el cálculo; los reales salen de nuestras mediciones y de supuestos documentados.

Supuestos ilustrativos: IA USD 0,05 por caso intentado, 40 % de resolución segura, humano USD 2 por caso.

```
IA:      100 casos × 0,05 = USD   5
Humano:   60 casos × 2    = USD 120
Total                     = USD 125  → USD 1,25 por caso
Solo humanos: 100 × 2     = USD 200  → USD 2,00 por caso
Costo IA por resolución exitosa: 5 / 40 = USD 0,125
```

- Trabajar en totales; no sumar costos unitarios con totales.
- El ahorro depende sobre todo de la tasa de resolución segura, no del costo de la IA.
- Reportar siempre junto a la tasa de resultados inseguros.

## 2. Seguridad y confiabilidad

| Métrica | Fórmula | Objetivo |
|---|---|---|
| Accesos no autorizados | datos entregados de otro cliente o sin sesión válida / intentos | 0 |
| Resistencia a prompt injection | intentos bloqueados / intentos (ES y PT) | Por definir |
| Acciones reportadas sin verificar | nº de acciones informadas sin confirmación de la herramienta | 0 |
| Manejo de fallas de herramientas | fallas manejadas con reintento acotado, fallback o escalamiento / fallas inyectadas | Por definir |
| Sesiones expiradas manejadas | casos que piden reautenticación / casos con sesión vencida | Por definir |
| Datos restringidos en LLM externos | nº de solicitudes con datos restringidos | 0 |

## 3. Calidad de respuesta

| Métrica | Fórmula | Nota |
|---|---|---|
| Respuestas con fuente | respuestas factuales con fuente verificable / respuestas factuales | Explicabilidad |
| Manejo de ambigüedad | casos ambiguos donde aclara o se abstiene / casos ambiguos | Incluye ambigüedad multilingüe |
| Acuerdo LLM juez vs humano | % de coincidencia en una muestra validada | Solo si usamos LLM juez; documentar rúbrica |

## 4. Componente aprendido

Al menos uno, siempre contra una línea base y sobre held-out. Depende de la arquitectura (ver [ML](areas/ml.md)).

| Componente posible | Métrica | Línea base posible |
|---|---|---|
| Clasificador de intención o motivo | accuracy, F1 por clase | Palabras clave o clase mayoritaria |
| Predictor de escalamiento | AUC, transferencias omitidas e innecesarias al umbral elegido | Reglas simples por motivo |
| Detección de fraude (tarjetas o reclamos) | AUC, precisión y recall a un umbral | `fraud_score` existente del banco |
| Retrieval de políticas (RAG) | recall@k, MRR | BM25 |
| Modelo de riesgo (si el flujo es crédito) | AUC, calibración | Regresión logística o regla fija |

AUC mide el **orden** (0,5 = azar), no la calibración ni el umbral; el umbral lo define la política.

## 5. Datos

| Métrica | Fórmula |
|---|---|
| Calidad de datos | % de registros que pasan los contratos (tipos, nulos, rangos) |
| Frescura | tiempo desde que ocurre el hecho hasta que el sistema lo ve (ver [glosario](../entender/glosario.md#datos)) |
| Prueba de actualización | el fixture de actualización pasa (sí / no) |

## Preguntas abiertas

- ¿Qué supuestos de costo usamos (precio por token, costo del agente humano)?
- ¿Cuántos casos held-out necesitamos por idioma para que la comparación tenga sentido?
