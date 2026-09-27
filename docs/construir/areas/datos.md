# Data Engineering

**Criterio de evaluación:** extracción y transformación de los datos. **Responsable:** por definir.

**Requerimientos:** REQ-0015 (pipeline con contratos), REQ-0018 (incremental), REQ-0027 (aislamiento por cliente), REQ-0031 (datos etiquetados), REQ-0039 (frescura). Ver [requerimientos](../../requerimientos/requerimientos.md).

**Relacionados:** [dataset](../../entender/dataset.md) (tablas y columnas), [arquitectura](../../entender/arquitectura.md).

## Qué construye esta área

- **Pipeline ETL/ELT** repetible y determinista: misma entrada, misma salida.
- **Contratos de esquema estrictos**: un dato inválido se rechaza o se aísla y se reporta; nunca entra en silencio.
- **Controles de calidad**, **linaje** y **política de frescura**.
- **Aislamiento de registros por cliente**, base del control de acceso.
- Procesamiento batch, incremental o streaming según latencia y frescura. Archivos incrementales no obligan a streaming.
- Con datos estáticos: **fixture de actualización** etiquetado, sin modificar los datos oficiales.
- Inventario de fuentes: real, desidentificado, sintético o generado por el equipo.

## Procesamiento incremental

Las tablas grandes vienen particionadas por fecha, con llegadas tardías, duplicados y esquema cambiante. Piezas del pipeline:

| Pieza | Qué hace |
|---|---|
| Watermark | Guarda hasta qué partición se procesó; la próxima ejecución toma solo lo nuevo |
| Ventana de reproceso | Vuelve a mirar los últimos N días para capturar llegadas tardías (el watermark solo las saltaría) |
| Upsert idempotente | Si la clave existe, actualiza; si no, inserta. Reprocesar no duplica |
| Deduplicación por clave | Absorbe el ~2 % de duplicados |
| Contratos versionados | Detecta columnas nuevas y decide si aceptarlas; nunca en silencio |
| Política de frescura | Declara el atraso máximo aceptable (ej.: 24 h) |

Streaming no es obligatorio: se justifica solo si el flujo necesita segundos de frescura.

## Casos a cuidar en el pipeline

- Formatos numéricos LATAM (ej.: "1.200,50"): el contrato define el formato esperado en lugar de adivinarlo.
- Moneda obligatoria y validada en cada monto.
- Nulo no es huérfano: el contrato los distingue (ver [dataset](../../entender/dataset.md#relaciones-entre-tablas)).
- Particiones por fecha: leer solo las nuevas y las de la ventana de reproceso.
- Cada lectura de herramienta devuelve el dato y su marca de "actualizado hasta".

## Evidencia para la evaluación

- [ ] Pipeline ejecutable con un comando
- [ ] Contratos y reporte de calidad
- [ ] Fixture de actualización que pasa
- [ ] Inventario de fuentes

## Decisiones pendientes

- Herramientas del pipeline
- Batch o incremental (depende de cómo lleguen los datos)

