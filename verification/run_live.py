"""Checkpointed StudioNet Raw GitHub lifecycle; signed writes are never automatically retried."""
import base64
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from genlayer_py import create_account, create_client
from genlayer_py.abi import calldata
from genlayer_py.abi.transactions import serialize
from genlayer_py.chains import studionet

ROOT = Path(__file__).resolve().parents[1]
ADDRESS = "0xf902855724f6a9Fe63D77A672C53180921b320d0"
RPC = "https://studio.genlayer.com/api"
SOURCE_HASH = "141363acdcc907a5b13e5a4ce129e5c0ec6b56967f18e1d0466904df28c02334"
OWNER, REPO = "dearmore5382", "RunbookDrift-Gate"
COMMIT = "53c6627541a052413f0bf7c1241603b97fec4ba9"
BASE = "1d91d09725536e5e8bf5fead2d1f600b5edff537e38dfe00a5adbb72b1174b3b"
SAFE = "790b0f0c9cad9e541a3b77b4672ef5c1b03701f7771b710d7409956c05166106"
UNSAFE = "6577ac41831eb71b519199af69c0af7c4304612a4ea3c58daf3bf25cda3c8072"
POLICY = "Preserve rollback, post-action verification and incident escalation; do not broaden hazardous targets."
PRIVATE = ROOT / ".private" / ("live-" + ADDRESS.lower() + ".json")
PUBLIC = ROOT / "verification" / ("live-" + ADDRESS.lower() + ".json")
TEST_ENV = ROOT.parent / "DAOProposalContextVerifier" / ".env.lifecycle"


def rpc(method, params):
    last = None
    for attempt in range(5):
        try:
            response = requests.post(RPC, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, timeout=45)
            response.raise_for_status()
            data = response.json()
            if "error" in data:
                raise RuntimeError("RPC_ERROR:" + str(data["error"].get("message")))
            return data["result"]
        except (requests.RequestException, ValueError) as error:
            last = error
            if attempt < 4:
                time.sleep(3 * (attempt + 1))
    raise RuntimeError("RPC_READ_UNAVAILABLE:" + str(last))


def view(method, args=None, sender="0x0000000000000000000000000000000000000001"):
    data = serialize([calldata.encode({"method": method, "args": args or []}), b"\x00"])
    raw = rpc("gen_call", [{"type": "read", "to": ADDRESS, "from": sender, "value": "0x0", "data": data,
                            "transaction_hash_variant": "latest-final"}])
    return str(calldata.decode(bytes.fromhex(raw.removeprefix("0x"))))


def parity():
    deployed = base64.b64decode(rpc("gen_getContractCode", [ADDRESS]))
    local = (ROOT / "contracts" / "RunbookDriftGate.py").read_bytes()
    if deployed != local or hashlib.sha256(deployed).hexdigest() != SOURCE_HASH:
        raise RuntimeError("SOURCE_MISMATCH")


def keys():
    values = {}
    for raw in TEST_ENV.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    result = [os.environ.get("WALLET_A_PRIVATE_KEY") or values.get("WALLET_A_PRIVATE_KEY"),
              os.environ.get("WALLET_B_PRIVATE_KEY") or values.get("WALLET_B_PRIVATE_KEY")]
    if not all(result):
        raise RuntimeError("LOCAL_TEST_KEYS_NOT_FOUND")
    return result


def tx_return(tx):
    receipts = (tx.get("consensus_data") or {}).get("leader_receipt") or []
    receipts = [receipts] if isinstance(receipts, dict) else receipts
    leaders = [item for item in receipts if item.get("mode") == "leader"]
    if not leaders or leaders[-1].get("execution_result") != "SUCCESS":
        raise RuntimeError("LEADER_EXECUTION_FAILED")
    value = leaders[-1].get("result")
    raw = base64.b64decode(value["raw"] if isinstance(value, dict) else value)
    if not raw or raw[0] != 0:
        raise RuntimeError("CONTRACT_EXECUTION_ERROR")
    return str(calldata.decode(raw[1:]))


def save(record):
    PRIVATE.parent.mkdir(exist_ok=True)
    PRIVATE.write_text(json.dumps(record, indent=2), encoding="utf-8")
    public = json.loads(json.dumps(record))
    public.pop("balances", None)
    for step in public["steps"]:
        step.pop("receipt", None)
    PUBLIC.write_text(json.dumps(public, indent=2) + "\n", encoding="utf-8")


def main():
    secret_keys = keys()
    accounts = [create_account(account_private_key="0x" + key.removeprefix("0x")) for key in secret_keys]
    del secret_keys
    curator, outsider = accounts
    clients = {account.address.lower(): create_client(chain=studionet, account=account) for account in accounts}
    parity()
    balances = {account.address: int(rpc("eth_getBalance", [account.address, "latest"]), 16) for account in accounts}
    open_args = lambda name: [name, OWNER, REPO, COMMIT, "fixtures/baseline-runbook.md", BASE, POLICY]
    plan = [
        {"id": "F1-invalid-commit", "actor": curator.address, "method": "open_lineage", "args": ["Invalid", OWNER, REPO, "main", "fixtures/baseline-runbook.md", BASE, POLICY], "allowed": ["INVALID_BASELINE_LOCATOR"]},
        {"id": "H1-open-safe-lineage", "actor": curator.address, "method": "open_lineage", "args": open_args("Safe wording revision"), "allowed": ["0"]},
        {"id": "F2-outsider-propose", "actor": outsider.address, "method": "propose_revision", "args": [0, COMMIT, "fixtures/safe-revision.md", SAFE], "allowed": ["CURATOR_ONLY"]},
        {"id": "H2-propose-safe", "actor": curator.address, "method": "propose_revision", "args": [0, COMMIT, "fixtures/safe-revision.md", SAFE], "allowed": ["0"]},
        {"id": "F3-second-pending", "actor": curator.address, "method": "propose_revision", "args": [0, COMMIT, "fixtures/missing-rollback.md", UNSAFE], "allowed": ["REVISION_NOT_PROPOSABLE"]},
        {"id": "H3-assess-safe", "actor": outsider.address, "method": "assess_revision", "args": [0], "allowed": ["SAFE_REVISION"]},
        {"id": "H4-promote-safe", "actor": curator.address, "method": "promote_revision", "args": [0], "allowed": ["BASELINE_PROMOTED"]},
        {"id": "F4-promote-replay", "actor": curator.address, "method": "promote_revision", "args": [0], "allowed": ["REVISION_NOT_PROMOTABLE"]},
        {"id": "H5-open-unsafe-lineage", "actor": curator.address, "method": "open_lineage", "args": open_args("Rollback removal control"), "allowed": ["1"]},
        {"id": "H6-propose-unsafe", "actor": curator.address, "method": "propose_revision", "args": [1, COMMIT, "fixtures/missing-rollback.md", UNSAFE], "allowed": ["1"]},
        {"id": "H7-assess-unsafe", "actor": outsider.address, "method": "assess_revision", "args": [1], "allowed": ["SAFETY_REGRESSION"]},
        {"id": "F5-promote-unsafe", "actor": curator.address, "method": "promote_revision", "args": [1], "allowed": ["REVISION_NOT_PROMOTABLE"]},
        {"id": "H8-dismiss-unsafe", "actor": curator.address, "method": "dismiss_revision", "args": [1], "allowed": ["REVISION_DISMISSED"]},
        {"id": "H9-open-integrity-lineage", "actor": curator.address, "method": "open_lineage", "args": open_args("Digest mismatch control"), "allowed": ["2"]},
        {"id": "H10-propose-wrong-digest", "actor": curator.address, "method": "propose_revision", "args": [2, COMMIT, "fixtures/safe-revision.md", "0" * 64], "allowed": ["2"]},
        {"id": "H11-assess-integrity", "actor": outsider.address, "method": "assess_revision", "args": [2], "allowed": ["INTEGRITY_FAILURE"]},
        {"id": "F6-promote-integrity", "actor": curator.address, "method": "promote_revision", "args": [2], "allowed": ["REVISION_NOT_PROMOTABLE"]},
        {"id": "H12-dismiss-integrity", "actor": curator.address, "method": "dismiss_revision", "args": [2], "allowed": ["REVISION_DISMISSED"]},
    ]
    if PRIVATE.exists():
        record = json.loads(PRIVATE.read_text(encoding="utf-8"))
    else:
        if view("get_counts", sender=curator.address) != "0|0":
            raise RuntimeError("EXPECTED_EMPTY_DEPLOYMENT")
        record = {"contract": ADDRESS, "source_sha256": SOURCE_HASH, "fixture_commit": COMMIT,
                  "started_at": datetime.now(timezone.utc).isoformat(), "wallets": [a.address for a in accounts],
                  "balances": balances, "steps": [], "complete": False}
        save(record)
    print(json.dumps({"ready": True, "balances": balances, "completed": len(record["steps"]), "total": len(plan)}), flush=True)
    for index, wanted in enumerate(plan):
        parity()
        if index < len(record["steps"]):
            item = record["steps"][index]
            if item["id"] != wanted["id"]:
                raise RuntimeError("PLAN_MISMATCH")
            if item.get("status") == "VERIFIED":
                continue
            if item.get("status") != "SUBMITTED":
                raise RuntimeError("UNKNOWN_CHECKPOINT")
        else:
            item = dict(wanted)
            item["status"] = "INTENT_SAVED"
            record["steps"].append(item)
            save(record)
            item["hash"] = str(clients[item["actor"].lower()].write_contract(address=ADDRESS, function_name=item["method"], args=item["args"], value=0, leader_only=False))
            item["status"] = "SUBMITTED"
            save(record)
            print(json.dumps({"step": item["id"], "hash": item["hash"]}), flush=True)
        deadline = time.monotonic() + 1200
        while time.monotonic() < deadline:
            tx = rpc("eth_getTransactionByHash", [item["hash"]])
            if tx and tx.get("status") == "FINALIZED":
                if tx.get("result_name") != "MAJORITY_AGREE":
                    raise RuntimeError("CONSENSUS_FAILED")
                actual = tx_return(tx)
                if actual == "ASSESSMENT_RETRYABLE":
                    raise RuntimeError("RETRYABLE_STOP_NO_RESUBMIT")
                if actual not in item["allowed"]:
                    raise RuntimeError("UNEXPECTED:" + actual)
                counts = view("get_counts", sender=curator.address)
                readback = {"counts": counts}
                for object_id in range(int(counts.split("|")[0])):
                    readback["lineage" + str(object_id)] = view("get_lineage", [object_id], curator.address)
                for object_id in range(int(counts.split("|")[1])):
                    readback["revision" + str(object_id)] = view("get_revision", [object_id], curator.address)
                item.update({"actual": actual, "receipt": tx, "readback": readback, "status": "VERIFIED",
                             "explorer": "https://explorer-studio.genlayer.com/tx/" + item["hash"]})
                save(record)
                print(json.dumps({"step": item["id"], "actual": actual}), flush=True)
                break
            time.sleep(8)
        else:
            raise RuntimeError("POLL_TIMEOUT_KEEP_HASH")
    record["complete"] = True
    record["completed_at"] = datetime.now(timezone.utc).isoformat()
    save(record)
    print(json.dumps({"complete": True, "steps": len(plan)}))


if __name__ == "__main__":
    main()
