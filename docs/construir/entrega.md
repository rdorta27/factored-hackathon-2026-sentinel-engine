# Entrega

Lunes 5/10 (hora por confirmar). Se trabaja en español y se entrega en **inglés**. Lista completa de entregables en el [resumen](../entender/resumen.md#entregables-lunes-510-hora-por-confirmar).

## Idioma

Lo que se entrega se escribe en **inglés desde el primer borrador**; lo que se trabaja se escribe en **español**. No hay una pasada de traducción al final: el README, la presentación y el guion del video se redactan en inglés mientras se crean. `docs/` y `team/` se quedan en español. Registrado como [REQ-0051](../requerimientos/requerimientos.md).

| Pieza | Idioma | Estado | Quién revisa | Se congela |
|---|---|---|---|---|
| `README.md` del repo (el link de la entrega) | Inglés | Listo | Rubén | Mantenido en inglés |
| Título y descripción del repo en GitHub | Inglés | Listo | Rubén | Mantenido en inglés |
| Presentación (4 a 6 diapositivas) | Nace en inglés | Pendiente | | Vie 2/10 |
| Guion del video | Nace en inglés | Pendiente | | Vie 2/10 |
| Demos: casos ES y PT | Español y portugués | — | — | Es lo que dice el sistema |
| `docs/` y `team/` | Español | — | — | No se traducen |

Se actualiza en cada revisión, no al final. Estados: Pendiente, En curso, Listo.

## Presentación

4 a 6 diapositivas.

| # | Diapositiva | Fuente |
|---|---|---|
| 1 | Problema y flujo elegido, respaldado por datos | [análisis](areas/analisis.md), [decisiones](decisiones/) |
| 2 | Arquitectura (principio central y capas) | [arquitectura](../entender/arquitectura.md), [decisiones](decisiones/) |
| 3 | Seguridad y control: permisos, handoff, cuándo NO actuar | [seguridad](seguridad.md), [conversación](conversacion.md) |
| 4 | Resultados: línea base vs sistema (métricas principales, por idioma) | [métricas](metricas.md) |
| 5 | Limitaciones y ruta a producción | [requerimientos](../requerimientos/requerimientos.md) (REQ-0030, lo que falta) |

- Mostrar las 3 métricas principales: resolución segura, resultados inseguros, costo.
- Cada cifra con n y tipo de medición (offline, simulación, proyección).
- Incluir las fallas y las limitaciones; ocultarlas resta.

## Video pitch

Obligatorio y corto. Muestra la solución funcionando y explica las decisiones de arquitectura.

1. El problema, en una frase y con un dato.
2. Demo del **caso normal** (ES).
3. Demo del **caso ambiguo** (PT).
4. Demo del **caso humano**, mostrando el handoff JSON.
5. Un intento de prompt injection que falla.
6. Decisiones de arquitectura clave (desde [decisiones](decisiones/)).
7. Resultados principales y limitaciones.

## Pendientes

- [ ] Duración máxima del video (confirmar con los organizadores)
- [ ] Herramienta de grabación
