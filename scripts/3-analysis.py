import json
from web3 import Web3
from collections import Counter

# Connect to Ganache
web3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))

# Load addresses and ABIs
with open("shared/contract_address.json") as f:
    addresses = json.load(f)

with open("shared/abis/ReportCard_abi.json") as f:
    report_abi = json.load(f)

with open("shared/abis/GradeToken_abi.json") as f:
    token_abi = json.load(f)

# Initialize contracts
report = web3.eth.contract(address=addresses["ReportCard"], abi=report_abi)
token  = web3.eth.contract(address=addresses["GradeToken"],  abi=token_abi)

# ===== Fetch data =====
student_count = report.functions.getStudentCount().call()
total_supply  = token.functions.totalSupply().call()

# Scan all blocks and count transactions
sender_counter = Counter()
total_txns = 0

for i in range(web3.eth.block_number + 1):
    block = web3.eth.get_block(i, full_transactions=True)
    for tx in block.transactions:
        if tx['to'] and tx['to'].lower() == addresses["ReportCard"].lower():
            total_txns += 1
            sender_counter[tx['from']] += 1

top3 = sender_counter.most_common(3)

# ===== Print results =====
print("=" * 45)
print("         ADMIN DASHBOARD - REPORT CARD")
print("=" * 45)
print(f"Total Students   : {student_count}")
print(f"Total GradeCoins : {web3.from_wei(total_supply, 'ether')} GRC")
print(f"Total Transactions: {total_txns}")
print("\nTop 3 Active Addresses:")
for i, (addr, count) in enumerate(top3, 1):
    print(f"  {i}. {addr} — {count} txns")
print("=" * 45)