# Recorded fixtures (offline replay)

One online run recorded these responses; each file was reviewed for personal
data before commit. File name: `<prompt_version>-<input_hash>.json`, where the
hash covers the normalized message. Each file stores `prompt_version`,
`input_hash`, the generic input, the understanding result, and token/cost
figures. Tests and the evaluation runner replay them with `FixtureTransport`
and open no network connection.

Fixtures carrying `"generator": "keyword-baseline-mirror"` were derived from
the keyword baseline, not a live model: the router Delta in a run using them
is zero by construction, and the report says so. They are replaced by recorded
model responses once a live model is configured (decision 010).
