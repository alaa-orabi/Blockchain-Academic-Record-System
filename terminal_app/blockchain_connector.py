# ─────────────────────────────────────────────────────────────────────────────
#  blockchain_connector.py
#  Handles all low-level Web3 plumbing: connection, contract loading,
#  transaction sending, and balance helpers.
# ─────────────────────────────────────────────────────────────────────────────

import json
import os
from web3 import Web3
from web3.exceptions import ContractLogicError

# ── Path helpers ──────────────────────────────────────────────────────────────

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARED_DIR = os.path.join(BASE_DIR, "shared")

GANACHE_URL = "http://127.0.0.1:8545"

# ── Connect ───────────────────────────────────────────────────────────────────

def connect() -> Web3:
    """Return a connected Web3 instance or raise with a helpful message."""
    w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
    if not w3.is_connected():
        raise ConnectionError(
            "\n  ✗ Cannot reach Ganache at " + GANACHE_URL +
            "\n  Start it with:  ganache --deterministic --accounts 10\n"
        )
    return w3


# ── JSON loaders ──────────────────────────────────────────────────────────────

def _load_json(filename: str):
    path = os.path.join(SHARED_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"\n  ✗ Missing file: {path}"
            "\n  Run  scripts/1-deploy.py  first.\n"
        )
    with open(path) as f:
        return json.load(f)


def load_contracts(w3: Web3):
    """
    Returns (rc_contract, gc_contract, addresses_dict)
    rc  = ReportCard contract
    gc  = GradeCoin  contract
    """
    addresses = _load_json("contract_address.json")
    rc_abi    = _load_json("ReportCard_abi.json")
    gc_abi    = _load_json("GradeCoin_abi.json")

    rc = w3.eth.contract(address=addresses["ReportCard"], abi=rc_abi)
    gc = w3.eth.contract(address=addresses["GradeCoin"],  abi=gc_abi)
    return rc, gc, addresses


# ── Transaction helper ────────────────────────────────────────────────────────

def send_tx(w3: Web3, fn, sender: str, gas: int = 300_000) -> dict:
    """
    Build, send, and wait for a contract function call.
    Returns the transaction receipt.
    Raises a clean RuntimeError on revert.
    """
    try:
        tx_hash    = fn.transact({"from": sender, "gas": gas})
        receipt    = w3.eth.wait_for_transaction_receipt(tx_hash)
        return receipt
    except ContractLogicError as e:
        raise RuntimeError(f"Transaction reverted: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Transaction failed: {e}") from e


# ── Balance helpers ───────────────────────────────────────────────────────────

def eth_balance(w3: Web3, address: str) -> float:
    """Return ETH balance as a float (in Ether)."""
    wei = w3.eth.get_balance(Web3.to_checksum_address(address))
    return float(w3.from_wei(wei, "ether"))


def coin_balance(gc_contract, address: str) -> float:
    """Return GradeCoin balance as a float (human-readable, 18 decimals)."""
    raw = gc_contract.functions.balanceOf(
        Web3.to_checksum_address(address)
    ).call()
    return raw / (10 ** 18)


# ── Address validator ─────────────────────────────────────────────────────────

def to_checksum(address: str) -> str:
    """Convert address to checksum format, raise ValueError if invalid."""
    try:
        return Web3.to_checksum_address(address)
    except Exception:
        raise ValueError(f"Invalid Ethereum address: {address!r}")


# ── Block-scan helpers ────────────────────────────────────────────────────────

def iter_blocks(w3: Web3, start: int = 0, end: int | None = None):
    """Yield every block dict from start to end (inclusive)."""
    if end is None:
        end = w3.eth.block_number
    for num in range(start, end + 1):
        yield w3.eth.get_block(num, full_transactions=True)


def get_all_transactions(w3: Web3):
    """
    Return a list of all transactions on-chain as plain dicts:
    {block, hash, from, to, value, input}
    """
    txs = []
    latest = w3.eth.block_number
    for block in iter_blocks(w3, 0, latest):
        for tx in block.transactions:
            txs.append({
                "block":  block.number,
                "hash":   tx.hash.hex(),
                "from":   tx["from"],
                "to":     tx.get("to", ""),
                "value":  tx.value,
                "input":  tx.input.hex() if isinstance(tx.input, (bytes, bytearray)) else tx.input,
            })
    return txs


def tx_count_per_address(w3: Web3) -> dict:
    """Return {address: tx_count} for every sender seen on-chain."""
    counts: dict[str, int] = {}
    for tx in get_all_transactions(w3):
        addr = tx["from"]
        counts[addr] = counts.get(addr, 0) + 1
    return counts