import os
import requests
from flask import Flask, redirect, request, session, render_template_string

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "sky_secret_key_123")

CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET", "")
REDIRECT_URI = os.environ.get("DISCORD_REDIRECT_URI", "")
BOT_TOKEN = os.environ.get("DISCORD_TOKEN", "")

API_ENDPOINT = "https://discord.com/api/v10"

@app.route("/")
def home():
    return '''
    <html lang="ar" dir="rtl">
    <head><meta charset="UTF-8"><title>Sky Panel</title></head>
    <body style="background:#0b0f19;color:white;font-family:Tahoma;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;">
        <div style="background:#1e293b;padding:40px;border-radius:15px;text-align:center;box-shadow:0 10px 25px rgba(0,0,0,0.5);border:1px solid #334155;">
            <h1 style="color:#38bdf8;margin-bottom:10px;">🤖 لوحة تحكم بوت Sky</h1>
            <p style="color:#9ca3af;">إدارة خصائص الحماية، التذاكر، والترحيب المتقدمة لسيرفرك</p>
            <a href="/login" style="background:#38bdf8;color:#0b0f19;padding:12px 30px;text-decoration:none;border-radius:8px;font-weight:bold;display:inline-block;margin-top:20px;">تسجيل الدخول عبر Discord 🚀</a>
        </div>
    </body>
    </html>
    '''

@app.route("/login")
def login():
    return redirect(f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify%20guilds")

@app.route("/callback")
def callback():
    code = request.args.get('code')
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    r = requests.post(f"{API_ENDPOINT}/oauth2/token", data=data, headers=headers)
    token = r.json().get('access_token')
    session['token'] = token
    return redirect("/dashboard")

@app.route("/dashboard")
def dashboard():
    token = session.get('token')
    if not token:
        return redirect("/")
    
    headers = {"Authorization": f"Bearer {token}"}
    guilds_res = requests.get(f"{API_ENDPOINT}/users/@me/guilds", headers=headers)
    user_guilds = guilds_res.json() if guilds_res.status_code == 200 else []

    bot_headers = {"Authorization": f"Bot {BOT_TOKEN}"}
    bot_guilds_res = requests.get(f"{API_ENDPOINT}/users/@me/guilds", headers=bot_headers)
    bot_guilds = {g['id'] for g in bot_guilds_res.json()} if bot_guilds_res.status_code == 200 else set()

    valid_guilds = [g for g in user_guilds if (int(g.get('permissions', 0)) & 0x8) == 0x8 or g.get('owner', False)]

    cards_html = ""
    for g in valid_guilds:
        has_bot = g['id'] in bot_guilds
        icon_url = f"https://cdn.discordapp.com/icons/{g['id']}/{g['icon']}.png" if g['icon'] else "https://cdn.discordapp.com/embed/avatars/0.png"
        
        btn_action = f"<a href='/server/{g['id']}' style='background:#10b981;color:white;padding:8px 15px;text-decoration:none;border-radius:6px;display:inline-block;margin-top:10px;font-weight:bold;'>إدارة السيرفر ⚙️</a>" if has_bot else f"<a href='https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&permissions=8&scope=bot' target='_blank' style='background:#38bdf8;color:#0b0f19;padding:8px 15px;text-decoration:none;border-radius:6px;display:inline-block;margin-top:10px;font-weight:bold;'>إضافة البوت 🤖</a>"

        cards_html += f'''
        <div style="background:#1e293b;padding:20px;border-radius:12px;width:220px;text-align:center;border:1px solid #334155;">
            <img src="{icon_url}" width="80" height="80" style="border-radius:50%;object-fit:cover;border:2px solid #38bdf8;">
            <h3 style="color:white;margin:10px 0;font-size:16px;">{g['name']}</h3>
            {btn_action}
        </div>
        '''

    return render_template_string(f'''
    <html lang="ar" dir="rtl">
    <head><meta charset="UTF-8"><title>اختر السيرفر | Sky Panel</title></head>
    <body style="background:#0b0f19;color:white;font-family:Tahoma;padding:40px;">
        <h2 style="color:#38bdf8;border-bottom:2px solid #334155;padding-bottom:10px;">اختر السيرفر لإدارة الإعدادات:</h2>
        <div style="display:flex;gap:20px;flex-wrap:wrap;margin-top:20px;">
            {cards_html}
        </div>
    </body>
    </html>
    ''')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
