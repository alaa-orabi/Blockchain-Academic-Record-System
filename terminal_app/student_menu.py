# ─────────────────────────────────────────────────────────────────────────────
#  student_menu.py
#  All normal-user operations:
#    • View own grade
#    • Check any address's coin + ETH balance
#    • View personal activity history (all on-chain actions)
#    • Data history report (class average, grade table)
# ─────────────────────────────────────────────────────────────────────────────

from web3 import Web3
from blockchain_connector import (
    eth_balance, coin_balance, get_all_transactions, to_checksum
)

# ── Colour helpers ────────────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BLUE   = "\033[94m"
DIM    = "\033[2m"

def _sep(char="─", width=60, color=CYAN):
    print(f"{color}{char * width}{RESET}")

def _title(text):
    _sep()
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    _sep()

def _ok(msg):    print(f"  {GREEN}✔  {msg}{RESET}")
def _err(msg):   print(f"  {RED}✗  {msg}{RESET}")
def _info(msg):  print(f"  {CYAN}ℹ  {msg}{RESET}")
def _warn(msg):  print(f"  {YELLOW}⚠  {msg}{RESET}")

def _input(prompt):
    return input(f"  {YELLOW}▶  {prompt}{RESET}").strip()


# ── Student menu entry point ──────────────────────────────────────────────────

def run_student_menu(w3: Web3, rc, gc, addresses: dict, active_account: str):
    """Show the student menu. active_account is the user's wallet address."""
    while True:
        print()
        _sep("═")
        print(f"{BOLD}{CYAN}  🎓  STUDENT PORTAL{RESET}")
        _sep("═")

        # Show registered name if available
        try:
            name, grade, has_grade = rc.functions.getGrade(active_account).call()
            print(f"  Welcome back, {BOLD}{name}{RESET}")
        except Exception:
            name = None
            print(f"  Wallet: {BOLD}{active_account}{RESET}")

        _sep()
        print(f"  {BOLD}[1]{RESET}  View my grade")
        print(f"  {BOLD}[2]{RESET}  Check coin & ETH balance (any address)")
        print(f"  {BOLD}[3]{RESET}  My activity history")
        print(f"  {BOLD}[4]{RESET}  Class data history report")
        print(f"  {BOLD}[5]{RESET}  Transfer GradeCoins")
        print(f"  {BOLD}[0]{RESET}  ← Back to main menu")
        _sep()

        choice = _input("Choose an option: ")

        if   choice == "1": _view_my_grade(rc, active_account)
        elif choice == "2": _check_balance(w3, gc)
        elif choice == "3": _activity_history(w3, rc, gc, addresses, active_account)
        elif choice == "4": _data_history_report(w3, rc)
        elif choice == "5": _transfer_coins(w3, gc, active_account)
        elif choice == "0": break
        else: _warn("Unknown option. Please try again.")


# ── [1] View my grade ─────────────────────────────────────────────────────────

def _view_my_grade(rc, active_account: str):
    _title("MY GRADE")
    try:
        name, grade, has_grade = rc.functions.getGrade(active_account).call()
    except Exception as e:
        if "No record found" in str(e) or "execution reverted" in str(e).lower():
            _err("You are not registered. Please register first from the main menu.")
        else:
            _err(f"Error fetching grade: {e}")
        return

    print(f"\n  Name  : {BOLD}{name}{RESET}")
    if has_grade:
        grade_color = GREEN if grade >= 70 else YELLOW if grade >= 50 else RED
        bar_len     = grade // 5  # 0-20 chars
        bar         = "█" * bar_len + "░" * (20 - bar_len)
        print(f"  Grade : {grade_color}{BOLD}{grade:>3}/100{RESET}  {grade_color}{bar}{RESET}")
        if grade >= 90:
            print(f"\n  {BOLD}{GREEN}  Outstanding!{RESET}")
        elif grade >= 70:
            print(f"\n  {BOLD}{CYAN}  Good work!{RESET}")
        elif grade >= 50:
            print(f"\n  {BOLD}{YELLOW}  Needs improvement.{RESET}")
        else:
            print(f"\n  {BOLD}{RED}  At risk. Please seek help.{RESET}")
    else:
        _warn("No grade has been assigned yet. Check back later.")
    print()


# ── [2] Coin & ETH balance checker ───────────────────────────────────────────

def _check_balance(w3: Web3, gc):
    _title("BALANCE CHECKER")
    addr_raw = _input("Enter wallet address (or press Enter for your own): ")

    if not addr_raw:
        _warn("No address entered.")
        return

    try:
        addr = to_checksum(addr_raw)
    except ValueError as e:
        _err(str(e))
        return

    try:
        grc = coin_balance(gc, addr)
        eth = eth_balance(w3, addr)
    except Exception as e:
        _err(f"Could not fetch balances: {e}")
        return

    print()
    print(f"  Address : {BOLD}{addr}{RESET}")
    print()
    print(f"  {'Token':<20} {'Balance':>20}")
    print(f"  {DIM}{'─'*42}{RESET}")
    print(f"  {'GradeCoin (GRC)':<20} {BOLD}{GREEN}{grc:>18,.4f}{RESET}  GRC")
    print(f"  {'Ether (ETH)':<20} {BOLD}{BLUE}{eth:>18,.6f}{RESET}  ETH")
    print()


# ── [3] Personal activity history ─────────────────────────────────────────────

def _categorise(tx: dict, rc_addr: str, gc_addr: str, user_addr: str) -> str:
    """Return a human-readable action label for a transaction."""
    to   = (tx.get("to")   or "").lower()
    frm  = (tx.get("from") or "").lower()
    inp  = tx.get("input",  "")

    # Function selectors (first 4 bytes = 8 hex chars after 0x)
    sel = inp[2:10] if len(inp) >= 10 else ""

    SELECTORS = {
        # ReportCard
        "b3e1d2b5": "Registered name",
        "e232e366": "Registered name",
        # addGrade / batchAddGrades — received
        "a9059cbb": "Transferred GRC",
        # mint
        "40c10f19": "Received GRC mint",
        "d0d41fe1": "Received batch mint",
    }

    rc_lc = rc_addr.lower()
    gc_lc = gc_addr.lower()
    user  = user_addr.lower()

    if frm == user and to == rc_lc:
        if sel == "b3e1d2b5" or sel == "e232e366":
            return "Registered name on ReportCard"
        return "Interacted with ReportCard"
    if frm == user and to == gc_lc:
        if sel == "a9059cbb":
            return "Transferred GradeCoins"
        return "Interacted with GradeCoin"
    if to == user:
        if frm == rc_lc:
            return "Received grade update"
        if frm == gc_lc:
            return "Received GradeCoins"
        return "Received transaction"
    if frm == user:
        return "Sent transaction"
    return "Unknown action"


def _activity_history(w3: Web3, rc, gc, addresses: dict, active_account: str):
    _title("MY ACTIVITY HISTORY")

    addr_raw = _input("Address to inspect (Enter for your own): ")
    if not addr_raw:
        target = active_account
    else:
        try:
            target = to_checksum(addr_raw)
        except ValueError as e:
            _err(str(e))
            return

    print(f"\n  {CYAN}Scanning blockchain for {target} …{RESET}\n", end="", flush=True)

    all_txs = get_all_transactions(w3)
    target_l = target.lower()
    rc_addr  = addresses["ReportCard"]
    gc_addr  = addresses["GradeCoin"]

    # Filter transactions where this address is sender OR receiver
    relevant = [
        tx for tx in all_txs
        if tx["from"].lower() == target_l or (tx.get("to") or "").lower() == target_l
    ]

    print(f"\r  Found {len(relevant)} transaction(s) for {target}\n")

    if not relevant:
        _info("No on-chain activity found for this address.")
        return

    col_block  = 8
    col_hash   = 14
    col_action = 34
    col_eth    = 12

    header = (f"  {'Block':<{col_block}}"
              f"{'Tx Hash':<{col_hash}}"
              f"{'Action':<{col_action}}"
              f"{'ETH Value':>{col_eth}}")
    print(f"  {DIM}{header}{RESET}")
    print(f"  {DIM}{'─'*(col_block+col_hash+col_action+col_eth+2)}{RESET}")

    for tx in relevant:
        block     = tx["block"]
        tx_hash   = tx["hash"][:12] + "…"
        action    = _categorise(tx, rc_addr, gc_addr, target)
        eth_val   = w3.from_wei(tx["value"], "ether")
        eth_str   = f"{float(eth_val):.4f} ETH"

        print(f"  {str(block):<{col_block}}"
              f"{tx_hash:<{col_hash}}"
              f"{action:<{col_action}}"
              f"{eth_str:>{col_eth}}")

    print()


# ── [4] Data history report ───────────────────────────────────────────────────

def _data_history_report(w3: Web3, rc):
    _title("CLASS DATA HISTORY REPORT")
    print(f"  {CYAN}Reading student records …{RESET}")

    count = rc.functions.getStudentCount().call()

    if count == 0:
        _info("No students are registered yet.")
        return

    rows = []
    for i in range(count):
        addr = rc.functions.getStudentAt(i).call()
        name, grade, has_grade = rc.functions.getGrade(addr).call()
        rows.append({
            "address":   addr,
            "name":      name,
            "grade":     grade if has_grade else None,
            "has_grade": has_grade,
        })

    graded = [r for r in rows if r["has_grade"]]
    avg    = sum(r["grade"] for r in graded) / len(graded) if graded else None

    print()
    print(f"  {BOLD}{'#':<4}{'Name':<22}{'Address':<44}{'Grade':>7}{'Bar':<22}{RESET}")
    print(f"  {DIM}{'─'*98}{RESET}")

    for i, row in enumerate(rows, 1):
        name_str  = row["name"][:20]
        addr_str  = row["address"]
        if row["has_grade"]:
            g         = row["grade"]
            bar_len   = g // 5
            bar       = "█" * bar_len + "░" * (20 - bar_len)
            color     = GREEN if g >= 70 else YELLOW if g >= 50 else RED
            grade_str = f"{color}{g:>3}{RESET}"
            bar_str   = f"{color}{bar}{RESET}"
        else:
            grade_str = f"{DIM}N/A{RESET}"
            bar_str   = f"{DIM}{'─'*20}{RESET}"

        print(f"  {i:<4}{name_str:<22}{addr_str:<44}{grade_str:>7}  {bar_str}")

    print(f"\n  {DIM}{'─'*98}{RESET}")
    print(f"  Total students : {count}")
    print(f"  With grades    : {len(graded)}")
    if avg is not None:
        avg_color = GREEN if avg >= 70 else YELLOW if avg >= 50 else RED
        print(f"  Class average  : {avg_color}{BOLD}{avg:.1f}/100{RESET}")
    print()


# ── [5] Transfer GradeCoins ───────────────────────────────────────────────────

def _transfer_coins(w3: Web3, gc, active_account: str):
    _title("TRANSFER GRADECOINS")

    my_balance = coin_balance(gc, active_account)
    print(f"\n  Your GRC balance: {BOLD}{GREEN}{my_balance:,.4f} GRC{RESET}\n")

    if my_balance <= 0:
        _warn("You have no GradeCoins to transfer.")
        return

    addr_raw = _input("Recipient address: ")
    amount_s = _input("Amount of GRC to send: ")

    try:
        addr   = to_checksum(addr_raw)
        amount = float(amount_s)
        if amount <= 0:
            raise ValueError
    except ValueError:
        _err("Invalid address or amount.")
        return

    if amount > my_balance:
        _err(f"Insufficient balance. You have {my_balance:.4f} GRC.")
        return

    amount_wei = int(amount * 10**18)

    try:
        from blockchain_connector import send_tx
        send_tx(w3, gc.functions.transfer(addr, amount_wei), active_account)
        _ok(f"Sent {amount} GRC → {addr}")
    except RuntimeError as e:
        _err(str(e))