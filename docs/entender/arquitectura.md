# Arquitectura: Sentinel Engine

Vista general del sistema para el procesamiento de disputas bancarias (*transaction-dispute intake*). **Plataforma principal:** Microsoft Azure + Azure Databricks.

**Para qué sirve:** Entender cómo encajan las piezas técnicas, de datos y de IA antes de leer las áreas. **Relacionados:** [conversación](../construir/conversacion.md), [seguridad](../construir/seguridad.md), [áreas](../construir/areas/), [glosario](glosario.md).

## Principio central

**La IA entiende; el código ejecuta y verifica.** Este documento es la fuente de este principio y de las capas; las reglas de conversación que se derivan de él están en [conversación](../construir/conversacion.md). Los demás documentos enlazan aquí en vez de repetirlo.

## Dos capas

```text
CAPA DE ATENCIÓN (tiempo real)                 CAPA DE DATOS (batch o incremental)
──────────────────────────────                 ───────────────────────────────────
Cliente ⇄ Frontend (chat multilingüe)          Archivos del dataset en S3 (~19M filas,
              │                                13 tablas, MXN/COP/ARS/USD)
              ▼                                         │
   Orquestador (Python / FastAPI)                       ▼
   Entender (LLM) → Decidir (Reglas/Tools)     Databricks Pipeline (Delta Lake)
   → Actuar → Verificar → Escalar              Bronze ➔ Silver (limpieza de ~2%
              │                                duplicados y ~5% nulos)
              ▼                                         │
   Herramientas con sesión segura                       ▼
   · listar_transacciones_cliente              Almacén operativo y analítico (mock
   · abrir_reclamo_disputa (Escritura)         del core bancario optimizado por cliente)
              │                                         │
              ▼                                         ▼
   Handoff JSON → asesor (simulado)            Modelos de ML y métricas de calidad
   (Hechos verificados, preguntas abiertas)    (Predictor de escalamiento)

- **Capa de atención:** Importan la latencia, la verificación de acciones, los reintentos acotados y la idempotencia. Desplegada en Azure (Azure Container Apps o App Service) bajo la responsabilidad de Felix (Backend & Tools). **
- **Capa de datos:** Importan la calidad, la frescura y la reproducibilidad. Construida en Azure Databricks procesando el dataset regional de México, Colombia y Argentina. Cada lectura devuelve el dato y hasta cuándo está actualizado.**.

## Quién decide qué

Orden de prioridad, de mayor a menor:

1. **Política en código.** Política en código. Permisos, confirmaciones y reglas fijas (ej.: transacciones con más de 90 días no entran en disputas automáticas, o si el cliente pide hablar con una persona, se escala de inmediato).
2. **Predictor de escalamiento** Predictor de escalamiento (componente aprendido de ML a cargo de Rubén). Decide si conviene escalar el caso evaluando el historial de call_center_interactions y satisfaction_surveys donde no hay una regla fija.
3. **LLM.** LLM. Entiende al cliente, maneja el contexto multilingüe en español y portugués, redacta respuestas y elige qué herramienta invocar; nunca elige de qué cliente leer ni toma decisiones de autorización de cuentas por sí mismo.

## Qué ve el LLM

- El texto del cliente y los **resultados** de las herramientas.
- **Nunca:** identificadores, documentos, ingresos, puntaje de crédito ni IP. El orquestador sabe quién es el cliente por la sesión.
- Detalle en [seguridad](../construir/seguridad.md).

## Recorrido de un caso (ejemplo: reclamo por cobro doble)

1. El cliente escribe: "me cobraron dos veces".
2. **Entender:** intención = reclamo por cargo.
3. **Decidir:** faltan datos, así que la herramienta busca compras repetidas del cliente de la sesión.
4. El asistente muestra las candidatas en su moneda y con la fecha de corte de los datos. El cliente elige una.
5. **Actuar:** pide confirmación y la herramienta abre el reclamo.
6. **Verificar:** la herramienta confirma el número de caso; solo entonces se informa.
7. **Escalar** si el predictor o una regla lo indican: handoff JSON con hechos verificados y preguntas abiertas.

## Componente aprendido

Candidato principal: **predictor de escalamiento**, entrenado con el historial del call center y comparado contra reglas simples. Detalle en [ML](../construir/areas/ml.md).

## Stack

| Pieza | Elección |
|---|---|
| Plataforma | **Azure** ([decisión 001](../construir/decisiones/001-plataforma-azure.md)) |
| Especificaciones | **OpenSpec** ([decisión 002](../construir/decisiones/002-openspec.md)) |
| LLM | Por decidir; propuesta: Azure OpenAI |
| Despliegue | Por decidir; propuesta: Azure Container Apps o App Service |
| Lenguaje, framework, almacenamiento | Por decidir. La propuesta inicial de [opciones de flujo](../construir/flujos/opciones.md) (DuckDB, FastAPI, embeddings multilingües) sigue siendo válida dentro de Azure |

Cada elección se registra en [decisiones](../construir/decisiones/).
