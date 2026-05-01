# 🎓 Blockchain Academic Record System

## Overview

The **Blockchain Academic Record System** is a decentralized application (DApp) built using blockchain technology to securely store and manage student academic records.

The system ensures that all grades are **immutable, transparent, and tamper-proof** — once data is recorded on-chain, it cannot be modified or deleted without a full audit trail.

This project demonstrates how blockchain can be applied in real-world academic environments to improve trust, transparency, and security.

---

## Objectives

- Build a secure and decentralized academic record system
- Prevent unauthorized modification of student grades
- Ensure transparency in academic data storage
- Implement role-based access control (Admin / Student)
- Demonstrate blockchain immutability in education systems

---

## System Architecture

```
Student / Admin (Terminal)
        ↓
  Python CLI App  (web3.py)
        ↓
  Smart Contracts (Solidity)
        ↓
  Blockchain Network (Ganache)
```

| Layer | Technology | Purpose |
|---|---|---|
| Smart Contracts | Solidity 0.8.0 | Core logic, grade storage, access control |
| ERC-20 Token | GradeToken (GradeCoin) | Reward system for student interactions |
| Blockchain Interaction | Python + web3.py | Deploy, transact, read from chain |
| Terminal Application | Python CLI | User interface for Admin and Students |
| Blockchain Network | Ganache (local) | Local Ethereum test network |

---

## 👥 User Roles

### 🔴 Admin
- Add and update student grades (single and batch)
- Mint and distribute Grade Coins
- Pause / Resume the system in emergencies
- Transfer ownership to a new admin
- View system analytics dashboard

### 🟢 Student
- Register personal on-chain profile (once)
- View personal academic grade
- Check Grade Coin and ETH balances
- View personal activity history

---

## ⚙️ Features

| Feature | Description |
|---|---|
| Immutable grade storage | Grades written on-chain cannot be altered without a trace |
| Custom ERC-20 token | GradeCoin — minted by Admin only |
| User registration | One-time on-chain profile per wallet address |
| Admin dashboard | Analytics summary pulled directly from the blockchain |
| Activity history | Full per-address transaction log scanned from blocks |
| Balance checker | ETH + GradeCoin balance for any address |
| Batch grade updates | Assign grades to multiple students in one transaction |
| Emergency stop | Pause / Resume switch blocks all user actions instantly |
| Ownership transfer | Admin rights can be handed to a new address securely |
| Security tests | Automated proof that non-admins cannot call admin functions |
| CSV export | Snapshot of all balances exported to a file |
| Live alerts | Background script prints real-time grade-change notifications |

---

## 📁 Project Structure

```
BLOCKCHAIN/
│
├── contracts/
│   ├── ReportCard.sol          ← Core contract (grades, access control, registration)
│   └── GradeToken.sol          ← ERC-20 GradeCoin contract
│
├── scripts/                    ← Run in order: 1 → 2 → then 3/4/5/6 as needed
│   ├── 1-deploy.py             ← Deploy both contracts to Ganache
│   ├── 2-setup.py              ← Seed fake students and coins for testing
│   ├── 3-analysis.py           ← Admin dashboard: system summary from blockchain
│   ├── 4-security_test.py      ← Prove non-admins are blocked by the EVM
│   ├── 5-alert.py              ← Live background alert for grade changes
│   └── 6-export_csv.py         ← Export balance snapshot to CSV file
│
├── shared/                     ← Single source of truth — everyone reads from here
│   ├── abis/
│   │   ├── ReportCard_abi.json ← Auto-generated after deploy (do not edit)
│   │   └── GradeToken_abi.json ← Auto-generated after deploy (do not edit)
│   └── contract_address.json   ← Filled automatically by 1-deploy.py
│
├── terminal_app/
│   ├── main.py                 ← Entry point — launches the CLI menu
│   ├── blockchain_connector.py ← Shared web3 connection and contract loader
│   ├── student_menu.py         ← Register / view grade / check balance
│   └── admin_menu.py           ← Hidden admin menu (add grade / mint / pause)
│
├── README.md
└── requirements.txt
```

> **Numbers in `scripts/` are intentional.** They show the correct execution order.
> Always run `1-deploy.py` first, then `2-setup.py`, before using anything else.

---

## 🔗 How the Team Shares One Blockchain

Every teammate connects using the same three things — **one address, one ABI, one Ganache**.

```python
from web3 import Web3
import json

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))

with open("shared/abis/ReportCard_abi.json") as f:
    abi = json.load(f)

with open("shared/contract_address.json") as f:
    address = json.load(f)["ReportCard"]

contract = w3.eth.contract(address=address, abi=abi)
```

**Nobody hardcodes an address or ABI. Everyone reads from `shared/`.**

---

## 🚀 How to Run

### 1. Install dependencies
```bash
pip install web3 py-solc-x
```

### 2. Start Ganache
Open Ganache and ensure it is running on `http://127.0.0.1:7545`

### 3. Deploy smart contracts
```bash
python scripts/1-deploy.py
```
This will automatically populate `shared/contract_address.json` and both ABI files.

### 4. Seed test data
```bash
python scripts/2-setup.py
```

### 5. Run the terminal application
```bash
python terminal_app/main.py
```

### 6. (Optional) Run analysis and tests
```bash
python scripts/3-analysis.py
python scripts/4-security_test.py
python scripts/5-alert.py
python scripts/6-export_csv.py
```

---

## 🔐 Security Features

- `onlyOwner` modifier on every sensitive admin function
- `whenNotPaused` modifier blocks all user actions during emergency stop
- Re-registration blocked at the contract level with `require`
- Automated security test proves non-admins are rejected by the EVM
- `transferOwnership` verified with a before/after Python test script
- Blockchain immutability prevents any silent data tampering

---

## 📋 Smart Contract: ReportCard.sol

### Functions

| Function | Who can call | Description |
|---|---|---|
| `registerUser(name)` | Student | One-time profile registration |
| `getGrade(address)` | Anyone | Returns name, grade, and whether grade was set |
| `addGrade(address, grade)` | Admin | Assigns or updates a student's grade |
| `batchAddGrades(addresses[], grades[])` | Admin | Assigns grades to multiple students at once |
| `pause()` / `resume()` | Admin | Emergency stop switch |
| `transferOwnership(newOwner)` | Admin | Hands admin rights to a new address |
| `getAdmin()` | Anyone | Returns current admin address |
| `getStudentCount()` | Anyone | Returns total number of registered students |
| `getStudentAt(index)` | Anyone | Returns student address at a given index |

### Events (used by activity history scanner in `3-analysis.py`)

| Event | Emitted when |
|---|---|
| `StudentRegistered` | A student calls `registerUser` |
| `GradeRecorded` | Admin calls `addGrade` or `batchAddGrades` |
| `ContractPaused` | Admin calls `pause` |
| `ContractResumed` | Admin calls `resume` |
| `OwnershipTransferred` | Admin calls `transferOwnership` |

---

## 👨‍💻 Team Members & File Ownership

| Member | Role | Files Owned |
|---|---|---|
| Alaa Orabi | Backend Solidity Dev | `contracts/ReportCard.sol` |
| Walaa Omar | Coin & Advanced Contract Dev | `contracts/GradeToken.sol` |
| Ahmed Sameh | Deployment Engineer | `scripts/1-deploy.py`, `scripts/2-setup.py`, `shared/` |
| Mahmoud Sayed | Terminal App Developer | `terminal_app/main.py`, `terminal_app/blockchain_connector.py`, `terminal_app/student_menu.py`, `terminal_app/admin_menu.py` |
| Mayada Yasser | Data, Testing & System Features | `scripts/3-analysis.py`, `scripts/4-security_test.py`, `scripts/5-alert.py`, `scripts/

---

## 📌 Conclusion

This project demonstrates the power of blockchain technology in education systems by ensuring **secure, transparent, and immutable** academic records. It eliminates trust issues and provides a decentralized alternative to traditional centralized databases.

All data flows through the smart contract — Python is only the interface. The blockchain enforces every rule.