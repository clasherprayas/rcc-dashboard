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
    const theme = document.documentElement.getAttribute('data-theme') || 'dark';
    document.getElementById('menuThemeLabel').textContent = theme === 'dark' ? '☀️ Light Mode' : '🌙 Dark Mode';
    const projToggle = document.getElementById('projToggle');
    if (projToggle) projToggle.checked = showProjection;
    loadPublicAccessStatus();
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
    if (linkToggle) linkToggle.checked = data.enabled;
    if (pwdToggle) pwdToggle.checked = data.password_required;
    if (searchToggle) searchToggle.checked = data.search_enabled;
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
  loadFlowList();
}

async function forceRefresh() {
  toggleMenu();
  showToast('🔄 Syncing data...');
  try {
    await fetch(`${API}/api/force-sync`, { method: 'POST' });
  } catch(e) {}
  loadDashboard();
  loadTrails();
  loadRanking();
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
  loadFlowList();
  loadRanking();
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
    rows = `<tr><td colspan="3" style="text-align:center;padding:30px;color:var(--muted)">✅ No flow cases in this bucket</td></tr>`;
  } else {
    data.cases.forEach(c => {
      const posCls = c.projection === 'FLOW' ? 'orange' : 'green';
      rows += `<tr><td>${c.customer_name}</td><td class="mono ${posCls} text-right">₹${fmtIndianFull(c.pos)}</td><td class="mono ${posCls} text-right">${c.dra_pct}%</td></tr>`;
    });
  }

  // Render table immediately (no delay)
  el.innerHTML = `
    <div class="pill-tabs">${tabs}</div>
    <div class="summary-banner">
      <div class="banner-left">
        <span style="font-size:1.3rem">📋</span>
        <div>
          <div class="banner-label">BKT-${bucket} FLOW CASES</div>
          <div class="banner-value">${data.total}</div>
        </div>
      </div>
      ${showProjection ? `
      <div style="display:flex;gap:6px;position:relative;z-index:1">
        <div class="banner-projection" id="curResBox">
          <div class="proj-label">CURRENT</div>
          <div class="proj-value" id="curResVal">--%</div>
        </div>
        <div class="banner-projection" id="projResBox">
          <div class="proj-label">PROJECTION</div>
          <div class="proj-value" id="projResVal">--%</div>
        </div>
      </div>` : ''}
    </div>
    <div class="rcc-table-wrap flow-table-wrap">
      <table class="rcc-table flow-table">
        <colgroup><col><col><col></colgroup>
        <thead><tr><th>CUSTOMER NAME</th><th class="text-right">POS</th><th class="text-right">DRA CASE %</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;

  // Load projection in background (no blocking)
  if (showProjection) {
    const execParam = (currentUser.role === 'admin' && selectedExec !== 'ALL') ? selectedExec : 
                      (currentUser.role !== 'admin') ? currentUser.username : '';
    const projUrl = execParam ? `/api/projection?bucket=${bucket}&user=${encodeURIComponent(execParam)}` : `/api/projection?bucket=${bucket}`;
    apiCall(projUrl).then(projData => {
      if (!projData) return;
      let projValue = '--', curResValue = '--';
      // User-specific response: resolution at top level
      if (projData.user && projData.resolution !== undefined) {
        projValue = projData.resolution.toFixed(1);
        curResValue = (projData.current_res || 0).toFixed(1);
      }
      // ALL executives response: grand_total is an object with resolution
      else if (projData.grand_total && typeof projData.grand_total === 'object') {
        projValue = projData.grand_total.resolution.toFixed(1);
        curResValue = (projData.grand_total.current_res || 0).toFixed(1);
      }
      const curEl = document.getElementById('curResVal');
      const projEl = document.getElementById('projResVal');
      if (curEl) curEl.textContent = curResValue + '%';
      if (projEl) projEl.textContent = projValue + '%';
    });
  }
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

// ── RANKING ──
async function loadRanking() {
  const el = document.getElementById('rankingContent');
  const data = await apiCall('/api/ranking');
  if (!data || !data.ranking.length) {
    el.innerHTML = '<div class="empty-state"><div class="emoji">🏆</div><div class="msg">No ranking data</div></div>';
    return;
  }

  let rows = '';
  data.ranking.forEach(r => {
    const resCls = r.resolution_pct >= 80 ? 'chip-green' : r.resolution_pct >= 60 ? 'chip-amber' : 'chip-red';
    rows += `<tr>
      <td class="rank-cell"><span class="rank-badge ${r.rank<=3?'rank-'+r.rank:''}">${r.rank}</span></td>
      <td class="exec-name">${r.executive}</td>
      <td class="mono">${r.cases}</td>
      <td class="mono green">${r.paid}</td>
      <td><span class="status-chip ${resCls}">${r.resolution_pct.toFixed(1)}%</span></td>
      <td class="mono">${formatIndian(r.collection)}</td>
    </tr>`;
  });

  el.innerHTML = `
    <div class="summary-banner">
      <div class="banner-left">
        <span style="font-size:1.3rem">🏆</span>
        <div>
          <div class="banner-label">EXECUTIVE RANKING</div>
          <div class="banner-value">${data.ranking.length} Executives</div>
        </div>
      </div>
    </div>
    <div class="rcc-table-wrap">
      <table class="rcc-table">
        <thead><tr><th>#</th><th>EXECUTIVE</th><th>CASES</th><th>PAID</th><th>RES%</th><th>COLLECTION</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
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
