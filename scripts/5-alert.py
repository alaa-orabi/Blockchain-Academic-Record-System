import json
import time
import os
import signal
from web3 import Web3

# Handle CTRL+C cleanly
def stop_handler(signum, frame):
    print("\n[INFO] Alert system stopped. Goodbye!")
    os._exit(0)

signal.signal(signal.SIGINT, stop_handler)

# Connect to Ganache (NO trailing space after 7545!)
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

print("=" * 45)
print("      LIVE ALERT SYSTEM - RUNNING")
print("  Waiting for grade changes...")
print("  (Press CTRL+C to stop)")
print("=" * 45)

last_block = web3.eth.block_number

while True:
    current_block = web3.eth.block_number

    if current_block > last_block:
        # FIXED: web3.py v6 uses snake_case: from_block / to_block
        events = report.events.GradeRecorded.get_logs(
            from_block=last_block + 1,
            to_block=current_block
        )

        for event in events:
            student = event['args']['studentAddress']
            grade   = event['args']['grade']
            print(f"\nALERT: A grade change just happened!")
            print(f"  Student : {student}")
            print(f"  Grade   : {grade}")
            print("-" * 45)

        last_block = current_block

    time.sleep(2)