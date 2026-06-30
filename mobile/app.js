// ── RCC Mobile PWA — Premium App (Streamlit-style) ──

const API = window.location.origin;
let currentUser = null;
let refreshTimer = null;
let selectedExec = "ALL";

// ── UTILS ──
function formatIndian(v) {
  if (!v || isNaN(v)) return '₹0';
  v = parseFloat(v);
  if (Math.abs(v) >= 10000000) return `₹${(v/10000000).toFixed(2)} Cr`;
  if (Math.abs(v) >= 100000) return `₹${(v/100000).toFixed(2)} L`;
  if (Math.abs(v) >= 1000) return `₹${(v/1000).toFixed(1)} K`;
  return `₹${v.toFixed(0)}`;
}

function fmtFullINR(v) {
  if (!v || isNaN(v)) return '₹0';
  v = Math.round(Math.abs(v));
  let s = v.toString();
  if (s.length <= 3) return `₹${s}`;
  let result = s.slice(-3);
  s = s.slice(0, -3);
  while (s.length > 0) {
    result = s.slice(-2) + ',' + result;
    s = s.slice(0, -2);
  }
  return `₹${result}`;
}

async function apiCall(endpoint, options = {}) {
  try {
    const res = await fetch(`${API}${endpoint}`, options);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error('API Error:', err);
    return null;
  }
}

function getFilterParams() {
  if (currentUser.role === 'admin' && selectedExec !== 'ALL') {
    return `user=${encodeURIComponent(selectedExec)}&role=executive`;
  }
  return `user=${encodeURIComponent(currentUser.username)}&role=${currentUser.role}`;
}

// ── THEME TOGGLE ──
let isLandscape = false;

function toggleLandscape() {
  isLandscape = !isLandscape;
  const app = document.getElementById('appContainer') || document.body;
  if (isLandscape) {
    app.style.transform = 'rotate(90deg)';
    app.style.transformOrigin = 'top left';
    app.style.width = '100vh';
    app.style.height = '100vw';
    app.style.position = 'fixed';
    app.style.top = '0';
    app.style.left = '100%';
    app.style.overflow = 'auto';
    document.getElementById('landscapeBtn').textContent = '📱';
  } else {
    app.style.transform = '';
    app.style.transformOrigin = '';
    app.style.width = '';
    app.style.height = '';
    app.style.position = '';
    app.style.top = '';
    app.style.left = '';
    app.style.overflow = '';
    document.getElementById('landscapeBtn').textContent = '🔄';
  }
}

function initTheme() {
  const saved = localStorage.getItem('rcc_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
  updateThemeBtn(saved);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'dark';
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('rcc_theme', next);
  updateThemeBtn(next);
  // Reload dashboard to update donut SVG colors
  if (currentUser) loadDashboard();
}

function updateThemeBtn(theme) {
  const btn = document.getElementById('themeBtn');
  if (btn) btn.textContent = theme === 'dark' ? '☀️' : '🌙';
}

initTheme();

// ── SERVICE WORKER ──
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/mobile/sw.js').catch(console.error);
}

// ── LOGIN ──
const loginScreen = document.getElementById('loginScreen');
const appContainer = document.getElementById('appContainer');
const loginBtn = document.getElementById('loginBtn');
const loginError = document.getElementById('loginError');

function checkSession() {
  const saved = localStorage.getItem('rcc_user');
  if (saved) {
    currentUser = JSON.parse(saved);
    showApp();
  }
}

loginBtn.addEventListener('click', async () => {
  const username = document.getElementById('loginUser').value.trim();
  const password = document.getElementById('loginPass').value;
  if (!username || !password) {
    loginError.style.display = 'block';
    loginError.textContent = 'Enter username and password';
    return;
  }
  loginBtn.textContent = 'Signing in...';
  loginBtn.disabled = true;
  const data = await apiCall('/api/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  loginBtn.textContent = 'Sign In';
  loginBtn.disabled = false;
  if (data && data.username) {
    currentUser = data;
    localStorage.setItem('rcc_user', JSON.stringify(data));
    showApp();
  } else {
    loginError.style.display = 'block';
    loginError.textContent = 'Invalid username or password';
  }
});

document.getElementById('loginPass').addEventListener('keypress', (e) => {
  if (e.key === 'Enter') loginBtn.click();
});

document.getElementById('logoutBtn').addEventListener('click', () => {
  localStorage.removeItem('rcc_user');
  currentUser = null;
  if (refreshTimer) clearInterval(refreshTimer);
  appContainer.classList.remove('active');
  loginScreen.classList.remove('hidden');
  document.getElementById('loginUser').value = '';
  document.getElementById('loginPass').value = '';
  loginError.style.display = 'none';
});

function showApp() {
  loginScreen.classList.add('hidden');
  appContainer.classList.add('active');
  document.getElementById('userBadge').textContent = currentUser.username;
  document.getElementById('menuFooter').textContent = `Logged in as ${currentUser.username}`;
  // Show menu button only for admin
  document.getElementById('menuBtn').style.display = currentUser.role === 'admin' ? 'inline-flex' : 'none';
  if (currentUser.role === 'admin') {
    loadExecFilter();
    loadPublicAccessStatus();
  }
  loadDashboard();
  loadTrails();
  loadRanking();
  refreshTimer = setInterval(() => { loadDashboard(); }, 30000);

  // Handle ?view= URL parameter for shared links
  const urlParams = new URLSearchParams(window.location.search);
  const view = urlParams.get('view');
  if (view) {
    let targetPage = null;
    if (view === 'trails') targetPage = 'pageTrails';
    else if (view === 'flowlist') targetPage = 'pageFlow';
    else if (view === 'search') targetPage = 'pageSearch';
    else if (view === 'ranking') targetPage = 'pageRanking';

    if (targetPage) {
      navItems.forEach(n => n.classList.remove('active'));
      pages.forEach(p => p.classList.remove('active'));
      document.getElementById(targetPage).classList.add('active');
      // Highlight correct nav item
      navItems.forEach(n => { if (n.dataset.page === targetPage) n.classList.add('active'); });
      // Load data for that page
      if (targetPage === 'pageTrails') loadTrails();
      if (targetPage === 'pageFlow') loadFlowList();
      if (targetPage === 'pageRanking') loadRanking();
      if (targetPage === 'pageSearch') loadSearchCases();
      if (targetPage === 'pageProjection') loadProjection();
    }
  }
}

// ── SIDE MENU ──
function toggleMenu() {
  const menu = document.getElementById('sideMenu');
  const overlay = document.getElementById('menuOverlay');
  const isOpen = menu.classList.contains('open');
  if (isOpen) {
    menu.classList.remove('open');
    overlay.classList.remove('open');
  } else {
    menu.classList.add('open');
    overlay.classList.add('open');
    const projToggle = document.getElementById('projToggle');
    if (projToggle) projToggle.checked = showProjection;
    loadPublicAccessStatus();
  }
}

function toggleAccordion(el) {
  const body = el.nextElementSibling;
  const arrow = el.querySelector('.acc-arrow');
  if (body.style.display === 'none') {
    body.style.display = 'block';
    arrow.classList.add('open');
  } else {
    body.style.display = 'none';
    arrow.classList.remove('open');
  }
}

function copyLink(type) {
  const baseUrl = 'https://app.rccapp.xyz';
  let url = '';
  if (type === 'trails') {
    url = `${baseUrl}/public/trails`;
  } else if (type === 'flowlist') {
    url = `${baseUrl}/public/flowlist`;
  } else if (type === 'search') {
    url = `${baseUrl}/public/search`;
  }
  navigator.clipboard.writeText(url).then(() => {
    showToast('✅ Link copied! Share on WhatsApp');
  }).catch(() => {
    prompt('Copy this link:', url);
  });
  toggleMenu();
}

// ── PUBLIC ACCESS TOGGLE ──
async function loadPublicAccessStatus() {
  try {
    const res = await fetch(`${API}/api/public-access`);
    const data = await res.json();
    const linkToggle = document.getElementById('linkToggle');
    const pwdToggle = document.getElementById('pwdToggle');
    const searchToggle = document.getElementById('searchToggle');
    const projToggle = document.getElementById('projToggle');
    if (linkToggle) linkToggle.checked = data.enabled;
    if (pwdToggle) pwdToggle.checked = data.password_required;
    if (searchToggle) searchToggle.checked = data.search_enabled;
    if (projToggle) {
      projToggle.checked = data.show_projection !== false;
      showProjection = data.show_projection !== false;
    }
    if (data.password) {
      const el = document.getElementById('currentPwd');
      if (el) el.textContent = data.password;
    }
    if (data.search_password) {
      const el = document.getElementById('searchPwd');
      if (el) el.textContent = data.search_password;
    }
  } catch(e) {}
}

async function togglePublicAccess() {
  try {
    const newState = document.getElementById('linkToggle').checked;
    await fetch(`${API}/api/public-access`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled: newState })
    });
    showToast(newState ? '🔓 Links enabled' : '🔒 Links disabled');
  } catch(e) {
    showToast('❌ Error toggling access');
  }
}

// ── PASSWORD CONTROL ──
async function togglePasswordRequired() {
  try {
    const newState = document.getElementById('pwdToggle').checked;
    await fetch(`${API}/api/public-access`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password_required: newState })
    });
    showToast(newState ? '🔑 Password ON' : '🔓 Password OFF');
  } catch(e) {
    showToast('❌ Error toggling password');
  }
}

async function changePassword() {
  const newPwd = prompt('Enter new password for public links:');
  if (!newPwd || newPwd.trim() === '') return;
  try {
    await fetch(`${API}/api/public-access`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: newPwd.trim() })
    });
    document.getElementById('currentPwd').textContent = newPwd.trim();
    showToast('✅ Password changed to: ' + newPwd.trim());
  } catch(e) {
    showToast('❌ Error changing password');
  }
}

// ── SEARCH/ACTION CENTER ACCESS ──
async function toggleSearchAccess() {
  try {
    const newState = document.getElementById('searchToggle').checked;
    await fetch(`${API}/api/public-access`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ search_enabled: newState })
    });
    showToast(newState ? '🔓 Action Center enabled' : '🔒 Action Center disabled');
  } catch(e) {
    showToast('❌ Error toggling access');
  }
}

async function changeSearchPassword() {
  const newPwd = prompt('Enter new password for Action Center:');
  if (!newPwd || newPwd.trim() === '') return;
  try {
    await fetch(`${API}/api/public-access`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ search_password: newPwd.trim() })
    });
    document.getElementById('searchPwd').textContent = newPwd.trim();
    showToast('✅ Search password changed to: ' + newPwd.trim());
  } catch(e) {
    showToast('❌ Error changing password');
  }
}

function showToast(msg) {
  let toast = document.getElementById('toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'toast';
    toast.className = 'toast';
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 2500);
}

// ── PROJECTION TOGGLE ──
let showProjection = localStorage.getItem('rcc_projection') !== 'false';

function toggleProjection() {
  showProjection = document.getElementById('projToggle').checked;
  localStorage.setItem('rcc_projection', showProjection);
  showToast(showProjection ? '📊 Projection visible' : '📊 Projection hidden');
  // Sync to server for public pages
  fetch(`${API}/api/public-access`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({show_projection: showProjection})
  }).catch(() => {});
  loadFlowList();
}

async function forceRefresh() {
  showToast('🔄 Syncing data...');
  try {
    await fetch(`${API}/api/force-sync`, { method: 'POST' });
  } catch(e) {}
  // Reload active page
  const activePage = document.querySelector('.page.active');
  if (activePage) {
    const id = activePage.id;
    if (id === 'pageDashboard') loadDashboard();
    else if (id === 'pageTrails') loadTrails();
    else if (id === 'pageFlow') loadFlowList();
    else if (id === 'pageSearch') loadSearchCases();
    else if (id === 'pageRanking') loadRanking();
    else loadDashboard();
  } else {
    loadDashboard();
  }
  showToast('✅ Data refreshed!');
}

let deferredPrompt = null;
window.addEventListener('beforeinstallprompt', (e) => { e.preventDefault(); deferredPrompt = e; });
function installApp() {
  if (deferredPrompt) {
    deferredPrompt.prompt();
    deferredPrompt = null;
  } else {
    alert('Use browser menu → "Add to Home Screen" to install');
  }
  toggleMenu();
}

// ── VISITOR LOGS ──
async function showVisitorLogs() {
  toggleMenu();
  hideExecFilter();
  const data = await apiCall('/api/visitor-logs');
  if (!data || !data.logs || !data.logs.length) {
    // Show empty state in page instead of just toast
    const pages = document.querySelectorAll('.page');
    const navItems = document.querySelectorAll('.nav-item');
    pages.forEach(p => p.classList.remove('active'));
    navItems.forEach(n => n.classList.remove('active'));
    document.getElementById('pageFlow').classList.add('active');
    document.getElementById('flowContent').innerHTML = `
      <div class="summary-banner">
        <div class="banner-left">
          <span style="font-size:1.3rem">👁️</span>
          <div>
            <div class="banner-label">VISITOR LOGS</div>
            <div class="banner-value">0</div>
          </div>
        </div>
      </div>
      <div class="empty-state"><div class="emoji">📋</div><div class="msg">No logs yet. Jab koi public link kholega tab yahan dikhega.</div></div>
    `;
    return;
  }
  let rows = '';
  data.logs.forEach(l => {
    rows += `<tr><td style="font-size:.7rem">${l.time}</td><td>${l.page}</td><td><b>${l.executive}</b></td><td>${l.device}</td></tr>`;
  });
  // Show in flow content area (reuse page)
  const pages = document.querySelectorAll('.page');
  const navItems = document.querySelectorAll('.nav-item');
  pages.forEach(p => p.classList.remove('active'));
  navItems.forEach(n => n.classList.remove('active'));
  document.getElementById('pageFlow').classList.add('active');
  document.getElementById('flowContent').innerHTML = `
    <div class="summary-banner">
      <div class="banner-left">
        <span style="font-size:1.3rem">👁️</span>
        <div>
          <div class="banner-label">VISITOR LOGS</div>
          <div class="banner-value">${data.logs.length}</div>
        </div>
      </div>
    </div>
    <div class="rcc-table-wrap">
      <table class="rcc-table">
        <thead><tr><th>TIME</th><th>PAGE</th><th>EXECUTIVE</th><th>DEVICE</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

// ── TILL TIME REPORT ──
async function generateReport() {
  toggleMenu();
  hideExecFilter();
  // Show date picker
  const pages = document.querySelectorAll('.page');
  const navItems = document.querySelectorAll('.nav-item');
  pages.forEach(p => p.classList.remove('active'));
  navItems.forEach(n => n.classList.remove('active'));
  document.getElementById('pageFlow').classList.add('active');
  
  const now = new Date();
  document.getElementById('flowContent').innerHTML = `
    <div class="summary-banner">
      <div class="banner-left">
        <span style="font-size:1.3rem">📊</span>
        <div>
          <div class="banner-label">TILL TIME REPORT</div>
          <div class="banner-value">Select Date</div>
        </div>
      </div>
    </div>
    <div style="text-align:center;padding:20px">
      <input type="date" id="reportDatePicker" value="${now.toISOString().split('T')[0]}" style="padding:12px 16px;border:2px solid var(--accent);border-radius:8px;font-size:16px;font-weight:700;background:var(--surface);color:var(--ink);font-family:var(--font)">
      <br><br>
      <button onclick="fetchReport()" style="background:linear-gradient(135deg,#2563eb,#1d4ed8);color:#fff;border:none;padding:14px 32px;border-radius:8px;font-weight:700;font-size:15px;cursor:pointer">📊 Generate</button>
    </div>
  `;
}

async function fetchReport() {
  const dateInput = document.getElementById('reportDatePicker').value;
  const parts = dateInput.split('-');
  const dateStr = parts[2] + '.' + parts[1] + '.' + parts[0].slice(-2);
  
  showToast('📊 Generating report...');
  const data = await apiCall(`/api/report/tilltime?date=${encodeURIComponent(dateStr)}`);
  if (!data || data.error) {
    showToast('❌ Report generation failed');
    return;
  }

  // Also fetch resolution for overall RESL %
  const res1 = await apiCall('/api/report/resolution?bucket=1');
  const res2 = await apiCall('/api/report/resolution?bucket=2');
  const totalResl = res1 && res1.grand ? res1.grand.resl : 0;
  const totalRes2 = res2 && res2.grand ? res2.grand.resl : 0;
  const todayMovement = res1 ? res1.movement : 0;

  // Fetch total receipt cut %
  const rcData = await apiCall('/api/report/receiptcut');
  const totalRcPct = rcData && rcData.grand ? rcData.grand.pct_achi : 0;

  const buckets = data.buckets || [];
  const now = new Date();
  const timeStr = now.toLocaleTimeString('en-IN', {hour:'2-digit', minute:'2-digit', hour12:true}).toUpperCase();

  // Count table rows
  let countRows = '';
  let teams = Object.keys(data.team_count).sort();
  teams.forEach(team => {
    let total = 0;
    let cells = buckets.map(b => {
      const v = data.team_count[team][b] || 0;
      total += v;
      return `<td style="text-align:center;padding:10px 12px;font-size:13px;font-weight:700;color:#1e293b;border:1px solid #e2e8f0">${v || ''}</td>`;
    }).join('');
    countRows += `<tr><td style="padding:10px 14px;font-size:12px;font-weight:700;color:#1e293b;border:1px solid #e2e8f0">👤 ${team}</td>${cells}<td style="text-align:center;padding:10px 12px;color:#1e40af;font-weight:900;font-size:14px;border:1px solid #e2e8f0">${total}</td></tr>`;
  });
  let grandTotal = Object.values(data.grand_count).reduce((a,b)=>a+b, 0);
  let grandCells = buckets.map(b => `<td style="text-align:center;padding:10px 12px;color:#059669;font-weight:900;font-size:14px;border:1px solid #e2e8f0">${data.grand_count[b] || 0}</td>`).join('');
  countRows += `<tr style="background:#f0fdf4"><td style="padding:10px 14px;color:#059669;font-weight:900;font-size:12px;border:1px solid #e2e8f0">TOTAL</td>${grandCells}<td style="text-align:center;padding:10px 12px;color:#1e40af;font-weight:900;font-size:15px;border:1px solid #e2e8f0">${grandTotal}</td></tr>`;

  // POS table rows
  let posRows = '';
  teams.forEach(team => {
    let cells = buckets.map(b => {
      const v = data.team_pos[team][b] || 0;
      return `<td style="text-align:center;padding:10px 12px;color:#059669;font-size:12px;font-weight:700;border:1px solid #e2e8f0">${v ? '₹' + fmtIndianFull(v) : ''}</td>`;
    }).join('');
    posRows += `<tr><td style="padding:10px 14px;font-size:12px;font-weight:700;color:#1e293b;border:1px solid #e2e8f0">${team}</td>${cells}</tr>`;
  });
  let grandPosCells = buckets.map(b => `<td style="text-align:center;padding:10px 12px;color:#1e40af;font-weight:900;font-size:13px;border:1px solid #e2e8f0">${data.grand_pos[b] ? '₹' + fmtIndianFull(data.grand_pos[b]) : ''}</td>`).join('');
  posRows += `<tr style="background:#eff6ff"><td style="padding:10px 14px;color:#1e40af;font-weight:900;font-size:12px;border:1px solid #e2e8f0">GRAND TOTAL</td>${grandPosCells}</tr>`;

  const reportHtml = `
    <div id="reportCard" style="width:620px;background:#ffffff;border-radius:4px;padding:28px 30px;font-family:'Inter',-apple-system,sans-serif;color:#0f172a;box-shadow:0 2px 12px rgba(15,23,42,.06);border:2px solid #1e293b">
      <div style="text-align:center;margin-bottom:20px;padding-bottom:14px;border-bottom:3px solid #2563eb">
        <div style="font-size:22px;font-weight:900;color:#0f172a;letter-spacing:-.01em">TILL TIME PAYMENTS</div>
        <div style="font-size:12px;color:#64748b;margin-top:6px;font-weight:600">📅 ${data.date} &nbsp;|&nbsp; 🕐 ${timeStr} &nbsp;|&nbsp; <span style="color:#2563eb;font-weight:800">${data.total_paid_today}</span> Payments</div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:22px">
        <div style="border:1.5px solid #93c5fd;border-radius:10px;padding:12px 10px;text-align:center">
          <div style="font-size:8px;color:#64748b;font-weight:800;letter-spacing:.08em;margin-bottom:4px">RECEIPT CUT</div>
          <div style="font-size:22px;font-weight:900;color:#1d4ed8">${totalRcPct}%</div>
          <div style="font-size:10px;color:#1d4ed8;font-weight:800;margin-top:4px">+${data.rc_movement}% today</div>
        </div>
        <div style="border:1.5px solid #6ee7b7;border-radius:10px;padding:12px 10px;text-align:center">
          <div style="font-size:8px;color:#64748b;font-weight:800;letter-spacing:.08em;margin-bottom:4px">BKT-1 RES</div>
          <div style="font-size:22px;font-weight:900;color:#047857">${totalResl.toFixed(1)}%</div>
          <div style="font-size:10px;color:#059669;font-weight:800;margin-top:4px">+${data.bkt1_movement}% today</div>
        </div>
        <div style="border:1.5px solid #c4b5fd;border-radius:10px;padding:12px 10px;text-align:center">
          <div style="font-size:8px;color:#64748b;font-weight:800;letter-spacing:.08em;margin-bottom:4px">BKT-2 RES</div>
          <div style="font-size:22px;font-weight:900;color:#6d28d9">${totalRes2.toFixed(1)}%</div>
          <div style="font-size:10px;color:#7c3aed;font-weight:800;margin-top:4px">+${data.bkt2_movement}% today</div>
        </div>
      </div>
      <div style="font-size:11px;color:#1e293b;font-weight:800;margin-bottom:8px;letter-spacing:.03em">👥 · EXECUTIVE WISE (COUNT)</div>
      <table style="width:100%;border-collapse:collapse;border:1.5px solid #1e293b;margin-bottom:20px">
        <thead><tr style="background:#0f172a"><th style="text-align:left;padding:10px 14px;font-size:10px;font-weight:800;color:#e2e8f0;border:1px solid #334155">TEAM</th>${buckets.map(b => `<th style="text-align:center;padding:10px 12px;font-size:10px;font-weight:800;color:#e2e8f0;border:1px solid #334155">BKT ${b}</th>`).join('')}<th style="text-align:center;padding:10px 12px;font-size:10px;font-weight:800;color:#e2e8f0;border:1px solid #334155">TOTAL</th></tr></thead>
        <tbody>${countRows}</tbody>
      </table>
      <div style="font-size:11px;color:#1e293b;font-weight:800;margin-bottom:8px;letter-spacing:.03em">💰 · COLLECTION (POS AMOUNT)</div>
      <table style="width:100%;border-collapse:collapse;border:1.5px solid #1e293b">
        <thead><tr style="background:#0f172a"><th style="text-align:left;padding:10px 14px;font-size:10px;font-weight:800;color:#e2e8f0;border:1px solid #334155">TEAM</th>${buckets.map(b => `<th style="text-align:center;padding:10px 12px;font-size:10px;font-weight:800;color:#e2e8f0;border:1px solid #334155">BKT ${b} (POS)</th>`).join('')}</tr></thead>
        <tbody>${posRows}</tbody>
      </table>
      <div style="text-align:center;margin-top:14px"><div style="font-size:9px;color:#94a3b8;font-weight:600">📊 Till Time Payments &nbsp;|&nbsp; Generated at ${timeStr}</div></div>
    </div>
  `;

  const pages = document.querySelectorAll('.page');
  const navItems = document.querySelectorAll('.nav-item');
  pages.forEach(p => p.classList.remove('active'));
  navItems.forEach(n => n.classList.remove('active'));
  document.getElementById('pageFlow').classList.add('active');
  document.getElementById('flowContent').innerHTML = `
    <div style="text-align:center;margin-bottom:12px">
      <button onclick="copyReportImage()" style="background:linear-gradient(135deg,#2563eb,#1d4ed8);color:#fff;border:none;padding:12px 24px;border-radius:8px;font-weight:700;font-size:14px;cursor:pointer">📋 Copy Image</button>
      <button onclick="shareReport()" style="background:linear-gradient(135deg,#25d366,#128c7e);color:#fff;border:none;padding:12px 24px;border-radius:8px;font-weight:700;font-size:14px;cursor:pointer;margin-left:8px">📤 Share</button>
      <button onclick="zoomReport(1)" style="background:#f1f5f9;border:1px solid #e2e8f0;padding:10px 14px;border-radius:8px;font-size:16px;cursor:pointer;margin-left:8px">🔍+</button>
      <button onclick="zoomReport(-1)" style="background:#f1f5f9;border:1px solid #e2e8f0;padding:10px 14px;border-radius:8px;font-size:16px;cursor:pointer;margin-left:4px">🔍−</button>
    </div>
    <div id="reportContainer" style="overflow:auto;padding:10px;-webkit-overflow-scrolling:touch">${reportHtml}</div>
  `;
}

let reportZoom = 1;
function zoomReport(dir) {
  reportZoom += dir * 0.2;
  reportZoom = Math.max(0.5, Math.min(2, reportZoom));
  const card = document.getElementById('reportCard');
  if (card) card.style.transform = 'scale(' + reportZoom + ')';
  if (card) card.style.transformOrigin = 'top left';
}

// ── RESOLUTION TABLE ──
async function generateResolutionTable() {
  toggleMenu();
  hideExecFilter();
  const pages = document.querySelectorAll('.page');
  const navItems = document.querySelectorAll('.nav-item');
  pages.forEach(p => p.classList.remove('active'));
  navItems.forEach(n => n.classList.remove('active'));
  document.getElementById('pageFlow').classList.add('active');
  document.getElementById('flowContent').innerHTML = `
    <div class="summary-banner">
      <div class="banner-left">
        <span style="font-size:1.3rem">📋</span>
        <div>
          <div class="banner-label">RESOLUTION TABLE</div>
          <div class="banner-value">Select BKT</div>
        </div>
      </div>
    </div>
    <div style="text-align:center;padding:20px">
      <button onclick="fetchResTable(1)" style="background:linear-gradient(135deg,#059669,#10b981);color:#fff;border:none;padding:14px 28px;border-radius:8px;font-weight:700;font-size:15px;cursor:pointer;margin:6px">BKT-1</button>
      <button onclick="fetchResTable(2)" style="background:linear-gradient(135deg,#2563eb,#3b82f6);color:#fff;border:none;padding:14px 28px;border-radius:8px;font-weight:700;font-size:15px;cursor:pointer;margin:6px">BKT-2</button>
      <button onclick="fetchReceiptCut()" style="background:linear-gradient(135deg,#0891b2,#06b6d4);color:#fff;border:none;padding:14px 28px;border-radius:8px;font-weight:700;font-size:15px;cursor:pointer;margin:6px">🧾 Receipt Cut</button>
      <button onclick="fetchBucketSummary()" style="background:linear-gradient(135deg,#7c3aed,#8b5cf6);color:#fff;border:none;padding:14px 28px;border-radius:8px;font-weight:700;font-size:15px;cursor:pointer;margin:6px">📊 Bucket Summary</button>
      <button onclick="shareAllReports()" style="background:linear-gradient(135deg,#dc2626,#ef4444);color:#fff;border:none;padding:14px 28px;border-radius:8px;font-weight:700;font-size:15px;cursor:pointer;margin:6px">📤 Share All</button>
    </div>
  `;
}

async function fetchResTable(bucket) {
  resTableCurrentBucket = bucket;
  showToast('📋 Loading...');
  const data = await apiCall(`/api/report/resolution?bucket=${bucket}`);
  if (!data || data.error || !data.teams.length) {
    showToast('❌ No data');
    return;
  }

  // Apply sort
  if (resTableSortMode === 'resl_asc') data.teams.sort((a,b) => a.resl - b.resl);
  else if (resTableSortMode === 'az') data.teams.sort((a,b) => a.team.localeCompare(b.team));
  else if (resTableSortMode === 'za') data.teams.sort((a,b) => b.team.localeCompare(a.team));
  // resl_desc is default from API

  function fmtInd(v) { if (!v) return ''; v=Math.round(v); let s=v.toString(); if(s.length<=3) return s; let r=s.slice(-3); s=s.slice(0,-3); while(s.length>0){r=s.slice(-2)+','+r; s=s.slice(0,-2);} return r; }
  function reslColor(r) { if(r>=80) return '#10b981'; if(r>=50) return '#f59e0b'; if(r>=30) return '#f97316'; return '#ef4444'; }
  function reslBg(r) { if(r>=80) return 'rgba(16,185,129,.12)'; if(r>=50) return 'rgba(245,158,11,.1)'; if(r>=30) return 'rgba(249,115,22,.1)'; return 'rgba(239,68,68,.1)'; }
  function barWidth(r) { return Math.min(r, 100); }

  let rows = '';
  data.teams.forEach((t, i) => {
    const c = reslColor(t.resl);
    const bg = reslBg(t.resl);
    const rank = i + 1;
    const rankIcon = rank === 1 ? '🥇' : rank === 2 ? '🥈' : rank === 3 ? '🥉' : `<span style="color:#94a3b8;font-size:11px">${rank}</span>`;
    rows += `<tr style="background:${i%2===0?'#ffffff':'#f8fafc'}">
      <td style="padding:9px 8px;text-align:center;border-bottom:1px solid #f1f5f9;border-right:1px solid #f1f5f9;font-size:14px">${rankIcon}</td>
      <td style="padding:9px 10px;font-size:12px;font-weight:700;color:#0f172a;border-bottom:1px solid #f1f5f9;border-right:1px solid #f1f5f9;white-space:nowrap">${t.team}</td>
      <td style="text-align:right;padding:9px 10px;font-size:12px;font-family:'JetBrains Mono',monospace;color:#ef4444;border-bottom:1px solid #f1f5f9;border-right:1px solid #f1f5f9;font-weight:600">${fmtInd(t.flow)}</td>
      <td style="text-align:right;padding:9px 10px;font-size:12px;font-family:'JetBrains Mono',monospace;color:#059669;border-bottom:1px solid #f1f5f9;border-right:1px solid #f1f5f9;font-weight:600">${fmtInd(t.stable)}</td>
      <td style="text-align:right;padding:9px 10px;font-size:12px;font-family:'JetBrains Mono',monospace;color:#d97706;border-bottom:1px solid #f1f5f9;border-right:1px solid #f1f5f9;font-weight:600">${fmtInd(t.rb)}</td>
      <td style="text-align:right;padding:9px 10px;font-size:12px;font-family:'JetBrains Mono',monospace;font-weight:800;color:#0f172a;border-bottom:1px solid #f1f5f9;border-right:1px solid #f1f5f9">${fmtInd(t.grand_total)}</td>
      <td style="text-align:center;padding:9px 8px;font-size:12px;font-weight:700;color:#059669;border-bottom:1px solid #f1f5f9;border-right:1px solid #f1f5f9">${t.stable_pct.toFixed(1)}</td>
      <td style="text-align:center;padding:9px 8px;font-size:12px;font-weight:700;color:#d97706;border-bottom:1px solid #f1f5f9;border-right:1px solid #f1f5f9">${t.rb_pct.toFixed(1)}</td>
      <td style="padding:9px 10px;border-bottom:1px solid #f1f5f9;min-width:100px">
        <div style="display:flex;align-items:center;gap:6px">
          <div style="flex:1;height:8px;background:#f1f5f9;border-radius:4px;overflow:hidden"><div style="height:100%;width:${barWidth(t.resl)}%;background:linear-gradient(90deg,${c},${c}88);border-radius:4px"></div></div>
          <span style="font-size:13px;font-weight:900;color:${c};min-width:45px;text-align:right">${t.resl.toFixed(1)}%</span>
        </div>
      </td>
    </tr>`;
  });
  // Grand total
  const g = data.grand;
  rows += `<tr style="background:linear-gradient(135deg,#0f172a,#1e293b)">
    <td style="padding:10px 8px;text-align:center;color:#fbbf24;font-size:12px;font-weight:800" colspan="2">GRAND TOTAL</td>
    <td style="text-align:right;padding:10px 10px;font-size:12px;font-family:'JetBrains Mono',monospace;font-weight:700;color:#f87171">${fmtInd(g.flow)}</td>
    <td style="text-align:right;padding:10px 10px;font-size:12px;font-family:'JetBrains Mono',monospace;font-weight:700;color:#4ade80">${fmtInd(g.stable)}</td>
    <td style="text-align:right;padding:10px 10px;font-size:12px;font-family:'JetBrains Mono',monospace;font-weight:700;color:#fbbf24">${fmtInd(g.rb)}</td>
    <td style="text-align:right;padding:10px 10px;font-size:12px;font-family:'JetBrains Mono',monospace;font-weight:900;color:#fff">${fmtInd(g.grand_total)}</td>
    <td style="text-align:center;padding:10px 8px;font-size:12px;font-weight:800;color:#4ade80">${g.stable_pct.toFixed(1)}</td>
    <td style="text-align:center;padding:10px 8px;font-size:12px;font-weight:800;color:#fbbf24">${g.rb_pct.toFixed(1)}</td>
    <td style="padding:10px 10px">
      <div style="display:flex;align-items:center;gap:6px">
        <div style="flex:1;height:8px;background:rgba(255,255,255,.2);border-radius:4px;overflow:hidden"><div style="height:100%;width:${barWidth(g.resl)}%;background:linear-gradient(90deg,#fbbf24,#f59e0b);border-radius:4px"></div></div>
        <span style="font-size:14px;font-weight:900;color:#fbbf24;min-width:45px;text-align:right">${g.resl.toFixed(1)}%</span>
      </div>
    </td>
  </tr>`;

  const now = new Date();
  const timeStr = now.toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit',hour12:true}).toUpperCase();

  const reportHtml = `
    <div id="resTableCard" style="width:680px;background:linear-gradient(180deg,#ffffff,#f8fafc);border-radius:16px;padding:24px;font-family:'Inter',sans-serif;color:#0f172a;box-shadow:0 12px 40px rgba(0,0,0,.12);border:1px solid #e2e8f0">
      <div style="text-align:center;margin-bottom:18px">
          <div style="font-size:11px;color:#64748b;font-weight:700;letter-spacing:.08em">RESOLUTION TABLE</div>
          <div style="font-size:22px;font-weight:900;color:#0f172a;margin-top:2px">BKT-${bucket}</div>
          <div style="display:inline-block;margin-top:8px;background:linear-gradient(135deg,#0f172a,#1e293b);border-radius:10px;padding:10px 20px;box-shadow:0 4px 12px rgba(0,0,0,.15)">
            <span style="font-size:9px;color:#94a3b8;font-weight:800;letter-spacing:.06em">TODAY'S MOVEMENT</span>
            <span style="font-size:20px;font-weight:900;color:#4ade80;margin-left:10px">${data.movement}%</span>
          </div>
      </div>
      <table style="width:100%;border-collapse:separate;border-spacing:0;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.04)">
        <thead><tr style="background:linear-gradient(135deg,#1e293b,#334155)">
          <th style="padding:10px 8px;font-size:10px;font-weight:800;color:#94a3b8;border-right:1px solid #475569;text-align:center">#</th>
          <th style="text-align:left;padding:10px 10px;font-size:10px;font-weight:800;color:#94a3b8;border-right:1px solid #475569;letter-spacing:.05em">EXECUTIVE</th>
          <th style="text-align:right;padding:10px 10px;font-size:10px;font-weight:800;color:#f87171;border-right:1px solid #475569">FLOW</th>
          <th style="text-align:right;padding:10px 10px;font-size:10px;font-weight:800;color:#4ade80;border-right:1px solid #475569">STABLE</th>
          <th style="text-align:right;padding:10px 10px;font-size:10px;font-weight:800;color:#fbbf24;border-right:1px solid #475569">RB</th>
          <th style="text-align:right;padding:10px 10px;font-size:10px;font-weight:800;color:#e2e8f0;border-right:1px solid #475569">TOTAL</th>
          <th style="text-align:center;padding:10px 10px;font-size:10px;font-weight:800;color:#4ade80;border-right:1px solid #475569">STABLE%</th>
          <th style="text-align:center;padding:10px 10px;font-size:10px;font-weight:800;color:#fbbf24;border-right:1px solid #475569">RB%</th>
          <th style="text-align:center;padding:10px 10px;font-size:10px;font-weight:800;color:#e2e8f0">RESOLUTION %</th>
        </tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;

  document.getElementById('flowContent').innerHTML = `
    <div style="text-align:center;margin-bottom:12px;display:flex;flex-wrap:wrap;gap:6px;justify-content:center">
      <button onclick="shareResTable()" style="background:linear-gradient(135deg,#25d366,#128c7e);color:#fff;border:none;padding:10px 18px;border-radius:8px;font-weight:700;font-size:13px;cursor:pointer">📤 Share</button>
      <button onclick="copyResTableImage()" style="background:linear-gradient(135deg,#2563eb,#1d4ed8);color:#fff;border:none;padding:10px 18px;border-radius:8px;font-weight:700;font-size:13px;cursor:pointer">📋 Copy Image</button>
      <button onclick="fetchResTable(1)" style="background:${bucket===1?'linear-gradient(135deg,#059669,#10b981)':'var(--surface2)'};color:${bucket===1?'#fff':'var(--ink)'};border:1px solid ${bucket===1?'#059669':'var(--border)'};padding:10px 16px;border-radius:8px;font-weight:700;font-size:13px;cursor:pointer">BKT-1</button>
      <button onclick="fetchResTable(2)" style="background:${bucket===2?'linear-gradient(135deg,#2563eb,#3b82f6)':'var(--surface2)'};color:${bucket===2?'#fff':'var(--ink)'};border:1px solid ${bucket===2?'#2563eb':'var(--border)'};padding:10px 16px;border-radius:8px;font-weight:700;font-size:13px;cursor:pointer">BKT-2</button>
      <button onclick="fetchReceiptCut()" style="background:linear-gradient(135deg,#0891b2,#06b6d4);color:#fff;border:none;padding:10px 16px;border-radius:8px;font-weight:700;font-size:13px;cursor:pointer">🧾 Receipt Cut</button>
      <button onclick="zoomResTable(1)" style="background:#f1f5f9;border:1px solid #e2e8f0;padding:10px 12px;border-radius:8px;font-size:14px;cursor:pointer">🔍+</button>
      <button onclick="zoomResTable(-1)" style="background:#f1f5f9;border:1px solid #e2e8f0;padding:10px 12px;border-radius:8px;font-size:14px;cursor:pointer">🔍−</button>
      <button onclick="toggleResSort(${bucket})" style="background:#f1f5f9;border:1px solid #e2e8f0;padding:10px 12px;border-radius:8px;font-size:13px;cursor:pointer;font-weight:700">↕ Sort</button>
      <button onclick="fetchFlowAgencyView(${bucket})" style="background:linear-gradient(135deg,#7c3aed,#6d28d9);color:#fff;border:none;padding:10px 16px;border-radius:8px;font-weight:700;font-size:13px;cursor:pointer">📊 Flow</button>
      <button onclick="generateResolutionTable()" style="background:linear-gradient(135deg,#0f172a,#334155);color:#fff;border:none;padding:10px 16px;border-radius:8px;font-weight:700;font-size:13px;cursor:pointer">← Back</button>
    </div>
    <div id="resTableContainer" style="overflow:auto;padding:10px">${reportHtml}</div>
  `;
  // Auto-fit zoom on load
  resTableZoom = getResTableDefaultZoom();
  setTimeout(() => {
    const card = document.getElementById('resTableCard');
    if (card) { card.style.transform = 'scale(' + resTableZoom + ')'; card.style.transformOrigin = 'top left'; }
  }, 50);
}

let resTableZoom = 1;
let resTableSortMode = 'resl_desc';
let resTableCurrentBucket = 1;

// Auto-fit zoom for mobile
function getResTableDefaultZoom() {
  const screenW = window.innerWidth - 40;
  return Math.min(1, screenW / 680);
}

function zoomResTable(dir) {
  resTableZoom += dir * 0.2;
  resTableZoom = Math.max(0.5, Math.min(2, resTableZoom));
  const card = document.getElementById('resTableCard');
  if (card) { card.style.transform = 'scale(' + resTableZoom + ')'; card.style.transformOrigin = 'top left'; }
}

function toggleResSort(bucket) {
  if (resTableSortMode === 'resl_desc') { resTableSortMode = 'resl_asc'; showToast('↑ Resolution Low → High'); }
  else if (resTableSortMode === 'resl_asc') { resTableSortMode = 'az'; showToast('↕ A → Z'); }
  else if (resTableSortMode === 'az') { resTableSortMode = 'za'; showToast('↕ Z → A'); }
  else { resTableSortMode = 'resl_desc'; showToast('↓ Resolution High → Low'); }
  fetchResTableSorted(bucket);
}

async function fetchResTableSorted(bucket) {
  // Just re-fetch with sort applied inside fetchResTable
  resTableZoom = 1;
  fetchResTable(bucket);
}

// ── FLOW & AGENCY VIEW (toggle from Resolution Table) ──
let flowSortMode = 'az';
let flowViewSortAsc = false;

async function fetchFlowAgencyView(bucket) {
  showToast('📊 Loading...');
  const data = await apiCall(`/api/report/resolution?bucket=${bucket}`);
  if (!data || data.error || !data.teams.length) {
    showToast('❌ No data');
    return;
  }

  if (flowSortMode === 'az') { data.teams.sort((a, b) => a.team.localeCompare(b.team)); }
  else if (flowSortMode === 'za') { data.teams.sort((a, b) => b.team.localeCompare(a.team)); }
  else if (flowSortMode === 'resl') { data.teams.sort((a, b) => b.resl - a.resl); }
  else if (flowSortMode === 'resl_asc') { data.teams.sort((a, b) => a.resl - b.resl); }
  const g = data.grand;

  let rows = '';
  data.teams.forEach((t, i) => {
    const reslW = Math.min(t.resl, 100);
    const reslCol = t.resl >= 80 ? '#10b981' : t.resl >= 60 ? '#84cc16' : t.resl >= 50 ? '#eab308' : t.resl >= 30 ? '#f97316' : '#ef4444';
    rows += `<tr>
      <td style="padding:11px 14px;font-size:12px;font-weight:700;color:#1e293b;border:1px solid #e2e8f0;white-space:nowrap">${t.team}</td>
      <td style="text-align:center;padding:11px 8px;font-size:12px;font-weight:600;color:#334155;border:1px solid #e2e8f0">${t.stable_pct.toFixed(2)}</td>
      <td style="text-align:center;padding:11px 8px;font-size:12px;font-weight:600;color:#334155;border:1px solid #e2e8f0">${t.rb_pct.toFixed(2)}</td>
      <td style="padding:11px 12px;border:1px solid #e2e8f0">
        <div style="display:flex;align-items:center;gap:8px;justify-content:flex-start;padding-left:8px">
          <div style="width:5px;height:20px;border-radius:3px;background:${reslCol};flex-shrink:0"></div>
          <span style="font-size:12px;font-weight:800;color:${reslCol}">${t.resl.toFixed(2)}</span>
        </div>
      </td>
      <td style="text-align:center;padding:11px 6px;font-size:12px;font-weight:800;color:#1e293b;border:1px solid #e2e8f0">${t.flow_cases || 0}</td>
      <td style="text-align:center;padding:11px 6px;font-size:11.5px;font-weight:700;color:#64748b;border:1px solid #e2e8f0">${(t.flow_pct || 0).toFixed(1)}%</td>
    </tr>`;
  });

  const reportHtml = `
    <div id="resTableCard" style="width:580px;background:#ffffff;border-radius:4px;padding:22px 24px;font-family:'Inter',-apple-system,sans-serif;color:#0f172a;box-shadow:0 2px 12px rgba(15,23,42,.06);border:2px solid #1e293b">
      <div style="text-align:center;margin-bottom:18px">
        <div style="font-size:18px;font-weight:900;color:#0f172a;letter-spacing:-.01em">BKT ${bucket} RESOLUTION TILL TIME</div>
        <div style="font-size:11px;color:#64748b;font-weight:600;margin-top:4px">${new Date().toLocaleDateString('en-IN',{day:'2-digit',month:'short',year:'numeric'}).toUpperCase()}</div>
      </div>
      <table style="width:100%;border-collapse:collapse;border:1.5px solid #1e293b">
        <thead><tr style="background:#0f172a">
          <th style="text-align:left;padding:10px 14px;font-size:10px;font-weight:800;color:#e2e8f0;letter-spacing:.05em;border:1px solid #334155">TEAM</th>
          <th style="text-align:center;padding:10px 8px;font-size:10px;font-weight:800;color:#4ade80;letter-spacing:.04em;border:1px solid #334155">STABLE %</th>
          <th style="text-align:center;padding:10px 8px;font-size:10px;font-weight:800;color:#fbbf24;letter-spacing:.04em;border:1px solid #334155">RB %</th>
          <th style="text-align:center;padding:10px 8px;font-size:10px;font-weight:800;color:#e2e8f0;letter-spacing:.04em;border:1px solid #334155">RESOLUTION</th>
          <th style="text-align:center;padding:10px 6px;font-size:10px;font-weight:800;color:#f87171;letter-spacing:.04em;border:1px solid #334155">FLOW<br>CASES</th>
          <th style="text-align:center;padding:10px 8px;font-size:10px;font-weight:800;color:#fb923c;letter-spacing:.04em;border:1px solid #334155">FLOW %</th>
        </tr></thead>
        <tbody>${rows}
          <tr style="background:#f1f5f9">
            <td style="padding:11px 14px;font-size:12px;font-weight:900;color:#0f172a;border:1px solid #e2e8f0">GRAND TOTAL</td>
            <td style="text-align:center;padding:11px 8px;font-size:12px;font-weight:900;color:#0f172a;border:1px solid #e2e8f0">${g.stable_pct.toFixed(2)}</td>
            <td style="text-align:center;padding:11px 8px;font-size:12px;font-weight:900;color:#0f172a;border:1px solid #e2e8f0">${g.rb_pct.toFixed(2)}</td>
            <td style="padding:11px 12px;border:1px solid #e2e8f0">
              <div style="display:flex;align-items:center;gap:8px;justify-content:flex-start;padding-left:8px">
                <div style="width:5px;height:22px;border-radius:3px;background:${g.resl>=80?'#10b981':g.resl>=60?'#84cc16':g.resl>=50?'#eab308':g.resl>=30?'#f97316':'#ef4444'};flex-shrink:0"></div>
                <span style="font-size:13px;font-weight:900;color:${g.resl>=80?'#10b981':g.resl>=60?'#84cc16':g.resl>=50?'#eab308':g.resl>=30?'#f97316':'#ef4444'}">${g.resl.toFixed(2)}</span>
              </div>
            </td>
            <td style="text-align:center;padding:11px 6px;font-size:13px;font-weight:900;color:#0f172a;border:1px solid #e2e8f0">${g.flow_cases||0}</td>
            <td style="text-align:center;padding:11px 8px;font-size:12px;font-weight:900;color:#0f172a;border:1px solid #e2e8f0">${(g.flow_pct||0).toFixed(1)}%</td>
          </tr>
        </tbody>
      </table>
      <div style="text-align:right;margin-top:8px"><div style="font-size:8px;color:#94a3b8;font-weight:600">RCC · ${new Date().toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit',hour12:true}).toUpperCase()}</div></div>
    </div>
  `;

  document.getElementById('flowContent').innerHTML = `
    <div style="text-align:center;margin-bottom:12px">
      <button onclick="shareResTable()" style="background:linear-gradient(135deg,#25d366,#128c7e);color:#fff;border:none;padding:12px 24px;border-radius:8px;font-weight:700;font-size:14px;cursor:pointer">📤 Share</button>
      <button onclick="copyResTableImage()" style="background:linear-gradient(135deg,#2563eb,#1d4ed8);color:#fff;border:none;padding:12px 24px;border-radius:8px;font-weight:700;font-size:14px;cursor:pointer;margin-left:8px">📋 Copy Image</button>
      <button onclick="fetchFlowAgencyView(${bucket===1?2:1})" style="background:var(--surface2);border:1px solid var(--border);color:var(--ink);padding:12px 20px;border-radius:8px;font-weight:700;font-size:14px;cursor:pointer;margin-left:8px">BKT-${bucket===1?2:1}</button>
      <button onclick="zoomResTable(1)" style="background:#f1f5f9;border:1px solid #e2e8f0;padding:10px 14px;border-radius:8px;font-size:16px;cursor:pointer;margin-left:8px">🔍+</button>
      <button onclick="zoomResTable(-1)" style="background:#f1f5f9;border:1px solid #e2e8f0;padding:10px 14px;border-radius:8px;font-size:16px;cursor:pointer;margin-left:4px">🔍−</button>
      <button onclick="toggleFlowSort(${bucket})" style="background:#f1f5f9;border:1px solid #e2e8f0;padding:10px 14px;border-radius:8px;font-size:13px;cursor:pointer;margin-left:4px;font-weight:700">↕ Sort</button>
      <button onclick="fetchResTable(${bucket})" style="background:linear-gradient(135deg,#0f172a,#334155);color:#fff;border:none;padding:12px 20px;border-radius:8px;font-weight:700;font-size:13px;cursor:pointer;margin-left:8px">📋 Resolution</button>
    </div>
    <div id="resTableContainer" style="overflow:auto;padding:10px">${reportHtml}</div>
  `;
  // Auto-fit zoom for Flow report
  resTableZoom = getResTableDefaultZoom();
  setTimeout(() => {
    const card = document.getElementById('resTableCard');
    if (card) { card.style.transform = 'scale(' + resTableZoom + ')'; card.style.transformOrigin = 'top left'; }
  }, 50);
}

function toggleFlowSort(bucket) {
  if (flowSortMode === 'az') { flowSortMode = 'za'; showToast('↕ Z → A'); }
  else if (flowSortMode === 'za') { flowSortMode = 'resl'; showToast('↓ Resolution High → Low'); }
  else if (flowSortMode === 'resl') { flowSortMode = 'resl_asc'; showToast('↑ Resolution Low → High'); }
  else { flowSortMode = 'az'; showToast('↕ A → Z'); }
  fetchFlowAgencyView(bucket);
}

function shareResTable() {
  const el = document.getElementById('resTableCard');
  if (!el) return;
  const bktTitle = `BKT ${resTableCurrentBucket} RESOLUTION`;
  const load = () => {
    html2canvas(el, {scale: 3, backgroundColor: '#ffffff'}).then(c => {
      c.toBlob(blob => {
        const file = new File([blob], `BKT${resTableCurrentBucket}_Resolution.png`, {type: 'image/png'});
        if (navigator.share && navigator.canShare({files: [file]})) {
          navigator.share({files: [file], title: bktTitle, text: `📋 ${bktTitle}\n🔗 https://app.rccapp.xyz/public/flowlist`});
        } else { const link=document.createElement('a'); link.download=`BKT${resTableCurrentBucket}_Resolution.png`; link.href=c.toDataURL(); link.click(); }
      });
    });
  };
  if (typeof html2canvas !== 'undefined') { load(); } else { const s=document.createElement('script'); s.src='https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js'; s.onload=load; document.head.appendChild(s); }
}

function copyResTableImage() {
  const el = document.getElementById('resTableCard');
  if (!el) return;
  showToast('📋 Copying...');
  const load = () => {
    html2canvas(el, {scale: 3, backgroundColor: '#ffffff'}).then(c => {
      c.toBlob(blob => {
        if (navigator.clipboard && navigator.clipboard.write && window.ClipboardItem && window.isSecureContext) {
          navigator.clipboard.write([new ClipboardItem({'image/png': blob})]).then(() => showToast('✅ Image copied!')).catch(() => { _downloadCanvas(c, 'Resolution_Table.png'); });
        } else {
          _downloadCanvas(c, 'Resolution_Table.png');
        }
      });
    });
  };
  if (typeof html2canvas !== 'undefined') { load(); } else { const s=document.createElement('script'); s.src='https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js'; s.onload=load; document.head.appendChild(s); }
}

function _downloadCanvas(canvas, filename) {
  const link = document.createElement('a');
  link.download = filename;
  link.href = canvas.toDataURL('image/png');
  link.click();
  showToast('📥 Image downloaded!');
}

// ── RECEIPT CUT REPORT ──
let rcSortMode = 'pct_desc';

async function generateReceiptCut() {
  toggleMenu();
  hideExecFilter();
  showToast('Loading...');
  fetchReceiptCut();
}

async function fetchReceiptCut() {
  const data = await apiCall('/api/report/receiptcut');
  if (!data || data.error || !data.teams.length) {
    showToast('No data');
    return;
  }

  // Sort
  if (rcSortMode === 'pct_asc') data.teams.sort((a,b) => a.pct_achi - b.pct_achi);
  else if (rcSortMode === 'az') data.teams.sort((a,b) => a.team.localeCompare(b.team));
  else if (rcSortMode === 'za') data.teams.sort((a,b) => b.team.localeCompare(a.team));
  // pct_desc is default from API

  function rColor(r) { if(r>=50) return '#059669'; if(r>=30) return '#d97706'; if(r>=20) return '#f97316'; return '#ef4444'; }
  function rBg(r) { if(r>=50) return '#ecfdf5'; if(r>=30) return '#fffbeb'; if(r>=20) return '#fff7ed'; return '#fef2f2'; }

  let rows = '';
  data.teams.forEach((t, i) => {
    const c = rColor(t.pct_achi);
    rows += `<tr style="background:${i%2===0?'#ffffff':'#f8fafc'}">
      <td style="padding:8px 10px;font-size:11px;font-weight:700;color:#0f172a;border:1px solid #e2e8f0;white-space:nowrap">👤 ${t.team}</td>
      <td style="text-align:center;padding:8px 6px;font-size:12px;font-weight:800;color:#059669;border:1px solid #e2e8f0">${t.paid}</td>
      <td style="text-align:center;padding:8px 6px;font-size:12px;font-weight:800;color:#ef4444;border:1px solid #e2e8f0">${t.unpaid}</td>
      <td style="text-align:center;padding:8px 6px;font-size:12px;font-weight:800;color:#0f172a;border:1px solid #e2e8f0">${t.total}</td>
      <td style="text-align:center;padding:8px 6px;font-size:11px;color:#64748b;border:1px solid #e2e8f0">${t.target}</td>
      <td style="text-align:center;padding:8px 6px;font-size:11px;font-weight:700;color:${t.shortfall>0?'#ef4444':'#059669'};border:1px solid #e2e8f0">${t.shortfall>0?t.shortfall:''}</td>
      <td style="text-align:center;padding:8px 6px;font-size:11px;color:#64748b;border:1px solid #e2e8f0">${t.drr||''}</td>
      <td style="text-align:center;padding:8px 6px;font-size:12px;font-weight:900;color:${c};background:${rBg(t.pct_achi)};border:1px solid #e2e8f0">${t.pct_achi.toFixed(1)}%</td>
      <td style="text-align:center;padding:8px 6px;font-size:12px;font-weight:700;color:#2563eb;border:1px solid #e2e8f0">${t.payment || ''}</td>
      <td style="text-align:center;padding:8px 6px;font-size:12px;font-weight:700;color:${t.pending_trails>0?'#f97316':'#059669'};border:1px solid #e2e8f0">${t.pending_trails || ''}</td>
    </tr>`;
  });
  const g = data.grand;
  rows += `<tr style="background:#ecfdf5;border-top:2px solid #1e293b">
    <td style="padding:10px 10px;font-size:12px;font-weight:900;color:#059669;border:1px solid #e2e8f0">TOTAL</td>
    <td style="text-align:center;padding:10px 6px;font-weight:900;color:#059669;font-size:13px;border:1px solid #e2e8f0">${g.paid}</td>
    <td style="text-align:center;padding:10px 6px;font-weight:900;color:#ef4444;font-size:13px;border:1px solid #e2e8f0">${g.unpaid}</td>
    <td style="text-align:center;padding:10px 6px;font-weight:900;color:#0f172a;font-size:13px;border:1px solid #e2e8f0">${g.total}</td>
    <td style="text-align:center;padding:10px 6px;color:#64748b;font-size:11px;font-weight:700;border:1px solid #e2e8f0">${g.target}</td>
    <td style="text-align:center;padding:10px 6px;font-weight:900;color:#ef4444;font-size:12px;border:1px solid #e2e8f0">${g.shortfall||''}</td>
    <td style="text-align:center;padding:10px 6px;color:#64748b;font-size:11px;font-weight:700;border:1px solid #e2e8f0">${g.drr||''}</td>
    <td style="text-align:center;padding:10px 6px;font-weight:900;color:#059669;font-size:14px;border:1px solid #e2e8f0">${g.pct_achi.toFixed(1)}%</td>
    <td style="text-align:center;padding:10px 6px;font-weight:900;color:#2563eb;font-size:13px;border:1px solid #e2e8f0">${g.payment||''}</td>
    <td style="text-align:center;padding:10px 6px;font-weight:900;color:#f97316;font-size:13px;border:1px solid #e2e8f0">${g.pending_trails||''}</td>
  </tr>`;

  const reportHtml = `
    <div id="rcReportCard" style="width:720px;background:#ffffff;border-radius:14px;padding:24px 20px;font-family:'Inter',-apple-system,sans-serif;color:#0f172a;box-shadow:0 4px 20px rgba(0,0,0,.08);border:1px solid #e2e8f0">
      <div style="text-align:center;margin-bottom:18px">
        <div style="font-size:20px;font-weight:900;color:#0f172a;letter-spacing:-.01em">RECEIPT CUT REPORT</div>
        <div style="display:inline-flex;align-items:center;gap:24px;margin-top:12px;padding:12px 28px;border:1.5px solid #e2e8f0;border-radius:12px;background:#f8fafc">
          <div style="display:flex;align-items:center;gap:8px"><svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#1d4ed8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/><path d="M12 2v4M12 18v4"/></svg><div><div style="font-size:9px;color:#64748b;font-weight:800;letter-spacing:.06em">TARGET</div><div style="font-size:22px;font-weight:900;color:#1d4ed8;line-height:1.1">${data.target_pct}%</div></div></div>
          <div style="display:flex;align-items:center;gap:8px"><svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg><div><div style="font-size:9px;color:#64748b;font-weight:800;letter-spacing:.06em">MOVEMENT</div><div style="font-size:22px;font-weight:900;color:#059669;line-height:1.1">${data.movement}%</div></div></div>
          <div style="display:flex;align-items:center;gap:8px"><svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg><div><div style="font-size:9px;color:#64748b;font-weight:800;letter-spacing:.06em">DAYS LEFT</div><div style="font-size:22px;font-weight:900;color:#0f172a;line-height:1.1">${data.days_remaining || data.remaining_days || ''}</div></div></div>
        </div>
      </div>
      <table style="width:100%;border-collapse:collapse">
        <thead><tr style="background:#1e293b">
          <th style="text-align:left;padding:10px 10px;font-size:10px;font-weight:800;color:#e2e8f0;border:1px solid #334155">👥 TEAM</th>
          <th style="text-align:center;padding:10px 6px;font-size:10px;font-weight:800;color:#4ade80;border:1px solid #334155">✅ PAID</th>
          <th style="text-align:center;padding:10px 6px;font-size:10px;font-weight:800;color:#f87171;border:1px solid #334155">❌ UNPAID</th>
          <th style="text-align:center;padding:10px 6px;font-size:10px;font-weight:800;color:#e2e8f0;border:1px solid #334155">TOTAL</th>
          <th style="text-align:center;padding:10px 6px;font-size:10px;font-weight:800;color:#94a3b8;border:1px solid #334155">${data.target_pct}%<br><span style="font-size:8px;color:#64748b">TARGET</span></th>
          <th style="text-align:center;padding:10px 6px;font-size:10px;font-weight:800;color:#f87171;border:1px solid #334155">SHORT<br>FALL</th>
          <th style="text-align:center;padding:10px 6px;font-size:10px;font-weight:800;color:#94a3b8;border:1px solid #334155">DRR</th>
          <th style="text-align:center;padding:10px 6px;font-size:10px;font-weight:800;color:#fbbf24;border:1px solid #334155">%ACHI</th>
          <th style="text-align:center;padding:10px 6px;font-size:10px;font-weight:800;color:#60a5fa;border:1px solid #334155">TODAY'S<br>PAYMENTS</th>
          <th style="text-align:center;padding:10px 6px;font-size:10px;font-weight:800;color:#fb923c;border:1px solid #334155">PENDING<br>TRAILS</th>
        </tr></thead>
        <tbody>${rows}</tbody>
      </table>
      <div style="text-align:right;margin-top:6px"><div style="font-size:8px;color:#94a3b8;font-weight:600">RCC · ${new Date().toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit',hour12:true}).toUpperCase()}</div></div>
    </div>
  `;

  const pages = document.querySelectorAll('.page');
  const navItems = document.querySelectorAll('.nav-item');
  pages.forEach(p => p.classList.remove('active'));
  navItems.forEach(n => n.classList.remove('active'));
  document.getElementById('pageFlow').classList.add('active');
  document.getElementById('flowContent').innerHTML = `
    <div style="text-align:center;margin-bottom:12px;display:flex;flex-wrap:wrap;gap:6px;justify-content:center">
      <button onclick="shareRcReport()" style="background:linear-gradient(135deg,#25d366,#128c7e);color:#fff;border:none;padding:10px 18px;border-radius:8px;font-weight:700;font-size:13px;cursor:pointer">📤 Share</button>
      <button onclick="copyRcReport()" style="background:linear-gradient(135deg,#2563eb,#1d4ed8);color:#fff;border:none;padding:10px 18px;border-radius:8px;font-weight:700;font-size:13px;cursor:pointer">📋 Copy Image</button>
      <button onclick="zoomRcReport(1)" style="background:#f1f5f9;border:1px solid #e2e8f0;padding:10px 14px;border-radius:8px;font-size:16px;cursor:pointer">🔍+</button>
      <button onclick="zoomRcReport(-1)" style="background:#f1f5f9;border:1px solid #e2e8f0;padding:10px 14px;border-radius:8px;font-size:16px;cursor:pointer">🔍−</button>
      <button onclick="toggleRcSort()" style="background:#f1f5f9;border:1px solid #e2e8f0;padding:10px 14px;border-radius:8px;font-size:13px;cursor:pointer;font-weight:700">↕ Sort</button>
      <button onclick="generateResolutionTable()" style="background:linear-gradient(135deg,#0f172a,#334155);color:#fff;border:none;padding:10px 16px;border-radius:8px;font-weight:700;font-size:13px;cursor:pointer">← Back</button>
    </div>
    <div id="rcReportContainer" style="overflow:auto;padding:10px">${reportHtml}</div>
  `;
  // Auto-fit zoom for Receipt Cut
  rcZoom = Math.min(1, (window.innerWidth - 40) / 700);
  setTimeout(() => {
    const card = document.getElementById('rcReportCard');
    if (card) { card.style.transform = 'scale(' + rcZoom + ')'; card.style.transformOrigin = 'top left'; }
  }, 50);
}

let rcZoom = 1;
function zoomRcReport(dir) {
  rcZoom += dir * 0.2;
  rcZoom = Math.max(0.5, Math.min(2, rcZoom));
  const card = document.getElementById('rcReportCard');
  if (card) { card.style.transform = 'scale(' + rcZoom + ')'; card.style.transformOrigin = 'top left'; }
}

function toggleRcSort() {
  if (rcSortMode === 'pct_desc') { rcSortMode = 'pct_asc'; showToast('↑ %Achi Low → High'); }
  else if (rcSortMode === 'pct_asc') { rcSortMode = 'az'; showToast('↕ A → Z'); }
  else if (rcSortMode === 'az') { rcSortMode = 'za'; showToast('↕ Z → A'); }
  else { rcSortMode = 'pct_desc'; showToast('↓ %Achi High → Low'); }
  fetchReceiptCut();
}

function toggleRcSort() {
  if (rcSortMode === 'pct_desc') { rcSortMode = 'pct_asc'; showToast('↑ %Achi Low → High'); }
  else if (rcSortMode === 'pct_asc') { rcSortMode = 'az'; showToast('↕ A → Z'); }
  else if (rcSortMode === 'az') { rcSortMode = 'za'; showToast('↕ Z → A'); }
  else { rcSortMode = 'pct_desc'; showToast('↓ %Achi High → Low'); }
  fetchReceiptCut();
}

// ── BUCKET SUMMARY REPORT ──
async function fetchBucketSummary() {
  showToast('📊 Loading...');
  const data = await apiCall('/api/report/bucket-summary');
  if (!data || data.error || !data.rows.length) {
    showToast('❌ No data');
    return;
  }

  function fmtInd(v) { if(!v) return ''; v=Math.round(v); let s=v.toString(); if(s.length<=3) return s; let r=s.slice(-3); s=s.slice(0,-3); while(s.length>0){r=s.slice(-2)+','+r; s=s.slice(0,-2);} return r; }
  function reslColor(r) { if(r>=60) return '#059669'; if(r>=40) return '#ca8a04'; if(r>=20) return '#ea580c'; return '#dc2626'; }

  let rows = '';
  data.rows.forEach((r, i) => {
    const rc = reslColor(r.resl);
    rows += `<tr style="background:${i%2===0?'#ffffff':'#f8fafc'}">
      <td style="padding:10px 14px;font-size:13px;font-weight:800;color:#0f172a;border:1px solid #e2e8f0;text-align:center">${r.bucket}</td>
      <td style="text-align:right;padding:10px 12px;font-size:12px;font-weight:700;color:#ef4444;border:1px solid #e2e8f0">${fmtInd(r.flow)}</td>
      <td style="text-align:right;padding:10px 12px;font-size:12px;font-weight:700;color:#059669;border:1px solid #e2e8f0">${fmtInd(r.stable)}</td>
      <td style="text-align:right;padding:10px 12px;font-size:12px;font-weight:700;color:#d97706;border:1px solid #e2e8f0">${fmtInd(r.rb)}</td>
      <td style="text-align:right;padding:10px 12px;font-size:12px;font-weight:800;color:#0f172a;border:1px solid #e2e8f0">${fmtInd(r.grand_total)}</td>
      <td style="text-align:center;padding:10px 10px;font-size:12px;font-weight:700;color:#059669;border:1px solid #e2e8f0">${r.stable_pct.toFixed(2)}</td>
      <td style="text-align:center;padding:10px 10px;font-size:12px;font-weight:700;color:#d97706;border:1px solid #e2e8f0">${r.rb_pct.toFixed(2)}</td>
      <td style="padding:10px 12px;border:1px solid #e2e8f0">
        <div style="display:flex;align-items:center;gap:8px;justify-content:flex-start;padding-left:4px">
          <div style="width:5px;height:20px;border-radius:3px;background:${rc};flex-shrink:0"></div>
          <span style="font-size:13px;font-weight:800;color:${rc}">${r.resl.toFixed(2)}</span>
        </div>
      </td>
    </tr>`;
  });

  const g = data.grand;
  const gc = reslColor(g.resl);
  rows += `<tr style="background:#ecfdf5">
    <td style="padding:10px 14px;font-size:13px;font-weight:900;color:#059669;border:1px solid #e2e8f0;text-align:center">Grand Total</td>
    <td style="text-align:right;padding:10px 12px;font-size:12px;font-weight:900;color:#ef4444;border:1px solid #e2e8f0">${fmtInd(g.flow)}</td>
    <td style="text-align:right;padding:10px 12px;font-size:12px;font-weight:900;color:#059669;border:1px solid #e2e8f0">${fmtInd(g.stable)}</td>
    <td style="text-align:right;padding:10px 12px;font-size:12px;font-weight:900;color:#d97706;border:1px solid #e2e8f0">${fmtInd(g.rb)}</td>
    <td style="text-align:right;padding:10px 12px;font-size:12px;font-weight:900;color:#0f172a;border:1px solid #e2e8f0">${fmtInd(g.grand_total)}</td>
    <td style="text-align:center;padding:10px 10px;font-size:12px;font-weight:900;color:#059669;border:1px solid #e2e8f0">${g.stable_pct.toFixed(2)}</td>
    <td style="text-align:center;padding:10px 10px;font-size:12px;font-weight:900;color:#d97706;border:1px solid #e2e8f0">${g.rb_pct.toFixed(2)}</td>
    <td style="padding:10px 12px;border:1px solid #e2e8f0">
      <div style="display:flex;align-items:center;gap:8px;justify-content:flex-start;padding-left:4px">
        <div style="width:5px;height:22px;border-radius:3px;background:${gc};flex-shrink:0"></div>
        <span style="font-size:14px;font-weight:900;color:${gc}">${g.resl.toFixed(2)}</span>
      </div>
    </td>
  </tr>`;

  const reportHtml = `
    <div id="resTableCard" style="width:650px;background:#ffffff;border-radius:14px;padding:24px 20px;font-family:'Inter',-apple-system,sans-serif;color:#0f172a;box-shadow:0 4px 20px rgba(0,0,0,.08);border:1px solid #e2e8f0">
      <div style="text-align:center;margin-bottom:16px">
        <div style="font-size:18px;font-weight:900;color:#0f172a">BUCKET SUMMARY</div>
        <div style="font-size:10px;color:#64748b;font-weight:600;margin-top:4px">${new Date().toLocaleDateString('en-IN',{day:'2-digit',month:'short',year:'numeric'}).toUpperCase()} · POS STATUS WISE</div>
      </div>
      <table style="width:100%;border-collapse:collapse">
        <thead><tr style="background:#1e293b">
          <th style="padding:10px 14px;font-size:10px;font-weight:800;color:#e2e8f0;border:1px solid #334155;text-align:center">BUCKET</th>
          <th style="text-align:right;padding:10px 12px;font-size:10px;font-weight:800;color:#f87171;border:1px solid #334155">FLOW</th>
          <th style="text-align:right;padding:10px 12px;font-size:10px;font-weight:800;color:#4ade80;border:1px solid #334155">STABLE</th>
          <th style="text-align:right;padding:10px 12px;font-size:10px;font-weight:800;color:#fbbf24;border:1px solid #334155">RB</th>
          <th style="text-align:right;padding:10px 12px;font-size:10px;font-weight:800;color:#e2e8f0;border:1px solid #334155">GRAND TOTAL</th>
          <th style="text-align:center;padding:10px 10px;font-size:10px;font-weight:800;color:#4ade80;border:1px solid #334155">STABLE %</th>
          <th style="text-align:center;padding:10px 10px;font-size:10px;font-weight:800;color:#fbbf24;border:1px solid #334155">RB %</th>
          <th style="text-align:center;padding:10px 10px;font-size:10px;font-weight:800;color:#e2e8f0;border:1px solid #334155">RESL</th>
        </tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;

  const pages = document.querySelectorAll('.page');
  const navItems = document.querySelectorAll('.nav-item');
  pages.forEach(p => p.classList.remove('active'));
  navItems.forEach(n => n.classList.remove('active'));
  document.getElementById('pageFlow').classList.add('active');
  document.getElementById('flowContent').innerHTML = `
    <div style="text-align:center;margin-bottom:12px;display:flex;flex-wrap:wrap;gap:6px;justify-content:center">
      <button onclick="shareResTable()" style="background:linear-gradient(135deg,#25d366,#128c7e);color:#fff;border:none;padding:10px 18px;border-radius:8px;font-weight:700;font-size:13px;cursor:pointer">📤 Share</button>
      <button onclick="copyResTableImage()" style="background:linear-gradient(135deg,#2563eb,#1d4ed8);color:#fff;border:none;padding:10px 18px;border-radius:8px;font-weight:700;font-size:13px;cursor:pointer">📋 Copy Image</button>
      <button onclick="zoomResTable(1)" style="background:#f1f5f9;border:1px solid #e2e8f0;padding:10px 12px;border-radius:8px;font-size:14px;cursor:pointer">🔍+</button>
      <button onclick="zoomResTable(-1)" style="background:#f1f5f9;border:1px solid #e2e8f0;padding:10px 12px;border-radius:8px;font-size:14px;cursor:pointer">🔍−</button>
      <button onclick="generateResolutionTable()" style="background:linear-gradient(135deg,#0f172a,#334155);color:#fff;border:none;padding:10px 16px;border-radius:8px;font-weight:700;font-size:13px;cursor:pointer">← Back</button>
    </div>
    <div id="resTableContainer" style="overflow:auto;padding:10px">${reportHtml}</div>
  `;
  resTableZoom = getResTableDefaultZoom();
  setTimeout(() => {
    const card = document.getElementById('resTableCard');
    if (card) { card.style.transform = 'scale(' + resTableZoom + ')'; card.style.transformOrigin = 'top left'; }
  }, 50);
}

// ── SHARE ALL REPORTS ──
async function shareAllReports() {
  showToast('📤 Generating all reports...');
  
  const loadH2C = () => new Promise((resolve) => {
    if (typeof html2canvas !== 'undefined') return resolve();
    const s = document.createElement('script');
    s.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
    s.onload = resolve;
    document.head.appendChild(s);
  });
  await loadH2C();

  // Generate all 4 reports in hidden container
  const container = document.createElement('div');
  container.style.cssText = 'position:absolute;left:-9999px;top:0;';
  document.body.appendChild(container);

  const files = [];
  
  // 1. BKT-1 Resolution
  try {
    const d1 = await apiCall('/api/report/resolution?bucket=1');
    if (d1 && d1.teams) {
      const img = await _generateResImage(d1, 1);
      if (img) files.push(new File([img], 'BKT1_Resolution.png', {type: 'image/png'}));
    }
  } catch(e) {}

  // 2. BKT-2 Resolution
  try {
    const d2 = await apiCall('/api/report/resolution?bucket=2');
    if (d2 && d2.teams) {
      const img = await _generateResImage(d2, 2);
      if (img) files.push(new File([img], 'BKT2_Resolution.png', {type: 'image/png'}));
    }
  } catch(e) {}

  // 3. Receipt Cut
  try {
    const d3 = await apiCall('/api/report/receiptcut');
    if (d3 && d3.teams) {
      // Render receipt cut, capture, then restore
      await fetchReceiptCut();
      await new Promise(r => setTimeout(r, 200));
      const el3 = document.getElementById('rcReportCard');
      if (el3) {
        const c3 = await html2canvas(el3, {scale: 2, backgroundColor: '#ffffff'});
        const b3 = await new Promise(r => c3.toBlob(r));
        files.push(new File([b3], 'ReceiptCut_Report.png', {type: 'image/png'}));
      }
    }
  } catch(e) {}

  // 4. Bucket Summary
  try {
    await fetchBucketSummary();
    await new Promise(r => setTimeout(r, 200));
    const el4 = document.getElementById('resTableCard');
    if (el4) {
      const c4 = await html2canvas(el4, {scale: 2, backgroundColor: '#ffffff'});
      const b4 = await new Promise(r => c4.toBlob(r));
      files.push(new File([b4], 'Bucket_Summary.png', {type: 'image/png'}));
    }
  } catch(e) {}

  document.body.removeChild(container);

  if (files.length === 0) {
    showToast('❌ No reports generated');
    return;
  }

  // Share all files
  if (navigator.share && navigator.canShare({files})) {
    const caption = `📊 BUCKET WISE PERFORMANCE\n📋 BKT-1 RESOLUTION PERFORMANCE\n📋 BKT-2 RESOLUTION PERFORMANCE\n🧾 TEAM WISE RECEIPT CUT IN BKT 1 TO 6 WITH DAILY DRR & TODAY COLLECT PAYMENT AND TRAILS COUNT`;
    navigator.share({files, title: 'RCC Reports', text: caption}).then(() => {
      showToast('✅ Shared!');
    }).catch(() => showToast('Share cancelled'));
  } else {
    // Fallback — download all
    files.forEach(f => {
      const url = URL.createObjectURL(f);
      const a = document.createElement('a'); a.href = url; a.download = f.name; a.click();
    });
    showToast('📥 Downloaded ' + files.length + ' images');
  }
  
  // Go back to selection page
  generateResolutionTable();
}

async function _generateResImage(data, bucket) {
  // Quick render BKT resolution table as image
  try {
    resTableCurrentBucket = bucket;
    await fetchResTable(bucket);
    await new Promise(r => setTimeout(r, 200));
    const el = document.getElementById('resTableCard');
    if (!el) return null;
    const canvas = await html2canvas(el, {scale: 2, backgroundColor: '#ffffff'});
    return await new Promise(r => canvas.toBlob(r));
  } catch(e) { return null; }
}

function shareRcReport() {
  const el = document.getElementById('rcReportCard');
  if (!el) return;
  const shareText = 'TEAM WISE RECEIPT CUT IN BKT 1 TO 6 WITH DAILY DRR & TODAY COLLECT PAYMENT AND TRAILS COUNT';
  const load = () => {
    html2canvas(el, {scale: 3, backgroundColor: '#ffffff'}).then(c => {
      c.toBlob(blob => {
        const file = new File([blob], 'ReceiptCut_Report.png', {type: 'image/png'});
        if (navigator.share && navigator.canShare({files: [file]})) {
          navigator.share({files: [file], title: 'Receipt Cut Report', text: shareText});
        } else { const l=document.createElement('a'); l.download='ReceiptCut_Report.png'; l.href=c.toDataURL(); l.click(); }
      });
    });
  };
  if (typeof html2canvas !== 'undefined') { load(); } else { const s=document.createElement('script'); s.src='https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js'; s.onload=load; document.head.appendChild(s); }
}

function copyRcReport() {
  const el = document.getElementById('rcReportCard');
  if (!el) return;
  showToast('Copying...');
  const load = () => {
    html2canvas(el, {scale: 3, backgroundColor: '#ffffff'}).then(c => {
      c.toBlob(blob => {
        try { navigator.clipboard.write([new ClipboardItem({'image/png': blob})]).then(() => showToast('Image copied!')).catch(() => { const l=document.createElement('a'); l.download='ReceiptCut_Report.png'; l.href=c.toDataURL(); l.click(); showToast('Downloaded'); }); }
        catch(e) { const l=document.createElement('a'); l.download='ReceiptCut_Report.png'; l.href=c.toDataURL(); l.click(); showToast('Downloaded'); }
      });
    });
  };
  if (typeof html2canvas !== 'undefined') { load(); } else { const s=document.createElement('script'); s.src='https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js'; s.onload=load; document.head.appendChild(s); }
}

// ── DAILY WINNERS ──
let winnersDate = '';

async function generateWinners() {
  toggleMenu();
  // Show date picker first
  const pages = document.querySelectorAll('.page');
  const navItems = document.querySelectorAll('.nav-item');
  pages.forEach(p => p.classList.remove('active'));
  navItems.forEach(n => n.classList.remove('active'));
  document.getElementById('pageFlow').classList.add('active');
  
  // Default today in dd.mm.yy format
  const now = new Date();
  const defaultDate = ('0'+now.getDate()).slice(-2) + '.' + ('0'+(now.getMonth()+1)).slice(-2) + '.' + String(now.getFullYear()).slice(-2);
  
  document.getElementById('flowContent').innerHTML = `
    <div class="summary-banner">
      <div class="banner-left">
        <span style="font-size:1.3rem">🏅</span>
        <div>
          <div class="banner-label">DAILY WINNERS</div>
          <div class="banner-value">Select Date</div>
        </div>
      </div>
    </div>
    <div style="text-align:center;padding:20px">
      <input type="date" id="winnersDatePicker" value="${now.toISOString().split('T')[0]}" style="padding:12px 16px;border:2px solid var(--accent);border-radius:8px;font-size:16px;font-weight:700;background:var(--surface);color:var(--ink);font-family:var(--font)">
      <br><br>
      <button onclick="fetchWinners()" style="background:linear-gradient(135deg,#2563eb,#1d4ed8);color:#fff;border:none;padding:14px 32px;border-radius:8px;font-weight:700;font-size:15px;cursor:pointer">🏅 Generate</button>
    </div>
  `;
}

async function fetchWinners() {
  const dateInput = document.getElementById('winnersDatePicker').value;
  // Convert yyyy-mm-dd to dd.mm.yy
  const parts = dateInput.split('-');
  const dateStr = parts[2] + '.' + parts[1] + '.' + parts[0].slice(-2);
  
  showToast('🏅 Generating...');
  const data = await apiCall(`/api/report/winners?date=${encodeURIComponent(dateStr)}`);
  if (!data || !data.text) {
    showToast('❌ Failed to generate');
    return;
  }
  // Show text + copy button
  const pages = document.querySelectorAll('.page');
  const navItems = document.querySelectorAll('.nav-item');
  pages.forEach(p => p.classList.remove('active'));
  navItems.forEach(n => n.classList.remove('active'));
  document.getElementById('pageFlow').classList.add('active');
  document.getElementById('flowContent').innerHTML = `
    <div class="summary-banner">
      <div class="banner-left">
        <span style="font-size:1.3rem">🏅</span>
        <div>
          <div class="banner-label">DAILY WINNERS</div>
          <div class="banner-value">Today</div>
        </div>
      </div>
    </div>
    <div style="text-align:center;margin-bottom:12px">
      <button onclick="copyWinnersText()" style="background:linear-gradient(135deg,#25d366,#128c7e);color:#fff;border:none;padding:12px 24px;border-radius:8px;font-weight:700;font-size:14px;cursor:pointer">📋 Copy for WhatsApp</button>
    </div>
    <pre id="winnersText" style="background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;font-size:.85rem;white-space:pre-wrap;word-wrap:break-word;line-height:1.6;color:var(--ink);font-family:var(--font)">${data.text}</pre>
  `;
}

function copyWinnersText() {
  const text = document.getElementById('winnersText').textContent;
  navigator.clipboard.writeText(text).then(() => {
    showToast('✅ Copied! Paste in WhatsApp');
  }).catch(() => {
    const ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    showToast('✅ Copied! Paste in WhatsApp');
  });
}

// ── TRAILS CSV UPLOAD ──
function showTrailsUpload() {
  toggleMenu();
  const pages = document.querySelectorAll('.page');
  const navItems = document.querySelectorAll('.nav-item');
  pages.forEach(p => p.classList.remove('active'));
  navItems.forEach(n => n.classList.remove('active'));
  document.getElementById('pageFlow').classList.add('active');
  document.getElementById('flowContent').innerHTML = `
    <div class="summary-banner">
      <div class="banner-left">
        <span style="font-size:1.3rem">📤</span>
        <div>
          <div class="banner-label">UPLOAD TRAILS CSV</div>
          <div class="banner-value">Vymo Report</div>
        </div>
      </div>
    </div>
    <div style="text-align:center;padding:24px">
      <p style="color:var(--muted);font-size:.85rem;margin-bottom:16px">Vymo se download ki hui CSV file upload karo</p>
      <input type="file" id="trailsCsvFile" accept=".csv" style="display:none" onchange="uploadTrailsCsv()">
      <button onclick="document.getElementById('trailsCsvFile').click()" style="background:linear-gradient(135deg,#2563eb,#1d4ed8);color:#fff;border:none;padding:16px 32px;border-radius:10px;font-weight:700;font-size:16px;cursor:pointer;box-shadow:0 4px 15px rgba(37,99,235,.3)">📁 Select CSV File</button>
    </div>
  `;
}

async function uploadTrailsCsv() {
  const fileInput = document.getElementById('trailsCsvFile');
  if (!fileInput.files.length) return;
  
  const file = fileInput.files[0];
  showToast('📤 Uploading...');
  
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const res = await fetch(`${API}/api/trails/upload`, {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    
    if (data.error) {
      showToast('❌ ' + data.error);
      return;
    }
    
    // Build image report table
    let tableRows = '';
    const teams = Object.keys(data.team_count).sort();
    teams.forEach(team => {
      const today = data.team_count[team] || 0;
      const pending = data.pending_count[team] || 0;
      tableRows += `<tr><td style="padding:8px 14px;font-size:13px;font-weight:700;color:#1e293b;border-bottom:1px solid #e2e8f0;border-right:1px solid #e2e8f0">${team}</td><td style="text-align:center;padding:8px 14px;font-size:14px;font-weight:800;color:#059669;border-bottom:1px solid #e2e8f0;border-right:1px solid #e2e8f0">${today}</td><td style="text-align:center;padding:8px 14px;font-size:14px;font-weight:800;color:#dc2626;border-bottom:1px solid #e2e8f0">${pending}</td></tr>`;
    });
    tableRows += `<tr style="background:#f0fdf4"><td style="padding:8px 14px;font-size:13px;font-weight:800;color:#059669;border-right:1px solid #e2e8f0">TOTAL</td><td style="text-align:center;padding:8px 14px;font-size:15px;font-weight:900;color:#059669;border-right:1px solid #e2e8f0">${data.matched}</td><td style="text-align:center;padding:8px 14px;font-size:15px;font-weight:900;color:#dc2626">${data.total_pending}</td></tr>`;

    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-IN', {hour:'2-digit', minute:'2-digit', hour12:true}).toUpperCase();
    const dateStr = now.toLocaleDateString('en-IN', {day:'2-digit', month:'short', year:'numeric'});

    const reportHtml = `
      <div id="trailsReportCard" style="width:420px;background:linear-gradient(180deg,#ffffff,#f8fafc);border-radius:14px;padding:24px;font-family:'Inter',sans-serif;color:#0f172a;box-shadow:0 8px 40px rgba(0,0,0,.1);border:1.5px solid #e2e8f0">
        <div style="text-align:center;margin-bottom:16px;padding-bottom:12px;border-bottom:2px solid #f1f5f9">
          <div style="font-size:20px;font-weight:900;color:#0f172a">📋 TRAILS REPORT</div>
          <div style="font-size:13px;color:#475569;margin-top:4px;font-weight:600">${dateStr} · ${timeStr}</div>
        </div>
        <div style="display:flex;gap:10px;margin-bottom:16px">
          <div style="flex:1;background:linear-gradient(135deg,#ecfdf5,#d1fae5);border:2px solid #6ee7b7;border-radius:10px;padding:12px;text-align:center">
            <div style="font-size:10px;color:#475569;font-weight:800">TODAY DONE</div>
            <div style="font-size:24px;font-weight:900;color:#047857">${data.matched}</div>
          </div>
          <div style="flex:1;background:linear-gradient(135deg,#fef2f2,#fecaca);border:2px solid #fca5a5;border-radius:10px;padding:12px;text-align:center">
            <div style="font-size:10px;color:#475569;font-weight:800">PENDING</div>
            <div style="font-size:24px;font-weight:900;color:#dc2626">${data.total_pending}</div>
          </div>
        </div>
        <table style="width:100%;border-collapse:separate;border-spacing:0;border:1.5px solid #e2e8f0;border-radius:10px;overflow:hidden">
          <thead><tr style="background:linear-gradient(180deg,#f1f5f9,#e8eef6)"><th style="text-align:left;padding:10px 14px;font-size:12px;font-weight:800;color:#475569;border-bottom:2px solid #cbd5e1;border-right:1px solid #cbd5e1">TEAM</th><th style="text-align:center;padding:10px 14px;font-size:12px;font-weight:800;color:#059669;border-bottom:2px solid #cbd5e1;border-right:1px solid #cbd5e1">TODAY</th><th style="text-align:center;padding:10px 14px;font-size:12px;font-weight:800;color:#dc2626;border-bottom:2px solid #cbd5e1">PENDING</th></tr></thead>
          <tbody>${tableRows}</tbody>
        </table>
        <div style="text-align:center;margin-top:12px;font-size:10px;color:#94a3b8;font-weight:600">📱 Generated at ${timeStr}</div>
      </div>
    `;

    // Show report
    document.getElementById('flowContent').innerHTML = `
      <div style="text-align:center;margin-bottom:12px">
        <button onclick="shareTrailsImg()" style="background:linear-gradient(135deg,#25d366,#128c7e);color:#fff;border:none;padding:12px 24px;border-radius:8px;font-weight:700;font-size:14px;cursor:pointer">📤 Share</button>
        <button onclick="copyTrailsReport()" style="background:linear-gradient(135deg,#2563eb,#1d4ed8);color:#fff;border:none;padding:12px 24px;border-radius:8px;font-weight:700;font-size:14px;cursor:pointer;margin-left:8px">📋 Copy Text</button>
        <button onclick="showTrailsUpload()" style="background:var(--surface2);border:1px solid var(--border);color:var(--ink);padding:12px 24px;border-radius:8px;font-weight:700;font-size:14px;cursor:pointer;margin-left:8px">📤 Upload Another</button>
      </div>
      ${data.unmatched > 0 ? '<div style="text-align:center;margin-bottom:10px;color:var(--amber);font-size:.8rem">⚠️ ' + data.unmatched + ' loan nos not matched</div>' : ''}
      <div id="trailsImgContainer" style="overflow:auto;padding:10px">${reportHtml}</div>
      <pre id="trailsReportText" style="display:none">${data.text}</pre>
    `;
    showToast('✅ Trails updated + report ready!');
  } catch(e) {
    showToast('❌ Upload failed');
  }
}

function shareTrailsImg() {
  const el = document.getElementById('trailsReportCard');
  if (!el) return;
  const script = document.createElement('script');
  script.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
  script.onload = () => {
    html2canvas(el, {scale: 3, backgroundColor: null}).then(c => {
      c.toBlob(blob => {
        const file = new File([blob], 'Trails_Report.png', {type: 'image/png'});
        if (navigator.share && navigator.canShare({files: [file]})) {
          navigator.share({files: [file], title: 'Trails Report'});
        } else {
          const link = document.createElement('a');
          link.download = 'Trails_Report.png';
          link.href = c.toDataURL();
          link.click();
        }
      });
    });
  };
  document.head.appendChild(script);
}

function copyReportImage() {
  const el = document.getElementById('reportCard');
  if (!el) return;
  showToast('📋 Copying image...');
  const loadAndCopy = () => {
    html2canvas(el, {scale: 3, backgroundColor: '#ffffff'}).then(c => {
      c.toBlob(blob => {
        try {
          navigator.clipboard.write([new ClipboardItem({'image/png': blob})]).then(() => {
            showToast('✅ Image copied! Paste in WhatsApp');
          }).catch(() => {
            // Fallback: download
            const link = document.createElement('a');
            link.download = 'TillTime_Report.png';
            link.href = c.toDataURL();
            link.click();
            showToast('📥 Downloaded (copy not supported on this device)');
          });
        } catch(e) {
          const link = document.createElement('a');
          link.download = 'TillTime_Report.png';
          link.href = c.toDataURL();
          link.click();
          showToast('📥 Downloaded (copy not supported)');
        }
      });
    });
  };
  if (typeof html2canvas !== 'undefined') {
    loadAndCopy();
  } else {
    const script = document.createElement('script');
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
    script.onload = loadAndCopy;
    document.head.appendChild(script);
  }
}

function shareReport() {
  const el = document.getElementById('reportCard');
  if (!el) return;
  showToast('📤 Preparing...');
  const loadAndShare = () => {
    html2canvas(el, {scale: 3, backgroundColor: '#ffffff'}).then(c => {
      c.toBlob(blob => {
        const file = new File([blob], 'TillTime_Report.png', {type: 'image/png'});
        if (navigator.share && navigator.canShare({files: [file]})) {
          navigator.share({
            files: [file],
            title: '📊 Till Time Payments',
            text: '📊 Till Time Payments\n📋 FLOW CASES\n🔗 https://app.rccapp.xyz/public/flowlist'
          });
        } else {
          // Fallback: download
          const link = document.createElement('a');
          link.download = 'TillTime_Report.png';
          link.href = c.toDataURL();
          link.click();
          showToast('📥 Downloaded');
        }
      });
    });
  };
  if (typeof html2canvas !== 'undefined') {
    loadAndShare();
  } else {
    const script = document.createElement('script');
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
    script.onload = loadAndShare;
    document.head.appendChild(script);
  }
}

// ── PAYMENT UPDATE ──
function showPaymentUpdate() {
  toggleMenu();
  hideExecFilter();
  const pages = document.querySelectorAll('.page');
  const navItems = document.querySelectorAll('.nav-item');
  pages.forEach(p => p.classList.remove('active'));
  navItems.forEach(n => n.classList.remove('active'));
  document.getElementById('pageFlow').classList.add('active');
  
  document.getElementById('flowContent').innerHTML = `
    <div style="max-width:480px;margin:0 auto;padding:16px">
      <div style="text-align:center;margin-bottom:20px">
        <div style="font-size:18px;font-weight:900;color:var(--ink)">💳 Payment Update</div>
        <div style="font-size:11px;color:var(--muted);margin-top:4px">Update payment → saves to RCC file instantly</div>
      </div>
      
      <div style="background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:20px;margin-bottom:16px">
        <div style="margin-bottom:14px">
          <label style="font-size:11px;font-weight:700;color:var(--muted);letter-spacing:.04em;display:block;margin-bottom:5px">LOAN NO</label>
          <input type="text" id="payLoanNo" placeholder="Enter Loan Number" style="width:100%;padding:12px 14px;border:1.5px solid var(--border);border-radius:8px;font-size:14px;font-weight:600;background:var(--bg);color:var(--ink);outline:none">
        </div>
        <div style="margin-bottom:14px">
          <label style="font-size:11px;font-weight:700;color:var(--muted);letter-spacing:.04em;display:block;margin-bottom:5px">AMOUNT (₹)</label>
          <input type="number" id="payAmount" placeholder="Enter Amount" style="width:100%;padding:12px 14px;border:1.5px solid var(--border);border-radius:8px;font-size:14px;font-weight:600;background:var(--bg);color:var(--ink);outline:none">
        </div>
        <div style="margin-bottom:14px">
          <label style="font-size:11px;font-weight:700;color:var(--muted);letter-spacing:.04em;display:block;margin-bottom:5px">MODE OF PAYMENT</label>
          <select id="payMode" style="width:100%;padding:12px 14px;border:1.5px solid var(--border);border-radius:8px;font-size:14px;font-weight:600;background:var(--bg);color:var(--ink);outline:none">
            <option value="">Select Mode</option>
            <option value="COLLECT">COLLECT</option>
            <option value="CASH">CASH</option>
            <option value="ONLINE">ONLINE</option>
            <option value="CHEQUE">CHEQUE</option>
          </select>
        </div>
        <div style="margin-bottom:14px">
          <label style="font-size:11px;font-weight:700;color:var(--muted);letter-spacing:.04em;display:block;margin-bottom:5px">POS STATUS</label>
          <select id="payPosStatus" style="width:100%;padding:12px 14px;border:1.5px solid var(--border);border-radius:8px;font-size:14px;font-weight:600;background:var(--bg);color:var(--ink);outline:none">
            <option value="STABLE">STABLE</option>
            <option value="RB">RB</option>
            <option value="FLOW">FLOW</option>
          </select>
        </div>
        <div style="margin-bottom:14px">
          <label style="font-size:11px;font-weight:700;color:var(--muted);letter-spacing:.04em;display:block;margin-bottom:5px">RECEIPT CUT</label>
          <select id="payReceiptCut" style="width:100%;padding:12px 14px;border:1.5px solid var(--border);border-radius:8px;font-size:14px;font-weight:600;background:var(--bg);color:var(--ink);outline:none">
            <option value="PAID">PAID</option>
            <option value="UNPAID">UNPAID</option>
          </select>
        </div>
        <div style="margin-bottom:14px">
          <label style="font-size:11px;font-weight:700;color:var(--muted);letter-spacing:.04em;display:block;margin-bottom:5px">PAYMENT DATE</label>
          <input type="date" id="payDate" style="width:100%;padding:12px 14px;border:1.5px solid var(--border);border-radius:8px;font-size:14px;font-weight:600;background:var(--bg);color:var(--ink);outline:none">
        </div>
        <button onclick="submitPayment()" style="width:100%;padding:14px;background:linear-gradient(135deg,#059669,#10b981);color:#fff;border:none;border-radius:10px;font-size:15px;font-weight:800;cursor:pointer;margin-top:8px">✅ Update Payment</button>
      </div>
      
      <div id="payResult" style="display:none;padding:14px;border-radius:10px;text-align:center;font-weight:700;font-size:13px;margin-bottom:16px"></div>
      
      <div style="text-align:center">
        <button onclick="loadPaymentQueue()" style="background:var(--surface);border:1px solid var(--border);color:var(--ink);padding:10px 20px;border-radius:8px;font-weight:700;font-size:12px;cursor:pointer">📋 HDFC Sync Queue</button>
        <button onclick="triggerMainSync()" style="background:linear-gradient(135deg,#1e40af,#2563eb);color:#fff;border:none;padding:10px 20px;border-radius:8px;font-weight:700;font-size:12px;cursor:pointer;margin-left:8px">🔄 Sync to Main File</button>
      </div>
      <div id="payQueueList" style="margin-top:12px"></div>
    </div>
  `;
  
  // Set today's date as default
  const today = new Date().toISOString().split('T')[0];
  document.getElementById('payDate').value = today;
}

async function submitPayment() {
  const loanNo = document.getElementById('payLoanNo').value.trim();
  const amount = document.getElementById('payAmount').value.trim();
  const mode = document.getElementById('payMode').value;
  const posStatus = document.getElementById('payPosStatus').value;
  const receiptCut = document.getElementById('payReceiptCut').value;
  const dateInput = document.getElementById('payDate').value;
  
  if (!loanNo || !amount || !mode || !dateInput) {
    showToast('❌ All fields required');
    return;
  }
  
  // Convert date to dd.mm.yy format
  const parts = dateInput.split('-');
  const payDate = parts[2] + '.' + parts[1] + '.' + parts[0].slice(-2);
  
  showToast('💳 Updating...');
  
  // 1. Save to Google Sheets directly from frontend (bypasses Render redirect issues)
  const GSHEET_URL = 'https://script.google.com/macros/s/AKfycbyKveIlFfsklkMv6Q0FpWC-Y2RtYi6jkZWKBwxgeGifIP6L-71XcmWMOaNdZOushRDwag/exec';
  try {
    fetch(GSHEET_URL, {
      method: 'POST',
      mode: 'no-cors',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({loan_no: loanNo, amount: parseFloat(amount), mode: mode, date: payDate, pos_status: posStatus, receipt_cut: receiptCut})
    });
  } catch(e) { console.log('GSheet save attempt:', e); }
  
  // 2. Update in-memory on Render (for instant report update)
  const result = await apiCall('/api/payment-update', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({loan_no: loanNo, amount: parseFloat(amount), mode: mode, date: payDate, pos_status: posStatus, receipt_cut: receiptCut})
  });
  
  const resDiv = document.getElementById('payResult');
  if (result && result.status === 'ok') {
    resDiv.style.display = 'block';
    resDiv.style.background = '#dcfce7';
    resDiv.style.color = '#166534';
    resDiv.style.border = '1px solid #86efac';
    resDiv.textContent = result.message;
    document.getElementById('payLoanNo').value = '';
    document.getElementById('payAmount').value = '';
    document.getElementById('payMode').value = '';
    showToast('✅ Payment saved!');
  } else {
    resDiv.style.display = 'block';
    resDiv.style.background = '#fee2e2';
    resDiv.style.color = '#991b1b';
    resDiv.style.border = '1px solid #fca5a5';
    resDiv.textContent = result ? result.message : '❌ Server error';
    showToast('❌ Failed');
  }
}

async function cancelPayment(loanNo) {
  if (!confirm(`Cancel payment for ${loanNo}?`)) return;
  showToast('🔄 Cancelling...');
  const result = await apiCall('/api/payment-cancel', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({loan_no: loanNo})
  });
  if (result && result.status === 'ok') {
    showToast('✅ Payment cancelled — reverted to FLOW');
    loadPaymentQueue();
  } else {
    showToast(result ? result.message : '❌ Failed');
  }
}

async function triggerMainSync() {
  showToast('🔄 Triggering sync...');
  const result = await apiCall('/api/sync-to-main', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'}
  });
  if (result && result.status === 'ok') {
    showToast(result.message);
  } else {
    showToast('❌ Sync trigger failed — PC on hai?');
  }
}

async function loadPaymentQueue() {
  const data = await apiCall('/api/payment-queue');
  const div = document.getElementById('payQueueList');
  if (!data || !data.entries || !data.entries.length) {
    div.innerHTML = '<div style="text-align:center;padding:12px;color:var(--muted);font-size:12px">✅ No pending entries. All synced!</div>';
    return;
  }
  let rows = '';
  data.entries.forEach((e, i) => {
    rows += `<tr>
      <td style="padding:8px 10px;font-size:11px;font-weight:700;border-bottom:1px solid var(--border)">${e.loan_no}</td>
      <td style="padding:8px 8px;font-size:11px;text-align:center;border-bottom:1px solid var(--border)">${e.mode}</td>
      <td style="padding:8px 8px;font-size:11px;text-align:center;border-bottom:1px solid var(--border)">₹${e.amount}</td>
      <td style="padding:8px 8px;font-size:11px;text-align:center;border-bottom:1px solid var(--border)">${e.date}</td>
      <td style="padding:8px 4px;text-align:center;border-bottom:1px solid var(--border)"><button onclick="cancelPayment('${e.loan_no}')" style="background:#fee2e2;color:#dc2626;border:none;border-radius:4px;padding:4px 8px;font-size:10px;font-weight:700;cursor:pointer">✕</button></td>
    </tr>`;
  });
  div.innerHTML = `
    <div style="font-size:11px;font-weight:800;color:var(--ink);margin-bottom:6px">⏳ HDFC Sync Pending (${data.pending}) — RCC mein already saved ✅</div>
    <table style="width:100%;border-collapse:collapse;font-size:11px">
      <thead><tr style="background:var(--surface2)">
        <th style="padding:6px 10px;text-align:left;font-size:10px;color:var(--muted)">LOAN NO</th>
        <th style="padding:6px 8px;text-align:center;font-size:10px;color:var(--muted)">MODE</th>
        <th style="padding:6px 8px;text-align:center;font-size:10px;color:var(--muted)">AMT</th>
        <th style="padding:6px 8px;text-align:center;font-size:10px;color:var(--muted)">DATE</th>
        <th style="padding:6px 4px;text-align:center;font-size:10px;color:var(--muted)">❌</th>
      </tr></thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

// ── ADMIN EXECUTIVE FILTER ──
async function loadExecFilter() {
  const data = await apiCall('/api/executives');
  if (!data || !data.executives) return;
  let filterEl = document.getElementById('execFilter');
  if (!filterEl) {
    filterEl = document.createElement('div');
    filterEl.id = 'execFilter';
    filterEl.className = 'exec-filter';
    const pageContent = document.querySelector('.page-content');
    pageContent.parentNode.insertBefore(filterEl, pageContent);
  }
  let options = '<option value="ALL">👥 ALL EXECUTIVES</option>';
  data.executives.forEach(name => {
    options += `<option value="${name}" ${selectedExec === name ? 'selected' : ''}>${name}</option>`;
  });
  filterEl.innerHTML = `
    <div class="filter-label">👤 EXECUTIVE</div>
    <select id="execSelect" onchange="onExecFilterChange(this.value)">${options}</select>
  `;
}

function onExecFilterChange(val) {
  selectedExec = val;
  loadDashboard();
  loadTrails();
  loadFlowList();
  loadRanking();
  searchLoan(document.getElementById('searchInput') ? document.getElementById('searchInput').value : '');
}

function hideExecFilter() {
  const ef = document.getElementById('execFilter');
  if (ef) ef.style.display = 'none';
}

// ── NAVIGATION ──
const navItems = document.querySelectorAll('.nav-item');
const pages = document.querySelectorAll('.page');

navItems.forEach(item => {
  item.addEventListener('click', () => {
    const pageId = item.dataset.page;
    navItems.forEach(n => n.classList.remove('active'));
    item.classList.add('active');
    pages.forEach(p => p.classList.remove('active'));
    document.getElementById(pageId).classList.add('active');
    // Show exec filter on main pages
    const ef = document.getElementById('execFilter');
    if (ef) ef.style.display = '';
    if (pageId === 'pageTrails') loadTrails();
    if (pageId === 'pageFlow') loadFlowList();
    if (pageId === 'pageRanking') loadRanking();
    if (pageId === 'pageSearch') loadSearchCases();
    if (pageId === 'pageProjection') loadProjection();
  });
});

// ── SVG DONUT ──
function donutSVG(pct, color1, color2, id) {
  const r = 36, circ = 2 * Math.PI * r;
  const safePct = Math.max(0, Math.min(100, pct));
  const fill = safePct / 100 * circ;
  const gap = circ - fill;
  const isDark = document.documentElement.getAttribute('data-theme') !== 'light';
  const trackColor = isDark ? '#0a1425' : '#e2e8f0';
  return `<svg width="70" height="70" viewBox="0 0 100 100" style="transform:rotate(-90deg)">
    <circle cx="50" cy="50" r="${r}" fill="none" stroke="${trackColor}" stroke-width="10"/>
    <circle cx="50" cy="50" r="${r}" fill="none" stroke="url(#${id})" stroke-width="10" stroke-dasharray="${fill.toFixed(1)} ${gap.toFixed(1)}" stroke-linecap="round"/>
    <defs><linearGradient id="${id}" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" style="stop-color:${color1}"/><stop offset="100%" style="stop-color:${color2}"/></linearGradient></defs>
  </svg>`;
}

// ── DASHBOARD ──
async function loadDashboard() {
  const el = document.getElementById('dashboardContent');
  const data = await apiCall(`/api/dashboard?${getFilterParams()}`);
  if (!data || data.error) {
    el.innerHTML = '<div class="empty-state"><div class="emoji">📭</div><div class="msg">No data available</div></div>';
    return;
  }

  const b1 = data.bkt1, b2 = data.bkt2;
  const b1Target = 90, b2Target = 70, rcTarget = 65;
  const b1Color = b1.res_pct >= 90 ? '#4ade80' : b1.res_pct >= 85 ? '#fbbf24' : '#f87171';
  const b2Color = b2.res_pct >= 70 ? '#7dd3fc' : b2.res_pct >= 60 ? '#fbbf24' : '#f87171';
  const rcPct = data.receipt_pct;
  const rcBar = Math.min(rcPct / rcTarget * 100, 100);
  const rcGap = Math.max(rcTarget - rcPct, 0).toFixed(0);

  el.innerHTML = `
    <!-- PAYOUT SLAB CARD -->
    <div class="payout-card">
      <div class="payout-header">
        <span style="font-size:1.1rem">💰</span>
        <span class="payout-label">TOTAL COLLECTION</span>
      </div>
      <div class="payout-amount">${fmtFullINR(data.total_collection)}</div>
      <div class="payout-subtitle">Payout: <span class="green">${fmtFullINR(data.total_payout)}</span> (${b1.slab}% slab)</div>
      <div class="slab-grid">
        <div class="slab-item red-bg">
          <div class="slab-tag">CURRENT</div>
          <div class="slab-rate red">${b1.slab}%</div>
          <div class="slab-amt">${fmtFullINR(data.total_payout)}</div>
        </div>
        <div class="slab-item amber-bg">
          <div class="slab-tag">10% SLAB</div>
          <div class="slab-rate amber">10%</div>
          <div class="slab-amt">${fmtFullINR(data.slab_10)}</div>
        </div>
        <div class="slab-item green-bg">
          <div class="slab-tag">12% SLAB</div>
          <div class="slab-rate green">12%</div>
          <div class="slab-amt">${fmtFullINR(data.slab_12)}</div>
        </div>
        <div class="slab-item purple-bg">
          <div class="slab-tag">15% SLAB</div>
          <div class="slab-rate purple">15%</div>
          <div class="slab-amt">${fmtFullINR(data.slab_15)}</div>
        </div>
      </div>
    </div>

    <!-- BKT-1 RESOLUTION CARD -->
    <div class="bkt-card">
      <div class="bkt-header">
        <div class="bkt-title"><span>🏦</span> BKT-1</div>
        <div class="bkt-cases">Cases: <strong>${b1.total}</strong></div>
      </div>
      <div class="bkt-donut-row">
        <div class="donut-wrap">
          ${donutSVG(b1.res_pct, '#10b981', '#4ade80', 'db1')}
          <div class="donut-center">
            <div class="donut-sub">RES%</div>
            <div class="donut-val" style="color:#4ade80">${b1.res_pct.toFixed(0)}%</div>
          </div>
        </div>
        <div class="bkt-big">
          <div class="bkt-big-label">Resolution</div>
          <div class="bkt-big-val" style="color:${b1Color}">${b1.res_pct.toFixed(1)}%</div>
          <div class="bkt-big-target">Target ${b1Target}%</div>
        </div>
        <div class="bkt-rb-box">
          <div class="bkt-rb-label">RB%</div>
          <div class="bkt-rb-val">${b1.rb_pct ? b1.rb_pct.toFixed(1) : '0.0'}%</div>
        </div>
      </div>
      <div class="progress-bar"><div class="progress-fill green" style="width:${Math.min(b1.res_pct, 100)}%"></div><div class="target-marker" style="left:${b1Target}%"></div></div>
      <div class="bkt-stats">
        <div class="bkt-stat"><div class="bkt-stat-label">Flow</div><div class="bkt-stat-val flow">${b1.flow}</div></div>
        <div class="bkt-stat"><div class="bkt-stat-label">Stable</div><div class="bkt-stat-val stable">${b1.stable}</div></div>
        <div class="bkt-stat"><div class="bkt-stat-label">RB</div><div class="bkt-stat-val rb">${b1.rb}</div></div>
      </div>
      <div class="bkt-collection"><span>💰 Collection</span><span class="green">${fmtFullINR(b1.collection)}</span></div>
    </div>

    <!-- BKT-2 RESOLUTION CARD -->
    <div class="bkt-card">
      <div class="bkt-header">
        <div class="bkt-title"><span>🏦</span> BKT-2</div>
        <div class="bkt-cases">Cases: <strong>${b2.total}</strong></div>
      </div>
      <div class="bkt-donut-row">
        <div class="donut-wrap">
          ${donutSVG(b2.res_pct, '#3b82f6', '#7dd3fc', 'db2')}
          <div class="donut-center">
            <div class="donut-sub">RES%</div>
            <div class="donut-val" style="color:#7dd3fc">${b2.res_pct.toFixed(0)}%</div>
          </div>
        </div>
        <div class="bkt-big">
          <div class="bkt-big-label">Resolution</div>
          <div class="bkt-big-val" style="color:${b2Color}">${b2.res_pct.toFixed(1)}%</div>
          <div class="bkt-big-target">Target ${b2Target}%</div>
        </div>
        <div class="bkt-rb-box">
          <div class="bkt-rb-label">RB%</div>
          <div class="bkt-rb-val">${b2.rb_pct ? b2.rb_pct.toFixed(1) : '0.0'}%</div>
        </div>
      </div>
      <div class="progress-bar"><div class="progress-fill blue" style="width:${Math.min(b2.res_pct, 100)}%"></div><div class="target-marker" style="left:${b2Target}%"></div></div>
      <div class="bkt-stats">
        <div class="bkt-stat"><div class="bkt-stat-label">Flow</div><div class="bkt-stat-val flow">${b2.flow}</div></div>
        <div class="bkt-stat"><div class="bkt-stat-label">Stable</div><div class="bkt-stat-val stable">${b2.stable}</div></div>
        <div class="bkt-stat"><div class="bkt-stat-label">RB</div><div class="bkt-stat-val rb">${b2.rb}</div></div>
      </div>
      <div class="bkt-collection"><span>💰 Collection</span><span class="blue">${fmtFullINR(b2.collection)}</span></div>
    </div>

    <!-- RECEIPT CUT CARD -->
    <div class="receipt-card">
      <div class="bkt-header">
        <div class="bkt-title"><span>📋</span> RECEIPT CUT</div>
      </div>
      <div class="receipt-main">
        <div>
          <div class="receipt-label">Current</div>
          <div class="receipt-val green">${rcPct.toFixed(0)}%</div>
        </div>
        <div style="text-align:right">
          <div class="receipt-label">Target</div>
          <div class="receipt-val blue">${rcTarget}%</div>
        </div>
      </div>
      <div class="progress-bar"><div class="progress-fill purple" style="width:${rcBar}%"></div><div class="target-marker" style="left:65%"></div></div>
      <div class="receipt-gap">Gap: <span class="amber">${rcGap}%</span></div>
      <div class="receipt-stats">
        <div class="receipt-stat green-bg"><div class="receipt-stat-label">✅ Paid</div><div class="receipt-stat-val green">${data.paid}</div></div>
        <div class="receipt-stat red-bg"><div class="receipt-stat-label">❌ Unpaid</div><div class="receipt-stat-val red">${data.unpaid}</div></div>
      </div>
      <div class="bkt-collection"><span>💰 Total Collection</span><span class="purple">${fmtFullINR(data.total_collection)}</span></div>
    </div>
  `;
}

// ── PENDING TRAILS (TABLE — LOAN NO + CUSTOMER NAME + AREA) ──
async function loadTrails() {
  const el = document.getElementById('trailsContent');
  const data = await apiCall(`/api/trails?${getFilterParams()}&auth=rcc-admin-token`);
  if (!data) {
    el.innerHTML = '<div class="empty-state"><div class="emoji">⚠️</div><div class="msg">Failed to load</div></div>';
    return;
  }
  if (data.total === 0) {
    el.innerHTML = '<div class="empty-state"><div class="emoji">✅</div><div class="msg">No pending trails! All done.</div></div>';
    return;
  }

  let rows = '';
  data.trails.forEach(t => {
    rows += `<tr><td class="mono">${t.loan_no}</td><td>${t.customer_name}</td><td><span class="area-chip">${t.area}</span></td></tr>`;
  });

  el.innerHTML = `
    <div class="summary-banner">
      <div class="banner-left">
        <span style="font-size:1.3rem">📋</span>
        <div>
          <div class="banner-label">TOTAL PENDING CASES</div>
          <div class="banner-value">${data.total}</div>
        </div>
      </div>
      <div class="banner-right">Showing ${data.total}</div>
    </div>
    <div class="rcc-table-wrap">
      <table class="rcc-table trails-table">
        <colgroup><col><col><col></colgroup>
        <thead><tr><th>LOAN NO</th><th>CUSTOMER NAME</th><th>AREA</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

// ── FLOW LIST (TABLE — CUSTOMER NAME + POS + DRA%) ──
let currentFlowBucket = 1;

function fmtIndianFull(v) {
  if (!v || isNaN(v)) return '0';
  v = Math.round(Math.abs(v));
  let s = v.toString();
  if (s.length <= 3) return s;
  let result = s.slice(-3);
  s = s.slice(0, -3);
  while (s.length > 0) {
    result = s.slice(-2) + ',' + result;
    s = s.slice(0, -2);
  }
  return result;
}

// ── SHARE FLOW LIST ──
async function shareFlowList(bucket) {
  showToast('📤 Generating image...');
  
  // Load html2canvas
  if (typeof html2canvas === 'undefined') {
    await new Promise(resolve => {
      const s = document.createElement('script');
      s.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
      s.onload = resolve;
      document.head.appendChild(s);
    });
  }

  // Capture the flow table area
  const tableEl = document.querySelector('.flow-table-wrap');
  const bannerEl = document.querySelector('.summary-banner');
  
  // Create a container with both banner + table for screenshot
  const wrapper = document.createElement('div');
  wrapper.style.cssText = 'position:absolute;left:-9999px;top:0;background:#ffffff;padding:16px;width:500px;font-family:Inter,sans-serif';
  wrapper.innerHTML = `
    <div style="text-align:center;margin-bottom:12px">
      <div style="font-size:16px;font-weight:900;color:#0f172a">📋 BKT-${bucket} FLOW CASES</div>
      <div style="font-size:12px;color:#64748b;margin-top:4px">${new Date().toLocaleDateString('en-IN',{day:'2-digit',month:'short',year:'numeric'})} · ${document.querySelector('.banner-value')?.textContent || ''} cases</div>
    </div>
  ` + (tableEl ? tableEl.outerHTML : '');
  document.body.appendChild(wrapper);

  try {
    const canvas = await html2canvas(wrapper, {scale: 2, backgroundColor: '#ffffff'});
    const blob = await new Promise(r => canvas.toBlob(r));
    const file = new File([blob], `BKT${bucket}_FlowCases.png`, {type: 'image/png'});
    
    if (navigator.share && navigator.canShare({files: [file]})) {
      await navigator.share({files: [file], title: `BKT-${bucket} Flow Cases`, text: `📋 BKT-${bucket} FLOW CASES`});
    } else {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url; a.download = file.name; a.click();
      showToast('📥 Image downloaded!');
    }
  } catch(e) {
    showToast('❌ Share failed');
  }
  
  document.body.removeChild(wrapper);
}

async function loadFlowList(bucket = currentFlowBucket) {


  currentFlowBucket = bucket;
  const el = document.getElementById('flowContent');
  const data = await apiCall(`/api/flowlist?${getFilterParams()}&bucket=${bucket}&auth=rcc-admin-token`);
  if (!data) {
    el.innerHTML = '<div class="empty-state"><div class="emoji">⚠️</div><div class="msg">Failed to load</div></div>';
    return;
  }

  let tabs = '';
  for (let i = 1; i <= 6; i++) {
    tabs += `<div class="pill-tab ${bucket===i?'active':''}" onclick="loadFlowList(${i})">BKT-${i}</div>`;
  }

  let rows = '';
  if (data.total === 0) {
    rows = `<tr><td colspan="4" style="text-align:center;padding:30px;color:var(--muted)">✅ No flow cases in this bucket</td></tr>`;
  } else {
    data.cases.forEach(c => {
      const posCls = c.projection === 'FLOW' ? 'orange' : 'green';
      rows += `<tr><td>${c.customer_name}</td><td class="mono ${posCls} text-center">₹${fmtIndianFull(c.pos)}</td><td class="mono ${posCls} text-center">${c.dra_pct}%</td><td class="mono text-center" style="font-size:10px;font-weight:700">${c.current_code||''}</td></tr>`;
    });
  }

  // Render table immediately (no delay)
  el.innerHTML = `
    <div class="pill-tabs">${tabs}</div>
    <div style="text-align:center;margin-bottom:8px">
      <button onclick="shareFlowList(${bucket})" style="background:linear-gradient(135deg,#25d366,#128c7e);color:#fff;border:none;padding:8px 16px;border-radius:8px;font-weight:700;font-size:12px;cursor:pointer">📤 Share Flow List</button>
    </div>
    <div class="summary-banner">
      <div class="banner-left">
        <span style="font-size:1.3rem">📋</span>
        <div>
          <div class="banner-label">BKT-${bucket} FLOW CASES</div>
          <div class="banner-value">${data.total}</div>
        </div>
      </div>
      ${showProjection && data.projection ? `
      <div style="display:flex;gap:5px;position:relative;z-index:1">
        <div class="banner-projection">
          <div class="proj-label">CURRENT</div>
          <div class="proj-value">${data.projection.current_res.toFixed(1)}%</div>
          <div style="font-size:.5rem;color:#fbbf24;font-weight:700;margin-top:2px">RB ${data.projection.current_rb.toFixed(1)}%</div>
        </div>
        <div class="banner-projection">
          <div class="proj-label">PROJECTION</div>
          <div class="proj-value">${data.projection.resolution.toFixed(1)}%</div>
        </div>
      </div>` : ''}
    </div>
    <div class="rcc-table-wrap flow-table-wrap">
      <table class="rcc-table flow-table">
        <colgroup><col><col><col><col></colgroup>
        <thead><tr><th>CUSTOMER NAME</th><th class="text-center">POS</th><th class="text-center">DRA%</th><th class="text-center">CODE</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;

}

// ── SEARCH (ACTION CENTER STYLE) ──
let searchTimeout = null;
let searchPageLoaded = false;
let searchBkt = 'ALL';

document.getElementById('searchInput').addEventListener('input', (e) => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => searchLoan(e.target.value), 300);
});

function setSearchBkt(bkt) {
  searchBkt = bkt;
  document.querySelectorAll('#searchBktTabs .pill-tab').forEach((tab, i) => {
    if (bkt === 'ALL' && i === 0) tab.classList.add('active');
    else if (bkt === i) tab.classList.add('active');
    else tab.classList.remove('active');
  });
  searchLoan(document.getElementById('searchInput').value);
}

function loadSearchCases() {
  if (!searchPageLoaded) {
    searchPageLoaded = true;
    searchLoan('');
  }
}

async function searchLoan(query) {
  const el = document.getElementById('searchResults');
  let url = `/api/search?q=${encodeURIComponent(query || '')}&${getFilterParams()}`;
  if (searchBkt !== 'ALL') url += `&bucket=${searchBkt}`;
  
  const data = await apiCall(url);
  if (!data || data.results.length === 0) {
    el.innerHTML = '<div class="empty-state"><div class="emoji">📭</div><div class="msg">No cases found</div></div>';
    return;
  }

  let html = `<div style="font-size:.75rem;color:var(--muted);margin-bottom:10px">Showing: <strong style="color:var(--ink)">${data.results.length}</strong> cases</div>`;

  data.results.forEach((r) => {
    const statusCls = r.pos_status === 'STABLE' ? 'chip-green' : r.pos_status === 'RB' ? 'chip-purple' : 'chip-amber';
    const rcCls = r.receipt_cut === 'PAID' ? 'green' : 'red';
    html += `
      <div class="action-card" onclick="this.classList.toggle('expanded')">
        <div class="action-header">
          <div class="action-title">
            <span style="font-size:.85rem">🏦</span>
            <span>${r.customer_name}</span>
          </div>
          <span class="status-chip ${statusCls}">${r.pos_status}</span>
        </div>
        <div class="action-subtitle">
          For Stable ₹${fmtIndianFull(r.stab_amount)} · POS ₹${fmtIndianFull(r.pos)} · BKT-${r.bucket}
        </div>
        <div class="action-details">
          <div class="detail-section">
            <div class="detail-title">Basic Details</div>
            <div class="detail-grid">
              <div class="detail-item"><span class="detail-label">Loan No</span><span class="detail-value mono">${r.loan_no}</span></div>
              <div class="detail-item"><span class="detail-label">Customer</span><span class="detail-value">${r.customer_name}</span></div>
              <div class="detail-item"><span class="detail-label">Executive</span><span class="detail-value">${r.team}</span></div>
              <div class="detail-item"><span class="detail-label">Area</span><span class="detail-value">${r.area || '—'}</span></div>
              <div class="detail-item"><span class="detail-label">Mobile</span><span class="detail-value mono">${r.mobile || '—'}</span></div>
              <div class="detail-item"><span class="detail-label">Bucket</span><span class="detail-value">BKT-${r.bucket}</span></div>
            </div>
          </div>
          <div class="detail-section">
            <div class="detail-title">Recovery</div>
            <div class="detail-grid">
              <div class="detail-item"><span class="detail-label">EMI</span><span class="detail-value mono">₹${fmtIndianFull(r.emi)}</span></div>
              <div class="detail-item"><span class="detail-label">EMI Due</span><span class="detail-value mono">₹${fmtIndianFull(r.emi_due)}</span></div>
              <div class="detail-item"><span class="detail-label">Stable Amount</span><span class="detail-value mono green">₹${fmtIndianFull(r.stab_amount)}</span></div>
              <div class="detail-item"><span class="detail-label">RB Amount</span><span class="detail-value mono purple">₹${fmtIndianFull(r.rb_amount)}</span></div>
              <div class="detail-item"><span class="detail-label">DPIC</span><span class="detail-value mono amber">₹${fmtIndianFull(r.dpic)}</span></div>
              <div class="detail-item"><span class="detail-label">DPD</span><span class="detail-value mono">${r.dpd}</span></div>
            </div>
          </div>
          <div class="detail-section">
            <div class="detail-title">Status</div>
            <div class="detail-grid">
              <div class="detail-item"><span class="detail-label">POS</span><span class="detail-value mono green">₹${fmtIndianFull(r.pos)}</span></div>
              <div class="detail-item"><span class="detail-label">Paid Amount</span><span class="detail-value mono green">₹${fmtIndianFull(r.paid_amount)}</span></div>
              <div class="detail-item"><span class="detail-label">DRA Case%</span><span class="detail-value mono amber">${r.dra_pct}%</span></div>
              <div class="detail-item"><span class="detail-label">Receipt Cut</span><span class="detail-value ${rcCls}">${r.receipt_cut}</span></div>
              <div class="detail-item"><span class="detail-label">POS Status</span><span class="status-chip ${statusCls}">${r.pos_status}</span></div>
              <div class="detail-item"><span class="detail-label">Trails</span><span class="detail-value mono">${r.trails_pending === 0 ? '⚠️ Pending' : '✅ Done'}</span></div>
            </div>
          </div>
        </div>
      </div>
    `;
  });

  el.innerHTML = html;
}

// ── PROJECTION (replaces Ranking) ──
let projBucket = 1;
let projFilter = 'ALL';

async function loadRanking() {
  // This now loads Projection page
  loadProjectionPage();
}

async function loadProjectionPage() {
  const el = document.getElementById('rankingContent');
  const data = await apiCall(`/api/projection-cases?${getFilterParams()}&bucket=${projBucket}&filter=${projFilter}`);
  if (!data) {
    el.innerHTML = '<div class="empty-state"><div class="emoji">📊</div><div class="msg">Failed to load</div></div>';
    return;
  }

  // Bucket tabs
  let bktTabs = '';
  for (let i = 1; i <= 6; i++) {
    bktTabs += `<div class="pill-tab ${projBucket===i?'active':''}" onclick="projBucket=${i};loadProjectionPage()">BKT-${i}</div>`;
  }

  // Filter tabs
  const filters = ['ALL','FLOW','STABLE','RB'];
  let filterTabs = '';
  filters.forEach(f => {
    const active = projFilter === f ? 'active' : '';
    filterTabs += `<div class="pill-tab ${active}" onclick="projFilter='${f}';loadProjectionPage()" style="font-size:11px">${f}${f==='FLOW'?' ('+data.flow_count+')':f==='STABLE'?' ('+data.stable_count+')':f==='RB'?' ('+data.rb_count+')':''}</div>`;
  });

  // Table rows
  let rows = '';
  if (data.total === 0) {
    rows = `<tr><td colspan="4" style="text-align:center;padding:30px;color:var(--muted)">No cases</td></tr>`;
  } else {
    data.cases.forEach(c => {
      const codeCls = c.code === 'FLOW' ? 'color:#ef4444' : c.code === 'STABLE' ? 'color:#059669' : c.code === 'RB' ? 'color:#d97706' : 'color:var(--muted)';
      rows += `<tr>
        <td style="font-size:11px;font-weight:700;padding:8px 6px">${c.customer_name}</td>
        <td class="mono" style="font-size:11px;text-align:right;padding:8px 6px">₹${fmtIndianFull(c.pos)}</td>
        <td class="mono" style="font-size:11px;text-align:center;padding:8px 6px;color:#059669">${c.dra_pct}%</td>
        <td style="font-size:10px;font-weight:800;text-align:center;padding:8px 6px;${codeCls}">${c.code}</td>
      </tr>`;
    });
  }

  el.innerHTML = `
    <div style="text-align:center;margin-bottom:8px">
      <button onclick="shareProjection()" style="background:linear-gradient(135deg,#25d366,#128c7e);color:#fff;border:none;padding:8px 16px;border-radius:8px;font-weight:700;font-size:12px;cursor:pointer">📤 Share</button>
    </div>
    <div class="pill-tabs">${bktTabs}</div>
    <div class="pill-tabs" style="margin-top:6px">${filterTabs}</div>
    <div class="summary-banner">
      <div class="banner-left">
        <span style="font-size:1.3rem">📊</span>
        <div>
          <div class="banner-label">BKT-${projBucket} PROJECTION</div>
          <div class="banner-value">${data.total} cases</div>
        </div>
      </div>
    </div>
    <div class="rcc-table-wrap">
      <table class="rcc-table">
        <thead><tr><th>CUSTOMER</th><th class="text-center">POS</th><th class="text-center">DRA%</th><th class="text-center">CODE</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

function downloadMonthlyIncentive() {
  toggleMenu();
  const now = new Date();
  const month = now.getMonth() + 1;
  const year = now.getFullYear();
  showToast('📊 Downloading...');
  window.open(`${API}/api/report/monthly-incentive/download?month=${month}&year=${year}`, '_blank');
}

async function shareProjection() {
  showToast('📤 Generating...');
  if (typeof html2canvas === 'undefined') {
    await new Promise(r => { const s=document.createElement('script'); s.src='https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js'; s.onload=r; document.head.appendChild(s); });
  }
  const el = document.querySelector('#rankingContent .rcc-table-wrap');
  if (!el) return;
  const canvas = await html2canvas(el, {scale: 2, backgroundColor: '#0b1120'});
  const blob = await new Promise(r => canvas.toBlob(r));
  const file = new File([blob], `BKT${projBucket}_Projection.png`, {type: 'image/png'});
  if (navigator.share && navigator.canShare({files: [file]})) {
    navigator.share({files: [file], title: `BKT-${projBucket} Projection`});
  } else {
    const url = URL.createObjectURL(blob); const a=document.createElement('a'); a.href=url; a.download=file.name; a.click();
    showToast('📥 Downloaded');
  }
}

// ── PROJECTION ──
let currentProjBkt = 1;

function setProjBkt(bkt) {
  currentProjBkt = bkt;
  document.querySelectorAll('#projBktTabs .pill-tab').forEach((t, i) => {
    t.classList.toggle('active', i === bkt - 1);
  });
  loadProjection();
}

async function loadProjection() {
  const el = document.getElementById('projContent');
  el.innerHTML = '<div class="loader"><div class="spinner"></div></div>';
  const data = await apiCall(`/api/projection?bucket=${currentProjBkt}`);
  if (!data || !data.teams || !data.teams.length) {
    el.innerHTML = '<div class="empty-state"><div class="emoji">📈</div><div class="msg">No projection data for BKT-' + currentProjBkt + '</div></div>';
    return;
  }

  let rows = '';
  data.teams.forEach((t, i) => {
    const resColor = t.resolution >= 85 ? '#22c55e' : t.resolution >= 70 ? '#f59e0b' : t.resolution >= 50 ? '#f97316' : '#ef4444';
    const bgColor = t.resolution >= 85 ? 'rgba(34,197,94,0.08)' : t.resolution >= 70 ? 'rgba(245,158,11,0.08)' : t.resolution >= 50 ? 'rgba(249,115,22,0.08)' : 'rgba(239,68,68,0.08)';
    rows += `<tr style="background:${bgColor}">
      <td class="exec-name">${t.team}</td>
      <td class="mono">${formatIndian(t.flow)}</td>
      <td class="mono green">${formatIndian(t.stable)}</td>
      <td class="mono" style="color:#f59e0b">${formatIndian(t.rb)}</td>
      <td class="mono">${formatIndian(t.grand_total)}</td>
      <td class="mono">${t.stable_pct.toFixed(1)}%</td>
      <td class="mono">${t.rb_pct.toFixed(1)}%</td>
      <td><span class="status-chip" style="background:${resColor};color:#fff;font-weight:700">${t.resolution.toFixed(2)}%</span></td>
    </tr>`;
  });

  // Grand total row
  const g = data.grand_total;
  const gColor = g.resolution >= 85 ? '#22c55e' : g.resolution >= 70 ? '#f59e0b' : g.resolution >= 50 ? '#f97316' : '#ef4444';
  rows += `<tr style="font-weight:700;border-top:2px solid var(--border)">
    <td>TOTAL</td>
    <td class="mono">${formatIndian(g.flow)}</td>
    <td class="mono green">${formatIndian(g.stable)}</td>
    <td class="mono" style="color:#f59e0b">${formatIndian(g.rb)}</td>
    <td class="mono">${formatIndian(g.grand_total)}</td>
    <td class="mono">${g.stable_pct.toFixed(1)}%</td>
    <td class="mono">${g.rb_pct.toFixed(1)}%</td>
    <td><span class="status-chip" style="background:${gColor};color:#fff;font-weight:700">${g.resolution.toFixed(2)}%</span></td>
  </tr>`;

  el.innerHTML = `
    <div class="summary-banner">
      <div class="banner-left">
        <span style="font-size:1.3rem">📈</span>
        <div>
          <div class="banner-label">PROJECTION BKT-${currentProjBkt}</div>
          <div class="banner-value">${data.teams.length} Executives · Resolution ${g.resolution.toFixed(2)}%</div>
        </div>
      </div>
      <div class="banner-right">
        <span class="status-chip" style="background:${gColor};color:#fff;font-size:1.1rem;font-weight:700">${g.resolution.toFixed(1)}%</span>
      </div>
    </div>
    <div class="rcc-table-wrap">
      <table class="rcc-table">
        <thead><tr><th>TEAM</th><th>FLOW</th><th>STABLE</th><th>RB</th><th>TOTAL</th><th>S%</th><th>RB%</th><th>RES%</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

// ── INIT ──
checkSession();
