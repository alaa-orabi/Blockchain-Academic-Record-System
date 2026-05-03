#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
#  gui_main.py  –  Flask API server for the Report Card Web UI
#
#  Usage:
#    cd gui
#    python gui_main.py
#
#  Then open http://127.0.0.1:5000 in your browser.
#  Ganache must be running and 1-deploy.py + 2-setup.py must have been run.
# ─────────────────────────────────────────────────────────────────────────────

import sys
import os
import json
import io

# Fix Windows emoji/unicode issue
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Allow importing from the terminal_app folder (blockchain_connector lives there)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'terminal_app'))

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from web3 import Web3

# ── Import our existing connector ─────────────────────────────────────────────
from blockchain_connector import (
    connect, load_contracts, send_tx,
    eth_balance, coin_balance, to_checksum,
    get_all_transactions, tx_count_per_address
)

# ── Flask app setup ───────────────────────────────────────────────────────────
app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# ── Global state (loaded once at startup) ─────────────────────────────────────
w3        = None
rc        = None   # ReportCard contract
gc        = None   # GradeCoin contract
addresses = {}

def init_blockchain():
    global w3, rc, gc, addresses
    w3               = connect()
    rc, gc, addresses = load_contracts(w3)
    print(f"  ✔  Connected to Ganache  |  Chain ID: {w3.eth.chain_id}")
    print(f"  ✔  ReportCard : {addresses['ReportCard']}")
    print(f"  ✔  GradeCoin  : {addresses['GradeCoin']}")

# ─────────────────────────────────────────────────────────────────────────────
#  Helper
# ─────────────────────────────────────────────────────────────────────────────

def err(msg, code=400):
    return jsonify({"ok": False, "error": msg}), code

def ok(data=None):
    payload = {"ok": True}
    if data:
        payload.update(data)
    return jsonify(payload)

# ─────────────────────────────────────────────────────────────────────────────
#  ROUTES — Pages
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

# ─────────────────────────────────────────────────────────────────────────────
#  ROUTES — System info
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/info")
def api_info():
    """Return basic system info shown in the header."""
    try:
        return ok({
            "chainId":      w3.eth.chain_id,
            "blockNumber":  w3.eth.block_number,
            "admin":        addresses["admin"],
            "reportCard":   addresses["ReportCard"],
            "gradeCoin":    addresses["GradeCoin"],
            "paused":       rc.functions.paused().call(),
            "totalStudents": rc.functions.getStudentCount().call(),
            "totalSupply":  gc.functions.totalSupply().call() / 10**18,
            "accounts":     w3.eth.accounts,
        })
    except Exception as e:
        return err(str(e), 500)


@app.route("/api/accounts")
def api_accounts():
    """Return all Ganache accounts with their ETH and GRC balances."""
    try:
        admin = addresses["admin"].lower()
        result = []
        for acc in w3.eth.accounts:
            result.append({
                "address": acc,
                "eth":     eth_balance(w3, acc),
                "grc":     coin_balance(gc, acc),
                "isAdmin": acc.lower() == admin,
            })
        return ok({"accounts": result})
    except Exception as e:
        return err(str(e), 500)

# ─────────────────────────────────────────────────────────────────────────────
#  ROUTES — Students
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/students")
def api_students():
    """Return all registered students with their grades."""
    try:
        count = rc.functions.getStudentCount().call()
        students = []
        for i in range(count):
            addr = rc.functions.getStudentAt(i).call()
            name, grade, has_grade = rc.functions.getGrade(addr).call()
            students.append({
                "address":  addr,
                "name":     name,
                "grade":    grade if has_grade else None,
                "hasGrade": has_grade,
                "grc":      coin_balance(gc, addr),
                "eth":      eth_balance(w3, addr),
            })
        return ok({"students": students})
    except Exception as e:
        return err(str(e), 500)


@app.route("/api/student/<address>")
def api_student(address):
    """Return a single student's info."""
    try:
        addr = to_checksum(address)
        name, grade, has_grade = rc.functions.getGrade(addr).call()
        return ok({
            "address":  addr,
            "name":     name,
            "grade":    grade if has_grade else None,
            "hasGrade": has_grade,
            "grc":      coin_balance(gc, addr),
            "eth":      eth_balance(w3, addr),
        })
    except Exception as e:
        return err(str(e))


@app.route("/api/register", methods=["POST"])
def api_register():
    """Register a new student."""
    data    = request.json or {}
    address = data.get("address", "")
    name    = data.get("name", "").strip()

    if not name:
        return err("Name cannot be empty.")
    try:
        addr = to_checksum(address)
        send_tx(w3, rc.functions.registerUser(name), addr)
        return ok({"message": f"Registered '{name}' successfully."})
    except (ValueError, RuntimeError) as e:
        return err(str(e))

# ─────────────────────────────────────────────────────────────────────────────
#  ROUTES — Admin actions
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/grade", methods=["POST"])
def api_add_grade():
    """Admin: add or update a student's grade."""
    data    = request.json or {}
    admin   = data.get("admin", "")
    student = data.get("student", "")
    grade   = data.get("grade")

    try:
        admin_addr   = to_checksum(admin)
        student_addr = to_checksum(student)
        grade_int    = int(grade)
        if not (0 <= grade_int <= 100):
            raise ValueError("Grade must be 0–100.")
        send_tx(w3, rc.functions.addGrade(student_addr, grade_int), admin_addr)
        return ok({"message": f"Grade {grade_int} saved for {student_addr}."})
    except (ValueError, RuntimeError) as e:
        return err(str(e))


@app.route("/api/grade/batch", methods=["POST"])
def api_batch_grade():
    """Admin: batch add grades."""
    data    = request.json or {}
    admin   = data.get("admin", "")
    entries = data.get("entries", [])  # [{address, grade}, ...]

    try:
        admin_addr = to_checksum(admin)
        addrs  = [to_checksum(e["address"]) for e in entries]
        grades = [int(e["grade"]) for e in entries]
        for g in grades:
            if not (0 <= g <= 100):
                raise ValueError(f"Grade {g} out of range.")
        send_tx(w3, rc.functions.batchAddGrades(addrs, grades), admin_addr)
        return ok({"message": f"Batch of {len(addrs)} grades saved."})
    except (ValueError, RuntimeError) as e:
        return err(str(e))


@app.route("/api/mint", methods=["POST"])
def api_mint():
    """Admin: mint GradeCoins."""
    data      = request.json or {}
    admin     = data.get("admin", "")
    recipient = data.get("recipient", "")
    amount    = data.get("amount")

    try:
        admin_addr = to_checksum(admin)
        rec_addr   = to_checksum(recipient)
        amt        = float(amount)
        if amt <= 0:
            raise ValueError("Amount must be > 0.")
        amt_wei = int(amt * 10**18)
        send_tx(w3, gc.functions.mint(rec_addr, amt_wei), admin_addr)
        return ok({"message": f"Minted {amt} GRC → {rec_addr}."})
    except (ValueError, RuntimeError) as e:
        return err(str(e))


@app.route("/api/pause", methods=["POST"])
def api_pause():
    """Admin: pause the contract."""
    data  = request.json or {}
    admin = data.get("admin", "")
    try:
        admin_addr = to_checksum(admin)
        send_tx(w3, rc.functions.pause(), admin_addr)
        return ok({"message": "Contract paused."})
    except (ValueError, RuntimeError) as e:
        return err(str(e))


@app.route("/api/resume", methods=["POST"])
def api_resume():
    """Admin: resume the contract."""
    data  = request.json or {}
    admin = data.get("admin", "")
    try:
        admin_addr = to_checksum(admin)
        send_tx(w3, rc.functions.resume(), admin_addr)
        return ok({"message": "Contract resumed."})
    except (ValueError, RuntimeError) as e:
        return err(str(e))


@app.route("/api/transfer-ownership", methods=["POST"])
def api_transfer_ownership():
    """Admin: transfer ownership to a new address."""
    data      = request.json or {}
    admin     = data.get("admin", "")
    new_admin = data.get("newAdmin", "")
    try:
        admin_addr     = to_checksum(admin)
        new_admin_addr = to_checksum(new_admin)
        send_tx(w3, rc.functions.transferOwnership(new_admin_addr), admin_addr)
        send_tx(w3, gc.functions.transferOwnership(new_admin_addr), admin_addr)
        addresses["admin"] = new_admin_addr
        return ok({"message": f"Ownership transferred to {new_admin_addr}."})
    except (ValueError, RuntimeError) as e:
        return err(str(e))

# ─────────────────────────────────────────────────────────────────────────────
#  ROUTES — Balance & activity
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/balance/<address>")
def api_balance(address):
    """Return ETH + GRC balance for any address."""
    try:
        addr = to_checksum(address)
        return ok({
            "address": addr,
            "eth":     eth_balance(w3, addr),
            "grc":     coin_balance(gc, addr),
        })
    except Exception as e:
        return err(str(e))


@app.route("/api/activity/<address>")
def api_activity(address):
    """Return all on-chain transactions involving an address."""
    try:
        addr    = to_checksum(address)
        addr_lc = addr.lower()
        rc_lc   = addresses["ReportCard"].lower()
        gc_lc   = addresses["GradeCoin"].lower()

        all_txs = get_all_transactions(w3)
        relevant = [
            tx for tx in all_txs
            if tx["from"].lower() == addr_lc
            or (tx.get("to") or "").lower() == addr_lc
        ]

        def label(tx):
            to  = (tx.get("to")   or "").lower()
            frm = (tx.get("from") or "").lower()
            if frm == addr_lc and to == rc_lc:
                return "Interacted with ReportCard"
            if frm == addr_lc and to == gc_lc:
                return "Interacted with GradeCoin"
            if to == addr_lc:
                return "Received transaction"
            if frm == addr_lc:
                return "Sent transaction"
            return "Unknown"

        rows = [{
            "block":  tx["block"],
            "hash":   tx["hash"][:18] + "…",
            "action": label(tx),
            "eth":    float(w3.from_wei(tx["value"], "ether")),
        } for tx in relevant]

        return ok({"transactions": rows})
    except Exception as e:
        return err(str(e), 500)


@app.route("/api/dashboard")
def api_dashboard():
    """Return full dashboard data for the admin panel."""
    try:
        counts    = tx_count_per_address(w3)
        total_txs = sum(counts.values())
        top3      = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:3]

        count = rc.functions.getStudentCount().call()
        students = []
        grades_found = []
        for i in range(count):
            addr = rc.functions.getStudentAt(i).call()
            name, grade, has_grade = rc.functions.getGrade(addr).call()
            if has_grade:
                grades_found.append(grade)
            students.append({
                "address":  addr,
                "name":     name,
                "grade":    grade if has_grade else None,
                "hasGrade": has_grade,
            })

        return ok({
            "totalStudents": count,
            "totalSupply":   gc.functions.totalSupply().call() / 10**18,
            "totalTxs":      total_txs,
            "paused":        rc.functions.paused().call(),
            "admin":         rc.functions.getAdmin().call(),
            "blockNumber":   w3.eth.block_number,
            "top3":          [{"address": a, "count": c} for a, c in top3],
            "students":      students,
            "classAverage":  round(sum(grades_found)/len(grades_found), 1) if grades_found else None,
        })
    except Exception as e:
        return err(str(e), 500)


# ─────────────────────────────────────────────────────────────────────────────
#  ROUTES — Coin transfer (student)
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/api/transfer-coins", methods=["POST"])
def api_transfer_coins():
    """Student: transfer GradeCoins to another address."""
    data      = request.json or {}
    sender    = data.get("sender", "")
    recipient = data.get("recipient", "")
    amount    = data.get("amount")

    try:
        sender_addr = to_checksum(sender)
        rec_addr    = to_checksum(recipient)
        amt         = float(amount)
        if amt <= 0:
            raise ValueError("Amount must be > 0.")
        amt_wei = int(amt * 10**18)
        send_tx(w3, gc.functions.transfer(rec_addr, amt_wei), sender_addr)
        return ok({"message": f"Sent {amt} GRC → {rec_addr}."})
    except (ValueError, RuntimeError) as e:
        return err(str(e))


# ─────────────────────────────────────────────────────────────────────────────
#  Run
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n  📚  Report Card — Web UI Server")
    print("  ─────────────────────────────────────")
    try:
        init_blockchain()
    except Exception as e:
        print(f"\n  ✗  {e}\n")
        sys.exit(1)
    print("\n  ✔  Open your browser at:  http://127.0.0.1:5000\n")
    app.run(debug=True, port=5000)