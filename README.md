# 🎓 Blockchain Academic Record System

##  Overview

The **Blockchain Academic Record System** is a decentralized application (DApp) built using blockchain technology to securely store and manage student academic records.

The system ensures that all grades are **immutable, transparent, and tamper-proof**, meaning once data is recorded, it cannot be modified or deleted.

This project demonstrates how blockchain can be applied in real-world academic environments to improve trust, transparency, and security.

---

##  Objectives

- Build a secure and decentralized academic record system  
- Prevent unauthorized modification of student grades  
- Ensure transparency in academic data storage  
- Implement role-based access control (Admin / Student)  
- Demonstrate blockchain immutability in education systems  

---

##  System Architecture

The system consists of:

- Smart Contracts (Solidity) → Core logic and grade storage  
- ERC-20 Token (Grade Coin) → Reward system for interactions  
- Python Scripts (Web3) → Blockchain interaction and automation  
- Terminal Application (CLI) → User interface for Admin and Students  
- Blockchain Network → Ganache / Ethereum test network  

---

## 👥 User Roles

### 🔴 Admin

- Add and update student grades  
- Mint and distribute Grade Coins  
- Manage system operations  
- View system analytics dashboard  

### 🟢 Student

- View personal academic grades  
- Check token and ETH balances  
- View activity history  
- Register personal profile  

---

## ⚙️ Features

- ✔ Immutable storage of academic records  
- ✔ Custom ERC-20 Grade Token  
- ✔ User registration system  
- ✔ Admin dashboard with analytics  
- ✔ Full transaction history tracking  
- ✔ Balance checker (ETH + Tokens)  
- ✔ Batch grade updates  
- ✔ Pause / Resume emergency system  
- ✔ Ownership transfer functionality  

---

## 📁 Project Structure
contracts/
Core.sol
GradeToken.sol

scripts/
deploy.py
admin_dashboard.py
alerts.py
test_security.py

terminal_app/
main.py
admin_menu.py
student_menu.py
blockchain_connector.py

tests/

docs/
report.md
architecture.png
flowchart.png

abi/

requirements.txt
README.md


## 🚀 How to Run

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Deploy smart contract**
```bash
python scripts/deploy.py
```

**3. Run terminal application**
```bash
python terminal_app/main.py
```

## 🔐 Security Features

- `onlyOwner` access control for Admin functions
- Blockchain immutability prevents data tampering
- Emergency pause/resume system for safety
- Secure transaction handling using Web3

## 📊 System Output

- All grades stored permanently on blockchain
- Each transaction recorded in blocks
- Real-time balance updates
- Transparent and auditable history

## 👨‍💻 Team Members

| Member   | Role                          | Responsibilities                                                                 |
|----------|-------------------------------|---------------------------------------------------------------------------------|
| Alaa orabi | Backend Solidity Dev (Core Contract) | Smart Contract: `addGrade`, `getGrade`, `registerUser`, `onlyOwner`, pause/resume |
| Walaa omar | Coin & Advanced Contract Dev  | GradeCoin ERC-20: `mint`, `transfer`, `balanceOf`, `transferOwnership`, batch functions |
| ahmed sameh | Deployment Engineer           | Ganache setup, deploy contracts, Python deploy script, auto-setup with fake students & coins |
| Mahmoud sayed | Terminal App Developer        | Python CLI menu: User (register/grade/balance) & hidden Admin (add grade/mint/pause) |
| Mayada yasser | Data, Testing & System Features | Activity history, balance checker, security tests, CSV export, live alerts |
## 📌 Conclusion

This project demonstrates the power of blockchain technology in education systems by ensuring secure, transparent, and immutable academic records. It eliminates trust issues and provides a decentralized alternative to traditional centralized databases.