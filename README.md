# Evaluation Claim Gate

A reusable GenLayer Intelligent Contract for verifying public benchmark claims
against independent evidence. A publisher registers a model ID, a claim source,
an independent evidence source, a benchmark name, the claimed score in basis
points, and a tolerance. Anyone can trigger an assessment.

Validators independently fetch both sources and compare whether each source
supports the claim. Deterministic contract code returns `VERIFIED`,
`REVIEW_REQUIRED`, or `REJECTED`.

## Decision policy

| Condition | Decision |
| --- | --- |
| The benchmark is absent or sources conflict | `REVIEW_REQUIRED` |
| Both sources support the claimed score | `VERIFIED` |
| The claim source supports the score but independent evidence does not | `REJECTED` |
| The claim source itself does not support the score | `REVIEW_REQUIRED` |

## Contract interface

| Method | Type | Purpose |
| --- | --- | --- |
| `register_claim(model_id, claim_url, evidence_url, benchmark, claimed_score_bps, tolerance_bps)` | write | Register a claim and its evidence |
| `assess(model_id)` | write | Fetch both sources through validator consensus |
| `withdraw(model_id)` | write | Publisher-only withdrawal |
| `is_verified(model_id)` | view | Boolean signal for procurement or listing |
| `get_assessment(model_id)` | view | Full public assessment record |
| `policy_catalog()` | view | Expose the fixed decision codes |

## Why GenLayer

Benchmark claims are live, unstructured, and frequently copied from vendor
marketing pages. A static allowlist cannot notice when a claim source changes or
when independent evidence disagrees. This gate makes the evidence reads, the
validator comparison, and the final policy decision public and reproducible.

## Local verification

```shell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
genvm-lint check contracts/eval_claim_gate.py
pytest tests/direct/ -q
```

## License

MIT
