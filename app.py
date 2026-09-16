from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify, json
from flask_sqlalchemy import SQLAlchemy
import random
import string
import time
from datetime import datetime, timezone, timedelta
import os

app = Flask(__name__)
app.secret_key = 'empire_of_numbers_secure_2026_key'

# --- توقيت مدينة بيروت (لبنان) ---
def get_local_time():
    beirut_tz = timezone(timedelta(hours=3))
    return datetime.now(beirut_tz).strftime('%Y-%m-%d %H:%M:%S')

db_path = 'empire_numbers.db'
if os.path.exists('/data'):
    db_path = '/data/empire_numbers.db'

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{db_path}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- نماذج قاعدة البيانات ---

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    role = db.Column(db.String(20), nullable=False, default='user')
    created_by = db.Column(db.String(80), nullable=False, default='system')
    owner_name = db.Column(db.String(100), default='غير محدد')

class SystemVault(db.Model):
    __tablename__ = 'system_vault'
    id = db.Column(db.Integer, primary_key=True)
    vault_balance = db.Column(db.Float, default=1000000.0)

class FinancialLog(db.Model):
    __tablename__ = 'financial_logs'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    action_type = db.Column(db.String(100))
    admin_name = db.Column(db.String(80))
    target_user = db.Column(db.String(80))
    amount = db.Column(db.Float)
    log_time = db.Column(db.String(50))

class RechargeCard(db.Model):
    __tablename__ = 'recharge_cards'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    used_by = db.Column(db.String(80), nullable=True)
    created_at = db.Column(db.String(50))

# جدول تخزين الأرقام الفائزة لـ 50 جولة قادمة لكل لعبة
class GameFutureDraw(db.Model):
    __tablename__ = 'game_future_draws'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    game_name = db.Column(db.String(50), nullable=False) # 'golden', 'roulette', 'empire', 'wheel', 'game20'
    round_index = db.Column(db.Integer, nullable=False) # من 1 إلى 50
    winning_number = db.Column(db.Integer, nullable=False)

# جدول الدردشة الفورية والسرية بين اللاعبين والإدارة
class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sender = db.Column(db.String(80), nullable=False)   # اسم المرسل (لاعب أو admin1)
    recipient = db.Column(db.String(80), nullable=False) # اسم المستلم (admin1 أو اسم اللاعب)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.String(50))

class GoldenNumberBooking(db.Model):
    __tablename__ = 'golden_number_bookings'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80))
    number = db.Column(db.Integer)
    booking_date = db.Column(db.String(50))

class NumbersEmpireBooking(db.Model):
    __tablename__ = 'numbers_empire_bookings'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80))
    number = db.Column(db.Integer)
    booking_date = db.Column(db.String(50))

# --- تهيئة الجداول ---
with app.app_context():
    db.create_all()
    vault = SystemVault.query.get(1)
    if not vault:
        db.session.add(SystemVault(id=1, vault_balance=1000000.0))
    if not User.query.filter_by(username='admin1').first():
        db.session.add(User(username='admin1', password='admin123', balance=0.0, role='admin', created_by='system', owner_name='المشرف العام'))
    db.session.commit()

# --- قاموس الترجمات الشامل ---
TRANSLATIONS = {
    'ar': {
        'dir': 'rtl', 'title': 'امبراطورية الأرقام', 'subtitle': 'منصة الألعاب التفاعلية الفائقة 12D',
        'login': 'دخول للبرنامج', 'username': 'اسم المستخدم', 'password': 'كلمة المرور', 'balance': 'الرصيد',
        'recharge': 'شحن رصيد', 'withdraw': 'سحب رصيد', 'change_pass': 'تغيير الباسورد', 'logout': 'خروج',
        'dashboard': 'لوحة التحكم', 'back_dash': '🏠 الرئيسية', 'customers': 'الزبائن', 'accounting': 'المحاسبة والخزنة',
        'game_control': '🎮 غرفة تحكم الألعاب', 'chat': '💬 الدردشة الفورية والدعم',
        'game1': 'الرقم الحنون', 'game2': 'روليت الحظ', 'game3': 'إمبراطورية الأرقام',
        'game4': 'عجلة الأرقام', 'game5': 'اكشف واربح', 'game6': 'لعبة 70 USDD',
        'cost': 'التكلفة', 'prize': 'الجائزة', 'book': 'حجز', 'cancel': 'تراجع', 'booked': 'محجوز',
        'spin': 'تدوير العجلة', 'reveal': 'اكشف الصناديق', 'draw_now': 'اسحب الآن'
    },
    'en': {
        'dir': 'ltr', 'title': 'Empire of Numbers', 'subtitle': 'Super Interactive 12D Gaming Platform',
        'login': 'Login', 'username': 'Username', 'password': 'Password', 'balance': 'Balance',
        'recharge': 'Recharge', 'withdraw': 'Withdraw', 'change_pass': 'Change Password', 'logout': 'Logout',
        'dashboard': 'Dashboard', 'back_dash': '🏠 Home', 'customers': 'Customers', 'accounting': 'Vault & Accounting',
        'game_control': '🎮 Game Control Room', 'chat': '💬 Live Chat & Support',
        'game1': 'The Tender Number', 'game2': 'Lucky Roulette', 'game3': 'Empire of Numbers',
        'game4': 'Number Wheel', 'game5': 'Reveal & Win', 'game6': '70 USDD Game',
        'cost': 'Cost', 'prize': 'Prize', 'book': 'Book', 'cancel': 'Cancel', 'booked': 'Booked',
        'spin': 'Spin Wheel', 'reveal': 'Reveal Boxes', 'draw_now': 'Draw Now'
    }
}

def get_t():
    lang = session.get('lang', 'ar')
    if lang not in TRANSLATIONS: lang = 'ar'
    return TRANSLATIONS[lang]

def get_lang_bar():
    curr = session.get('lang', 'ar')
    return f"""
<div style="padding: 10px 25px; background: rgba(18, 18, 25, 0.95); display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,215,0,0.2);">
    <div>
        <select onchange="location.href='/set_lang/' + this.value" style="background:#1a1c29; color:#ffd700; border:1px solid #ffd700; padding:6px 12px; border-radius:8px; font-weight:bold; cursor:pointer;">
            <option value="ar" {'selected' if curr=='ar' else ''}>العربية 🇸🇦</option>
            <option value="en" {'selected' if curr=='en' else ''}>English 🇬🇧</option>
        </select>
    </div>
    <div style="display:flex; gap:15px; align-items:center;">
        <a href="/chat" style="color:#38bdf8; text-decoration:none; font-weight:bold; font-size:14px;">💬 الدعم والدردشة</a>
        <a href="/dashboard" style="color:#ffd700; text-decoration:none; font-weight:bold; font-size:14px;">🏠 الرئيسية</a>
    </div>
</div>
"""

# دالة مساعدة لجلب أو استهلاك الرقم الفائز المبرمج للـ 50 جولة القادمة
def get_next_winning_number(game_name, default_min, default_max):
    # نبحث عن أول جولة متاحة (مثلاً أصغر round_index مسجل لهذه اللعبة)
    future_draw = GameFutureDraw.query.filter_by(game_name=game_name).order_by(GameFutureDraw.round_index.asc()).first()
    if future_draw:
        winning_num = future_draw.winning_number
        db.session.delete(future_draw) # استهلاك الرقم لهذه الجولة
        db.session.commit()
        return winning_num
    return random.randint(default_min, default_max)

# --- قوالب HTML ---

LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><title>{{ t.title }} - 12D</title></head>
<body style="font-family:'Segoe UI', Tahoma, sans-serif; background:radial-gradient(circle at center, #1a1c29 0%, #0b0f19 100%); color:#fff; display:flex; justify-content:center; align-items:center; height:90vh; margin:0;">
    <div style="background:rgba(20, 24, 38, 0.85); padding:50px; border-radius:25px; width:380px; text-align:center; border:2px solid rgba(255,215,0,0.5);">
        <h2 style="color:#ffd700;">👑 {{ t.title }}</h2>
        {% if error %}<div style="color:#ef4444; margin-bottom:15px; font-weight:bold;">{{ error }}</div>{% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="{{ t.username }}" required style="width:100%; padding:15px; margin:12px 0; border-radius:12px; background:rgba(10, 13, 22, 0.8); color:#fff; border:1px solid #444;">
            <input type="password" name="password" placeholder="{{ t.password }}" required style="width:100%; padding:15px; margin:12px 0; border-radius:12px; background:rgba(10, 13, 22, 0.8); color:#fff; border:1px solid #444;">
            <button type="submit" style="width:100%; padding:15px; background:linear-gradient(135deg, #ffd700, #ff8c00); color:#000; font-weight:900; border:none; border-radius:12px; cursor:pointer; font-size:18px;">{{ t.login }}</button>
        </form>
    </div>
</body>
</html>
"""

DASHBOARD_PAGE = """
<!DOCTYPE html>
<html lang="{{ lang_key }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ t.dashboard }} - 12D</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: radial-gradient(circle at center, #151928 0%, #070a12 100%); color: #fff; margin: 0; padding: 20px; min-height: 100vh; }
        .header { display: flex; justify-content: space-between; align-items: center; background: rgba(20, 24, 38, 0.9); padding: 18px 30px; border-radius: 18px; border-bottom: 3px solid #ffd700; flex-wrap: wrap; gap: 15px; }
        .icons-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 30px; max-width: 1000px; margin: 40px auto; }
        @media (max-width: 900px) { .icons-grid { grid-template-columns: repeat(2, 1fr); } }
        .icon-card { background: rgba(25,30,48,0.95); border: 3px solid rgba(184,134,11,0.6); border-radius: 28px; padding: 35px 20px; text-align: center; text-decoration: none; box-shadow: 0 20px 45px rgba(0,0,0,0.9); transition: 0.3s; }
        .icon-card:hover { border-color: #ffd700; transform: translateY(-8px); }
        .icon-logo { font-size: 75px; margin-bottom: 15px; }
        .icon-title { color: #ffd700; font-size: 21px; font-weight: 900; }
    </style>
</head>
<body>
    {{ lang_bar | safe }}
    <div class="header">
        <div style="display:flex; gap:18px; align-items:center; flex-wrap:wrap;">
            <h2 style="color:#ffd700; margin:0;">👑 {{ t.title }} (12D)</h2>
            <div style="background:rgba(15,20,32,0.9); padding:8px 15px; border-radius:10px;">👤 <b>{{ username }}</b></div>
            <div style="background:rgba(6,95,70,0.8); color:#34d399; padding:8px 18px; border-radius:10px; font-weight:900;">{{ t.balance }}: <span id="liveBalance">{{ balance }}</span> USDD</div>
        </div>
        <div style="display:flex; gap:12px; flex-wrap:wrap;">
            {% if username == 'admin1' %}
                <a href="/admin_game_control" style="background:#38bdf8; color:#000; padding:10px 16px; text-decoration:none; border-radius:10px; font-weight:900;">🎮 {{ t.game_control }}</a>
                <a href="/admin_chats" style="background:#38bdf8; color:#000; padding:10px 16px; text-decoration:none; border-radius:10px; font-weight:900;">💬 إدارة الدردشة</a>
                <a href="/admin_customers" style="background:#ffd700; color:#000; padding:10px 16px; text-decoration:none; border-radius:10px; font-weight:900;">👥 {{ t.customers }}</a>
                <a href="/admin_accounting" style="background:#ffd700; color:#000; padding:10px 16px; text-decoration:none; border-radius:10px; font-weight:900;">📊 {{ t.accounting }}</a>
            {% endif %}
            <a href="/logout" style="background:#ef4444; color:#fff; padding:10px 16px; text-decoration:none; border-radius:10px; font-weight:900;">{{ t.logout }}</a>
        </div>
    </div>

    <div class="icons-grid">
        <a href="/game_golden_number" class="icon-card"><div class="icon-logo">🏆</div><div class="icon-title">{{ t.game1 }}</div></a>
        <a href="/game_roulette" class="icon-card"><div class="icon-logo">🎰</div><div class="icon-title">{{ t.game2 }}</div></a>
        <a href="/game_numbers_empire" class="icon-card"><div class="icon-logo">🏛️</div><div class="icon-title">{{ t.game3 }}</div></a>
        <a href="/game_number_wheel" class="icon-card"><div class="icon-logo">🎡</div><div class="icon-title">{{ t.game4 }}</div></a>
        <a href="/game_reveal_and_win" class="icon-card"><div class="icon-logo">🎟️</div><div class="icon-title">{{ t.game5 }}</div></a>
        <a href="/game_20_numbers" class="icon-card"><div class="icon-logo">💎</div><div class="icon-title">{{ t.game6 }}</div></a>
    </div>

    <script>
        setInterval(() => {
            fetch('/api/sync_balance').then(res => res.json()).then(data => {
                let badge = document.getElementById('liveBalance');
                if(badge && badge.innerText !== String(data.balance)) badge.innerText = data.balance;
            }).catch(err => {});
        }, 2000);
    </script>
</body>
</html>
"""

# --- غرفة تحكم الألعاب (تحديد الأرقام الفائزة لـ 50 جولة قادمة) ---
ADMIN_GAME_CONTROL_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><title>غرفة تحكم الألعاب (50 جولة)</title>
    <style>
        body { font-family: Tahoma; background: #151928; color: #fff; padding: 25px; text-align: center; }
        .panel { background: rgba(25,30,48,0.95); padding: 25px; border-radius: 20px; border: 2px solid #ffd700; max-width: 700px; margin: 20px auto; text-align: right; }
        input, select { width: 100%; padding: 12px; margin: 8px 0; background: #0a0d16; color: #fff; border: 1px solid #444; border-radius: 8px; box-sizing: border-box; }
    </style>
</head>
<body>
    {{ lang_bar | safe }}
    <h2>🎮 غرفة تحكم الألعاب - برمجة الأرقام الفائزة لـ 50 جولة قادمة</h2>
    <a href="/dashboard" style="background:#3b82f6; color:#fff; padding:10px 18px; text-decoration:none; border-radius:10px; font-weight:900;">الرئيسية</a>

    {% if msg %}<div style="background:#065f46; color:#34d399; padding:12px; border-radius:10px; margin:15px auto; max-width:500px; font-weight:bold;">{{ msg }}</div>{% endif %}

    <div class="panel">
        <h3 style="color:#ffd700; text-align:center;">حدد الرقم الفائز لجولة قادمة</h3>
        <form method="POST">
            <label>اختر اللعبة:</label>
            <select name="game_name" required>
                <option value="golden">الرقم الحنون (1-50)</option>
                <option value="roulette">روليت الحظ (0-36)</option>
                <option value="empire">إمبراطورية الأرقام (1-5)</option>
                <option value="wheel">عجلة الأرقام (1-20)</option>
                <option value="game20">لعبة 70 USDD (1-20)</option>
            </select>
            <label>رقم الجولة القادمة (من 1 إلى 50):</label>
            <input type="number" name="round_index" min="1" max="50" required placeholder="أدخل رقم الجولة القادمة...">
            <label>الرقم الفائز المبرمج:</label>
            <input type="number" name="winning_number" required placeholder="أدخل الرقم الفائز...">
            <button type="submit" style="background:#22c55e; color:#000; padding:12px; font-weight:900; border:none; border-radius:8px; width:100%; cursor:pointer; margin-top:15px;">حفظ في غرفة التحكم ⚡</button>
        </form>
    </div>

    <div style="background:rgba(25,30,48,0.9); padding:20px; border-radius:15px; max-width:800px; margin:20px auto;">
        <h3 style="color:#ffd700;">📋 الأرقام المبرمجة حالياً للجولات القادمة</h3>
        <table style="width:100%; border-collapse:collapse; margin-top:10px;">
            <tr style="background:#0a0d16; color:#ffd700;"><th style="padding:10px; border:1px solid #444;">اللعبة</th><th style="padding:10px; border:1px solid #444;">رقم الجولة</th><th style="padding:10px; border:1px solid #444;">الرقم الفائز المبرمج</th></tr>
            {% for d in future_draws %}
            <tr><td style="padding:10px; border:1px solid #444;">{{ d.game_name }}</td><td style="padding:10px; border:1px solid #444;">جولة #{{ d.round_index }}</td><td style="padding:10px; border:1px solid #444; color:#34d399;"><b>{{ d.winning_number }}</b></td></tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

# --- نظام الدردشة الفورية والسرية التامة للعبّاد مع الإدارة ---
CHAT_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><title>الدردشة الفورية والدعم الفني</title>
    <style>
        body { font-family: Tahoma; background: #151928; color: #fff; padding: 20px; text-align: center; }
        .chat-box { background: rgba(25,30,48,0.95); border: 2px solid #ffd700; border-radius: 20px; max-width: 650px; margin: 20px auto; padding: 25px; text-align: right; }
        .messages-area { height: 350px; background: #0a0d16; border: 1px solid #444; border-radius: 12px; padding: 15px; overflow-y: scroll; margin-bottom: 15px; display: flex; flex-direction: column; gap: 10px; }
        .msg { padding: 10px 15px; border-radius: 10px; max-width: 75%; font-size: 15px; }
        .msg.user { background: #1e3a8a; align-self: flex-start; }
        .msg.admin { background: #065f46; align-self: flex-end; }
        input, button { padding: 12px; border-radius: 8px; border: 1px solid #444; }
    </style>
</head>
<body>
    {{ lang_bar | safe }}
    <h2>💬 غرفة الدردشة والدعم الفني الفوري (سرية تامة)</h2>
    <a href="/dashboard" style="background:#3b82f6; color:#fff; padding:10px 18px; text-decoration:none; border-radius:10px; font-weight:900;">الرئيسية</a>

    <div class="chat-box">
        <div class="messages-area" id="msgArea">
            {% for m in messages %}
            <div class="msg {% if m.sender == username %}user{% else %}admin{% endif %}">
                <b style="font-size:12px; color:#ffd700;">{{ m.sender }}:</b><br>
                <span>{{ m.message }}</span>
                <div style="font-size:10px; color:#aaa; margin-top:5px; text-align:left;">{{ m.timestamp }}</div>
            </div>
            {% endfor %}
        </div>
        <form method="POST" style="display:flex; gap:10px;">
            <input type="text" name="message" required placeholder="اكتب استفسارك هنا بسرية تامة..." style="flex:1; background:#0a0d16; color:#fff;">
            <button type="submit" style="background:#22c55e; color:#000; font-weight:900; cursor:pointer;">إرسال</button>
        </form>
    </div>
    <script>
        let area = document.getElementById('msgArea');
        area.scrollTop = area.scrollHeight;
    </script>
</body>
</html>
"""

# --- لوحة إدارة الدردشات للآدمن (لكل لاعب دردشة منفصلة وسرية) ---
ADMIN_CHATS_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><title>إدارة الدردشات السرية</title>
    <style>
        body { font-family: Tahoma; background: #151928; color: #fff; padding: 20px; text-align: center; }
        .chat-container { display: flex; max-width: 1000px; margin: 20px auto; background: rgba(25,30,48,0.95); border-radius: 20px; border: 2px solid #ffd700; overflow: hidden; }
        .users-list { width: 30%; background: #0a0d16; border-left: 1px solid #444; padding: 15px; text-align: right; }
        .user-link { display: block; padding: 12px; color: #ffd700; text-decoration: none; border-bottom: 1px solid #222; font-weight: bold; border-radius: 8px; margin-bottom: 5px; background: #141824; }
        .user-link:hover, .user-link.active { background: #3b82f6; color: #fff; }
        .chat-window { width: 70%; padding: 20px; text-align: right; display: flex; flex-direction: column; }
        .messages-area { height: 350px; background: #0a0d16; border: 1px solid #444; border-radius: 12px; padding: 15px; overflow-y: scroll; margin-bottom: 15px; display: flex; flex-direction: column; gap: 10px; }
        .msg { padding: 10px 15px; border-radius: 10px; max-width: 75%; }
        .msg.admin { background: #1e3a8a; align-self: flex-start; }
        .msg.user { background: #065f46; align-self: flex-end; }
    </style>
</head>
<body>
    {{ lang_bar | safe }}
    <h2>💬 لوحة إدارة ومتابعة دردشات اللاعبين (سرية تامة)</h2>
    <a href="/dashboard" style="background:#3b82f6; color:#fff; padding:10px 18px; text-decoration:none; border-radius:10px; font-weight:900;">الرئيسية</a>

    <div class="chat-container">
        <div class="users-list">
            <h4 style="color:#ffd700; margin-top:0;">اللاعبون المتحدثون</h4>
            {% for u in chatting_users %}
            <a href="/admin_chats?user={{ u }}" class="user-link {% if active_user == u %}active{% endif %}">👤 {{ u }}</a>
            {% endfor %}
        </div>
        <div class="chat-window">
            {% if active_user %}
            <h4 style="color:#38bdf8; margin-top:0;">محادثة مع اللاعب: {{ active_user }}</h4>
            <div class="messages-area" id="adminMsgArea">
                {% for m in messages %}
                <div class="msg {% if m.sender == 'admin1' %}admin{% else %}user{% endif %}">
                    <b style="font-size:12px; color:#ffd700;">{{ m.sender }}:</b><br>
                    <span>{{ m.message }}</span>
                    <div style="font-size:10px; color:#aaa; margin-top:5px; text-align:left;">{{ m.timestamp }}</div>
                </div>
                {% endfor %}
            </div>
            <form method="POST" style="display:flex; gap:10px;">
                <input type="hidden" name="recipient" value="{{ active_user }}">
                <input type="text" name="message" required placeholder="اكتب ردك للسبون..." style="flex:1; padding:12px; background:#0a0d16; color:#fff; border:1px solid #444; border-radius:8px;">
                <button type="submit" style="background:#22c55e; color:#000; font-weight:900; padding:0 20px; border:none; border-radius:8px; cursor:pointer;">إرسال الرد</button>
            </form>
            {% else %}
            <p style="color:#aaa; text-align:center; margin-top:150px;">اختر لاعباً من القائمة لعرض المحادثة السرية والرد عليه.</p>
            {% endif %}
        </div>
    </div>
    <script>
        let area = document.getElementById('adminMsgArea');
        if(area) area.scrollTop = area.scrollHeight;
    </script>
</body>
</html>
"""

# بقية قوالب الألعاب الأساسية والمحاسبة...
GAME_GOLDEN_PAGE = """
<!DOCTYPE html>
<html lang="{{ lang_key }}" dir="{{ t.dir }}">
<head><meta charset="UTF-8"><title>{{ t.game1 }}</title>
<style>body{background:#151928;color:#fff;text-align:center;padding:25px;font-family:Tahoma;} .grid{display:grid;grid-template-columns:repeat(10,1fr);gap:10px;max-width:800px;margin:20px auto;} .cell{background:#7c3aed;padding:15px;color:#fff;font-weight:bold;border:2px solid #ffd700;border-radius:10px;cursor:pointer;}</style>
</head>
<body>
    {{ lang_bar | safe }}
    <div style="max-width:850px;margin:20px auto;background:#1e2336;padding:30px;border-radius:20px;border:3px solid #ffd700;">
        <h2 style="color:#ffd700;">🏆 {{ t.game1 }}</h2>
        <p><b>{{ t.balance }}: {{ balance }} USDD</b></p>
        <div class="grid">
            {% for i in range(1, 51) %}
            <button onclick="book({{ i }})" class="cell">{{ i }}</button>
            {% endfor %}
        </div>
    </div>
    <script>
        function book(n) {
            let fd = new FormData(); fd.append('action_type', 'book'); fd.append('number', n);
            fetch('/game_golden_number', {method:'POST', body:fd}).then(r=>r.json()).then(d=>{ alert(d.msg); location.reload(); });
        }
    </script>
</body>
</html>
"""

# --- المسارات والتحكم بالفلسب ---

@app.route('/set_lang/<lang>')
def set_lang(lang):
    if lang in TRANSLATIONS: session['lang'] = lang
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/api/sync_balance')
def api_sync_balance():
    if 'username' not in session: return jsonify({"balance": 0.0})
    user = User.query.filter_by(username=session['username']).first()
    return jsonify({"balance": user.balance if user else 0.0})

@app.route('/', methods=['GET', 'POST'])
def login():
    t = get_t()
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session.clear()
            session['username'] = user.username
            session['balance'] = user.balance
            session['role'] = user.role
            return redirect(url_for('dashboard'))
        else:
            error = "خطأ في اسم المستخدم أو كلمة المرور!"
    return render_template_string(LOGIN_PAGE, t=t, error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session: return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    t = get_t()
    lang_key = session.get('lang', 'ar')
    return render_template_string(DASHBOARD_PAGE, t=t, lang_key=lang_key, lang_bar=get_lang_bar(), username=user.username, balance=user.balance)

# --- مسار غرفة تحكم الألعاب (50 جولة) ---
@app.route('/admin_game_control', methods=['GET', 'POST'])
def admin_game_control():
    if 'username' not in session or session.get('username') != 'admin1': return redirect(url_for('dashboard'))
    msg = None
    if request.method == 'POST':
        game_name = request.form.get('game_name')
        round_index = int(request.form.get('round_index', 1))
        winning_number = int(request.form.get('winning_number', 0))
        
        # تحقق أو تحديث الجولة القادمة المسجلة مسبقاً
        existing = GameFutureDraw.query.filter_by(game_name=game_name, round_index=round_index).first()
        if existing:
            existing.winning_number = winning_number
        else:
            db.session.add(GameFutureDraw(game_name=game_name, round_index=round_index, winning_number=winning_number))
        db.session.commit()
        msg = f"تمت برمجة الرقم {winning_number} للجولة #{round_index} في لعبة {game_name} بنجاح!"
    
    future_draws = GameFutureDraw.query.order_by(GameFutureDraw.game_name, GameFutureDraw.round_index).all()
    return render_template_string(ADMIN_GAME_CONTROL_PAGE, lang_bar=get_lang_bar(), future_draws=future_draws, msg=msg)

# --- مسار الدردشة الفورية لللاعبين (سرية تامة) ---
@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'username' not in session: return redirect(url_for('login'))
    username = session['username']
    if request.method == 'POST':
        message = request.form.get('message', '').strip()
        if message:
            db.session.add(ChatMessage(sender=username, recipient='admin1', message=message, timestamp=get_local_time()))
            db.session.commit()
            return redirect(url_for('chat'))
    
    # جلب محادثات هذا اللاعب فقط (سرية تامة بحيث لا يرى محادثات الآخرين)
    messages = ChatMessage.query.filter(
        ((ChatMessage.sender == username) & (ChatMessage.recipient == 'admin1')) |
        ((ChatMessage.sender == 'admin1') & (ChatMessage.recipient == username))
    ).order_by(ChatMessage.id.asc()).all()
    
    return render_template_string(CHAT_PAGE, lang_bar=get_lang_bar(), username=username, messages=messages)

# --- مسار إدارة الدردشات للآدمن ---
@app.route('/admin_chats', methods=['GET', 'POST'])
def admin_chats():
    if 'username' not in session or session.get('username') != 'admin1': return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        recipient = request.form.get('recipient')
        message = request.form.get('message', '').strip()
        if recipient and message:
            db.session.add(ChatMessage(sender='admin1', recipient=recipient, message=message, timestamp=get_local_time()))
            db.session.commit()
            return redirect(url_for('admin_chats', user=recipient))
            
    active_user = request.args.get('user')
    # استخراج قائمة اللاعبين الذين أرسلوا رسائل للإدارة
    chatting_users = db.session.query(ChatMessage.sender).filter(ChatMessage.sender != 'admin1').distinct().all()
    chatting_users = [u[0] for u in chatting_users]
    
    messages = []
    if active_user:
        messages = ChatMessage.query.filter(
            ((ChatMessage.sender == active_user) & (ChatMessage.recipient == 'admin1')) |
            ((ChatMessage.sender == 'admin1') & (ChatMessage.recipient == active_user))
        ).order_by(ChatMessage.id.asc()).all()
        
    return render_template_string(ADMIN_CHATS_PAGE, lang_bar=get_lang_bar(), chatting_users=chatting_users, active_user=active_user, messages=messages)

# مثال على دمج سحب الرقم في اللعبة (مثل الرقم الحنون)
@app.route('/game_golden_number', methods=['GET', 'POST'])
def game_golden_number():
    if 'username' not in session: return redirect(url_for('login'))
    username = session['username']
    user = User.query.filter_by(username=username).first()
    if request.method == 'POST':
        action_type = request.form.get('action_type')
        if action_type == 'book':
            number = int(request.form.get('number', 0))
            if user.balance >= 20.0 and not GoldenNumberBooking.query.filter_by(number=number).first():
                user.balance -= 20.0
                db.session.add(GoldenNumberBooking(username=username, number=number, booking_date=get_local_time()))
                db.session.commit()
                return jsonify({"success": True, "msg": f"تم حجز الرقم {number}!"})
    return render_template_string(GAME_GOLDEN_PAGE, t=get_t(), lang_key=session.get('lang', 'ar'), lang_bar=get_lang_bar(), balance=user.balance)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
