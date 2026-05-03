import json
import os
from web3 import Web3

GANACHE_URL = "http://127.0.0.1:8545"
w3 = Web3(Web3.HTTPProvider(GANACHE_URL))

if not w3.is_connected():
    raise ConnectionError("Cannot connect to Ganache. Is it still running?")

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARED_DIR = os.path.join(BASE_DIR, "shared")

def load_json(filename):
    with open(os.path.join(SHARED_DIR, filename)) as f:
        return json.load(f)

addresses    = load_json("contract_address.json")
rc_abi       = load_json("ReportCard_abi.json")
gc_abi       = load_json("GradeCoin_abi.json")

admin_address = addresses["admin"]
rc_contract   = w3.eth.contract(address=addresses["ReportCard"], abi=rc_abi)
gc_contract   = w3.eth.contract(address=addresses["GradeCoin"],  abi=gc_abi)

print(f"Admin:       {admin_address}")
print(f"ReportCard:  {addresses['ReportCard']}")
print(f"GradeCoin:   {addresses['GradeCoin']}\n")

FAKE_STUDENTS = [
    {"name": "Ali Hassan",    "grade": 88, "coins": 50},
    {"name": "Sara Khalid",   "grade": 95, "coins": 75},
    {"name": "Omar Youssef",  "grade": 72, "coins": 40},
    {"name": "Nour Ibrahim",  "grade": 80, "coins": 60},
]

print("── Registering students ──────────────────────────────────")
for i, student in enumerate(FAKE_STUDENTS):
    student_account = w3.eth.accounts[i + 1]


    tx_hash = rc_contract.functions.registerUser(student["name"]).transact(
        {"from": student_account}
    )
    w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"  Registered: {student['name']}  ({student_account})")


print("\n── Adding grades ─────────────────────────────────────────")
for i, student in enumerate(FAKE_STUDENTS):
    student_account = w3.eth.accounts[i + 1]


    tx_hash = rc_contract.functions.addGrade(
        student_account,
        student["grade"]
    ).transact({"from": admin_address})
    w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"  Grade {student['grade']} → {student['name']}")


print("\n── Minting GradeCoins ────────────────────────────────────")
for i, student in enumerate(FAKE_STUDENTS):
    student_account = w3.eth.accounts[i + 1]
    amount_wei = student["coins"] * (10 ** 18)

    tx_hash = gc_contract.functions.mint(
        student_account,
        amount_wei
    ).transact({"from": admin_address})
    w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"  Minted {student['coins']} GRC → {student['name']}")

print("\n── Verification ──────────────────────────────────────────")
print(f"  Total students registered: {rc_contract.functions.getStudentCount().call()}")
print(f"  Total GradeCoins minted:   {gc_contract.functions.totalSupply().call() // (10**18)} GRC")

print("\nSetup complete! The system is ready for testing.")
print("Hand the shared/ folder to the rest of the team.")
