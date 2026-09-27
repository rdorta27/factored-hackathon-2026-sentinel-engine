# El reto en una página

**Para qué sirve:** entender el hackathon sin leer los PDF. **Relacionados:** [arquitectura](arquitectura.md), [dataset](dataset.md), [requerimientos](../requerimientos/requerimientos.md), [glosario](glosario.md).

> "Build something that works, prove that it works, and know when it should not act. And show us what it would take to make it real."

## Qué hay que construir

Un **asistente de atención al cliente para un banco** que opera en México, Colombia y Argentina. No un chatbot: un **sistema** que entiende al cliente, consulta datos verificados, ejecuta acciones seguras, verifica que ocurrieron y pasa el caso a una persona cuando corresponde.

- **Un solo flujo**, a elegir el lunes 28/9: consultas de cuenta o pagos, tarjetas, reclamos por cargos no reconocidos, o información y elegibilidad de crédito. Implementar más flujos no da bonificación automática: cuentan la profundidad y el criterio de ingeniería.
- Debe funcionar en **español y portugués**. Los datos solo están en español.
- **Primero que funcione de punta a punta**, después optimizar.

## Lo que se muestra en la demo

| Caso | Qué hace el asistente |
|---|---|
| Normal | Resuelve solo, conforme a las políticas del banco |
| Ambiguo o no soportado | Pregunta lo que falta o dice que no puede |
| Requiere una persona | Escala con un resumen estructurado para el asesor |

## Reglas de oro

Resumen; el detalle está en [arquitectura](arquitectura.md) y [conversación](../construir/conversacion.md).

1. **La IA entiende; el código ejecuta y verifica.** Los permisos están en el código, no en el prompt.
2. **Solo hechos verificados.** Si el dato no está o no está al día, se dice.
3. **La autonomía depende del riesgo.** Las acciones con consecuencias piden confirmación.
4. **Honestidad.** Se reportan las fallas, las limitaciones y lo que falta para producción.

## Cómo se evalúa

| Criterio | Qué miran |
|---|---|
| Fundamento y documentación | Por qué elegimos el flujo, decisiones escritas, limitaciones |
| AI Engineering | Backend, frontend y despliegue |
| Data Analytics | Calidad de datos e insights |
| Data Engineering | Pipeline de extracción y transformación |
| Machine Learning | Selección, evaluación contra una línea base y tracking de modelos |

Métricas principales: **resolución automatizada segura**, **resultados inseguros** y **costo**. Detalle en [métricas](../construir/metricas.md).

## Entregables: lunes 5/10 (hora por confirmar)

El reto es un sprint de 10 días: lanzamiento el 25/9 y cierre de envíos el 5/10.

Enviar a hackathon.admin@factored.ai:

1. Repositorio público `factored-hackathon-2026-[equipo]`
2. Link a la herramienta desplegada
3. Presentación de 4 a 6 diapositivas
4. Video corto: demo y decisiones de arquitectura

"Submit your tool no matter what": se entrega a tiempo, con las limitaciones declaradas.

## Riesgos conocidos

- **Portugués sin datos:** los evaluadores probablemente prueben en portugués de Brasil. Ver [idiomas](../construir/idiomas.md).
- **Datos con problemas a propósito:** duplicados, nulos, llegadas tardías, esquema cambiante. Ver [dataset](dataset.md).
- **Nadie del equipo trabaja en contact centers:** el [glosario](glosario.md) explica las siglas del negocio.

## Material oficial

*Planteamiento* · *Kickoff* · *Resumen del dataset* · *Diccionario de datos*
