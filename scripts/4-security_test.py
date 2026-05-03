import json
from web3 import Web3

# Connect to Ganache
web3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))

# Load addresses and ABI
with open("shared/contract_address.json") as f:
    addresses = json.load(f)

with open("shared/abis/ReportCard_abi.json") as f:
    report_abi = json.load(f)

# Initialize contract
report = web3.eth.contract(
    address=addresses["ReportCard"],
    abi=report_abi
)

# accounts[0] = admin , accounts[1] = normal student
admin     = web3.eth.accounts[0]
non_admin = web3.eth.accounts[1]

print("=" * 45)
print("         SECURITY TEST")
print("=" * 45)
print(f"Admin    : {admin}")
print(f"Non-Admin: {non_admin}")
print()

# Try to add a grade from a non-admin account
try:
    report.functions.addGrade(
        non_admin, 90
    ).transact({'from': non_admin})
    
    print("FAIL ❌ — Contract allowed student to add a grade!")

except Exception as e:
    print("PASS ✅ — Non-admin was rejected successfully")
    print(f"Reason: {e}")

print("=" * 45)