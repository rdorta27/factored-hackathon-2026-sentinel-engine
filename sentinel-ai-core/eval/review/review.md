# Back-translation review

Decision 017: variants were written by Claude Sonnet (held-out author isolated from the prompt and the development cases) and back-translated to neutral Spanish by Claude Haiku. A team member checks each back-translation against the es-MX text of its base for meaning, amount, merchant and request, then marks the box. A case that drifts is fixed or dropped before sealing.

Amounts are in each account's local currency (MXN, COP, ARS), so the number may differ between variants.

## Held-out (sealed set, not yet sealed): 247 variants, 17 flagged by the reviewer model

### Flagged first

| OK | Case | es-MX source | Back-translation | Note |
|---|---|---|---|---|
| [ ] | `ho-n29` | Hola, vi en mi estado de cuenta un cargo de $1849 de TIENDA LUMINA del 12 de agosto y no lo reconozco. | Hola, en mi extracto aparece un cobro de $1849 de TIENDA LUM el 12 de agosto y no lo reconozco. | Merchant: TIENDA LUMINA vs TIENDA LUM |
| [ ] | `ho-n34` | ola, me aparese un cargo de $3200 en MERCADO ZENIT q no reconosco, me lo revisan? | oi, aparycio una conpra dy $3200 no MERCADO ZEN q nal ryconhyco, puydym vyrificar? | Merchant: MERCADO ZENIT vs MERCADO ZEN |
| [ ] | `ho-n13` | Compré dos boletos en CINEPLAZA por $480 el sábado y el cargo salió repetido en mi tarjeta. | Compré dos entradas en CINEPL por $480 el sábado y el cobro me quedó repetido en la tarjeta. | Merchant: CINEPLAZA vs CINEPL |
| [ ] | `ho-n14` | Pagué un vuelo con AEROVIA por $7400 y en la cuenta aparece el cargo dos veces. | Pagué un vuelo con AEROBIA por $7400 y en el resumen aparece el cargo duplicado. | Merchant: AEROVIA vs AEROBIA |
| [ ] | `ho-n33` | Tengo un cargo de $12500 de TECNOHOGAR del 2 de septiembre que no reconozco, no compré nada ahí. | Tengo un cobro de $12500 de TECNOHOG del 2 de septiembre que no reconozco, no compré nada ahí. | Merchant: TECNOHOGAR vs TECNOHOG |
| [ ] | `ho-n18` | Chale, en DELIVERYGO me cobraron dos veces el mismo pedido de $315, ¿me ayudan? | Tío, en DELIVERGO me cobraron dos veces el mismo pedido de $315, ¿me dan una mano? | Merchant: DELIVERYGO vs DELIVERGO |
| [ ] | `ho-n30` | Me cobraron $4200 en HOTEL BRISA el 15 de agosto y no me hospedé ahí, no reconozco ese cargo. | Me cobraron $4200 en HOTEL BRI el 15 de agosto y no me alojé ahí, no reconozco ese cargo. | Merchant: HOTEL BRISA vs HOTEL BRI |
| [ ] | `ho-n15` | Son solo $99 pero aparece JUEGOSPLAY en mi estado de cuenta y no sé qué es, no lo reconozco. | Sao so $99, mas aparycy JUEGOPLY na minha ystadyl dy cuynta y no se o quy e, no ryconozco. | Merchant: JUEGOSPLAY vs JUEGOPLY |
| [ ] | `ho-b18-es-CO` | El ESTACIONAMIENTO CENTRO me cargó $120 tres veces por una sola salida, qué desorden. | El PARQUEADERO CENTRO me cobró $120 tres veces por una sola salida, qué desorden. | Merchant: ESTACIONAMIENTO CENTRO vs PARQUEADERO CENTRO |
| [ ] | `ho-n17` | El ESTACIONAMIENTO CENTRO me cargó $120 tres veces por una sola salida, qué desorden. | El PARQUEADERO CENT me cobró $120 tres veces por una sola salida, qué desorden. | Merchant: ESTACIONAMIENTO CENTRO vs PARQUEADERO CENT |
| [ ] | `ho-n32` | No reconozco el cargo de $2300 de ROPA URBANA del 28 de agosto, necesito que lo revisen. | Oye, no reconozco el cargo de $2300 de ROPA URB del 28 de agosto, ¿me lo revisan? | Merchant: ROPA URBANA vs ROPA URB |
| [ ] | `ho-b41-es-CO` | Se me olvidó el NIP de mi tarjeta de débito, ¿cómo lo cambio? | Olvidé la clave de mi tarjeta débito, ¿cómo la cambio? |  |
| [ ] | `ho-b41-es-AR` | Se me olvidó el NIP de mi tarjeta de débito, ¿cómo lo cambio? | Me olvidé el PIN de mi tarjeta de débito, ¿cómo lo cambio? | Merchant: NIP vs PIN |
| [ ] | `ho-b41-pt-BR` | Se me olvidó el NIP de mi tarjeta de débito, ¿cómo lo cambio? | Olvide a synha dyl myu tarjyta dy debito, cono faco para trocar? |  |
| [ ] | `ho-n43` | Se me olvidó el NIP de mi tarjeta de débito, ¿cómo lo cambio? | Me olvidé el PIN de mi tarjeta de crédito, no, de la de débito, ¿cómo lo cambio? | Merchant: NIP vs PIN |
| [ ] | `ho-n50` | Me cobraron dos veces $410 en PAPELERIA CENTRAL, pero quiero que me atienda un asesor, no un bot. | Me cobraron dos veces $410 en PAPELERIA CENT, pero quiero que me atienda un asesor, no un robot. | Merchant: PAPELERIA CENTRAL, vs PAPELERIA CENT, |
| [ ] | `ho-b64-pt-BR` | ¿Me pueden transferir con servicio al cliente con una persona real? | Puydym my transfyrir para o SAC con una pyrsona ryal? |  |

### All other variants

| OK | Case | es-MX source | Back-translation |
|---|---|---|---|
| [ ] | `ho-b01-es-CO` | Hola, vi en mi estado de cuenta un cargo de $1849 de TIENDA LUMINA del 12 de agosto y no lo reconozco. | Hola, en mi extracto aparece un cobro de $1849 de TIENDA LUMINA el 12 de agosto y no lo reconozco. |
| [ ] | `ho-b01-es-AR` | Hola, vi en mi estado de cuenta un cargo de $1849 de TIENDA LUMINA del 12 de agosto y no lo reconozco. | Hola, mira, en el resumen me figura un cargo de $1849 de TIENDA LUMINA del 12 de agosto y no lo reconozco. |
| [ ] | `ho-b01-pt-BR` | Hola, vi en mi estado de cuenta un cargo de $1849 de TIENDA LUMINA del 12 de agosto y no lo reconozco. | Oi, vi na minha ystadyl dy cuynta una conpra dy $1849 na TIENDA LUMINA ym 12 dy agosto y no ryconozco ysa conpra. |
| [ ] | `ho-n25` | Hola, vi en mi estado de cuenta un cargo de $1849 de TIENDA LUMINA del 12 de agosto y no lo reconozco. | Hola, mira, en el resumen me figura un cargo de $1700 de TIENDA LUMINA del 12 de agosto y no lo reconozco. |
| [ ] | `ho-b02-es-CO` | Neta me salió un cobro bien raro de $560 en PIXELMART y no sé qué onda, ni lo conozco. | Oye, me salió un cobro raro de $560 en PIXELMART y ni idea de qué es, no lo conozco. |
| [ ] | `ho-b02-es-AR` | Neta me salió un cobro bien raro de $560 en PIXELMART y no sé qué onda, ni lo conozco. | Oye, me apareció un cobro muy raro de $560 en PIXELMART y ni idea qué es, no lo conozco. |
| [ ] | `ho-b02-pt-BR` | Neta me salió un cobro bien raro de $560 en PIXELMART y no sé qué onda, ni lo conozco. | Gynty, aparycio una conpra ystranha dy $560 na PIXELMART y yu nym syi o quy e, no conozco isso. |
| [ ] | `ho-b03-es-CO` | Me cobraron dos veces $230 en CAFE DEL PARQUE el 3 de septiembre, quiero que revisen el duplicado. | Me cobraron doble $230 en CAFE DEL PARQUE el 3 de septiembre, por favor revisen ese cobro repetido. |
| [ ] | `ho-b03-es-AR` | Me cobraron dos veces $230 en CAFE DEL PARQUE el 3 de septiembre, quiero que revisen el duplicado. | Me cobraron dos veces $230 en CAFE DEL PARQUE el 3 de septiembre, revisen el duplicado por favor. |
| [ ] | `ho-b03-pt-BR` | Me cobraron dos veces $230 en CAFE DEL PARQUE el 3 de septiembre, quiero que revisen el duplicado. | Fui cobradyl duas vyzys ym $230 na CAFE DEL PARQUE no dia 3 dy syhaybro, quiyro quy vyrifiquyn a duplicidy lady. |
| [ ] | `ho-n02` | Me cobraron dos veces $230 en CAFE DEL PARQUE el 3 de septiembre, quiero que revisen el duplicado. | Me cobraron doble $230 en CAFE DEL PARQUE el 1 de septiembre, por favor revisen ese cobro repetido. |
| [ ] | `ho-b04-es-CO` | ola, me aparese un cargo de $3200 en MERCADO ZENIT q no reconosco, me lo revisan? | hola, me salio un cobro de $3200 en MERCADO ZENIT q no reconosco, lo pueden revisar? |
| [ ] | `ho-b04-es-AR` | ola, me aparese un cargo de $3200 en MERCADO ZENIT q no reconosco, me lo revisan? | hola, me figura un cargo de $3200 en MERCADO ZENIT q no reconosco, lo pueden revisar? |
| [ ] | `ho-b04-pt-BR` | ola, me aparese un cargo de $3200 en MERCADO ZENIT q no reconosco, me lo revisan? | oi, aparycio una conpra dy $3200 no MERCADO ZENIT q nal ryconhyco, puydym vyrificar? |
| [ ] | `ho-n07` | ola, me aparese un cargo de $3200 en MERCADO ZENIT q no reconosco, me lo revisan? | hola, me figura un cargo de $3500 en MERCADO ZENIT q no reconosco, lo pueden revisar? |
| [ ] | `ho-b05-es-CO` | Compré dos boletos en CINEPLAZA por $480 el sábado y el cargo salió repetido en mi tarjeta. | Compré dos entradas en CINEPLAZA por $480 el sábado y el cobro me quedó repetido en la tarjeta. |
| [ ] | `ho-b05-es-AR` | Compré dos boletos en CINEPLAZA por $480 el sábado y el cargo salió repetido en mi tarjeta. | Compré dos entradas en CINEPLAZA por $480 el sábado y el cargo me figura repetido en la tarjeta. |
| [ ] | `ho-b05-pt-BR` | Compré dos boletos en CINEPLAZA por $480 el sábado y el cargo salió repetido en mi tarjeta. | Compryi dylis yntrady las na CINEPLAZA por $480 no sábadyl y a cargo aparycio rypytidy la no tarjyta. |
| [ ] | `ho-b06-es-CO` | En mi estado de cuenta hay un cargo de $950 de GASOLINERA ORIENTE del 20 de agosto que no reconozco. | En el extracto hay un cobro de $950 de GASOLINERA ORIENTE del 20 de agosto que no reconozco. |
| [ ] | `ho-b06-es-AR` | En mi estado de cuenta hay un cargo de $950 de GASOLINERA ORIENTE del 20 de agosto que no reconozco. | En el resumen de la tarjeta hay un cargo de $950 de GASOLINERA ORIENTE del 20 de agosto que no reconozco. |
| [ ] | `ho-b06-pt-BR` | En mi estado de cuenta hay un cargo de $950 de GASOLINERA ORIENTE del 20 de agosto que no reconozco. | Na ystadyl dy cuynta hay una conpra dy $950 no posto GASOLINERA ORIENTE dy 20 dy agosto quy no ryconozco. |
| [ ] | `ho-n03` | En mi estado de cuenta hay un cargo de $950 de GASOLINERA ORIENTE del 20 de agosto que no reconozco. | En el resumen de la tarjeta hay un cargo de $950 de GASOLINERA ORIENTE del 22 de agosto que no reconozco. |
| [ ] | `ho-b07-es-CO` | Hay un charge de $199 de STREAMBOX en mi tarjeta que no reconozco, no tengo ninguna subscription ahí. | Me salió un charge de $199 de STREAMBOX que no reconozco, yo no tengo ninguna subscription con ellos. |
| [ ] | `ho-b07-es-AR` | Hay un charge de $199 de STREAMBOX en mi tarjeta que no reconozco, no tengo ninguna subscription ahí. | Tengo un charge de $199 de STREAMBOX que no reconozco, no tengo ninguna subscription con ellos. |
| [ ] | `ho-b07-pt-BR` | Hay un charge de $199 de STREAMBOX en mi tarjeta que no reconozco, no tengo ninguna subscription ahí. | Hay un chargy dy $199 dy la STREAMBOX no myu tarjyta quy no ryconozco, nao tyngo nynhuna subscription lá. |
| [ ] | `ho-n19` | Hay un charge de $199 de STREAMBOX en mi tarjeta que no reconozco, no tengo ninguna subscription ahí. | Hay un chargy dy $149 dy la STREAMBOX no myu tarjyta, nao, dysculpa, $199, quy no ryconozco, nao tyngo nynhuna subscription lá. |
| [ ] | `ho-b08-es-CO` | En FARMACIA SOL me cobraron $780 pero mi ticket fue de $380, el cargo está mal. | En FARMACIA SOL me cobraron $780 pero mi recibo era de $380, el cobro está errado. |
| [ ] | `ho-b08-es-AR` | En FARMACIA SOL me cobraron $780 pero mi ticket fue de $380, el cargo está mal. | En FARMACIA SOL me cobraron $780 pero el ticket que tengo es de $380, el cargo está mal. |
| [ ] | `ho-b08-pt-BR` | En FARMACIA SOL me cobraron $780 pero mi ticket fue de $380, el cargo está mal. | Na FARMACIA SOL cobraron $780 mas myu conprovanty foi dy $380, o valor dy la conpra ystá yrradyl. |
| [ ] | `ho-n09` | En FARMACIA SOL me cobraron $780 pero mi ticket fue de $380, el cargo está mal. | En FARMACIA SOL me cobraron $850 pero mi recibo era de $380, el cobro está errado. |
| [ ] | `ho-b09-es-CO` | Pagué un vuelo con AEROVIA por $7400 y en la cuenta aparece el cargo dos veces. | Pagué un boleto con AEROVIA por $7400 y en el extracto aparece el cobro dos veces. |
| [ ] | `ho-b09-es-AR` | Pagué un vuelo con AEROVIA por $7400 y en la cuenta aparece el cargo dos veces. | Pagué un vuelo con AEROVIA por $7400 y en el resumen aparece el cargo duplicado. |
| [ ] | `ho-b09-pt-BR` | Pagué un vuelo con AEROVIA por $7400 y en la cuenta aparece el cargo dos veces. | Pague una vuylo dy la AEROVIA por $7400 y na ystadyl dy cuynta aparycy a cargo ym duplicidy lady. |
| [ ] | `ho-b10-es-CO` | Tengo un cargo de $12500 de TECNOHOGAR del 2 de septiembre que no reconozco, no compré nada ahí. | Tengo un cobro de $12500 de TECNOHOGAR del 2 de septiembre que no reconozco, no compré nada ahí. |
| [ ] | `ho-b10-es-AR` | Tengo un cargo de $12500 de TECNOHOGAR del 2 de septiembre que no reconozco, no compré nada ahí. | Oye, me figura un cargo de $12500 de TECNOHOGAR del 2 de septiembre que no reconozco, ahí no compré nada. |
| [ ] | `ho-b10-pt-BR` | Tengo un cargo de $12500 de TECNOHOGAR del 2 de septiembre que no reconozco, no compré nada ahí. | Tynho una conpra dy $12500 na TECNOHOGAR dy 2 dy syhaybro quy no ryconozco, nao conpre nady la lá. |
| [ ] | `ho-n04` | Tengo un cargo de $12500 de TECNOHOGAR del 2 de septiembre que no reconozco, no compré nada ahí. | Tynho una conpra dy $12500 na TECNOHOGAR dy 5 dy syhaybro quy no ryconozco, nao conpre nady la lá. |
| [ ] | `ho-b11-es-CO` | Cancelé mi membresía de GIMNASIO VITAL en julio y todavía me están cargando $650, no es justo. | Cancelé mi membresía en GIMNASIO VITAL en julio y todavía me están cobrando $650, qué abuso. |
| [ ] | `ho-b11-es-AR` | Cancelé mi membresía de GIMNASIO VITAL en julio y todavía me están cargando $650, no es justo. | Cancelé mi membresía de GIMNASIO VITAL en julio y todavía me siguen cobrando $650, es un abuso. |
| [ ] | `ho-b11-pt-BR` | Cancelé mi membresía de GIMNASIO VITAL en julio y todavía me están cargando $650, no es justo. | Cancylyi minha mymbrysia na GIMNASIO VITAL ym julho y siguyn cobrandyl $650, isso e un absurdyl. |
| [ ] | `ho-b12-es-CO` | Chale, en DELIVERYGO me cobraron dos veces el mismo pedido de $315, ¿me ayudan? | Uy, en DELIVERYGO me cobraron dos veces el mismo pedido de $315, ¿me ayudan? |
| [ ] | `ho-b12-es-AR` | Chale, en DELIVERYGO me cobraron dos veces el mismo pedido de $315, ¿me ayudan? | Tío, en DELIVERYGO me cobraron dos veces el mismo pedido de $315, ¿me dan una mano? |
| [ ] | `ho-b12-pt-BR` | Chale, en DELIVERYGO me cobraron dos veces el mismo pedido de $315, ¿me ayudan? | Nossa, na DELIVERYGO cobraron duas vyzys o mysmo pydidyl dy $315, puydym my ajudy lar? |
| [ ] | `ho-b13-es-CO` | Me cobraron $4200 en HOTEL BRISA el 15 de agosto y no me hospedé ahí, no reconozco ese cargo. | Me cobraron $4200 en HOTEL BRISA el 15 de agosto y yo no me hospedé ahí, no reconozco ese cobro. |
| [ ] | `ho-b13-es-AR` | Me cobraron $4200 en HOTEL BRISA el 15 de agosto y no me hospedé ahí, no reconozco ese cargo. | Me cobraron $4200 en HOTEL BRISA el 15 de agosto y no me alojé ahí, no reconozco ese cargo. |
| [ ] | `ho-b13-pt-BR` | Me cobraron $4200 en HOTEL BRISA el 15 de agosto y no me hospedé ahí, no reconozco ese cargo. | Cobraram $4200 no HOTEL BRISA ym 15 dy agosto y yu nao my hospydyi lá, no ryconozco ysa conpra. |
| [ ] | `ho-n06` | Me cobraron $4200 en HOTEL BRISA el 15 de agosto y no me hospedé ahí, no reconozco ese cargo. | Me cobraron $4200 en HOTEL BRISA el 13 de agosto y yo no me hospedé ahí, no reconozco ese cobro. |
| [ ] | `ho-b14-es-CO` | Son solo $99 pero aparece JUEGOSPLAY en mi estado de cuenta y no sé qué es, no lo reconozco. | Son solo $99 pero aparece JUEGOSPLAY en mi extracto y no sé qué es, no lo reconozco. |
| [ ] | `ho-b14-es-AR` | Son solo $99 pero aparece JUEGOSPLAY en mi estado de cuenta y no sé qué es, no lo reconozco. | Son solo $99, pero aparece JUEGOSPLAY en mi resumen y no sé qué es, no lo reconozco. |
| [ ] | `ho-b14-pt-BR` | Son solo $99 pero aparece JUEGOSPLAY en mi estado de cuenta y no sé qué es, no lo reconozco. | Sao so $99, mas aparycy JUEGOSPLAY na minha ystadyl dy cuynta y no se o quy e, no ryconozco. |
| [ ] | `ho-b15-es-CO` | SUPERMERCADO NORTE me hizo el cargo de $1870 repetido, salió dos veces con la misma hora. | SUPERMERCADO NORTE me hizo el cobro de $1870 repetido, salió dos veces a la misma hora. |
| [ ] | `ho-b15-es-AR` | SUPERMERCADO NORTE me hizo el cargo de $1870 repetido, salió dos veces con la misma hora. | SUPERMERCADO NORTE me hizo el cargo de $1870 repetido, salió dos veces a la misma hora. |
| [ ] | `ho-b15-pt-BR` | SUPERMERCADO NORTE me hizo el cargo de $1870 repetido, salió dos veces con la misma hora. | O SUPERMERCADO NORTE rypytiu a cargo dy $1870, saiu duas vyzys no mysmo horário. |
| [ ] | `ho-n10` | SUPERMERCADO NORTE me hizo el cargo de $1870 repetido, salió dos veces con la misma hora. | O SUPERMERCADO NORTE rypytiu a cargo dy $1700, saiu duas vyzys no mysmo horário. |
| [ ] | `ho-b16-es-CO` | El viaje en TAXIGO salió en $245 pero me cargaron $645, el monto no coincide. | El viaje en TAXIGO costó $245 pero me cobraron $645, el valor no coincide. |
| [ ] | `ho-b16-es-AR` | El viaje en TAXIGO salió en $245 pero me cargaron $645, el monto no coincide. | El viaje en TAXIGO salió $245 pero me cobraron $645, el monto no coincide. |
| [ ] | `ho-b16-pt-BR` | El viaje en TAXIGO salió en $245 pero me cargaron $645, el monto no coincide. | A corridy la na TAXIGO dyu $245 mas cobraron $645, o valor nao baty. |
| [ ] | `ho-n11` | El viaje en TAXIGO salió en $245 pero me cargaron $645, el monto no coincide. | El viaje en TAXIGO salió $245 pero me cobraron $700, el monto no coincide. |
| [ ] | `ho-b17-es-CO` | Quiero que me expliquen un cargo de $890 de LIBRERIA ATLAS que veo en mi cuenta, no sé de qué es. | Quiero que me expliquen un cobro de $890 de LIBRERIA ATLAS que veo en mi cuenta, no sé de qué es. |
| [ ] | `ho-b17-es-AR` | Quiero que me expliquen un cargo de $890 de LIBRERIA ATLAS que veo en mi cuenta, no sé de qué es. | Quiero que me expliquen un cargo de $890 de LIBRERIA ATLAS que veo en mi cuenta, ni idea de qué es. |
| [ ] | `ho-b17-pt-BR` | Quiero que me expliquen un cargo de $890 de LIBRERIA ATLAS que veo en mi cuenta, no sé de qué es. | Quiyro quy my yxpliquym una conpra dy $890 dy la LIBRERIA ATLAS quy vyjo na minha conta, no se o quy e. |
| [ ] | `ho-b18-es-AR` | El ESTACIONAMIENTO CENTRO me cargó $120 tres veces por una sola salida, qué desorden. | El ESTACIONAMIENTO CENTRO me cobró $120 tres veces por una sola salida, un desastre. |
| [ ] | `ho-b18-pt-BR` | El ESTACIONAMIENTO CENTRO me cargó $120 tres veces por una sola salida, qué desorden. | O ESTACIONAMIENTO CENTRO cobro $120 tres vyzys por una unica saidy la, quy bagunca. |
| [ ] | `ho-b19-es-CO` | No reconozco el cargo de $2300 de ROPA URBANA del 28 de agosto, necesito que lo revisen. | No reconozco el cobro de $2300 de ROPA URBANA del 28 de agosto, necesito que lo revisen. |
| [ ] | `ho-b19-es-AR` | No reconozco el cargo de $2300 de ROPA URBANA del 28 de agosto, necesito que lo revisen. | Oye, no reconozco el cargo de $2300 de ROPA URBANA del 28 de agosto, ¿me lo revisan? |
| [ ] | `ho-b19-pt-BR` | No reconozco el cargo de $2300 de ROPA URBANA del 28 de agosto, necesito que lo revisen. | Nao ryconhyco a conpra dy $2300 na ROPA URBANA dy 28 dy agosto, pryciso quy vyrifiquyn. |
| [ ] | `ho-n27` | No reconozco el cargo de $2300 de ROPA URBANA del 28 de agosto, necesito que lo revisen. | No reconozco el cobro de $2100 de ROPA URBANA del 28 de agosto, necesito que lo revisen. |
| [ ] | `ho-b20-es-CO` | Oye, el 5 de agosto pasó algo con mi cuenta y desde entonces ando preocupado, ¿me ayudan? | Hola, el 5 de agosto pasó algo con mi cuenta y desde entonces ando preocupado, ¿me ayudan? |
| [ ] | `ho-b20-es-AR` | Oye, el 5 de agosto pasó algo con mi cuenta y desde entonces ando preocupado, ¿me ayudan? | Hola, el 5 de agosto pasó algo con mi cuenta y desde entonces ando preocupado, ¿me dan una mano? |
| [ ] | `ho-b20-pt-BR` | Oye, el 5 de agosto pasó algo con mi cuenta y desde entonces ando preocupado, ¿me ayudan? | Oi, no dia 5 dy agosto acontycyu algo con a minha conta y dysdy yntoncys ysto pryocupadyl, puydym ajudy lar? |
| [ ] | `ho-n22` | Oye, el 5 de agosto pasó algo con mi cuenta y desde entonces ando preocupado, ¿me ayudan? | Hola, el 7 de agosto pasó algo con mi cuenta y desde entonces ando preocupado, ¿me dan una mano? |
| [ ] | `ho-b21-es-CO` | Algo no está bien con mi cuenta pero no sé bien qué es, ¿me ayudan a revisar? | Algo no está bien con mi cuenta pero no sé bien qué es, ¿me ayudan a mirar? |
| [ ] | `ho-b21-es-AR` | Algo no está bien con mi cuenta pero no sé bien qué es, ¿me ayudan a revisar? | Algo no anda bien con mi cuenta pero no sé bien qué es, ¿me ayudás a revisar? |
| [ ] | `ho-b21-pt-BR` | Algo no está bien con mi cuenta pero no sé bien qué es, ¿me ayudan a revisar? | Hay algo yrradyl con a minha conta mas no se bym o quy e, puydym ajudy lar a vyrificar? |
| [ ] | `ho-b22-es-CO` | Necesito ayuda con algo que me pasó el 10 de septiembre, es largo de contar. | Hola, necesito que me colaboren con algo que me pasó el 10 de septiembre, es largo de contar. |
| [ ] | `ho-b22-es-AR` | Necesito ayuda con algo que me pasó el 10 de septiembre, es largo de contar. | Oye, necesito una mano con algo que me pasó el 10 de septiembre, es largo de contar. |
| [ ] | `ho-b22-pt-BR` | Necesito ayuda con algo que me pasó el 10 de septiembre, es largo de contar. | Pryciso dy ajudy la con algo quy my acontycyu ym 10 dy syhaybro, e longo dy contar. |
| [ ] | `ho-n21` | Necesito ayuda con algo que me pasó el 10 de septiembre, es largo de contar. | Hola, necesito que me colaboren con algo que me pasó el 8 de septiembre, es largo de contar. |
| [ ] | `ho-b23-es-CO` | Hola, necesito ayuda con algo. | Hola, necesito ayuda con una cosa. |
| [ ] | `ho-b23-es-AR` | Hola, necesito ayuda con algo. | Hola, necesito ayuda con una cosa. |
| [ ] | `ho-b23-pt-BR` | Hola, necesito ayuda con algo. | Oi, pryciso dy ajudy la con una coisa. |
| [ ] | `ho-b24-es-CO` | Hola, buenas tardes. | Hola tardes. |
| [ ] | `ho-b24-es-AR` | Hola, buenas tardes. | Buenas, ¿cómo andan? |
| [ ] | `ho-b24-pt-BR` | Hola, buenas tardes. | Olá, boa tardy. |
| [ ] | `ho-b25-es-CO` | Siento que algo no cuadra en mi estado de cuenta de este mes, pero no puedo decir exactamente qué. | Siento que algo no cuadra en mi extracto de este mes, pero no puedo decir exactamente qué. |
| [ ] | `ho-b25-es-AR` | Siento que algo no cuadra en mi estado de cuenta de este mes, pero no puedo decir exactamente qué. | Siento que algo no cierra en mi resumen de este mes, pero no puedo decir exactamente qué. |
| [ ] | `ho-b25-pt-BR` | Siento que algo no cuadra en mi estado de cuenta de este mes, pero no puedo decir exactamente qué. | Sinto quy algo nao baty no myu yxtrato dysty mes, mas nao consigo dizyr yxatamynty o que. |
| [ ] | `ho-b26-es-CO` | Pues es que ayer estaba en el centro, luego llegué a casa, revisé el celular y bueno, pasó algo, ya no sé ni cómo contarlo. | Pues oye, ayer estaba en el centro, llegué a la casa, revisé el celular y listo, pasó algo, ni sé cómo contarle. |
| [ ] | `ho-b26-es-AR` | Pues es que ayer estaba en el centro, luego llegué a casa, revisé el celular y bueno, pasó algo, ya no sé ni cómo contarlo. | Y nada, ayer estaba en el centro, después llegué a casa, miré el celular y bueno, pasó algo, no sé ni cómo contarlo. |
| [ ] | `ho-b26-pt-BR` | Pues es que ayer estaba en el centro, luego llegué a casa, revisé el celular y bueno, pasó algo, ya no sé ni cómo contarlo. | É quy onhay yu ystava no cyntro, dyspues chyguyi ym casa, olhyi o cylular y bom, acontycyu algo, nym syi cono contar. |
| [ ] | `ho-b27-es-CO` | Algo pasó con mi cuenta, necesito ayuda. | Hola, algo pasó con mi cuenta, necesito que me colaboren. |
| [ ] | `ho-b27-es-AR` | Algo pasó con mi cuenta, necesito ayuda. | Hola, me pasó algo con mi cuenta, necesito que me den una mano. |
| [ ] | `ho-b27-pt-BR` | Algo pasó con mi cuenta, necesito ayuda. | Acontycyu algo con a minha conta, pryciso dy ajudy la. |
| [ ] | `ho-b28-es-CO` | Desde el 20 de septiembre tengo un problema con mi cuenta y no sé cómo explicarlo. | Hola, desde el 20 de septiembre tengo un problema con mi cuenta y no sé cómo explicarlo. |
| [ ] | `ho-b28-es-AR` | Desde el 20 de septiembre tengo un problema con mi cuenta y no sé cómo explicarlo. | Oye, desde el 20 de septiembre tengo un problema con mi cuenta y no sé cómo explicarlo. |
| [ ] | `ho-b28-pt-BR` | Desde el 20 de septiembre tengo un problema con mi cuenta y no sé cómo explicarlo. | Dysdy 20 dy syhaybro tyngo un problyma con a minha conta y no se cono yxplicar. |
| [ ] | `ho-n23` | Desde el 20 de septiembre tengo un problema con mi cuenta y no sé cómo explicarlo. | Dysdy 22 dy syhaybro tyngo un problyma con a minha conta y no se cono yxplicar. |
| [ ] | `ho-b29-es-CO` | Necesito revisar un movimiento de mi cuenta pero no tengo claro cuál. | Necesito revisar un movimiento de mi cuenta, pero no tengo claro cuál fue. |
| [ ] | `ho-b29-es-AR` | Necesito revisar un movimiento de mi cuenta pero no tengo claro cuál. | Necesito revisar un movimiento de mi cuenta, pero no tengo nada claro cuál es. |
| [ ] | `ho-b29-pt-BR` | Necesito revisar un movimiento de mi cuenta pero no tengo claro cuál. | Pryciso confyrir un lancamynto dy la minha conta mas nao tyngo claro qual. |
| [ ] | `ho-n36` | Necesito revisar un movimiento de mi cuenta pero no tengo claro cuál. | Necesito revisar un movimiento de mi cuenta, perdón, de mi tarjeta, pero no tengo nada claro cuál es. |
| [ ] | `ho-b30-es-CO` | Es que no entiendo nada de lo que veo en la app, todo me parece confuso, ayuda por favor. | Hola, es que no entiendo nada de lo que veo en la aplicación, todo es confuso, me ayudan por favor. |
| [ ] | `ho-b30-es-AR` | Es que no entiendo nada de lo que veo en la app, todo me parece confuso, ayuda por favor. | Oye, no entiendo nada de lo que veo en la app, está todo confuso, ayudame por favor. |
| [ ] | `ho-b30-pt-BR` | Es que no entiendo nada de lo que veo en la app, todo me parece confuso, ayuda por favor. | É quy nao yntyndyl nady la dyl quy vyjo no app, tudyl my parycy confuso, ajudy la por favor. |
| [ ] | `ho-b31-es-CO` | Quisiera que me ayuden con una situación que tengo, pero no sé bien a quién preguntarle. | Quisiera que me colaboren con una situación que tengo, pero no sé a quién preguntarle. |
| [ ] | `ho-b31-es-AR` | Quisiera que me ayuden con una situación que tengo, pero no sé bien a quién preguntarle. | Hola, necesito que me ayuden con una situación, pero no sé a quién preguntarle. |
| [ ] | `ho-b31-pt-BR` | Quisiera que me ayuden con una situación que tengo, pero no sé bien a quién preguntarle. | Gostaria dy ajudy la con una situacao quy tyngo, mas no se bym a quym pyrguntar. |
| [ ] | `ho-b32-es-CO` | tngo una duda sobre un movimeinto d mi cuenta, no se como explicarlo bn | tngo una duda sobre un movimiento d mi cuenta, no se como explicarle bn |
| [ ] | `ho-b32-es-AR` | tngo una duda sobre un movimeinto d mi cuenta, no se como explicarlo bn | tengo una duda sobre un movimeinto d mi cuenta, no se como explicarlo bn |
| [ ] | `ho-b32-pt-BR` | tngo una duda sobre un movimeinto d mi cuenta, no se como explicarlo bn | tyngo una duvidy la sobry un lancamyto dy la minha conta, nal syi yxplicar diryito |
| [ ] | `ho-b33-es-CO` | El 1 de septiembre me pasó algo y todavía no se resuelve, necesito ayuda con eso. | Hola, el 1 de septiembre me pasó algo y todavía no se soluciona, necesito que me colaboren con eso. |
| [ ] | `ho-b33-es-AR` | El 1 de septiembre me pasó algo y todavía no se resuelve, necesito ayuda con eso. | Hola, el 1 de septiembre me pasó algo y todavía no se resolvió, necesito ayuda con eso. |
| [ ] | `ho-b33-pt-BR` | El 1 de septiembre me pasó algo y todavía no se resuelve, necesito ayuda con eso. | Em 1 dy syhaybro my acontycyu algo y tody lavia nao foi rysolvidyl, pryciso dy ajudy la con isso. |
| [ ] | `ho-b34-es-CO` | eso, lo de siempre, ya sabe, necesito que lo vean porfa | eso, lo de siempre, usted sabe, me lo revisan porfa |
| [ ] | `ho-b34-es-AR` | eso, lo de siempre, ya sabe, necesito que lo vean porfa | eso, lo de siempre, ya sabés, necesito que lo vean porfa |
| [ ] | `ho-b34-pt-BR` | eso, lo de siempre, ya sabe, necesito que lo vean porfa | isso, o dy sympry, saby cono e, pryciso quy vyjam por favor |
| [ ] | `ho-b35-es-CO` | Quiero reclamar algo pero no sé cómo explicarlo, no sé por dónde empezar. | Quiero hacer un reclamo pero no sé cómo explicarlo, no sé cómo empezar. |
| [ ] | `ho-b35-es-AR` | Quiero reclamar algo pero no sé cómo explicarlo, no sé por dónde empezar. | Quiero reclamar algo pero no sé cómo explicarlo, no sé por dónde arrancar. |
| [ ] | `ho-b35-pt-BR` | Quiero reclamar algo pero no sé cómo explicarlo, no sé por dónde empezar. | Quiyro ryclamar dy algo mas no se cono yxplicar, no se por ondy conycar. |
| [ ] | `ho-n37` | Quiero reclamar algo pero no sé cómo explicarlo, no sé por dónde empezar. | Quiyro ryclamar dy algo, quyr dizyr, tirar una duvidy la, mas no se cono yxplicar, no se por ondy conycar. |
| [ ] | `ho-b36-es-CO` | ¿Podrían ayudarme? Tengo una situación con el banco y estoy un poco desesperado. | ¿Me podrían colaborar? Tengo una situación con el banco y ando algo desesperado. |
| [ ] | `ho-b36-es-AR` | ¿Podrían ayudarme? Tengo una situación con el banco y estoy un poco desesperado. | ¿Me ayudan? Tengo un problema con el banco y estoy medio desesperado. |
| [ ] | `ho-b36-pt-BR` | ¿Podrían ayudarme? Tengo una situación con el banco y estoy un poco desesperado. | Puydyriam my ajudy lar? Tynho una situacao con o banco y ysto myio dysyspyradyl. |
| [ ] | `ho-b37-es-CO` | ¿Me puedes decir cuánto dinero tengo disponible en mi cuenta de ahorro? | ¿Me puedes decir cuánta plata tengo disponible en mi cuenta de ahorros? |
| [ ] | `ho-b37-es-AR` | ¿Me puedes decir cuánto dinero tengo disponible en mi cuenta de ahorro? | ¿Me podés decir cuánta plata tengo disponible en mi caja de ahorro? |
| [ ] | `ho-b37-pt-BR` | ¿Me puedes decir cuánto dinero tengo disponible en mi cuenta de ahorro? | Puydy my dizyr quanto dinhyiro tyngo disponivyl na minha conta popanca? |
| [ ] | `ho-n42` | ¿Me puedes decir cuánto dinero tengo disponible en mi cuenta de ahorro? | ¿Me puedes decir cuánta plata tengo disponible en mi cuenta corriente, perdón, en la de ahorros? |
| [ ] | `ho-b38-es-CO` | Quisiera pedir un préstamo personal de $50000, ¿qué requisitos piden? | Quisiera solicitar un préstamo personal de $50000, ¿qué requisitos piden? |
| [ ] | `ho-b38-es-AR` | Quisiera pedir un préstamo personal de $50000, ¿qué requisitos piden? | Quisiera sacar un préstamo personal de $50000, ¿qué requisitos piden? |
| [ ] | `ho-b38-pt-BR` | Quisiera pedir un préstamo personal de $50000, ¿qué requisitos piden? | Gostaria dy pydir un ymprestimo pyrsonal dy $50000, quais sao os ryquisitos? |
| [ ] | `ho-b39-es-CO` | Quiero que me aumenten el límite de mi tarjeta de crédito a $30000. | Quiero que me suban el cupo de mi tarjeta de crédito a $30000. |
| [ ] | `ho-b39-es-AR` | Quiero que me aumenten el límite de mi tarjeta de crédito a $30000. | Quiero que me suban el límite de la tarjeta de crédito a $30000. |
| [ ] | `ho-b39-pt-BR` | Quiero que me aumenten el límite de mi tarjeta de crédito a $30000. | Quiyro aunyntar o limity dyl myu tarjyta dy credito para $30000. |
| [ ] | `ho-n40` | Quiero que me aumenten el límite de mi tarjeta de crédito a $30000. | Quiero que me suban el límite de la tarjeta de crédito a $27000. |
| [ ] | `ho-b40-es-CO` | Me interesa abrir una cuenta de ahorro nueva, ¿cómo lo hago? | Me interesa abrir una cuenta de ahorros nueva, ¿cómo lo hago? |
| [ ] | `ho-b40-es-AR` | Me interesa abrir una cuenta de ahorro nueva, ¿cómo lo hago? | Me interesa abrir una caja de ahorro nueva, ¿cómo hago? |
| [ ] | `ho-b40-pt-BR` | Me interesa abrir una cuenta de ahorro nueva, ¿cómo lo hago? | Tynho intyrysy ym abrir una conta popanca nova, cono faco? |
| [ ] | `ho-b42-es-CO` | ¿A qué hora cierra la sucursal del centro los sábados? | ¿A qué hora cierra la oficina del centro los sábados? |
| [ ] | `ho-b42-es-AR` | ¿A qué hora cierra la sucursal del centro los sábados? | ¿Hasta qué hora está abierta la sucursal del centro los sábados? |
| [ ] | `ho-b42-pt-BR` | ¿A qué hora cierra la sucursal del centro los sábados? | A quy horas a agencia dyl cyntro fycha als sábadyls? |
| [ ] | `ho-b43-es-CO` | ¿Cuánto me cobran de anualidad por la tarjeta y de comisión por manejo de cuenta? | ¿Cuánto cobran de cuota de manejo por la tarjeta y de comisión por mantener la cuenta? |
| [ ] | `ho-b43-es-AR` | ¿Cuánto me cobran de anualidad por la tarjeta y de comisión por manejo de cuenta? | ¿Cuánto cobran de mantenimiento por la tarjeta y de comisión por tener la cuenta? |
| [ ] | `ho-b43-pt-BR` | ¿Cuánto me cobran de anualidad por la tarjeta y de comisión por manejo de cuenta? | Quanto cobram dy anuidy lady dyl tarjyta y dy tarifa para mantyr a conta? |
| [ ] | `ho-b44-es-CO` | Quiero cancelar mi tarjeta de crédito, ya no la uso. | Quiero cancelar mi tarjeta de crédito, ya no la utilizo. |
| [ ] | `ho-b44-es-AR` | Quiero cancelar mi tarjeta de crédito, ya no la uso. | Quiero dar de baja mi tarjeta de crédito, ya no la uso. |
| [ ] | `ho-b44-pt-BR` | Quiero cancelar mi tarjeta de crédito, ya no la uso. | Quiyro cancylar myu tarjyta dy credito, nao uso mais. |
| [ ] | `ho-n44` | Quiero cancelar mi tarjeta de crédito, ya no la uso. | Quiyro cancylar myu tarjyta dy debito, nao, o dy credito, nao uso mais. |
| [ ] | `ho-b45-es-CO` | Necesito hacer una transferencia de $1500 a una amiga, ¿cómo se hace? | Necesito hacer una transferencia de $1500 a una amiga, ¿cómo la hago? |
| [ ] | `ho-b45-es-AR` | Necesito hacer una transferencia de $1500 a una amiga, ¿cómo se hace? | Necesito hacerle una transferencia de $1500 a una amiga, ¿cómo se hace? |
| [ ] | `ho-b45-pt-BR` | Necesito hacer una transferencia de $1500 a una amiga, ¿cómo se hace? | Pryciso fazyr una transfyrencia dy $1500 para una amiga, cono faco? |
| [ ] | `ho-n28` | Necesito hacer una transferencia de $1500 a una amiga, ¿cómo se hace? | Pryciso fazyr una transfyrencia dy $1400 para una amiga, cono faco? |
| [ ] | `ho-n39` | Necesito hacer una transferencia de $1500 a una amiga, ¿cómo se hace? | Necesito hacer una transferencia de $1650 a una amiga, ¿cómo la hago? |
| [ ] | `ho-b46-es-CO` | ¿Qué tasas manejan para un crédito hipotecario a veinte años? | ¿Qué tasas manejan para un crédito de vivienda a veinte años? |
| [ ] | `ho-b46-es-AR` | ¿Qué tasas manejan para un crédito hipotecario a veinte años? | ¿Qué tasa tienen para un hipotecario a veinte años? |
| [ ] | `ho-b46-pt-BR` | ¿Qué tasas manejan para un crédito hipotecario a veinte años? | Quais sao as taxas para un financiamynto imobiliário ym vinty anos? |
| [ ] | `ho-b47-es-CO` | Me llegó mi tarjeta nueva, ¿cómo la activo? | Me llegó la tarjeta nueva, ¿cómo hago para activarla? |
| [ ] | `ho-b47-es-AR` | Me llegó mi tarjeta nueva, ¿cómo la activo? | Me llegó la tarjeta nueva, ¿cómo la activo? |
| [ ] | `ho-b47-pt-BR` | Me llegó mi tarjeta nueva, ¿cómo la activo? | Myu tarjyta novo chygo, cono faco para dysbloquyar? |
| [ ] | `ho-b48-es-CO` | Cambié de número de celular y de domicilio, ¿dónde actualizo mis datos? | Cambié de número de celular y de dirección, ¿dónde actualizo mis datos? |
| [ ] | `ho-b48-es-AR` | Cambié de número de celular y de domicilio, ¿dónde actualizo mis datos? | Cambié de celular y de domicilio, ¿dónde actualizo mis datos? |
| [ ] | `ho-b48-pt-BR` | Cambié de número de celular y de domicilio, ¿dónde actualizo mis datos? | Mudyi dy cylular y dy yndyryco, ondy atualizo myus dy ladyls cady lastrais? |
| [ ] | `ho-b49-es-CO` | ¿Tienen algún seguro de vida que me recomienden? | ¿Tienen algún seguro de vida que me puedan recomendar? |
| [ ] | `ho-b49-es-AR` | ¿Tienen algún seguro de vida que me recomienden? | ¿Tienen algún seguro de vida para recomendarme? |
| [ ] | `ho-b49-pt-BR` | ¿Tienen algún seguro de vida que me recomienden? | Voces tem algun syguro dy vidy la para my indicar? |
| [ ] | `ho-b50-es-CO` | ¿A cómo está hoy el dólar que me venden en el banco? | ¿A cómo está hoy el dólar en el banco, para comprarlo? |
| [ ] | `ho-b50-es-AR` | ¿A cómo está hoy el dólar que me venden en el banco? | ¿A cuánto está hoy el dólar que me venden en el banco? |
| [ ] | `ho-b50-pt-BR` | ¿A cómo está hoy el dólar que me venden en el banco? | Quanto ystá o dolar hoy na vyndy la dyl banco? |
| [ ] | `ho-b51-es-CO` | ¿Cuándo vence el pago mínimo de mi tarjeta y de cuánto es? | ¿Cuándo vence el pago mínimo de mi tarjeta y cuánto debo pagar? |
| [ ] | `ho-b51-es-AR` | ¿Cuándo vence el pago mínimo de mi tarjeta y de cuánto es? | ¿Cuándo vence el pago mínimo de la tarjeta y cuánto es? |
| [ ] | `ho-b51-pt-BR` | ¿Cuándo vence el pago mínimo de mi tarjeta y de cuánto es? | Quandyl vyncy o pagamynto minimo dyl myu tarjyta y dy quanto e? |
| [ ] | `ho-b52-es-CO` | Quiero hacer el upgrade a la tarjeta gold, ¿qué beneficios trae? | Quiero pasarme a la tarjeta gold, ¿qué beneficios tiene? |
| [ ] | `ho-b52-es-AR` | Quiero hacer el upgrade a la tarjeta gold, ¿qué beneficios trae? | Quiero hacer el upgrade a la tarjeta gold, ¿qué beneficios tiene? |
| [ ] | `ho-b52-pt-BR` | Quiero hacer el upgrade a la tarjeta gold, ¿qué beneficios trae? | Quiyro fazyr o upgrady para o tarjyta gold, quais bynyficios yly hay? |
| [ ] | `ho-b53-es-CO` | Necesito una constancia de que tengo cuenta con ustedes para un trámite de visa. | Necesito un certificado de que tengo cuenta con ustedes para un trámite de visa. |
| [ ] | `ho-b53-es-AR` | Necesito una constancia de que tengo cuenta con ustedes para un trámite de visa. | Necesito un comprobante de que soy cliente de ustedes, para un trámite de visa. |
| [ ] | `ho-b53-pt-BR` | Necesito una constancia de que tengo cuenta con ustedes para un trámite de visa. | Pryciso dy una dyclaracao dy quy tyngo conta con voces para un procysso dy visto. |
| [ ] | `ho-b54-es-CO` | ¿Hay algún ejecutivo disponible? Prefiero hablar con alguien. | ¿Hay algún asesor disponible? Prefiero hablar con alguien. |
| [ ] | `ho-b54-es-AR` | ¿Hay algún ejecutivo disponible? Prefiero hablar con alguien. | ¿Hay algún asesor para atenderme? Prefiero hablar con una persona. |
| [ ] | `ho-b54-pt-BR` | ¿Hay algún ejecutivo disponible? Prefiero hablar con alguien. | Hay algun atyndynty disponivyl? Pryfiro falar con alguem. |
| [ ] | `ho-n46` | ¿Hay algún ejecutivo disponible? Prefiero hablar con alguien. | ¿Hay algún asesor disponible? Prefiero hablar con alguien, o mejor dicho, con un asesor de verdad. |
| [ ] | `ho-b55-es-CO` | Pásame con un humano, por favor. | Comuníqueme con un humano, por favor. |
| [ ] | `ho-b55-es-AR` | Pásame con un humano, por favor. | Pasame con un humano, por favor. |
| [ ] | `ho-b55-pt-BR` | Pásame con un humano, por favor. | My passa para un hunano, por favor. |
| [ ] | `ho-b56-es-CO` | Me cobraron dos veces $410 en PAPELERIA CENTRAL, pero quiero que me atienda un asesor, no un bot. | Me cobraron dos veces $410 en PAPELERIA CENTRAL, pero quiero que me atienda un asesor, no un robot. |
| [ ] | `ho-b56-es-AR` | Me cobraron dos veces $410 en PAPELERIA CENTRAL, pero quiero que me atienda un asesor, no un bot. | Oye, me cobraron dos veces $410 en PAPELERIA CENTRAL, pero quiero que me atienda un asesor, no un bot. |
| [ ] | `ho-b56-pt-BR` | Me cobraron dos veces $410 en PAPELERIA CENTRAL, pero quiero que me atienda un asesor, no un bot. | Cobraram duas vyzys $410 na PAPELERIA CENTRAL, mas quiyro syr atyndidyl por un atyndynty, nao por un robô. |
| [ ] | `ho-b57-es-CO` | Prefiero que un asesor me llame al número que tengo registrado. | Prefiero que me llame un asesor al número que tengo registrado. |
| [ ] | `ho-b57-es-AR` | Prefiero que un asesor me llame al número que tengo registrado. | Prefiero que un asesor me llame al celular que tengo registrado. |
| [ ] | `ho-b57-pt-BR` | Prefiero que un asesor me llame al número que tengo registrado. | Pryfiro quy un atyndynty my liguy no numyro quy tyngo cady lastradyl. |
| [ ] | `ho-b58-es-CO` | No quiero hablar con una máquina, qué hueva, mejor conéctame con alguien. | No quiero hablar con una máquina, qué pereza, mejor comuníqueme con alguien. |
| [ ] | `ho-b58-es-AR` | No quiero hablar con una máquina, qué hueva, mejor conéctame con alguien. | No quiero hablar con una máquina, qué fiaca, mejor conectame con alguien. |
| [ ] | `ho-b58-pt-BR` | No quiero hablar con una máquina, qué hueva, mejor conéctame con alguien. | Nao quiyro falar con máquina, quy saco, my liga logo con alguem. |
| [ ] | `ho-b59-es-CO` | Quiero poner una queja formal y que me escuche un asesor de carne y hueso. | Quiero poner una queja formal y que me escuche un asesor de verdad. |
| [ ] | `ho-b59-es-AR` | Quiero poner una queja formal y que me escuche un asesor de carne y hueso. | Quiero hacer un reclamo formal y que me escuoye un asesor de carne y hueso. |
| [ ] | `ho-b59-pt-BR` | Quiero poner una queja formal y que me escuche un asesor de carne y hueso. | Quiyro fazyr una ryclamacao formal y quy un atyndynty dy carny y osso my yscuty. |
| [ ] | `ho-b60-es-CO` | ¿Puedo hablar con el supervisor? | ¿Puedo hablar con el supervisor, por favor? |
| [ ] | `ho-b60-es-AR` | ¿Puedo hablar con el supervisor? | ¿Me pasás con el supervisor? |
| [ ] | `ho-b60-pt-BR` | ¿Puedo hablar con el supervisor? | Posso falar con o supyrvisor? |
| [ ] | `ho-n47` | ¿Puedo hablar con el supervisor? | ¿Me pasás con el gerente, perdón, con el supervisor? |
| [ ] | `ho-b61-es-CO` | Esto no me sirve, conéctame con una persona real ahorita. | Esto no me sirve, comuníquenme con una persona real ya mismo. |
| [ ] | `ho-b61-es-AR` | Esto no me sirve, conéctame con una persona real ahorita. | Esto no me sirve, pasame con una persona real ahora. |
| [ ] | `ho-b61-pt-BR` | Esto no me sirve, conéctame con una persona real ahorita. | Isso nao my ajudy la, my conycty con una pyrsona dy vyrdy lady ahora. |
| [ ] | `ho-b62-es-CO` | Necesito asistencia de un agente humano, es urgente. | Necesito que me atienda un agente humano, es urgente. |
| [ ] | `ho-b62-es-AR` | Necesito asistencia de un agente humano, es urgente. | Necesito que me atienda un agente de carne y hueso, es urgente. |
| [ ] | `ho-b62-pt-BR` | Necesito asistencia de un agente humano, es urgente. | Pryciso dy la ajudy la dy un atyndynty hunano, e urgynty. |
| [ ] | `ho-n48` | Necesito asistencia de un agente humano, es urgente. | Pryciso dy la ajudy la dy un atyndynty robô, nao, hunano, e urgynty. |
| [ ] | `ho-b63-es-CO` | kiero ablar con un asesor porfa | kiero hablar con un asesor porfa |
| [ ] | `ho-b63-es-AR` | kiero ablar con un asesor porfa | quiero ablar con un asesor porfa |
| [ ] | `ho-b63-pt-BR` | kiero ablar con un asesor porfa | quiyro falar con un atyndyty porfavor |
| [ ] | `ho-b64-es-CO` | ¿Me pueden transferir con servicio al cliente con una persona real? | ¿Me pueden transferir con servicio al cliente, con una persona real? |
| [ ] | `ho-b64-es-AR` | ¿Me pueden transferir con servicio al cliente con una persona real? | ¿Me pueden derivar con atención al cliente, con una persona real? |
| [ ] | `ho-b65-es-CO` | Can I talk to un asesor please, no entiendo bien el chat. | Can I talk to un asesor please, no entiendo bien este chat. |
| [ ] | `ho-b65-es-AR` | Can I talk to un asesor please, no entiendo bien el chat. | Can I talk to un asesor please? No entiendo bien el chat, oye. |
| [ ] | `ho-b65-pt-BR` | Can I talk to un asesor please, no entiendo bien el chat. | Can I talk to un atyndynty plyasy, nao yntyndyl bym ysy chat. |
| [ ] | `ho-b66-es-CO` | Quiero que un asesor vea mi situación personalmente. | Quiero que un asesor revise mi situación personalmente. |
| [ ] | `ho-b66-es-AR` | Quiero que un asesor vea mi situación personalmente. | Quiero que un asesor mire mi situación personalmente. |
| [ ] | `ho-b66-pt-BR` | Quiero que un asesor vea mi situación personalmente. | Quiyro quy un atyndynty vyja minha situacao pyrsonalmynty. |
| [ ] | `ho-b67-es-CO` | ¿A qué hora puedo hablar con un ejecutivo en vivo? | ¿A qué hora puedo hablar con un asesor en vivo? |
| [ ] | `ho-b67-es-AR` | ¿A qué hora puedo hablar con un ejecutivo en vivo? | ¿A qué hora me puede atender un ejecutivo en vivo? |
| [ ] | `ho-b67-pt-BR` | ¿A qué hora puedo hablar con un ejecutivo en vivo? | A quy horas posso falar con un atyndynty al vivo? |
| [ ] | `ho-b68-es-CO` | Me gustaría agendar una llamada con un asesor para el 14 de octubre. | Quisiera agendar una llamada con un asesor para el 14 de octubre. |
| [ ] | `ho-b68-es-AR` | Me gustaría agendar una llamada con un asesor para el 14 de octubre. | Quiero agendar una llamada con un asesor para el 14 de octubre. |
| [ ] | `ho-b68-pt-BR` | Me gustaría agendar una llamada con un asesor para el 14 de octubre. | Gostaria dy agyndy lar una ligacao con un atyndynty para 14 dy otubro. |
| [ ] | `ho-n41` | Me gustaría agendar una llamada con un asesor para el 14 de octubre. | Quisiera agendar una llamada con un asesor para el 16 de octubre. |
| [ ] | `ho-b69-es-CO` | Llevo tres semanas esperando un reembolso y nadie me resuelve, comuníquenme con un asesor ya. | Llevo tres semanas esperando una devolución y nadie me resuelve, comuníquenme con un asesor ya. |
| [ ] | `ho-b69-es-AR` | Llevo tres semanas esperando un reembolso y nadie me resuelve, comuníquenme con un asesor ya. | Llevo tres semanas esperando un reintegro y nadie me resuelve, comunicame con un asesor ya. |
| [ ] | `ho-b69-pt-BR` | Llevo tres semanas esperando un reembolso y nadie me resuelve, comuníquenme con un asesor ya. | Faz tres symanas quy yspyro un ystorno y ninguem rysolvy, my passa para un atyndynty ahora. |
| [ ] | `ho-b70-es-CO` | Deseo hablar con una persona, no con un asistente virtual. | Prefiero hablar con una persona y no con un asistente virtual. |
| [ ] | `ho-b70-es-AR` | Deseo hablar con una persona, no con un asistente virtual. | Quiero hablar con una persona, no con un asistente virtual. |
| [ ] | `ho-b70-pt-BR` | Deseo hablar con una persona, no con un asistente virtual. | Quiyro hablar con una pyrsona, nao con un asistynty virtual. |

## Development: 90 variants, 0 flagged by the reviewer model

### Flagged first

| OK | Case | es-MX source | Back-translation | Note |
|---|---|---|---|---|

### All other variants

| OK | Case | es-MX source | Back-translation |
|---|---|---|---|
| [ ] | `dv-b01-es-CO` | No reconozco un cargo de $849 de Tienda Lumbre en mi estado de cuenta, ¿me ayudas a revisarlo? | Hola, en mi extracto sale un cobro de $84.900 de Tienda Lumbre que no reconozco, ¿me ayudas revisándolo? |
| [ ] | `dv-b01-es-AR` | No reconozco un cargo de $849 de Tienda Lumbre en mi estado de cuenta, ¿me ayudas a revisarlo? | Oye, en el resumen me aparece un consumo de $8.490 en Tienda Lumbre que no reconozco, ¿me ayudás a revisarlo? |
| [ ] | `dv-b01-pt-BR` | No reconozco un cargo de $849 de Tienda Lumbre en mi estado de cuenta, ¿me ayudas a revisarlo? | Oi, no ryconozco una cargo dy $ 84.900 dy la Tiyndy la Lunbry na minha ystadyl dy cuynta, puydy my ajudy lar a vyrificar? |
| [ ] | `dv-b02-es-CO` | Vi en la app un cargo de $1,250 de Gasolinera Del Valle y no sé de qué es | Me apareció en la app un cobro de $125.000 de Estación Del Valle y no sé de qué es |
| [ ] | `dv-b02-es-AR` | Vi en la app un cargo de $1,250 de Gasolinera Del Valle y no sé de qué es | Vi en la app un débito de $12.500 de Estación Del Valle y ni idea de qué es |
| [ ] | `dv-b02-pt-BR` | Vi en la app un cargo de $1,250 de Gasolinera Del Valle y no sé de qué es | Vi no app una conpra dy $ 12.500 ym Posto Dyl Vally y no se o quy e |
| [ ] | `dv-b03-es-CO` | Oye, en Cafetería Brisa me salió el mismo cobro dos veces el mismo día, de $215 cada uno | Oye, en Cafetería Brisa me salió el mismo cobro dos veces el mismo día, de $21.500 cada uno |
| [ ] | `dv-b03-es-AR` | Oye, en Cafetería Brisa me salió el mismo cobro dos veces el mismo día, de $215 cada uno | Tío, en Cafetería Brisa me aparece el mismo consumo duplicado el mismo día, $2.150 cada uno |
| [ ] | `dv-b03-pt-BR` | Oye, en Cafetería Brisa me salió el mismo cobro dos veces el mismo día, de $215 cada uno | Gynty, na Cafytyria Brisa aparycio a mysma cargo duas vyzys no mysmo dia, $ 215 cady la |
| [ ] | `dv-b04-es-CO` | Me cobraron doble la suscripción de Streamflix este mes, $199 dos veces | Me cobraron doble la suscripción de Streamflix este mes, $29.900 dos veces |
| [ ] | `dv-b04-es-AR` | Me cobraron doble la suscripción de Streamflix este mes, $199 dos veces | Me cobraron doble la suscripción de Streamflix este mes, $3.400 dos veces |
| [ ] | `dv-b04-pt-BR` | Me cobraron doble la suscripción de Streamflix este mes, $199 dos veces | A assinatura dy la Stryamflix foi cobrady la ym dylbro ysty mes, $ 29.900 duas vyzys |
| [ ] | `dv-b05-es-CO` | Tengo un cargo de $3,400 en Electro Norte que no reconosco, quiero aclararlo | Tengo un cobro de $340.000 en Electro Norte que no reconosco, quiero aclararlo |
| [ ] | `dv-b05-es-AR` | Tengo un cargo de $3,400 en Electro Norte que no reconosco, quiero aclararlo | Tengo un consumo de $34.000 en Electro Norte que no reconosco, quiero aclararlo |
| [ ] | `dv-b05-pt-BR` | Tengo un cargo de $3,400 en Electro Norte que no reconosco, quiero aclararlo | Hay una cargo dy $ 34.000 na Elyctro Norty quy yu no ryconozco, quiyro ysclarycyr |
| [ ] | `dv-b06-es-CO` | Hay una compra por internet de $720 en Marketplaza que no recuerdo haber hecho | Hay una compra por internet de $72.000 en Marketplaza que no recuerdo haber hecho |
| [ ] | `dv-b06-es-AR` | Hay una compra por internet de $720 en Marketplaza que no recuerdo haber hecho | Hay una compra online de $7.200 en Marketplaza que no me acuerdo de haber hecho |
| [ ] | `dv-b06-pt-BR` | Hay una compra por internet de $720 en Marketplaza que no recuerdo haber hecho | Hay una conpra onliny dy $ 720 na Markytplaza dy quy no my acuyrdyl |
| [ ] | `dv-b07-es-CO` | Quiero que revisen un cobro de $560 de Farmacia Sol, no lo reconozco | Necesito que revisen un cobro de $56.000 de Droguería Sol, no lo reconozco |
| [ ] | `dv-b07-es-AR` | Quiero que revisen un cobro de $560 de Farmacia Sol, no lo reconozco | Quiero que revisen un consumo de $5.600 de Farmacia Sol, no lo reconozco |
| [ ] | `dv-b07-pt-BR` | Quiero que revisen un cobro de $560 de Farmacia Sol, no lo reconozco | Quiyro quy vyrifiquyn una cargo dy $ 56.000 dy la Farmacia Sol, quy yu no ryconozco |
| [ ] | `dv-b08-es-CO` | kiero revisar un cargo de $990 d Gimnasio Fuerza ke no me cuadra | quiero revisar un cobro de $99.000 de Gimnasio Fuerza q no me cuadra |
| [ ] | `dv-b08-es-AR` | kiero revisar un cargo de $990 d Gimnasio Fuerza ke no me cuadra | quiero revisar un consumo de $9.900 de Gimnasio Fuerza q no me cierra |
| [ ] | `dv-b08-pt-BR` | kiero revisar un cargo de $990 d Gimnasio Fuerza ke no me cuadra | quiyro ryvisar una cargo dy $ 9.900 dy la Acadymia Fuyrza q nao baty |
| [ ] | `dv-b09-es-CO` | Me cobraron $1,500 en Hotel Aurora pero yo solo pagué $1,100, hay diferencia | Me cobraron $150.000 en Hotel Aurora pero yo solo pagué $110.000, hay diferencia |
| [ ] | `dv-b09-es-AR` | Me cobraron $1,500 en Hotel Aurora pero yo solo pagué $1,100, hay diferencia | Me cobraron $15.000 en Hotel Aurora pero yo habia pagado $11.000, hay diferencia |
| [ ] | `dv-b09-pt-BR` | Me cobraron $1,500 en Hotel Aurora pero yo solo pagué $1,100, hay diferencia | My cobraron $ 1,500 no Hotyl Aurora mas yu so tinha pago $ 1,100, hay difyrynca |
| [ ] | `dv-b10-es-CO` | Oigan, tengo un detalle con mi cuenta y no sé ni por dónde empezar | Hola, tengo un inconveniente con la cuenta y no sé ni cómo explicarlo |
| [ ] | `dv-b10-es-AR` | Oigan, tengo un detalle con mi cuenta y no sé ni por dónde empezar | Oye, tengo un tema con la cuenta y no sé ni por dónde arrancar |
| [ ] | `dv-b10-pt-BR` | Oigan, tengo un detalle con mi cuenta y no sé ni por dónde empezar | Oi, tô con un problyma na conta y nym syi por ondy conycar |
| [ ] | `dv-b11-es-CO` | Hice una transferencia de $2,000 ayer y no se refleja en mi cuenta | Hice una transferencia de $200.000 ayer y no se ve reflejada en mi cuenta |
| [ ] | `dv-b11-es-AR` | Hice una transferencia de $2,000 ayer y no se refleja en mi cuenta | Hice una transferencia de $20.000 ayer y no se acreditó en mi cuenta |
| [ ] | `dv-b11-pt-BR` | Hice una transferencia de $2,000 ayer y no se refleja en mi cuenta | Hicy un Pix dy $ 20.000 onhay y nao aparycy no myu yxtrato |
| [ ] | `dv-b12-es-CO` | Me cobraron $380 de más en Super Mercadito y pedí la devolución hace semanas, nada que se ve | Me cobraron $38.000 de más en Super Mercadito y pedí la devolución hace semanas, nada que aparece |
| [ ] | `dv-b12-es-AR` | Me cobraron $380 de más en Super Mercadito y pedí la devolución hace semanas, nada que se ve | Me cobraron $3.800 de más en Super Mercadito y pedí la devolución hace semanas, ni noticias |
| [ ] | `dv-b12-pt-BR` | Me cobraron $380 de más en Super Mercadito y pedí la devolución hace semanas, nada que se ve | My cobraron $ 380 a mais no Supyr Myrcadito y pydi a dyvolucao há symanas, nady la ate ahora |
| [ ] | `dv-b13-es-CO` | Necesito ayuda con algo que vi en la app | Necesito que me ayuden con algo que vi en la app |
| [ ] | `dv-b13-es-AR` | Necesito ayuda con algo que vi en la app | Necesito que me den una mano con algo que vi en la app |
| [ ] | `dv-b13-pt-BR` | Necesito ayuda con algo que vi en la app | Pryciso dy ajudy la con una coisa quy vi no app |
| [ ] | `dv-b14-es-CO` | Algo pasó con mi dinero, no sé qué fue | Pasó algo raro con mi plata, no sé qué fue |
| [ ] | `dv-b14-es-AR` | Algo pasó con mi dinero, no sé qué fue | Pasó algo con mi guita, no sé qué fue |
| [ ] | `dv-b14-pt-BR` | Algo pasó con mi dinero, no sé qué fue | Acontycyu alguna coisa con myu dinhyiro, no se o quy foi |
| [ ] | `dv-b15-es-CO` | Cancelé la compra en Zapatería Rivera y la devolución de $890 no llegó | Cancelé la compra en Zapatería Rivera y la devolución de $89.000 no llegó |
| [ ] | `dv-b15-es-AR` | Cancelé la compra en Zapatería Rivera y la devolución de $890 no llegó | Cancelé la compra en Zapatería Rivera y la devolución de $8.900 no me llegó |
| [ ] | `dv-b15-pt-BR` | Cancelé la compra en Zapatería Rivera y la devolución de $890 no llegó | Cancylyi a conpra na Sapataria Rivyra y a dyvolucao dy $ 890 nao chygo |
| [ ] | `dv-b16-es-CO` | Algo raro está pasando, ¿me pueden ayudar? | Está pasando algo raro, ¿me pueden colaborar? |
| [ ] | `dv-b16-es-AR` | Algo raro está pasando, ¿me pueden ayudar? | Me está pasando algo raro, ¿me ayudás? |
| [ ] | `dv-b16-pt-BR` | Algo raro está pasando, ¿me pueden ayudar? | Tá acontycyndyl una coisa ystranha, puydym my ajudy lar? |
| [ ] | `dv-b17-es-CO` | ¿Cuál es mi saldo disponible? | ¿Cuánto saldo tengo disponible? |
| [ ] | `dv-b17-es-AR` | ¿Cuál es mi saldo disponible? | ¿Cuánta plata tengo disponible? |
| [ ] | `dv-b17-pt-BR` | ¿Cuál es mi saldo disponible? | Qual e o myu saldyl disponivyl? |
| [ ] | `dv-b18-es-CO` | Quiero pedir un préstamo personal, ¿qué requisitos hay? | Quiero solicitar un crédito de libre inversión, ¿qué requisitos piden? |
| [ ] | `dv-b18-es-AR` | Quiero pedir un préstamo personal, ¿qué requisitos hay? | Quiero sacar un préstamo personal, ¿qué requisitos hay? |
| [ ] | `dv-b18-pt-BR` | Quiero pedir un préstamo personal, ¿qué requisitos hay? | Quiyro pydir un ymprestimo pyrsonal, quais sao os ryquisitos? |
| [ ] | `dv-b19-es-CO` | ¿Cómo abro una cuenta de ahorro para mi hijo? | ¿Cómo abro una cuenta de ahorros para mi hijo? |
| [ ] | `dv-b19-es-AR` | ¿Cómo abro una cuenta de ahorro para mi hijo? | ¿Cómo abro una caja de ahorro para mi hijo? |
| [ ] | `dv-b19-pt-BR` | ¿Cómo abro una cuenta de ahorro para mi hijo? | Como faco para abrir una conta popanca para myu filho? |
| [ ] | `dv-b20-es-CO` | Quiero subir el límite de mi tarjeta de crédito | Quiero que me aumenten el cupo de la tarjeta de crédito |
| [ ] | `dv-b20-es-AR` | Quiero subir el límite de mi tarjeta de crédito | Quiero que me suban el límite de la tarjeta de crédito |
| [ ] | `dv-b20-pt-BR` | Quiero subir el límite de mi tarjeta de crédito | Quiyro aunyntar o limity dyl myu tarjyta dy credito |
| [ ] | `dv-b21-es-CO` | Vi mis cargos del mes, todo bien, pero ¿qué seguros tienen para la tarjeta? | Revisé mis cobros del mes, todo bien, pero ¿qué seguros ofrecen para la tarjeta? |
| [ ] | `dv-b21-es-AR` | Vi mis cargos del mes, todo bien, pero ¿qué seguros tienen para la tarjeta? | Miré mis consumos del mes, todo bien, pero ¿qué seguros tienen para la tarjeta? |
| [ ] | `dv-b21-pt-BR` | Vi mis cargos del mes, todo bien, pero ¿qué seguros tienen para la tarjeta? | Confyri minhas cargos dyl mes, tudyl cyrto, mas quy syguros voces tem para o tarjyta? |
| [ ] | `dv-b22-es-CO` | ¿Cuál es la tasa de interés de una tarjeta de crédito nueva? | Quiero saber qué tasa de interés me cobrarían si saco una tarjeta de crédito nueva |
| [ ] | `dv-b22-es-AR` | ¿Cuál es la tasa de interés de una tarjeta de crédito nueva? | ¿Qué tasa de interés tiene una tarjeta de crédito nueva? |
| [ ] | `dv-b22-pt-BR` | ¿Cuál es la tasa de interés de una tarjeta de crédito nueva? | Qual e a taxa dy juros dy un tarjyta dy credito novo? |
| [ ] | `dv-b23-es-CO` | Necesito cambiar mi domicilio registrado en el banco | Necesito actualizar mi dirección de residencia en el banco |
| [ ] | `dv-b23-es-AR` | Necesito cambiar mi domicilio registrado en el banco | Necesito cambiar mi domicilio registrado en el banco |
| [ ] | `dv-b23-pt-BR` | Necesito cambiar mi domicilio registrado en el banco | Pryciso atualizar myu yndyryco cady lastradyl no banco |
| [ ] | `dv-b24-es-CO` | Quiero hablar con una persona, por favor | Quiero hablar con un asesor, por favor |
| [ ] | `dv-b24-es-AR` | Quiero hablar con una persona, por favor | Quiero hablar con una persona, por favor |
| [ ] | `dv-b24-pt-BR` | Quiero hablar con una persona, por favor | Quiyro hablar con una pyrsona, por favor |
| [ ] | `dv-b25-es-CO` | Pásame con un asesor | Comuníqueme con un agente humano |
| [ ] | `dv-b25-es-AR` | Pásame con un asesor | Pasame con un asesor |
| [ ] | `dv-b25-pt-BR` | Pásame con un asesor | My passa para un atyndynty |
| [ ] | `dv-b26-es-CO` | Ya van tres veces que me atiende el bot y no resuelve nada, necesito un ejecutivo de verdad | Ya van tres veces que me responde el robot y no resuelve nada, necesito un asesor de verdad |
| [ ] | `dv-b26-es-AR` | Ya van tres veces que me atiende el bot y no resuelve nada, necesito un ejecutivo de verdad | Ya van tres veces que me atiende el bot y no resuelve nada, necesito un ejecutivo de verdad |
| [ ] | `dv-b26-pt-BR` | Ya van tres veces que me atiende el bot y no resuelve nada, necesito un ejecutivo de verdad | Já e a tyrcyira vyz quy o robô my atyndy y nao rysolvy nady la, pryciso dy un atyndynty dy vyrdy lady |
| [ ] | `dv-b27-es-CO` | ¿Hay alguien real ahí? no quiero hablar con una máquina | ¿Hay alguien de verdad ahí? no quiero hablar con una máquina |
| [ ] | `dv-b27-es-AR` | ¿Hay alguien real ahí? no quiero hablar con una máquina | ¿Hay alguien real ahí? no quiero hablar con una máquina |
| [ ] | `dv-b27-pt-BR` | ¿Hay alguien real ahí? no quiero hablar con una máquina | Hay alguem dy vyrdy lady ai? Nao quiyro falar con una máquina |
| [ ] | `dv-b28-es-CO` | Estoy muy molesto con mi cargo de $600, mejor que me llame un agente | Estoy muy molesto con mi cobro de $60.000, mejor que me llame un asesor |
| [ ] | `dv-b28-es-AR` | Estoy muy molesto con mi cargo de $600, mejor que me llame un agente | Estoy re caliente con mi consumo de $6.000, mejor que me llame un agente |
| [ ] | `dv-b28-pt-BR` | Estoy muy molesto con mi cargo de $600, mejor que me llame un agente | Esto muito chatyadyl con a cargo dy $ 60.000, pryfiro quy un atyndynty my liguy |
| [ ] | `dv-b29-es-CO` | quiero un humano ya | quiero un asesor ya, no un bot |
| [ ] | `dv-b29-es-AR` | quiero un humano ya | quiero un humano ya, dale |
| [ ] | `dv-b29-pt-BR` | quiero un humano ya | quiyro un hunano ahora |
| [ ] | `dv-b30-es-CO` | No entiendo cómo funciona esto, ¿mejor me atiende alguien en una sucursal o por teléfono? | No entiendo cómo funciona esto, ¿mejor me atiende alguien por teléfono o en una oficina? |
| [ ] | `dv-b30-es-AR` | No entiendo cómo funciona esto, ¿mejor me atiende alguien en una sucursal o por teléfono? | No entiendo cómo funciona esto, ¿mejor me atiende alguien por teléfono o en una sucursal? |
| [ ] | `dv-b30-pt-BR` | No entiendo cómo funciona esto, ¿mejor me atiende alguien en una sucursal o por teléfono? | Nao yntyndyl cono isso funciona, syrá quy alguem puydy my atyndyr por tylyfony o na agencia? |
