import os
import re
import json
import time
import hmac
import secrets
import tempfile
import threading
import requests
from datetime import timedelta
from functools import wraps
from urllib.parse import urlencode
from flask import Flask, redirect, request, session, render_template_string, abort, jsonify
from markupsafe import escape
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

# ======================= الإعدادات الأمنية =======================
SECRET = os.environ.get("SESSION_SECRET", "")
if len(SECRET) < 32:
    raise RuntimeError("اضبط SESSION_SECRET (32 حرف أو أكثر) في متغيرات البيئة")
app.secret_key = SECRET

LOCAL_DEV = os.environ.get("LOCAL_DEV") == "1"

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

app.config.update(
    SESSION_COOKIE_SECURE=not LOCAL_DEV,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=2),
    MAX_CONTENT_LENGTH=5 * 1024 * 1024,
)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["300 per hour"],
    storage_uri="memory://",
)

CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET", "").strip()

REDIRECT_URI = os.environ.get(
    "DISCORD_REDIRECT_URI",
    "https://sky-panel-z0b2.onrender.com/callback"
).strip()
BOT_TOKEN = os.environ.get("DISCORD_TOKEN", "").strip()
BOT_API_KEY = os.environ.get("BOT_API_KEY", "").strip()

API_ENDPOINT = "https://discord.com/api/v10"
BOT_PERMISSIONS = os.environ.get("BOT_PERMISSIONS", "8")

BOT_INVITE_URL = (
    "https://discord.com/oauth2/authorize?"
    + urlencode({
        "client_id": CLIENT_ID,
        "permissions": BOT_PERMISSIONS,
        "integration_type": "0",
        "scope": "bot"
    })
)

GUILD_ID_RE = re.compile(r"^\d{15,25}$")
KEY_RE = re.compile(r"^[a-z0-9_]{1,64}$")
SEC_KEYS = {"bad_words", "spam", "links", "mention_spam"}
CMD_NAMES = {
    "ban", "unban", "clear", "hide", "show", "lock", "unlock", "move", "role",
    "setnick", "timeout", "untimeout", "vkick", "warn", "unwarn", "warns", "vmute"
}

# ======================= تخزين الإعدادات + سجل التعديلات =======================
DATA_FILE = os.environ.get("DATA_FILE", "settings_db.json")
_db_lock = threading.Lock()
_STATE = {"rev": 0, "guilds": {}, "log": []}


def _load_db():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            _STATE["rev"] = int(data.get("rev", 0))
            _STATE["guilds"] = data.get("guilds", {})
            _STATE["log"] = data.get("log", [])
    except (FileNotFoundError, ValueError):
        pass


def _save_db():
    d = os.path.dirname(os.path.abspath(DATA_FILE))
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(_STATE, f, ensure_ascii=False)
    os.replace(tmp, DATA_FILE)


_load_db()


def commit_settings(guild_id, page_key, new_data):
    with _db_lock:
        guild = _STATE["guilds"].setdefault(guild_id, {})
        old = guild.get(page_key, {})
        changed = sorted(k for k in (set(old) | set(new_data)) if old.get(k) != new_data.get(k))
        if not changed:
            return []
        guild[page_key] = new_data
        _STATE["rev"] += 1
        _STATE["log"].append({
            "rev": _STATE["rev"], "guild_id": guild_id, "page": page_key,
            "changed": changed, "ts": int(time.time()),
        })
        _STATE["log"] = _STATE["log"][-200:]
        _save_db()
        return changed


STYLE = r"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ page_title }} | Sky Universe</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800;900&display=swap');

:root {
  --bg: #050816;
  --panel: rgba(14, 23, 48, .85);
  --line: rgba(120, 170, 255, .2);
  --blue: #64caff;
  --purple: #9b8cff;
  --gold: #f0b429;
  --green: #2ed573;
  --red: #ff4757;
  --text: #f4f7ff;
  --muted: #9baaca;
}

* { box-sizing: border-box; }

body {
  margin: 0; min-height: 100vh; color: var(--text);
  font-family: 'Cairo', Tahoma, sans-serif;
  background:
    radial-gradient(ellipse at 15% 15%, rgba(46, 80, 180, .27), transparent 38%),
    radial-gradient(ellipse at 85% 35%, rgba(110, 49, 180, .20), transparent 36%),
    radial-gradient(ellipse at 50% 100%, rgba(18, 105, 165, .19), transparent 43%),
    var(--bg);
  overflow-x: hidden; padding-bottom: 90px;
}

body:before {
  content: ""; position: fixed; inset: 0; pointer-events: none; z-index: -1;
  background-image:
    radial-gradient(2px 2px at 12% 22%, #ffffffa8 50%, transparent 100%),
    radial-gradient(1px 1px at 35% 72%, #b5d9ff 50%, transparent 100%),
    radial-gradient(2px 2px at 78% 18%, #ffffffa0 50%, transparent 100%),
    radial-gradient(1px 1px at 91% 67%, #c6c4ff 50%, transparent 100%),
    radial-gradient(1px 1px at 62% 43%, #ffffffb0 50%, transparent 100%),
    radial-gradient(2px 2px at 24% 88%, #8ccfff90 50%, transparent 100%);
  background-size: 290px 260px, 340px 310px, 400px 350px,
                   320px 300px, 270px 330px, 370px 290px;
  opacity: .75;
}

a { color: inherit; text-decoration: none; }

.nav {
  display: flex; justify-content: space-between; align-items: center;
  gap: 18px; padding: 20px clamp(24px, 5vw, 60px);
  border-bottom: 1px solid var(--line);
  background: rgba(5, 8, 22, .85);
  backdrop-filter: blur(18px); position: relative; z-index: 2;
}

.brand { display: flex; align-items: center; gap: 14px; }
.logo {
  width: 50px; height: 50px; display: grid; place-items: center;
  border-radius: 16px; font-size: 26px;
  background: linear-gradient(135deg, #53caff, #8271ff);
  box-shadow: 0 0 30px #4c9fff38;
}
.brand h2 { margin: 0; font-size: 22px; font-weight: 900; }
.brand small { color: var(--muted); font-size: 12px; display: block; }
.nav-right { display: flex; align-items: center; gap: 14px; }

.user-pill {
  display: flex; align-items: center; gap: 10px; padding: 8px 16px;
  background: #ffffff08; border: 1px solid var(--line); border-radius: 50px;
  font-size: 14px; backdrop-filter: blur(10px);
}
.user-pill img { width: 36px; height: 36px; border-radius: 50%; }

.btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  padding: 12px 22px; border-radius: 12px; text-decoration: none;
  font-family: inherit; font-size: 14px; font-weight: 800;
  transition: transform .2s ease, box-shadow .2s ease, background .2s ease;
  border: 1px solid transparent; cursor: pointer;
}
.btn:hover { transform: translateY(-3px); }
.btn-primary {
  color: #06101f; background: linear-gradient(115deg, #73dcff, #a6a0ff);
  box-shadow: 0 8px 28px #58baff38;
}
.btn-green { color: #ffffff; background: var(--green); font-weight: 900; box-shadow: 0 4px 15px rgba(46, 213, 115, 0.4); }
.btn-green:hover { background: #26af5f; }
.btn-red { color: #ffffff; background: var(--red); font-weight: 900; box-shadow: 0 4px 15px rgba(255, 71, 87, 0.4); }
.btn-red:hover { background: #e03847; }
.btn-secondary {
  color: #e5edff; border-color: var(--line); background: rgba(255,255,255,0.05);
  backdrop-filter: blur(10px);
}
.btn-discord {
  color: #ffffff; background: #5865F2; box-shadow: 0 4px 20px rgba(88,101,242,0.4);
}
.btn-discord:hover { background: #4752C4; }

.page { width: min(1350px, 95%); margin: 40px auto 70px; }
.page-head { display: flex; justify-content: space-between; align-items: center; gap: 20px; margin-bottom: 35px; }
.page-head h1 { font-size: 30px; margin: 0 0 6px; }
.page-head p { color: var(--muted); margin: 0; font-size: 14px; }

.server-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 22px; }
.server-card {
  padding: 30px 22px; text-align: center; border-radius: 22px;
  border: 1px solid var(--line);
  background: linear-gradient(155deg, rgba(24, 36, 65, 0.8), rgba(11, 18, 39, 0.9));
  box-shadow: 0 12px 35px rgba(0,0,0,0.3); transition: transform .22s, border-color .22s;
  backdrop-filter: blur(12px);
}
.server-card:hover { transform: translateY(-5px); border-color: rgba(117, 202, 255, 0.6); }
.server-icon {
  width: 90px; height: 90px; border-radius: 26px; object-fit: cover;
  border: 2px solid rgba(128, 207, 255, 0.5); box-shadow: 0 0 25px rgba(100, 186, 255, 0.2);
}
.server-card h3 { margin: 16px 0 6px; font-size: 17px; overflow-wrap: anywhere; }
.status { color: #78e3bc; font-size: 12px; margin-bottom: 12px; }
.server-card .btn { margin-top: 12px; width: 100%; }

.empty {
  padding: 55px 25px; text-align: center; border: 1px dashed rgba(123, 157, 202, 0.3);
  background: rgba(255,255,255,0.02); border-radius: 20px; color: var(--muted); font-size: 15px;
}
.empty span { display: block; font-size: 40px; margin-bottom: 12px; }

.dashboard-layout {
  display: grid; grid-template-columns: 300px 1fr; gap: 30px;
  width: 100%; margin: 40px auto 70px; align-items: start; direction: rtl;
}

.sidebar {
  background: linear-gradient(155deg, rgba(18, 28, 56, 0.9), rgba(8, 13, 31, 0.95));
  border: 1px solid var(--line); border-radius: 24px; padding: 26px;
  display: flex; flex-direction: column; gap: 18px; backdrop-filter: blur(16px);
  position: sticky; top: 25px; order: 1;
}

.content-panel {
  background: var(--panel); border: 1px solid var(--line); border-radius: 24px; padding: 35px;
  backdrop-filter: blur(16px); min-height: 700px;
  box-shadow: 0 20px 50px rgba(0,0,0,0.4); order: 2; width: 100%; overflow: hidden;
}

.sidebar-header { text-align: center; padding-bottom: 16px; border-bottom: 1px solid var(--line); }
.sidebar-icon {
  width: 75px; height: 75px; border-radius: 22px; object-fit: cover;
  border: 2px solid rgba(117, 202, 255, 0.5); box-shadow: 0 0 25px rgba(100, 186, 255, 0.2);
  margin: 0 auto 10px; display: block;
}
.sidebar-header h3 { margin: 0 0 3px; font-size: 16px; overflow-wrap: anywhere; }
.sidebar-header p { color: var(--muted); font-size: 12px; margin: 0; }

.menu-list { display: flex; flex-direction: column; gap: 6px; }
.menu-item {
  display: flex; align-items: center; gap: 12px; padding: 11px 15px;
  border-radius: 12px; color: var(--muted); font-weight: 700; font-size: 14px;
  transition: all .15s ease; border: 1px solid transparent;
}
.menu-item:hover, .menu-item.active {
  background: linear-gradient(115deg, rgba(91, 191, 255, 0.12), rgba(143, 130, 255, 0.12));
  color: var(--text); border-color: rgba(122, 203, 255, 0.3);
  box-shadow: 0 4px 18px rgba(88, 186, 255, 0.1); transform: translateX(-3px);
}
.menu-item span { font-size: 18px; }

.form-group { margin-bottom: 22px; width: 100%; }
.form-group label { display: block; font-size: 14px; font-weight: 700; color: #cedbfa; margin-bottom: 8px; text-align: right; }
.field-desc { font-size: 12px; color: var(--muted); margin-bottom: 6px; text-align: right; line-height: 1.6; }

.form-control {
  width: 100%; padding: 12px 16px; border-radius: 12px;
  background: rgba(6, 10, 23, 0.85); border: 1px solid var(--line); color: var(--text);
  font-family: inherit; font-size: 14px; outline: none; transition: border-color .2s;
  text-align: right; direction: rtl;
}
.form-control:focus { border-color: var(--blue); box-shadow: 0 0 15px rgba(100, 186, 255, 0.2); }

select.form-control {
  appearance: none; -webkit-appearance: none; -moz-appearance: none;
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%239baaca' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
  background-repeat: no-repeat; background-position: left 14px center; background-size: 16px; cursor: pointer;
}

.tag-input-container {
  background: rgba(6, 10, 23, 0.85); border: 1px solid var(--line); border-radius: 12px;
  padding: 8px 12px; min-height: 50px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; cursor: pointer; position: relative;
}
.tag-badge {
  background: linear-gradient(115deg, #64caff, #9b8cff); color: #06101f;
  padding: 4px 12px; border-radius: 8px; font-size: 12px; font-weight: 800;
  display: inline-flex; align-items: center; gap: 8px; flex-direction: row-reverse;
}
.tag-badge .remove-tag { cursor: pointer; font-size: 14px; font-weight: 900; color: #06101f; }
.tag-select-dropdown {
  width: 100%; margin-top: 6px; background: rgba(12, 19, 39, 0.98); border: 1px solid var(--line);
  border-radius: 10px; padding: 8px; max-height: 180px; overflow-y: auto; display: none; position: relative; z-index: 50; box-shadow: 0 10px 30px rgba(0,0,0,0.6);
}
.tag-select-dropdown.show { display: block; }
.tag-option { padding: 8px 12px; border-radius: 6px; cursor: pointer; font-size: 13px; color: var(--text); text-align: right; }
.tag-option:hover { background: rgba(100,202,255,0.2); }

.settings-section-card {
  background: rgba(8, 13, 31, 0.7); border: 1px solid var(--line); border-radius: 18px;
  padding: 26px; margin-bottom: 24px; box-shadow: 0 8px 25px rgba(0,0,0,0.25);
  backdrop-filter: blur(10px); width: 100%;
}
.settings-section-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; padding-bottom: 14px; border-bottom: 1px solid var(--line);
}
.settings-section-title { font-size: 16px; font-weight: 800; color: #e4eeff; display: flex; align-items: center; gap: 10px; }

.floating-save-bar {
  position: fixed; bottom: 25px; left: 50%; transform: translateX(-50%) translateY(120px);
  background: rgba(10, 16, 35, 0.95); border: 1px solid rgba(46, 213, 115, 0.4); border-radius: 16px;
  padding: 14px 28px; display: flex; align-items: center; gap: 24px;
  box-shadow: 0 15px 45px rgba(0,0,0,0.6); backdrop-filter: blur(16px);
  z-index: 1000; transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
.floating-save-bar.visible { transform: translateX(-50%) translateY(0); }
.save-bar-info { display: flex; align-items: center; gap: 10px; font-size: 14px; font-weight: 700; color: #e4eeff; }
.save-dot { width: 10px; height: 10px; background: var(--green); border-radius: 50%; box-shadow: 0 0 10px var(--green); animation: pulse 1.5s infinite; }
@keyframes pulse { 0% { opacity: 0.4; } 50% { opacity: 1; } 100% { opacity: 0.4; } }

.switch { position: relative; display: inline-block; width: 48px; height: 26px; }
.switch input { opacity: 0; width: 0; height: 0; }
.slider {
  position: absolute; cursor: pointer; inset: 0;
  background-color: #1a2748; transition: .3s; border-radius: 34px; border: 1px solid var(--line);
}
.slider:before {
  position: absolute; content: ""; height: 18px; width: 18px; left: 4px; bottom: 3px;
  background-color: white; transition: .3s; border-radius: 50%;
}
input:checked + .slider { background: linear-gradient(115deg, #64caff, #9b8cff); }
input:checked + .slider:before { transform: translateX(22px); }

.cards-grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 25px; }
.card-item {
  background: rgba(8, 13, 31, 0.7); border: 1px solid var(--line); border-radius: 16px;
  padding: 20px; display: flex; flex-direction: column; gap: 14px;
  box-shadow: 0 8px 25px rgba(0,0,0,0.25); backdrop-filter: blur(10px);
}
.card-header { display: flex; justify-content: space-between; align-items: center; }
.card-title { font-size: 15px; font-weight: 800; color: #e4eeff; display: flex; align-items: center; gap: 8px; }

.security-card {
  background: rgba(8, 13, 31, 0.7); border: 1px solid var(--line); border-radius: 16px;
  padding: 22px; display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 15px; box-shadow: 0 8px 25px rgba(0,0,0,0.25); backdrop-filter: blur(10px);
}
.security-info h3 { margin: 0 0 5px; font-size: 16px; color: #e4eeff; text-align: right; }
.security-info p { margin: 0; font-size: 13px; color: var(--muted); text-align: right; }

.btn-edit {
  background: #152242; border: 1px solid var(--line); color: var(--blue);
  padding: 8px 16px; border-radius: 10px; display: inline-flex; align-items: center; gap: 6px;
  cursor: pointer; transition: background .2s; font-size: 13px; font-weight: 700;
}
.btn-edit:hover { background: #20356b; }

.footer {
  text-align: center; color: #7785a5; font-size: 13px; padding: 35px 20px;
  border-top: 1px solid var(--line); margin-top: 50px;
  display: flex; flex-direction: column; align-items: center; gap: 14px;
}
.footer-links { display: flex; gap: 16px; align-items: center; }
</style>
<script>
let hasUnsavedChanges = false;

function triggerChange() {
  hasUnsavedChanges = true;
  const bar = document.getElementById('saveBar');
  if (bar) bar.classList.add('visible');
}

function revertToLastSaved() {
  hasUnsavedChanges = false;
  const bar = document.getElementById('saveBar');
  if (bar) bar.classList.remove('visible');
  window.location.href = window.location.pathname;
}

function applySavedSettings() {
  const saved = window.COMMITTED_SETTINGS;
  const form = document.getElementById('mainForm');
  if (!saved || !form) return;

  for (const el of Array.from(form.elements)) {
    if (!el.name || el.name === 'csrf_token' || el.type === 'submit' || el.type === 'button') continue;
    const has = Object.prototype.hasOwnProperty.call(saved, el.name);
    if (el.type === 'checkbox') { el.checked = has; continue; }
    if (!has) continue;
    const v = saved[el.name];
    if (el.tagName === 'SELECT' && el.multiple) {
      const arr = Array.isArray(v) ? v : [v];
      Array.from(el.options).forEach(o => { o.selected = arr.includes(o.value); });
    } else if (el.type === 'radio') {
      el.checked = (el.value === v);
    } else {
      el.value = Array.isArray(v) ? v[0] : v;
    }
  }

  hasUnsavedChanges = false;
  const bar = document.getElementById('saveBar');
  if (bar) bar.classList.remove('visible');
}

window.addEventListener('DOMContentLoaded', () => {
  applySavedSettings();
  const form = document.getElementById('mainForm');
  if (form) {
    form.addEventListener('input', triggerChange);
    form.addEventListener('change', triggerChange);
    form.addEventListener('submit', () => {
      hasUnsavedChanges = false;
      const bar = document.getElementById('saveBar');
      if (bar) bar.classList.remove('visible');
    });
  }
  window.addEventListener('beforeunload', (e) => {
    if (hasUnsavedChanges) {
      e.preventDefault();
      e.returnValue = '';
    }
  });

  hasUnsavedChanges = false;
});

function setupTagSelector(containerId, hiddenInputId, dropdownId) {
  const container = document.getElementById(containerId);
  const dropdown = document.getElementById(dropdownId);
  const hiddenInput = document.getElementById(hiddenInputId);
  if (!container || !dropdown || !hiddenInput) return;

  let selectedValues = [];
  if (hiddenInput.value) {
    try {
      selectedValues = JSON.parse(hiddenInput.value);
      renderTags();
    } catch(e) {}
  }

  container.addEventListener('click', (e) => {
    e.stopPropagation();
    dropdown.classList.toggle('show');
  });

  document.addEventListener('click', (e) => {
    if (!container.contains(e.target) && !dropdown.contains(e.target)) {
      dropdown.classList.remove('show');
    }
  });

  dropdown.querySelectorAll('.tag-option').forEach(opt => {
    opt.addEventListener('click', () => {
      const val = opt.dataset.value;
      if (!selectedValues.includes(val)) {
        selectedValues.push(val);
        renderTags();
        triggerChange();
      }
      dropdown.classList.remove('show');
    });
  });

  function renderTags() {
    container.innerHTML = '';
    if (selectedValues.length === 0) {
      container.textContent = 'اختر...';
      hiddenInput.value = '';
      return;
    }
    selectedValues.forEach(val => {
      const opt = Array.from(dropdown.querySelectorAll('.tag-option')).find(o => o.dataset.value === val);
      const name = opt ? opt.textContent : val;
      const badge = document.createElement('div');
      badge.className = 'tag-badge';
      const label = document.createElement('span');
      label.textContent = name;
      const x = document.createElement('span');
      x.className = 'remove-tag';
      x.textContent = '×';
      x.addEventListener('click', (e) => {
        e.stopPropagation();
        selectedValues = selectedValues.filter(v => v !== val);
        renderTags();
        triggerChange();
      });
      badge.append(label, x);
      container.appendChild(badge);
    });
    hiddenInput.value = JSON.stringify(selectedValues);
  }
}

let categoryCount = 1;
function addTicketCategory(rolesJSON, channelOptionsHTML) {
  categoryCount++;
  const container = document.getElementById('categoriesContainer');
  const div = document.createElement('div');
  div.className = 'settings-section-card';
  div.style.marginTop = '20px';
  div.innerHTML = `
    <div class="settings-section-header">
      <div class="settings-section-title"><span>📂</span> الفئة رقم ${categoryCount}</div>
      <button type="button" class="btn btn-secondary" style="padding: 4px 10px; font-size:12px; color:#ff6b6b;" onclick="this.parentElement.parentElement.remove(); triggerChange();">حذف الفئة</button>
    </div>
    <div class="form-group">
      <label>اسم الفئة *</label>
      <input type="text" class="form-control" name="cat_name_${categoryCount}" placeholder="أدخل اسم الفئة...">
    </div>
    <div class="form-group">
      <label>وصف التذكرة *</label>
      <textarea class="form-control" name="cat_desc_${categoryCount}" placeholder="أدخل وصفاً تفصيلياً..."></textarea>
    </div>
    <div class="form-group">
      <label>صورة التذكرة (Image URL)</label>
      <input type="url" class="form-control" name="cat_image_${categoryCount}" placeholder="https://...">
    </div>
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 15px;">
      <div class="form-group">
        <label>روم التذاكر *</label>
        <select class="form-control" name="cat_ticket_channel_${categoryCount}"><option value="">اختر الروم...</option>${channelOptionsHTML}</select>
      </div>
      <div class="form-group">
        <label>روم السجل *</label>
        <select class="form-control" name="cat_log_channel_${categoryCount}"><option value="">اختر روم السجل...</option>${channelOptionsHTML}</select>
      </div>
    </div>
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 15px;">
      <div class="form-group">
        <label>رتب المسؤولين *</label>
        <div class="tag-input-container" id="container_staff_${categoryCount}">اختر...</div>
        <input type="hidden" name="cat_staff_roles_${categoryCount}" id="input_staff_${categoryCount}">
        <div class="tag-select-dropdown" id="dropdown_staff_${categoryCount}">${rolesJSON}</div>
      </div>
      <div class="form-group">
        <label>نوع العرض *</label>
        <select class="form-control" name="cat_display_type_${categoryCount}">
          <option value="button">Button Primary</option>
          <option value="select">Select Menu</option>
        </select>
      </div>
    </div>
  `;
  container.appendChild(div);
  setTimeout(() => {
    setupTagSelector(`container_staff_${categoryCount}`, `input_staff_${categoryCount}`, `dropdown_staff_${categoryCount}`);
  }, 50);
  triggerChange();
}
</script>
</head>
<body>
<header class="nav">
  <div class="brand">
    <div class="logo">✦</div>
    <div><h2>Sky Universe</h2><small>DISCORD BOT CONTROL PANEL</small></div>
  </div>
  <div class="nav-right">{{ header_auth|safe }}</div>
</header>
{{ content|safe }}
<footer class="footer">
  <div>✦ SKY UNIVERSE · لوحة تحكم البوت الاحترافية ✦</div>
  <div class="footer-links">
    <span>تحتاج مساعدة؟ تواصل معنا فوراً:</span>
    <a href="https://discord.gg/HuH8TtmGA" target="_blank" rel="noopener noreferrer" class="btn btn-discord" style="padding: 8px 18px; font-size: 13px;">
      💬 دعم البوت (Discord)
    </a>
  </div>
</footer>
</body>
</html>
"""


# ======================= أدوات الحماية =======================
@app.after_request
def security_headers(resp):
    resp.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    )
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    resp.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if not LOCAL_DEV:
        resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    if "user" in session:
        resp.headers["Cache-Control"] = "no-store"
    return resp


def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(32)
    return session["csrf"]


@app.before_request
def csrf_protect():
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        if request.path.startswith("/api/bot/"):
            return
        expected = session.get("csrf")
        sent = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token", "")
        if not expected or not hmac.compare_digest(sent.encode(), expected.encode()):
            abort(403)


def guild_access(f):
    @wraps(f)
    def wrapper(guild_id, *args, **kwargs):
        if "user" not in session:
            return redirect("/login")
        if not GUILD_ID_RE.match(guild_id):
            abort(404)
        if guild_id not in session.get("guilds", {}):
            abort(403)
        return f(guild_id, *args, **kwargs)
    return wrapper


def options_html(items, prefix=""):
    return "".join(
        f'<option value="{escape(str(i["id"]))}">{prefix}{escape(str(i["name"]))}</option>'
        for i in items
    )


def tag_options_html(items):
    return "".join(
        f'<div class="tag-option" data-value="{escape(str(i["id"]))}">@{escape(str(i["name"]))}</div>'
        for i in items
    )


def page(title, content, header_auth=""):
    return render_template_string(
        STYLE, page_title=title, content=content, header_auth=header_auth
    )


def discord_get(path, token, token_type="Bearer"):
    try:
        return requests.get(
            f"{API_ENDPOINT}{path}",
            headers={"Authorization": f"{token_type} {token}"},
            timeout=15
        )
    except requests.RequestException:
        return None


# ======================= API البوت =======================
def bot_auth(f):
    @wraps(f)
    def w(*a, **kw):
        if not BOT_API_KEY:
            return jsonify({"error": "BOT_API_KEY not configured"}), 503
        sent = request.headers.get("X-API-Key", "")
        if not hmac.compare_digest(sent.encode(), BOT_API_KEY.encode()):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*a, **kw)
    return w


@app.route("/api/bot/settings", methods=["GET"])
@limiter.exempt
@bot_auth
def api_all_settings():
    with _db_lock:
        return jsonify({"rev": _STATE["rev"], "guilds": _STATE["guilds"]})


@app.route("/api/bot/settings/<guild_id>", methods=["GET"])
@limiter.exempt
@bot_auth
def api_guild_settings(guild_id):
    with _db_lock:
        return jsonify({"guild_id": guild_id, "settings": _STATE["guilds"].get(guild_id, {})})


@app.route("/api/bot/updates", methods=["GET"])
@limiter.exempt
@bot_auth
def api_updates():
    since = request.args.get("since", default=0, type=int)
    with _db_lock:
        return jsonify({
            "rev": _STATE["rev"],
            "updates": [u for u in _STATE["log"] if u["rev"] > since],
        })


# ======================= الصفحات العامة =======================
@app.route("/")
def home():
    user = session.get("user")
    if user:
        uid = escape(str(user.get("id", "")))
        username = escape(str(user.get("username", "Discord User")))
        avatar = user.get("avatar")
        avatar_url = f"https://cdn.discordapp.com/avatars/{uid}/{escape(str(avatar))}.png" if avatar else "https://cdn.discordapp.com/embed/avatars/0.png"
        header_auth = f"""
        <div class="user-pill"><img src="{avatar_url}" alt="Avatar"><span>{username}</span></div>
        <form method="POST" action="/logout" style="margin:0;">
          <input type="hidden" name="csrf_token" value="{csrf_token()}">
          <button type="submit" class="btn btn-secondary" style="padding: 8px 16px;">خروج</button>
        </form>
        """
        actions = '<a class="btn btn-primary" href="/dashboard">⚙️ لوحة التحكم</a><a class="btn btn-secondary" href="/invite">🤖 أضف البوت</a>'
    else:
        header_auth = '<a class="btn btn-secondary" href="/login">تسجيل الدخول ↗</a>'
        actions = '<a class="btn btn-primary" href="/login">🚀 تسجيل الدخول عبر Discord</a><a class="btn btn-secondary" href="/invite">🤖 دعوة البوت</a>'

    content = f"""
    <main>
      <section class="hero">
        <div>
          <div class="eyebrow"><span class="dot"></span> عالمك، إدارتك، تحكمك</div>
          <h1>ارتقِ بسيرفرك<br><span class="gradient-text">إلى عالم آخر.</span></h1>
          <p class="subtitle">مرحباً بك في Sky Universe، لوحة تحكم متطورة لإدارة سيرفرات ديسكورد.</p>
          <div class="actions">{actions}</div>
        </div>
      </section>
    </main>
    """
    return page("الرئيسية", content, header_auth)


@app.route("/invite")
def invite():
    return redirect(BOT_INVITE_URL)


@app.route("/login")
@limiter.limit("10 per minute")
def login():
    state = secrets.token_urlsafe(24)
    session["oauth_state"] = state
    params = urlencode({
        "client_id": CLIENT_ID, "redirect_uri": REDIRECT_URI,
        "response_type": "code", "scope": "identify guilds", "state": state,
    })
    return redirect(f"https://discord.com/oauth2/authorize?{params}")


@app.route("/callback")
@limiter.limit("10 per minute")
def callback():
    expected = session.pop("oauth_state", None)
    got = request.args.get("state", "")
    if not expected or not hmac.compare_digest(got.encode(), expected.encode()):
        return "طلب غير صالح.", 400
    code = request.args.get("code")
    if not code:
        return "لم يتم استلام كود التحقق.", 400

    try:
        r = requests.post(
            f"{API_ENDPOINT}/oauth2/token",
            data={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
                  "grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT_URI},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )
        if r.status_code != 200:
            return "فشل تسجيل الدخول.", 502
        access_token = r.json().get("access_token")

        user_res = discord_get("/users/@me", access_token)
        guilds_res = discord_get("/users/@me/guilds", access_token)
        if not user_res or not guilds_res:
            return "تعذر جلب البيانات.", 502

        u = user_res.json()
        admin_guilds = {
            g["id"]: {"name": g.get("name", ""), "icon": g.get("icon")}
            for g in guilds_res.json()
            if (int(g.get("permissions", 0)) & 0x8) == 0x8 or g.get("owner", False)
        }

        session.clear()
        session.permanent = True
        session["user"] = {"id": u.get("id"), "username": u.get("username"), "avatar": u.get("avatar")}
        session["guilds"] = admin_guilds
        session["csrf"] = secrets.token_urlsafe(32)
        return redirect("/")
    except Exception:
        return "حدث خطأ.", 502


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    bot_guilds = set()
    if BOT_TOKEN:
        bot_res = discord_get("/users/@me/guilds", BOT_TOKEN, "Bot")
        if bot_res and bot_res.status_code == 200:
            bot_guilds = {g["id"] for g in bot_res.json()}
    valid = {gid: g for gid, g in session.get("guilds", {}).items() if gid in bot_guilds}
    cards = []
    for gid, g in valid.items():
        name = escape(str(g.get("name") or "سيرفر"))
        icon = g.get("icon")
        icon_url = f"https://cdn.discordapp.com/icons/{gid}/{escape(str(icon))}.png" if icon else "https://cdn.discordapp.com/embed/avatars/0.png"
        cards.append(f'<article class="server-card"><img class="server-icon" src="{icon_url}"><h3>{name}</h3><div class="status">● البوت متصل</div><a class="btn btn-primary" href="/server/{gid}/settings">⚙️ إدارة السيرفر</a></article>')
    grid = f'<div class="server-grid">{"".join(cards)}</div>' if cards else '<div class="empty"><span>🌌</span>لا توجد سيرفرات مشتركة مع البوت وأنت مشرف فيها.</div>'
    return page("اختيار السيرفر", f'<main class="page"><div class="page-head"><h1>📂 سيرفراتك</h1></div>{grid}</main>')


# ======================= إدارة السيرفر والأقسام الكاملة =======================
def get_server_context(guild_id):
    channels, roles = [], []
    if BOT_TOKEN:
        ch_res = discord_get(f"/guilds/{guild_id}/channels", BOT_TOKEN, "Bot")
        if ch_res and ch_res.status_code == 200:
            channels = [c for c in ch_res.json() if c.get("type") == 0]
        role_res = discord_get(f"/guilds/{guild_id}/roles", BOT_TOKEN, "Bot")
        if role_res and role_res.status_code == 200:
            roles = role_res.json()
    if not roles:
        roles = [{"id": "members", "name": "MEMBERS"}]
    return session["guilds"][guild_id], channels, roles


def parse_form():
    data = {}
    for k in request.form.keys():
        if k == "csrf_token":
            continue
        if not KEY_RE.match(k):
            abort(400)
        vals = request.form.getlist(k)
        data[k] = vals[0] if len(vals) == 1 else vals
    return data


def validate_settings(guild_id, data):
    _, channels, roles = get_server_context(guild_id)
    for k, v in data.items():
        vals = v if isinstance(v, list) else [v]
        for item in vals:
            if len(str(item)) > 2000:
                abort(400)


def render_server_page(guild_id, active_tab, tab_content_html, page_key=None):
    page_key = page_key or active_tab
    if request.method == "POST":
        data = parse_form()
        validate_settings(guild_id, data)
        changed = commit_settings(guild_id, page_key, data)
        return redirect(f"{request.path}?saved={'1' if changed else '0'}")

    target_guild = session["guilds"][guild_id]
    guild_name = escape(str(target_guild.get("name", "السيرفر")))
    icon = target_guild.get("icon")
    icon_url = f"https://cdn.discordapp.com/icons/{guild_id}/{escape(str(icon))}.png" if icon else "https://cdn.discordapp.com/embed/avatars/0.png"

    with _db_lock:
        saved_page = _STATE["guilds"].get(guild_id, {}).get(page_key)
    saved_json = (json.dumps(saved_page, ensure_ascii=False)
                  .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"))

    saved = request.args.get("saved")
    notice = ""
    box = "padding:12px 18px; border-radius:12px; margin-bottom:20px; font-weight:700; font-size:14px;"
    if saved == "1":
        notice = f'<div style="{box} background:rgba(46,213,115,.12); border:1px solid rgba(46,213,115,.4);">✅ تم الحفظ بنجاح، وتطبيق التعديلات قيد التنفيذ.</div>'
    elif saved == "0":
        notice = f'<div style="{box} background:rgba(100,202,255,.1); border:1px solid rgba(100,202,255,.3);">ℹ️ لا توجد تغييرات جديدة للحفظ.</div>'

    sidebar_html = f"""
    <aside class="sidebar">
      <div class="sidebar-header"><img class="sidebar-icon" src="{icon_url}"><h3>{guild_name}</h3></div>
      <div class="menu-list">
        <a class="menu-item {'active' if active_tab=='settings' else ''}" href="/server/{guild_id}/settings"><span>⚙️</span> الأساسيات</a>
        <a class="menu-item {'active' if active_tab=='welcome' else ''}" href="/server/{guild_id}/welcome"><span>👋</span> نظام الترحيب</a>
        <a class="menu-item {'active' if active_tab=='security' else ''}" href="/server/{guild_id}/security"><span>🛡️</span> الحماية والأمان</a>
        <a class="menu-item {'active' if active_tab=='commands' else ''}" href="/server/{guild_id}/commands"><span>🤖</span> أوامر الإشراف</a>
        <a class="menu-item {'active' if active_tab=='logs' else ''}" href="/server/{guild_id}/logs"><span>📊</span> السجلات (Logs)</a>
        <a class="menu-item {'active' if active_tab=='tickets' else ''}" href="/server/{guild_id}/tickets"><span>🎫</span> نظام التذاكر</a>
      </div>
      <div style="margin-top: auto; padding-top: 15px; border-top: 1px solid var(--line);">
        <a class="btn btn-secondary" style="width: 100%; text-align: center;" href="/dashboard">← عودة للسيرفرات</a>
      </div>
    </aside>
    """

    floating_bar = f"""
    <script>window.COMMITTED_SETTINGS = {saved_json};</script>
    <div id="saveBar" class="floating-save-bar">
      <div class="save-bar-info"><span class="save-dot"></span><span>تغييرات غير محفوظة!</span></div>
      <div style="display:flex; gap:10px;">
        <button type="submit" form="mainForm" class="btn btn-green" style="padding: 8px 22px;">حفظ</button>
        <button type="button" onclick="revertToLastSaved()" class="btn btn-red" style="padding: 8px 20px;">إلغاء</button>
      </div>
    </div>
    """

    return page(f"إدارة {guild_name}", f'<div class="dashboard-layout">{sidebar_html}<main class="content-panel"><form id="mainForm" method="POST"><input type="hidden" name="csrf_token" value="{csrf_token()}">{notice}{tab_content_html}</form></main></div>{floating_bar}')


@app.route("/server/<guild_id>/settings", methods=["GET", "POST"])
@guild_access
def s_settings(guild_id):
    _, _, roles = get_server_context(guild_id)
    role_options_str = tag_options_html(roles)
    html = f"""
    <div class="settings-section-card">
      <div class="settings-section-header"><div class="settings-section-title"><span>⚙️</span> الأساسيات</div></div>
      <div class="form-group">
        <label>لغة البوت</label>
        <select class="form-control" name="bot_lang"><option value="ar">🇸🇦 العربية</option><option value="en">🇺🇸 English</option></select>
      </div>
    </div>
    <div class="settings-section-card">
      <div class="settings-section-header"><div class="settings-section-title"><span>🤖</span> الرتب التلقائية</div></div>
      <div class="form-group">
        <label>👥 رتب الأعضاء الجدد</label>
        <div class="tag-input-container" id="container_users">اختر الرتب...</div>
        <input type="hidden" name="auto_roles_users" id="input_users">
        <div class="tag-select-dropdown" id="dropdown_users">{role_options_str}</div>
      </div>
    </div>
    <script>
      window.addEventListener('DOMContentLoaded', () => {{
        setupTagSelector('container_users', 'input_users', 'dropdown_users');
      }});
    </script>
    """
    return render_server_page(guild_id, "settings", html)


@app.route("/server/<guild_id>/welcome", methods=["GET", "POST"])
@guild_access
def s_welcome(guild_id):
    _, channels, _ = get_server_context(guild_id)
    ch_options = options_html(channels, "#")
    html = f"""
    <div class="page-head"><div><h1>👋 نظام الترحيب</h1><p>تخصيص رسائل الترحيب بالأعضاء.</p></div></div>
    <div class="settings-section-card">
      <div class="settings-section-header">
        <div class="settings-section-title"><span>👋</span> رسالة الترحيب</div>
        <label class="switch"><input type="checkbox" name="welcome_enabled" checked><span class="slider"></span></label>
      </div>
      <div class="form-group">
        <label>نص الرسالة</label>
        <textarea class="form-control" name="welcome_msg" rows="3">مرحباً بك {{user}} في سيرفرنا! 🎉</textarea>
      </div>
      <div class="form-group">
        <label>قناة الترحيب</label>
        <select class="form-control" name="welcome_channel"><option value="">اختر القناة...</option>{ch_options}</select>
      </div>
    </div>
    """
    return render_server_page(guild_id, "welcome", html)


@app.route("/server/<guild_id>/security", methods=["GET", "POST"])
@guild_access
def s_security(guild_id):
    sec_items = [
        ("كشف الكلمات السيئة", "bad_words", "فلترة وحظر الكلمات النابية والسيئة تلقائياً"),
        ("كشف السبام", "spam", "منع التكرار المفرط وإزعاج الأعضاء"),
        ("فلترة الروابط", "links", "التحكم في الروابط المسموحة والمحظورة"),
        ("سبام المنشن", "mention_spam", "حماية الشات من الإشارات المتكررة")
    ]
    list_html = "".join([f"""
    <div class="security-card">
      <div class="security-info"><h3>{title}</h3><p>{desc}</p></div>
      <div style="display:flex; align-items:center; gap:14px;">
        <label class="switch"><input type="checkbox" name="sec_{key}" checked><span class="slider"></span></label>
      </div>
    </div>""" for title, key, desc in sec_items])
    return render_server_page(guild_id, "security", f'<div class="page-head"><h1>🛡️ الحماية والأمان</h1></div>{list_html}')


@app.route("/server/<guild_id>/commands", methods=["GET", "POST"])
@guild_access
def s_commands(guild_id):
    cmds = [
        ("ban", "حظر عضو من السيرفر"), ("unban", "إلغاء حظر عضو"), ("clear", "مسح الرسائل"),
        ("hide", "إخفاء قناة معينة"), ("show", "إظهار قناة معينة"), ("lock", "قفل القناة"),
        ("unlock", "فتح القناة"), ("timeout", "إسكات عضو مؤقتاً"), ("warn", "تحذير عضو")
    ]
    cards_html = "".join([f"""
    <div class="card-item">
      <div class="card-header">
        <div class="card-title">/{cmd}</div>
        <label class="switch"><input type="checkbox" name="cmd_{cmd}" checked><span class="slider"></span></label>
      </div>
      <div style="font-size: 13px; color: var(--muted); text-align: right;">{desc}</div>
    </div>""" for cmd, desc in cmds])
    return render_server_page(guild_id, "commands", f'<div class="page-head"><h1>🤖 أوامر الإشراف</h1></div><div class="cards-grid-3">{cards_html}</div>')


@app.route("/server/<guild_id>/logs", methods=["GET", "POST"])
@guild_access
def s_logs(guild_id):
    _, channels, _ = get_server_context(guild_id)
    ch_options = options_html(channels, "#")
    
    logs_list = [
        ("حظر عضو", "log_ban"), ("طرد عضو", "log_kick"), ("انضمام عضو", "log_join"),
        ("مغادرة عضو", "log_leave"), ("حذف رسالة", "log_msg_delete"), ("تعديل رسالة", "log_msg_edit"),
        ("إنشاء قناة", "log_channel_create"), ("حذف قناة", "log_channel_delete")
    ]

    cards_html = "".join([f"""
    <div class="card-item">
      <div class="card-header">
        <div class="card-title"><span>📊</span> {title}</div>
        <label class="switch"><input type="checkbox" name="{prefix}_enabled" checked><span class="slider"></span></label>
      </div>
      <div style="display: flex; flex-direction: column; gap: 6px;">
        <label style="color:var(--muted); font-size:12px; text-align:right;">قناة السجل</label>
        <select class="form-control" name="{prefix}_channel" style="padding: 10px 14px; font-size: 13px;"><option value="">اختر القناة...</option>{ch_options}</select>
      </div>
    </div>""" for title, prefix in logs_list])

    return render_server_page(guild_id, "logs", f'<div class="page-head"><h1>📊 السجلات (Logs)</h1></div><div class="cards-grid-3">{cards_html}</div>')


@app.route("/server/<guild_id>/tickets", methods=["GET", "POST"])
@guild_access
def s_tickets(guild_id):
    _, channels, roles = get_server_context(guild_id)
    ch_options = options_html(channels, "#")
    role_options_str = tag_options_html(roles)
    roles_attr = escape(role_options_str)
    chans_attr = escape(ch_options)

    html = f"""
    <div class="page-head" style="margin-bottom:25px;">
      <div><h1>🎫 نظام التذاكر المتقدم</h1><p>إدارة فئات التذاكر وتخصيص رتب المسؤولين.</p></div>
    </div>

    <div id="categoriesContainer">
      <div class="settings-section-card">
        <div class="settings-section-header">
          <div class="settings-section-title"><span>📂</span> الفئة رقم 1</div>
        </div>
        <div class="form-group">
          <label>اسم الفئة *</label>
          <input type="text" class="form-control" name="cat_name_1" placeholder="مثال: الدعم الفني">
        </div>
        <div class="form-group">
          <label>وصف التذكرة *</label>
          <textarea class="form-control" name="cat_desc_1" placeholder="وصف يظهر للمستخدم..."></textarea>
        </div>
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 15px;">
          <div class="form-group">
            <label>روم التذاكر *</label>
            <select class="form-control" name="cat_ticket_channel_1"><option value="">اختر الروم...</option>{ch_options}</select>
          </div>
          <div class="form-group">
            <label>روم السجل *</label>
            <select class="form-control" name="cat_log_channel_1"><option value="">اختر روم السجل...</option>{ch_options}</select>
          </div>
        </div>
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 15px;">
          <div class="form-group">
            <label>رتب المسؤولين *</label>
            <div class="tag-input-container" id="container_staff_1">اختر...</div>
            <input type="hidden" name="cat_staff_roles_1" id="input_staff_1">
            <div class="tag-select-dropdown" id="dropdown_staff_1">{role_options_str}</div>
          </div>
          <div class="form-group">
            <label>نوع العرض *</label>
            <select class="form-control" name="cat_display_type_1">
              <option value="button">Button Primary</option>
              <option value="select">Select Menu</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <div style="margin-bottom: 25px;">
      <button type="button" class="btn btn-secondary" style="width: 100%; border: 2px dashed var(--blue); padding: 16px;"
        data-roles="{roles_attr}" data-channels="{chans_attr}"
        onclick="addTicketCategory(this.dataset.roles, this.dataset.channels)">
        + إضافة فئة جديدة
      </button>
    </div>

    <script>
      window.addEventListener('DOMContentLoaded', () => {{
        setupTagSelector('container_staff_1', 'input_staff_1', 'dropdown_staff_1');
      }});
    </script>
    """
    return render_server_page(guild_id, "tickets", html)


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="127.0.0.1" if LOCAL_DEV else "0.0.0.0", port=port, debug=False)
