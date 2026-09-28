# 001 · Plataforma: Microsoft Azure

**Fecha:** 2026-09-27
**Estado:** Aceptada
**Participantes:** Equipo

## Contexto

El kickoff deja libertad de herramientas y sugiere Azure, Snowflake, AWS y Databricks como opcionales. Necesitamos dónde desplegar la herramienta (REQ-0035, link desplegado), un LLM que cumpla los límites de datos (REQ-0047, el LLM no recibe datos personales; REQ-0031, datos aprobados) y dónde guardar los secretos.

## Opciones

1. **Azure:** un solo proveedor para LLM, despliegue, almacenamiento y secretos. Sugerido en el kickoff.
2. **AWS:** equivalente en servicios; también sugerido.
3. **Servicios gratuitos sueltos** (Hugging Face Spaces, Render, APIs gratuitas de LLM): sin costo, pero menos control sobre los datos y más piezas que integrar.

## Decisión

Azure.

## Consecuencias

- Servicios a definir (propuesta, pendiente de confirmar):
  - **LLM:** Azure OpenAI (Azure AI Foundry). Verificar que no retiene los datos ni los usa para entrenar.
  - **Despliegue:** Azure Container Apps o App Service.
  - **Secretos:** Azure Key Vault o variables de entorno del servicio; nunca en el repositorio.
  - **Datos:** donde lleguen los datos del hackathon (almacenamiento de Azure o local).
- Pendiente: quién tiene la suscripción o los créditos, y fijar un **tope de gasto** y alertas de presupuesto desde el primer día.
- El despliegue público necesita límites de uso para evitar abuso (ver [seguridad](../seguridad.md#repositorio-y-despliegue-públicos)).
- La presentación debe justificar la elección: reproducibilidad, control de datos y despliegue.
