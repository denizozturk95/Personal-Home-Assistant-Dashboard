const TOKEN_KEY = "dashboard_token";
const ICONS = {
  toggle: "⏻",
  bulb: "💡",
  lock: "🔒",
  fan: "🌀",
  bolt: "⚡",
  plug: "🔌",
  tv: "📺",
  speaker: "🔊",
};

const grid = document.getElementById("grid");
const settingsBtn = document.getElementById("settings-btn");
const dialog = document.getElementById("settings-dialog");
const tokenInput = document.getElementById("token-input");
const saveTokenBtn = document.getElementById("save-token");

function getToken() {
  return localStorage.getItem(TOKEN_KEY) || "";
}

function authHeaders() {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function loadActions() {
  grid.innerHTML = "";
  if (!getToken()) {
    openSettings();
    return;
  }
  try {
    const res = await fetch("/api/actions", { headers: authHeaders() });
    if (res.status === 401) {
      openSettings();
      return;
    }
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const { actions } = await res.json();
    for (const a of actions) grid.appendChild(renderTile(a));
  } catch (err) {
    const note = document.createElement("p");
    note.textContent = `Failed to load actions: ${err.message}`;
    note.style.color = "var(--err)";
    note.style.padding = "0 16px";
    grid.appendChild(note);
  }
}

function renderTile(action) {
  const btn = document.createElement("button");
  btn.className = "tile";
  btn.dataset.id = action.id;
  btn.innerHTML = `
    <span class="icon">${ICONS[action.icon] || ICONS.bolt}</span>
    <span class="label">${action.label}</span>
  `;
  btn.addEventListener("click", () => runAction(btn, action.id));
  return btn;
}

async function runAction(btn, id) {
  if (btn.dataset.state === "running") return;
  const prev = btn.dataset.state;
  btn.dataset.state = "running";
  try {
    const res = await fetch(`/api/run/${encodeURIComponent(id)}`, {
      method: "POST",
      headers: authHeaders(),
    });
    const body = await res.json().catch(() => ({}));
    btn.dataset.state = res.ok && body.ok ? "ok" : "err";
  } catch {
    btn.dataset.state = "err";
  }
  setTimeout(() => {
    if (btn.dataset.state !== "running") delete btn.dataset.state;
  }, 1400);
}

function openSettings() {
  tokenInput.value = getToken();
  dialog.showModal();
}

settingsBtn.addEventListener("click", openSettings);
saveTokenBtn.addEventListener("click", (e) => {
  e.preventDefault();
  const value = tokenInput.value.trim();
  if (value) localStorage.setItem(TOKEN_KEY, value);
  dialog.close();
  loadActions();
});

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("sw.js").catch(() => {});
}

loadActions();
