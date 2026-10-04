# Probe v3: development cases through the served prompt

Rows: 60. Kind match: 60/60. Subtype match: 40/40.
Drafts returned: 44. Rejected: 0. Live spend: USD 0.036115 (cap 0.45).

Felix spotlight: `v3-loan-es-MX` (point 4, loan stays out of scope) and `v3-amount-es-MX` (point 8, amount slot 1000). Both rows are marked below.

| Case | Message | Kind (want) | Subtype (want) | Slots | Draft raw | Draft shown | Reject | Lang |
|---|---|---|---|---|---|---|---|---|
| v3-amount-es-AR | No reconozco un consumo de mil pesos | charge (charge) | - (-) | amount=1000.0 | - | - | - | es-419 |
| v3-amount-es-CO | No reconozco un cobro de mil pesos | charge (charge) | - (-) | amount=1000.0 | - | - | - | es-419 |
| v3-amount-es-MX **[Felix 8]** | Hay un cobro de mil pesos que no reconozco | charge (charge) | - (-) | amount=1000.0 | - | - | - | es-419 |
| v3-amount-pt-BR | Não reconheço uma cobrança de mil reais | charge (charge) | - (-) | amount=1000.0 | - | - | - | pt-BR |
| v3-balance-es-AR | ¿Cuánta guita tengo disponible? | out_of_scope (out_of_scope) | balance (balance) | - | Te digo cómo ver tu saldo en la app. | Te digo cómo ver tu saldo en la app. | ok | es-419 |
| v3-balance-es-CO | ¿Cuál es el saldo de mi cuenta de ahorros? | out_of_scope (out_of_scope) | balance (balance) | - | Te muestro cómo ver tu saldo en la app. | Te muestro cómo ver tu saldo en la app. | ok | es-419 |
| v3-balance-es-MX | ¿Cuánta plata tengo en mi cuenta? | out_of_scope (out_of_scope) | balance (balance) | - | Te digo cómo consultar tu saldo en la app. | Te digo cómo consultar tu saldo en la app. | ok | es-419 |
| v3-balance-pt-BR | Quanto dinheiro eu tenho na conta? | out_of_scope (out_of_scope) | balance (balance) | - | Vou te mostrar como consultar seu saldo no aplicativo. | Vou te mostrar como consultar seu saldo no aplicativo. | ok | pt-BR |
| v3-bye-es-AR | Chau, hasta luego | missing (missing) | goodbye (goodbye) | - | ¡Hasta luego! Que tengas un buen día. | ¡Hasta luego! Que tengas un buen día. | ok | es-419 |
| v3-bye-es-CO | Chao, gracias | missing (missing) | goodbye (goodbye) | - | ¡Chao! Que tengas un buen día. | ¡Chao! Que tengas un buen día. | ok | es-419 |
| v3-bye-es-MX | Adiós, nos vemos | missing (missing) | goodbye (goodbye) | - | ¡Hasta luego! Que tengas un buen día. | ¡Hasta luego! Que tengas un buen día. | ok | es-419 |
| v3-bye-pt-BR | Tchau, até mais | missing (missing) | goodbye (goodbye) | - | Até logo! Estou por aqui se precisar. | Até logo! Estou por aqui se precisar. | ok | pt-BR |
| v3-card-es-AR | Quiero pedir una tarjeta nueva | out_of_scope (out_of_scope) | card (card) | - | Te explico cómo solicitar una tarjeta nueva. | Te explico cómo solicitar una tarjeta nueva. | ok | es-419 |
| v3-card-es-CO | Necesito una tarjeta de crédito nueva | out_of_scope (out_of_scope) | card (card) | - | Te explico cómo solicitar una tarjeta nueva. | Te explico cómo solicitar una tarjeta nueva. | ok | es-419 |
| v3-card-es-MX | Quiero subir el límite de mi tarjeta | out_of_scope (out_of_scope) | card (card) | - | Te explico cómo solicitar el aumento de límite de tu tarjeta. | Te explico cómo solicitar el aumento de límite de tu tarjeta. | ok | es-419 |
| v3-card-pt-BR | Quero pedir um cartão novo | out_of_scope (out_of_scope) | card (card) | - | Vou te explicar como pedir um cartão novo. | Vou te explicar como pedir um cartão novo. | ok | pt-BR |
| v3-greet-es-AR | Hola, ¿cómo andás? | missing (missing) | greeting (greeting) | - | ¡Hola! ¿En qué te ayudo hoy? | ¡Hola! ¿En qué te ayudo hoy? | ok | es-419 |
| v3-greet-es-CO | Buenos días, ¿cómo están? | missing (missing) | greeting (greeting) | - | ¡Hola! ¿En qué te puedo colaborar hoy? | ¡Hola! ¿En qué te puedo colaborar hoy? | ok | es-419 |
| v3-greet-es-MX | Hola, buenos días | missing (missing) | greeting (greeting) | - | ¡Hola! ¿En qué te ayudo hoy? | ¡Hola! ¿En qué te ayudo hoy? | ok | es-419 |
| v3-greet-pt-BR | Olá, bom dia | missing (missing) | greeting (greeting) | - | Olá! Como posso ajudar hoje? | Olá! Como posso ajudar hoje? | ok | pt-BR |
| v3-greetcharge-es-AR | Hola, soy Ana y no reconozco un consumo | charge (charge) | - (-) | - | - | - | - | es-419 |
| v3-greetcharge-es-CO | Buenas, soy Ana y me aparece un cobro que no hice | charge (charge) | - (-) | - | - | - | - | es-419 |
| v3-greetcharge-es-MX | Hola, soy Ana y no reconozco un cargo | charge (charge) | - (-) | - | - | - | - | es-419 |
| v3-greetcharge-pt-BR | Olá, sou Ana e não reconheço uma cobrança | charge (charge) | - (-) | - | - | - | - | pt-BR |
| v3-help-es-AR | ¿Me das una mano con la cuenta? | missing (missing) | help (help) | - | ¡Claro! ¿Qué necesitás con tu cuenta? | ¡Claro! ¿Qué necesitás con tu cuenta? | ok | es-419 |
| v3-help-es-CO | Necesito ayuda con mi cuenta | missing (missing) | help (help) | - | Claro, ¿me cuentas qué pasó con tu cuenta? | Claro, ¿me cuentas qué pasó con tu cuenta? | ok | es-419 |
| v3-help-es-MX | ¿Me puedes ayudar con una duda? | missing (missing) | help (help) | - | ¡Claro! Contame tu duda y te ayudo. | ¡Claro! Contame tu duda y te ayudo. | ok | es-419 |
| v3-help-pt-BR | Preciso de ajuda com a minha conta | missing (missing) | help (help) | - | Claro, me conta o que está acontecendo com sua conta. | Claro, me conta o que está acontecendo com sua conta. | ok | pt-BR |
| v3-identity-es-AR | ¿Sos un bot? | missing (missing) | identity (identity) | - | Soy un asistente del banco, ¿en qué te ayudo? | Soy un asistente del banco, ¿en qué te ayudo? | ok | es-419 |
| v3-identity-es-CO | ¿Usted es un robot? | missing (missing) | identity (identity) | - | Soy un asistente del banco, ¿en qué te colaboro? | Soy un asistente del banco, ¿en qué te colaboro? | ok | es-419 |
| v3-identity-es-MX | ¿Eres un bot o una persona? | missing (missing) | identity (identity) | - | Soy un asistente del banco, ¿en qué te ayudo? | Soy un asistente del banco, ¿en qué te ayudo? | ok | es-419 |
| v3-identity-pt-BR | Você é um robô ou uma pessoa? | missing (missing) | identity (identity) | - | Sou um assistente do banco, como posso ajudar? | Sou um assistente do banco, como posso ajudar? | ok | pt-BR |
| v3-loan-es-AR | Quiero pedir un préstamo | out_of_scope (out_of_scope) | loan (loan) | - | Te explico qué puedo hacer por tu préstamo. | Te explico qué puedo hacer por tu préstamo. | ok | es-419 |
| v3-loan-es-CO | Necesito un préstamo de libre inversión | out_of_scope (out_of_scope) | loan (loan) | - | Te explico qué opciones de préstamo tenemos. | Te explico qué opciones de préstamo tenemos. | ok | es-419 |
| v3-loan-es-MX **[Felix 4]** | Quiero un préstamo personal | out_of_scope (out_of_scope) | loan (loan) | - | Te explico qué puedo hacer por tu préstamo. | Te explico qué puedo hacer por tu préstamo. | ok | es-419 |
| v3-loan-pt-BR | Quero um empréstimo pessoal | out_of_scope (out_of_scope) | loan (loan) | - | Vou explicar o que posso fazer pelo seu empréstimo. | Vou explicar o que posso fazer pelo seu empréstimo. | ok | pt-BR |
| v3-merchantdate-es-AR | No reconozco el consumo de la cafetería de ayer | charge (charge) | - (-) | merchant_words='la cafetería'; date_phrase='ayer' | - | - | - | es-419 |
| v3-merchantdate-es-CO | No reconozco el cobro de la cafetería de ayer | charge (charge) | - (-) | merchant_words='la cafetería'; date_phrase='ayer' | - | - | - | es-419 |
| v3-merchantdate-es-MX | No reconozco el cargo de la cafetería de ayer | charge (charge) | - (-) | merchant_words='la cafetería'; date_phrase='ayer' | - | - | - | es-419 |
| v3-merchantdate-pt-BR | Não reconheço a cobrança da cafeteria de ontem | charge (charge) | - (-) | merchant_words='cafeteria'; date_phrase='ontem' | - | - | - | pt-BR |
| v3-status-es-AR | ¿Cómo va el estado de mi último consumo? | status (status) | - (-) | - | Reviso el estado de tu consumo y te lo muestro. | Reviso el estado de tu consumo y te lo muestro. | ok | es-419 |
| v3-status-es-CO | ¿En qué estado está mi último cobro? | status (status) | - (-) | - | Reviso el estado de tu cobro y te lo muestro. | Reviso el estado de tu cobro y te lo muestro. | ok | es-419 |
| v3-status-es-MX | Quiero ver el estado de mi último cargo | status (status) | - (-) | - | Reviso el estado de tu cargo y te lo muestro. | Reviso el estado de tu cargo y te lo muestro. | ok | es-419 |
| v3-status-pt-BR | Quero ver o estado da minha última cobrança | status (status) | - (-) | - | Vou verificar o estado da sua cobrança e te mostro. | Vou verificar o estado da sua cobrança e te mostro. | ok | pt-BR |
| v3-thanks-es-AR | Gracias, genio | missing (missing) | thanks (thanks) | - | ¡De nada! ¿Te ayudo en algo más? | ¡De nada! ¿Te ayudo en algo más? | ok | es-419 |
| v3-thanks-es-CO | Gracias, muy amable | missing (missing) | thanks (thanks) | - | ¡Con gusto! ¿Necesitas algo más? | ¡Con gusto! ¿Necesitas algo más? | ok | es-419 |
| v3-thanks-es-MX | Muchas gracias por tu ayuda | missing (missing) | thanks (thanks) | - | ¡De nada! ¿Te ayudo en algo más? | ¡De nada! ¿Te ayudo en algo más? | ok | es-419 |
| v3-thanks-pt-BR | Obrigado pela ajuda | missing (missing) | thanks (thanks) | - | De nada! Precisa de mais alguma coisa? | De nada! Precisa de mais alguma coisa? | ok | pt-BR |
| v3-transfer-es-AR | Hice una transferencia que no llegó | out_of_scope (out_of_scope) | transfer (transfer) | - | Te explico cómo revisar esa transferencia. | Te explico cómo revisar esa transferencia. | ok | es-419 |
| v3-transfer-es-CO | Envié una transferencia y no aparece | out_of_scope (out_of_scope) | transfer (transfer) | - | Te explico cómo revisar el estado de tu transferencia. | Te explico cómo revisar el estado de tu transferencia. | ok | es-419 |
| v3-transfer-es-MX | Hice una transferencia que no llega | out_of_scope (out_of_scope) | transfer (transfer) | - | Te explico cómo revisar el estado de tu transferencia. | Te explico cómo revisar el estado de tu transferencia. | ok | es-419 |
| v3-transfer-pt-BR | Fiz uma transferência que não chegou | out_of_scope (out_of_scope) | transfer (transfer) | - | Vou te explicar como acompanhar sua transferência. | Vou te explicar como acompanhar sua transferência. | ok | pt-BR |
| v3-twice-es-AR | Me cobraron dos veces el mismo consumo | charge (charge) | - (-) | twice=True | - | - | - | es-419 |
| v3-twice-es-CO | Me hicieron el mismo cobro dos veces | charge (charge) | - (-) | twice=True | - | - | - | es-419 |
| v3-twice-es-MX | Me cobraron dos veces en la cafetería | charge (charge) | - (-) | merchant_words='la cafetería'; twice=True | - | - | - | es-419 |
| v3-twice-pt-BR | Me cobraram duas vezes na cafeteria | charge (charge) | - (-) | merchant_words='cafeteria'; twice=True | - | - | - | es-419 |
| v3-unclear-es-AR | Algo raro ayer, che | missing (missing) | unclear (unclear) | - | ¿Me contás un poco más sobre lo que viste? | ¿Me contás un poco más sobre lo que viste? | ok | es-419 |
| v3-unclear-es-CO | Pasó algo raro ayer, no sé qué fue | missing (missing) | unclear (unclear) | - | ¿Me das más detalles sobre lo que pasó? | ¿Me das más detalles sobre lo que pasó? | ok | es-419 |
| v3-unclear-es-MX | Algo raro pasó ayer con mi cuenta | missing (missing) | unclear (unclear) | - | ¿Me cuentas un poco más sobre lo que viste? | ¿Me cuentas un poco más sobre lo que viste? | ok | es-419 |
| v3-unclear-pt-BR | Algo estranho aconteceu ontem na conta | missing (missing) | unclear (unclear) | - | Pode me contar mais sobre o que você viu? | Pode me contar mais sobre o que você viu? | ok | pt-BR |
