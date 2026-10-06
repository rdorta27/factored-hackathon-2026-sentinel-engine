# decision-explanation Specification

## Purpose

Answers a why follow-up from the last stored policy decision, with the rule and the verified values used then, never from the model or the customer's words.

## Requirements

### Requirement: The last decision is remembered per thread

The system SHALL keep, for each conversation, the last policy decision it showed the customer: the `rule_id`, the candidate it was about, the policy file version and a snapshot of the verified values it used. The snapshot SHALL come from the policy file and the verified candidate, never from the model or the customer's words. The record SHALL be replaced by each new decision and SHALL be deleted with the conversation on logout or expiry. A conversation saved before this field existed SHALL load with no last decision. Traces to REQ-0033 (P0, Done), REQ-0001 (P0, Done) and REQ-0027 (P0, Done).

#### Scenario: A refused charge is remembered

- **WHEN** the policy refuses a charge with `window.expired`
- **THEN** the conversation holds that rule, the charge and its date, and the window in force

#### Scenario: A newer decision replaces the older

- **WHEN** a second charge is refused for another rule
- **THEN** only the second decision is held

#### Scenario: Old stored conversations still load

- **WHEN** a conversation stored without the field is read
- **THEN** it loads with no last decision and no error

### Requirement: A why follow-up is answered from the stored decision

When a last decision exists and the customer's message asks the reason for it, the system SHALL answer from that stored decision and SHALL NOT evaluate the policy again, look up charges, change the candidate list or count the turn as a new request. Recognition SHALL be deterministic and SHALL be active only while a last decision exists. A message that asks a reason and also names a charge SHALL be treated as a new request. The model SHALL NOT be called for the follow-up. Traces to REQ-0033 (P0, Done) and REQ-0006 (P0, Done).

#### Scenario: Why after a refused charge

- **WHEN** a charge was refused with `window.expired` and the customer asks on what the refusal is based
- **THEN** the reply is an explanation of that decision and the charge list is not shown again

#### Scenario: The same decision is explained as it was made

- **WHEN** the policy file changes after the decision and the customer asks why
- **THEN** the explanation states the values stored with the decision

#### Scenario: Why with no decision

- **WHEN** the customer asks why before any decision exists in the conversation
- **THEN** the reply says what the service can do and states no rule

#### Scenario: A reason question that names a charge is a new request

- **WHEN** the customer asks why while naming another charge
- **THEN** the message is processed as a charge request

### Requirement: Window and status rules explain their rule and values

For `window.expired`, `status.pending`, `status.reversed`, `status.declined` and `already.disputed` the explanation SHALL state the rule that applied and the verified values it used. For `window.expired` those values SHALL be the window in days read from the country file, the charge date, the last eligible date and the number of days between them and the reference date. When the country file is marked synthetic, the explanation SHALL say that the rule is a demonstration policy of the service and not a bank's rule. No customer text SHALL carry the window as a number written in a locale file. Traces to REQ-0033 (P0, Done) and REQ-0030 (P0, Done).

#### Scenario: Window explanation uses the file's value

- **WHEN** `window.expired` is explained for a country whose file sets `window_days` to a given number
- **THEN** the reply carries that number, the charge date and the last eligible date

#### Scenario: Demonstration label is shown

- **WHEN** the country file is synthetic
- **THEN** the explanation says the rule is a demonstration policy

#### Scenario: Locale files hold no window number

- **WHEN** the locale files are checked
- **THEN** no explanation text contains the window as a written number

### Requirement: Safety rules answer with a fixed sentence

For `amount.high`, `fraud.score` and `fraud.claim` the explanation SHALL be one fixed sentence saying that an advisor reviews the case. It SHALL NOT contain a threshold, a score, an amount limit, the word fraud, or any value that would let repeated questions infer the criterion. The same sentence SHALL be returned for all three rules. Traces to REQ-0006 (P0, Done), REQ-0007 (P0, Done) and REQ-0033 (P0, Done); decisions 010 and 011.

#### Scenario: High amount does not reveal the limit

- **WHEN** a charge was handed off for `amount.high` and the customer asks why
- **THEN** the reply says an advisor reviews it and states no limit

#### Scenario: Fraud rules look alike

- **WHEN** the customer asks why after `fraud.score` and after `fraud.claim`
- **THEN** both replies are the same sentence and neither names fraud or a score

#### Scenario: Probing does not leak

- **WHEN** the customer asks repeatedly what amount or score triggers the review
- **THEN** every reply is the same fixed sentence and records no unsafe outcome
