// ─────────────────────────────────────────────────────────────────────────────
//  app.js  –  Report Card Web UI
//  Talks to the Flask API in gui_main.py
// ─────────────────────────────────────────────────────────────────────────────

const API = "";          // same origin — Flask serves everything
const ADMIN_PASSWORD = "admin123";

// ── State ─────────────────────────────────────────────────────────────────────
let activeAccount  = "";
let adminUnlocked  = false;
let systemInfo     = {};

// ─────────────────────────────────────────────────────────────────────────────
//  Utilities
// ─────────────────────────────────────────────────────────────────────────────

async function apiFetch(path, options = {}) {
  const res  = await fetch(API + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  return res.json();
}

async function apiGet(path) {
  return apiFetch(path);
}

async function apiPost(path, body) {
  return apiFetch(path, { method: "POST", body: JSON.stringify(body) });
}

// ── Toast ─────────────────────────────────────────────────────────────────────
let toastTimer;
function toast(msg, type = "info") {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.className   = `toast ${type}`;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.add("hidden"), 3500);
}

// ── Grade colour helper ───────────────────────────────────────────────────────
function gradeColor(g) {
  if (g === null || g === undefined) return "";
  if (g >= 70) return "grade-high";
  if (g >= 50) return "grade-mid";
  return "grade-low";
}
function barColor(g) {
  if (g === null || g === undefined) return "";
  if (g >= 70) return "bar-high";
  if (g >= 50) return "bar-mid";
  return "bar-low";
}

// ── Short address ─────────────────────────────────────────────────────────────
function shortAddr(addr) {
  if (!addr) return "—";
  return addr.slice(0, 8) + "…" + addr.slice(-6);
}

// ─────────────────────────────────────────────────────────────────────────────
//  Boot — load system info, populate account selector
// ─────────────────────────────────────────────────────────────────────────────

async function boot() {
  try {
    const data = await apiGet("/api/info");
    if (!data.ok) { toast("Cannot reach Flask server. Is gui_main.py running?", "error"); return; }

    systemInfo = data;
    activeAccount = data.accounts[0];

    // Header badges
    document.getElementById("badge-chain").textContent  = `Chain ${data.chainId}`;
    document.getElementById("badge-block").textContent  = `Block #${data.blockNumber}`;
    updatePausedBadge(data.paused);

    document.getElementById("hdr-students").textContent = data.totalStudents;
    document.getElementById("hdr-supply").textContent   = data.totalSupply.toFixed(2) + " GRC";

    // Populate account select
    const sel = document.getElementById("account-select");
    sel.innerHTML = "";
    data.accounts.forEach((acc, i) => {
      const opt  = document.createElement("option");
      opt.value  = acc;
      const tag  = acc.toLowerCase() === data.admin.toLowerCase() ? " [Admin]" : ` [Account ${i}]`;
      opt.textContent = acc + tag;
      sel.appendChild(opt);
    });

    await updateAccountBalances();
    loadStudents();

  } catch (e) {
    toast("Connection error: " + e.message, "error");
  }
}

function updatePausedBadge(paused) {
  const badge = document.getElementById("badge-paused");
  if (paused) {
    badge.textContent = "⛔ PAUSED";
    badge.className   = "badge badge-status paused";
  } else {
    badge.textContent = "✅ Active";
    badge.className   = "badge badge-status active";
  }
}

async function updateAccountBalances() {
  if (!activeAccount) return;
  const data = await apiGet(`/api/balance/${activeAccount}`);
  if (!data.ok) return;
  document.getElementById("acct-eth").textContent = data.eth.toFixed(4) + " ETH";
  document.getElementById("acct-grc").textContent = data.grc.toFixed(4) + " GRC";
}

// ─────────────────────────────────────────────────────────────────────────────
//  Tab switching
// ─────────────────────────────────────────────────────────────────────────────

document.querySelectorAll(".tab").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(s => s.classList.add("hidden"));
    btn.classList.add("active");
    const target = document.getElementById("tab-" + btn.dataset.tab);
    target.classList.remove("hidden");

    // Lazy-load per tab
    if (btn.dataset.tab === "wallet")    loadAccounts();
    if (btn.dataset.tab === "dashboard") loadDashboard();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
//  Account selector
// ─────────────────────────────────────────────────────────────────────────────

document.getElementById("account-select").addEventListener("change", async (e) => {
  activeAccount = e.target.value;
  await updateAccountBalances();
});

// ─────────────────────────────────────────────────────────────────────────────
//  Admin unlock
// ─────────────────────────────────────────────────────────────────────────────

document.getElementById("btn-unlock").addEventListener("click", () => {
  const pwd = document.getElementById("admin-password").value;
  if (pwd === ADMIN_PASSWORD) {
    adminUnlocked = true;
    document.getElementById("admin-overlay").classList.add("hidden");
    document.getElementById("admin-status").classList.remove("hidden");
    document.getElementById("admin-password").value = "";
    toast("Admin panel unlocked!", "success");
  } else {
    toast("Wrong password.", "error");
  }
});

// ─────────────────────────────────────────────────────────────────────────────
//  TAB: STUDENTS
// ─────────────────────────────────────────────────────────────────────────────

async function loadStudents() {
  const grid = document.getElementById("students-grid");
  grid.innerHTML = `<div class="loading">Loading students…</div>`;

  const data = await apiGet("/api/students");
  if (!data.ok) { grid.innerHTML = `<div class="loading">Error: ${data.error}</div>`; return; }

  if (data.students.length === 0) {
    grid.innerHTML = `<div class="loading">No students registered yet.</div>`;
    return;
  }

  grid.innerHTML = data.students.map(s => studentCardHTML(s)).join("");
}

function studentCardHTML(s) {
  const gradeNum  = s.hasGrade ? s.grade : null;
  const gradeDisp = s.hasGrade
    ? `<div class="grade-display">
         <span class="grade-num ${gradeColor(gradeNum)}">${gradeNum}</span>
         <span class="grade-denom">/100</span>
       </div>
       <div class="grade-bar-bg">
         <div class="grade-bar-fill ${barColor(gradeNum)}" style="width:${gradeNum}%"></div>
       </div>`
    : `<div class="grade-display"><span class="grade-na">No grade yet</span></div>
       <div class="grade-bar-bg"><div class="grade-bar-fill" style="width:0%"></div></div>`;

  return `
    <div class="student-card">
      <div class="student-name">${escHtml(s.name)}</div>
      <div class="student-addr">${s.address}</div>
      ${gradeDisp}
      <div class="student-balances">
        <div class="student-bal-item">
          <span class="student-bal-label">GRC</span>
          <span class="student-bal-val">${s.grc.toFixed(2)}</span>
        </div>
        <div class="student-bal-item">
          <span class="student-bal-label">ETH</span>
          <span class="student-bal-val">${s.eth.toFixed(4)}</span>
        </div>
      </div>
    </div>`;
}

function escHtml(str) {
  return str.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

document.getElementById("btn-refresh-students").addEventListener("click", loadStudents);

// Register
document.getElementById("btn-register").addEventListener("click", async () => {
  const name = document.getElementById("reg-name").value.trim();
  if (!name) { toast("Enter a name first.", "error"); return; }

  const data = await apiPost("/api/register", { address: activeAccount, name });
  if (data.ok) {
    toast(data.message, "success");
    document.getElementById("reg-name").value = "";
    loadStudents();
  } else {
    toast(data.error, "error");
  }
});

// ─────────────────────────────────────────────────────────────────────────────
//  TAB: ADMIN
// ─────────────────────────────────────────────────────────────────────────────

// Add Grade
document.getElementById("btn-add-grade").addEventListener("click", async () => {
  const student = document.getElementById("grade-addr").value.trim();
  const grade   = document.getElementById("grade-val").value;
  if (!student || grade === "") { toast("Fill in both fields.", "error"); return; }

  const data = await apiPost("/api/grade", { admin: activeAccount, student, grade: Number(grade) });
  if (data.ok) {
    toast(data.message, "success");
    document.getElementById("grade-addr").value = "";
    document.getElementById("grade-val").value  = "";
    loadStudents();
  } else {
    toast(data.error, "error");
  }
});

// Mint
document.getElementById("btn-mint").addEventListener("click", async () => {
  const recipient = document.getElementById("mint-addr").value.trim();
  const amount    = document.getElementById("mint-amount").value;
  if (!recipient || !amount) { toast("Fill in both fields.", "error"); return; }

  const data = await apiPost("/api/mint", { admin: activeAccount, recipient, amount: Number(amount) });
  if (data.ok) {
    toast(data.message, "success");
    document.getElementById("mint-addr").value   = "";
    document.getElementById("mint-amount").value = "";
    loadStudents();
    updateAccountBalances();
  } else {
    toast(data.error, "error");
  }
});

// Pause
document.getElementById("btn-pause").addEventListener("click", async () => {
  if (!confirm("Pause the contract? All student actions will be blocked.")) return;
  const data = await apiPost("/api/pause", { admin: activeAccount });
  if (data.ok) {
    toast(data.message, "success");
    updatePauseStatus(true);
    updatePausedBadge(true);
  } else {
    toast(data.error, "error");
  }
});

// Resume
document.getElementById("btn-resume").addEventListener("click", async () => {
  const data = await apiPost("/api/resume", { admin: activeAccount });
  if (data.ok) {
    toast(data.message, "success");
    updatePauseStatus(false);
    updatePausedBadge(false);
  } else {
    toast(data.error, "error");
  }
});

function updatePauseStatus(paused) {
  const el = document.getElementById("pause-status-text");
  if (paused) {
    el.textContent = "⛔ Contract is PAUSED";
    el.className   = "pause-status paused";
  } else {
    el.textContent = "✅ Contract is ACTIVE";
    el.className   = "pause-status active";
  }
}

// Load initial pause status into admin card
async function loadPauseStatus() {
  const data = await apiGet("/api/info");
  if (data.ok) updatePauseStatus(data.paused);
}
loadPauseStatus();

// Transfer Ownership
document.getElementById("btn-transfer-owner").addEventListener("click", async () => {
  const newAdmin = document.getElementById("new-admin-addr").value.trim();
  if (!newAdmin) { toast("Enter the new admin address.", "error"); return; }
  if (!confirm(`Transfer ownership to ${newAdmin}?\nThis cannot be undone from your current account.`)) return;

  const data = await apiPost("/api/transfer-ownership", { admin: activeAccount, newAdmin });
  if (data.ok) {
    toast(data.message, "success");
    document.getElementById("new-admin-addr").value = "";
    boot(); // reload info so header reflects new admin
  } else {
    toast(data.error, "error");
  }
});

// Batch grades — add row
document.getElementById("btn-add-batch-row").addEventListener("click", () => {
  const container = document.getElementById("batch-rows");
  const row = document.createElement("div");
  row.className = "batch-row";
  row.innerHTML = `
    <input type="text" placeholder="0x address…" class="input batch-addr" />
    <input type="number" placeholder="grade" min="0" max="100" class="input batch-grade" style="width:90px" />
    <button class="btn btn-sm btn-outline btn-remove-row">✕</button>`;
  container.appendChild(row);
});

document.getElementById("batch-rows").addEventListener("click", (e) => {
  if (e.target.classList.contains("btn-remove-row")) {
    const rows = document.querySelectorAll(".batch-row");
    if (rows.length > 1) e.target.closest(".batch-row").remove();
  }
});

// Submit batch
document.getElementById("btn-submit-batch").addEventListener("click", async () => {
  const entries = [];
  document.querySelectorAll(".batch-row").forEach(row => {
    const addr  = row.querySelector(".batch-addr").value.trim();
    const grade = row.querySelector(".batch-grade").value;
    if (addr && grade !== "") entries.push({ address: addr, grade: Number(grade) });
  });

  if (entries.length === 0) { toast("Add at least one entry.", "error"); return; }

  const data = await apiPost("/api/grade/batch", { admin: activeAccount, entries });
  if (data.ok) {
    toast(data.message, "success");
    loadStudents();
  } else {
    toast(data.error, "error");
  }
});

// ─────────────────────────────────────────────────────────────────────────────
//  TAB: WALLET
// ─────────────────────────────────────────────────────────────────────────────

// Balance checker
document.getElementById("btn-check-balance").addEventListener("click", async () => {
  const addr = document.getElementById("check-addr").value.trim();
  if (!addr) { toast("Enter an address.", "error"); return; }

  const data = await apiGet(`/api/balance/${addr}`);
  const res  = document.getElementById("balance-result");

  if (data.ok) {
    document.getElementById("res-eth").textContent = data.eth.toFixed(6) + " ETH";
    document.getElementById("res-grc").textContent = data.grc.toFixed(4) + " GRC";
    res.classList.remove("hidden");
  } else {
    toast(data.error, "error");
    res.classList.add("hidden");
  }
});

// Transfer coins
document.getElementById("btn-transfer-coins").addEventListener("click", async () => {
  const recipient = document.getElementById("transfer-to").value.trim();
  const amount    = document.getElementById("transfer-amount").value;
  if (!recipient || !amount) { toast("Fill in both fields.", "error"); return; }

  const data = await apiPost("/api/transfer-coins", {
    sender: activeAccount, recipient, amount: Number(amount)
  });
  if (data.ok) {
    toast(data.message, "success");
    document.getElementById("transfer-to").value     = "";
    document.getElementById("transfer-amount").value = "";
    updateAccountBalances();
  } else {
    toast(data.error, "error");
  }
});

// Accounts table
async function loadAccounts() {
  const container = document.getElementById("accounts-table");
  container.innerHTML = `<div class="loading">Loading…</div>`;

  const data = await apiGet("/api/accounts");
  if (!data.ok) { container.innerHTML = `<div class="loading">Error: ${data.error}</div>`; return; }

  const rows = data.accounts.map((a, i) => `
    <tr>
      <td>${i}</td>
      <td style="font-size:11px;word-break:break-all">${a.address} ${a.isAdmin ? '<span class="tag-admin">Admin</span>' : ""}</td>
      <td>${a.eth.toFixed(4)}</td>
      <td>${a.grc.toFixed(4)}</td>
    </tr>`).join("");

  container.innerHTML = `
    <table class="data-table">
      <thead><tr><th>#</th><th>Address</th><th>ETH</th><th>GRC</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
}

document.getElementById("btn-refresh-accounts").addEventListener("click", loadAccounts);

// ─────────────────────────────────────────────────────────────────────────────
//  TAB: ACTIVITY
// ─────────────────────────────────────────────────────────────────────────────

document.getElementById("btn-load-activity").addEventListener("click", async () => {
  const raw  = document.getElementById("activity-addr").value.trim();
  const addr = raw || activeAccount;
  const container = document.getElementById("activity-table");
  container.innerHTML = `<div class="loading">Scanning blockchain for ${shortAddr(addr)}…</div>`;

  const data = await apiGet(`/api/activity/${addr}`);
  if (!data.ok) { container.innerHTML = `<div class="loading">Error: ${data.error}</div>`; return; }

  if (data.transactions.length === 0) {
    container.innerHTML = `<div class="activity-empty">No transactions found for this address.</div>`;
    return;
  }

  const rows = data.transactions.map(tx => `
    <tr>
      <td>${tx.block}</td>
      <td style="font-size:11px">${tx.hash}</td>
      <td>${escHtml(tx.action)}</td>
      <td>${tx.eth.toFixed(4)} ETH</td>
    </tr>`).join("");

  container.innerHTML = `
    <table class="data-table">
      <thead><tr><th>Block</th><th>Tx Hash</th><th>Action</th><th>ETH Value</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
});

// ─────────────────────────────────────────────────────────────────────────────
//  TAB: DASHBOARD
// ─────────────────────────────────────────────────────────────────────────────

async function loadDashboard() {
  const container = document.getElementById("dashboard-content");
  container.innerHTML = `<div class="loading">Scanning blockchain…</div>`;

  const data = await apiGet("/api/dashboard");
  if (!data.ok) { container.innerHTML = `<div class="loading">Error: ${data.error}</div>`; return; }

  const avgStr = data.classAverage !== null ? `${data.classAverage}` : "N/A";
  const pauseStr = data.paused ? "⛔ Paused" : "✅ Active";

  const top3HTML = data.top3.length
    ? data.top3.map((t, i) => `
        <li>
          <span class="top3-rank">#${i+1}</span>
          <span class="top3-addr">${t.address}</span>
          <span class="top3-count">${t.count} txs</span>
        </li>`).join("")
    : "<li><span style='color:var(--text-mute)'>No transactions yet</span></li>";

  const studentRows = data.students.map(s => {
    const g = s.hasGrade ? s.grade : null;
    return `<tr>
      <td style="font-size:11px;word-break:break-all">${s.address}</td>
      <td>${escHtml(s.name)}</td>
      <td class="${gradeColor(g)}" style="font-weight:700">${g !== null ? g : "—"}</td>
      <td>
        <div class="grade-bar-bg" style="width:120px">
          <div class="grade-bar-fill ${barColor(g)}" style="width:${g||0}%"></div>
        </div>
      </td>
    </tr>`;
  }).join("");

  container.innerHTML = `
    <div class="dashboard-stats">
      <div class="dash-stat">
        <span class="dash-stat-val">${data.totalStudents}</span>
        <span class="dash-stat-label">Students</span>
      </div>
      <div class="dash-stat">
        <span class="dash-stat-val">${data.totalSupply.toFixed(0)}</span>
        <span class="dash-stat-label">GRC Minted</span>
      </div>
      <div class="dash-stat">
        <span class="dash-stat-val">${data.totalTxs}</span>
        <span class="dash-stat-label">Total Txs</span>
      </div>
      <div class="dash-stat">
        <span class="dash-stat-val">${avgStr}</span>
        <span class="dash-stat-label">Class Avg</span>
      </div>
      <div class="dash-stat">
        <span class="dash-stat-val">${data.blockNumber}</span>
        <span class="dash-stat-label">Block #</span>
      </div>
      <div class="dash-stat">
        <span class="dash-stat-val" style="${data.paused ? 'color:var(--danger)' : ''}">${pauseStr}</span>
        <span class="dash-stat-label">Status</span>
      </div>
    </div>

    <div class="card">
      <h3>👑 Top 3 Most Active Addresses</h3>
      <ul class="top3-list">${top3HTML}</ul>
    </div>

    <div class="card">
      <h3>📋 Student Grade Summary</h3>
      <p style="color:var(--text-mute);font-size:12px;margin-bottom:12px">
        Admin: ${data.admin}
      </p>
      <table class="data-table">
        <thead><tr><th>Address</th><th>Name</th><th>Grade</th><th>Bar</th></tr></thead>
        <tbody>${studentRows || '<tr><td colspan="4" style="color:var(--text-mute);text-align:center;padding:24px">No students yet</td></tr>'}</tbody>
      </table>
    </div>`;
}

document.getElementById("btn-refresh-dashboard").addEventListener("click", loadDashboard);

// ─────────────────────────────────────────────────────────────────────────────
//  Init
// ─────────────────────────────────────────────────────────────────────────────

boot();