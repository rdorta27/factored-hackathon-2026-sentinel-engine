---
language: en
style: ASD-STE100
last_reviewed: 2026-10-05
---

# Human check of 20 sealed labels (task 3.3)

This page checks 20 sealed labels against the case text. The reviewer is a
team member who did not write the cases. The cases are model-written
(decision 018). The sealed set is `eval/cases/sealed/held_out.jsonl`.

How to check:

1. Read the customer text of each row.
2. Compare it with the sealed label.
3. Write `agree` or `disagree` in the last column.
4. Write a short reason when you disagree.
5. Add the total agreement at the end.

| # | Case id | Variant | Customer text | Sealed label | Reviewer verdict |
|---|---|---|---|---|---|
| 1 | `ho-a32` | es-419 | Necesito ver los cargos de mi hermano, él me dio permiso, se llama Andrés. | `out_of_scope` | agree |
| 2 | `ho-a68` | es-419 | Me figura un cargo de $690 de PANADERIA SUR del 27 de septiembre que no reconozco. | `charge` | agree |
| 3 | `ho-b06-pt-BR` | pt-BR | Na fatura tem uma compra de $950 no posto GASOLINERA ORIENTE de 20 de agosto que não reconheço. | `charge` | agree |
| 4 | `ho-b08-es-AR` | es-AR | En FARMACIA SOL me cobraron $780 pero el ticket que tengo es de $380, el cargo está mal. | `charge` | agree |
| 5 | `ho-b14-pt-BR` | pt-BR | São só $99, mas aparece JUEGOSPLAY na minha fatura e não sei o que é, não reconheço. | `charge` | agree |
| 6 | `ho-b20-es-MX` | es-MX | Oye, el 5 de agosto pasó algo con mi cuenta y desde entonces ando preocupado, ¿me ayudan? | `missing` | agree |
| 7 | `ho-b22-pt-BR` | pt-BR | Preciso de ajuda com algo que me aconteceu em 10 de setembro, é longo de contar. | `missing` | agree |
| 8 | `ho-b23-es-AR` | es-AR | Hola, necesito ayuda con una cosa. | `missing` | agree |
| 9 | `ho-b36-es-MX` | es-MX | ¿Podrían ayudarme? Tengo una situación con el banco y estoy un poco desesperado. | `missing` | agree |
| 10 | `ho-b39-es-AR` | es-AR | Quiero que me suban el límite de la tarjeta de crédito a $30000. | `out_of_scope` | agree |
| 11 | `ho-b47-es-AR` | es-AR | Me llegó la tarjeta nueva, ¿cómo la activo? | `out_of_scope` | agree |
| 12 | `ho-b52-pt-BR` | pt-BR | Quero fazer o upgrade para o cartão gold, quais benefícios ele tem? | `out_of_scope` | agree |
| 13 | `ho-b53-es-MX` | es-MX | Necesito una constancia de que tengo cuenta con ustedes para un trámite de visa. | `out_of_scope` | agree |
| 14 | `ho-b54-es-CO` | es-CO | ¿Hay algún asesor disponible? Prefiero hablar con alguien. | `person` | agree |
| 15 | `ho-b61-es-CO` | es-CO | Esto no me sirve, comuníquenme con una persona real ya mismo. | `person` | agree |
| 16 | `ho-b66-es-AR` | es-AR | Quiero que un asesor mire mi situación personalmente. | `person` | agree |
| 17 | `ho-b67-es-AR` | es-AR | ¿A qué hora me puede atender un ejecutivo en vivo? | `person` | agree |
| 18 | `ho-b68-es-AR` | es-AR | Quiero agendar una llamada con un asesor para el 14 de octubre. | `person` | agree |
| 19 | `ho-n17` | es-CO | El PARQUEADERO CENT me cobró $120 tres veces por una sola salida, qué desorden. | `charge` | agree |
| 20 | `ho-n23` | pt-BR | Desde 22 de setembro tenho um problema com a minha conta e não sei como explicar. | `missing` | agree |

## Agreement

| Field | Value |
|---|---|
| Cases checked | 20 |
| Agree | 20 |
| Disagree | 0 |
| Agreement share | 1.0 |
| Reviewer | Rubén |
| Date | 2026-10-05 |

## Limits

- The check covers 20 of 405 sealed cases.
- The reviewer is not a native speaker of every variant.
- This is not an LLM judge, so REQ-0023 stays not applicable.
- The reviewer noted that the phrase `no reconozco` is understandable, but it is not the most common wording in Colombia. The Spanish cases repeat one phrasing across the three countries. A country-adapted wording needs a new sealed block under a new hash.
