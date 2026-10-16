import os
import requests
from flask import Flask, redirect, request, session, render_template_string

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "sky_secret_key_123")

CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET", "").strip()
REDIRECT_URI = os.environ.get("DISCORD_REDIRECT_URI", "").strip()
BOT_TOKEN = os.environ.get("DISCORD_TOKEN", "").strip()

BOT_INVITE_URL = f"https://discord.com/oauth2/authorize?client_id={CLIENT_ID}&permissions=8&integration_type=0&scope=bot"
API_ENDPOINT = "https://discord.com/api/v10"

@app.route("/")
def home():
    user = session.get('user')
    
    if user:
        avatar_url = f"https://cdn.discordapp.com/avatars/{user['id']}/{user['avatar']}.png" if user.get('avatar') else "https://cdn.discordapp.com/embed/avatars/0.png"
        header_auth = f'''
        <div style="display:flex; align-items:center; gap:12px; background:#1e293b; padding:8px 16px; border-radius:30px; border:1px solid #334155;">
            <img src="{avatar_url}" style="width:40px; height:40px; border-radius:50%; object-fit:cover;">
            <span style="font-weight:bold; color:#f8fafc;">{user['username']}</span>
        </div>
        '''
        center_buttons = f'''
        <a href="/dashboard" style="background:#10b981; color:white; padding:14px 30px; text-decoration:none; border-radius:8px; font-weight:bold; font-size:16px;">تحكم في البوت ⚙️</a>
        <a href="{BOT_INVITE_URL}" target="_blank" style="background:#38bdf8; color:#0b0f19; padding:14px 30px; text-decoration:none; border-radius:8px; font-weight:bold; font-size:16px;">دعوة البوت للسيرفر 🤖</a>
        '''
    else:
        header_auth = '<a href="/login" style="background:#38bdf8; color:#0b0f19; padding:10px 22px; text-decoration:none; border-radius:8px; font-weight:bold;">تسجيل الدخول 🚀</a>'
        center_buttons = f'''
        <a href="/login" style="background:#38bdf8; color:#0b0f19; padding:14px 35px; text-decoration:none; border-radius:8px; font-weight:bold; font-size:16px;">تسجيل الدخول عبر Discord 🚀</a>
        <a href="{BOT_INVITE_URL}" target="_blank" style="background:#1e293b; color:#38bdf8; padding:14px 35px; text-decoration:none; border-radius:8px; font-weight:bold; font-size:16px; border:1px solid #38bdf8;">دعوة البوت للسيرفر 🤖</a>
        '''

    return render_template_string(f'''
    <html lang="ar" dir="rtl">
    <head><meta charset="UTF-8"><title>Sky Universe | لوحة التحكم</title></head>
    <body style="background:#0b0f19; color:white; font-family:Tahoma; margin:0; height:100vh; display:flex; flex-direction:column;">
        <div style="display:flex; justify-content:space-between; align-items:center; padding:20px 40px; background:#111827; border-bottom:1px solid #1f2937;">
            <h2 style="color:#38bdf8; margin:0;">✨ Sky Bot Panel</h2>
            <div>{header_auth}</div>
        </div>
        <div style="flex:1; display:flex; justify-content:center; align-items:center;">
            <div style="background:#1e293b; padding:50px; border-radius:16px; text-align:center; border:1px solid #334155; max-width:550px; width:100%;">
                <h1 style="color:#38bdf8; margin-top:0; font-size:28px;">أهلاً بك في لوحة تحكم بوت Sky</h1>
                <p style="color:#9ca3af; line-height:1.6; margin-bottom:35px;">قم بإدارة سيرفرك، الحماية، التذاكر، وأنظمة الترحيب بكل احترافية.</p>
                <div style="display:flex; justify-content:center; gap:15px; flex-wrap:wrap;">{center_buttons}</div>
            </div>
        </div>
    </body>
    </html>
    ''')

@app.route("/login")
def login():
    return redirect(f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify%20guilds")

@app.route("/callback")
def callback():
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        return f"<h3 style='color:red; font-family:Tahoma; direction:rtl;'>❌ خطأ من ديسكورد: {error}</h3>"
    
    if not code:
        return "<h3 style='color:orange; font-family:Tahoma; direction:rtl;'>⚠️ لم يتم استلام كود التحقق من ديسكورد.</h3>"

    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    r = requests.post(f"{API_ENDPOINT}/oauth2/token", data=data, headers=headers)
    
    if r.status_code != 200:
        return f"<h3 style='color:red; font-family:Tahoma; direction:rtl;'>❌ فشل الاتصال بديسكورد (كود الخطأ: {r.status_code})<br>التفاصيل: {r.text}</h3>"
        
    token_data = r.json()
    access_token = token_data.get('access_token')
    
    user_res = requests.get(f"{API_ENDPOINT}/users/@me", headers={"Authorization": f"Bearer {access_token}"})
    if user_res.status_code == 200:
        session['user'] = user_res.json()
        session['token'] = access_token
        return redirect("/")
    else:
        return f"<h3 style='color:red; font-family:Tahoma; direction:rtl;'>❌ تعذر جلب بيانات المستخدم (كود: {user_res.status_code})</h3>"

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
        
        if has_bot:
            btn_action = f"<a href='/server/{g['id']}' style='background:#10b981; color:white; padding:8px 18px; text-decoration:none; border-radius:6px; display:inline-block; margin-top:12px; font-weight:bold;'>إدارة السيرفر ⚙️</a>"
        else:
            btn_action = f"<a href='{BOT_INVITE_URL}' target='_blank' style='background:#38bdf8; color:#0b0f19; padding:8px 18px; text-decoration:none; border-radius:6px; display:inline-block; margin-top:12px; font-weight:bold;'>إضافة البوت 🤖</a>"

        cards_html += f'''
        <div style="background:#1e293b; padding:25px; border-radius:12px; width:240px; text-align:center; border:1px solid #334155;">
            <img src="{icon_url}" width="85" height="85" style="border-radius:50%; object-fit:cover; border:3px solid #38bdf8;">
            <h3 style="color:white; margin:15px 0 5px 0; font-size:16px;">{g['name']}</h3>
            {btn_action}
        </div>
        '''

    return render_template_string(f'''
    <html lang="ar" dir="rtl">
    <head><meta charset="UTF-8"><title>اختر السيرفر | Sky Panel</title></head>
    <body style="background:#0b0f19; color:white; font-family:Tahoma; padding:40px;">
        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:2px solid #334155; padding-bottom:15px; margin-bottom:30px;">
            <h2 style="color:#38bdf8; margin:0;">📂 اختر السيرفر لإدارة الإعدادات:</h2>
            <a href="/" style="background:#334155; color:white; padding:8px 16px; text-decoration:none; border-radius:6px; font-weight:bold;">الرئيسية 🏠</a>
        </div>
        <div style="display:flex; gap:20px; flex-wrap:wrap;">
            {cards_html if cards_html else "<p style='color:#9ca3af;'>لا توجد سيرفرات تمتلك فيها صلاحية Administrator ومتاحة للإدارة حالياً.</p>"}
        </div>
    </body>
    </html>
    ''')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
