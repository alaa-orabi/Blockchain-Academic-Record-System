#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
#  main.py  –  ReportCard Terminal App
#
#  Usage:
#    cd terminal_app
#    python main.py
#
#  Make sure Ganache is running and scripts/1-deploy.py has been executed first.
# ─────────────────────────────────────────────────────────────────────────────

import sys
import os

# Allow imports from this folder even when run directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web3 import Web3
from blockchain_connector import connect, load_contracts, send_tx, to_checksum
from admin_menu   import run_admin_menu
from student_menu import run_student_menu

# ── Colour helpers ────────────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BLUE   = "\033[94m"
DIM    = "\033[2m"

# ── Admin password (change this for production!) ──────────────────────────────

ADMIN_PASSWORD = "admin123"

# ── Formatting utilities ──────────────────────────────────────────────────────

def _sep(char="─", width=60, color=CYAN):
    print(f"{color}{char * width}{RESET}")

def _title(text):
    _sep("═")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    _sep("═")

def _ok(msg):    print(f"  {GREEN}✔  {msg}{RESET}")
def _err(msg):   print(f"  {RED}✗  {msg}{RESET}")
def _info(msg):  print(f"  {CYAN}ℹ  {msg}{RESET}")
def _warn(msg):  print(f"  {YELLOW}⚠  {msg}{RESET}")

def _input(prompt):
    return input(f"  {YELLOW}▶  {prompt}{RESET}").strip()

# ─────────────────────────────────────────────────────────────────────────────
#  Banner
# ─────────────────────────────────────────────────────────────────────────────

def _banner():
    print()
    print(f"{BOLD}{CYAN}╔══════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{CYAN}║         📚  REPORT CARD  ·  Blockchain Terminal          ║{RESET}")
    print(f"{BOLD}{CYAN}╚══════════════════════════════════════════════════════════╝{RESET}")
    print()

# ─────────────────────────────────────────────────────────────────────────────
#  Account selection
# ─────────────────────────────────────────────────────────────────────────────

def _select_account(w3: Web3, addresses: dict) -> str:
    """
    Let the user pick a wallet address from the Ganache accounts list.
    Returns the chosen checksum address.
    """
    accounts = w3.eth.accounts
    admin    = addresses["admin"]

    print(f"\n  {BOLD}Available accounts:{RESET}")
    _sep(width=72)
    print(f"  {'#':<4}{'Address':<44}{'ETH':>10}  {'Note'}")
    print(f"  {DIM}{'─'*70}{RESET}")
    for i, acc in enumerate(accounts):
        bal  = float(w3.from_wei(w3.eth.get_balance(acc), "ether"))
        note = f"{YELLOW}[Admin]{RESET}" if acc.lower() == admin.lower() else ""
        print(f"  {i:<4}{acc:<44}{bal:>9.2f}  {note}")
    _sep(width=72)

    while True:
        raw = _input("Enter account number or paste an address: ")
        if raw.isdigit() and 0 <= int(raw) < len(accounts):
            return accounts[int(raw)]
        try:
            return to_checksum(raw)
        except ValueError:
            _err("Invalid input. Enter a number from the list or a full address.")

# ─────────────────────────────────────────────────────────────────────────────
#  First-visit registration check
# ─────────────────────────────────────────────────────────────────────────────

def _ensure_registered(w3: Web3, rc, active_account: str):
    """
    Check if the user is registered on-chain.
    If not, prompt them to register now.
    Returns the display name (or empty string if still unregistered).
    """
    try:
        name, _, _ = rc.functions.getGrade(active_account).call()
        return name  # already registered
    except Exception:
        pass  # Not registered yet

    print()
    _warn("You are not registered on-chain yet.")
    _info("Registration saves your display name permanently to the blockchain.")
    choice = _input("Register now? (y/n): ")
    if choice.lower() != "y":
        return ""

    while True:
        name = _input("Enter your display name: ")
        if not name:
            _err("Name cannot be empty.")
            continue
        break

    try:
        if rc.functions.paused().call():
            _err("The contract is currently paused. Cannot register right now.")
            return ""
        send_tx(w3, rc.functions.registerUser(name), active_account)
        _ok(f"Registered as '{name}'!")
        return name
    except RuntimeError as e:
        _err(f"Registration failed: {e}")
        return ""

# ─────────────────────────────────────────────────────────────────────────────
#  Main menu
# ─────────────────────────────────────────────────────────────────────────────

def _main_menu(w3: Web3, rc, gc, addresses: dict, active_account: str, display_name: str):
    """
    Show the main menu, dispatch to student or admin menus.
    """
    admin_addr = addresses["admin"]

    while True:
        print()
        _sep("═")
        print(f"{BOLD}{CYAN}  📚  REPORT CARD  –  Main Menu{RESET}")
        _sep("═")

        # Refresh name each loop in case it changed
        try:
            display_name, _, _ = rc.functions.getGrade(active_account).call()
        except Exception:
            pass

        name_str = f"  {BOLD}{display_name}{RESET}" if display_name else ""
        is_admin = active_account.lower() == admin_addr.lower()
        role_str = f"{YELLOW}[Admin]{RESET}" if is_admin else f"{CYAN}[Student]{RESET}"

        if name_str:
            print(f"  Logged in as :{name_str}  {role_str}")
        else:
            print(f"  Wallet : {BOLD}{active_account}{RESET}  {role_str}")

        paused = rc.functions.paused().call()
        if paused:
            print(f"  {RED}{BOLD}  ⛔ Contract is currently PAUSED{RESET}")

        _sep()
        print(f"  {BOLD}[1]{RESET}  Student portal")
        print(f"  {BOLD}[2]{RESET}  Admin panel  {DIM}(password required){RESET}")
        print(f"  {BOLD}[3]{RESET}  Switch account")
        print(f"  {BOLD}[0]{RESET}  Exit")
        _sep()

        choice = _input("Choose an option: ")

        if choice == "1":
            run_student_menu(w3, rc, gc, addresses, active_account)

        elif choice == "2":
            # Password gate
            pwd = _input("Admin password: ")
            if pwd != ADMIN_PASSWORD:
                _err("Incorrect password. Access denied.")
                continue

            # Warn if this account is not the on-chain admin
            current_admin = rc.functions.getAdmin().call()
            if active_account.lower() != current_admin.lower():
                _warn(f"Your account ({active_account}) is NOT the current on-chain admin.")
                _warn(f"Current admin: {current_admin}")
                _warn("Admin transactions will likely revert.")

            run_admin_menu(w3, rc, gc, addresses, active_account)

        elif choice == "3":
            active_account = _select_account(w3, addresses)
            display_name   = _ensure_registered(w3, rc, active_account)

        elif choice == "0":
            print(f"\n  {CYAN}Goodbye! 👋{RESET}\n")
            sys.exit(0)

        else:
            _warn("Unknown option. Please try again.")

# ─────────────────────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    _banner()

    # ── Connect to Ganache ────────────────────────────────────────────────────
    print(f"  {CYAN}Connecting to Ganache …{RESET}")
    try:
        w3 = connect()
    except ConnectionError as e:
        print(e)
        sys.exit(1)
    _ok(f"Connected  |  Chain ID: {w3.eth.chain_id}  |  Block #{w3.eth.block_number}")

    # ── Load contracts ────────────────────────────────────────────────────────
    print(f"  {CYAN}Loading contracts …{RESET}")
    try:
        rc, gc, addresses = load_contracts(w3)
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)
    _ok(f"ReportCard : {addresses['ReportCard']}")
    _ok(f"GradeCoin  : {addresses['GradeCoin']}")

    # ── Account selection ─────────────────────────────────────────────────────
    print()
    _info("Select the wallet you want to use:")
    active_account = _select_account(w3, addresses)

    # ── First-visit registration check ────────────────────────────────────────
    display_name = _ensure_registered(w3, rc, active_account)

    # ── Main menu loop ────────────────────────────────────────────────────────
    _main_menu(w3, rc, gc, addresses, active_account, display_name)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {CYAN}Interrupted. Goodbye! 👋{RESET}\n")
        sys.exit(0)