# ─────────────────────────────────────────────────────────────────────────────
#  admin_menu.py
#  All admin-only operations:
#    • Add / batch-add grades
#    • Mint / batch-mint GradeCoins
#    • Pause / resume contract
#    • Transfer ownership
#    • Dashboard summary
#    • Ownership-transfer security demo
# ─────────────────────────────────────────────────────────────────────────────

from web3 import Web3
from blockchain_connector import (
    send_tx, eth_balance, coin_balance,
    get_all_transactions, tx_count_per_address, to_checksum
)

# ── Pretty-print helpers ──────────────────────────────────────────────────────

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


# ── Admin menu entry point ────────────────────────────────────────────────────

def run_admin_menu(w3: Web3, rc, gc, addresses: dict, active_account: str):
    """
    Show the admin menu. active_account is the wallet address the admin
    is acting from (must match admin on-chain, or actions will revert).
    """
    while True:
        print()
        _sep("═")
        print(f"{BOLD}{CYAN}  ⚙  ADMIN PANEL{RESET}")
        _sep("═")
        current_admin = rc.functions.getAdmin().call()
        is_paused     = rc.functions.paused().call()
        print(f"  Admin address : {BOLD}{current_admin}{RESET}")
        print(f"  Acting as     : {BOLD}{active_account}{RESET}")
        print(f"  Contract state: {'  ' + BOLD + RED + '⛔ PAUSED' + RESET if is_paused else BOLD + GREEN + '  ✅ ACTIVE' + RESET}")
        _sep()
        print(f"  {BOLD}[1]{RESET}  Add grade for a student")
        print(f"  {BOLD}[2]{RESET}  Batch-add grades (multiple students)")
        print(f"  {BOLD}[3]{RESET}  Mint GradeCoins to a student")
        print(f"  {BOLD}[4]{RESET}  Batch-mint GradeCoins")
        print(f"  {BOLD}[5]{RESET}  Dashboard — system summary")
        print(f"  {BOLD}[6]{RESET}  {'Resume' if is_paused else 'Pause'} the contract")
        print(f"  {BOLD}[7]{RESET}  Transfer admin ownership")
        print(f"  {BOLD}[8]{RESET}  Run ownership-transfer security demo")
        print(f"  {BOLD}[0]{RESET}  ← Back to main menu")
        _sep()

        choice = _input("Choose an option: ")

        if   choice == "1": _add_grade(w3, rc, active_account)
        elif choice == "2": _batch_add_grades(w3, rc, active_account)
        elif choice == "3": _mint_coins(w3, gc, active_account)
        elif choice == "4": _batch_mint_coins(w3, gc, active_account)
        elif choice == "5": _dashboard(w3, rc, gc, addresses)
        elif choice == "6": _toggle_pause(w3, rc, active_account, is_paused)
        elif choice == "7": _transfer_ownership(w3, rc, gc, active_account)
        elif choice == "8": _ownership_transfer_demo(w3, rc, gc, addresses)
        elif choice == "0": break
        else: _warn("Unknown option. Please try again.")


# ── [1] Add grade ─────────────────────────────────────────────────────────────

def _add_grade(w3: Web3, rc, admin: str):
    _title("ADD GRADE")
    addr_raw = _input("Student wallet address: ")
    grade_s  = _input("Grade (0-100): ")

    try:
        addr  = to_checksum(addr_raw)
        grade = int(grade_s)
        if not (0 <= grade <= 100):
            raise ValueError
    except ValueError:
        _err("Invalid address or grade. Grade must be an integer 0-100.")
        return

    try:
        send_tx(w3, rc.functions.addGrade(addr, grade), admin)
        _ok(f"Grade {grade} recorded for {addr}")
    except RuntimeError as e:
        _err(str(e))


# ── [2] Batch add grades ──────────────────────────────────────────────────────

def _batch_add_grades(w3: Web3, rc, admin: str):
    _title("BATCH ADD GRADES")
    _info("Enter student address and grade pairs, one per line.")
    _info("Leave the address blank when done.\n")

    addrs  = []
    grades = []

    while True:
        addr_raw = _input(f"Student address #{len(addrs)+1} (blank to finish): ")
        if not addr_raw:
            break
        grade_s = _input(f"Grade for student #{len(addrs)+1}: ")
        try:
            addr  = to_checksum(addr_raw)
            grade = int(grade_s)
            if not (0 <= grade <= 100):
                raise ValueError
        except ValueError:
            _err("Skipping: invalid address or grade.")
            continue

        addrs.append(addr)
        grades.append(grade)

    if not addrs:
        _warn("No entries to submit.")
        return

    print()
    _info(f"About to record {len(addrs)} grade(s):")
    for a, g in zip(addrs, grades):
        print(f"    {a}  →  {g}")
    confirm = _input("Confirm? (y/n): ")
    if confirm.lower() != "y":
        _warn("Cancelled.")
        return

    try:
        send_tx(w3, rc.functions.batchAddGrades(addrs, grades), admin)
        _ok(f"Batch of {len(addrs)} grades recorded successfully.")
    except RuntimeError as e:
        _err(str(e))


# ── [3] Mint coins ────────────────────────────────────────────────────────────

def _mint_coins(w3: Web3, gc, admin: str):
    _title("MINT GRADECOINS")
    addr_raw = _input("Recipient wallet address: ")
    amount_s = _input("Amount of GRC to mint: ")

    try:
        addr   = to_checksum(addr_raw)
        amount = float(amount_s)
        if amount <= 0:
            raise ValueError
    except ValueError:
        _err("Invalid address or amount.")
        return

    amount_wei = int(amount * 10**18)

    try:
        send_tx(w3, gc.functions.mint(addr, amount_wei), admin)
        _ok(f"Minted {amount} GRC → {addr}")
    except RuntimeError as e:
        _err(str(e))


# ── [4] Batch mint coins ──────────────────────────────────────────────────────

def _batch_mint_coins(w3: Web3, gc, admin: str):
    _title("BATCH MINT GRADECOINS")
    _info("Enter recipient address and amount pairs, one per line.")
    _info("Leave the address blank when done.\n")

    addrs   = []
    amounts = []

    while True:
        addr_raw = _input(f"Recipient address #{len(addrs)+1} (blank to finish): ")
        if not addr_raw:
            break
        amount_s = _input(f"Amount (GRC) for recipient #{len(addrs)+1}: ")
        try:
            addr   = to_checksum(addr_raw)
            amount = float(amount_s)
            if amount <= 0:
                raise ValueError
        except ValueError:
            _err("Skipping: invalid address or amount.")
            continue

        addrs.append(addr)
        amounts.append(int(amount * 10**18))

    if not addrs:
        _warn("No entries to submit.")
        return

    print()
    _info(f"About to mint to {len(addrs)} recipient(s):")
    for a, amt in zip(addrs, amounts):
        print(f"    {a}  →  {amt // 10**18} GRC")
    confirm = _input("Confirm? (y/n): ")
    if confirm.lower() != "y":
        _warn("Cancelled.")
        return

    try:
        send_tx(w3, gc.functions.batchMint(addrs, amounts), admin)
        _ok(f"Batch mint of {len(addrs)} recipients completed.")
    except RuntimeError as e:
        _err(str(e))


# ── [5] Dashboard ─────────────────────────────────────────────────────────────

def _dashboard(w3: Web3, rc, gc, addresses: dict):
    _title("ADMIN DASHBOARD")

    # ── contract stats ────────────────────────────────────────────────────────
    total_students = rc.functions.getStudentCount().call()
    total_supply   = gc.functions.totalSupply().call() / 10**18
    paused         = rc.functions.paused().call()
    admin_addr     = rc.functions.getAdmin().call()

    print(f"\n  {BOLD}Contract State{RESET}")
    print(f"    Admin            : {admin_addr}")
    print(f"    Paused           : {'Yes ⛔' if paused else 'No ✅'}")
    print(f"    Students on file : {total_students}")
    print(f"    GRC total supply : {total_supply:,.2f} GRC")

    # ── on-chain transactions ─────────────────────────────────────────────────
    print(f"\n  {BOLD}Scanning blockchain …{RESET}", end="", flush=True)
    counts = tx_count_per_address(w3)
    total_txs = sum(counts.values())
    print(f"\r  {BOLD}On-Chain Transactions{RESET}           ")
    print(f"    Total transactions : {total_txs}")

    # ── top 3 active addresses ────────────────────────────────────────────────
    print(f"\n  {BOLD}Top 3 Most Active Addresses{RESET}")
    sorted_addrs = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:3]
    if sorted_addrs:
        header = f"    {'#':<4}{'Address':<44}{'Txs':>5}"
        print(f"  {DIM}{header}{RESET}")
        print(f"  {DIM}{'─'*58}{RESET}")
        for rank, (addr, cnt) in enumerate(sorted_addrs, 1):
            print(f"    {rank:<4}{addr:<44}{cnt:>5}")
    else:
        _info("No transactions found yet.")

    # ── per-student grade summary ─────────────────────────────────────────────
    print(f"\n  {BOLD}Student Grade Summary{RESET}")
    header = f"    {'Address':<44}{'Name':<18}{'Grade':>7}"
    print(f"  {DIM}{header}{RESET}")
    print(f"  {DIM}{'─'*70}{RESET}")
    grades_found = []
    for i in range(total_students):
        addr = rc.functions.getStudentAt(i).call()
        name, grade, has_grade = rc.functions.getGrade(addr).call()
        grade_str = str(grade) if has_grade else "N/A"
        if has_grade:
            grades_found.append(grade)
        print(f"    {addr:<44}{name:<18}{grade_str:>7}")

    if grades_found:
        avg = sum(grades_found) / len(grades_found)
        print(f"\n    {BOLD}Class average: {avg:.1f}{RESET}")

    print()


# ── [6] Pause / resume ────────────────────────────────────────────────────────

def _toggle_pause(w3: Web3, rc, admin: str, currently_paused: bool):
    action = "resume" if currently_paused else "pause"
    _title(f"{'RESUME' if currently_paused else 'PAUSE'} CONTRACT")
    confirm = _input(f"Are you sure you want to {action} the contract? (y/n): ")
    if confirm.lower() != "y":
        _warn("Cancelled.")
        return

    try:
        fn = rc.functions.resume() if currently_paused else rc.functions.pause()
        send_tx(w3, fn, admin)
        state = "resumed ✅" if currently_paused else "paused ⛔"
        _ok(f"Contract is now {state}.")
    except RuntimeError as e:
        _err(str(e))


# ── [7] Transfer ownership ────────────────────────────────────────────────────

def _transfer_ownership(w3: Web3, rc, gc, admin: str):
    _title("TRANSFER ADMIN OWNERSHIP")
    _warn("This is irreversible from this account. The new address will be admin.")
    new_raw = _input("New admin address: ")

    try:
        new_addr = to_checksum(new_raw)
    except ValueError as e:
        _err(str(e))
        return

    confirm = _input(f"Transfer ownership to {new_addr}? (y/n): ")
    if confirm.lower() != "y":
        _warn("Cancelled.")
        return

    try:
        send_tx(w3, rc.functions.transferOwnership(new_addr), admin)
        send_tx(w3, gc.functions.transferOwnership(new_addr), admin)
        _ok(f"ReportCard admin → {new_addr}")
        _ok(f"GradeCoin admin  → {new_addr}")
        _warn("You no longer have admin rights. Returning to main menu.")
    except RuntimeError as e:
        _err(str(e))


# ── [8] Ownership-transfer security demo ─────────────────────────────────────

def _ownership_transfer_demo(w3: Web3, rc, gc, addresses: dict):
    """
    Automated script that:
     1. Does an admin action as the original admin  → should PASS
     2. Transfers ownership to account[1]
     3. Tries the same action from account[0]       → should FAIL
     4. Does the action from account[1]              → should PASS
    """
    _title("OWNERSHIP TRANSFER SECURITY DEMO")

    original_admin = addresses["admin"]
    new_admin      = w3.eth.accounts[1]

    # pick any registered student for the demo grade action
    student_count = rc.functions.getStudentCount().call()
    if student_count == 0:
        _err("No students registered. Run scripts/2-setup.py first.")
        return

    student_addr = rc.functions.getStudentAt(0).call()

    def try_add_grade(sender: str, grade: int) -> bool:
        """Return True on success, False on revert."""
        try:
            send_tx(w3, rc.functions.addGrade(student_addr, grade), sender)
            return True
        except RuntimeError:
            return False

    print()
    print(f"  Original admin : {original_admin}")
    print(f"  New admin      : {new_admin}")
    print(f"  Test student   : {student_addr}")
    print()

    # Step 1 ─ action by original admin
    result1 = try_add_grade(original_admin, 90)
    status1 = f"{GREEN}PASS ✔{RESET}" if result1 else f"{RED}FAIL ✗{RESET}"
    print(f"  [1] addGrade from original admin  → {status1}")

    # Step 2 ─ transfer both contracts
    try:
        send_tx(w3, rc.functions.transferOwnership(new_admin), original_admin)
        send_tx(w3, gc.functions.transferOwnership(new_admin), original_admin)
        print(f"  [2] Ownership transferred to new admin  → {GREEN}DONE ✔{RESET}")
    except RuntimeError as e:
        _err(f"Transfer failed: {e}")
        return

    # Step 3 ─ original admin should now be blocked
    result3 = try_add_grade(original_admin, 55)
    status3 = f"{GREEN}PASS ✔{RESET}" if not result3 else f"{RED}FAIL ✗{RESET}"
    print(f"  [3] addGrade from OLD admin (should fail) → {status3}")

    # Step 4 ─ new admin should succeed
    result4 = try_add_grade(new_admin, 77)
    status4 = f"{GREEN}PASS ✔{RESET}" if result4 else f"{RED}FAIL ✗{RESET}"
    print(f"  [4] addGrade from NEW admin (should pass) → {status4}")

    print()
    if result1 and not result3 and result4:
        _ok("All 4 steps passed. Ownership transfer works correctly.")
    else:
        _err("One or more steps failed. Check the output above.")

    _warn("Ownership is now held by the NEW admin account.")
    _warn(f"Update your active account to: {new_admin}")
    print()