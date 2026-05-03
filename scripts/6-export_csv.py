import json
import csv
from web3 import Web3

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
report = web3.eth.contract(
    address=addresses["ReportCard"],
    abi=report_abi
)
token = web3.eth.contract(
    address=addresses["GradeToken"],
    abi=token_abi
)

print("=" * 45)
print("      BALANCE SNAPSHOT EXPORTER")
print("=" * 45)

# Get total number of students
student_count = report.functions.getStudentCount().call()
print(f"Total Students Found: {student_count}")
print("Exporting...")

# Write CSV file
with open("balances.csv", "w", newline="") as f:
    writer = csv.writer(f)

    # Header row
    writer.writerow([
        "Account Address",
        "Grade Coin Balance",
        "ETH Balance"
    ])

    # One row per student
    for i in range(student_count):
        addr = report.functions.getStudentAt(i).call()

        coin_balance = token.functions.balanceOf(addr).call()
        coin_balance = web3.from_wei(coin_balance, 'ether')

        eth_balance = web3.eth.get_balance(addr)
        eth_balance = web3.from_wei(eth_balance, 'ether')

        writer.writerow([addr, coin_balance, eth_balance])
        print(f"  {i+1}. {addr[:20]}... | Coins: {coin_balance} | ETH: {eth_balance}")

print()
print("Done! File saved: balances.csv ✅")
print("=" * 45)