import os
import re
import hmac
import secrets
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

SECRET = os.environ.get("SESSION_SECRET", "vZRj3Y11P3hh2CoeIk0VdWwH88icJOQK")
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
SEC_KEYS = {"bad_words", "spam", "links", "mention_spam"}
CMD_NAMES = {
    "ban", "unban", "clear", "hide", "show", "lock", "unlock", "move", "role",
    "setnick", "timeout", "untimeout", "vkick", "warn", "unwarn", "warns", "vmute"
}

SERVER_SETTINGS_DB = {}
PENDING_SETTINGS_DB = {}

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
.btn-gold { color: #06101f; background: var(--gold); font-weight: 900; }
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

.hero {
  width: min(1350px, 95%); margin: auto; padding: 40px 0 20px;
  display: grid; grid-template-columns: 0.85fr 1.15fr;
  align-items: center; gap: 20px; min-height: 600px;
}

.eyebrow {
  display: inline-flex; align-items: center; gap: 9px; padding: 7px 14px;
  color: #b6dfff; border: 1px solid #67bfff35; background: #57baff0c;
  border-radius: 50px; font-size: 13px; font-weight: 800; backdrop-filter: blur(8px);
}
.dot { width: 8px; height: 8px; background: #72e5ba; border-radius: 50%; box-shadow: 0 0 10px #72e5ba; }

h1 {
  font-size: clamp(32px, 4vw, 52px); line-height: 1.35;
  letter-spacing: -.8px; margin: 18px 0 12px; font-weight: 900;
}
.gradient-text {
  background: linear-gradient(100deg, #71ddff, #9b9aff 60%, #d6b5ff);
  color: transparent; background-clip: text; -webkit-background-clip: text;
}
.subtitle { color: var(--muted); font-size: 15px; line-height: 2.0; max-width: 480px; }
.actions { display: flex; flex-wrap: wrap; gap: 14px; margin-top: 22px; }

/* تصميم الكوكب والمدار */
.space-art {
  height: 580px; position: relative; display: grid; place-items: center;
}
.planet-system {
  position: relative; width: 520px; height: 520px; display: grid; place-items: center;
}
.planet-core {
  width: 150px; height: 150px; border-radius: 50%;
  background:
    radial-gradient(circle at 30% 25%, #c2edff, transparent 15%),
    radial-gradient(circle at 35% 30%, #7bd8ff, #526de2 45%, #23154f 80%, #0a0d20);
  box-shadow: inset -22px -16px 36px rgba(3, 7, 24, 0.9), 0 0 55px rgba(99, 125, 255, 0.45);
  position: relative; z-index: 2;
}
.planet-core:after {
  content: ""; position: absolute; width: 200px; height: 36px;
  border: 6px solid rgba(155, 184, 255, 0.7); border-left-color: #c2a9ff;
  border-right-color: #6ad8ff; border-radius: 50%; top: 57px; left: -25px;
  transform: rotate(-22deg); box-shadow: 0 0 22px rgba(109, 175, 255, 0.4);
}
@keyframes mainOrbit {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
@keyframes fixText {
  from { transform: rotate(360deg); }
  to { transform: rotate(0deg); }
}
.orbit-container {
  position: absolute; inset: 0;
  animation: mainOrbit 45s linear infinite;
  pointer-events: none;
}
.orbit-container:hover { animation-play-state: paused; }
.orbit-container::before {
  content: ""; position: absolute; inset: 50px; border-radius: 50%;
  border: 1px dashed rgba(120, 170, 255, 0.15); pointer-events: none;
}
.orbit-node {
  position: absolute; top: 50%; left: 50%; width: 130px; height: 75px;
  margin-top: -37.5px; margin-left: -65px; pointer-events: auto;
}
.orbit-card {
  width: 100%; height: 100%; padding: 8px 10px; border: 1px solid var(--line);
  border-radius: 12px; background: rgba(14, 23, 48, 0.92); backdrop-filter: blur(14px);
  box-shadow: 0 6px 20px rgba(0,0,0,0.4); font-size: 11px; text-align: center;
  display: flex; flex-direction: column; justify-content: center; align-items: center;
  animation: fixText 45s linear infinite;
  transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s;
}
.orbit-card:hover {
  border-color: var(--blue); transform: scale(1.12);
  box-shadow: 0 10px 30px rgba(100, 202, 255, 0.3); z-index: 50;
}
.orbit-card .icon { font-size: 15px; line-height: 1; margin-bottom: 3px; display: block; }
.orbit-card strong { display: block; font-size: 11px; color: #fff; margin-bottom: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 110px; }
.orbit-card p { margin: 0; color: var(--muted); font-size: 9.5px; line-height: 1.25; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

.node-1  { transform: rotate(0deg) translate(210px) rotate(0deg); }
.node-2  { transform: rotate(36deg) translate(210px) rotate(-36deg); }
.node-3  { transform: rotate(72deg) translate(210px) rotate(-72deg); }
.node-4  { transform: rotate(108deg) translate(210px) rotate(-108deg); }
.node-5  { transform: rotate(144deg) translate(210px) rotate(-144deg); }
.node-6  { transform: rotate(180deg) translate(210px) rotate(-180deg); }
.node-7  { transform: rotate(216deg) translate(210px) rotate(-216deg); }
.node-8  { transform: rotate(252deg) translate(210px) rotate(-252deg); }
.node-9  { transform: rotate(288deg) translate(210px) rotate(-288deg); }
.node-10 { transform: rotate(324deg) translate(210px) rotate(-324deg); }

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

/* تعديل شكل فقاعة التاغ ليصير الـ X على اليسار والنص على اليمين */
.tag-input-container {
  background: rgba(6, 10, 23, 0.85); border: 1px solid var(--line); border-radius: 12px;
  padding: 8px 12px; min-height: 50px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; cursor: pointer;
}
.tag-badge {
  background: linear-gradient(115deg, #64caff, #9b8cff); color: #06101f;
  padding: 4px 12px; border-radius: 8px; font-size: 12px; font-weight: 800;
  display: inline-flex; align-items: center; gap: 8px; flex-direction: row-reverse;
}
.tag-badge .remove-tag {
  cursor: pointer; font-size: 14px; font-weight: 900; color: #06101f;
}
.tag-select-dropdown {
  width: 100%; margin-top: 6px; background: rgba(12, 19, 39, 0.95); border: 1px solid var(--line);
  border-radius: 10px; padding: 8px; max-height: 150px; overflow-y: auto; display: none; position: absolute; z-index: 100;
}
.tag-select-dropdown.show { display: block; }
.tag-option {
  padding: 8px 12px; border-radius: 6px; cursor: pointer; font-size: 13px; color: var(--text); text-align: right;
}
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

function resetFormValues() {
  hasUnsavedChanges = false;
  const bar = document.getElementById('saveBar');
  if (bar) bar.classList.remove('visible');
  const form = document.getElementById('mainForm');
  if (form) form.reset();
}

window.addEventListener('DOMContentLoaded', () => {
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

  // منع المغادرة إذا كان هناك تغييرات غير محفوظة
  window.addEventListener('beforeunload', (e) => {
    if (hasUnsavedChanges) {
      e.preventDefault();
      e.returnValue = '';
    }
  });

  // منع الضغط على الروابط الجانبية لو فيه تعديلات غير محفوظة
  document.querySelectorAll('.sidebar a, .nav a').forEach(link => {
    link.addEventListener('click', (e) => {
      if (hasUnsavedChanges) {
        if (!confirm('تنبيه: لديك تعديلات غير محفوظة! هل أنت متأكد من مغادرة الصفحة دون حفظ؟')) {
          e.preventDefault();
        }
      }
    });
  });
});

function setupTagSelector(containerId, hiddenInputId, dropdownId) {
  const container = document.getElementById(containerId);
  const dropdown = document.getElementById(dropdownId);
  const hiddenInput = document.getElementById(hiddenInputId);
  if (!container || !dropdown || !hiddenInput) return;

  let selectedValues = [];

  container.addEventListener('click', () => {
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
      const name = opt.textContent;
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
    selectedValues.forEach(val => {
      const opt = dropdown.querySelector(`[data-value="${val}"]`);
      const name = opt ? opt.textContent : val;
      const badge = document.createElement('div');
      badge.className = 'tag-badge';
      badge.innerHTML = `${name} <span class="remove-tag">&times;</span>`;
      badge.querySelector('.remove-tag').addEventListener('click', (e) => {
        e.stopPropagation();
        selectedValues = selectedValues.filter(v => v !== val);
        renderTags();
        triggerChange();
      });
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
      <textarea class="form-control" name="cat_desc_${categoryCount}" placeholder="أدخل وصفاً تفصيلياً يظهر للمستخدمين عند فتح التذكرة..."></textarea>
    </div>
    <div class="form-group">
      <label>رابط أو صورة التذكرة (Image URL)</label>
      <input type="url" class="form-control" name="cat_image_${categoryCount}" placeholder="https://...">
    </div>
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 15px;">
      <div class="form-group">
        <label>روم التذاكر *</label>
        <select class="form-control" name="cat_ticket_channel_${categoryCount}">
          <option value="">اختر الروم...</option>
          ${channelOptionsHTML}
        </select>
      </div>
      <div class="form-group">
        <label>روم السجل (Log Channel) *</label>
        <select class="form-control" name="cat_log_channel_${categoryCount}">
          <option value="">اختر روم السجل...</option>
          ${channelOptionsHTML}
        </select>
      </div>
    </div>
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 15px;">
      <div class="form-group">
        <label>رتب المسؤولين *</label>
        <div class="tag-input-container" id="container_staff_${categoryCount}">اختر الرتب...</div>
        <input type="hidden" name="cat_staff_roles_${categoryCount}" id="input_staff_${categoryCount}">
        <div class="tag-select-dropdown" id="dropdown_staff_${categoryCount}">
          ${rolesJSON}
        </div>
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
        if not expected or not hmac.compare_digest(sent, expected):
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


@app.route("/api/bot/settings/<guild_id>", methods=["GET"])
def api_get_guild_settings(guild_id):
    auth_header = request.headers.get("Authorization", "")
    if BOT_TOKEN and auth_header != f"Bot {BOT_TOKEN}":
        return jsonify({"error": "Unauthorized"}), 401
    settings = SERVER_SETTINGS_DB.get(guild_id, {})
    return jsonify({"guild_id": guild_id, "settings": settings}), 200


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
          <p class="subtitle">
            مرحباً بك في Sky Universe، لوحة تحكم متطورة بتصميم فضي ومجرات فريد، تتيح لك إدارة سيرفر البوت واختيار الرتب المتعددة وإعدادات التذاكر والترحيب بكل احترافية.
          </p>
          <div class="actions">{actions}</div>
        </div>
        <div class="space-art">
          <div class="planet-system">
            <div class="planet-core"></div>
            <div class="orbit-container">
              <div class="orbit-node node-1">
                <div class="orbit-card">
                  <span class="icon">👋</span>
                  <strong>نظام الترحيب</strong>
                  <p>استقبال الأعضاء الجدد</p>
                </div>
              </div>
              <div class="orbit-node node-2">
                <div class="orbit-card">
                  <span class="icon">🛡️</span>
                  <strong>الحماية المتقدمة</strong>
                  <p>مكافحة السبام والروابط</p>
                </div>
              </div>
              <div class="orbit-node node-3">
                <div class="orbit-card">
                  <span class="icon">🎫</span>
                  <strong>نظام التذاكر</strong>
                  <p>تنظيم الدعم والشراء</p>
                </div>
              </div>
              <div class="orbit-node node-4">
                <div class="orbit-card">
                  <span class="icon">📂</span>
                  <strong>إدارة السيرفر</strong>
                  <p>إعدادات القنوات والرتب</p>
                </div>
              </div>
              <div class="orbit-node node-5">
                <div class="orbit-card">
                  <span class="icon">📊</span>
                  <strong>الإحصائيات</strong>
                  <p>عرض تفاصيل السيرفر</p>
                </div>
              </div>
              <div class="orbit-node node-6">
                <div class="orbit-card">
                  <span class="icon">⚡</span>
                  <strong>التحكم الذكي</strong>
                  <p>إعدادات البوت والخصائص</p>
                </div>
              </div>
              <div class="orbit-node node-7">
                <div class="orbit-card">
                  <span class="icon">👑</span>
                  <strong>إدارة الرتب</strong>
                  <p>صلاحيات الإشراف</p>
                </div>
              </div>
              <div class="orbit-node node-8">
                <div class="orbit-card">
                  <span class="icon">🌐</span>
                  <strong>إعدادات اللغة</strong>
                  <p>دعم العربية والإنجليزية</p>
                </div>
              </div>
              <div class="orbit-node node-9">
                <div class="orbit-card">
                  <span class="icon">🎨</span>
                  <strong>تخصيص البطاقات</strong>
                  <p>تعديل رسائل ومظهر البوت</p>
                </div>
              </div>
              <div class="orbit-node node-10" style="cursor: pointer;" onclick="window.open('https://discord.gg/HuH8TtmGA', '_blank', 'noopener')">
                <div class="orbit-card">
                  <span class="icon">💬</span>
                  <strong>الدعم الفني</strong>
                  <p>مجتمع الدعم عبر Discord</p>
                </div>
              </div>
            </div>
          </div>
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
    params = urlencode({"client_id": CLIENT_ID, "redirect_uri": REDIRECT_URI, "response_type": "code", "scope": "identify guilds", "state": state})
    return redirect(f"https://discord.com/oauth2/authorize?{params}")


@app.route("/callback")
@limiter.limit("10 per minute")
def callback():
    expected = session.pop("oauth_state", None)
    got = request.args.get("state", "")
    if not expected or not hmac.compare_digest(got, expected):
        return "طلب غير صالح (state).", 400
    code = request.args.get("code")
    if not code:
        return "لم يتم استلام كود التحقق.", 400

    try:
        r = requests.post(f"{API_ENDPOINT}/oauth2/token", data={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT_URI}, headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=15)
        if r.status_code != 200:
            return "فشل تسجيل الدخول.", 502
        access_token = r.json().get("access_token")
        user_res = discord_get("/users/@me", access_token)
        guilds_res = discord_get("/users/@me/guilds", access_token)
        u = user_res.json()
        admin_guilds = {g["id"]: {"name": g.get("name", ""), "icon": g.get("icon")} for g in guilds_res.json() if (int(g.get("permissions", 0)) & 0x8) == 0x8 or g.get("owner", False)}
        session.clear()
        session.permanent = True
        session["user"] = {"id": u.get("id"), "username": u.get("username"), "avatar": u.get("avatar")}
        session["guilds"] = admin_guilds
        session["csrf"] = secrets.token_urlsafe(32)
        return redirect("/")
    except:
        return "تعذر الاتصال بـ Discord.", 502


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
    grid = f'<div class="server-grid">{"".join(cards)}</div>' if cards else '<div class="empty"><span>🌌</span>ما لقينا سيرفرات فيها البوت وأنت أدمن فيها.</div>'
    return page("اختيار السيرفر", f'<main class="page"><div class="page-head"><h1>📂 سيرفراتك</h1></div>{grid}</main>')


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


def handle_form_post(guild_id):
    if request.method == "POST":
        form_data = request.form.to_dict(flat=False)
        # حفظ البيانات مؤقتاً في قاعدة بيانات الطلبات المعلقة فقط، ولا ترسل للبوت إلا عند الضغط المباشر على حفظ
        PENDING_SETTINGS_DB[guild_id] = form_data
        if "save_action" in form_data or request.form.get("action_type") == "save":
            SERVER_SETTINGS_DB[guild_id] = form_data


def render_server_page(guild_id, active_tab, tab_content_html):
    if request.method == "POST":
        # الاعتماد الفعلي يتم فقط عند إرسال النموذج وزر الحفظ
        handle_form_post(guild_id)
    target_guild = session["guilds"][guild_id]
    guild_name = escape(str(target_guild.get("name", "السيرفر")))
    icon = target_guild.get("icon")
    icon_url = f"https://cdn.discordapp.com/icons/{guild_id}/{escape(str(icon))}.png" if icon else "https://cdn.discordapp.com/embed/avatars/0.png"

    sidebar_html = f"""
    <aside class="sidebar">
      <div class="sidebar-header"><img class="sidebar-icon" src="{icon_url}"><h3>{guild_name}</h3></div>
      <div class="menu-list">
        <a class="menu-item {'active' if active_tab=='settings' else ''}" href="/server/{guild_id}/settings"><span>⚙️</span> الأساسيات</a>
        <a class="menu-item {'active' if active_tab=='welcome' else ''}" href="/server/{guild_id}/welcome"><span>👋</span> نظام الترحيب</a>
        <a class="menu-item {'active' if active_tab=='security' else ''}" href="/server/{guild_id}/security"><span>🛡️</span> الحماية والأمان</a>
        <a class="menu-item {'active' if active_tab=='commands' else ''}" href="/server/{guild_id}/commands"><span>🤖</span> أوامر الإشراف</a>
        <a class="menu-item {'active' if active_tab=='logs' else ''}" href="/server/{guild_id}/logs"><span>📊</span> السجلات</a>
        <a class="menu-item {'active' if active_tab=='tickets' else ''}" href="/server/{guild_id}/tickets"><span>🎫</span> نظام التذاكر</a>
      </div>
      <div style="margin-top: auto; padding-top: 15px; border-top: 1px solid var(--line);">
        <a class="btn btn-secondary" style="width: 100%; text-align: center;" href="/dashboard">← عودة</a>
      </div>
    </aside>
    """

    floating_bar = """
    <div id="saveBar" class="floating-save-bar">
      <div class="save-bar-info"><span class="save-dot"></span><span>تم اكتشاف تغييرات غير محفوظة!</span></div>
      <div style="display:flex; gap:10px;">
        <button type="submit" name="action_type" value="save" form="mainForm" class="btn btn-green" style="padding: 8px 22px;">حفظ</button>
        <button type="button" form="mainForm" onclick="resetFormValues()" class="btn btn-red" style="padding: 8px 20px;">إلغاء</button>
      </div>
    </div>
    """

    return page(f"إدارة {guild_name}", f'<div class="dashboard-layout">{sidebar_html}<main class="content-panel"><form id="mainForm" method="POST" enctype="multipart/form-data"><input type="hidden" name="csrf_token" value="{csrf_token()}">{tab_content_html}</form></main></div>{floating_bar}')


@app.route("/server/<guild_id>/settings", methods=["GET", "POST"])
@guild_access
def s_settings(guild_id):
    _, _, roles = get_server_context(guild_id)
    role_options_str = tag_options_html(roles)

    html = f"""
    <div class="settings-section-card">
      <div class="settings-section-header">
        <div class="settings-section-title"><span>⚙️</span> الأساسيات</div>
      </div>
      <div class="form-group">
        <label>لغة البوت</label>
        <select class="form-control" name="bot_lang"><option value="ar">🇸🇦 العربية</option><option value="en">🇺🇸 English</option></select>
      </div>
    </div>

    <div class="settings-section-card">
      <div class="settings-section-header">
        <div class="settings-section-title"><span>🤖</span> الرتب التلقائية</div>
      </div>
      <div class="form-group">
        <label>👥 رتب المستخدمين</label>
        <div class="tag-input-container" id="container_users">اختر الرتب...</div>
        <input type="hidden" name="auto_roles_users" id="input_users">
        <div class="tag-select-dropdown" id="dropdown_users">{role_options_str}</div>
      </div>
      <div class="form-group">
        <label>🤖 رتب البوتات</label>
        <div class="tag-input-container" id="container_bots">اختر الرتب...</div>
        <input type="hidden" name="auto_roles_bots" id="input_bots">
        <div class="tag-select-dropdown" id="dropdown_bots">{role_options_str}</div>
      </div>
    </div>
    <script>
      window.addEventListener('DOMContentLoaded', () => {{
        setupTagSelector('container_users', 'input_users', 'dropdown_users');
        setupTagSelector('container_bots', 'input_bots', 'dropdown_bots');
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
    <div class="page-head" style="margin-bottom:25px;">
      <div><h1>👋 نظام الترحيب</h1><p>قم بتكوين رسائل الترحيب المخصصة للأعضاء المنضمين إلى سيرفرك.</p></div>
    </div>
    <div class="settings-section-card">
      <div class="settings-section-header">
        <div class="settings-section-title"><span>👋</span> رسالة الترحيب</div>
        <label class="switch"><input type="checkbox" name="welcome_enabled" checked><span class="slider"></span></label>
      </div>
      <div class="form-group">
        <label>نص رسالة الترحيب</label>
        <textarea class="form-control" name="welcome_msg" rows="4" placeholder="مرحباً بك {{user}} في سيرفرنا!">مرحباً بك {{user}} في خادمنا الرائع! 🎉</textarea>
        <div class="field-desc" style="margin-top:6px;">
          ✨ الاختصارات المتاحة: <code>{{user}}</code> للإشارة إلى العضو، <code>{{username}}</code> لاسم العضو، <code>{{server}}</code> لاسم السيرفر، <code>{{membercount}}</code> لعدد الأعضاء.
        </div>
      </div>
      <div class="form-group">
        <label>طريقة التوصيل</label>
        <div style="display: flex; gap: 20px; align-items: center; margin-top: 8px;">
          <label style="display: flex; align-items: center; gap: 8px; cursor: pointer; font-size: 14px; font-weight: normal;">
            <input type="radio" name="welcome_delivery" value="dm"> إرسال كرسالة خاصة (DM)
          </label>
          <label style="display: flex; align-items: center; gap: 8px; cursor: pointer; font-size: 14px; font-weight: normal;">
            <input type="radio" name="welcome_delivery" value="channel" checked> إرسال إلى روم
          </label>
        </div>
      </div>
      <div class="form-group">
        <label>اختر الروم</label>
        <select class="form-control" name="welcome_channel">
          <option value="">اختر الرومات...</option>
          {ch_options}
        </select>
      </div>
    </div>
    """
    return render_server_page(guild_id, "welcome", html)


@app.route("/server/<guild_id>/security", methods=["GET", "POST"])
@guild_access
def s_security(guild_id):
    sec_items = [
        ("كشف الكلمات السيئة", "bad_words", "كشف ومعالجة الرسائل التي تحتوي على كلمات سيئة"),
        ("كشف السبام", "spam", "تحديد ومعالجة رسائل السبام"),
        ("فلترة الروابط", "links", "فلترة وإدارة الرسائل التي تحتوي على روابط"),
        ("سبام المنشن", "mention_spam", "كشف المنشنات المفرطة للمستخدمين")
    ]
    list_html = "".join([f"""
    <div class="security-card">
      <div class="security-info"><h3>{title}</h3><p>{desc}</p></div>
      <div style="display:flex; align-items:center; gap:14px;">
        <a class="btn-edit" href="/server/{guild_id}/security-edit/{key}">إعدادات متقدمة</a>
        <label class="switch"><input type="checkbox" name="sec_{key}" checked><span class="slider"></span></label>
      </div>
    </div>""" for title, key, desc in sec_items])
    return render_server_page(guild_id, "security", f'<div class="page-head"><h1>🛡️ الحماية والأمان</h1></div>{list_html}')


@app.route("/server/<guild_id>/security-edit/<sec_key>", methods=["GET", "POST"])
@guild_access
def s_security_edit(guild_id, sec_key):
    if sec_key not in SEC_KEYS:
        abort(404)
    _, channels, roles = get_server_context(guild_id)
    ch_options = options_html(channels, "#")
    role_options = options_html(roles, "@")
    html = f"""
    <div class="page-head" style="margin-bottom:25px;"><div><h1>✎ تخصيص حماية: {escape(sec_key)}</h1></div><a class="btn btn-secondary" href="/server/{guild_id}/security">← عودة</a></div>
    <div class="form-group"><label>الرومات المستثناة</label><select class="form-control" name="excluded_channels" multiple>{ch_options}</select></div>
    <div class="form-group"><label>الرتب المستثناة</label><select class="form-control" name="excluded_roles" multiple>{role_options}</select></div>
    <div class="form-group"><label>إجراءات العقوبة</label><select class="form-control" name="punishment_action"><option value="warn">تحذير</option><option value="timeout">تايم آوت</option><option value="ban">حظر</option></select></div>
    """
    return render_server_page(guild_id, "security", html)


@app.route("/server/<guild_id>/commands", methods=["GET", "POST"])
@guild_access
def s_commands(guild_id):
    cmds = [
        ("ban", "حظر عضو"), ("unban", "إلغاء حظر"), ("clear", "مسح رسائل"),
        ("hide", "إخفاء روم"), ("show", "إظهار روم"), ("lock", "قفل روم"),
        ("unlock", "فتح روم"), ("move", "نقل صوتي"), ("role", "إضافة/إزالة رتبة"),
        ("setnick", "تغيير لقب"), ("timeout", "إسكات مؤقت"), ("untimeout", "إزالة الإسكات"),
        ("vkick", "طرد صوتي"), ("warn", "تحذير"), ("unwarn", "إزالة تحذير"),
        ("warns", "عرض التحذيرات"), ("vmute", "كتم صوتي")
    ]
    cards_html = "".join([f"""
    <div class="card-item">
      <div class="card-header">
        <div class="card-title"><a class="btn-edit" href="/server/{guild_id}/command-edit/{cmd}">✎ تعديل</a> /{cmd}</div>
        <label class="switch"><input type="checkbox" name="cmd_{cmd}" checked><span class="slider"></span></label>
      </div>
      <div style="font-size: 13px; color: var(--muted); text-align: right;">{desc}</div>
    </div>""" for cmd, desc in cmds])
    return render_server_page(guild_id, "commands", f'<div class="page-head"><h1>🤖 أوامر الإشراف</h1></div><div class="cards-grid-3">{cards_html}</div>')


@app.route("/server/<guild_id>/command-edit/<cmd_name>", methods=["GET", "POST"])
@guild_access
def s_command_edit(guild_id, cmd_name):
    if cmd_name not in CMD_NAMES:
        abort(404)
    _, channels, roles = get_server_context(guild_id)
    ch_options = options_html(channels, "#")
    role_options = options_html(roles, "@")
    html = f"""
    <div class="page-head" style="margin-bottom:25px;"><div><h1>✎ تعديل أمر: /{escape(cmd_name)}</h1></div><a class="btn btn-secondary" href="/server/{guild_id}/commands">← عودة</a></div>
    <div class="form-group"><label>الأسماء البديلة</label><input type="text" class="form-control" name="aliases" value="{escape(cmd_name)}"></div>
    <div class="form-group"><label>الرتب المسموحة</label><select class="form-control" name="allowed_roles" multiple>{role_options}</select></div>
    <div class="form-group"><label>الرومات المسموحة</label><select class="form-control" name="allowed_channels" multiple>{ch_options}</select></div>
    """
    return render_server_page(guild_id, "commands", html)


@app.route("/server/<guild_id>/logs", methods=["GET", "POST"])
@guild_access
def s_logs(guild_id):
    _, channels, _ = get_server_context(guild_id)
    ch_options = options_html(channels, "#")
    empty_ch = '<option value="">اختر الروم...</option>' + ch_options

    logs_list = [
        ("حظر عضو", "log_ban"), ("مهلة عضو", "log_timeout"), ("طرد عضو", "log_kick"),
        ("إنضمام عضو", "log_join"), ("مغادرة عضو", "log_leave"), ("إلغاء حظر عضو", "log_unban"),
        ("إعطاء رتبه", "log_role_give"), ("إزالة رتبه", "log_role_take"), ("تغيير اللقب", "log_name_change"),
        ("حذف رسالة", "log_msg_delete"), ("حذف رسائل", "log_msgs_purge"), ("تعديل رسالة", "log_msg_edit"),
        ("إنشاء روم", "log_channel_create"), ("تعديل روم", "log_channel_edit"), ("حذف روم", "log_channel_delete"),
        ("إنشاء تريد", "log_thread_create"), ("تعديل تريد", "log_thread_edit"), ("حذف تريد", "log_thread_delete"),
        ("إنشاء رتبة", "log_role_create"), ("تعديل رتبة", "log_role_edit"), ("حذف رتبة", "log_role_delete"),
        ("صلاحيات الرومات", "log_channel_perms"), ("تعديل السيرفر", "log_guild_edit"), ("تعديل الإيموجيات", "log_emojis_edit"),
        ("تعديل الملصقات", "log_stickers_edit"), ("الانضمام للصوت", "log_voice_join"), ("مغادرة الصوت", "log_voice_leave"),
        ("التبديل الصوتي", "log_voice_switch"), ("نقل في الصوت", "log_voice_move"), ("قطع الصوت", "log_voice_mute"),
        ("حالة الصوت", "log_voice_state")
    ]

    cards_html = "".join([f"""
    <div class="card-item">
      <div class="card-header">
        <div class="card-title"><span>📊</span> {title}</div>
        <label class="switch"><input type="checkbox" name="{prefix}_enabled" checked><span class="slider"></span></label>
      </div>
      <div style="display: flex; flex-direction: column; gap: 6px;">
        <label style="color:var(--muted); font-size:12px; text-align:right;"># الروم</label>
        <select class="form-control" name="{prefix}_channel" style="padding: 10px 14px; font-size: 13px;">{empty_ch}</select>
      </div>
    </div>""" for title, prefix in logs_list])

    return render_server_page(guild_id, "logs", f'<div class="page-head"><h1>📊 سجلات السيرفر (Logs)</h1></div><div class="cards-grid-3">{cards_html}</div>')


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
      <div><h1>🎫 نظام التذاكر المتقدم</h1><p>إدارة فئات التذاكر وتخصيص الأوصاف والصور ورتب المسؤولين.</p></div>
    </div>

    <div id="categoriesContainer">
      <div class="settings-section-card">
        <div class="settings-section-header">
          <div class="settings-section-title"><span>📂</span> الفئة رقم 1</div>
        </div>
        <div class="form-group">
          <label>اسم الفئة *</label>
          <input type="text" class="form-control" name="cat_name_1" placeholder="أدخل اسم الفئة...">
        </div>
        <div class="form-group">
          <label>وصف التذكرة *</label>
          <textarea class="form-control" name="cat_desc_1" placeholder="أدخل وصفاً تفصيلياً يظهر للمستخدمين عند فتح التذكرة..."></textarea>
        </div>
        <div class="form-group">
          <label>رابط أو صورة التذكرة (Image URL)</label>
          <input type="url" class="form-control" name="cat_image_1" placeholder="https://...">
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
            <div class="tag-input-container" id="container_staff_1">اختر الرتب...</div>
            <input type="hidden" name="cat_staff_roles_1" id="input_staff_1">
            <div class="tag-select-dropdown" id="dropdown_staff_1">{role_options_str}</div>
          </div>
          <div class="form-group">
            <label>نوع العرض *</label>
            <select class="form-control" name="cat_display_type_1"><option value="button">Button Primary</option><option value="select">Select Menu</option></select>
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
