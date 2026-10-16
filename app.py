import os
import requests
from urllib.parse import urlencode
from flask import Flask, redirect, request, session, render_template_string
from markupsafe import escape

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-only-change-this-secret")

CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET", "").strip()

REDIRECT_URI = os.environ.get(
    "DISCORD_REDIRECT_URI",
    "https://sky-panel-z0b2.onrender.com/callback"
).strip()
BOT_TOKEN = os.environ.get("DISCORD_TOKEN", "").strip()

API_ENDPOINT = "https://discord.com/api/v10"
BOT_INVITE_URL = (
    "https://discord.com/oauth2/authorize?"
    + urlencode({
        "client_id": CLIENT_ID,
        "permissions": "8",
        "integration_type": "0",
        "scope": "bot"
    })
)

STYLE = """
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
  --panel: rgba(14, 23, 48, .94);
  --line: rgba(120, 170, 255, .18);
  --blue: #64caff;
  --purple: #9b8cff;
  --gold: #f0b429;
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
  background: rgba(5, 8, 22, .9);
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
  font-size: 14px;
}
.user-pill img { width: 36px; height: 36px; border-radius: 50%; }
.btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 8px;
  padding: 12px 22px; border-radius: 12px; text-decoration: none;
  font-family: inherit; font-size: 14px; font-weight: 800;
  transition: transform .15s ease, box-shadow .15s ease;
  border: 1px solid transparent; cursor: pointer;
}
.btn:hover { transform: translateY(-2px); }
.btn-primary {
  color: #06101f; background: linear-gradient(115deg, #73dcff, #a6a0ff);
  box-shadow: 0 8px 28px #58baff28;
}
.btn-gold {
  color: #06101f; background: var(--gold); font-weight: 900;
}
.btn-secondary {
  color: #e5edff; border-color: var(--line); background: #ffffff08;
}
.btn-discord {
  color: #ffffff; background: #5865F2; box-shadow: 0 4px 20px rgba(88,101,242,0.4);
}
.btn-discord:hover { background: #4752C4; }

.hero {
  width: min(1200px, 92%); margin: auto; padding: 78px 0 65px;
  display: grid; grid-template-columns: 1.15fr .85fr;
  align-items: center; gap: 45px; min-height: 580px;
}
.eyebrow {
  display: inline-flex; align-items: center; gap: 9px; padding: 7px 14px;
  color: #b6dfff; border: 1px solid #67bfff35; background: #57baff0c;
  border-radius: 50px; font-size: 13px; font-weight: 800;
}
.dot { width: 8px; height: 8px; background: #72e5ba; border-radius: 50%; }
h1 {
  font-size: clamp(37px, 5.1vw, 65px); line-height: 1.35;
  letter-spacing: -.8px; margin: 22px 0 14px; font-weight: 900;
}
.gradient-text {
  background: linear-gradient(100deg, #71ddff, #9b9aff 60%, #d6b5ff);
  color: transparent; background-clip: text; -webkit-background-clip: text;
}
.subtitle { color: var(--muted); font-size: 17px; line-height: 2.1; max-width: 550px; }
.actions { display: flex; flex-wrap: wrap; gap: 14px; margin-top: 28px; }
.features { display: flex; flex-wrap: wrap; gap: 22px; margin-top: 32px; color: #b8c6e2; font-size: 13px; }
.feature { display: flex; align-items: center; gap: 8px; }
.feature b { color: #76e3c0; }

.space-art {
  min-height: 360px; position: relative; display: grid; place-items: center;
}
.orbit {
  width: min(340px, 75vw); aspect-ratio: 1; border-radius: 50%;
  border: 1px solid #7b9bff35; display: grid; place-items: center;
  transform: rotate(-18deg); position: relative;
  box-shadow: 0 0 90px #5a7dff0b, inset 0 0 60px #618aff0b;
}
.orbit:before, .orbit:after {
  content: ""; position: absolute; border: 1px solid #80baff30;
  border-radius: 50%; inset: 25px;
}
.orbit:after { inset: 55px; border-color: #b4a0ff35; }
.planet {
  width: 145px; height: 145px; border-radius: 50%;
  background:
    radial-gradient(circle at 30% 25%, #c2edff, transparent 16%),
    radial-gradient(circle at 35% 30%, #7bd8ff, #526de2 42%, #34215f 76%, #10142f);
  box-shadow: inset -20px -15px 35px #030718b5, 0 0 75px #637dff52;
  position: relative; z-index: 1;
}
.planet:after {
  content: ""; position: absolute; width: 190px; height: 35px;
  border: 7px solid #9bb8ff9c; border-left-color: #c2a9ff;
  border-right-color: #6ad8ff; border-radius: 50%; top: 55px; left: -25px;
  transform: rotate(-25deg); box-shadow: 0 0 22px #6dafff38;
}
.float-card {
  position: absolute; padding: 14px 18px; border: 1px solid var(--line);
  border-radius: 14px; background: #101a33d9; backdrop-filter: blur(12px);
  box-shadow: 0 15px 40px #0003; font-size: 13px;
}
.float-card strong { display: block; font-size: 15px; margin-bottom: 3px; }
.float-card small { color: var(--muted); }
.card-top { top: 13%; right: 0; }
.card-bottom { bottom: 12%; left: 0; }

.page { width: min(1250px, 92%); margin: 40px auto 70px; }
.page-head { display: flex; justify-content: space-between; align-items: center; gap: 20px; margin-bottom: 35px; }
.page-head h1 { font-size: 30px; margin: 0 0 6px; }
.page-head p { color: var(--muted); margin: 0; font-size: 14px; }
.server-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 22px; }
.server-card {
  padding: 30px 22px; text-align: center; border-radius: 22px;
  border: 1px solid var(--line);
  background: linear-gradient(155deg, #182441c9, #0b1227db);
  box-shadow: 0 12px 35px #0002; transition: transform .22s, border-color .22s;
}
.server-card:hover { transform: translateY(-5px); border-color: #75caff80; }
.server-icon {
  width: 90px; height: 90px; border-radius: 26px; object-fit: cover;
  border: 2px solid #80cfff80; box-shadow: 0 0 25px #64baff20;
}
.server-card h3 { margin: 16px 0 6px; font-size: 17px; overflow-wrap: anywhere; }
.status { color: #78e3bc; font-size: 12px; margin-bottom: 12px; }
.server-card .btn { margin-top: 12px; width: 100%; }
.empty {
  padding: 55px 25px; text-align: center; border: 1px dashed #7b9dca40;
  background: #ffffff04; border-radius: 20px; color: var(--muted); font-size: 15px;
}
.empty span { display: block; font-size: 40px; margin-bottom: 12px; }

/* القائمة في اليسار والمحتوى في اليمين */
.dashboard-layout {
  display: grid; grid-template-columns: 310px 1fr; gap: 30px;
  width: min(1480px, 97%); margin: 40px auto 70px; align-items: start;
}
.sidebar {
  background: linear-gradient(155deg, #121c38dd, #080d1fff);
  border: 1px solid var(--line); border-radius: 24px; padding: 26px;
  display: flex; flex-direction: column; gap: 18px; backdrop-filter: blur(16px);
  position: sticky; top: 25px; order: 1;
}
.content-panel {
  background: linear-gradient(155deg, #15203acc, #0c1327dd);
  border: 1px solid var(--line); border-radius: 24px; padding: 40px;
  backdrop-filter: blur(16px); min-height: 700px;
  box-shadow: 0 20px 50px rgba(0,0,0,0.4); order: 2;
}

.sidebar-header { text-align: center; padding-bottom: 16px; border-bottom: 1px solid var(--line); }
.sidebar-icon {
  width: 75px; height: 75px; border-radius: 22px; object-fit: cover;
  border: 2px solid #75caff80; box-shadow: 0 0 25px #64baff30; margin: 0 auto 10px; display: block;
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
  background: linear-gradient(115deg, #5bbfff1a, #8f82ff1a);
  color: var(--text); border-color: #7acbff50;
  box-shadow: 0 4px 18px #58baff15; transform: translateX(-3px);
}
.menu-item span { font-size: 18px; }

.form-group { margin-bottom: 22px; }
.form-group label { display: block; font-size: 14px; font-weight: 700; color: #cedbfa; margin-bottom: 8px; text-align: right; }
.field-desc { font-size: 12px; color: var(--muted); margin-bottom: 6px; text-align: right; line-height: 1.6; }
.form-control {
  width: 100%; padding: 12px 16px; border-radius: 12px;
  background: #060a17; border: 1px solid var(--line); color: var(--text);
  font-family: inherit; font-size: 14px; outline: none; transition: border-color .2s;
  text-align: right;
}
.form-control:focus { border-color: var(--blue); box-shadow: 0 0 15px #64baff30; }

select.form-control {
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%239baaca' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: left 14px center;
  background-size: 16px;
  cursor: pointer;
}

.settings-section-card {
  background: #080d1fe6; border: 1px solid var(--line); border-radius: 18px;
  padding: 26px; margin-bottom: 24px; box-shadow: 0 8px 25px rgba(0,0,0,0.25);
}
.settings-section-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; padding-bottom: 14px; border-bottom: 1px solid var(--line);
}
.settings-section-title { font-size: 16px; font-weight: 800; color: #e4eeff; display: flex; align-items: center; gap: 10px; }

/* شريط الحفظ العائم السفلي */
.floating-save-bar {
  position: fixed; bottom: 25px; left: 50%; transform: translateX(-50%) translateY(100px);
  background: rgba(10, 16, 35, 0.95); border: 1px solid #7acbff60; border-radius: 16px;
  padding: 14px 28px; display: flex; align-items: center; gap: 24px;
  box-shadow: 0 15px 45px rgba(0,0,0,0.6); backdrop-filter: blur(16px);
  z-index: 1000; transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
.floating-save-bar.visible { transform: translateX(-50%) translateY(0); }
.save-bar-info { display: flex; align-items: center; gap: 10px; font-size: 14px; font-weight: 700; color: #e4eeff; }
.save-dot { width: 10px; height: 10px; background: #f0b429; border-radius: 50%; box-shadow: 0 0 10px #f0b429; animation: pulse 1.5s infinite; }
@keyframes pulse { 0% { opacity: 0.4; } 50% { opacity: 1; } 100% { opacity: 0.4; } }

.switch {
  position: relative; display: inline-block; width: 48px; height: 26px;
}
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

.cards-grid-3 {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 25px;
}
.card-item {
  background: #080d1fe6; border: 1px solid var(--line); border-radius: 16px;
  padding: 20px; display: flex; flex-direction: column; gap: 14px;
  box-shadow: 0 8px 25px rgba(0,0,0,0.25);
}
.card-header {
  display: flex; justify-content: space-between; align-items: center;
}
.card-title { font-size: 15px; font-weight: 800; color: #e4eeff; display: flex; align-items: center; gap: 8px; }

.security-card {
  background: #080d1fe6; border: 1px solid var(--line); border-radius: 16px;
  padding: 22px; display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 15px; box-shadow: 0 8px 25px rgba(0,0,0,0.25);
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

/* مصمم الصورة القابل للسحب بالماوس مع قيود داخل الصندوق */
.canvas-container {
  width: 100%; height: 260px; background: #050816; border: 2px dashed var(--blue);
  border-radius: 16px; position: relative; overflow: hidden; margin-bottom: 20px;
  background-size: cover; background-position: center; cursor: crosshair; user-select: none;
}
.draggable-item {
  position: absolute; cursor: move; display: inline-block; padding: 4px;
  border: 1px dashed transparent; transition: border 0.2s; z-index: 10;
}
.draggable-item:hover, .draggable-item.active {
  border-color: #64caff; background: rgba(100, 202, 255, 0.1); border-radius: 8px;
}

/* صندوق الاختصارات */
.variable-box {
  background: #060a17; border: 1px solid var(--line); border-radius: 12px; padding: 14px; margin-bottom: 20px;
}
.variable-tag {
  display: inline-block; background: rgba(100,202,255,0.15); color: var(--blue);
  padding: 2px 8px; border-radius: 6px; font-family: monospace; font-size: 13px; margin: 2px 4px; border: 1px solid rgba(100,202,255,0.3);
}

@media(max-width: 1050px) {
  .dashboard-layout { grid-template-columns: 1fr; }
  .sidebar { position: static; order: 2; }
  .content-panel { order: 1; }
  .cards-grid-3 { grid-template-columns: 1fr; }
  .hero { grid-template-columns: 1fr; padding-top: 50px; gap: 15px; }
  .space-art { min-height: 310px; grid-row: 1; }
  .orbit { width: 260px; }
  .planet { width: 110px; height: 110px; }
  .nav { padding: 15px 5%; }
}
</style>
<script>
let initialPositions = {};

function triggerChange() {
  const bar = document.getElementById('saveBar');
  if (bar) bar.classList.add('visible');
}

function saveState() {
  const avatarLeft = document.getElementById('avatar_left');
  const avatarTop = document.getElementById('avatar_top');
  const avatarSize = document.getElementById('avatar_size');
  const textLeft = document.getElementById('text_left');
  const textTop = document.getElementById('text_top');
  const bgUrl = document.getElementById('bg_url_input');

  if (avatarLeft && avatarTop && textLeft && textTop) {
    initialPositions = {
      avatarLeft: avatarLeft.value,
      avatarTop: avatarTop.value,
      avatarSize: avatarSize ? avatarSize.value : '85',
      textLeft: textLeft.value,
      textTop: textTop.value,
      bgUrl: bgUrl ? bgUrl.value : ''
    };
  }
}

function resetPositions() {
  const bar = document.getElementById('saveBar');
  if (bar) bar.classList.remove('visible');

  if (initialPositions.avatarLeft !== undefined) {
    document.getElementById('avatar_left').value = initialPositions.avatarLeft;
    document.getElementById('avatar_top').value = initialPositions.avatarTop;
    if (document.getElementById('avatar_size')) {
      document.getElementById('avatar_size').value = initialPositions.avatarSize;
      changeAvatarSize(initialPositions.avatarSize);
    }
    document.getElementById('text_left').value = initialPositions.textLeft;
    document.getElementById('text_top').value = initialPositions.textTop;

    const dragAvatar = document.getElementById('dragAvatar');
    const dragText = document.getElementById('dragText');

    if (dragAvatar) {
      dragAvatar.style.left = initialPositions.avatarLeft + 'px';
      dragAvatar.style.top = initialPositions.avatarTop + 'px';
    }
    if (dragText) {
      dragText.style.left = initialPositions.textLeft + 'px';
      dragText.style.top = initialPositions.textTop + 'px';
    }

    if (initialPositions.bgUrl !== undefined) {
      updateBg(initialPositions.bgUrl);
    }
  }
}

window.addEventListener('DOMContentLoaded', () => {
  saveState();
  document.querySelectorAll('input, select, textarea').forEach(el => {
    el.addEventListener('input', triggerChange);
    el.addEventListener('change', triggerChange);
  });
});

let activeDrag = null;
let offsetX = 0, offsetY = 0;

function startDrag(e, id) {
  activeDrag = document.getElementById(id);
  offsetX = e.clientX - activeDrag.offsetLeft;
  offsetY = e.clientY - activeDrag.offsetTop;
  document.addEventListener('mousemove', doDrag);
  document.addEventListener('mouseup', stopDrag);
}

function doDrag(e) {
  if (!activeDrag) return;
  const parent = activeDrag.parentElement;
  let x = e.clientX - offsetX;
  let y = e.clientY - offsetY;
  
  if (x < 0) x = 0;
  if (y < 0) y = 0;
  if (x > parent.clientWidth - activeDrag.clientWidth) x = parent.clientWidth - activeDrag.clientWidth;
  if (y > parent.clientHeight - activeDrag.clientHeight) y = parent.clientHeight - activeDrag.clientHeight;

  activeDrag.style.left = x + 'px';
  activeDrag.style.top = y + 'px';

  if (activeDrag.id === 'dragAvatar') {
    document.getElementById('avatar_left').value = Math.round(x);
    document.getElementById('avatar_top').value = Math.round(y);
  } else if (activeDrag.id === 'dragText') {
    document.getElementById('text_left').value = Math.round(x);
    document.getElementById('text_top').value = Math.round(y);
  }
  triggerChange();
}

function stopDrag() {
  activeDrag = null;
  document.removeEventListener('mousemove', doDrag);
  document.removeEventListener('mouseup', stopDrag);
}

function updateBg(url) {
  const canvas = document.getElementById('canvasPreview');
  if (canvas) {
    canvas.style.backgroundImage = 'url(' + url + ')';
  }
}

function changeAvatarSize(size) {
  const avCircle = document.getElementById('avatarCircle');
  if (avCircle) {
    avCircle.style.width = size + 'px';
    avCircle.style.height = size + 'px';
    if (size < 60) {
      avCircle.style.fontSize = '20px';
    } else if (size < 90) {
      avCircle.style.fontSize = '32px';
    } else {
      avCircle.style.fontSize = '44px';
    }
  }
}

function previewLocalImage(input) {
  if (input.files && input.files[0]) {
    const reader = new FileReader();
    reader.onload = function(e) {
      updateBg(e.target.result);
      const urlInput = document.getElementById('bg_url_input');
      if (urlInput) urlInput.value = e.target.result;
      triggerChange();
    };
    reader.readAsDataURL(input.files[0]);
  }
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
    <a href="https://discord.gg/HuH8TtmGA" target="_blank" class="btn btn-discord" style="padding: 8px 18px; font-size: 13px;">
      💬 دعم البوت (Discord)
    </a>
  </div>
</footer>
</body>
</html>
"""

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

@app.route("/")
def home():
    user = session.get("user")
    if user:
        uid = escape(str(user.get("id", "")))
        username = escape(str(user.get("username", "Discord User")))
        avatar = user.get("avatar")
        if avatar:
            avatar_url = f"https://cdn.discordapp.com/avatars/{uid}/{escape(str(avatar))}.png"
        else:
            avatar_url = "https://cdn.discordapp.com/embed/avatars/0.png"

        header_auth = f"""
        <div class="user-pill">
          <img src="{avatar_url}" alt="Avatar">
          <span>{username}</span>
        </div>
        """
        actions = """
        <a class="btn btn-primary" href="/dashboard">⚙️ لوحة التحكم</a>
        <a class="btn btn-secondary" href="/invite">🤖 أضف البوت</a>
        """
    else:
        header_auth = '<a class="btn btn-secondary" href="/login">تسجيل الدخول ↗</a>'
        actions = """
        <a class="btn btn-primary" href="/login">🚀 تسجيل الدخول عبر Discord</a>
        <a class="btn btn-secondary" href="/invite">🤖 دعوة البوت</a>
        """

    content = f"""
    <main>
      <section class="hero">
        <div>
          <div class="eyebrow"><span class="dot"></span> عالمك، إدارتك، تحكمك</div>
          <h1>ارتقِ بسيرفرك<br><span class="gradient-text">إلى عالم آخر.</span></h1>
          <p class="subtitle">
            مرحباً بك في Sky Universe، لوحة تحكم متطورة مرتبة بقوائم في اليسار مع نظام تذاكر متقدم وصلاحيات المسؤولين والمستخدمين.
          </p>
          <div class="actions">{actions}</div>
          <div class="features">
            <div class="feature"><b>✦</b> القائمة في اليسار</div>
            <div class="feature"><b>✦</b> نظام التذاكر المتكامل والصلاحيات</div>
            <div class="feature"><b>✦</b> زر دعم ديسكورد مباشر</div>
          </div>
        </div>
        <div class="space-art">
          <div class="orbit"><div class="planet"></div></div>
          <div class="float-card card-top"><strong>🌌 Sky Universe</strong><small>رحلتك تبدأ هنا</small></div>
          <div class="float-card card-bottom"><strong>⚡ تحكم أذكى</strong><small>كل شيء في مكان واحد</small></div>
        </div>
      </section>
    </main>
    """
    return page("الرئيسية", content, header_auth)

@app.route("/invite")
def invite():
    if not CLIENT_ID:
        return "يرجى ضبط DISCORD_CLIENT_ID في متغيرات البيئة.", 500
    return redirect(BOT_INVITE_URL)

@app.route("/login")
def login():
    if not CLIENT_ID or not CLIENT_SECRET:
        return "يرجى ضبط DISCORD_CLIENT_ID و DISCORD_CLIENT_SECRET.", 500

    params = urlencode({
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "identify guilds"
    })
    return redirect(f"https://discord.com/oauth2/authorize?{params}")

@app.route("/callback")
def callback():
    error = request.args.get("error")
    code = request.args.get("code")

    if error:
        return "تم إلغاء تسجيل الدخول أو رفضه من Discord.", 400
    if not code:
        return "لم يتم استلام كود التحقق من Discord.", 400

    try:
        r = requests.post(
            f"{API_ENDPOINT}/oauth2/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15
        )
        if r.status_code != 200:
            return "فشل تسجيل الدخول. تحقق من إعدادات OAuth2 وحاول مجدداً.", 502

        access_token = r.json().get("access_token")
        if not access_token:
            return "لم يتم استلام رمز الدخول.", 502

        user_res = discord_get("/users/@me", access_token)
        if not user_res or user_res.status_code != 200:
            return "تعذر جلب بيانات حساب Discord.", 502

        session.clear()
        session["user"] = user_res.json()
        session["token"] = access_token
        return redirect("/")

    except (requests.RequestException, ValueError):
        return "تعذر الاتصال بـ Discord حالياً. حاول مجدداً.", 502

@app.route("/dashboard")
def dashboard():
    token = session.get("token")
    if not token:
        return redirect("/login")

    user_res = discord_get("/users/@me/guilds", token)
    if not user_res or user_res.status_code != 200:
        session.clear()
        return redirect("/login")

    user_guilds = user_res.json()
    bot_guilds = set()

    if BOT_TOKEN:
        bot_res = discord_get("/users/@me/guilds", BOT_TOKEN, "Bot")
        if bot_res and bot_res.status_code == 200:
            bot_guilds = {g["id"] for g in bot_res.json()}

    valid_guilds = [
        g for g in user_guilds
        if ((int(g.get("permissions", 0)) & 0x8) == 0x8 or g.get("owner", False))
        and g.get("id") in bot_guilds
    ]

    cards = []
    for g in valid_guilds:
        gid = str(g.get("id", ""))
        name = escape(str(g.get("name", "سيرفر Discord")))
        icon = g.get("icon")
        if icon:
            icon_url = f"https://cdn.discordapp.com/icons/{gid}/{escape(str(icon))}.png"
        else:
            icon_url = "https://cdn.discordapp.com/embed/avatars/0.png"

        action = f'<a class="btn btn-primary" href="/server/{gid}/settings">⚙️ إدارة السيرفر</a>'
        status = '<div class="status">● البوت متصل وجاهز</div>'

        cards.append(f"""
        <article class="server-card">
          <img class="server-icon" src="{icon_url}" alt="Server icon">
          <h3>{name}</h3>
          {status}
          {action}
        </article>
        """)

    content = f"""
    <main class="page">
      <div class="page-head">
        <div><h1>📂 سيرفراتك المتاحة للإدارة</h1>
          <p>السيرفرات التي تمتلك فيها صلاحية Administrator والبوت مضاف إليها.</p></div>
        <a class="btn btn-secondary" href="/">⌂ الرئيسية</a>
      </div>
      {"<div class='server-grid'>" + "".join(cards) + "</div>" if cards else
       "<div class='empty'><span>🌌</span>ما لقينا سيرفرات فيها البوت وأنت أدمن فيها.<br>أضف البوت للسيرفر أولاً ثم حدّث الصفحة.</div>"}
    </main>
    """
    return page("اختيار السيرفر", content)

def get_server_context(guild_id):
    token = session.get("token")
    if not token:
        return None, None, None
    user_res = discord_get("/users/@me/guilds", token)
    if not user_res or user_res.status_code != 200:
        return None, None, None
    
    target_guild = None
    for g in user_res.json():
        if str(g.get("id")) == str(guild_id):
            if (int(g.get("permissions", 0)) & 0x8) == 0x8 or g.get("owner", False):
                target_guild = g
            break
    if not target_guild:
        return None, None, None
        
    channels = []
    roles = []
    if BOT_TOKEN:
        ch_res = discord_get(f"/guilds/{guild_id}/channels", BOT_TOKEN, "Bot")
        if ch_res and ch_res.status_code == 200:
            channels = [c for c in ch_res.json() if c.get("type") == 0]
            
        role_res = discord_get(f"/guilds/{guild_id}/roles", BOT_TOKEN, "Bot")
        if role_res and role_res.status_code == 200:
            roles = role_res.json()
            
    return target_guild, channels, roles

def render_server_page(guild_id, active_tab, tab_content_html):
    target_guild, _, _ = get_server_context(guild_id)
    if not target_guild:
        return "عذراً، ليس لديك صلاحية أو أن السيرفر غير صالح.", 403
        
    guild_name = escape(str(target_guild.get("name", "السيرفر")))
    icon = target_guild.get("icon")
    if icon:
        icon_url = f"https://cdn.discordapp.com/icons/{guild_id}/{escape(str(icon))}.png"
    else:
        icon_url = "https://cdn.discordapp.com/embed/avatars/0.png"
        
    sidebar_html = f"""
    <aside class="sidebar">
      <div class="sidebar-header">
        <img class="sidebar-icon" src="{icon_url}" alt="Server Icon">
        <h3>{guild_name}</h3>
        <p>لوحة التحكم الشاملة</p>
      </div>
      <div class="menu-list">
        <a class="menu-item {'active' if active_tab=='settings' else ''}" href="/server/{guild_id}/settings"><span>⚙️</span> الإعدادات العامة</a>
        <a class="menu-item {'active' if active_tab=='welcome' else ''}" href="/server/{guild_id}/welcome"><span>👋</span> نظام الترحيب</a>
        <a class="menu-item {'active' if active_tab=='security' else ''}" href="/server/{guild_id}/security"><span>🛡️</span> الحماية والأمان</a>
        <a class="menu-item {'active' if active_tab=='commands' else ''}" href="/server/{guild_id}/commands"><span>🤖</span> أوامر الإشراف</a>
        <a class="menu-item {'active' if active_tab=='logs' else ''}" href="/server/{guild_id}/logs"><span>📊</span> السجلات (Logs)</a>
        <a class="menu-item {'active' if active_tab=='tickets' else ''}" href="/server/{guild_id}/tickets"><span>🎫</span> نظام التذاكر</a>
      </div>
      <div style="margin-top: auto; padding-top: 15px; border-top: 1px solid var(--line);">
        <a class="btn btn-secondary" style="width: 100%; text-align: center;" href="/dashboard">← عودة لقائمة السيرفرات</a>
      </div>
    </aside>
    """
    
    floating_bar = f"""
    <div id="saveBar" class="floating-save-bar">
      <div class="save-bar-info">
        <span class="save-dot"></span>
        <span>تم اكتشاف تغييرات! يرجى الحفظ أو الإلغاء.</span>
      </div>
      <div style="display:flex; gap:10px;">
        <button type="submit" form="mainForm" onclick="saveState()" class="btn btn-gold" style="padding: 8px 20px;">حفظ</button>
        <button type="button" form="mainForm" onclick="resetPositions()" class="btn btn-secondary" style="padding: 8px 18px;">إلغاء</button>
      </div>
    </div>
    """
    
    layout_content = f"""
    <div class="dashboard-layout">
      {sidebar_html}
      <main class="content-panel">
        <form id="mainForm" method="POST" enctype="multipart/form-data">
          {tab_content_html}
        </form>
      </main>
    </div>
    {floating_bar}
    """
    return page(f"إدارة {guild_name}", layout_content)

@app.route("/server/<guild_id>/settings", methods=["GET", "POST"])
def s_settings(guild_id):
    html = f"""
    <div class="page-head" style="margin-bottom:25px;">
      <div><h1>⚙️ إعدادات السيرفر واللغة</h1><p>اختر لغة البوت الأساسية وبادئة الأوامر.</p></div>
    </div>
    <div class="form-group">
      <label>لغة البوت (Bot Language)</label>
      <div class="field-desc">حدد اللغة التي سيتفاعل بها البوت مع الأعضاء داخل سيرفرك (عربي / إنجليزي).</div>
      <select class="form-control" name="bot_lang">
        <option value="ar">العربية (Arabic) 🇸🇦</option>
        <option value="en">الإنجليزية (English) 🇺🇸</option>
      </select>
    </div>
    <div class="form-group">
      <label>بادئة الأوامر (Prefix)</label>
      <div class="field-desc">الرمز أو الحرف الذي يبدأ به استخدام أوامر البوت التقليدية (مثال: ! أو ?).</div>
      <input type="text" class="form-control" name="prefix" value="!">
    </div>
    """
    return render_server_page(guild_id, "settings", html)

@app.route("/server/<guild_id>/welcome", methods=["GET", "POST"])
def s_welcome(guild_id):
    _, channels, _ = get_server_context(guild_id)
    ch_options = "".join([f'<option value="{c["id"]}">#{c["name"]}</option>' for c in channels])

    html = f"""
    <div class="page-head" style="margin-bottom:25px;">
      <div><h1>👋 إعدادات الترحيب</h1><p>قم بتكوين رسائل الترحيب وصور الترحيب المخصصة للأعضاء الجدد المنضمين إلى سيرفرك.</p></div>
    </div>

    <!-- صندوق الاختصارات المتاحة -->
    <div class="variable-box">
      <div style="font-weight:800; color:#fff; margin-bottom:6px;">✨ الاختصارات المتاحة لاستخدامها في الرسائل:</div>
      <div>
        <span class="variable-tag">{{user}}</span> لإشارة (منشن) العضو الجديد[cite: 17].<br>
        <span class="variable-tag">{{username}}</span> لكتابة اسم العضو نصياً[cite: 17].<br>
        <span class="variable-tag">{{server}}</span> لكتابة اسم السيرفر تلقائياً[cite: 17].<br>
        <span class="variable-tag">{{membercount}}</span> لطباعة عدد أعضاء السيرفر[cite: 17].
      </div>
    </div>

    <!-- بطاقة رسالة الترحيب -->
    <div class="settings-section-card">
      <div class="settings-section-header">
        <div class="settings-section-title"><span>💬</span> رسالة الترحيب النصية</div>
        <label class="switch">
          <input type="checkbox" name="welcome_msg_enabled" checked>
          <span class="slider"></span>
        </label>
      </div>
      <div class="form-group">
        <label>نص رسالة الترحيب</label>
        <textarea class="form-control" name="welcome_msg" style="min-height: 90px;">مرحباً بك {{user}} في سيرفر {{server}}! 🌸 أنت العضو رقم {{membercount}}</textarea>
      </div>
      <div class="form-group">
        <label>طريقة التوصيل</label>
        <div style="display: flex; gap: 20px; margin-top: 8px;">
          <label style="display: flex; align-items: center; gap: 8px; font-size: 14px; cursor: pointer;">
            <input type="radio" name="welcome_delivery" value="dm"> إرسال كرسالة خاصة (DM)
          </label>
          <label style="display: flex; align-items: center; gap: 8px; font-size: 14px; cursor: pointer;">
            <input type="radio" name="welcome_delivery" value="channel" checked> إرسال إلى روم
          </label>
        </div>
      </div>
      <div class="form-group">
        <label>اختر الروم</label>
        <select class="form-control" name="welcome_channel">
          <option value="">اختر الرومات...</option>
          {ch_options if ch_options else '<option value="">لا توجد رومات متاحة</option>'}
        </select>
      </div>
    </div>

    <!-- بطاقة مصمم صورة الترحيب التفاعلي -->
    <div class="settings-section-card">
      <div class="settings-section-header">
        <div class="settings-section-title"><span>🎨</span> مصمم صورة الترحيب التفاعلي (تصغير، تكبير، وسحب)</div>
        <label class="switch">
          <input type="checkbox" name="welcome_img_enabled" checked>
          <span class="slider"></span>
        </label>
      </div>
      <div class="field-desc">يمكنك سحب العناصر بالماوس (بضمن الحدود المخصصة للقائمة) وتعديل حجم صورة العضو بكل سهولة!</div>

      <!-- لوحة المعاينة والسحب بالماوس -->
      <div id="canvasPreview" class="canvas-container">
        <div id="dragAvatar" class="draggable-item" style="left: 40px; top: 40px;" onmousedown="startDrag(event, 'dragAvatar')">
          <div id="avatarCircle" style="width:85px; height:85px; border-radius:50%; background:#5865F2; display:grid; place-items:center; font-size:32px; box-shadow:0 0 20px rgba(88,101,242,0.5);">👤</div>
        </div>
        <div id="dragText" class="draggable-item" style="left: 150px; top: 60px;" onmousedown="startDrag(event, 'dragText')">
          <div style="font-size:22px; font-weight:900; color:#fff;">Welcome to the server</div>
          <div style="font-size:16px; color:var(--blue);">Username</div>
        </div>
      </div>

      <div class="form-group">
        <label>رفع صورة خلفية من جهازك (الملفات)</label>
        <input type="file" class="form-control" accept="image/*" onchange="previewLocalImage(this)">
      </div>

      <div class="form-group">
        <label>أو ضع رابط صورة خلفية مباشرة (Background Image URL)</label>
        <input type="url" id="bg_url_input" class="form-control" placeholder="https://..." oninput="updateBg(this.value)">
      </div>

      <div style="display:grid; grid-template-columns: 1fr 1fr; gap:15px;">
        <div class="form-group">
          <label>حجم صورة العضو (بالبكسل - تصغير/تكبير)</label>
          <input type="number" id="avatar_size" class="form-control" name="avatar_size" value="85" min="40" max="180" oninput="changeAvatarSize(this.value)">
        </div>
        <div class="form-group">
          <label>موضع صورة العضو (Left)</label>
          <input type="number" id="avatar_left" class="form-control" name="avatar_left" value="40">
        </div>
        <div class="form-group">
          <label>موضع صورة العضو (Top)</label>
          <input type="number" id="avatar_top" class="form-control" name="avatar_top" value="40">
        </div>
        <div class="form-group">
          <label>موضع النص (Left)</label>
          <input type="number" id="text_left" class="form-control" name="text_left" value="150">
        </div>
        <div class="form-group">
          <label>موضع النص (Top)</label>
          <input type="number" id="text_top" class="form-control" name="text_top" value="60">
        </div>
      </div>
    </div>
    """
    return render_server_page(guild_id, "welcome", html)

@app.route("/server/<guild_id>/security", methods=["GET", "POST"])
def s_security(guild_id):
    sec_items = [
        ("كشف الكلمات السيئة", "bad_words", "كشف ومعالجة الرسائل التي تحتوي على كلمات أو عبارات سيئة محددة"),
        ("كشف السبام", "spam", "تحديد ومعالجة رسائل السبام بناءً على التكرار والمحتوى"),
        ("فلترة الروابط", "links", "فلترة وإدارة الرسائل التي تحتوي على روابط، مع خيارات للنطاقات المسموحة"),
        ("سبام المنشن", "mention_spam", "كشف ومعالجة الرسائل التي تحتوي على منشنات مفرطة للمستخدمين")
    ]

    list_html = ""
    for title, key, desc in sec_items:
        list_html += f"""
        <div class="security-card">
          <div class="security-info">
            <h3>{title}</h3>
            <p>{desc}</p>
          </div>
          <div style="display:flex; align-items:center; gap:14px;">
            <a class="btn-edit" href="/server/{guild_id}/security-edit/{key}">إعدادات متقدمة</a>
            <label class="switch">
              <input type="checkbox" name="sec_{key}" checked>
              <span class="slider"></span>
            </label>
          </div>
        </div>
        """

    html = f"""
    <div class="page-head" style="margin-bottom:25px;">
      <div><h1>🛡️ الحماية والأمان</h1><p>أنظمة الحماية المتقدمة لحماية سيرفرك وتأمينه ضد التخريب والسبام.</p></div>
    </div>
    {list_html}
    """
    return render_server_page(guild_id, "security", html)

@app.route("/server/<guild_id>/security-edit/<sec_key>", methods=["GET", "POST"])
def s_security_edit(guild_id, sec_key):
    _, channels, roles = get_server_context(guild_id)
    ch_options = "".join([f'<option value="{c["id"]}">#{c["name"]}</option>' for c in channels])
    role_options = "".join([f'<option value="{r["id"]}">@{r["name"]}</option>' for r in roles])

    html = f"""
    <div class="page-head" style="margin-bottom:25px;">
      <div><h1>✎ تخصيص حماية: {sec_key}</h1><p>تحديد الاستثناءات من رومات ورتب، واختيار إجراءات العقوبة.</p></div>
      <a class="btn btn-secondary" href="/server/{guild_id}/security">← عودة</a>
    </div>
    <div class="form-group">
      <label>الرومات المستثناة</label>
      <select class="form-control" name="excluded_channels">
        <option value="">اختر الروم المستثنى...</option>
        {ch_options if ch_options else '<option value="">لا توجد رومات متاحة</option>'}
      </select>
    </div>
    <div class="form-group">
      <label>الرتب المستثناة</label>
      <select class="form-control" name="excluded_roles">
        <option value="">اختر الرتبة المستثناة...</option>
        {role_options if role_options else '<option value="">لا توجد رتب متاحة</option>'}
      </select>
    </div>
    <div class="form-group">
      <label>إجراءات العقوبة التلقائية</label>
      <select class="form-control" name="punishment_action">
        <option value="warn">إرسال تحذير (Warn)</option>
        <option value="timeout">إسكات مؤقت - تايم آوت (Timeout)</option>
        <option value="ban">حظر نهائي - باند (Ban)</option>
      </select>
    </div>
    """
    return render_server_page(guild_id, "security", html)

@app.route("/server/<guild_id>/commands", methods=["GET", "POST"])
def s_commands(guild_id):
    cmds = [
        ("ban", "حظر عضو من السيرفر"), ("unban", "إلغاء حظر عضو"), ("clear", "مسح الرسائل في روم"),
        ("hide", "إخفاء روم عن الأعضاء"), ("show", "إظهار روم مخفي"), ("lock", "قفل روم لمنع الرسائل"),
        ("unlock", "فتح روم"), ("move", "نقل الأعضاء بين رومات الصوت"), ("role", "إضافة أو إزالة الرتب لعضو"),
        ("setnick", "تعيين لقب لعضو"), ("timeout", "إسكات عضو مؤقتاً"), ("untimeout", "إزالة الإسكات عن عضو"),
        ("vkick", "طرد عضو من روم صوتي"), ("warn", "تحذير عضو"), ("unwarn", "إزالة إنذار عن عضو"),
        ("warns", "عرض تحذيرات عضو"), ("vmute", "كتم عضو في الصوت")
    ]
    cards_html = ""
    for cmd, desc in cmds:
        cards_html += f"""
        <div class="card-item">
          <div class="card-header">
            <div class="card-title"><a class="btn-edit" href="/server/{guild_id}/command-edit/{cmd}">✎ تعديل</a> /{cmd}</div>
            <label class="switch">
              <input type="checkbox" name="cmd_{cmd}" checked>
              <span class="slider"></span>
            </label>
          </div>
          <div style="font-size: 13px; color: var(--muted); text-align: right;">{desc}</div>
        </div>
        """
    html = f"""
    <div class="page-head" style="margin-bottom:25px;">
      <div><h1>🤖 أوامر الإشراف</h1><p>تفعيل، تعطيل، وإعداد أوامر الإشراف.</p></div>
    </div>
    <div class="cards-grid-3">{cards_html}</div>
    """
    return render_server_page(guild_id, "commands", html)

@app.route("/server/<guild_id>/command-edit/<cmd_name>", methods=["GET", "POST"])
def s_command_edit(guild_id, cmd_name):
    _, channels, roles = get_server_context(guild_id)
    ch_options = "".join([f'<option value="{c["id"]}">#{c["name"]}</option>' for c in channels])
    role_options = "".join([f'<option value="{r["id"]}">@{r["name"]}</option>' for r in roles])

    html = f"""
    <div class="page-head" style="margin-bottom:25px;">
      <div><h1>✎ تعديل أمر: /{cmd_name}</h1><p>إعداد الأسماء البديلة، الرتب المسموحة، والرومات المفعلة.</p></div>
      <a class="btn btn-secondary" href="/server/{guild_id}/commands">← عودة</a>
    </div>
    <div class="form-group">
      <label>الأسماء البديلة للأمر</label>
      <input type="text" class="form-control" value="{cmd_name}">
    </div>
    <div class="form-group">
      <label>الرتب المفعلة لاستخدام الأمر</label>
      <select class="form-control" name="allowed_roles">
        <option value="">اختر الرتبة المسموحة...</option>
        {role_options if role_options else '<option value="">لا توجد رتب</option>'}
      </select>
    </div>
    <div class="form-group">
      <label>الرومات المفعلة لاستخدام الأمر</label>
      <select class="form-control" name="allowed_channels">
        <option value="">اختر الروم المسموح...</option>
        {ch_options if ch_options else '<option value="">لا توجد رومات</option>'}
      </select>
    </div>
    """
    return render_server_page(guild_id, "commands", html)

@app.route("/server/<guild_id>/logs", methods=["GET", "POST"])
def s_logs(guild_id):
    _, channels, _ = get_server_context(guild_id)
    ch_options = "".join([f'<option value="{c["id"]}">#{c["name"]}</option>' for c in channels])
    empty_ch = '<option value="">اختر الروم...</option>' + ch_options

    logs_list = [
        ("حظر عضو", "log_ban"), ("مهلة عضو", "log_timeout"), ("طرد عضو", "log_kick"),
        ("إنضمام عضو", "log_join"), ("مغادرة عضو", "log_leave"), ("إلغاء حظر عضو", "log_unban"),
        ("إعطاء رتبه", "log_role_give"), ("إزالة رتبه", "log_role_take"), ("تغيير اللقب", "log_name_change")
    ]
    cards_html = ""
    for title, prefix in logs_list:
        cards_html += f"""
        <div class="card-item">
          <div class="card-header">
            <div class="card-title"><span>📊</span> {title}</div>
            <label class="switch">
              <input type="checkbox" name="{prefix}_enabled" checked>
              <span class="slider"></span>
            </label>
          </div>
          <div style="display: flex; flex-direction: column; gap: 6px;">
            <label style="color:var(--muted); font-size:12px; text-align:right;"># الروم</label>
            <select class="form-control" name="{prefix}_channel" style="padding: 10px 14px; font-size: 13px;">
              {empty_ch}
            </select>
          </div>
        </div>
        """
    html = f"""
    <div class="page-head" style="margin-bottom:25px;">
      <div><h1>📊 سجلات السيرفر (Logs)</h1><p>تكوين رومات التسجيل والأحداث المختلفة.</p></div>
    </div>
    <div class="cards-grid-3">{cards_html}</div>
    """
    return render_server_page(guild_id, "logs", html)

@app.route("/server/<guild_id>/tickets", methods=["GET", "POST"])
def s_tickets(guild_id):
    _, channels, roles = get_server_context(guild_id)
    ch_options = "".join([f'<option value="{c["id"]}">#{c["name"]}</option>' for c in channels])
    role_options = "".join([f'<option value="{r["id"]}">@{r["name"]}</option>' for r in roles])

    html = f"""
    <div class="page-head" style="margin-bottom:25px;">
      <div><h1>🎫 نظام التذاكر المتقدم</h1><p>إدارة فئات التذاكر، صلاحيات المسؤولين والمستخدمين، وإعدادات التضمين.</p></div>
    </div>

    <!-- بطاقة فئات التذاكر -->
    <div class="settings-section-card">
      <div class="settings-section-header">
        <div class="settings-section-title"><span>📂</span> فئات التذاكر (Categories)</div>
      </div>
      <div class="form-group">
        <label>اسم الفئة (مثل: الدعم الفني، الشكاوي)</label>
        <input type="text" class="form-control" name="ticket_category_name" placeholder="أدخل اسم الفئة...">
      </div>
      <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 15px;">
        <div class="form-group">
          <label>روم السجل (Log Channel)</label>
          <select class="form-control" name="ticket_log_channel">
            <option value="">اختر الروم...</option>
            {ch_options if ch_options else '<option value="">لا توجد رومات</option>'}
          </select>
        </div>
        <div class="form-group">
          <label>رتب المسؤولين (Staff Roles)</label>
          <select class="form-control" name="ticket_staff_role">
            <option value="">اختر الرتبة...</option>
            {role_options if role_options else '<option value="">لا توجد رتب</option>'}
          </select>
        </div>
      </div>
    </div>

    <!-- بطاقة صلاحيات المسؤولين والمستخدمين -->
    <div class="settings-section-card">
      <div class="settings-section-header">
        <div class="settings-section-title"><span>🛡️</span> صلاحيات التحكم داخل التذكرة</div>
      </div>
      <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div>
          <h4 style="color:var(--blue); margin-bottom:12px;">صلاحيات المسؤولين</h4>
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <span>إغلاق التذكرة</span>
            <label class="switch"><input type="checkbox" checked><span class="slider"></span></label>
          </div>
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <span>حذف التذكرة</span>
            <label class="switch"><input type="checkbox" checked><span class="slider"></span></label>
          </div>
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <span>نسخ وتصدير محادثة التذكرة</span>
            <label class="switch"><input type="checkbox" checked><span class="slider"></span></label>
          </div>
        </div>
        <div>
          <h4 style="color:var(--purple); margin-bottom:12px;">صلاحيات المستخدمين</h4>
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <span>إغلاق التذكرة الخاصة به</span>
            <label class="switch"><input type="checkbox" checked><span class="slider"></span></label>
          </div>
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <span>إضافة مستخدمين آخرين</span>
            <label class="switch"><input type="checkbox"><span class="slider"></span></label>
          </div>
        </div>
      </div>
    </div>

    <!-- بطاقة صور الخلفية والخطوط للتذاكر -->
    <div class="settings-section-card">
      <div class="settings-section-header">
        <div class="settings-section-title"><span>🖼️</span> صور الخلفية والخطوط المخصصة للتذاكر</div>
      </div>
      <div class="form-group">
        <label>صورة خلفية إعداد التذكرة (1920x1080 مقترح)</label>
        <input type="file" class="form-control" accept="image/*">
      </div>
      <div class="form-group">
        <label>صورة خط الفاصل لتذاكر الدعم</label>
        <input type="file" class="form-control" accept="image/*">
      </div>
    </div>
    """
    return render_server_page(guild_id, "tickets", html)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
