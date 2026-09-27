# Arquitectura

Vista general del sistema. Plataforma: Azure; el resto del stack se decide después de elegir el flujo.

**Para qué sirve:** entender cómo encajan las piezas antes de leer las áreas. **Relacionados:** [conversación](../construir/conversacion.md), [seguridad](../construir/seguridad.md), [áreas](../construir/areas/), [glosario](glosario.md).

## Principio central

**La IA entiende; el código ejecuta y verifica.** Este documento es la fuente de este principio y de las capas; las reglas de conversación que se derivan de él están en [conversación](../construir/conversacion.md). Los demás documentos enlazan aquí en vez de repetirlo.

## Dos capas

```
CAPA DE ATENCIÓN (tiempo real)                 CAPA DE DATOS (batch o incremental)
──────────────────────────────                 ───────────────────────────────────
Cliente ⇄ Frontend (chat)                      Archivos del dataset
              │                                (particiones por fecha, llegadas
              ▼                                 tardías, duplicados, esquema
   Orquestador (código + LLM)                   cambiante)
   Entender → Decidir → Actuar                          │
   → Verificar → Escalar                                ▼
              │                                Pipeline: contratos, deduplicación,
              ▼                                upsert, calidad
   Herramientas (con sesión)                            │
   · consultar saldo, movimientos  ◄── leen ──  Almacén operativo (mock del core
   · bloquear tarjeta, abrir reclamo ── escriben ─► bancario, por cliente)
              │                                         │
              ▼                                Almacén analítico (análisis,
   Handoff JSON → asesor (simulado)            entrenamiento, línea base)
```

- **Capa de atención:** importan la latencia, la verificación de acciones, los reintentos y la idempotencia.
- **Capa de datos:** importan la calidad, la frescura y la reproducibilidad. Cada lectura devuelve el dato **y hasta cuándo está actualizado**.

## Quién decide qué

Orden de prioridad, de mayor a menor:

1. **Política en código.** Permisos, confirmaciones y reglas fijas (ej.: si el cliente pide hablar con una persona, se escala).
2. **Componente aprendido**, si participa en la decisión (ej.: un predictor de escalamiento). Decide si conviene escalar donde no hay regla.
3. **LLM.** Entiende al cliente, redacta las respuestas y elige qué herramienta pedir; nunca elige de qué cliente leer.

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

Se decide junto con el flujo (lunes 28/9). Candidatos: predictor de escalamiento, clasificador de intención, detector de fraude. Cualquiera se compara contra una línea base. Detalle en [ML](../construir/areas/ml.md).

## Stack

| Pieza | Elección |
|---|---|
| Plataforma | **Azure** ([decisión 001](../construir/decisiones/001-plataforma-azure.md)) |
| Especificaciones | **OpenSpec** ([decisión 002](../construir/decisiones/002-openspec.md)) |
| LLM | Por decidir; propuesta: Azure OpenAI |
| Despliegue | Por decidir; propuesta: Azure Container Apps o App Service |
| Lenguaje, framework, almacenamiento | Por decidir. La propuesta inicial de [opciones de flujo](../construir/flujos/opciones.md) (DuckDB, FastAPI, embeddings multilingües, Azure OpenAI) sigue siendo válida dentro de Azure |

Cada elección se registra en [decisiones](../construir/decisiones/).
