# Conversación

Cómo se comporta el asistente con el cliente, organizado por situación, y cómo maneja el español y el portugués. Es la base de la demo y del video.

**Para qué sirve:** decidir qué dice y qué hace el asistente en cada situación. **Relacionados:** [arquitectura](../entender/arquitectura.md), [seguridad](seguridad.md), [requerimientos](../requerimientos/requerimientos.md).

## Principios

- **La IA entiende; el código ejecuta y verifica** (ver [arquitectura](../entender/arquitectura.md#principio-central)).
- **Autonomía según el riesgo:** las acciones con consecuencias (bloquear, abrir un reclamo) piden confirmación (REQ-0006, reglas de autonomía).
- **Solo hechos verificados;** si el dato no existe, decirlo y ofrecer una alternativa. Nunca responder con el conocimiento propio del modelo (REQ-0003, registros verificados).
- **Separar lo verificado de lo que declara el cliente.**
- **Solo reportar acciones confirmadas** por la herramienta; timeout no es éxito (REQ-0005, acciones verificadas).

## Cuando los datos no están al día

REQ-0039 (declarar frescura). Si el cliente menciona algo más reciente que los datos, no afirmar que se ve:

> "Mis registros están actualizados hasta hoy a las 00:00 y todavía no veo ese cobro. Puedo abrir el reclamo ahora como pendiente de verificación; se confirmará en la próxima actualización. ¿Lo abro?"

## Cuando falta información

REQ-0002 (aclarar o abstenerse). Preguntar solo lo imprescindible. Si se puede, **mostrar opciones** verificadas en vez de pedir que el cliente escriba datos.

## Al abrir un reclamo

REQ-0042 (mínimo esfuerzo) y REQ-0043 (revisar el estado del cargo).

1. Buscar las transacciones candidatas del cliente de la sesión.
2. Revisar el estado: **Pending** puede ser una preautorización que se libera sola (ofrecer esperar o reclamar); **Reversed** significa que ya se devolvió.
3. Mostrar las candidatas y que el cliente elija:
   > "Veo estas compras repetidas en los últimos 7 días:
   > 1. Supermercado Éxito, 85.000 COP, 25/09, tarjeta de débito •••4521
   > 2. Rappi, 32.500 COP, 24/09, tarjeta de crédito •••7788
   > ¿Cuál quieres reclamar?"
4. Dos cargos iguales pueden ser legítimos: mostrar los hechos sin concluir que hubo un error.
5. Si no aparece, pedir lo mínimo y abrir el reclamo como **pendiente de verificación**.
6. Pedir confirmación antes de abrirlo; informar el número de caso solo cuando la herramienta lo confirme.

## Cuando el cliente pide hablar con una persona

REQ-0040 (pedido de asesor). Lo decide la política en código, no el predictor ni el LLM.

- Una sola oferta: "Puedo ayudarte con esto ahora mismo. ¿Prefieres intentarlo conmigo o que te comunique con un asesor?"
- Si repite o elige asesor: escalar de inmediato, sin insistir.
- Registrar cada pedido: muchos pedidos en un mismo paso señalan un problema del flujo.

## Contexto de la app

REQ-0045 (errores recientes de la app, solo como contexto auxiliar: el diagnóstico de app no es un flujo del planteamiento). Si hay un error reciente (ej.: transferencia fallida), ofrecerlo como pregunta: "¿Tu consulta tiene que ver con la transferencia que falló ayer?". Nunca afirmarlo ni sorprender al cliente.

## Lenguaje

REQ-0044 (español neutro) y REQ-0041 (moneda original). El país de la cuenta no dice de dónde es el cliente (ej.: un venezolano en Colombia).

- Español neutro y claro, sin modismos de un solo país.
- Explicar las siglas y los términos locales la primera vez (ej.: "SPEI, el sistema de transferencias inmediatas de México").
- Entender términos de otros países ("pago móvil", "Pix") y responder con lo que sí existe en su banco.
- El idioma de la respuesta sigue al cliente; la moneda sigue a la cuenta (ver [idiomas](#idioma-país-y-moneda-son-independientes)).
- Equivalencias por país en el [glosario](../entender/glosario.md).

## Idiomas

### Qué pide el reto

- Interacciones **robustas** en español y portugués. El kickoff lo marca como obligatorio.
- Reportar las limitaciones de datos y de cobertura de idiomas.
- No se exige paridad exacta, pero sí medir por idioma e investigar las diferencias.

### Riesgo principal

**No nos dan datos en portugués para construir** (el dataset confirma: todo el texto está en español, con acentos de México, Colombia y Argentina; ningún país lusófono), pero los evaluadores probablemente sí prueben en PT, como un set de prueba oculto.

### Estrategia

- Preferir componentes **multilingües** (LLM, embeddings multilingües) sobre modelos entrenados solo en ES.
- La lógica determinista **no depende del idioma**: nada de palabras clave solo en español.
- Crear casos de prueba propios en PT (traducidos o sintéticos), **etiquetados como tales** y **reservados**: no se usan para ajustar el sistema.
- Incluir PT en el set adversarial (injection, ambigüedad multilingüe).

### Idioma, país y moneda son independientes

Un cliente puede escribir en portugués y tener su cuenta en MX, CO o AR.

- El **idioma de la respuesta** sigue al cliente.
- La **moneda** sigue a la cuenta o transacción (MXN, COP, ARS o USD), nunca se convierte al idioma.
- Las métricas se desglosan por idioma **y** por país, por separado.

### Portugués de Brasil

Lo más probable es que las pruebas en portugués sean de Brasil (pt-BR). El cliente puede usar términos propios del sistema brasileño (Pix, extrato, estorno, atendente, CPF) aunque su cuenta sea de MX, CO o AR. El asistente debe entenderlos, pero responder con los datos reales de la cuenta (por ejemplo, no hay Pix en el dataset). Equivalencias en el [glosario](../entender/glosario.md#equivalencias-por-país).

### Variantes del español

El dataset incluye campos de detección de acento (mexicano, colombiano, argentino y, en `customers`, neutral). Sirven como segmentos para medir equidad dentro del español.

### Cómo se reporta

- Métricas desglosadas por idioma, con n.
- Si PT rinde peor: explicar la causa (ej.: sin datos de entrenamiento en PT), no ocultarlo.

### Preguntas abiertas

- ¿Cómo generamos y validamos los casos en PT? ¿Alguien del equipo lee portugués?
- ¿Cuántos casos PT necesitamos para que la comparación tenga sentido?
