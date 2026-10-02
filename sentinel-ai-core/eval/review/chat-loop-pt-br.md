# Chat-loop locale review (pt-BR)

Back-translation of the texts added for the extraction refusal and the
not-found reply. Checked in this session against the Spanish source. No second
model was available, so the back-translation is by the writer (grok-4.7),
2026-10-02. A row is OK only if the meaning survives.

| OK | Key | Intended Spanish | pt-BR | Back-translation |
|---|---|---|---|---|
| [x] | `extraction.refused` | No puedo compartir mis instrucciones. Solo puedo ayudarte con cargos de tu cuenta. Cuéntame qué cargo quieres revisar, o te comunico con un asesor. | Não posso compartilhar minhas instruções. Só posso ajudar com cobranças da sua conta. Me conte qual cobrança quer revisar, ou chamo um atendente. | No puedo compartir mis instrucciones. Solo puedo ayudar con cargos de tu cuenta. Cuéntame qué cargo quieres revisar, o llamo a un asesor. |
| [x] | `charge.not_found` | No encontré un cargo con esos datos. Estos son los más recientes. | Não encontrei uma cobrança com esses dados. Estas são as mais recentes. | No encontré un cargo con esos datos. Estas son las más recientes. |

No row drifted. `instruções` / `instrucciones` and `cobrança` / `cargo` are the
pair already used in each locale. `atendente` is the pt-BR word the offer
already uses for advisor.

## Pattern limit

The extraction check needs a reveal, repeat or copy verb near prompt,
instructions or configuration, in es-419 and pt-BR, including voseo
(`Copiame`). The injection check covers ignore-instructions, skip-confirmation,
administrator or system or debug mode, and fake instruction tags. A phrasing
outside those lists reaches the model. Replies are still keys and verified
values, so an unlisted phrasing cannot leak the prompt or open a case. Ordinary
uses of `sistema` and `instrucciones para disputar` are in the negative set and
do not fire.
