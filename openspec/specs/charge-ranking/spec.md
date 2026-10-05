# charge-ranking Specification

## Purpose
TBD - created by archiving change charge-ranker. Update Purpose after archive.

## Requirements

### Requirement: A learned selector ranks the customer's charges

A model SHALL score each charge of the session customer against the description of the customer, and SHALL rank the charges. It SHALL read clues computed by deterministic parsers. It SHALL pick a charge alone only when the model is sure. Otherwise the loop SHALL show the short list and ask. The confirm box and the policy SHALL not change. Traces to REQ-0002 (P0, Done), REQ-0003 (P0, Done) and REQ-0016 (P0, Done).

#### Scenario: The model is sure

- **WHEN** the top charge passes the threshold
- **THEN** the loop shows that charge in the confirm box

#### Scenario: The model is not sure

- **WHEN** no charge passes the threshold
- **THEN** the loop shows the short list and asks which one

### Requirement: The comparison is fair and the splits are safe

The evidence SHALL compare the current rules, the rules after `chat-start`, the learned selector and the language-model reading on the same held-out set. Training customers SHALL not appear in the test set. The test set SHALL be later in time than training and validation. Calibration SHALL use the train split only, and the threshold SHALL use the validation split only. New phrasing families SHALL appear only in the test set. The test set SHALL be measured once. Traces to REQ-0016 (P0, Done), REQ-0017 (P0, Done) and REQ-0020 (P0, Done).

#### Scenario: No customer in two splits

- **WHEN** the splits are frozen
- **THEN** a test checks that no customer id is in more than one split

#### Scenario: Evaluation cannot train

- **WHEN** the evaluation module is imported
- **THEN** it does not import the training module

### Requirement: The model file is locked

The run SHALL store the hash of the model file, the seed, the family list and the threshold. The service SHALL refuse to load a model file whose hash differs from the one in the run. Traces to REQ-0019 (P1, Done) and REQ-0028 (P0, Done).

#### Scenario: A changed model file

- **WHEN** the model file differs from the recorded hash
- **THEN** the service refuses to load it and reports the reason

### Requirement: Serving is off until the rule passes

The service SHALL not use the selector unless `SENTINEL_CHARGE_RANKER` is on. The switch SHALL turn on by default only if the selector has no more wrong automatic picks than the rules on the held-out set, ranks the right charge first more often than the rules, and the owner approves. Traces to REQ-0006 (P0, Done) and REQ-0033 (P0, Done).

#### Scenario: Switch off

- **WHEN** the switch is off
- **THEN** the replies are identical to the replies without the selector
