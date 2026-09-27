# Sentinel Engine

Felix, Natalia y Rubén · Factored AI & Data Hackathon 2026 · Entrega: **lunes 5/10**

Este es nuestro punto de partida y documento central. Estamos construyendo un sistema robusto, donde **el diseño y la arquitectura son un esfuerzo conjunto de los tres**, aprovechando nuestras fortalezas conjuntas en Ingeniería de Datos, Desarrollo Backend e Inteligencia Artificial. Todos estamos involucrados directamente en la construcción del sistema de IA desde nuestras respectivas áreas.

## Qué vamos a construir

Un **asistente de atención al cliente para un banco** que opera en México, Colombia y Argentina[cite: 2, 3]. La idea es que no sea solo un chatbot: que entienda al cliente, responda con datos verificados, haga acciones seguras, confirme que ocurrieron y pase el caso a una persona cuando haga falta[cite: 4].

**Flujo Seleccionado:** Ingreso de disputas de transacciones (Transaction-dispute intake)[cite: 1].
**Idiomas soportados:** Español y portugués (requerimiento de evaluación)[cite: 1].

## El Equipo y Roles

**Arquitectura y Diseño del Sistema (Todo el equipo):** La definición de la arquitectura general, los flujos de información y la integración entre Azure y Databricks se diseña y acuerda de manera colaborativa. A partir de esa base, nos enfocamos en la ejecución aplicando IA desde nuestra especialidad:

- **Natalia (IA - Capa de Datos):** Procesamiento incremental y batch de los ~19M de registros sintéticos[cite: 1, 3]. Implementación de la arquitectura Medallion en Azure Databricks y ADLS Gen2, garantizando contratos de datos, linaje y manejo de calidad (tratamiento del 2% de duplicados y 5% de nulos)[cite: 1, 3].
- **Felix (IA - Capa de Atención - Backend & Tools):** Desarrollo del orquestador, endpoints y mocks transaccionales desplegados en Azure[cite: 1, 5]. Implementación estricta de control de acceso a nivel de herramienta (aislamiento por sesión de cliente) garantizando que se verifiquen las acciones[cite: 1, 6].
- **Rubén (IA - ML - Componentes Inteligentes):** Desarrollo del componente aprendido (predictor de escalamiento)[cite: 5]. Integración del LLM, manejo del contexto conversacional, y estructuración del `Handoff JSON` con hechos verificados y preguntas abiertas para el asesor humano[cite: 1, 5].

## Para empezar (unos 15 minutos)

1. **[El reto en una página](docs/entender/resumen.md):** qué hay que construir, cómo nos evalúan y qué se entrega.
2. **[Plan del equipo](docs/plan.md):** un cronograma tentativo, una propuesta de cómo trabajar y las decisiones que tomaremos juntos.
3. **[Arquitectura](docs/entender/arquitectura.md):** diseño de nuestras dos capas (Databricks + Azure App).

## Dos cosas obligatorias

Las pide el hackathon, así que conviene tenerlas presentes desde el primer commit[cite: 4]:

- **No subir secretos ni datos al repositorio[cite: 4].** Las credenciales van en un archivo `.env`, que git ignora, y se comparten por mensaje directo[cite: 4].
- **La entrega va en inglés[cite: 4].** Por ahora trabajamos en español; al final pasamos a inglés este README, la presentación y el video[cite: 4].