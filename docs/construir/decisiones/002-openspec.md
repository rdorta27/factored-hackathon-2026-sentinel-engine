# 002 · Especificaciones con OpenSpec

**Fecha:** 2026-09-27
**Estado:** Aceptada
**Participantes:** Equipo

## Contexto

Somos 3 personas con 8 días y asistentes de IA para programar. Necesitamos que cada pieza tenga una especificación clara antes de implementarla, que el cambio sea revisable y que las especificaciones sirvan como documentación para la evaluación (criterio "fundamento y documentación").

## Opciones

1. **OpenSpec:** desarrollo guiado por especificaciones. Cada cambio se propone con su motivación, tareas y los requisitos que agrega o modifica; al terminar, las especificaciones quedan actualizadas.
2. **Solo GitHub Issues:** más liviano, pero las especificaciones quedan dispersas.
3. **Documentos libres en `docs/`:** ya los tenemos, pero no están pensados para guiar la implementación paso a paso.

## Decisión

OpenSpec, en la carpeta `openspec/` del repositorio.

## Consecuencias

- **Relación con `docs/`:** `docs/` explica el reto y las reglas de diseño; `openspec/` especifica lo que se construye.
  - Cada especificación cita los requerimientos que cubre (ej.: REQ-0008, handoff JSON).
  - El contexto del proyecto de OpenSpec enlaza a [arquitectura](../../entender/arquitectura.md), [conversación](../conversacion.md) y [seguridad](../seguridad.md), en vez de copiarlos.
- **Idioma:** por definir. Las especificaciones son parte de la entrega pública, por lo que conviene escribirlas en inglés.
- **Flujo de trabajo:** propuesta de cambio → revisión en pull request → implementación → archivo del cambio. Los issues de GitHub enlazan a su propuesta.
- Pendiente: instalar OpenSpec e inicializar la carpeta después de elegir el flujo (lunes 28/9).
