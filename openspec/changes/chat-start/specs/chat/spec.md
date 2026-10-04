## ADDED Requirements

### Requirement: Openers get a friendly reply

When the router labels a message `missing` and the message is a greeting, thanks, a goodbye or a question about the assistant, the reply SHALL greet or answer, SHALL say what the assistant can do, and SHALL NOT hand off. Traces to REQ-0002 (P0, Done) and REQ-0012 (P0, Done).

#### Scenario: Greeting alone

- **WHEN** the first message is "hola"
- **THEN** the reply greets the customer and says that it can review charges, and no handoff is filed

#### Scenario: Greeting with a request

- **WHEN** the message is "hola, no reconozco un cargo de Cafe Central"
- **THEN** the loop treats it as a charge request

### Requirement: Charge status is answered without a case

A message labelled `status` SHALL get the status, date and dispute eligibility of the verified charge, and SHALL NOT open a confirm box. Traces to REQ-0003 (P0, Done) and REQ-0043 (P1, Done).

#### Scenario: Status of the last charge

- **WHEN** the customer asks for the status of the last charge
- **THEN** the reply gives that charge's status and eligibility, and no box opens

### Requirement: Why for a named charge

A question about why a named charge cannot be disputed SHALL be answered from the policy rule and its values. Traces to REQ-0029 (P1, Done).

#### Scenario: Charge outside the window

- **WHEN** the customer asks "¿por qué no puedo reclamar el de enero?" and that charge is outside the window
- **THEN** the reply gives the window, the charge date and the last eligible date

### Requirement: Amounts in words ground a charge

The narrowing SHALL read amounts written in words in es-419 and pt-BR. A parsed amount SHALL count only when it matches a verified candidate. Traces to REQ-0002 (P0, Done) and REQ-0003 (P0, Done).

#### Scenario: One thousand in words

- **WHEN** the customer writes "un cobro de mil pesos" and a 1,000 charge exists
- **THEN** the loop shows that charge
