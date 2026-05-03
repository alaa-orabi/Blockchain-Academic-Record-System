import json
import os
from web3 import Web3
from solcx import compile_source, install_solc

install_solc("0.8.0")

GANACHE_URL = "http://127.0.0.1:8545"
w3 = Web3(Web3.HTTPProvider(GANACHE_URL))

if not w3.is_connected():
    raise ConnectionError("Cannot connect to Ganache. Make sure it is running:\n  ganache --deterministic --accounts 10")

print(f"Connected to Ganache  |  Chain ID: {w3.eth.chain_id}")


admin_account = w3.eth.accounts[0]
print(f"Admin (deployer): {admin_account}\n")

BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTRACTS_DIR = os.path.join(BASE_DIR, "contracts")
SHARED_DIR    = os.path.join(BASE_DIR, "shared")
os.makedirs(SHARED_DIR, exist_ok=True)

def compile_contract(filename):
    """Read a Solidity file and return its ABI + bytecode."""
    filepath = os.path.join(CONTRACTS_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    
    contract_name = filename.replace(".sol", "")

    compiled = compile_source(
        source,
        output_values=["abi", "bin"],
        solc_version="0.8.0",
    )

    
    key = f"<stdin>:{contract_name}"
    abi      = compiled[key]["abi"]
    bytecode = compiled[key]["bin"]
    return abi, bytecode


def deploy_contract(abi, bytecode, deployer):
    Contract   = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx_hash    = Contract.constructor().transact({"from": deployer})
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    deployed   = w3.eth.contract(address=tx_receipt.contractAddress, abi=abi)
    return deployed, tx_receipt.contractAddress


print("Compiling ReportCard.sol ...")
rc_abi, rc_bytecode = compile_contract("ReportCard.sol")

print("Deploying ReportCard ...")
rc_contract, rc_address = deploy_contract(rc_abi, rc_bytecode, admin_account)
print(f"  ReportCard deployed at:  {rc_address}")

print("\nCompiling GradeCoin.sol ...")
gc_abi, gc_bytecode = compile_contract("GradeCoin.sol")

print("Deploying GradeCoin ...")
gc_contract, gc_address = deploy_contract(gc_abi, gc_bytecode, admin_account)
print(f"  GradeCoin deployed at:   {gc_address}")

addresses = {
    "ReportCard": rc_address,
    "GradeCoin":  gc_address,
    "admin":      admin_account,
}

with open(os.path.join(SHARED_DIR, "contract_address.json"), "w") as f:
    json.dump(addresses, f, indent=2)

with open(os.path.join(SHARED_DIR, "ReportCard_abi.json"), "w") as f:
    json.dump(rc_abi, f, indent=2)

with open(os.path.join(SHARED_DIR, "GradeCoin_abi.json"), "w") as f:
    json.dump(gc_abi, f, indent=2)

print("\n── shared/ folder updated ──────────────────────────────")
print("  contract_address.json")
print("  ReportCard_abi.json")
print("  GradeCoin_abi.json")
print("\nDeployment complete! The team can now run their scripts.")
