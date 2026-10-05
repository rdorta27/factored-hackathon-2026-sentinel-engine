## ADDED Requirements

### Requirement: A filed handoff does not block new requests

After a handoff, the loop SHALL answer a message about the same case with the reference of its ticket, and SHALL process a request about another charge as a new request. The reason of a filed ticket SHALL NOT change. Traces to REQ-0001 (P0, Done) and REQ-0008 (P0, Done).

#### Scenario: Same case after a handoff

- **WHEN** a ticket exists for a charge and the customer writes about that charge again
- **THEN** the reply says that the case is with an advisor and gives the ticket reference

#### Scenario: Another charge after a handoff

- **WHEN** a ticket exists and the customer names a different eligible charge
- **THEN** the loop shows that charge in a confirm box

#### Scenario: Another charge after two requests for an advisor

- **WHEN** the customer asked twice for an advisor, and then names a different eligible charge
- **THEN** the policy does not apply the `person.insist` rule, and the loop continues the normal flow with that charge

#### Scenario: A third request for an advisor escalates

- **WHEN** the customer asked twice for an advisor, wrote about another charge, and then asks for an advisor again
- **THEN** the policy returns the handoff outcome with the rule `person.insist`

### Requirement: A dispute-status question never opens a case

A deterministic check before the model SHALL recognize a question about the status of an existing dispute in es-419 and pt-BR. The reply SHALL come from the cases of the session customer, or SHALL say that no case exists. The loop SHALL NOT open a case on this question. Traces to REQ-0003 (P0, Done) and REQ-0006 (P0, Done).

#### Scenario: Status of an open dispute

- **WHEN** the customer has an open dispute and asks "¿en qué va mi disputa?"
- **THEN** the reply gives the case reference and its status, and no case is created

### Requirement: A correction replaces the confirm box

With a confirm box open, a message that grounds a different candidate SHALL close the box and SHALL show the new candidate. A confirmation SHALL open only the candidate of the box that the customer saw. Traces to REQ-0006 (P0, Done).

#### Scenario: The customer corrects the amount

- **WHEN** the box shows the 1,000 charge and the customer writes "no, el de 700"
- **THEN** the box shows the 700 charge, and a confirmation opens the 700 charge

### Requirement: An open dispute is reported before the box

The loop SHALL tell the customer that a charge already has an open dispute before it shows a confirm box for that charge, and SHALL NOT show the box. Traces to REQ-0043 (P1, Done).

#### Scenario: Charge with an open dispute

- **WHEN** the customer selects a charge with an open dispute
- **THEN** the reply says that the charge already has a dispute, and no box opens
