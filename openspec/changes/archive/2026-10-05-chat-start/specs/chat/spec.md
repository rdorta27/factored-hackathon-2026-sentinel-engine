## ADDED Requirements

### Requirement: Openers get a friendly reply

A message read as `missing` with an opener subtype (greeting, thanks, goodbye, identity, help), or found as an opener by the code fallback, SHALL get a reply that answers it and says what the assistant can do, and SHALL NOT hand off. A greeting followed by a request SHALL keep the request. Traces to REQ-0002 (P0, Done) and REQ-0012 (P0, Done).

#### Scenario: Greeting alone

- **WHEN** the first message is "hola"
- **THEN** the reply greets the customer and says that it can review charges, and no handoff is filed

#### Scenario: Greeting with a request

- **WHEN** the message is "hola, no reconozco un cargo de Cafe Central"
- **THEN** the loop treats it as a charge request

### Requirement: Charge status is answered without a case

A message read as `status` SHALL get the status, date and dispute eligibility of the verified charge, and SHALL NOT open a confirm box. Traces to REQ-0003 (P0, Done) and REQ-0043 (P1, Done).

#### Scenario: Status of the last charge

- **WHEN** the customer asks for the status of the last charge
- **THEN** the reply gives that charge's status and eligibility, and no box opens

### Requirement: Slots narrow only verified candidates

Merchant words, an amount, a date phrase and a "twice" flag, from the router or from the code parsers, SHALL narrow the verified candidates only. A slot that matches no candidate SHALL be dropped. Traces to REQ-0002 (P0, Done) and REQ-0003 (P0, Done).

#### Scenario: One thousand in words

- **WHEN** the customer writes "un cobro de mil pesos" and a 1,000 charge exists
- **THEN** the loop shows that charge

#### Scenario: A slot with no match

- **WHEN** the amount slot matches no candidate
- **THEN** no charge is selected by it and the reply says what was searched

### Requirement: Why for a named charge

A question about why a named charge cannot be disputed SHALL be answered from the policy rule and its values. Traces to REQ-0029 (P1, Done).

#### Scenario: Charge outside the window

- **WHEN** the customer asks "¿por qué no puedo reclamar el de enero?" and that charge is outside the window
- **THEN** the reply gives the window, the charge date and the last eligible date

### Requirement: Model words only on turns that do not decide

A reply MAY carry a `text` from the model draft only on a turn that does not decide, and only after the draft passes the validator, with every value filled from verified facts. A confirm box, a case confirmation, a policy refusal, a handoff and an error SHALL use templates. Traces to REQ-0003 (P0, Done) and REQ-0005 (P0, Done); decision 024.

#### Scenario: Rejected draft

- **WHEN** the validator rejects a draft
- **THEN** the reply uses a template variant and the turn record names the reason
