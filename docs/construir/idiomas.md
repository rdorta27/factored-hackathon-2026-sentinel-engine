# Idiomas

**Para qué sirve:** estrategia de español y portugués. **Requerimientos:** R-12 (ES y PT robustos), R-13 (limitaciones de idiomas), R-24 (desglose por idioma), R-44 (español neutro). Ver [requerimientos](../requerimientos/requerimientos.md). **Relacionados:** [conversación](conversacion.md), [glosario](../entender/glosario.md).

## Requerimiento

- Interacciones **robustas** en español y portugués. El kickoff lo marca como obligatorio.
- Reportar las limitaciones de datos y de cobertura de idiomas.
- No se exige paridad exacta, pero sí medir por idioma e investigar las diferencias.

## Riesgo principal

**No nos dan datos en portugués para construir** (el dataset confirma: todo el texto está en español, con acentos de México, Colombia y Argentina; ningún país lusófono), pero los evaluadores probablemente sí prueben en PT, como un set de prueba oculto.

## Estrategia

- Preferir componentes **multilingües** (LLM, embeddings multilingües) sobre modelos entrenados solo en ES.
- La lógica determinista **no depende del idioma**: nada de palabras clave solo en español.
- Crear casos de prueba propios en PT (traducidos o sintéticos), **etiquetados como tales** y **reservados**: no se usan para ajustar el sistema.
- Incluir PT en el set adversarial (injection, ambigüedad multilingüe).

## Idioma, país y moneda son independientes

Un cliente puede escribir en portugués y tener su cuenta en MX, CO o AR.

- El **idioma de la respuesta** sigue al cliente.
- La **moneda** sigue a la cuenta o transacción (MXN, COP, ARS o USD), nunca se convierte al idioma.
- Las métricas se desglosan por idioma **y** por país, por separado.

## Portugués de Brasil

Lo más probable es que las pruebas en portugués sean de Brasil (pt-BR). El cliente puede usar términos propios del sistema brasileño (Pix, extrato, estorno, atendente, CPF) aunque su cuenta sea de MX, CO o AR. El asistente debe entenderlos, pero responder con los datos reales de la cuenta (por ejemplo, no hay Pix en el dataset). Equivalencias en el [glosario](../entender/glosario.md#equivalencias-por-país).

## Clientes de cualquier origen

El país de la cuenta no indica el origen del cliente (ej.: un venezolano con cuenta en Colombia). Español neutro, siglas y términos locales explicados, y comprensión de términos de otros países. Detalle en [conversación](conversacion.md#lenguaje).

## Variantes del español

El dataset incluye campos de detección de acento (MX, CO, AR). Sirven como segmentos para medir equidad dentro del español.

## Cómo se reporta

- Métricas desglosadas por idioma, con n.
- Si PT rinde peor: explicar la causa (ej.: sin datos de entrenamiento en PT), no ocultarlo.

## Preguntas abiertas

- ¿Cómo generamos y validamos los casos en PT? ¿Alguien del equipo lee portugués?
- ¿Cuántos casos PT necesitamos para que la comparación tenga sentido?
