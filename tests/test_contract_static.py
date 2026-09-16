from pathlib import Path

SOURCE = (Path(__file__).resolve().parents[1] / "contracts" / "RunbookDriftGate.py").read_text(encoding="utf-8")


def test_fetch_digest_and_consensus_are_on_critical_path():
    assert 'gl.nondet.web.request(url, method="GET")' in SOURCE
    assert "hashlib.sha256(baseline_bytes).hexdigest()" in SOURCE
    assert "hashlib.sha256(candidate_bytes).hexdigest()" in SOURCE
    assert "gl.vm.run_nondet_unsafe" in SOURCE
    assert "gl.eq_principle.strict_eq" not in SOURCE


def test_arbitrary_urls_and_payments_are_absent():
    assert "raw.githubusercontent.com/" in SOURCE
    assert "gl.message.value" not in SOURCE
    assert "emit_transfer" not in SOURCE


def test_versioned_lineage_surface_is_present():
    for method in ("open_lineage", "propose_revision", "assess_revision", "promote_revision",
                   "dismiss_revision", "cancel_pending", "get_lineage", "get_revision"):
        assert f"def {method}(" in SOURCE
