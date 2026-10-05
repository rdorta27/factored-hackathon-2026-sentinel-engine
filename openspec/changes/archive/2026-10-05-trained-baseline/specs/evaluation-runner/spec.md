## ADDED Requirements

### Requirement: A trained baseline is a measured version

The runner SHALL measure a `trained_baseline` version: a TF-IDF and logistic regression model trained on the development split only and tuned on the validation split only. Training SHALL refuse a held-out case. The training run SHALL be frozen with its split ids, its parameter and the hash of the model file. Traces to REQ-0016 (P0, Done), REQ-0017 (P0, Done) and REQ-0019 (P1, Done).

#### Scenario: Held-out case in training

- **WHEN** a held-out case id reaches the training data
- **THEN** training stops with an error that names the case

#### Scenario: Reproducible model

- **WHEN** `verify` retrains on the frozen split ids
- **THEN** the model hash is the same as in the frozen run

### Requirement: Precision and recall per intent

The runner summary SHALL report accuracy, precision, recall and F1 per intent for every version, with intervals from the cluster bootstrap over bases. Traces to REQ-0022 (P0, Done).

#### Scenario: Metrics per intent

- **WHEN** a run finishes
- **THEN** its summary has precision, recall and F1 for each intent and each version
