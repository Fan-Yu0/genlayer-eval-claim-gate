import json


MODEL_ID = "google/gemma-2-9b-it"
CLAIM_URL = "https://claims.example.com/gemma"
EVIDENCE_URL = "https://papers.example.com/gemma"
BENCHMARK = "MMLU"
SCORE_BPS = 7130
TOLERANCE_BPS = 50


def _mock_evidence(vm, payload):
    vm.mock_web(
        r".*claims\.example\.com/gemma.*",
        {"status": 200, "body": "Gemma 2 9B reports MMLU 71.3."},
    )
    vm.mock_web(
        r".*papers\.example\.com/gemma.*",
        {"status": 200, "body": "The technical report lists MMLU 71.3."},
    )
    vm.mock_llm(r".*EVALUATION CLAIM VERIFICATION.*", json.dumps(payload))


def _evidence(
    claim=True,
    evidence=True,
    present=True,
    consistency="consistent",
    summary="Both sources report MMLU 71.3.",
):
    return {
        "claim_supported": claim,
        "evidence_supported": evidence,
        "benchmark_present": present,
        "source_consistency": consistency,
        "summary": summary,
    }


def _register(contract, vm, publisher):
    vm.sender = publisher
    contract.register_claim(
        MODEL_ID,
        CLAIM_URL,
        EVIDENCE_URL,
        BENCHMARK,
        SCORE_BPS,
        TOLERANCE_BPS,
    )


def test_verified_when_both_sources_support_claim(
    direct_vm, direct_deploy, direct_alice
):
    contract = direct_deploy("contracts/eval_claim_gate.py")
    _register(contract, direct_vm, direct_alice)
    _mock_evidence(direct_vm, _evidence())

    contract.assess(MODEL_ID)

    result = contract.get_assessment(MODEL_ID)
    assert result["state"] == 1
    assert result["decision"] == 1
    assert result["claim_supported"] is True
    assert result["evidence_supported"] is True
    assert result["benchmark_present"] is True
    assert result["round"] == 1
    assert contract.is_verified(MODEL_ID) is True


def test_rejected_when_independent_evidence_does_not_support_claim(
    direct_vm, direct_deploy, direct_alice
):
    contract = direct_deploy("contracts/eval_claim_gate.py")
    _register(contract, direct_vm, direct_alice)
    _mock_evidence(direct_vm, _evidence(evidence=False))

    contract.assess(MODEL_ID)

    result = contract.get_assessment(MODEL_ID)
    assert result["decision"] == 3
    assert result["claim_supported"] is True
    assert result["evidence_supported"] is False
    assert contract.is_verified(MODEL_ID) is False


def test_review_when_claim_source_missing(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/eval_claim_gate.py")
    _register(contract, direct_vm, direct_alice)
    _mock_evidence(direct_vm, _evidence(claim=False))

    contract.assess(MODEL_ID)

    assert contract.get_assessment(MODEL_ID)["decision"] == 2


def test_review_when_benchmark_missing(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/eval_claim_gate.py")
    _register(contract, direct_vm, direct_alice)
    _mock_evidence(direct_vm, _evidence(present=False))

    contract.assess(MODEL_ID)

    assert contract.get_assessment(MODEL_ID)["decision"] == 2


def test_conflicting_sources_require_review(
    direct_vm, direct_deploy, direct_alice
):
    contract = direct_deploy("contracts/eval_claim_gate.py")
    _register(contract, direct_vm, direct_alice)
    _mock_evidence(direct_vm, _evidence(consistency="conflicting"))

    contract.assess(MODEL_ID)

    assert contract.get_assessment(MODEL_ID)["decision"] == 2


def test_insufficient_sources_require_review(
    direct_vm, direct_deploy, direct_alice
):
    contract = direct_deploy("contracts/eval_claim_gate.py")
    _register(contract, direct_vm, direct_alice)
    _mock_evidence(direct_vm, _evidence(consistency="insufficient"))

    contract.assess(MODEL_ID)

    assert contract.get_assessment(MODEL_ID)["decision"] == 2


def test_duplicate_registration_is_rejected(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/eval_claim_gate.py")
    _register(contract, direct_vm, direct_alice)

    with direct_vm.expect_revert("already registered"):
        contract.register_claim(
            MODEL_ID, CLAIM_URL, EVIDENCE_URL, BENCHMARK, SCORE_BPS, TOLERANCE_BPS
        )


def test_requires_https_urls(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/eval_claim_gate.py")
    direct_vm.sender = direct_alice

    with direct_vm.expect_revert("claim_url must be an https URL"):
        contract.register_claim(
            MODEL_ID,
            "http://claims.example.com/gemma",
            EVIDENCE_URL,
            BENCHMARK,
            SCORE_BPS,
            TOLERANCE_BPS,
        )


def test_evidence_urls_must_differ(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/eval_claim_gate.py")
    direct_vm.sender = direct_alice

    with direct_vm.expect_revert("evidence URLs must differ"):
        contract.register_claim(
            MODEL_ID, CLAIM_URL, CLAIM_URL, BENCHMARK, SCORE_BPS, TOLERANCE_BPS
        )


def test_score_and_tolerance_are_bounded(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/eval_claim_gate.py")
    direct_vm.sender = direct_alice

    with direct_vm.expect_revert("claimed_score_bps"):
        contract.register_claim(
            MODEL_ID, CLAIM_URL, EVIDENCE_URL, BENCHMARK, 10001, TOLERANCE_BPS
        )

    with direct_vm.expect_revert("tolerance_bps"):
        contract.register_claim(
            MODEL_ID, CLAIM_URL, EVIDENCE_URL, BENCHMARK, SCORE_BPS, 2001
        )


def test_only_publisher_can_withdraw(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = direct_deploy("contracts/eval_claim_gate.py")
    _register(contract, direct_vm, direct_alice)

    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("only the publisher can withdraw"):
        contract.withdraw(MODEL_ID)

    direct_vm.sender = direct_alice
    contract.withdraw(MODEL_ID)
    assert contract.get_assessment(MODEL_ID)["state"] == 2
    assert contract.is_verified(MODEL_ID) is False


def test_unknown_model_is_not_verified(direct_deploy):
    contract = direct_deploy("contracts/eval_claim_gate.py")

    assert contract.is_verified("unknown") is False
    assert contract.get_assessment("unknown") == {}


def test_validator_accepts_matching_evidence(
    direct_vm, direct_deploy, direct_alice
):
    contract = direct_deploy("contracts/eval_claim_gate.py")
    _register(contract, direct_vm, direct_alice)
    _mock_evidence(direct_vm, _evidence())
    contract.assess(MODEL_ID)

    assert direct_vm.run_validator() is True


def test_validator_rejects_changed_claim_support(
    direct_vm, direct_deploy, direct_alice
):
    contract = direct_deploy("contracts/eval_claim_gate.py")
    _register(contract, direct_vm, direct_alice)
    _mock_evidence(direct_vm, _evidence(claim=True))
    contract.assess(MODEL_ID)

    direct_vm.clear_mocks()
    _mock_evidence(direct_vm, _evidence(claim=False))

    assert direct_vm.run_validator() is False


def test_validator_rejects_changed_evidence_support(
    direct_vm, direct_deploy, direct_alice
):
    contract = direct_deploy("contracts/eval_claim_gate.py")
    _register(contract, direct_vm, direct_alice)
    _mock_evidence(direct_vm, _evidence(evidence=True))
    contract.assess(MODEL_ID)

    direct_vm.clear_mocks()
    _mock_evidence(direct_vm, _evidence(evidence=False))

    assert direct_vm.run_validator() is False


def test_validator_rejects_changed_benchmark_presence(
    direct_vm, direct_deploy, direct_alice
):
    contract = direct_deploy("contracts/eval_claim_gate.py")
    _register(contract, direct_vm, direct_alice)
    _mock_evidence(direct_vm, _evidence(present=True))
    contract.assess(MODEL_ID)

    direct_vm.clear_mocks()
    _mock_evidence(direct_vm, _evidence(present=False))

    assert direct_vm.run_validator() is False


def test_validator_ignores_summary_wording(
    direct_vm, direct_deploy, direct_alice
):
    contract = direct_deploy("contracts/eval_claim_gate.py")
    _register(contract, direct_vm, direct_alice)
    _mock_evidence(direct_vm, _evidence(summary="Leader wording."))
    contract.assess(MODEL_ID)

    direct_vm.clear_mocks()
    _mock_evidence(direct_vm, _evidence(summary="Different validator wording."))

    assert direct_vm.run_validator() is True


def test_policy_catalog_exposes_codes(direct_deploy):
    contract = direct_deploy("contracts/eval_claim_gate.py")

    policy = contract.policy_catalog()
    assert policy["policy_version"] == "eval-claim-v1"
    assert policy["verified"] == 1
    assert policy["review_required"] == 2
    assert policy["rejected"] == 3
