# Glosario

**Para qué sirve:** traducir términos técnicos, del negocio y del material oficial. **Relacionados:** [resumen](resumen.md), [dataset](dataset.md).

Dos vocabularios:

- **Construcción:** cómo armamos el sistema. Es el que usamos mientras diseñamos e implementamos.
- **Funcional:** cómo se llama cada cosa dentro del sistema terminado, en lenguaje bancario (para la interfaz, la presentación y el negocio).

La columna "Oficial" muestra el término del material del hackathon, para ubicarlo en los PDF.

## Contenido

[Siglas del negocio](#siglas-y-términos-del-negocio) · [Equivalencias por país](#equivalencias-por-país) · [Arquitectura](#arquitectura) · [Atención](#atención) · [Casos de uso](#casos-de-uso) · [Datos](#datos) · [Evaluación](#evaluación)

## Siglas y términos del negocio

El público del hackathon es técnico (software, datos). Estos términos de contact center y banca se explican siempre.

| Término | En inglés | Qué significa |
|---|---|---|
| CSAT | Customer Satisfaction Score | Satisfacción con una atención puntual, de 1 a 5 |
| NPS | Net Promoter Score | "¿Recomendarías el banco?" de 0 a 10; % de 9-10 menos % de 0-6 (de −100 a +100) |
| CES | Customer Effort Score | Qué tan fácil fue resolver el problema |
| FCR | First Call Resolution | Resuelto en el primer contacto, sin volver a llamar |
| IVR | Interactive Voice Response | Menú telefónico automático ("marque 1 para…") |
| STT | Speech-to-Text | Conversión de audio a texto |
| PQR | — | Peticiones, quejas y reclamos: sistema donde se registran |
| Contracargo | Chargeback | Devolución de un cobro con tarjeta no reconocido o incorrecto |
| Preautorización | Pre-authorization | Retención temporal de dinero; aparece como pendiente y suele liberarse sola |
| MCC | Merchant Category Code | Código del tipo de comercio |
| CLV | Customer Lifetime Value | Dinero que deja un cliente durante toda su relación con el banco |
| Churn | Churn | Abandono del cliente |
| Días de mora | Days past due | Días de atraso en el pago de un crédito |
| DNI, CURP, CC, CE | — | Documentos de identidad: DNI (AR), CURP (MX), cédula de ciudadanía y de extranjería (CO) |
| SLA | Service Level Agreement | Acuerdo de nivel de servicio: plazo máximo comprometido (ej.: responder un reclamo en 15 días); incumplirlo es "SLA breached" |
| UTM | Urchin Tracking Module | Parámetros en un link de campaña que indican de qué campaña y canal vino una visita |
| Conversión | Conversion | El cliente hizo lo que buscaba la campaña (ej.: pidió la tarjeta) |
| Supervisor | Supervisor | Responsable de un grupo de asesores; recibe los casos que un asesor no puede resolver |

## Equivalencias por país

- **Dataset:** México, Colombia y Argentina.
- **Brasil:** el reto exige atender en portugués, y lo más probable es que las pruebas sean en portugués de Brasil.
- **Venezuela y Ecuador:** no aplican a la solución. Están para que el equipo entienda los términos desde su propia experiencia.

Las siglas de métricas (CSAT, NPS, CES, FCR) son iguales en todos los países.

**Verificar con el equipo:** los términos de Venezuela y Ecuador deben confirmarlos los miembros de esos países.

### Términos bancarios

| Concepto | Dataset (MX / CO / AR) | Brasil (pt-BR) | Venezuela | Ecuador |
|---|---|---|---|---|
| Moneda | MXN / COP / ARS (+ USD) | BRL (real) | VES (bolívar) | USD (economía dolarizada) |
| Documento de identidad | CURP / CC, CE / DNI | CPF (número de registro de persona) y RG (carnet de identidad) | Cédula de identidad (V- nacional, E- extranjero) | Cédula de identidad |
| Cuenta corriente | Cuenta corriente / de cheques | Conta corrente | Cuenta corriente | Cuenta corriente |
| Cuenta de ahorro | Cuenta de ahorro | Conta poupança | Cuenta de ahorro | Cuenta de ahorros |
| Estado de cuenta | Estado de cuenta | Extrato | Estado de cuenta | Estado de cuenta |
| Saldo | Saldo | Saldo | Saldo | Saldo |
| Tarjeta de crédito / débito | Tarjeta de crédito / débito | Cartão de crédito / débito | Tarjeta de crédito / débito | Tarjeta de crédito / débito |
| Bloquear la tarjeta | Bloquear la tarjeta | Bloquear o cartão | Bloquear la tarjeta | Bloquear la tarjeta |
| Cargo no reconocido | Cargo no reconocido | Compra não reconhecida | Cargo no reconocido | Consumo no reconocido |
| Contracargo / devolución | Contracargo | Contestação de compra, estorno (devolución) | Reverso | Reverso, contracargo |
| Preautorización | Preautorización | Pré-autorização | Retención | Retención |
| Mora | Mora, días de atraso | Inadimplência, dias de atraso | Mora | Mora |
| Pago inmediato entre cuentas | Transferencia (SPEI en MX) | Pix | Pago móvil | Transferencia |

### Atención al cliente

| Concepto | Dataset (MX / CO / AR) | Brasil (pt-BR) | Venezuela | Ecuador |
|---|---|---|---|---|
| Asesor del call center | Asesor, agente, ejecutivo | Atendente | Operador, asesor | Asesor |
| Central de atención | Call center, centro de contacto | Central de atendimento, SAC (Serviço de Atendimento ao Consumidor) | Call center, centro de atención | Call center, centro de contacto |
| Sistema de reclamos | PQR (CO), aclaraciones (MX), reclamos (AR) | SAC; si no se resuelve, Ouvidoria (defensoría interna del banco) | Reclamos | Reclamos |
| Defensor del cliente | Defensor del consumidor financiero (CO) | Ouvidoria | Defensor del cliente | Defensor del cliente |
| Regulador bancario | CNBV (MX), SFC (CO), BCRA (AR) | Banco Central do Brasil | SUDEBAN | Superintendencia de Bancos |
| "Quiero hablar con una persona" | Quiero hablar con un asesor | Quero falar com um atendente | Quiero hablar con un operador | Quiero hablar con un asesor |

## Arquitectura

| Construcción | Funcional | Oficial | Definición |
|---|---|---|---|
| Capa de atención | Atención en tiempo real | — | Conversación, orquestador, herramientas y acciones. Responde al cliente al instante |
| Capa de datos | Procesamiento de datos | Pipeline | Prepara los datos que la capa de atención lee: contratos, deduplicación, upsert, almacenes |
| Orquestador | Asistente | Agent | Componente que entiende, decide, actúa, verifica y escala |
| Herramienta | Consulta u operación | Tool | Función que el orquestador llama para leer datos o ejecutar acciones, con control de acceso |
| Almacén operativo | Core bancario (simulado) | — | Datos por cliente que consultan las herramientas |
| Almacén analítico | — | — | Datos para análisis, línea base y entrenamiento |

## Atención

| Construcción | Funcional | Oficial | Definición |
|---|---|---|---|
| Handoff | Escalamiento a un asesor | Handoff / escalation | Paso del caso a una persona con resumen estructurado |
| Contención | Casos sin escalamiento | Containment | Casos que terminan sin pasar a una persona; no equivale a resolver |
| Resolución automatizada segura | Resolución sin asesor | Safe automated resolution | Caso resuelto bien y conforme a políticas, sin intervención humana |
| Abstención | Solicitud no atendida | Abstention | El sistema decide no actuar y lo explica |

## Casos de uso

| Construcción | Funcional | Oficial | Definición |
|---|---|---|---|
| Elección del flujo | — | Task selection | Qué trabajo de atención realizará el asistente; el proyecto (el asistente) ya está fijado |
| Flujo de reclamos | Reclamo por cargo no reconocido / contracargo | Transaction disputes | El cliente no reconoce un cargo y pide revertirlo |
| — | Queja | Complaint | Insatisfacción con el servicio; en el dataset, parte de PQR |
| — | PQR | Complaints (PQR) | Peticiones, quejas y reclamos |
| Flujo de tarjetas | Servicios de tarjeta | Card support | Bloqueo, reposición, consultas de tarjeta |
| Flujo de cuentas y pagos | Consultas de cuenta y pagos | Account / payment inquiries | Saldos, movimientos, estado de pagos |
| Flujo de crédito | Información y elegibilidad de crédito | Credit-product info & eligibility | Condiciones de productos y resultado de elegibilidad simulado |

## Datos

| Construcción | Funcional | Oficial | Definición |
|---|---|---|---|
| Upsert | Insertar o actualizar | — | Si la clave existe, actualiza; si no, inserta. Idempotente |
| Watermark | Marca de avance | — | Hasta qué partición se procesó |
| Ventana de reproceso | — | — | Últimos N días que se vuelven a procesar para capturar llegadas tardías |
| Contrato de datos | — | Data contract | Esquema y reglas que un dato debe cumplir para entrar |
| Frescura | Actualizado hasta | Freshness | Atraso entre que ocurre algo y que el sistema lo ve |
| Idempotente | — | — | Repetir la operación deja el mismo resultado |
| Registro huérfano | — | Orphaned record | Registro que apunta a otro que no existe (ej.: transacción de un cliente inexistente) |

## Evaluación

| Construcción | Funcional | Oficial | Definición |
|---|---|---|---|
| Held-out | Casos de prueba reservados | Held-out | Casos que no se usan para ajustar el sistema; se miden una vez al final |
| Línea base | Punto de comparación | Baseline | Versión simple contra la que se compara el sistema |
| Fuga de datos | — | Leakage | Información de prueba que se filtra al entrenamiento e infla las métricas: por caso partido, por división que ve el futuro o por variables que usan información posterior |
| Set adversarial | Pruebas de ataque | — | Casos de injection, acceso no autorizado, fallas |
| p50 / p95 | Tiempo típico / tiempo de los casos lentos | p50 / p95 latency | Percentiles de latencia |
