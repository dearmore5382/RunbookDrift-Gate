from pathlib import Path
import hashlib
import importlib
import json
import sys
from unittest.mock import patch

from gltest.direct import VMContext, create_address, deploy_contract

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "RunbookDriftGate.py"
COMMIT_A = "a" * 40
COMMIT_B = "b" * 40
DIGEST_A = "1" * 64
DIGEST_B = "2" * 64
POLICY = "Preserve rollback, post-action verification and incident escalation; do not broaden hazardous targets."


def deploy():
    curator, outsider = create_address("curator"), create_address("outsider")
    vm = VMContext(curator)
    with patch("os.unlink", lambda _path: None):
        with vm.activate():
            contract = deploy_contract(CONTRACT, vm)
            proxy = contract._instance.open_lineage.__globals__["gl"]
            _ = proxy.nondet
            _ = proxy.vm
    sdk_root = str(Path(proxy._cached_gl.__file__).resolve().parents[2])
    if sdk_root not in sys.path:
        sys.path.insert(0, sdk_root)
    importlib.import_module("genlayer")
    return vm, contract, curator, outsider


def sync(vm, contract):
    proxy = contract._instance.open_lineage.__globals__["gl"]
    sdk_root = str(Path(proxy._cached_gl.__file__).resolve().parents[2])
    if sdk_root not in sys.path:
        sys.path.insert(0, sdk_root)
    if "genlayer" not in sys.modules:
        importlib.invalidate_caches()
        importlib.import_module("genlayer")
    message = proxy.message
    sender = vm.sender
    if isinstance(sender, bytes):
        sender = type(message.sender_address)(sender)
    proxy._cached_gl.message = message._replace(sender_address=sender, origin_address=sender,
                                                 value=type(message.value)(vm.value))
    proxy._cached_gl.message_raw["sender_address"] = sender
    proxy._cached_gl.message_raw["origin_address"] = sender


def restore_validator_modules(contract):
    proxy = contract._instance.open_lineage.__globals__["gl"]
    if "genlayer" not in sys.modules:
        importlib.invalidate_caches()
        importlib.import_module("genlayer")
    genlayer_module = sys.modules["genlayer"]
    genlayer_module.gl = proxy._cached_gl
    sys.modules["genlayer.gl"] = proxy._cached_gl
    sys.modules["genlayer.gl.vm"] = proxy._cached_gl.vm


def remove_validator_modules():
    sys.modules.pop("genlayer.gl.vm", None)
    sys.modules.pop("genlayer.gl", None)


def open_lineage(vm, contract):
    with vm.activate():
        sync(vm, contract)
        return contract.open_lineage("Payments API recovery", "example-org", "operations", COMMIT_A,
                                     "runbooks/payments.md", DIGEST_A, POLICY)


def observation(**changes):
    result = {"source_status": "VERIFIED", "baseline_sha256": DIGEST_A,
              "candidate_sha256": DIGEST_B, "rollback_preserved": "YES",
              "verification_preserved": "YES", "escalation_preserved": "YES",
              "dangerous_scope_expanded": "NO", "operational_meaning_changed": "NO"}
    result.update(changes)
    return result


def assess(vm, contract, revision, result):
    with vm.activate(), patch.object(contract._instance, "_consensus", return_value=result):
        sync(vm, contract)
        return contract.assess_revision(revision)


def test_locator_validation_authority_pending_and_cancel():
    vm, contract, _, outsider = deploy()
    with vm.activate():
        sync(vm, contract)
        assert contract.open_lineage("x", "bad/owner", "repo", COMMIT_A, "a.md", DIGEST_A, POLICY) == "INVALID_REPOSITORY"
        assert contract.open_lineage("x", "owner", "repo", "main", "a.md", DIGEST_A, POLICY) == "INVALID_BASELINE_LOCATOR"
        assert contract.open_lineage("x", "owner", "repo", COMMIT_A, "../a.md", DIGEST_A, POLICY) == "INVALID_BASELINE_LOCATOR"
    lineage = open_lineage(vm, contract)
    with vm.prank(outsider):
        sync(vm, contract)
        assert contract.propose_revision(lineage, COMMIT_B, "runbooks/v2.md", DIGEST_B) == "CURATOR_ONLY"
    with vm.activate():
        sync(vm, contract)
        revision = contract.propose_revision(lineage, COMMIT_B, "runbooks/v2.md", DIGEST_B)
        assert contract.propose_revision(lineage, "c" * 40, "runbooks/v3.md", "3" * 64) == "REVISION_NOT_PROPOSABLE"
    with vm.prank(outsider):
        sync(vm, contract)
        assert contract.cancel_pending(revision) == "CURATOR_ONLY"
    with vm.activate():
        sync(vm, contract)
        assert contract.cancel_pending(revision) == "REVISION_CANCELLED"
        assert contract.cancel_pending(revision) == "REVISION_NOT_CANCELLABLE"


def test_safe_revision_promotes_and_creates_new_generation():
    vm, contract, _, _ = deploy()
    lineage = open_lineage(vm, contract)
    with vm.activate():
        sync(vm, contract)
        revision = contract.propose_revision(lineage, COMMIT_B, "runbooks/v2.md", DIGEST_B)
        assert contract.promote_revision(revision) == "REVISION_NOT_PROMOTABLE"
    assert assess(vm, contract, revision, observation()) == "SAFE_REVISION"
    with vm.activate():
        sync(vm, contract)
        assert contract.assess_revision(revision) == "REVISION_NOT_ASSESSABLE"
        assert contract.promote_revision(revision) == "BASELINE_PROMOTED"
        lineage_state = json.loads(contract.get_lineage(lineage))
        assert lineage_state["generation"] == 1
        assert lineage_state["baseline_commit"] == COMMIT_B
        assert lineage_state["baseline_sha256"] == DIGEST_B
        assert json.loads(contract.get_revision(revision))["status"] == "PROMOTED"


def test_all_semantic_outcomes_and_fail_closed_promotion():
    cases = [
        (observation(rollback_preserved="NO", operational_meaning_changed="YES"), "SAFETY_REGRESSION"),
        (observation(verification_preserved="NO"), "SAFETY_REGRESSION"),
        (observation(escalation_preserved="NO"), "SAFETY_REGRESSION"),
        (observation(dangerous_scope_expanded="YES", operational_meaning_changed="YES"), "SCOPE_EXPANSION"),
        (observation(rollback_preserved="UNCLEAR"), "UNCLEAR"),
        (observation(source_status="INTEGRITY_FAILURE", rollback_preserved="UNCLEAR",
                     verification_preserved="UNCLEAR", escalation_preserved="UNCLEAR",
                     dangerous_scope_expanded="UNCLEAR", operational_meaning_changed="UNCLEAR"), "INTEGRITY_FAILURE"),
    ]
    for result, expected in cases:
        vm, contract, _, _ = deploy()
        lineage = open_lineage(vm, contract)
        with vm.activate():
            sync(vm, contract)
            revision = contract.propose_revision(lineage, COMMIT_B, "runbooks/v2.md", DIGEST_B)
        assert assess(vm, contract, revision, result) == expected
        with vm.activate():
            sync(vm, contract)
            assert contract.promote_revision(revision) == "REVISION_NOT_PROMOTABLE"
            assert contract.dismiss_revision(revision) == "REVISION_DISMISSED"
            assert json.loads(contract.get_revision(revision))["verdict"] == expected


def test_source_unavailable_is_retryable_without_state_mutation():
    vm, contract, _, _ = deploy()
    lineage = open_lineage(vm, contract)
    with vm.activate():
        sync(vm, contract)
        revision = contract.propose_revision(lineage, COMMIT_B, "runbooks/v2.md", DIGEST_B)
        before = contract.get_revision(revision)
    unavailable = observation(source_status="SOURCE_UNAVAILABLE", rollback_preserved="UNCLEAR",
                              verification_preserved="UNCLEAR", escalation_preserved="UNCLEAR",
                              dangerous_scope_expanded="UNCLEAR", operational_meaning_changed="UNCLEAR",
                              baseline_sha256="", candidate_sha256="")
    assert assess(vm, contract, revision, unavailable) == "ASSESSMENT_RETRYABLE"
    with vm.activate():
        sync(vm, contract)
        assert contract.get_revision(revision) == before


def test_url_is_constructed_from_validated_components():
    vm, contract, _, _ = deploy()
    raw_url = contract._instance.open_lineage.__globals__["_raw_url"]
    assert raw_url("example-org", "operations", COMMIT_A.upper(), "runbooks/payments.md") == (
        "https://raw.githubusercontent.com/example-org/operations/" + COMMIT_A + "/runbooks/payments.md")


def test_observer_hashes_exact_fetched_bytes_before_llm():
    vm, contract, _, _ = deploy()
    globals_ = contract._instance.open_lineage.__globals__
    observe = globals_["_observe"]
    proxy = globals_["gl"]
    baseline = b"rollback and verify\n"
    candidate = b"restore the previous release and confirm health\n"
    expected_a = hashlib.sha256(baseline).hexdigest()
    expected_b = hashlib.sha256(candidate).hexdigest()
    semantic = {"rollback_preserved": "YES", "verification_preserved": "YES",
                "escalation_preserved": "YES", "dangerous_scope_expanded": "NO",
                "operational_meaning_changed": "NO"}
    with vm.activate(), patch.dict(globals_, {"_fetch": lambda url: baseline if url == "base" else candidate}), \
            patch.object(proxy.nondet, "exec_prompt", return_value=semantic):
        result = observe("base", expected_a, "candidate", expected_b, POLICY)
    assert result["source_status"] == "VERIFIED"
    assert result["baseline_sha256"] == expected_a
    assert result["candidate_sha256"] == expected_b


def test_observer_accepts_fixed_position_semantic_tokens():
    vm, contract, _, _ = deploy()
    globals_ = contract._instance.open_lineage.__globals__
    baseline, candidate = b"baseline", b"candidate"
    proxy = globals_["gl"]
    with vm.activate(), patch.dict(globals_, {"_fetch": lambda url: baseline if url == "base" else candidate}), \
            patch.object(proxy.nondet, "exec_prompt", return_value="YES|YES|YES|NO|NO"):
        result = globals_["_observe"]("base", hashlib.sha256(baseline).hexdigest(), "candidate",
                                      hashlib.sha256(candidate).hexdigest(), POLICY)
    assert result["source_status"] == "VERIFIED"
    assert result["rollback_preserved"] == "YES"


def test_observer_rejects_extra_semantic_token():
    vm, contract, _, _ = deploy()
    globals_ = contract._instance.open_lineage.__globals__
    content = b"document"
    proxy = globals_["gl"]
    with vm.activate(), patch.dict(globals_, {"_fetch": lambda _url: content}), \
            patch.object(proxy.nondet, "exec_prompt", return_value="YES|YES|YES|NO|NO|SAFE_REVISION"):
        result = globals_["_observe"]("base", hashlib.sha256(content).hexdigest(), "candidate",
                                      hashlib.sha256(content).hexdigest(), POLICY)
    assert result["source_status"] == "SOURCE_UNAVAILABLE"


def test_observer_rejects_prose_wrapped_semantic_line():
    vm, contract, _, _ = deploy()
    globals_ = contract._instance.open_lineage.__globals__
    content = b"document"
    proxy = globals_["gl"]
    with vm.activate(), patch.dict(globals_, {"_fetch": lambda _url: content}), \
            patch.object(proxy.nondet, "exec_prompt", return_value="Assessment:\nYES|YES|YES|NO|NO"):
        result = globals_["_observe"]("base", hashlib.sha256(content).hexdigest(), "candidate",
                                      hashlib.sha256(content).hexdigest(), POLICY)
    assert result["source_status"] == "SOURCE_UNAVAILABLE"


def test_full_public_happy_path_fetches_hashes_revalidates_and_promotes():
    vm, contract, _, _ = deploy()
    baseline = b"Stop on error. Roll back the release. Verify health. Escalate to incident command.\n"
    candidate = b"Stop on error. Restore the prior release. Confirm health. Escalate to incident command.\n"
    baseline_digest = hashlib.sha256(baseline).hexdigest()
    candidate_digest = hashlib.sha256(candidate).hexdigest()
    baseline_commit = "a" * 40
    candidate_commit = "b" * 40
    baseline_url = ("https://raw.githubusercontent.com/example-org/operations/" + baseline_commit +
                    "/runbooks/payments.md")
    candidate_url = ("https://raw.githubusercontent.com/example-org/operations/" + candidate_commit +
                     "/runbooks/payments-v2.md")
    vm.clear_mocks()
    vm.mock_web(baseline_url, {"status": 200, "body": baseline})
    vm.mock_web(candidate_url, {"status": 200, "body": candidate})
    vm.mock_llm(r"(?s).*pipe-delimited line.*Evidence:.*", "YES|YES|YES|NO|YES")
    with vm.activate():
        sync(vm, contract)
        lineage = contract.open_lineage("Payments API recovery", "example-org", "operations",
                                        baseline_commit, "runbooks/payments.md", baseline_digest, POLICY)
        revision = contract.propose_revision(lineage, candidate_commit, "runbooks/payments-v2.md",
                                             candidate_digest)
        assert contract.assess_revision(revision) == "SAFE_REVISION"
        receipt = json.loads(contract.get_revision(revision))
        observed = json.loads(receipt["observation"])
        assert observed["baseline_sha256"] == baseline_digest
        assert observed["candidate_sha256"] == candidate_digest
        assert receipt["status"] == "ASSESSED"
        restore_validator_modules(contract)
        assert vm.run_validator() is True
        assert contract.promote_revision(revision) == "BASELINE_PROMOTED"
        lineage_state = json.loads(contract.get_lineage(lineage))
        assert lineage_state["generation"] == 1
        assert lineage_state["baseline_commit"] == candidate_commit
        assert lineage_state["baseline_sha256"] == candidate_digest
    remove_validator_modules()


def test_full_public_failure_path_blocks_digest_substitution_before_llm():
    vm, contract, _, _ = deploy()
    baseline = b"authenticated baseline\n"
    candidate = b"substituted candidate bytes\n"
    commit_a, commit_b = "a" * 40, "b" * 40
    url_a = "https://raw.githubusercontent.com/example-org/operations/" + commit_a + "/baseline.md"
    url_b = "https://raw.githubusercontent.com/example-org/operations/" + commit_b + "/candidate.md"
    vm.clear_mocks()
    vm.mock_web(url_a, {"status": 200, "body": baseline})
    vm.mock_web(url_b, {"status": 200, "body": candidate})
    vm.mock_llm(r".*", "YES|YES|YES|NO|NO")
    with vm.activate():
        sync(vm, contract)
        lineage = contract.open_lineage("Digest guard", "example-org", "operations", commit_a,
                                        "baseline.md", hashlib.sha256(baseline).hexdigest(), POLICY)
        revision = contract.propose_revision(lineage, commit_b, "candidate.md", "0" * 64)
        assert contract.assess_revision(revision) == "INTEGRITY_FAILURE"
        receipt = json.loads(contract.get_revision(revision))
        observed = json.loads(receipt["observation"])
        assert observed["candidate_sha256"] == hashlib.sha256(candidate).hexdigest()
        assert receipt["verdict"] == "INTEGRITY_FAILURE"
        assert contract.promote_revision(revision) == "REVISION_NOT_PROMOTABLE"


def test_validator_rejects_consequential_model_disagreement():
    vm, contract, _, _ = deploy()
    baseline = b"Roll back, verify health, and escalate.\n"
    candidate = b"Restore, verify health, and escalate.\n"
    commit_a, commit_b = "a" * 40, "b" * 40
    url_a = "https://raw.githubusercontent.com/example-org/operations/" + commit_a + "/baseline.md"
    url_b = "https://raw.githubusercontent.com/example-org/operations/" + commit_b + "/candidate.md"
    vm.clear_mocks()
    vm.mock_web(url_a, {"status": 200, "body": baseline})
    vm.mock_web(url_b, {"status": 200, "body": candidate})
    vm.mock_llm(r".*", "YES|YES|YES|NO|NO")
    with vm.activate():
        sync(vm, contract)
        lineage = contract.open_lineage("Consensus guard", "example-org", "operations", commit_a,
                                        "baseline.md", hashlib.sha256(baseline).hexdigest(), POLICY)
        revision = contract.propose_revision(lineage, commit_b, "candidate.md",
                                             hashlib.sha256(candidate).hexdigest())
        assert contract.assess_revision(revision) == "SAFE_REVISION"
    vm.clear_mocks()
    vm.mock_web(url_a, {"status": 200, "body": baseline})
    vm.mock_web(url_b, {"status": 200, "body": candidate})
    vm.mock_llm(r".*", "NO|YES|YES|NO|YES")
    with vm.activate():
        sync(vm, contract)
        restore_validator_modules(contract)
        assert vm.run_validator() is False
    remove_validator_modules()


def test_digest_mismatch_blocks_semantic_prompt():
    vm, contract, _, _ = deploy()
    globals_ = contract._instance.open_lineage.__globals__
    proxy = globals_["gl"]
    with vm.activate(), patch.dict(globals_, {"_fetch": lambda _url: b"actual bytes"}), \
            patch.object(proxy.nondet, "exec_prompt") as prompt:
        result = globals_["_observe"]("base", "0" * 64, "candidate", "0" * 64, POLICY)
    assert result["source_status"] == "INTEGRITY_FAILURE"
    prompt.assert_not_called()


def test_fetch_returns_exact_response_bytes_and_checks_runtime_status_field():
    vm, contract, _, _ = deploy()
    globals_ = contract._instance.open_lineage.__globals__
    url = "https://raw.githubusercontent.com/example-org/operations/" + COMMIT_A + "/runbooks/payments.md"
    class Response:
        status = 200
        body = b"exact raw bytes\n"
    with vm.activate(), patch.object(globals_["gl"].nondet.web, "request", return_value=Response()):
        assert globals_["_fetch"](url) == b"exact raw bytes\n"
