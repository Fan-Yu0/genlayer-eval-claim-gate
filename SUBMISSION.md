# Portal submission draft

## Category

Builder -> Intelligent Contract

## Description (English, under 1,000 characters)

Evaluation Claim Gate is a reusable GenLayer primitive for verifying public AI benchmark claims against independent evidence. A publisher registers a model ID, claim source, independent evidence source, benchmark name, claimed score in basis points, and tolerance. Anyone can trigger an assessment. Validators independently fetch both sources and compare whether each source supports the claim. Deterministic contract code verifies a supported claim, rejects a claim contradicted by independent evidence, and requires review when the benchmark is absent or the sources conflict. Other contracts can consume `is_verified(model_id)`. The repository includes source, tests, deployment instructions, and a live example for model marketplaces, procurement, leaderboards, and agent registries.

## Live evidence

- Public source repository: https://github.com/Fan-Yu0/genlayer-eval-claim-gate
- Contract: `0x6F720E0DA299b66dDD298A8e3188063A8b78f3Db`
- Deployment transaction: `0xd25d3e73675af68bd10106cd4b51cbbfe21a9588cf1b756ec1e9d409982f6977`
- Assessment transaction: `0x4b3cdd90c40817d239949dba40026df600b4baa9107b64bf4e0f0a2d9ad22162`

## First live example

```text
model_id: google/gemma-2-9b-it
claim_url: https://huggingface.co/google/gemma-2-9b-it
evidence_url: https://arxiv.org/html/2408.00118
benchmark: MMLU
claimed_score_bps: 7130
tolerance_bps: 50
```

Then call `assess("google/gemma-2-9b-it")`.

## Reviewer checklist

- Persistent state and a clear lifecycle.
- Publisher-only registration and withdrawal.
- Permissionless evidence refresh.
- Validator independently re-fetches both sources.
- The LLM extracts only constrained evidence.
- The final decision is deterministic.
- Missing or conflicting evidence fails closed.
- Source, tests, documentation, and deployment instructions are public.
