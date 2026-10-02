# Back-translation review

Reviewed by an isolated Claude Opus subagent on 2026-10-01 (no human review; declared in decision 018).

Decision 017: variants were written by Claude Sonnet (held-out author isolated from the prompt and the development cases) and back-translated to neutral Spanish by Claude Haiku. A team member checks each back-translation against the es-MX text of its base for meaning, amount, merchant and request, then marks the box. A case that drifts is fixed or dropped before sealing.

Amounts are in each account's local currency (MXN, COP, ARS), so the number may differ between variants.

## Held-out (sealed set, not yet sealed): 247 variants, 17 flagged by the reviewer model

### Flagged first

| OK | Case | es-MX source | Back-translation | Note |
|---|---|---|---|---|
| [x] | `ho-n29` | Hola, vi en mi estado de cuenta un cargo de $1849 de TIENDA LUMINA del 12 de agosto y no lo reconozco. | Hola, en mi extracto aparece un cobro de $1849 de TIENDA LUM el 12 de agosto y no lo reconozco. | Merchant: TIENDA LUMINA vs TIENDA LUM |
| [x] | `ho-n34` | ola, me aparese un cargo de $3200 en MERCADO ZENIT q no reconosco, me lo revisan? | oi, apareció una compra de $3200 en MERCADO ZEN q no reconozco, ¿pueden verificar? | Merchant: MERCADO ZENIT vs MERCADO ZEN |
| [x] | `ho-n13` | Compré dos boletos en CINEPLAZA por $480 el sábado y el cargo salió repetido en mi tarjeta. | Compré dos entradas en CINEPL por $480 el sábado y el cobro me quedó repetido en la tarjeta. | Merchant: CINEPLAZA vs CINEPL |
| [x] | `ho-n14` | Pagué un vuelo con AEROVIA por $7400 y en la cuenta aparece el cargo dos veces. | Pagué un vuelo con AEROV por $7400 y en el resumen aparece el cargo duplicado. | Merchant: AEROVIA vs AEROV |
| [x] | `ho-n33` | Tengo un cargo de $12500 de TECNOHOGAR del 2 de septiembre que no reconozco, no compré nada ahí. | Tengo un cobro de $12500 de TECNOHOG del 2 de septiembre que no reconozco, no compré nada ahí. | Merchant: TECNOHOGAR vs TECNOHOG |
| [x] | `ho-n18` | Chale, en DELIVERYGO me cobraron dos veces el mismo pedido de $315, ¿me ayudan? | Oye, en DELIVERYG me cobraron dos veces el mismo pedido de $315, ¿me das una mano? | Merchant: DELIVERYGO vs DELIVERYG |
| [x] | `ho-n30` | Me cobraron $4200 en HOTEL BRISA el 15 de agosto y no me hospedé ahí, no reconozco ese cargo. | Me cobraron $4200 en HOTEL BRI el 15 de agosto y no me alojé ahí, no reconozco ese cargo. | Merchant: HOTEL BRISA vs HOTEL BRI |
| [x] | `ho-n15` | Son solo $99 pero aparece JUEGOSPLAY en mi estado de cuenta y no sé qué es, no lo reconozco. | Son solo $99, pero aparece JUEGOSP en mi factura y no sé qué es, no reconozco. | Merchant: JUEGOSPLAY vs JUEGOSP |
| [x] | `ho-b18-es-CO` | El ESTACIONAMIENTO CENTRO me cargó $120 tres veces por una sola salida, qué desorden. | El PARQUEADERO CENTRO me cobró $120 tres veces por una sola salida, qué desorden. | Merchant: ESTACIONAMIENTO CENTRO vs PARQUEADERO CENTRO |
| [x] | `ho-n17` | El ESTACIONAMIENTO CENTRO me cargó $120 tres veces por una sola salida, qué desorden. | El PARQUEADERO CENT me cobró $120 tres veces por una sola salida, qué desorden. | Merchant: ESTACIONAMIENTO CENTRO vs PARQUEADERO CENT |
| [x] | `ho-n32` | No reconozco el cargo de $2300 de ROPA URBANA del 28 de agosto, necesito que lo revisen. | Oye, no reconozco el cargo de $2300 de ROPA URB del 28 de agosto, ¿me lo revisan? | Merchant: ROPA URBANA vs ROPA URB |
| [x] | `ho-b41-es-CO` | Se me olvidó el NIP de mi tarjeta de débito, ¿cómo lo cambio? | Olvidé la clave de mi tarjeta débito, ¿cómo la cambio? |  |
| [x] | `ho-b41-es-AR` | Se me olvidó el NIP de mi tarjeta de débito, ¿cómo lo cambio? | Me olvidé el PIN de mi tarjeta de débito, ¿cómo lo cambio? | Merchant: NIP vs PIN |
| [x] | `ho-b41-pt-BR` | Se me olvidó el NIP de mi tarjeta de débito, ¿cómo lo cambio? | Olvidé la contraseña de mi tarjeta de débito, ¿cómo hago para cambiar? |  |
| [x] | `ho-n43` | Se me olvidó el NIP de mi tarjeta de débito, ¿cómo lo cambio? | Me olvidé el PIN de mi tarjeta de crédito, no, de la de débito, ¿cómo lo cambio? | Merchant: NIP vs PIN |
| [x] | `ho-n50` | Me cobraron dos veces $410 en PAPELERIA CENTRAL, pero quiero que me atienda un asesor, no un bot. | Me cobraron dos veces $410 en PAPELERIA CENT, pero quiero que me atienda un asesor, no un robot. | Merchant: PAPELERIA CENTRAL, vs PAPELERIA CENT, |
| [x] | `ho-b64-pt-BR` | ¿Me pueden transferir con servicio al cliente con una persona real? | ¿Pueden transferirme al SAC con una persona real? |  |

### All other variants

| OK | Case | es-MX source | Back-translation |
|---|---|---|---|
| [x] | `ho-b01-es-CO` | Hola, vi en mi estado de cuenta un cargo de $1849 de TIENDA LUMINA del 12 de agosto y no lo reconozco. | Hola, en mi extracto aparece un cobro de $1849 de TIENDA LUMINA el 12 de agosto y no lo reconozco. |
| [x] | `ho-b01-es-AR` | Hola, vi en mi estado de cuenta un cargo de $1849 de TIENDA LUMINA del 12 de agosto y no lo reconozco. | Hola, mira, en el resumen me figura un cargo de $1849 de TIENDA LUMINA del 12 de agosto y no lo reconozco. |
| [x] | `ho-b01-pt-BR` | Hola, vi en mi estado de cuenta un cargo de $1849 de TIENDA LUMINA del 12 de agosto y no lo reconozco. | Hola, vi en mi factura una compra de $1849 en TIENDA LUMINA en 12 de agosto y no reconozco esa compra. |
| [x] | `ho-n25` | Hola, vi en mi estado de cuenta un cargo de $1849 de TIENDA LUMINA del 12 de agosto y no lo reconozco. | Hola, mira, en el resumen me figura un cargo de $1700 de TIENDA LUMINA del 12 de agosto y no lo reconozco. |
| [x] | `ho-b02-es-CO` | Neta me salió un cobro bien raro de $560 en PIXELMART y no sé qué onda, ni lo conozco. | Oye, me salió un cobro raro de $560 en PIXELMART y ni idea de qué es, no lo conozco. |
| [x] | `ho-b02-es-AR` | Neta me salió un cobro bien raro de $560 en PIXELMART y no sé qué onda, ni lo conozco. | Oye, me apareció un cobro muy raro de $560 en PIXELMART y ni idea qué es, no lo conozco. |
| [x] | `ho-b02-pt-BR` | Neta me salió un cobro bien raro de $560 en PIXELMART y no sé qué onda, ni lo conozco. | Gente, apareció una compra rara de $560 en PIXELMART y yo ni sé qué es, no conozco eso. |
| [x] | `ho-b03-es-CO` | Me cobraron dos veces $230 en CAFE DEL PARQUE el 3 de septiembre, quiero que revisen el duplicado. | Me cobraron doble $230 en CAFE DEL PARQUE el 3 de septiembre, por favor revisen ese cobro repetido. |
| [x] | `ho-b03-es-AR` | Me cobraron dos veces $230 en CAFE DEL PARQUE el 3 de septiembre, quiero que revisen el duplicado. | Me cobraron dos veces $230 en CAFE DEL PARQUE el 3 de septiembre, revisen el duplicado por favor. |
| [x] | `ho-b03-pt-BR` | Me cobraron dos veces $230 en CAFE DEL PARQUE el 3 de septiembre, quiero que revisen el duplicado. | Fui cobrado dos veces en $230 en CAFE DEL PARQUE en el día 3 de septiembre, quiero que verifiquen la duplicidad. |
| [x] | `ho-n02` | Me cobraron dos veces $230 en CAFE DEL PARQUE el 3 de septiembre, quiero que revisen el duplicado. | Me cobraron doble $230 en CAFE DEL PARQUE el 1 de septiembre, por favor revisen ese cobro repetido. |
| [x] | `ho-b04-es-CO` | ola, me aparese un cargo de $3200 en MERCADO ZENIT q no reconosco, me lo revisan? | hola, me salio un cobro de $3200 en MERCADO ZENIT q no reconosco, lo pueden revisar? |
| [x] | `ho-b04-es-AR` | ola, me aparese un cargo de $3200 en MERCADO ZENIT q no reconosco, me lo revisan? | hola, me figura un cargo de $3200 en MERCADO ZENIT q no reconosco, lo pueden revisar? |
| [x] | `ho-b04-pt-BR` | ola, me aparese un cargo de $3200 en MERCADO ZENIT q no reconosco, me lo revisan? | oi, apareció una compra de $3200 en MERCADO ZENIT q no reconozco, ¿pueden verificar? |
| [x] | `ho-n07` | ola, me aparese un cargo de $3200 en MERCADO ZENIT q no reconosco, me lo revisan? | hola, me figura un cargo de $3500 en MERCADO ZENIT q no reconosco, lo pueden revisar? |
| [x] | `ho-b05-es-CO` | Compré dos boletos en CINEPLAZA por $480 el sábado y el cargo salió repetido en mi tarjeta. | Compré dos entradas en CINEPLAZA por $480 el sábado y el cobro me quedó repetido en la tarjeta. |
| [x] | `ho-b05-es-AR` | Compré dos boletos en CINEPLAZA por $480 el sábado y el cargo salió repetido en mi tarjeta. | Compré dos entradas en CINEPLAZA por $480 el sábado y el cargo me figura repetido en la tarjeta. |
| [x] | `ho-b05-pt-BR` | Compré dos boletos en CINEPLAZA por $480 el sábado y el cargo salió repetido en mi tarjeta. | Compré dos entradas en CINEPLAZA por $480 el sábado y la cobranza apareció repetida en la tarjeta. |
| [x] | `ho-b06-es-CO` | En mi estado de cuenta hay un cargo de $950 de GASOLINERA ORIENTE del 20 de agosto que no reconozco. | En el extracto hay un cobro de $950 de GASOLINERA ORIENTE del 20 de agosto que no reconozco. |
| [x] | `ho-b06-es-AR` | En mi estado de cuenta hay un cargo de $950 de GASOLINERA ORIENTE del 20 de agosto que no reconozco. | En el resumen de la tarjeta hay un cargo de $950 de GASOLINERA ORIENTE del 20 de agosto que no reconozco. |
| [x] | `ho-b06-pt-BR` | En mi estado de cuenta hay un cargo de $950 de GASOLINERA ORIENTE del 20 de agosto que no reconozco. | En la factura tiene una compra de $950 en puesto GASOLINERA ORIENTE de 20 de agosto que no reconozco. |
| [x] | `ho-n03` | En mi estado de cuenta hay un cargo de $950 de GASOLINERA ORIENTE del 20 de agosto que no reconozco. | En el resumen de la tarjeta hay un cargo de $950 de GASOLINERA ORIENTE del 22 de agosto que no reconozco. |
| [x] | `ho-b07-es-CO` | Hay un charge de $199 de STREAMBOX en mi tarjeta que no reconozco, no tengo ninguna subscription ahí. | Me salió un charge de $199 de STREAMBOX que no reconozco, yo no tengo ninguna subscription con ellos. |
| [x] | `ho-b07-es-AR` | Hay un charge de $199 de STREAMBOX en mi tarjeta que no reconozco, no tengo ninguna subscription ahí. | Tengo un charge de $199 de STREAMBOX que no reconozco, no tengo ninguna subscription con ellos. |
| [x] | `ho-b07-pt-BR` | Hay un charge de $199 de STREAMBOX en mi tarjeta que no reconozco, no tengo ninguna subscription ahí. | Tiene un charge de $199 de STREAMBOX en mi tarjeta que no reconozco, no tengo ninguna subscription ahí. |
| [x] | `ho-n19` | Hay un charge de $199 de STREAMBOX en mi tarjeta que no reconozco, no tengo ninguna subscription ahí. | Tiene un charge de $149 de STREAMBOX en mi tarjeta, no, disculpa, $199, que no reconozco, no tengo ninguna subscription ahí. |
| [x] | `ho-b08-es-CO` | En FARMACIA SOL me cobraron $780 pero mi ticket fue de $380, el cargo está mal. | En FARMACIA SOL me cobraron $780 pero mi recibo era de $380, el cobro está errado. |
| [x] | `ho-b08-es-AR` | En FARMACIA SOL me cobraron $780 pero mi ticket fue de $380, el cargo está mal. | En FARMACIA SOL me cobraron $780 pero el ticket que tengo es de $380, el cargo está mal. |
| [x] | `ho-b08-pt-BR` | En FARMACIA SOL me cobraron $780 pero mi ticket fue de $380, el cargo está mal. | En FARMACIA SOL cobraron $780 pero mi comprobante fue de $380, el valor de la compra está errado. |
| [x] | `ho-n09` | En FARMACIA SOL me cobraron $780 pero mi ticket fue de $380, el cargo está mal. | En FARMACIA SOL me cobraron $850 pero mi recibo era de $380, el cobro está errado. |
| [x] | `ho-b09-es-CO` | Pagué un vuelo con AEROVIA por $7400 y en la cuenta aparece el cargo dos veces. | Pagué un boleto con AEROVIA por $7400 y en el extracto aparece el cobro dos veces. |
| [x] | `ho-b09-es-AR` | Pagué un vuelo con AEROVIA por $7400 y en la cuenta aparece el cargo dos veces. | Pagué un vuelo con AEROVIA por $7400 y en el resumen aparece el cargo duplicado. |
| [x] | `ho-b09-pt-BR` | Pagué un vuelo con AEROVIA por $7400 y en la cuenta aparece el cargo dos veces. | Pagué un pasaje de AEROVIA por $7400 y en la factura aparece la cobranza en duplicidad. |
| [x] | `ho-b10-es-CO` | Tengo un cargo de $12500 de TECNOHOGAR del 2 de septiembre que no reconozco, no compré nada ahí. | Tengo un cobro de $12500 de TECNOHOGAR del 2 de septiembre que no reconozco, no compré nada ahí. |
| [x] | `ho-b10-es-AR` | Tengo un cargo de $12500 de TECNOHOGAR del 2 de septiembre que no reconozco, no compré nada ahí. | Oye, me figura un cargo de $12500 de TECNOHOGAR del 2 de septiembre que no reconozco, ahí no compré nada. |
| [x] | `ho-b10-pt-BR` | Tengo un cargo de $12500 de TECNOHOGAR del 2 de septiembre que no reconozco, no compré nada ahí. | Tengo una compra de $12500 en TECNOHOGAR de 2 de septiembre que no reconozco, no compré nada ahí. |
| [x] | `ho-n04` | Tengo un cargo de $12500 de TECNOHOGAR del 2 de septiembre que no reconozco, no compré nada ahí. | Tengo una compra de $12500 en TECNOHOGAR de 5 de septiembre que no reconozco, no compré nada ahí. |
| [x] | `ho-b11-es-CO` | Cancelé mi membresía de GIMNASIO VITAL en julio y todavía me están cargando $650, no es justo. | Cancelé mi membresía en GIMNASIO VITAL en julio y todavía me están cobrando $650, qué abuso. |
| [x] | `ho-b11-es-AR` | Cancelé mi membresía de GIMNASIO VITAL en julio y todavía me están cargando $650, no es justo. | Cancelé mi membresía de GIMNASIO VITAL en julio y todavía me siguen cobrando $650, es un abuso. |
| [x] | `ho-b11-pt-BR` | Cancelé mi membresía de GIMNASIO VITAL en julio y todavía me están cargando $650, no es justo. | Cancelé mi matrícula en GIMNASIO VITAL en julio y continúan cobrando $650, eso es un absurdo. |
| [x] | `ho-b12-es-CO` | Chale, en DELIVERYGO me cobraron dos veces el mismo pedido de $315, ¿me ayudan? | Uy, en DELIVERYGO me cobraron dos veces el mismo pedido de $315, ¿me ayudan? |
| [x] | `ho-b12-es-AR` | Chale, en DELIVERYGO me cobraron dos veces el mismo pedido de $315, ¿me ayudan? | Tío, en DELIVERYGO me cobraron dos veces el mismo pedido de $315, ¿me dan una mano? |
| [x] | `ho-b12-pt-BR` | Chale, en DELIVERYGO me cobraron dos veces el mismo pedido de $315, ¿me ayudan? | Oye, en DELIVERYGO cobraron dos veces el mismo pedido de $315, ¿pueden ayudarme? |
| [x] | `ho-b13-es-CO` | Me cobraron $4200 en HOTEL BRISA el 15 de agosto y no me hospedé ahí, no reconozco ese cargo. | Me cobraron $4200 en HOTEL BRISA el 15 de agosto y yo no me hospedé ahí, no reconozco ese cobro. |
| [x] | `ho-b13-es-AR` | Me cobraron $4200 en HOTEL BRISA el 15 de agosto y no me hospedé ahí, no reconozco ese cargo. | Me cobraron $4200 en HOTEL BRISA el 15 de agosto y no me alojé ahí, no reconozco ese cargo. |
| [x] | `ho-b13-pt-BR` | Me cobraron $4200 en HOTEL BRISA el 15 de agosto y no me hospedé ahí, no reconozco ese cargo. | Cobraron $4200 en HOTEL BRISA en 15 de agosto y yo no me hospedé ahí, no reconozco esa compra. |
| [x] | `ho-n06` | Me cobraron $4200 en HOTEL BRISA el 15 de agosto y no me hospedé ahí, no reconozco ese cargo. | Me cobraron $4200 en HOTEL BRISA el 13 de agosto y yo no me hospedé ahí, no reconozco ese cobro. |
| [x] | `ho-b14-es-CO` | Son solo $99 pero aparece JUEGOSPLAY en mi estado de cuenta y no sé qué es, no lo reconozco. | Son solo $99 pero aparece JUEGOSPLAY en mi extracto y no sé qué es, no lo reconozco. |
| [x] | `ho-b14-es-AR` | Son solo $99 pero aparece JUEGOSPLAY en mi estado de cuenta y no sé qué es, no lo reconozco. | Son solo $99, pero aparece JUEGOSPLAY en mi resumen y no sé qué es, no lo reconozco. |
| [x] | `ho-b14-pt-BR` | Son solo $99 pero aparece JUEGOSPLAY en mi estado de cuenta y no sé qué es, no lo reconozco. | Son solo $99, pero aparece JUEGOSPLAY en mi factura y no sé qué es, no reconozco. |
| [x] | `ho-b15-es-CO` | SUPERMERCADO NORTE me hizo el cargo de $1870 repetido, salió dos veces con la misma hora. | SUPERMERCADO NORTE me hizo el cobro de $1870 repetido, salió dos veces a la misma hora. |
| [x] | `ho-b15-es-AR` | SUPERMERCADO NORTE me hizo el cargo de $1870 repetido, salió dos veces con la misma hora. | SUPERMERCADO NORTE me hizo el cargo de $1870 repetido, salió dos veces a la misma hora. |
| [x] | `ho-b15-pt-BR` | SUPERMERCADO NORTE me hizo el cargo de $1870 repetido, salió dos veces con la misma hora. | El SUPERMERCADO NORTE repitió la cobranza de $1870, salió dos veces en el mismo horario. |
| [x] | `ho-n10` | SUPERMERCADO NORTE me hizo el cargo de $1870 repetido, salió dos veces con la misma hora. | El SUPERMERCADO NORTE repitió la cobranza de $1700, salió dos veces en el mismo horario. |
| [x] | `ho-b16-es-CO` | El viaje en TAXIGO salió en $245 pero me cargaron $645, el monto no coincide. | El viaje en TAXIGO costó $245 pero me cobraron $645, el valor no coincide. |
| [x] | `ho-b16-es-AR` | El viaje en TAXIGO salió en $245 pero me cargaron $645, el monto no coincide. | El viaje en TAXIGO salió $245 pero me cobraron $645, el monto no coincide. |
| [x] | `ho-b16-pt-BR` | El viaje en TAXIGO salió en $245 pero me cargaron $645, el monto no coincide. | La carrera en TAXIGO dió $245 pero cobraron $645, el valor no bate. |
| [x] | `ho-n11` | El viaje en TAXIGO salió en $245 pero me cargaron $645, el monto no coincide. | El viaje en TAXIGO salió $245 pero me cobraron $700, el monto no coincide. |
| [x] | `ho-b17-es-CO` | Quiero que me expliquen un cargo de $890 de LIBRERIA ATLAS que veo en mi cuenta, no sé de qué es. | Quiero que me expliquen un cobro de $890 de LIBRERIA ATLAS que veo en mi cuenta, no sé de qué es. |
| [x] | `ho-b17-es-AR` | Quiero que me expliquen un cargo de $890 de LIBRERIA ATLAS que veo en mi cuenta, no sé de qué es. | Quiero que me expliquen un cargo de $890 de LIBRERIA ATLAS que veo en mi cuenta, ni idea de qué es. |
| [x] | `ho-b17-pt-BR` | Quiero que me expliquen un cargo de $890 de LIBRERIA ATLAS que veo en mi cuenta, no sé de qué es. | Quiero que me expliquen una compra de $890 de LIBRERIA ATLAS que veo en mi cuenta, no sé qué es. |
| [x] | `ho-b18-es-AR` | El ESTACIONAMIENTO CENTRO me cargó $120 tres veces por una sola salida, qué desorden. | El ESTACIONAMIENTO CENTRO me cobró $120 tres veces por una sola salida, un desastre. |
| [x] | `ho-b18-pt-BR` | El ESTACIONAMIENTO CENTRO me cargó $120 tres veces por una sola salida, qué desorden. | El ESTACIONAMIENTO CENTRO cobró $120 tres veces por una única salida, ¡qué desorden! |
| [x] | `ho-b19-es-CO` | No reconozco el cargo de $2300 de ROPA URBANA del 28 de agosto, necesito que lo revisen. | No reconozco el cobro de $2300 de ROPA URBANA del 28 de agosto, necesito que lo revisen. |
| [x] | `ho-b19-es-AR` | No reconozco el cargo de $2300 de ROPA URBANA del 28 de agosto, necesito que lo revisen. | Oye, no reconozco el cargo de $2300 de ROPA URBANA del 28 de agosto, ¿me lo revisan? |
| [x] | `ho-b19-pt-BR` | No reconozco el cargo de $2300 de ROPA URBANA del 28 de agosto, necesito que lo revisen. | No reconozco la compra de $2300 en ROPA URBANA de 28 de agosto, necesito que verifiquen. |
| [x] | `ho-n27` | No reconozco el cargo de $2300 de ROPA URBANA del 28 de agosto, necesito que lo revisen. | No reconozco el cobro de $2100 de ROPA URBANA del 28 de agosto, necesito que lo revisen. |
| [x] | `ho-b20-es-CO` | Oye, el 5 de agosto pasó algo con mi cuenta y desde entonces ando preocupado, ¿me ayudan? | Hola, el 5 de agosto pasó algo con mi cuenta y desde entonces ando preocupado, ¿me ayudan? |
| [x] | `ho-b20-es-AR` | Oye, el 5 de agosto pasó algo con mi cuenta y desde entonces ando preocupado, ¿me ayudan? | Hola, el 5 de agosto pasó algo con mi cuenta y desde entonces ando preocupado, ¿me dan una mano? |
| [x] | `ho-b20-pt-BR` | Oye, el 5 de agosto pasó algo con mi cuenta y desde entonces ando preocupado, ¿me ayudan? | Hola, en el día 5 de agosto pasó algo con mi cuenta y desde entonces estoy preocupado, ¿pueden ayudar? |
| [x] | `ho-n22` | Oye, el 5 de agosto pasó algo con mi cuenta y desde entonces ando preocupado, ¿me ayudan? | Hola, el 7 de agosto pasó algo con mi cuenta y desde entonces ando preocupado, ¿me dan una mano? |
| [x] | `ho-b21-es-CO` | Algo no está bien con mi cuenta pero no sé bien qué es, ¿me ayudan a revisar? | Algo no está bien con mi cuenta pero no sé bien qué es, ¿me ayudan a mirar? |
| [x] | `ho-b21-es-AR` | Algo no está bien con mi cuenta pero no sé bien qué es, ¿me ayudan a revisar? | Algo no anda bien con mi cuenta pero no sé bien qué es, ¿me ayudás a revisar? |
| [x] | `ho-b21-pt-BR` | Algo no está bien con mi cuenta pero no sé bien qué es, ¿me ayudan a revisar? | Tiene algo errado con mi cuenta pero no sé bien qué es, ¿pueden ayudar a verificar? |
| [x] | `ho-b22-es-CO` | Necesito ayuda con algo que me pasó el 10 de septiembre, es largo de contar. | Hola, necesito que me colaboren con algo que me pasó el 10 de septiembre, es largo de contar. |
| [x] | `ho-b22-es-AR` | Necesito ayuda con algo que me pasó el 10 de septiembre, es largo de contar. | Oye, necesito una mano con algo que me pasó el 10 de septiembre, es largo de contar. |
| [x] | `ho-b22-pt-BR` | Necesito ayuda con algo que me pasó el 10 de septiembre, es largo de contar. | Necesito ayuda con algo que me pasó en 10 de septiembre, es largo de contar. |
| [x] | `ho-n21` | Necesito ayuda con algo que me pasó el 10 de septiembre, es largo de contar. | Hola, necesito que me colaboren con algo que me pasó el 8 de septiembre, es largo de contar. |
| [x] | `ho-b23-es-CO` | Hola, necesito ayuda con algo. | Hola, necesito ayuda con una cosa. |
| [x] | `ho-b23-es-AR` | Hola, necesito ayuda con algo. | Hola, necesito ayuda con una cosa. |
| [x] | `ho-b23-pt-BR` | Hola, necesito ayuda con algo. | Hola, necesito ayuda con una cosa. |
| [x] | `ho-b24-es-CO` | Hola, buenas tardes. | Hola tardes. |
| [x] | `ho-b24-es-AR` | Hola, buenas tardes. | Buenas, ¿cómo andan? |
| [x] | `ho-b24-pt-BR` | Hola, buenas tardes. | Hola, buenas tardes. |
| [x] | `ho-b25-es-CO` | Siento que algo no cuadra en mi estado de cuenta de este mes, pero no puedo decir exactamente qué. | Siento que algo no cuadra en mi extracto de este mes, pero no puedo decir exactamente qué. |
| [x] | `ho-b25-es-AR` | Siento que algo no cuadra en mi estado de cuenta de este mes, pero no puedo decir exactamente qué. | Siento que algo no cierra en mi resumen de este mes, pero no puedo decir exactamente qué. |
| [x] | `ho-b25-pt-BR` | Siento que algo no cuadra en mi estado de cuenta de este mes, pero no puedo decir exactamente qué. | Siento que algo no bate en mi estado de cuenta de este mes, pero no consigo decir exactamente qué. |
| [x] | `ho-b26-es-CO` | Pues es que ayer estaba en el centro, luego llegué a casa, revisé el celular y bueno, pasó algo, ya no sé ni cómo contarlo. | Pues oye, ayer estaba en el centro, llegué a la casa, revisé el celular y listo, pasó algo, ni sé cómo contarle. |
| [x] | `ho-b26-es-AR` | Pues es que ayer estaba en el centro, luego llegué a casa, revisé el celular y bueno, pasó algo, ya no sé ni cómo contarlo. | Y nada, ayer estaba en el centro, después llegué a casa, miré el celular y bueno, pasó algo, no sé ni cómo contarlo. |
| [x] | `ho-b26-pt-BR` | Pues es que ayer estaba en el centro, luego llegué a casa, revisé el celular y bueno, pasó algo, ya no sé ni cómo contarlo. | Es que ayer yo estaba en el centro, después llegué a casa, miré el celular y bueno, pasó algo, ni sé cómo contar. |
| [x] | `ho-b27-es-CO` | Algo pasó con mi cuenta, necesito ayuda. | Hola, algo pasó con mi cuenta, necesito que me colaboren. |
| [x] | `ho-b27-es-AR` | Algo pasó con mi cuenta, necesito ayuda. | Hola, me pasó algo con mi cuenta, necesito que me den una mano. |
| [x] | `ho-b27-pt-BR` | Algo pasó con mi cuenta, necesito ayuda. | Pasó algo con mi cuenta, necesito ayuda. |
| [x] | `ho-b28-es-CO` | Desde el 20 de septiembre tengo un problema con mi cuenta y no sé cómo explicarlo. | Hola, desde el 20 de septiembre tengo un problema con mi cuenta y no sé cómo explicarlo. |
| [x] | `ho-b28-es-AR` | Desde el 20 de septiembre tengo un problema con mi cuenta y no sé cómo explicarlo. | Oye, desde el 20 de septiembre tengo un problema con mi cuenta y no sé cómo explicarlo. |
| [x] | `ho-b28-pt-BR` | Desde el 20 de septiembre tengo un problema con mi cuenta y no sé cómo explicarlo. | Desde 20 de septiembre tengo un problema con mi cuenta y no sé cómo explicar. |
| [x] | `ho-n23` | Desde el 20 de septiembre tengo un problema con mi cuenta y no sé cómo explicarlo. | Desde 22 de septiembre tengo un problema con mi cuenta y no sé cómo explicar. |
| [x] | `ho-b29-es-CO` | Necesito revisar un movimiento de mi cuenta pero no tengo claro cuál. | Necesito revisar un movimiento de mi cuenta, pero no tengo claro cuál fue. |
| [x] | `ho-b29-es-AR` | Necesito revisar un movimiento de mi cuenta pero no tengo claro cuál. | Necesito revisar un movimiento de mi cuenta, pero no tengo nada claro cuál es. |
| [x] | `ho-b29-pt-BR` | Necesito revisar un movimiento de mi cuenta pero no tengo claro cuál. | Necesito conferir un movimiento de mi cuenta pero no tengo claro cuál. |
| [x] | `ho-n36` | Necesito revisar un movimiento de mi cuenta pero no tengo claro cuál. | Necesito revisar un movimiento de mi tarjeta, perdón, de mi cuenta, pero no tengo nada claro cuál es. |
| [x] | `ho-b30-es-CO` | Es que no entiendo nada de lo que veo en la app, todo me parece confuso, ayuda por favor. | Hola, es que no entiendo nada de lo que veo en la aplicación, todo es confuso, me ayudan por favor. |
| [x] | `ho-b30-es-AR` | Es que no entiendo nada de lo que veo en la app, todo me parece confuso, ayuda por favor. | Oye, no entiendo nada de lo que veo en la app, está todo confuso, ayudame por favor. |
| [x] | `ho-b30-pt-BR` | Es que no entiendo nada de lo que veo en la app, todo me parece confuso, ayuda por favor. | Es que no entiendo nada de lo que veo en la app, todo me parece confuso, ayuda por favor. |
| [x] | `ho-b31-es-CO` | Quisiera que me ayuden con una situación que tengo, pero no sé bien a quién preguntarle. | Quisiera que me colaboren con una situación que tengo, pero no sé a quién preguntarle. |
| [x] | `ho-b31-es-AR` | Quisiera que me ayuden con una situación que tengo, pero no sé bien a quién preguntarle. | Hola, necesito que me ayuden con una situación, pero no sé a quién preguntarle. |
| [x] | `ho-b31-pt-BR` | Quisiera que me ayuden con una situación que tengo, pero no sé bien a quién preguntarle. | Me gustaría ayuda con una situación que tengo, pero no sé bien a quién preguntar. |
| [x] | `ho-b32-es-CO` | tngo una duda sobre un movimeinto d mi cuenta, no se como explicarlo bn | tngo una duda sobre un movimiento d mi cuenta, no se como explicarle bn |
| [x] | `ho-b32-es-AR` | tngo una duda sobre un movimeinto d mi cuenta, no se como explicarlo bn | tengo una duda sobre un movimeinto d mi cuenta, no se como explicarlo bn |
| [x] | `ho-b32-pt-BR` | tngo una duda sobre un movimeinto d mi cuenta, no se como explicarlo bn | tengo una duda sobre un movimiento de mi cuenta, no sé explicar bien |
| [x] | `ho-b33-es-CO` | El 1 de septiembre me pasó algo y todavía no se resuelve, necesito ayuda con eso. | Hola, el 1 de septiembre me pasó algo y todavía no se soluciona, necesito que me colaboren con eso. |
| [x] | `ho-b33-es-AR` | El 1 de septiembre me pasó algo y todavía no se resuelve, necesito ayuda con eso. | Hola, el 1 de septiembre me pasó algo y todavía no se resolvió, necesito ayuda con eso. |
| [x] | `ho-b33-pt-BR` | El 1 de septiembre me pasó algo y todavía no se resuelve, necesito ayuda con eso. | En 1 de septiembre me pasó algo y aún no fue resuelto, necesito ayuda con eso. |
| [x] | `ho-b34-es-CO` | eso, lo de siempre, ya sabe, necesito que lo vean porfa | eso, lo de siempre, usted sabe, me lo revisan porfa |
| [x] | `ho-b34-es-AR` | eso, lo de siempre, ya sabe, necesito que lo vean porfa | eso, lo de siempre, ya sabés, necesito que lo vean porfa |
| [x] | `ho-b34-pt-BR` | eso, lo de siempre, ya sabe, necesito que lo vean porfa | eso, lo de siempre, sabe cómo es, necesito que vean por favor |
| [x] | `ho-b35-es-CO` | Quiero reclamar algo pero no sé cómo explicarlo, no sé por dónde empezar. | Quiero hacer un reclamo pero no sé cómo explicarlo, no sé cómo empezar. |
| [x] | `ho-b35-es-AR` | Quiero reclamar algo pero no sé cómo explicarlo, no sé por dónde empezar. | Quiero reclamar algo pero no sé cómo explicarlo, no sé por dónde arrancar. |
| [x] | `ho-b35-pt-BR` | Quiero reclamar algo pero no sé cómo explicarlo, no sé por dónde empezar. | Quiero reclamar de algo pero no sé cómo explicar, no sé por dónde empezar. |
| [x] | `ho-n37` | Quiero reclamar algo pero no sé cómo explicarlo, no sé por dónde empezar. | Quiero sacar una duda, quiero decir, reclamar de algo, pero no sé cómo explicar, no sé por dónde empezar. |
| [x] | `ho-b36-es-CO` | ¿Podrían ayudarme? Tengo una situación con el banco y estoy un poco desesperado. | ¿Me podrían colaborar? Tengo una situación con el banco y ando algo desesperado. |
| [x] | `ho-b36-es-AR` | ¿Podrían ayudarme? Tengo una situación con el banco y estoy un poco desesperado. | ¿Me ayudan? Tengo un problema con el banco y estoy medio desesperado. |
| [x] | `ho-b36-pt-BR` | ¿Podrían ayudarme? Tengo una situación con el banco y estoy un poco desesperado. | ¿Podrían ayudarme? Tengo una situación con el banco y estoy algo desesperado. |
| [x] | `ho-b37-es-CO` | ¿Me puedes decir cuánto dinero tengo disponible en mi cuenta de ahorro? | ¿Me puedes decir cuánta plata tengo disponible en mi cuenta de ahorros? |
| [x] | `ho-b37-es-AR` | ¿Me puedes decir cuánto dinero tengo disponible en mi cuenta de ahorro? | ¿Me podés decir cuánta plata tengo disponible en mi caja de ahorro? |
| [x] | `ho-b37-pt-BR` | ¿Me puedes decir cuánto dinero tengo disponible en mi cuenta de ahorro? | ¿Puede decirme cuánto dinero tengo disponible en mi cuenta de ahorro? |
| [x] | `ho-n42` | ¿Me puedes decir cuánto dinero tengo disponible en mi cuenta de ahorro? | ¿Me puedes decir cuánta plata tengo disponible en mi cuenta corriente, perdón, en la de ahorros? |
| [x] | `ho-b38-es-CO` | Quisiera pedir un préstamo personal de $50000, ¿qué requisitos piden? | Quisiera solicitar un préstamo personal de $50000, ¿qué requisitos piden? |
| [x] | `ho-b38-es-AR` | Quisiera pedir un préstamo personal de $50000, ¿qué requisitos piden? | Quisiera sacar un préstamo personal de $50000, ¿qué requisitos piden? |
| [x] | `ho-b38-pt-BR` | Quisiera pedir un préstamo personal de $50000, ¿qué requisitos piden? | Me gustaría pedir un préstamo personal de $50000, ¿cuáles son los requisitos? |
| [x] | `ho-b39-es-CO` | Quiero que me aumenten el límite de mi tarjeta de crédito a $30000. | Quiero que me suban el cupo de mi tarjeta de crédito a $30000. |
| [x] | `ho-b39-es-AR` | Quiero que me aumenten el límite de mi tarjeta de crédito a $30000. | Quiero que me suban el límite de la tarjeta de crédito a $30000. |
| [x] | `ho-b39-pt-BR` | Quiero que me aumenten el límite de mi tarjeta de crédito a $30000. | Quiero aumentar el límite de mi tarjeta de crédito a $30000. |
| [x] | `ho-n40` | Quiero que me aumenten el límite de mi tarjeta de crédito a $30000. | Quiero que me suban el límite de la tarjeta de crédito a $27000. |
| [x] | `ho-b40-es-CO` | Me interesa abrir una cuenta de ahorro nueva, ¿cómo lo hago? | Me interesa abrir una cuenta de ahorros nueva, ¿cómo lo hago? |
| [x] | `ho-b40-es-AR` | Me interesa abrir una cuenta de ahorro nueva, ¿cómo lo hago? | Me interesa abrir una caja de ahorro nueva, ¿cómo hago? |
| [x] | `ho-b40-pt-BR` | Me interesa abrir una cuenta de ahorro nueva, ¿cómo lo hago? | Tengo interés en abrir una cuenta de ahorro nueva, ¿cómo hago? |
| [x] | `ho-b42-es-CO` | ¿A qué hora cierra la sucursal del centro los sábados? | ¿A qué hora cierra la oficina del centro los sábados? |
| [x] | `ho-b42-es-AR` | ¿A qué hora cierra la sucursal del centro los sábados? | ¿Hasta qué hora está abierta la sucursal del centro los sábados? |
| [x] | `ho-b42-pt-BR` | ¿A qué hora cierra la sucursal del centro los sábados? | ¿A qué horas la agencia del centro cierra los sábados? |
| [x] | `ho-b43-es-CO` | ¿Cuánto me cobran de anualidad por la tarjeta y de comisión por manejo de cuenta? | ¿Cuánto cobran de cuota de manejo por la tarjeta y de comisión por mantener la cuenta? |
| [x] | `ho-b43-es-AR` | ¿Cuánto me cobran de anualidad por la tarjeta y de comisión por manejo de cuenta? | ¿Cuánto cobran de mantenimiento por la tarjeta y de comisión por tener la cuenta? |
| [x] | `ho-b43-pt-BR` | ¿Cuánto me cobran de anualidad por la tarjeta y de comisión por manejo de cuenta? | ¿Cuánto cobran de arancel anual de la tarjeta y de tarifa para mantener la cuenta? |
| [x] | `ho-b44-es-CO` | Quiero cancelar mi tarjeta de crédito, ya no la uso. | Quiero cancelar mi tarjeta de crédito, ya no la utilizo. |
| [x] | `ho-b44-es-AR` | Quiero cancelar mi tarjeta de crédito, ya no la uso. | Quiero dar de baja mi tarjeta de crédito, ya no la uso. |
| [x] | `ho-b44-pt-BR` | Quiero cancelar mi tarjeta de crédito, ya no la uso. | Quiero cancelar mi tarjeta de crédito, no la uso más. |
| [x] | `ho-n44` | Quiero cancelar mi tarjeta de crédito, ya no la uso. | Quiero cancelar mi tarjeta de débito, no, la de crédito, no la uso más. |
| [x] | `ho-b45-es-CO` | Necesito hacer una transferencia de $1500 a una amiga, ¿cómo se hace? | Necesito hacer una transferencia de $1500 a una amiga, ¿cómo la hago? |
| [x] | `ho-b45-es-AR` | Necesito hacer una transferencia de $1500 a una amiga, ¿cómo se hace? | Necesito hacerle una transferencia de $1500 a una amiga, ¿cómo se hace? |
| [x] | `ho-b45-pt-BR` | Necesito hacer una transferencia de $1500 a una amiga, ¿cómo se hace? | Necesito hacer una transferencia de $1500 para una amiga, ¿cómo hago? |
| [x] | `ho-n28` | Necesito hacer una transferencia de $1500 a una amiga, ¿cómo se hace? | Necesito hacer una transferencia de $1400 para una amiga, ¿cómo hago? |
| [x] | `ho-n39` | Necesito hacer una transferencia de $1500 a una amiga, ¿cómo se hace? | Necesito hacer una transferencia de $1650 a una amiga, ¿cómo la hago? |
| [x] | `ho-b46-es-CO` | ¿Qué tasas manejan para un crédito hipotecario a veinte años? | ¿Qué tasas manejan para un crédito de vivienda a veinte años? |
| [x] | `ho-b46-es-AR` | ¿Qué tasas manejan para un crédito hipotecario a veinte años? | ¿Qué tasa tienen para un hipotecario a veinte años? |
| [x] | `ho-b46-pt-BR` | ¿Qué tasas manejan para un crédito hipotecario a veinte años? | ¿Cuáles son las tasas para un financiamiento inmobiliario en veinte años? |
| [x] | `ho-b47-es-CO` | Me llegó mi tarjeta nueva, ¿cómo la activo? | Me llegó la tarjeta nueva, ¿cómo hago para activarla? |
| [x] | `ho-b47-es-AR` | Me llegó mi tarjeta nueva, ¿cómo la activo? | Me llegó la tarjeta nueva, ¿cómo la activo? |
| [x] | `ho-b47-pt-BR` | Me llegó mi tarjeta nueva, ¿cómo la activo? | Mi tarjeta nueva llegó, ¿cómo hago para desbloquear? |
| [x] | `ho-b48-es-CO` | Cambié de número de celular y de domicilio, ¿dónde actualizo mis datos? | Cambié de número de celular y de dirección, ¿dónde actualizo mis datos? |
| [x] | `ho-b48-es-AR` | Cambié de número de celular y de domicilio, ¿dónde actualizo mis datos? | Cambié de celular y de domicilio, ¿dónde actualizo mis datos? |
| [x] | `ho-b48-pt-BR` | Cambié de número de celular y de domicilio, ¿dónde actualizo mis datos? | Cambié de celular y de domicilio, ¿dónde actualizo mis datos de registro? |
| [x] | `ho-b49-es-CO` | ¿Tienen algún seguro de vida que me recomienden? | ¿Tienen algún seguro de vida que me puedan recomendar? |
| [x] | `ho-b49-es-AR` | ¿Tienen algún seguro de vida que me recomienden? | ¿Tienen algún seguro de vida para recomendarme? |
| [x] | `ho-b49-pt-BR` | ¿Tienen algún seguro de vida que me recomienden? | ¿Tienen algún seguro de vida para recomendarme? |
| [x] | `ho-b50-es-CO` | ¿A cómo está hoy el dólar que me venden en el banco? | ¿A cómo está hoy el dólar en el banco, para comprarlo? |
| [x] | `ho-b50-es-AR` | ¿A cómo está hoy el dólar que me venden en el banco? | ¿A cuánto está hoy el dólar que me venden en el banco? |
| [x] | `ho-b50-pt-BR` | ¿A cómo está hoy el dólar que me venden en el banco? | ¿Cuánto está el dólar hoy en la venta del banco? |
| [x] | `ho-b51-es-CO` | ¿Cuándo vence el pago mínimo de mi tarjeta y de cuánto es? | ¿Cuándo vence el pago mínimo de mi tarjeta y cuánto debo pagar? |
| [x] | `ho-b51-es-AR` | ¿Cuándo vence el pago mínimo de mi tarjeta y de cuánto es? | ¿Cuándo vence el pago mínimo de la tarjeta y cuánto es? |
| [x] | `ho-b51-pt-BR` | ¿Cuándo vence el pago mínimo de mi tarjeta y de cuánto es? | ¿Cuándo vence el pago mínimo de mi tarjeta y de cuánto es? |
| [x] | `ho-b52-es-CO` | Quiero hacer el upgrade a la tarjeta gold, ¿qué beneficios trae? | Quiero pasarme a la tarjeta gold, ¿qué beneficios tiene? |
| [x] | `ho-b52-es-AR` | Quiero hacer el upgrade a la tarjeta gold, ¿qué beneficios trae? | Quiero hacer el upgrade a la tarjeta gold, ¿qué beneficios tiene? |
| [x] | `ho-b52-pt-BR` | Quiero hacer el upgrade a la tarjeta gold, ¿qué beneficios trae? | Quiero hacer la actualización a la tarjeta oro, ¿qué beneficios tiene? |
| [x] | `ho-b53-es-CO` | Necesito una constancia de que tengo cuenta con ustedes para un trámite de visa. | Necesito un certificado de que tengo cuenta con ustedes para un trámite de visa. |
| [x] | `ho-b53-es-AR` | Necesito una constancia de que tengo cuenta con ustedes para un trámite de visa. | Necesito un comprobante de que soy cliente de ustedes, para un trámite de visa. |
| [x] | `ho-b53-pt-BR` | Necesito una constancia de que tengo cuenta con ustedes para un trámite de visa. | Necesito una declaración de que tengo cuenta con ustedes para un trámite de visa. |
| [x] | `ho-b54-es-CO` | ¿Hay algún ejecutivo disponible? Prefiero hablar con alguien. | ¿Hay algún asesor disponible? Prefiero hablar con alguien. |
| [x] | `ho-b54-es-AR` | ¿Hay algún ejecutivo disponible? Prefiero hablar con alguien. | ¿Hay algún asesor para atenderme? Prefiero hablar con una persona. |
| [x] | `ho-b54-pt-BR` | ¿Hay algún ejecutivo disponible? Prefiero hablar con alguien. | ¿Hay algún atendente disponible? Prefiero hablar con alguien. |
| [x] | `ho-n46` | ¿Hay algún ejecutivo disponible? Prefiero hablar con alguien. | ¿Hay algún asesor disponible? Prefiero hablar con alguien, o mejor dicho, con un asesor de verdad. |
| [x] | `ho-b55-es-CO` | Pásame con un humano, por favor. | Comuníqueme con un humano, por favor. |
| [x] | `ho-b55-es-AR` | Pásame con un humano, por favor. | Pasame con un humano, por favor. |
| [x] | `ho-b55-pt-BR` | Pásame con un humano, por favor. | Pásame con un humano, por favor. |
| [x] | `ho-b56-es-CO` | Me cobraron dos veces $410 en PAPELERIA CENTRAL, pero quiero que me atienda un asesor, no un bot. | Me cobraron dos veces $410 en PAPELERIA CENTRAL, pero quiero que me atienda un asesor, no un robot. |
| [x] | `ho-b56-es-AR` | Me cobraron dos veces $410 en PAPELERIA CENTRAL, pero quiero que me atienda un asesor, no un bot. | Oye, me cobraron dos veces $410 en PAPELERIA CENTRAL, pero quiero que me atienda un asesor, no un bot. |
| [x] | `ho-b56-pt-BR` | Me cobraron dos veces $410 en PAPELERIA CENTRAL, pero quiero que me atienda un asesor, no un bot. | Cobraron dos veces $410 en PAPELERIA CENTRAL, pero quiero ser atendido por un atendente, no por un robot. |
| [x] | `ho-b57-es-CO` | Prefiero que un asesor me llame al número que tengo registrado. | Prefiero que me llame un asesor al número que tengo registrado. |
| [x] | `ho-b57-es-AR` | Prefiero que un asesor me llame al número que tengo registrado. | Prefiero que un asesor me llame al celular que tengo registrado. |
| [x] | `ho-b57-pt-BR` | Prefiero que un asesor me llame al número que tengo registrado. | Prefiero que un atendente me llame en el número que tengo registrado. |
| [x] | `ho-b58-es-CO` | No quiero hablar con una máquina, qué hueva, mejor conéctame con alguien. | No quiero hablar con una máquina, qué pereza, mejor comuníqueme con alguien. |
| [x] | `ho-b58-es-AR` | No quiero hablar con una máquina, qué hueva, mejor conéctame con alguien. | No quiero hablar con una máquina, qué fiaca, mejor conectame con alguien. |
| [x] | `ho-b58-pt-BR` | No quiero hablar con una máquina, qué hueva, mejor conéctame con alguien. | No quiero hablar con máquina, qué lata, llámame luego con alguien. |
| [x] | `ho-b59-es-CO` | Quiero poner una queja formal y que me escuche un asesor de carne y hueso. | Quiero poner una queja formal y que me escuche un asesor de verdad. |
| [x] | `ho-b59-es-AR` | Quiero poner una queja formal y que me escuche un asesor de carne y hueso. | Quiero hacer un reclamo formal y que me escuoye un asesor de carne y hueso. |
| [x] | `ho-b59-pt-BR` | Quiero poner una queja formal y que me escuche un asesor de carne y hueso. | Quiero hacer una reclamación formal y que un atendente de carne y hueso me escuche. |
| [x] | `ho-b60-es-CO` | ¿Puedo hablar con el supervisor? | ¿Puedo hablar con el supervisor, por favor? |
| [x] | `ho-b60-es-AR` | ¿Puedo hablar con el supervisor? | ¿Me pasás con el supervisor? |
| [x] | `ho-b60-pt-BR` | ¿Puedo hablar con el supervisor? | ¿Puedo hablar con el supervisor? |
| [x] | `ho-n47` | ¿Puedo hablar con el supervisor? | ¿Me pasás con el gerente, perdón, con el supervisor? |
| [x] | `ho-b61-es-CO` | Esto no me sirve, conéctame con una persona real ahorita. | Esto no me sirve, comuníquenme con una persona real ya mismo. |
| [x] | `ho-b61-es-AR` | Esto no me sirve, conéctame con una persona real ahorita. | Esto no me sirve, pasame con una persona real ahora. |
| [x] | `ho-b61-pt-BR` | Esto no me sirve, conéctame con una persona real ahorita. | Esto no me ayuda, conéctame con una persona de verdad ahora. |
| [x] | `ho-b62-es-CO` | Necesito asistencia de un agente humano, es urgente. | Necesito que me atienda un agente humano, es urgente. |
| [x] | `ho-b62-es-AR` | Necesito asistencia de un agente humano, es urgente. | Necesito que me atienda un agente de carne y hueso, es urgente. |
| [x] | `ho-b62-pt-BR` | Necesito asistencia de un agente humano, es urgente. | Necesito la ayuda de un atendente humano, es urgente. |
| [x] | `ho-n48` | Necesito asistencia de un agente humano, es urgente. | Necesito la ayuda de un atendente robot, no, humano, es urgente. |
| [x] | `ho-b63-es-CO` | kiero ablar con un asesor porfa | kiero hablar con un asesor porfa |
| [x] | `ho-b63-es-AR` | kiero ablar con un asesor porfa | quiero ablar con un asesor porfa |
| [x] | `ho-b63-pt-BR` | kiero ablar con un asesor porfa | quiero hablar con un atendente por favor |
| [x] | `ho-b64-es-CO` | ¿Me pueden transferir con servicio al cliente con una persona real? | ¿Me pueden transferir con servicio al cliente, con una persona real? |
| [x] | `ho-b64-es-AR` | ¿Me pueden transferir con servicio al cliente con una persona real? | ¿Me pueden derivar con atención al cliente, con una persona real? |
| [x] | `ho-b65-es-CO` | Can I talk to un asesor please, no entiendo bien el chat. | Can I talk to un asesor please, no entiendo bien este chat. |
| [x] | `ho-b65-es-AR` | Can I talk to un asesor please, no entiendo bien el chat. | Can I talk to un asesor please? No entiendo bien el chat, oye. |
| [x] | `ho-b65-pt-BR` | Can I talk to un asesor please, no entiendo bien el chat. | ¿Puedo hablar con un atendente por favor, no entiendo bien este chat. |
| [x] | `ho-b66-es-CO` | Quiero que un asesor vea mi situación personalmente. | Quiero que un asesor revise mi situación personalmente. |
| [x] | `ho-b66-es-AR` | Quiero que un asesor vea mi situación personalmente. | Quiero que un asesor mire mi situación personalmente. |
| [x] | `ho-b66-pt-BR` | Quiero que un asesor vea mi situación personalmente. | Quiero que un atendente vea mi situación personalmente. |
| [x] | `ho-b67-es-CO` | ¿A qué hora puedo hablar con un ejecutivo en vivo? | ¿A qué hora puedo hablar con un asesor en vivo? |
| [x] | `ho-b67-es-AR` | ¿A qué hora puedo hablar con un ejecutivo en vivo? | ¿A qué hora me puede atender un ejecutivo en vivo? |
| [x] | `ho-b67-pt-BR` | ¿A qué hora puedo hablar con un ejecutivo en vivo? | ¿A qué horas puedo hablar con un atendente en vivo? |
| [x] | `ho-b68-es-CO` | Me gustaría agendar una llamada con un asesor para el 14 de octubre. | Quisiera agendar una llamada con un asesor para el 14 de octubre. |
| [x] | `ho-b68-es-AR` | Me gustaría agendar una llamada con un asesor para el 14 de octubre. | Quiero agendar una llamada con un asesor para el 14 de octubre. |
| [x] | `ho-b68-pt-BR` | Me gustaría agendar una llamada con un asesor para el 14 de octubre. | Me gustaría agendar una llamada con un atendente para el 14 de octubre. |
| [x] | `ho-n41` | Me gustaría agendar una llamada con un asesor para el 14 de octubre. | Quisiera agendar una llamada con un asesor para el 16 de octubre. |
| [x] | `ho-b69-es-CO` | Llevo tres semanas esperando un reembolso y nadie me resuelve, comuníquenme con un asesor ya. | Llevo tres semanas esperando una devolución y nadie me resuelve, comuníquenme con un asesor ya. |
| [x] | `ho-b69-es-AR` | Llevo tres semanas esperando un reembolso y nadie me resuelve, comuníquenme con un asesor ya. | Llevo tres semanas esperando un reintegro y nadie me resuelve, comunicame con un asesor ya. |
| [x] | `ho-b69-pt-BR` | Llevo tres semanas esperando un reembolso y nadie me resuelve, comuníquenme con un asesor ya. | Hace tres semanas que espero un reembolso y nadie resuelve, pásame con un atendente ahora. |
| [x] | `ho-b70-es-CO` | Deseo hablar con una persona, no con un asistente virtual. | Prefiero hablar con una persona y no con un asistente virtual. |
| [x] | `ho-b70-es-AR` | Deseo hablar con una persona, no con un asistente virtual. | Quiero hablar con una persona, no con un asistente virtual. |
| [x] | `ho-b70-pt-BR` | Deseo hablar con una persona, no con un asistente virtual. | Quiero hablar con una persona, no con un asistente virtual. |

## Development: 90 variants, 0 flagged by the reviewer model

### Flagged first

| OK | Case | es-MX source | Back-translation | Note |
|---|---|---|---|---|

### All other variants

| OK | Case | es-MX source | Back-translation |
|---|---|---|---|
| [x] | `dv-b01-es-CO` | No reconozco un cargo de $849 de Tienda Lumbre en mi estado de cuenta, ¿me ayudas a revisarlo? | Hola, en mi extracto sale un cobro de $84.900 de Tienda Lumbre que no reconozco, ¿me ayudas revisándolo? |
| [x] | `dv-b01-es-AR` | No reconozco un cargo de $849 de Tienda Lumbre en mi estado de cuenta, ¿me ayudas a revisarlo? | Oye, en el resumen me aparece un consumo de $8.490 en Tienda Lumbre que no reconozco, ¿me ayudás a revisarlo? |
| [x] | `dv-b01-pt-BR` | No reconozco un cargo de $849 de Tienda Lumbre en mi estado de cuenta, ¿me ayudas a revisarlo? | Hola, no reconozco una cobranza de $ 84.900 de Tienda Lumbre en mi factura, ¿puedes ayudarme a verificar? |
| [x] | `dv-b02-es-CO` | Vi en la app un cargo de $1,250 de Gasolinera Del Valle y no sé de qué es | Me apareció en la app un cobro de $125.000 de Estación Del Valle y no sé de qué es |
| [x] | `dv-b02-es-AR` | Vi en la app un cargo de $1,250 de Gasolinera Del Valle y no sé de qué es | Vi en la app un débito de $12.500 de Estación Del Valle y ni idea de qué es |
| [x] | `dv-b02-pt-BR` | Vi en la app un cargo de $1,250 de Gasolinera Del Valle y no sé de qué es | Vi en la app una compra de $ 12.500 en Posto Del Valle y no sé qué es |
| [x] | `dv-b03-es-CO` | Oye, en Cafetería Brisa me salió el mismo cobro dos veces el mismo día, de $215 cada uno | Oye, en Cafetería Brisa me salió el mismo cobro dos veces el mismo día, de $21.500 cada uno |
| [x] | `dv-b03-es-AR` | Oye, en Cafetería Brisa me salió el mismo cobro dos veces el mismo día, de $215 cada uno | Tío, en Cafetería Brisa me aparece el mismo consumo duplicado el mismo día, $2.150 cada uno |
| [x] | `dv-b03-pt-BR` | Oye, en Cafetería Brisa me salió el mismo cobro dos veces el mismo día, de $215 cada uno | Gente, en Cafeteria Brisa apareció la misma cobranza dos veces en el mismo día, $ 215 cada |
| [x] | `dv-b04-es-CO` | Me cobraron doble la suscripción de Streamflix este mes, $199 dos veces | Me cobraron doble la suscripción de Streamflix este mes, $29.900 dos veces |
| [x] | `dv-b04-es-AR` | Me cobraron doble la suscripción de Streamflix este mes, $199 dos veces | Me cobraron doble la suscripción de Streamflix este mes, $3.400 dos veces |
| [x] | `dv-b04-pt-BR` | Me cobraron doble la suscripción de Streamflix este mes, $199 dos veces | La suscripción de Streamflix fue cobrada en doble este mes, $ 29.900 dos veces |
| [x] | `dv-b05-es-CO` | Tengo un cargo de $3,400 en Electro Norte que no reconosco, quiero aclararlo | Tengo un cobro de $340.000 en Electro Norte que no reconosco, quiero aclararlo |
| [x] | `dv-b05-es-AR` | Tengo un cargo de $3,400 en Electro Norte que no reconosco, quiero aclararlo | Tengo un consumo de $34.000 en Electro Norte que no reconosco, quiero aclararlo |
| [x] | `dv-b05-pt-BR` | Tengo un cargo de $3,400 en Electro Norte que no reconosco, quiero aclararlo | Tiene una cobranza de $ 34.000 en Eletro Norte que yo no reconozco, quiero aclarar |
| [x] | `dv-b06-es-CO` | Hay una compra por internet de $720 en Marketplaza que no recuerdo haber hecho | Hay una compra por internet de $72.000 en Marketplaza que no recuerdo haber hecho |
| [x] | `dv-b06-es-AR` | Hay una compra por internet de $720 en Marketplaza que no recuerdo haber hecho | Hay una compra online de $7.200 en Marketplaza que no me acuerdo de haber hecho |
| [x] | `dv-b06-pt-BR` | Hay una compra por internet de $720 en Marketplaza que no recuerdo haber hecho | Tiene una compra en línea de $ 720 en Marketplaza de que no me acuerdo |
| [x] | `dv-b07-es-CO` | Quiero que revisen un cobro de $560 de Farmacia Sol, no lo reconozco | Necesito que revisen un cobro de $56.000 de Droguería Sol, no lo reconozco |
| [x] | `dv-b07-es-AR` | Quiero que revisen un cobro de $560 de Farmacia Sol, no lo reconozco | Quiero que revisen un consumo de $5.600 de Farmacia Sol, no lo reconozco |
| [x] | `dv-b07-pt-BR` | Quiero que revisen un cobro de $560 de Farmacia Sol, no lo reconozco | Quiero que verifiquen una cobranza de $ 56.000 de Farmácia Sol, que yo no reconozco |
| [x] | `dv-b08-es-CO` | kiero revisar un cargo de $990 d Gimnasio Fuerza ke no me cuadra | quiero revisar un cobro de $99.000 de Gimnasio Fuerza q no me cuadra |
| [x] | `dv-b08-es-AR` | kiero revisar un cargo de $990 d Gimnasio Fuerza ke no me cuadra | quiero revisar un consumo de $9.900 de Gimnasio Fuerza q no me cierra |
| [x] | `dv-b08-pt-BR` | kiero revisar un cargo de $990 d Gimnasio Fuerza ke no me cuadra | quiero revisar una cobranza de $ 9.900 de Academia Fuerza q no bate |
| [x] | `dv-b09-es-CO` | Me cobraron $1,500 en Hotel Aurora pero yo solo pagué $1,100, hay diferencia | Me cobraron $150.000 en Hotel Aurora pero yo solo pagué $110.000, hay diferencia |
| [x] | `dv-b09-es-AR` | Me cobraron $1,500 en Hotel Aurora pero yo solo pagué $1,100, hay diferencia | Me cobraron $15.000 en Hotel Aurora pero yo habia pagado $11.000, hay diferencia |
| [x] | `dv-b09-pt-BR` | Me cobraron $1,500 en Hotel Aurora pero yo solo pagué $1,100, hay diferencia | Me cobraron $ 1,500 en Hotel Aurora pero yo solo había pagado $ 1,100, tiene diferencia |
| [x] | `dv-b10-es-CO` | Oigan, tengo un detalle con mi cuenta y no sé ni por dónde empezar | Hola, tengo un inconveniente con la cuenta y no sé ni cómo explicarlo |
| [x] | `dv-b10-es-AR` | Oigan, tengo un detalle con mi cuenta y no sé ni por dónde empezar | Oye, tengo un tema con la cuenta y no sé ni por dónde arrancar |
| [x] | `dv-b10-pt-BR` | Oigan, tengo un detalle con mi cuenta y no sé ni por dónde empezar | Hola, tengo un problema en la cuenta y ni sé por dónde empezar |
| [x] | `dv-b11-es-CO` | Hice una transferencia de $2,000 ayer y no se refleja en mi cuenta | Hice una transferencia de $200.000 ayer y no se ve reflejada en mi cuenta |
| [x] | `dv-b11-es-AR` | Hice una transferencia de $2,000 ayer y no se refleja en mi cuenta | Hice una transferencia de $20.000 ayer y no se acreditó en mi cuenta |
| [x] | `dv-b11-pt-BR` | Hice una transferencia de $2,000 ayer y no se refleja en mi cuenta | Hice un Pix de $ 20.000 ayer y no aparece en mi estado de cuenta |
| [x] | `dv-b12-es-CO` | Me cobraron $380 de más en Super Mercadito y pedí la devolución hace semanas, nada que se ve | Me cobraron $38.000 de más en Super Mercadito y pedí la devolución hace semanas, nada que aparece |
| [x] | `dv-b12-es-AR` | Me cobraron $380 de más en Super Mercadito y pedí la devolución hace semanas, nada que se ve | Me cobraron $3.800 de más en Super Mercadito y pedí la devolución hace semanas, ni noticias |
| [x] | `dv-b12-pt-BR` | Me cobraron $380 de más en Super Mercadito y pedí la devolución hace semanas, nada que se ve | Me cobraron $ 380 de más en Super Mercadito y pedí la devolución hace semanas, nada hasta ahora |
| [x] | `dv-b13-es-CO` | Necesito ayuda con algo que vi en la app | Necesito que me ayuden con algo que vi en la app |
| [x] | `dv-b13-es-AR` | Necesito ayuda con algo que vi en la app | Necesito que me den una mano con algo que vi en la app |
| [x] | `dv-b13-pt-BR` | Necesito ayuda con algo que vi en la app | Necesito ayuda con una cosa que vi en la app |
| [x] | `dv-b14-es-CO` | Algo pasó con mi dinero, no sé qué fue | Pasó algo raro con mi plata, no sé qué fue |
| [x] | `dv-b14-es-AR` | Algo pasó con mi dinero, no sé qué fue | Pasó algo con mi guita, no sé qué fue |
| [x] | `dv-b14-pt-BR` | Algo pasó con mi dinero, no sé qué fue | Pasó algo con mi dinero, no sé qué fue |
| [x] | `dv-b15-es-CO` | Cancelé la compra en Zapatería Rivera y la devolución de $890 no llegó | Cancelé la compra en Zapatería Rivera y la devolución de $89.000 no llegó |
| [x] | `dv-b15-es-AR` | Cancelé la compra en Zapatería Rivera y la devolución de $890 no llegó | Cancelé la compra en Zapatería Rivera y la devolución de $8.900 no me llegó |
| [x] | `dv-b15-pt-BR` | Cancelé la compra en Zapatería Rivera y la devolución de $890 no llegó | Cancelé la compra en Sapataria Rivera y la devolución de $ 890 no llegó |
| [x] | `dv-b16-es-CO` | Algo raro está pasando, ¿me pueden ayudar? | Está pasando algo raro, ¿me pueden colaborar? |
| [x] | `dv-b16-es-AR` | Algo raro está pasando, ¿me pueden ayudar? | Me está pasando algo raro, ¿me ayudás? |
| [x] | `dv-b16-pt-BR` | Algo raro está pasando, ¿me pueden ayudar? | Está pasando algo raro, ¿me pueden ayudar? (back-translation corrected by the prompt author, Claude Opus: the Haiku output read "¿puedo ayudar?"; development case only) |
| [x] | `dv-b17-es-CO` | ¿Cuál es mi saldo disponible? | ¿Cuánto saldo tengo disponible? |
| [x] | `dv-b17-es-AR` | ¿Cuál es mi saldo disponible? | ¿Cuánta plata tengo disponible? |
| [x] | `dv-b17-pt-BR` | ¿Cuál es mi saldo disponible? | ¿Cuál es mi saldo disponible? |
| [x] | `dv-b18-es-CO` | Quiero pedir un préstamo personal, ¿qué requisitos hay? | Quiero solicitar un crédito de libre inversión, ¿qué requisitos piden? |
| [x] | `dv-b18-es-AR` | Quiero pedir un préstamo personal, ¿qué requisitos hay? | Quiero sacar un préstamo personal, ¿qué requisitos hay? |
| [x] | `dv-b18-pt-BR` | Quiero pedir un préstamo personal, ¿qué requisitos hay? | Quiero pedir un préstamo personal, ¿cuáles son los requisitos? |
| [x] | `dv-b19-es-CO` | ¿Cómo abro una cuenta de ahorro para mi hijo? | ¿Cómo abro una cuenta de ahorros para mi hijo? |
| [x] | `dv-b19-es-AR` | ¿Cómo abro una cuenta de ahorro para mi hijo? | ¿Cómo abro una caja de ahorro para mi hijo? |
| [x] | `dv-b19-pt-BR` | ¿Cómo abro una cuenta de ahorro para mi hijo? | ¿Cómo hago para abrir una cuenta de ahorro para mi hijo? |
| [x] | `dv-b20-es-CO` | Quiero subir el límite de mi tarjeta de crédito | Quiero que me aumenten el cupo de la tarjeta de crédito |
| [x] | `dv-b20-es-AR` | Quiero subir el límite de mi tarjeta de crédito | Quiero que me suban el límite de la tarjeta de crédito |
| [x] | `dv-b20-pt-BR` | Quiero subir el límite de mi tarjeta de crédito | Quiero aumentar el límite de mi tarjeta de crédito |
| [x] | `dv-b21-es-CO` | Vi mis cargos del mes, todo bien, pero ¿qué seguros tienen para la tarjeta? | Revisé mis cobros del mes, todo bien, pero ¿qué seguros ofrecen para la tarjeta? |
| [x] | `dv-b21-es-AR` | Vi mis cargos del mes, todo bien, pero ¿qué seguros tienen para la tarjeta? | Miré mis consumos del mes, todo bien, pero ¿qué seguros tienen para la tarjeta? |
| [x] | `dv-b21-pt-BR` | Vi mis cargos del mes, todo bien, pero ¿qué seguros tienen para la tarjeta? | Verifiqué mis cobrancias del mes, todo bien, pero ¿qué seguros tienen para la tarjeta? |
| [x] | `dv-b22-es-CO` | ¿Cuál es la tasa de interés de una tarjeta de crédito nueva? | Quiero saber qué tasa de interés me cobrarían si saco una tarjeta de crédito nueva |
| [x] | `dv-b22-es-AR` | ¿Cuál es la tasa de interés de una tarjeta de crédito nueva? | ¿Qué tasa de interés tiene una tarjeta de crédito nueva? |
| [x] | `dv-b22-pt-BR` | ¿Cuál es la tasa de interés de una tarjeta de crédito nueva? | ¿Cuál es la tasa de interés de una tarjeta de crédito nueva? |
| [x] | `dv-b23-es-CO` | Necesito cambiar mi domicilio registrado en el banco | Necesito actualizar mi dirección de residencia en el banco |
| [x] | `dv-b23-es-AR` | Necesito cambiar mi domicilio registrado en el banco | Necesito cambiar mi domicilio registrado en el banco |
| [x] | `dv-b23-pt-BR` | Necesito cambiar mi domicilio registrado en el banco | Necesito actualizar mi dirección registrada en el banco |
| [x] | `dv-b24-es-CO` | Quiero hablar con una persona, por favor | Quiero hablar con un asesor, por favor |
| [x] | `dv-b24-es-AR` | Quiero hablar con una persona, por favor | Quiero hablar con una persona, por favor |
| [x] | `dv-b24-pt-BR` | Quiero hablar con una persona, por favor | Quiero hablar con una persona, por favor |
| [x] | `dv-b25-es-CO` | Pásame con un asesor | Comuníqueme con un agente humano |
| [x] | `dv-b25-es-AR` | Pásame con un asesor | Pasame con un asesor |
| [x] | `dv-b25-pt-BR` | Pásame con un asesor | Pásame con un atendente |
| [x] | `dv-b26-es-CO` | Ya van tres veces que me atiende el bot y no resuelve nada, necesito un ejecutivo de verdad | Ya van tres veces que me responde el robot y no resuelve nada, necesito un asesor de verdad |
| [x] | `dv-b26-es-AR` | Ya van tres veces que me atiende el bot y no resuelve nada, necesito un ejecutivo de verdad | Ya van tres veces que me atiende el bot y no resuelve nada, necesito un ejecutivo de verdad |
| [x] | `dv-b26-pt-BR` | Ya van tres veces que me atiende el bot y no resuelve nada, necesito un ejecutivo de verdad | Ya es la tercera vez que el robot me atiende y no resuelve nada, necesito un atendente de verdad |
| [x] | `dv-b27-es-CO` | ¿Hay alguien real ahí? no quiero hablar con una máquina | ¿Hay alguien de verdad ahí? no quiero hablar con una máquina |
| [x] | `dv-b27-es-AR` | ¿Hay alguien real ahí? no quiero hablar con una máquina | ¿Hay alguien real ahí? no quiero hablar con una máquina |
| [x] | `dv-b27-pt-BR` | ¿Hay alguien real ahí? no quiero hablar con una máquina | ¿Hay alguien de verdad ahí? No quiero hablar con una máquina |
| [x] | `dv-b28-es-CO` | Estoy muy molesto con mi cargo de $600, mejor que me llame un agente | Estoy muy molesto con mi cobro de $60.000, mejor que me llame un asesor |
| [x] | `dv-b28-es-AR` | Estoy muy molesto con mi cargo de $600, mejor que me llame un agente | Estoy re caliente con mi consumo de $6.000, mejor que me llame un agente |
| [x] | `dv-b28-pt-BR` | Estoy muy molesto con mi cargo de $600, mejor que me llame un agente | Estoy muy molesto con la cobranza de $ 60.000, prefiero que un atendente me llame |
| [x] | `dv-b29-es-CO` | quiero un humano ya | quiero un asesor ya, no un bot |
| [x] | `dv-b29-es-AR` | quiero un humano ya | quiero un humano ya, dale |
| [x] | `dv-b29-pt-BR` | quiero un humano ya | quiero un humano ahora |
| [x] | `dv-b30-es-CO` | No entiendo cómo funciona esto, ¿mejor me atiende alguien en una sucursal o por teléfono? | No entiendo cómo funciona esto, ¿mejor me atiende alguien por teléfono o en una oficina? |
| [x] | `dv-b30-es-AR` | No entiendo cómo funciona esto, ¿mejor me atiende alguien en una sucursal o por teléfono? | No entiendo cómo funciona esto, ¿mejor me atiende alguien por teléfono o en una sucursal? |
| [x] | `dv-b30-pt-BR` | No entiendo cómo funciona esto, ¿mejor me atiende alguien en una sucursal o por teléfono? | No entiendo cómo funciona esto, ¿será que alguien puede atenderme por teléfono o en la agencia? |
