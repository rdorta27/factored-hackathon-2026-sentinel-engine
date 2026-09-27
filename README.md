# Sentinel Engine

Felix, Natalia y Rubén · Factored AI & Data Hackathon 2026 · Entrega: **lunes 5/10** (hora por confirmar)

Punto de partida del equipo. Casi todo es una propuesta y se va ajustando a medida que avanzamos.

## Qué vamos a construir

Un **asistente de atención al cliente para un banco** que opera en México, Colombia y Argentina. La idea es que no sea solo un chatbot: que entienda al cliente, responda con datos verificados, haga acciones seguras, confirme que ocurrieron y pase el caso a una persona cuando haga falta. Tiene que funcionar en **español y portugués**.

## Para empezar (unos 15 minutos)

1. **[El reto en una página](docs/entender/resumen.md):** qué hay que construir, cómo nos evalúan y qué se entrega.
2. **[Plan del equipo](docs/plan.md):** cronograma tentativo, propuesta de cómo trabajar y decisiones pendientes.
3. **[Arquitectura](docs/entender/arquitectura.md):** una primera idea de cómo encajan las piezas.

El [índice de la documentación](docs/README.md) ayuda a encontrar el resto de los temas.

## Tareas pendientes

**Para el lunes 28/9 hay que decidir** el flujo, los responsables por área, la forma de trabajo y el stack. El detalle está en las [decisiones pendientes](docs/plan.md#decisiones-pendientes).

| Tarea | Responsable | Para cuándo |
|---|---|---|
| Completar la [tabla del equipo](docs/plan.md#equipo): fortalezas y disponibilidad | Cada uno | Lun 28/9 |
| Dar acceso de escritura al repositorio a Felix y Natalia | Rubén | Lun 28/9 |
| Conseguir las credenciales de los datos y confirmar que funcionan para los 3 | Por asignar | Lun 28/9 |
| Preguntar en el canal de ayuda: acceso a los datos, términos de uso, el asterisco de "public\*", hora límite y duración del video | Por asignar | Lun 28/9 |
| Definir quién pone la suscripción de Azure, con tope de gasto y alertas | Por asignar | Lun 28/9 |
| Primer vistazo a los datos: inventario de tablas, perfil de los motivos de contacto y contraste con el diccionario | Por asignar | Lun 28/9 |
| Tomar las decisiones pendientes del lunes | Equipo | Lun 28/9 |

## Decisiones tomadas

| Decisión | Registro |
|---|---|
| Plataforma: Microsoft Azure | [001](docs/construir/decisiones/001-plataforma-azure.md) |
| Especificaciones con OpenSpec | [002](docs/construir/decisiones/002-openspec.md) |

## Requisitos del hackathon que aplican desde ya

- **Sin secretos ni datos en el repositorio.** El repositorio se entrega público; las credenciales van en `.env` (excluido por `.gitignore`) y se comparten por mensaje directo.
- **Entrega en inglés.** La documentación de trabajo está en español; para la entrega se pasan a inglés este README, la presentación y el video.
