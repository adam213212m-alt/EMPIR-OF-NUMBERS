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
    role = db.Column(db.String(20), nullable=False, default='user') # 'admin', 'supervisor', 'user'
    created_by = db.Column(db.String(80), nullable=False, default='system') # اسم المشرف الذي أنشأ اللاعب
    owner_name = db.Column(db.String(100), default='غير محدد')

class SystemVault(db.Model):
    __tablename__ = 'system_vault'
    id = db.Column(db.Integer, primary_key=True)
    vault_balance = db.Column(db.Float, default=1000000.0)

class FinancialLog(db.Model):
    __tablename__ = 'financial_logs'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    action_type = db.Column(db.String(100))
    admin_name = db.Column(db.String(80)) # المشرف أو الآدمن المنفذ
    target_user = db.Column(db.String(80))
    amount = db.Column(db.Float)
    log_time = db.Column(db.String(50))

class PlayerActivity(db.Model):
    __tablename__ = 'player_activities'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), nullable=False)
    supervisor_name = db.Column(db.String(80), nullable=False, default='system')
    game_name = db.Column(db.String(100), nullable=False)
    bet_details = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, default=0.0)
    outcome = db.Column(db.String(50), nullable=False)
    winning_number = db.Column(db.String(50), default='---')
    timestamp = db.Column(db.String(50), nullable=False)

class RechargeCard(db.Model):
    __tablename__ = 'recharge_cards'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    used_by = db.Column(db.String(80), nullable=True)
    created_at = db.Column(db.String(50))

class GameFutureDraw(db.Model):
    __tablename__ = 'game_future_draws'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    supervisor_scope = db.Column(db.String(80), nullable=False, default='global') # دعم 10 مشرفين أو عام
    game_name = db.Column(db.String(50), nullable=False)
    round_index = db.Column(db.Integer, nullable=False)
    winning_number = db.Column(db.Integer, nullable=False)

class RevealAndWinGlobalState(db.Model):
    __tablename__ = 'reveal_and_win_global'
    id = db.Column(db.Integer, primary_key=True)
    total_spins = db.Column(db.Integer, default=0)

class EmpireGlobalState(db.Model):
    __tablename__ = 'empire_global_state'
    id = db.Column(db.Integer, primary_key=True)
    last_winning_number = db.Column(db.Integer, default=0)
    draw_timestamp = db.Column(db.Float, default=0.0)
    last_winner_info = db.Column(db.String(150), default='لا يوجد فائز سابق بعد')

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sender = db.Column(db.String(80), nullable=False)
    recipient = db.Column(db.String(80), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.String(50))

class GoldenNumberBooking(db.Model):
    __tablename__ = 'golden_number_bookings'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    supervisor_name = db.Column(db.String(80), default='system')
    username = db.Column(db.String(80))
    number = db.Column(db.Integer)
    booking_date = db.Column(db.String(50))

class NumbersEmpireBooking(db.Model):
    __tablename__ = 'numbers_empire_bookings'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    supervisor_name = db.Column(db.String(80), default='system')
    username = db.Column(db.String(80))
    number = db.Column(db.Integer)
    booking_date = db.Column(db.String(50))

with app.app_context():
    db.create_all()
    vault = SystemVault.query.get(1)
    if not vault:
        db.session.add(SystemVault(id=1, vault_balance=1000000.0))
    if not User.query.filter_by(username='admin1').first():
        db.session.add(User(username='admin1', password='admin123', balance=0.0, role='admin', created_by='system', owner_name='المشرف العام'))
    if not RevealAndWinGlobalState.query.get(1):
        db.session.add(RevealAndWinGlobalState(id=1, total_spins=0))
    if not EmpireGlobalState.query.get(1):
        db.session.add(EmpireGlobalState(id=1, last_winning_number=0, draw_timestamp=0.0, last_winner_info='لا يوجد فائز سابق بعد'))
    db.session.commit()

TRANSLATIONS = {
    'ar': {
        'dir': 'rtl', 'title': 'امبراطورية الأرقام الملكية', 'subtitle': 'منصة الألعاب التفاعلية الفائقة 12D',
        'login': 'دخول للبرنامج', 'username': 'اسم المستخدم', 'password': 'كلمة المرور', 'balance': 'الرصيد',
        'recharge': 'شحن رصيد', 'withdraw': 'سحب رصيد', 'change_pass': 'تغيير الباسورد', 'logout': 'خروج',
        'dashboard': 'لوحة التحكم', 'back_dash': '🏠 الرئيسية', 'customers': 'الزبائن', 'accounting': 'المحاسبة والخزنة',
        'game_control': '🎮 إدارة الألعاب', 'chat': '💬 الدردشة الفورية',
        'game1': 'الرقم الحنون', 'game2': 'روليت الحظ', 'game3': 'إمبراطورية الأرقام', 'game4': 'عجلة الحظ', 'game5': 'اكشف واربح', 'game6': 'رمي السهم المتحركة',
        'cost': 'التكلفة', 'prize': 'الجائزة', 'book': 'حجز', 'cancel': 'تراجع', 'booked': 'محجوز',
        'spin': 'تدوير العجلة', 'draw_now': 'اسحب الآن'
    },
    'en': {
        'dir': 'ltr', 'title': 'Royal Empire of Numbers', 'subtitle': 'Super Interactive 12D Gaming Platform',
        'login': 'Login', 'username': 'Username', 'password': 'Password', 'balance': 'Balance',
        'recharge': 'Recharge', 'withdraw': 'Withdraw', 'change_pass': 'Change Password', 'logout': 'Logout',
        'dashboard': 'Dashboard', 'back_dash': '🏠 Home', 'customers': 'Customers', 'accounting': 'Vault & Accounting',
        'game_control': '🎮 Game Control', 'chat': '💬 Live Chat',
        'game1': 'The Tender Number', 'game2': 'Lucky Roulette', 'game3': 'Empire of Numbers', 'game4': 'Wheel of Fortune', 'game5': 'Reveal & Win', 'game6': 'Animated Arrow Throw',
        'cost': 'Cost', 'prize': 'Prize', 'book': 'Book', 'cancel': 'Cancel', 'booked': 'Booked',
        'spin': 'Spin Wheel', 'draw_now': 'Draw Now'
    }
}

def get_t():
    lang = session.get('lang', 'ar')
    if lang not in TRANSLATIONS: lang = 'ar'
    return TRANSLATIONS[lang]

def get_lang_bar():
    curr = session.get('lang', 'ar')
    ar_sel = 'selected' if curr == 'ar' else ''
    en_sel = 'selected' if curr == 'en' else ''
    return f"""
<div style="padding: 12px 30px; background: rgba(15, 18, 30, 0.95); display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid rgba(255,215,0,0.3); flex-wrap: wrap; gap: 10px; box-sizing: border-box; width: 100%; box-shadow: 0 4px 20px rgba(0,0,0,0.5);">
    <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
        <select onchange="location.href='/set_lang/' + this.value" style="background:#1a1c29; color:#ffd700; border:1px solid #ffd700; padding:6px 12px; border-radius:8px; font-weight:bold; cursor:pointer;">
            <option value="ar" {ar_sel}>العربية 🇸🇦</option>
            <option value="en" {en_sel}>English 🇬🇧</option>
        </select>
        <a href="javascript:location.reload();" title="تحديث الصفحة" style="background: rgba(255,215,0,0.1); border: 1px solid #ffd700; color:#ffd700; padding: 6px 14px; text-decoration:none; border-radius:8px; font-weight:bold; font-size:14px; display: flex; align-items: center; gap: 5px;">🔄 تحديث</a>
    </div>
    <div style="display:flex; gap:15px; align-items:center; flex-wrap: wrap;">
        <div style="background:rgba(6,95,70,0.9); color:#34d399; padding:6px 16px; border-radius:10px; font-weight:900; font-size:14px; border:1px solid #34d399;">الرصيد: <span id="globalLiveBalance">...</span> USDD</div>
        <a href="/chat" style="color:#38bdf8; text-decoration:none; font-weight:bold; font-size:14px;">💬 الدعم والدردشة</a>
        <a href="/dashboard" style="color:#ffd700; text-decoration:none; font-weight:bold; font-size:14px;">🏠 الرئيسية</a>
    </div>
</div>
<script>
    setInterval(() => {{
        fetch('/api/sync_balance').then(res => res.json()).then(data => {{
            let b1 = document.getElementById('liveBalance');
            let b2 = document.getElementById('globalLiveBalance');
            if(b1 && b1.innerText !== String(data.balance)) b1.innerText = data.balance;
            if(b2 && b2.innerText !== String(data.balance)) b2.innerText = data.balance;
        }}).catch(err => {{}});
    }}, 2000);
</script>
"""

@app.route('/sw.js')
def service_worker():
    return app.response_class("self.addEventListener('fetch', function(event) { });", mimetype='application/javascript')

def get_unified_math_outcome(game_name, supervisor_scope, player_choices, min_val, max_val):
    future = GameFutureDraw.query.filter_by(supervisor_scope=supervisor_scope, game_name=game_name).order_by(GameFutureDraw.round_index.asc()).first()
    if not future and supervisor_scope != 'global':
        future = GameFutureDraw.query.filter_by(supervisor_scope='global', game_name=game_name).order_by(GameFutureDraw.round_index.asc()).first()
    if future:
        win_num = future.winning_number
        db.session.delete(future)
        db.session.commit()
        return win_num

    total_bets = db.session.query(db.func.sum(FinancialLog.amount)).filter(FinancialLog.action_type.like(f'%مبيع رهان%{game_name}%')).scalar() or 0.0
    total_payouts = db.session.query(db.func.sum(FinancialLog.amount)).filter(FinancialLog.action_type.like(f'%جائزة%{game_name}%')).scalar() or 0.0

    if total_bets < 10.0:
        if player_choices and random.random() < 0.70:
            return random.choice(player_choices)
        return random.randint(min_val, max_val)

    current_payout_ratio = total_payouts / total_bets if total_bets > 0 else 0.0
    if current_payout_ratio > 0.70:
        safe_non_winning = [x for x in range(min_val, max_val + 1) if x not in player_choices]
        return random.choice(safe_non_winning) if safe_non_winning else random.randint(min_val, max_val)
    else:
        if player_choices and random.random() < 0.75:
            return random.choice(player_choices)
        return random.randint(min_val, max_val)

LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ t.title }} - 12D</title>
</head>
<body style="font-family:'Segoe UI', Tahoma, sans-serif; background:radial-gradient(circle at center, #1a1c29 0%, #0b0f19 100%); color:#fff; display:flex; justify-content:center; align-items:center; min-height:90vh; margin:0; box-sizing:border-box; padding:15px;">
    <div style="background:rgba(20, 24, 38, 0.95); padding:40px 30px; border-radius:25px; width:100%; max-width:380px; text-align:center; border:2px solid rgba(255,215,0,0.6); box-shadow: 0 20px 50px rgba(0,0,0,0.9); box-sizing:border-box;">
        <h2 style="color:#ffd700; margin-top:0; font-size:24px;">👑 {{ t.title }}</h2>
        {% if error %}<div style="color:#ef4444; margin-bottom:15px; font-weight:bold;">{{ error }}</div>{% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="{{ t.username }}" required style="width:100%; padding:14px; margin:10px 0; border-radius:12px; background:rgba(10, 13, 22, 0.9); color:#fff; border:1px solid #555; box-sizing:border-box; font-size:15px;">
            <input type="password" name="password" placeholder="{{ t.password }}" required style="width:100%; padding:14px; margin:10px 0; border-radius:12px; background:rgba(10, 13, 22, 0.9); color:#fff; border:1px solid #555; box-sizing:border-box; font-size:15px;">
            <button type="submit" style="width:100%; padding:14px; background:linear-gradient(135deg, #ffd700, #ff8c00); color:#000; font-weight:900; border:none; border-radius:12px; cursor:pointer; font-size:17px; margin-top:5px; box-shadow: 0 5px 15px rgba(255,215,0,0.3);">{{ t.login }}</button>
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
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: radial-gradient(circle at center, #151928 0%, #070a12 100%); color: #fff; margin: 0; padding: 15px; min-height: 100vh; box-sizing: border-box; }
        .header { display: flex; justify-content: space-between; align-items: center; background: rgba(20, 24, 38, 0.95); padding: 15px 20px; border-radius: 18px; border-bottom: 3px solid #ffd700; flex-wrap: wrap; gap: 15px; box-sizing: border-box; width: 100%; box-shadow: 0 10px 30px rgba(0,0,0,0.6); }
        .action-bar { display: flex; justify-content: center; align-items: center; gap: 15px; margin: 20px auto; max-width: 950px; flex-wrap: wrap; background: rgba(20,24,38,0.95); padding: 15px; border-radius: 20px; border: 2px solid rgba(255,215,0,0.4); box-sizing: border-box; width: 100%; }
        .dropdown { position: relative; display: inline-block; }
        .drop-btn { background: linear-gradient(135deg, #22c55e, #15803d); color: #fff; padding: 10px 20px; font-weight: 900; border: none; border-radius: 12px; cursor: pointer; font-size: 15px; }
        .drop-btn.withdraw { background: linear-gradient(135deg, #ef4444, #991b1b); }
        .dropdown-content { display: none; position: absolute; background: #1a1c29; min-width: 220px; box-shadow: 0px 8px 16px rgba(0,0,0,0.5); z-index: 10; border-radius: 12px; border: 1px solid #ffd700; overflow: hidden; right: 0; }
        .dropdown-content a { color: #fff; padding: 12px 16px; text-decoration: none; display: block; text-align: right; cursor: pointer; font-size: 14px; }
        .dropdown-content a:hover { background: #2d3748; color: #ffd700; }
        .redeem-box { display: flex; gap: 8px; align-items: center; background: #0a0d16; padding: 6px 12px; border-radius: 12px; border: 1px solid #ffd700; box-sizing: border-box; }
        .redeem-box input { background: transparent; border: none; color: #fff; padding: 5px; outline: none; font-size: 14px; width: 140px; }
        .redeem-box button { background: #ffd700; color: #000; border: none; padding: 6px 12px; border-radius: 8px; font-weight: 900; cursor: pointer; }
        .icons-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; max-width: 1000px; margin: 20px auto; box-sizing: border-box; width: 100%; }
        @media (max-width: 768px) { .icons-grid { grid-template-columns: repeat(1, 1fr); max-width: 100%; padding: 0 5px; } }
        .icon-card { background: rgba(25,30,48,0.95); border: 3px solid rgba(184,134,11,0.6); border-radius: 24px; padding: 25px 10px; text-align: center; text-decoration: none; box-shadow: 0 15px 35px rgba(0,0,0,0.8); transition: 0.3s; box-sizing: border-box; display: block; width: 100%; }
        .icon-card:hover { border-color: #ffd700; transform: translateY(-5px); box-shadow: 0 20px 40px rgba(255,215,0,0.2); }
        .icon-logo { font-size: 45px; margin-bottom: 8px; }
        .icon-title { color: #ffd700; font-size: 17px; font-weight: 900; }
    </style>
</head>
<body>
    {{ lang_bar | safe }}
    <div class="header">
        <div style="display:flex; gap:15px; align-items:center; flex-wrap:wrap;">
            <h2 style="color:#ffd700; margin:0; font-size:20px;">👑 {{ t.title }}</h2>
            <div style="background:rgba(15,20,32,0.9); padding:6px 12px; border-radius:10px; font-size:14px;">👤 <b>{{ username }}</b> {% if role == 'supervisor' %}<span style="color:#38bdf8;">(مشرف مجموعة مستقلة)</span>{% endif %}</div>
            <div style="background:rgba(6,95,70,0.8); color:#34d399; padding:6px 15px; border-radius:10px; font-weight:900; font-size:14px;">{{ t.balance }}: <span id="liveBalance">{{ balance }}</span> USDD</div>
        </div>
        <div style="display:flex; gap:10px; flex-wrap:wrap;">
            {% if role == 'admin' %}
                <a href="/admin_supervisors" style="background:#22c55e; color:#000; padding:8px 12px; text-decoration:none; border-radius:10px; font-weight:900; font-size:13px;">👥 إدارة المشرفين والتقارير</a>
                <a href="/admin_game_control" style="background:#38bdf8; color:#000; padding:8px 12px; text-decoration:none; border-radius:10px; font-weight:900; font-size:13px;">🎮 لوحة تحكم الألعاب (10 قنوات)</a>
            {% elif role == 'supervisor' %}
                <a href="/supervisor_dashboard" style="background:#22c55e; color:#000; padding:8px 14px; text-decoration:none; border-radius:10px; font-weight:900; font-size:13px;">📊 لوحة تحكم مجموعتك وصندوقك</a>
            {% endif %}
            <a href="/logout" style="background:#ef4444; color:#fff; padding:8px 12px; text-decoration:none; border-radius:10px; font-weight:900; font-size:13px;">{{ t.logout }}</a>
        </div>
    </div>

    {% if role == 'user' %}
    <div class="action-bar">
        <div class="redeem-box">
            <form method="POST" style="display:flex; gap:5px; margin:0;">
                <input type="hidden" name="action" value="redeem_card">
                <input type="text" name="card_code" placeholder="كود الشحن..." required>
                <button type="submit">تفعيل</button>
            </form>
        </div>
    </div>
    {% endif %}

    {% if msg %}<div style="background:#065f46; color:#34d399; padding:12px; border-radius:12px; max-width:600px; margin:15px auto; text-align:center; font-weight:900; font-size:14px;">{{ msg }}</div>{% endif %}

    <div class="icons-grid">
        <a href="/game_golden_number" class="icon-card"><div class="icon-logo">🏆</div><div class="icon-title">{{ t.game1 }}</div></a>
        <a href="/game_roulette" class="icon-card"><div class="icon-logo">🎰</div><div class="icon-title">{{ t.game2 }}</div></a>
        <a href="/game_numbers_empire" class="icon-card"><div class="icon-logo">🏛️</div><div class="icon-title">{{ t.game3 }}</div></a>
        <a href="/game_number_wheel" class="icon-card"><div class="icon-logo">🎡</div><div class="icon-title">{{ t.game4 }}</div></a>
        <a href="/game_reveal_and_win" class="icon-card"><div class="icon-logo">🎟️</div><div class="icon-title">{{ t.game5 }}</div></a>
        <a href="/game_arrow_wheel" class="icon-card"><div class="icon-logo">🎯</div><div class="icon-title">{{ t.game6 }}</div></a>
    </div>
</body>
</html>
"""

# --- لوحة تحكم المشرف المستقل (صندوقه الخاص + لاعبيه + تقاريره) ---
SUPERVISOR_DASHBOARD_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة مجموعة المشرف المستقل - 12D</title>
    <style>
        body { font-family: Tahoma; background: #151928; color: #fff; padding: 15px; text-align: center; box-sizing: border-box; margin:0; }
        .box { background: rgba(25,30,48,0.95); padding: 20px; border-radius: 18px; max-width: 800px; margin: 15px auto; border: 2px solid #ffd700; text-align: right; box-sizing: border-box; box-shadow: 0 10px 30px rgba(0,0,0,0.6); }
        input, select { width: 100%; padding: 10px; margin: 6px 0; border-radius: 8px; background: #0a0d16; color: #fff; border: 1px solid #444; box-sizing: border-box; font-size: 14px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }
        th, td { border: 1px solid #444; padding: 8px; text-align: center; }
        th { background: #0a0d16; color: #ffd700; }
        .grid-panels { display: flex; gap: 15px; justify-content: center; flex-wrap: wrap; max-width: 950px; margin: 0 auto; box-sizing: border-box; }
    </style>
</head>
<body>
    {{ lang_bar | safe }}
    <h2 style="color:#ffd700; font-size:22px;">📊 لوحة إدارة مجموعة المشرف: {{ supervisor.username }}</h2>
    <div style="font-size:20px; font-weight:bold; color:#34d399; margin:10px 0;">💰 رصيد صندوقك المالي الخاص: {{ supervisor.balance }} USDD</div>
    <a href="/dashboard" style="background:#38bdf8; color:#000; padding:8px 16px; text-decoration:none; border-radius:10px; font-weight:900; font-size:13px;">الرئيسية والألعاب</a>

    {% if msg %}<div style="background:#065f46; color:#34d399; padding:10px; border-radius:10px; margin:15px auto; max-width:600px; font-weight:bold; font-size:14px;">{{ msg }}</div>{% endif %}

    <div class="grid-panels">
        <!-- إنشاء لاعب -->
        <div class="box" style="flex: 1; min-width: 320px;">
            <h3 style="color:#ffd700; margin-top:0; font-size:17px; text-align:center;">➕ إنشاء حساب لاعب جديد لمجموعتك</h3>
            <form method="POST">
                <input type="hidden" name="action" value="create_player">
                <label>اسم المستخدم:</label>
                <input type="text" name="username" required placeholder="اسم اللاعب...">
                <label>كلمة المرور:</label>
                <input type="password" name="password" required placeholder="كلمة المرور...">
                <label>الرصيد الابتدائي:</label>
                <input type="number" name="balance" min="0" value="0" step="0.5" required>
                <button type="submit" style="background:#22c55e; color:#000; font-weight:900; padding:12px; border:none; border-radius:8px; width:100%; cursor:pointer; margin-top:10px;">إنشاء اللاعب فوراً</button>
            </form>
        </div>

        <!-- بيع وشراء رصيد من صندوق المشرف -->
        <div class="box" style="flex: 1; min-width: 320px; border-color:#38bdf8;">
            <h3 style="color:#38bdf8; margin-top:0; font-size:17px; text-align:center;">💳 بيع أو سحب رصيد من صندوقك</h3>
            <form method="POST">
                <input type="hidden" name="action" value="transfer_balance">
                <label>اختر اللاعب التابع لك:</label>
                <select name="target_player" required>
                    <option value="">اختر اللاعب</option>
                    {% for p in players %}
                    <option value="{{ p.username }}">{{ p.username }} (رصيده: {{ p.balance }})</option>
                    {% endfor %}
                </select>
                <label>المبلغ (USDD):</label>
                <input type="number" name="amount" min="1" required placeholder="المبلغ...">
                <label>نوع الحركة المالية:</label>
                <select name="transfer_type" required>
                    <option value="sell">بيع رصيد لللاعب (يخصم من صندوقك)</option>
                    <option value="buyback">سحب رصيد من اللاعب (يُضاف لصندوقك)</option>
                </select>
                <button type="submit" style="background:#38bdf8; color:#000; font-weight:900; padding:12px; border:none; border-radius:8px; width:100%; cursor:pointer; margin-top:10px;">تنفيذ العملية المالية</button>
            </form>
        </div>
    </div>

    <!-- قائمة اللاعبين التابعين للمشرف -->
    <div class="box" style="max-width: 950px;">
        <h3 style="color:#ffd700; font-size:17px; text-align:center;">📋 لاعبو مجموعتك الخاصة وكلمات مرورهم</h3>
        <table>
            <tr><th>اسم المستخدم</th><th>كلمة المرور</th><th>الرصيد الحالي</th><th>تاريخ الإنشاء</th></tr>
            {% for p in players %}
            <tr><td><b>{{ p.username }}</b></td><td style="color:#38bdf8; font-family:monospace;">{{ p.password }}</td><td style="color:#34d399;">{{ p.balance }} USDD</td><td>{{ p.created_by }}</td></tr>
            {% endfor %}
        </table>
    </div>

    <!-- تقارير وحركات لاعبي المجموعة مع فلتر -->
    <div class="box" style="max-width: 950px; border-color:#a78bfa;">
        <h3 style="color:#a78bfa; font-size:17px; text-align:center;">📊 تقارير وحركات لاعبي مجموعتك</h3>
        <form method="GET" style="display:flex; gap:10px; justify-content:center; align-items:center; flex-wrap:wrap; margin-bottom:15px;">
            <label style="font-weight:bold;">فلترة حسب اللاعب:</label>
            <select name="player_filter" onchange="this.form.submit()" style="min-width:200px;">
                <option value="">جميع لاعبي مجموعتي</option>
                {% for p in players %}
                <option value="{{ p.username }}" {% if selected_player == p.username %}selected{% endif %}>{{ p.username }}</option>
                {% endfor %}
            </select>
            {% if selected_player %}
            <a href="/supervisor_dashboard" style="background:#ef4444; color:#fff; padding:8px 14px; text-decoration:none; border-radius:8px; font-size:13px;">إلغاء الفلتر</a>
            {% endif %}
        </form>
        <div style="overflow-x:auto;">
            <table>
                <tr><th>#</th><th>اسم اللاعب</th><th>اللعبة</th><th>تفاصيل الرهان / الرقم</th><th>المبلغ</th><th>النتيجة</th><th>التوقيت</th></tr>
                {% for log in logs %}
                <tr>
                    <td>{{ log.id }}</td>
                    <td style="color:#ffd700;"><b>{{ log.username }}</b></td>
                    <td style="color:#38bdf8;">{{ log.game_name }}</td>
                    <td>{{ log.bet_details }}</td>
                    <td style="color:#34d399;">{{ log.amount }} USDD</td>
                    <td><span style="padding:3px 8px; border-radius:5px; background:{% if log.outcome == 'ربح' %}rgba(34,197,94,0.3){% else %}rgba(239,68,68,0.3){% endif %};">{{ log.outcome }}</span></td>
                    <td style="font-size:11px; color:#aaa;">{{ log.timestamp }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </div>
</body>
</html>
"""

# --- لوحة الآدمن الخاصة بالمشرفين وإدارة 10 قنوات تحكم ---
ADMIN_SUPERVISORS_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>إدارة المشرفين والتقارير الشاملة - الآدمن</title>
    <style>
        body { font-family: Tahoma; background: #151928; color: #fff; padding: 15px; text-align: center; box-sizing: border-box; margin:0; }
        .box { background: rgba(25,30,48,0.95); padding: 20px; border-radius: 18px; max-width: 950px; margin: 15px auto; border: 2px solid #ffd700; text-align: right; box-sizing: border-box; box-shadow: 0 10px 30px rgba(0,0,0,0.6); }
        input, select { width: 100%; padding: 10px; margin: 6px 0; border-radius: 8px; background: #0a0d16; color: #fff; border: 1px solid #444; box-sizing: border-box; font-size: 14px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }
        th, td { border: 1px solid #444; padding: 8px; text-align: center; }
        th { background: #0a0d16; color: #ffd700; }
    </style>
</head>
<body>
    {{ lang_bar | safe }}
    <h2 style="color:#ffd700; font-size:22px;">👥 إدارة المشرفين المستقلين وأرصدتهم</h2>
    <div style="font-size:18px; font-weight:bold; color:#34d399; margin:10px 0;">🏦 الخزنة المركزية العامة: {{ vault_balance }} USDD</div>
    <a href="/dashboard" style="background:#38bdf8; color:#000; padding:8px 16px; text-decoration:none; border-radius:10px; font-weight:900; font-size:13px;">الرئيسية</a>

    {% if msg %}<div style="background:#065f46; color:#34d399; padding:10px; border-radius:10px; margin:15px auto; max-width:600px; font-weight:bold; font-size:14px;">{{ msg }}</div>{% endif %}

    <div class="box">
        <h3 style="color:#ffd700; margin-top:0; font-size:17px; text-align:center;">➕ إنشاء مشرف جديد (مجموعة مستقلة)</h3>
        <form method="POST">
            <input type="hidden" name="action" value="create_supervisor">
            <label>اسم المستخدم للمشرف:</label>
            <input type="text" name="username" required placeholder="اسم المشرف...">
            <label>كلمة المرور:</label>
            <input type="password" name="password" required placeholder="كلمة المرور...">
            <label>اسم الوكيل أو المحل:</label>
            <input type="text" name="owner_name" placeholder="اسم المحل...">
            <button type="submit" style="background:#22c55e; color:#000; font-weight:900; padding:12px; border:none; border-radius:8px; width:100%; cursor:pointer; margin-top:10px;">إنشاء المشرف وصندوقه</button>
        </form>
    </div>

    <div class="box" style="border-color:#38bdf8;">
        <h3 style="color:#38bdf8; margin-top:0; font-size:17px; text-align:center;">💳 تمويل رصيد لصندوق المشرف من الخزنة العامة</h3>
        <form method="POST">
            <input type="hidden" name="action" value="fund_supervisor">
            <label>اختر المشرف:</label>
            <select name="target_sup" required>
                <option value="">اختر المشرف</option>
                {% for s in supervisors %}
                <option value="{{ s.username }}">{{ s.username }} (صندوقه الحالي: {{ s.balance }})</option>
                {% endfor %}
            </select>
            <label>المبلغ (USDD):</label>
            <input type="number" name="amount" min="1" required placeholder="المبلغ...">
            <button type="submit" style="background:#38bdf8; color:#000; font-weight:900; padding:12px; border:none; border-radius:8px; width:100%; cursor:pointer; margin-top:10px;">إتمام التمويل من الخزنة</button>
        </form>
    </div>

    <!-- جدول المشرفين ولاعبيهم وتفاصيلهم الكاملة -->
    <div class="box" style="border-color:#a78bfa;">
        <h3 style="color:#a78bfa; font-size:17px; text-align:center;">📋 تفاصيل المشرفين، صناديقهم، ولاعبيهم وأرصدتهم</h3>
        <table>
            <tr><th>المشرف / المحل</th><th>رصيد صندوقه</th><th>اللاعبون التابعون له</th><th>أرصدة وكلمات مرور لاعبيه</th></tr>
            {% for s in supervisors %}
            <tr>
                <td><b>{{ s.username }}</b><br><span style="font-size:11px; color:#aaa;">{{ s.owner_name }}</span></td>
                <td style="color:#34d399; font-weight:bold;">{{ s.balance }} USDD</td>
                <td>{{ s.player_count }} لاعبين</td>
                <td style="text-align:right; font-size:12px;">
                    {% for p in s.players %}
                    <div>👤 <b>{{ p.username }}</b> | كلمة المرور: <span style="color:#38bdf8; font-family:monospace;">{{ p.password }}</span> | الرصيد: <span style="color:#34d399;">{{ p.balance }}</span></div>
                    {% else %}
                    <span style="color:#aaa;">لا يوجد لاعبون بعد</span>
                    {% endfor %}
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

# --- غرفة إدارة الألعاب لـ 10 مشرفين ---
ADMIN_GAME_CONTROL_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>إدارة الألعاب (10 قنوات مشرفين) - الآدمن</title>
    <style>
        body { font-family: Tahoma; background: #151928; color: #fff; padding: 15px; text-align: center; box-sizing:border-box; margin:0; }
        .panel { background: rgba(25,30,48,0.95); padding: 20px; border-radius: 18px; border: 2px solid #ffd700; max-width: 850px; margin: 15px auto; text-align: right; box-sizing: border-box; box-shadow: 0 10px 30px rgba(0,0,0,0.6); }
        input, select { width: 100%; padding: 10px; margin: 6px 0; background: #0a0d16; color: #fff; border: 1px solid #444; border-radius: 8px; box-sizing: border-box; font-size:14px; }
    </style>
</head>
<body>
    {{ lang_bar | safe }}
    <h2 style="font-size:22px;">🎮 غرفة إدارة الألعاب (التحكم المستقل لـ 10 مشرفين وعام)</h2>
    <p style="color:#94a3b8; font-size:14px;">حدد المشرف المستهدف أو العام، ثم برمج الأرقام الرابحة بدقة لكل صفحة مجموعة بمفردها.</p>
    <a href="/dashboard" style="background:#3b82f6; color:#fff; padding:8px 16px; text-decoration:none; border-radius:10px; font-weight:900; font-size:14px;">الرئيسية</a>
    
    {% if msg %}<div style="background:#065f46; color:#34d399; padding:10px; border-radius:10px; margin:12px auto; max-width:600px; font-weight:bold; font-size:14px;">{{ msg }}</div>{% endif %}
    
    <div class="panel" style="border-color: #ffd700;">
        <h3 style="color: #ffd700; margin-top:0; font-size:18px;">🎯 برمجة الأرقام الرابحة حسب المشرف أو القناة</h3>
        <form method="POST">
            <label>اختر نطاق المشرف (القناة):</label>
            <select name="supervisor_scope" required>
                <option value="global">🌐 عام لجميع المنصة</option>
                {% for s in supervisors %}
                <option value="{{ s.username }}">👑 مشرف المجموعة: {{ s.username }}</option>
                {% endfor %}
            </select>

            <label>اختر اللعبة:</label>
            <select name="game_name" required>
                <option value="golden">الرقم الحنون (1-50)</option>
                <option value="roulette">روليت الحظ (0-36)</option>
                <option value="empire">إمبراطورية الأرقام (1-5)</option>
                <option value="wheel">عجلة الحظ (1-20)</option>
                <option value="arrow_wheel">رمي السهم المتحركة</option>
            </select>

            <label>رقم الجولة القادمة (1 إلى 50):</label>
            <input type="number" name="round_index" min="1" max="50" required placeholder="رقم الجولة...">
            
            <label>الرقم الفائز المبرمج:</label>
            <input type="number" name="winning_number" required placeholder="الرقم الفائز...">
            
            <button type="submit" style="background:#ffd700; color:#000; padding:12px; font-weight:900; border:none; border-radius:8px; width:100%; cursor:pointer; margin-top:12px; font-size:15px;">حفظ وتثبيت الرقم الفائز لهذه القناة</button>
        </form>
    </div>
</body>
</html>
"""

# Include all 6 game templates exactly as before (GAME_GOLDEN_PAGE, GAME_ROULETTE_PAGE, GAME_NUMBERS_EMPIRE_PAGE, GAME_NUMBER_WHEEL_PAGE, GAME_REVEAL_PAGE, GAME_ARROW_WHEEL_PAGE, CHAT_PAGE, ADMIN_CHATS_PAGE)
# To keep the script self-contained and fully working, we include them below:

GAME_GOLDEN_PAGE = """
<!DOCTYPE html>
<html lang="{{ lang_key }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ t.game1 }}</title>
    <style>
        body { font-family: Tahoma; background: #151928; color: #fff; padding: 10px; text-align: center; margin: 0; box-sizing: border-box; }
        .card { background: rgba(25,30,48,0.95); border: 3px solid #ffd700; padding: 20px; border-radius: 25px; max-width: 950px; margin: 10px auto; box-shadow: 0 20px 50px rgba(0,0,0,0.8); box-sizing: border-box; width: 100%; }
        .header-box { background: linear-gradient(135deg, #1e3a8a, #1e1b4b); border: 2px solid #38bdf8; padding: 12px; border-radius: 16px; margin-bottom: 15px; box-sizing: border-box; }
        .draw-screen-box { background: #000; border: 3px solid #ffd700; padding: 10px; border-radius: 16px; margin-bottom: 10px; display: inline-block; min-width: 200px; max-width: 100%; box-sizing: border-box; }
        .slot-screen { font-size: 38px; font-weight: 900; color: #ffd700; letter-spacing: 2px; }
        .winner-msg { font-size: 15px; font-weight: 900; color: #34d399; margin-bottom: 12px; min-height: 22px; }
        .grid { display: grid; grid-template-columns: repeat(10, 1fr); gap: 6px; margin-top: 12px; box-sizing: border-box; width: 100%; }
        @media(max-width: 768px){ .grid { grid-template-columns: repeat(5, 1fr); gap: 5px; } }
        .cell { background: linear-gradient(145deg, #7c3aed, #4c1d95); border: 2px solid #a78bfa; border-radius: 10px; aspect-ratio: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; font-weight: 900; cursor: pointer; color: #fff; font-size: 14px; transition: 0.2s; box-sizing: border-box; width: 100%; }
        .cell:hover { border-color: #ffd700; transform: scale(1.03); }
        .cell.booked { background: linear-gradient(145deg, #7f1d1d, #450a0a) !important; border-color: #ef4444 !important; cursor: not-allowed; }
        .cell.my { background: linear-gradient(145deg, #1e3a8a, #172554) !important; border-color: #3b82f6 !important; }
        .cell.winner-glow { background: #fbbf24 !important; border: 3px solid #fff !important; box-shadow: 0 0 20px #ffd700; color: #000 !important; transform: scale(1.1); }
        .player-info-box { background: rgba(15,20,32,0.9); border: 2px solid #34d399; padding: 10px; border-radius: 12px; margin-top: 15px; text-align: right; box-sizing: border-box; font-size: 14px; }
    </style>
</head>
<body>
    {{ lang_bar | safe }}
    <div class="card">
        <div class="header-box">
            <h2 style="color: #ffd700; margin: 0 0 6px 0; font-size: 18px;">احجز رقم ب 2 usdd واربح 70 usdd فورا</h2>
            <p style="color: #f8fafc; margin: 0; font-size: 14px; font-weight: bold;">مجموعة المشرف التابع له: {{ supervisor_name }}</p>
        </div>
        <div class="draw-screen-box"><div id="slotScreen" class="slot-screen">--</div></div>
        <div id="winnerAnnouncement" class="winner-msg"></div>
        <div class="grid" id="numbersGrid">
            {% for i in range(1, 51) %}
                {% if i in bookings %}
                    {% if bookings[i] == username %}
                        <button type="button" onclick="handleAction('cancel', {{ i }})" class="cell my" id="cell_{{ i }}">{{ i }}<br><span style="font-size:9px; color:#93c5fd;">تراجع</span></button>
                    {% else %}
                        <div class="cell booked" id="cell_{{ i }}">{{ i }}<br><span style="font-size:8px; color:#fca5a5;">{{ bookings[i] }}</span></div>
                    {% endif %}
                {% else %}
                    <button type="button" onclick="handleAction('book', {{ i }})" class="cell" id="cell_{{ i }}">{{ i }}</button>
                {% endif %}
            {% endfor %}
        </div>
        <div class="player-info-box">
            <h4 style="color: #34d399; margin-top: 0; font-size: 14px;">📋 لوحة حجوزاتي</h4>
            <p style="margin: 4px 0;"><b>أرقامك المحجوزة:</b> <span style="color: #ffd700;">{{ my_nums_str }}</span></p>
            <p style="margin: 4px 0;"><b>القيمة المخصومة:</b> <span style="color: #38bdf8;">{{ my_total_cost }} USDD</span></p>
        </div>
        {% if role == 'admin' or role == 'supervisor' %}
            <div style="margin-top: 20px; text-align: center;">
                <button type="button" onclick="triggerDraw()" style="background: linear-gradient(135deg, #22c55e, #15803d); color: #fff; font-weight: 900; padding: 12px 25px; border: none; border-radius: 12px; cursor: pointer; font-size: 16px;">⚡ اسحب الآن لمجموعتك</button>
            </div>
        {% endif %}
    </div>
    <script>
        function handleAction(actionType, numberVal) {
            let fd = new FormData();
            fd.append('action_type', actionType);
            fd.append('number', numberVal);
            fetch('/game_golden_number', { method: 'POST', body: fd }).then(res => res.json()).then(data => {
                if(data.success) { location.reload(); } else { alert(data.msg || "حدث خطأ!"); }
            });
        }
        function triggerDraw() {
            let fd = new FormData(); fd.append('action_type', 'admin_draw');
            fetch('/game_golden_number', { method: 'POST', body: fd }).then(res => res.json()).then(data => {
                if(data.winning_number) { runDrawAnimation(data.winning_number); } else if(data.msg) { alert(data.msg); }
            });
        }
        function runDrawAnimation(winningNum) {
            let screen = document.getElementById('slotScreen');
            let ann = document.getElementById('winnerAnnouncement');
            let counter = 0;
            let interval = setInterval(() => {
                screen.innerText = '#' + Math.floor(Math.random() * 50 + 1);
                counter++;
                if(counter > 22) {
                    clearInterval(interval);
                    screen.innerText = '#' + winningNum;
                    ann.innerText = `مبروك ربحت 70 usdd للرقم ${winningNum}`;
                    let winCell = document.getElementById('cell_' + winningNum);
                    if(winCell) { winCell.className = "cell winner-glow"; }
                    setTimeout(() => { location.reload(); }, 5000);
                }
            }, 90);
        }
    </script>
</body>
</html>
"""

GAME_ROULETTE_PAGE = """
<!DOCTYPE html>
<html lang="{{ lang_key }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ t.game2 }}</title>
    <style>
        body { font-family: Tahoma; background: #151928; color: #fff; padding: 10px; text-align: center; margin: 0; box-sizing: border-box; }
        .card { background: rgba(25,30,48,0.95); border: 3px solid #ffd700; padding: 15px; border-radius: 25px; max-width: 900px; margin: 10px auto; box-shadow: 0 20px 50px rgba(0,0,0,0.8); box-sizing: border-box; width: 100%; }
        .timer-box { font-size: 16px; font-weight: 900; color: #ffd700; background: #000; padding: 6px 12px; border-radius: 12px; border: 2px solid #38bdf8; margin-bottom: 10px; display: inline-block; }
        .spin-screen { font-size: 30px; font-weight: 900; color: #ffd700; background: #000; padding: 8px 15px; border-radius: 12px; border: 3px solid #b8860b; display: inline-block; margin-bottom: 10px; letter-spacing: 2px; }
        .total-bet-display { background: rgba(255,215,0,0.15); border: 2px solid #ffd700; padding: 8px 15px; border-radius: 12px; font-weight: 900; color: #ffd700; margin: 8px auto; max-width: 320px; font-size: 15px; box-sizing: border-box; width: 100%; }
        .roulette-table { display: grid; grid-template-columns: 45px repeat(12, 1fr); grid-template-rows: repeat(3, 45px); gap: 3px; max-width: 100%; overflow-x: auto; margin: 12px auto; background: #065f46; padding: 8px; border-radius: 14px; border: 3px solid #b8860b; box-sizing: border-box; }
        .r-cell { display: flex; flex-direction: column; align-items: center; justify-content: center; font-weight: bold; border-radius: 5px; cursor: pointer; color: #fff; font-size: 14px; transition: 0.15s; border: 1px solid rgba(255,255,255,0.2); box-sizing: border-box; }
        .r-cell.zero { grid-row: span 3; background: #047857; border-color: #ffd700; font-size: 18px; }
        .r-cell.red { background: #dc2626; }
        .r-cell.black { background: #111827; }
        .r-cell.selected { border: 2px solid #ffd700 !important; box-shadow: 0 0 8px #ffd700; }
        .r-cell.winner-highlight { background: #fbbf24 !important; color: #000 !important; border: 2px solid #fff !important; }
        .controls-grid { display: flex; gap: 6px; justify-content: center; flex-wrap: wrap; margin-bottom: 10px; box-sizing: border-box; }
        .btn-ctrl { padding: 8px 10px; font-weight: 900; border-radius: 8px; border: none; cursor: pointer; font-size: 12px; }
    </style>
</head>
<body>
    {{ lang_bar | safe }}
    <div class="card">
        <h2 style="color:#ffd700; margin-top:0; font-size: 20px;">🎰 روليت الحظ المستقلة</h2>
        <p style="font-size: 13px; margin: 5px 0;"><b>رصيدك: <span id="rouletteBal">{{ balance }}</span> USDD</b></p>
        <div><div id="timerBox" class="timer-box">⏳ وقت الرهان المتبقي: 15 ث</div></div>
        <div><div id="spinScreen" class="spin-screen">--</div></div>
        <div class="total-bet-display">🎯 إجمالي الرهان الحالي: <span id="currentTotalBet">0</span> USDD</div>
        <div id="rouletteMsg" style="font-weight:900; color:#34d399; margin-bottom:8px; font-size: 13px;">اختر أرقامك من الطاولة</div>
        
        <div class="roulette-table" id="rouletteTable">
            <div class="r-cell zero" onclick="toggleNum(0)" id="r_cell_0"><span>0</span><span id="r_mult_0" style="font-size:8px; color:#ffd700;">0$</span></div>
            {% set row1 = [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36] %}
            {% set row2 = [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35] %}
            {% set row3 = [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34] %}
            {% set red_list = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36] %}
            {% for n in row1 %}{% set is_red = n in red_list %}<div class="r-cell {{ 'red' if is_red else 'black' }}" onclick="toggleNum({{ n }})" id="r_cell_{{ n }}"><span>{{ n }}</span><span id="r_mult_{{ n }}" style="font-size:8px; color:#ffd700;">0$</span></div>{% endfor %}
            {% for n in row2 %}{% set is_red = n in red_list %}<div class="r-cell {{ 'red' if is_red else 'black' }}" onclick="toggleNum({{ n }})" id="r_cell_{{ n }}"><span>{{ n }}</span><span id="r_mult_{{ n }}" style="font-size:8px; color:#ffd700;">0$</span></div>{% endfor %}
            {% for n in row3 %}{% set is_red = n in red_list %}<div class="r-cell {{ 'red' if is_red else 'black' }}" onclick="toggleNum({{ n }})" id="r_cell_{{ n }}"><span>{{ n }}</span><span id="r_mult_{{ n }}" style="font-size:8px; color:#ffd700;">0$</span></div>{% endfor %}
        </div>
    </div>
    <script>
        let bets = {}; let timeLeft = 15; let gameActive = true;
        let timerInterval = setInterval(() => {
            timeLeft--;
            let tBox = document.getElementById('timerBox');
            if(tBox) tBox.innerText = `⏳ وقت الرهان: ${timeLeft} ث`;
            if(timeLeft <= 0) { clearInterval(timerInterval); gameActive = false; setTimeout(executeDraw, 2000); }
        }, 1000);
        function toggleNum(n) {
            if(!gameActive) { alert("انتهى وقت الرهان!"); return; }
            if(!bets[n]) bets[n] = 0;
            bets[n]++;
            fetch('/game_roulette_bet', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({action:'add', number:n})})
            .then(res => res.json()).then(d => {
                if(d.success) { document.getElementById('rouletteBal').innerText = d.balance; updateUI(); }
                else { bets[n]--; alert(d.msg || "رصيد غير كافي!"); }
            });
        }
        function updateUI() {
            let total = 0;
            for(let i=0; i<=36; i++) {
                let cell = document.getElementById('r_cell_' + i); let badge = document.getElementById('r_mult_' + i);
                if(bets[i] && bets[i] > 0) { cell.classList.add('selected'); badge.innerText = `x${bets[i]}`; total += bets[i]; }
                else { cell.classList.remove('selected'); badge.innerText = `0$`; }
            }
            document.getElementById('currentTotalBet').innerText = total;
        }
        function executeDraw() {
            fetch('/game_roulette_draw', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({bets: bets})})
            .then(res => res.json()).then(data => { if(data.success) { alert(data.msg); location.reload(); } });
        }
    </script>
</body>
</html>
"""

GAME_NUMBERS_EMPIRE_PAGE = """
<!DOCTYPE html>
<html lang="{{ lang_key }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ t.game3 }}</title>
    <style>
        body { font-family: Tahoma; background: #0f071f; color: #fff; padding: 10px; text-align: center; box-sizing: border-box; margin:0; }
        .card { background: linear-gradient(135deg, #1f1035 0%, #110522 100%); border: 4px solid #ffd700; padding: 20px; border-radius: 30px; max-width: 850px; margin: 10px auto; box-shadow: 0 0 40px rgba(255,215,0,0.3); box-sizing: border-box; width: 100%; }
        .boxes { display: flex; justify-content: center; gap: 12px; margin: 20px 0; flex-wrap: wrap; box-sizing: border-box; }
        .box { width: 95px; height: 110px; background: linear-gradient(145deg, #581c87, #3b0764); border: 3px solid #ffd700; border-radius: 18px; color: #ffd700; font-size: 17px; font-weight: 900; cursor: pointer; display: flex; flex-direction: column; align-items: center; justify-content: center; box-sizing: border-box; }
        .box.booked { background: linear-gradient(145deg, #7f1d1d, #450a0a) !important; border-color: #ef4444 !important; }
        .box.my { background: linear-gradient(145deg, #1e3a8a, #172554) !important; border-color: #60a5fa !important; }
    </style>
</head>
<body>
    {{ lang_bar | safe }}
    <div class="card">
        <h2 style="color:#ffd700; font-size: 20px;">🏛️ إمبراطورية الأرقام الملكية المستقلة</h2>
        <p style="font-size:14px; color:#fde047; margin:5px 0;">سعر الحجز: 50 USDD | الجائزة الكبرى: 200 USDD</p>
        <div class="boxes">
            {% for i in range(1, 6) %}
                {% if i in bookings %}
                    {% if bookings[i] == username %}
                        <button onclick="empAction('cancel', {{ i }})" class="box my"><span>👑</span><span>رقم {{ i }}</span><span style="font-size:11px;">تراجع</span></button>
                    {% else %}
                        <div class="box booked"><span>👑</span><span>رقم {{ i }}</span><span style="font-size:10px;">{{ bookings[i] }}</span></div>
                    {% endif %}
                {% else %}
                    <button onclick="empAction('book', {{ i }})" class="box"><span>👑</span><span>رقم {{ i }}</span><span style="font-size:11px; color:#fef08a;">50$</span></button>
                {% endif %}
            {% endfor %}
        </div>
        {% if role == 'admin' or role == 'supervisor' %}
            <div style="margin-top:20px;">
                <button onclick="empAction('admin_draw', 0)" style="background: linear-gradient(135deg, #22c55e, #15803d); color: #fff; padding: 12px 25px; font-weight: 900; border: none; border-radius: 12px; cursor: pointer; font-size: 16px;">⚡ بدء السحب الملكي لمجموعتك</button>
            </div>
        {% endif %}
    </div>
    <script>
        function empAction(type, box) {
            let fd = new FormData(); fd.append('action_type', type); fd.append('box_number', box);
            fetch('/game_numbers_empire', {method:'POST', body:fd}).then(r=>r.json()).then(d=>{
                alert(d.msg || "تم التنفيذ!"); location.reload();
            });
        }
    </script>
</body>
</html>
"""

GAME_NUMBER_WHEEL_PAGE = """
<!DOCTYPE html>
<html lang="{{ lang_key }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ t.game4 }}</title>
    <style>
        body { font-family: Tahoma; background: #151928; color: #fff; padding: 10px; text-align: center; box-sizing: border-box; margin: 0; }
        .card { background: rgba(25,30,48,0.95); border: 3px solid #ffd700; padding: 20px; border-radius: 25px; max-width: 750px; margin: 10px auto; box-shadow: 0 20px 50px rgba(0,0,0,0.8); box-sizing: border-box; width: 100%; }
        .wheel-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin: 12px auto; max-width: 440px; box-sizing: border-box; width: 100%; }
        .wheel-btn { background: #1f2937; border: 2px solid #ffd700; border-radius: 10px; padding: 10px 5px; font-size: 16px; font-weight: 900; color: #fff; cursor: pointer; aspect-ratio: 1; display:flex; align-items:center; justify-content:center; }
        .wheel-btn.selected { background: #d97706 !important; color: #000 !important; }
    </style>
</head>
<body>
    {{ lang_bar | safe }}
    <div class="card">
        <h2 style="color:#ffd700; margin-top:0; font-size: 20px;">🎡 عجلة الحظ</h2>
        <div class="wheel-grid">
            {% for n in range(1, 21) %}
                <button type="button" id="w_num_{{ n }}" onclick="toggleWheelNum({{ n }})" class="wheel-btn">{{ n }}</button>
            {% endfor %}
        </div>
        <button type="button" onclick="spinWheel()" style="padding: 12px 35px; background: linear-gradient(135deg,#22c55e,#15803d); color: #fff; font-weight: 900; font-size: 16px; border: none; border-radius: 14px; cursor: pointer; margin-top: 15px;">ابدأ السحب 🎡</button>
    </div>
    <script>
        let wheelSelected = [];
        function toggleWheelNum(n) {
            let idx = wheelSelected.indexOf(n);
            if(idx > -1) { wheelSelected.splice(idx, 1); document.getElementById('w_num_' + n).classList.remove('selected'); }
            else { wheelSelected.push(n); document.getElementById('w_num_' + n).classList.add('selected'); }
        }
        function spinWheel() {
            let fd = new FormData(); fd.append('selected_numbers', JSON.stringify(wheelSelected));
            fetch('/game_number_wheel', {method: 'POST', body: fd}).then(res => res.json()).then(d => {
                alert(d.msg || "تم السحب!"); location.reload();
            });
        }
    </script>
</body>
</html>
"""

GAME_REVEAL_PAGE = """
<!DOCTYPE html>
<html lang="{{ lang_key }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ t.game5 }}</title>
    <style>
        body { font-family: Tahoma; background: #151928; color: #fff; padding: 10px; text-align: center; box-sizing: border-box; margin:0; }
        .card { background: rgba(25,30,48,0.95); border: 3px solid #ffd700; padding: 20px; border-radius: 25px; max-width: 750px; margin: 10px auto; box-shadow: 0 20px 50px rgba(0,0,0,0.8); box-sizing: border-box; width: 100%; }
        .boxes-grid { display: flex; justify-content: center; gap: 10px; margin: 20px 0; flex-wrap: wrap; box-sizing: border-box; }
        .box-cell { background: linear-gradient(145deg, #7c3aed, #4c1d95); border: 3px solid #ffd700; border-radius: 15px; width: 85px; height: 95px; font-size: 30px; font-weight: 900; color: #fff; display: flex; align-items: center; justify-content: center; cursor: pointer; }
    </style>
</head>
<body>
    {{ lang_bar | safe }}
    <div class="card">
        <h2 style="color:#ffd700; margin-top:0; font-size: 20px;">🎟️ لعبة اكشف واربح</h2>
        <div class="boxes-grid">
            {% for i in range(1, 6) %}
                <div class="box-cell" id="b_{{ i }}" onclick="clickBox({{ i }})">📦</div>
            {% endfor %}
        </div>
        <button type="button" id="startBtn" onclick="startReveal()" style="padding: 12px 35px; background: linear-gradient(135deg,#ffd700,#ff8c00); color: #000; font-weight: 900; font-size: 16px; border: none; border-radius: 14px; cursor: pointer; margin-top: 10px;">ابدأ المحاولة (1 USDD) 🎟️</button>
    </div>
    <script>
        let sessionRevealed = []; let clicksCount = 0; let gameActive = false;
        function startReveal() {
            fetch('/game_reveal_and_win', {method: 'POST'}).then(res => res.json()).then(d => {
                if(d.success) { sessionRevealed = d.revealed; clicksCount = 0; gameActive = true; alert("تم الخصم! اختر 3 صناديق."); }
                else { alert(d.msg || "رصيد غير كافي!"); }
            });
        }
        function clickBox(boxIdx) {
            if(!gameActive) { alert("اضغط ابدأ المحاولة أولاً!"); return; }
            let cell = document.getElementById('b_' + boxIdx);
            if(clicksCount < sessionRevealed.length) {
                cell.innerText = sessionRevealed[clicksCount]; clicksCount++;
                if(clicksCount === sessionRevealed.length) {
                    gameActive = false;
                    setTimeout(() => {
                        fetch('/game_reveal_result_check', {method: 'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({revealed: sessionRevealed})})
                        .then(res => res.json()).then(resData => { alert(resData.msg); location.reload(); });
                    }, 400);
                }
            }
        }
    </script>
</body>
</html>
"""

GAME_ARROW_WHEEL_PAGE = """
<!DOCTYPE html>
<html lang="{{ lang_key }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ t.game6 }}</title>
    <style>
        body { font-family: Tahoma; background: #151928; color: #fff; padding: 10px; text-align: center; box-sizing: border-box; margin:0; }
        .card { background: rgba(25,30,48,0.95); border: 3px solid #ffd700; padding: 20px; border-radius: 25px; max-width: 750px; margin: 10px auto; box-shadow: 0 20px 50px rgba(0,0,0,0.8); box-sizing: border-box; width: 100%; }
    </style>
</head>
<body>
    {{ lang_bar | safe }}
    <div class="card">
        <h2 style="color:#ffd700; margin-top:0; font-size: 20px;">🎯 لعبة رمي السهم المتحركة</h2>
        <button type="button" onclick="throwArrow()" style="padding: 14px 35px; background: linear-gradient(135deg,#22c55e,#15803d); color: #fff; font-weight: 900; font-size: 18px; border: none; border-radius: 14px; cursor: pointer; margin-top: 15px;">🎯 ارم السهم (1 USDD)</button>
    </div>
    <script>
        function throwArrow() {
            fetch('/game_arrow_wheel', {method: 'POST'}).then(res => res.json()).then(d => {
                if(d.success) { alert(d.msg); location.reload(); } else { alert(d.msg || "رصيد غير كافي!"); }
            });
        }
    </script>
</body>
</html>
"""

CHAT_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>الدردشة الفورية والدعم</title>
    <style>
        body { font-family: Tahoma; background: #151928; color: #fff; padding: 10px; text-align: center; box-sizing:border-box; margin:0; }
        .chat-box { background: rgba(25,30,48,0.95); border: 2px solid #ffd700; border-radius: 20px; max-width: 650px; margin: 15px auto; padding: 15px; text-align: right; box-sizing:border-box; width:100%; }
        .messages-area { height: 320px; background: #0a0d16; border: 1px solid #444; border-radius: 12px; padding: 12px; overflow-y: scroll; margin-bottom: 12px; display: flex; flex-direction: column; gap: 8px; box-sizing:border-box; }
        .msg { padding: 8px 12px; border-radius: 10px; max-width: 85%; font-size: 14px; box-sizing:border-box; }
    </style>
</head>
<body>
    {{ lang_bar | safe }}
    <h2 style="font-size:20px;">💬 غرفة الدردشة والدعم الفني الفوري</h2>
    <a href="/dashboard" style="background:#3b82f6; color:#fff; padding:8px 16px; text-decoration:none; border-radius:10px; font-weight:900;">الرئيسية</a>
    <div class="chat-box">
        <div class="messages-area" id="msgArea">
            {% for m in messages %}
            <div class="msg" style="background:{% if m.sender == username %}#1e3a8a; align-self:flex-start;{% else %}#065f46; align-self:flex-end;{% endif %}">
                <b>{{ m.sender }}:</b><br><span>{{ m.message }}</span>
            </div>
            {% endfor %}
        </div>
        <form method="POST" style="display:flex; gap:8px;">
            <input type="text" name="message" required placeholder="اكتب استفسارك..." style="flex:1; padding:10px; background:#0a0d16; color:#fff; border:1px solid #444; border-radius:8px;">
            <button type="submit" style="background:#22c55e; color:#000; font-weight:900; padding:10px 20px; border:none; border-radius:8px; cursor:pointer;">إرسال</button>
        </form>
    </div>
    <script>let area = document.getElementById('msgArea'); area.scrollTop = area.scrollHeight;</script>
</body>
</html>
"""

# --- Routes وأكواد التشغيل الأساسية ---

@app.route('/set_lang/<lang>')
def set_lang(lang):
    if lang in TRANSLATIONS: session['lang'] = lang
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/api/sync_balance')
def api_sync_balance():
    if 'username' not in session: return jsonify({"balance": 0.0})
    user = User.query.filter_by(username=session['username']).first()
    return jsonify({"balance": user.balance if user else 0.0})

@app.route('/api/empire_status')
def api_empire_status():
    state = EmpireGlobalState.query.get(1)
    return jsonify({
        "winning_number": state.last_winning_number if state else 0,
        "timestamp": state.draw_timestamp if state else 0.0,
        "last_winner_info": state.last_winner_info if state else 'لا يوجد فائز سابق بعد'
    })

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
            session['created_by'] = user.created_by
            return redirect(url_for('dashboard'))
        else:
            error = "خطأ في اسم المستخدم أو كلمة المرور!"
    return render_template_string(LOGIN_PAGE, t=t, error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session: return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    if not user: return redirect(url_for('logout'))
    t = get_t()
    lang_key = session.get('lang', 'ar')
    msg = None
    if request.method == 'POST':
        action = request.form.get('action')
        vault = SystemVault.query.get(1)
        if action == 'redeem_card':
            card_code = request.form.get('card_code', '').strip()
            card = RechargeCard.query.filter_by(code=card_code, is_used=False).first()
            if card and vault.vault_balance >= card.amount:
                vault.vault_balance -= card.amount
                user.balance += card.amount
                card.is_used = True
                card.used_by = user.username
                db.session.add(FinancialLog(action_type='شحن عبر بطاقة كود', admin_name=user.created_by, target_user=user.username, amount=card.amount, log_time=get_local_time()))
                db.session.commit()
                msg = f"🎉 تم شحن {card.amount} USDD بنجاح!"
            else:
                msg = "⚠️ الكود غير صالح أو مستخدم مسبقاً!"
    return render_template_string(DASHBOARD_PAGE, t=t, lang_key=lang_key, lang_bar=get_lang_bar(), username=user.username, role=user.role, balance=user.balance, msg=msg)

# --- لوحة تحكم المشرف المستقل ---
@app.route('/supervisor_dashboard', methods=['GET', 'POST'])
def supervisor_dashboard():
    if 'username' not in session or session.get('role') != 'supervisor': return redirect(url_for('dashboard'))
    sup_username = session['username']
    supervisor = User.query.filter_by(username=sup_username).first()
    msg = None
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'create_player':
            uname = request.form.get('username', '').strip()
            pwd = request.form.get('password', '').strip()
            init_bal = float(request.form.get('balance', 0))
            if uname and pwd and not User.query.filter_by(username=uname).first():
                if supervisor.balance >= init_bal:
                    supervisor.balance -= init_bal
                    new_player = User(username=uname, password=pwd, balance=init_bal, role='user', created_by=sup_username, owner_name=f'مجموعة {sup_username}')
                    db.session.add(new_player)
                    db.session.add(FinancialLog(action_type='إنشاء لاعب برصيد من صندوق المشرف', admin_name=sup_username, target_user=uname, amount=init_bal, log_time=get_local_time()))
                    db.session.commit()
                    msg = f"تم إنشاء اللاعب {uname} بنجاح!"
                else:
                    msg = "رصيد صندوقك المالي غير كافي لمنح هذا الرصيد الابتدائي للاعب!"
            else:
                msg = "اسم المستخدم موجود مسبقاً أو البيانات ناقصة!"
        elif action == 'transfer_balance':
            target_p = request.form.get('target_player')
            amount = float(request.form.get('amount', 0))
            t_type = request.form.get('transfer_type')
            player = User.query.filter_by(username=target_p, created_by=sup_username).first()
            if player:
                if t_type == 'sell':
                    if supervisor.balance >= amount:
                        supervisor.balance -= amount
                        player.balance += amount
                        db.session.add(FinancialLog(action_type='بيع رصيد من صندوق المشرف لللاعب', admin_name=sup_username, target_user=target_p, amount=amount, log_time=get_local_time()))
                        db.session.commit()
                        msg = f"تم بيع {amount} USDD لللاعب {target_p} بنجاح!"
                    else:
                        msg = "رصيد صندوقك المالي غير كافي!"
                elif t_type == 'buyback':
                    if player.balance >= amount:
                        player.balance -= amount
                        supervisor.balance += amount
                        db.session.add(FinancialLog(action_type='سحب رصيد من اللاعب لصندوق المشرف', admin_name=sup_username, target_user=target_p, amount=amount, log_time=get_local_time()))
                        db.session.commit()
                        msg = f"تم سحب {amount} USDD من اللاعب {target_p} لصندوقك بنجاح!"
                    else:
                        msg = "رصيد اللاعب لا يكفي لإتمام عملية السحب!"

    selected_player = request.args.get('player_filter', '').strip()
    players = User.query.filter_by(created_by=sup_username, role='user').all()
    player_names = [p.username for p in players]
    if selected_player and selected_player in player_names:
        logs = PlayerActivity.query.filter_by(supervisor_name=sup_username, username=selected_player).order_by(PlayerActivity.id.desc()).all()
    else:
        logs = PlayerActivity.query.filter_by(supervisor_name=sup_username).order_by(PlayerActivity.id.desc()).all()

    return render_template_string(SUPERVISOR_DASHBOARD_PAGE, lang_bar=get_lang_bar(), supervisor=supervisor, players=players, logs=logs, selected_player=selected_player, msg=msg)

# --- إدارة الآدمن للمشرفين ---
@app.route('/admin_supervisors', methods=['GET', 'POST'])
def admin_supervisors():
    if 'username' not in session or session.get('username') != 'admin1': return redirect(url_for('dashboard'))
    vault = SystemVault.query.get(1)
    msg = None
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'create_supervisor':
            uname = request.form.get('username', '').strip()
            pwd = request.form.get('password', '').strip()
            owner = request.form.get('owner_name', 'مشرف مستقل').strip()
            if uname and pwd and not User.query.filter_by(username=uname).first():
                new_sup = User(username=uname, password=pwd, balance=0.0, role='supervisor', created_by='admin1', owner_name=owner)
                db.session.add(new_sup)
                db.session.commit()
                msg = f"تم إنشاء المشرف {uname} وصندوقه المستقل بنجاح!"
            else:
                msg = "خطأ: اسم المشرف موجود مسبقاً أو بيانات ناقصة!"
        elif action == 'fund_supervisor':
            target_sup = request.form.get('target_sup')
            amount = float(request.form.get('amount', 0))
            sup_user = User.query.filter_by(username=target_sup, role='supervisor').first()
            if sup_user and vault.vault_balance >= amount:
                vault.vault_balance -= amount
                sup_user.balance += amount
                db.session.add(FinancialLog(action_type='تمويل صندوق المشرف من الخزنة العامة', admin_name='admin1', target_user=sup_user.username, amount=amount, log_time=get_local_time()))
                db.session.commit()
                msg = f"تم تمويل صندوق المشرف {sup_user.username} بـ {amount} USDD بنجاح!"
            else:
                msg = "خطأ في الخزنة أو المشرف غير موجود!"
                
    supervisors = User.query.filter_by(role='supervisor').all()
    sup_data = []
    for s in supervisors:
        sup_players = User.query.filter_by(created_by=s.username, role='user').all()
        sup_data.append({
            'username': s.username,
            'owner_name': s.owner_name,
            'balance': s.balance,
            'player_count': len(sup_players),
            'players': sup_players
        })
    return render_template_string(ADMIN_SUPERVISORS_PAGE, lang_bar=get_lang_bar(), vault_balance=vault.vault_balance if vault else 0.0, supervisors=sup_data, msg=msg)

# --- إدارة الألعاب لـ 10 مشرفين وعام ---
@app.route('/admin_game_control', methods=['GET', 'POST'])
def admin_game_control():
    if 'username' not in session or session.get('username') != 'admin1': return redirect(url_for('dashboard'))
    msg = None
    if request.method == 'POST':
        scope = request.form.get('supervisor_scope', 'global')
        game_name = request.form.get('game_name')
        round_index = int(request.form.get('round_index', 1))
        winning_number = int(request.form.get('winning_number', 0))
        existing = GameFutureDraw.query.filter_by(supervisor_scope=scope, game_name=game_name, round_index=round_index).first()
        if existing:
            existing.winning_number = winning_number
        else:
            db.session.add(GameFutureDraw(supervisor_scope=scope, game_name=game_name, round_index=round_index, winning_number=winning_number))
        db.session.commit()
        msg = f"تمت برمجة الرقم {winning_number} للجولة #{round_index} في لعبة {game_name} للنطاق ({scope}) بنجاح!"
    supervisors = User.query.filter_by(role='supervisor').all()
    return render_template_string(ADMIN_GAME_CONTROL_PAGE, lang_bar=get_lang_bar(), supervisors=supervisors, msg=msg)

# --- مسارات الألعاب الأساسية مع ربط المشرفين ---
@app.route('/game_golden_number', methods=['GET', 'POST'])
def game_golden_number():
    if 'username' not in session: return redirect(url_for('login'))
    username = session['username']
    user = User.query.filter_by(username=username).first()
    sup_scope = user.created_by if user.role == 'user' else (username if user.role == 'supervisor' else 'global')
    t = get_t()
    lang_key = session.get('lang', 'ar')
    if request.method == 'POST':
        action = request.form.get('action_type')
        if action == 'book':
            num = int(request.form.get('number', 0))
            if GoldenNumberBooking.query.filter_by(supervisor_name=sup_scope, number=num).first():
                return jsonify({"success": False, "msg": "هذا الرقم محجوز مسبقاً!"})
            if user.balance >= 2.0:
                user.balance -= 2.0
                db.session.add(FinancialLog(action_type='مبيع رهان الرقم الحنون', admin_name=sup_scope, target_user=username, amount=2.0, log_time=get_local_time()))
                db.session.add(GoldenNumberBooking(supervisor_name=sup_scope, username=username, number=num, booking_date=get_local_time()))
                db.session.add(PlayerActivity(username=username, supervisor_name=sup_scope, game_name='الرقم الحنون', bet_details=f'حجز الرقم #{num}', amount=2.0, outcome='قيد الانتظار', winning_number='---', timestamp=get_local_time()))
                db.session.commit()
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "msg": "رصيد غير كافي"})
        elif action == 'cancel':
            num = int(request.form.get('number', 0))
            b = GoldenNumberBooking.query.filter_by(supervisor_name=sup_scope, number=num, username=username).first()
            if b:
                db.session.delete(b)
                user.balance += 2.0
                db.session.commit()
                return jsonify({"success": True})
        elif action == 'admin_draw' and (user.role == 'admin' or user.role == 'supervisor'):
            winning_num = get_unified_math_outcome('golden', sup_scope, [], 1, 50)
            winner_b = GoldenNumberBooking.query.filter_by(supervisor_name=sup_scope, number=winning_num).first()
            if winner_b:
                winner_u = User.query.filter_by(username=winner_b.username).first()
                if winner_u:
                    winner_u.balance += 70.0
                    db.session.add(FinancialLog(action_type='جائزة الرقم الحنون', admin_name=sup_scope, target_user=winner_u.username, amount=70.0, log_time=get_local_time()))
                    db.session.add(PlayerActivity(username=winner_u.username, supervisor_name=sup_scope, game_name='الرقم الحنون', bet_details=f'ربح الجائزة الكبرى', amount=70.0, outcome='ربح', winning_number=str(winning_num), timestamp=get_local_time()))
            GoldenNumberBooking.query.filter_by(supervisor_name=sup_scope).delete()
            db.session.commit()
            return jsonify({"success": True, "winning_number": winning_num})
    bookings = {b.number: b.username for b in GoldenNumberBooking.query.filter_by(supervisor_name=sup_scope).all()}
    my_bookings_list = [b.number for b in GoldenNumberBooking.query.filter_by(supervisor_name=sup_scope, username=username).all()]
    return render_template_string(GAME_GOLDEN_PAGE, t=t, lang_key=lang_key, lang_bar=get_lang_bar(), username=username, role=user.role, supervisor_name=sup_scope, balance=user.balance, bookings=bookings, my_nums_str=', '.join(map(str, my_bookings_list)) if my_bookings_list else 'لا توجد حجوزات', my_total_cost=len(my_bookings_list)*2.0)

@app.route('/game_roulette_bet', methods=['POST'])
def game_roulette_bet():
    if 'username' not in session: return jsonify({"success": False})
    user = User.query.filter_by(username=session['username']).first()
    data = request.get_json() or {}
    if data.get('action') == 'add':
        if user.balance >= 1.0:
            user.balance -= 1.0
            db.session.commit()
            return jsonify({"success": True, "balance": user.balance})
        return jsonify({"success": False, "msg": "رصيد غير كافي!"})
    return jsonify({"success": False})

@app.route('/game_roulette_draw', methods=['POST'])
def game_roulette_draw():
    if 'username' not in session: return jsonify({"success": False})
    username = session['username']
    user = User.query.filter_by(username=username).first()
    sup_scope = user.created_by if user.role == 'user' else username
    data = request.get_json() or {}
    bets = data.get('bets', {})
    total_bet = sum(float(v) for v in bets.values())
    winning_num = get_unified_math_outcome('roulette', sup_scope, [int(k) for k in bets.keys()], 0, 36)
    payout = 0.0
    if str(winning_num) in bets:
        payout = float(bets[str(winning_num)]) * 20.0
        user.balance += payout
        outcome = 'ربح'
        msg = f"🎉 مبروك! ظهر الرقم #{winning_num} وفزت بـ {payout} USDD!"
    else:
        outcome = 'خسارة'
        msg = f"❌ حظ أوفر! الرقم الفائز #{winning_num}"
    db.session.add(PlayerActivity(username=username, supervisor_name=sup_scope, game_name='روليت الحظ', bet_details=json.dumps(bets), amount=total_bet, outcome=outcome, winning_number=str(winning_num), timestamp=get_local_time()))
    db.session.commit()
    return jsonify({"success": True, "winning_number": winning_num, "msg": msg, "balance": user.balance})

@app.route('/game_roulette', methods=['GET'])
def game_roulette():
    if 'username' not in session: return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    return render_template_string(GAME_ROULETTE_PAGE, t=get_t(), lang_key=session.get('lang', 'ar'), lang_bar=get_lang_bar(), balance=user.balance)

@app.route('/game_numbers_empire', methods=['GET', 'POST'])
def game_numbers_empire():
    if 'username' not in session: return redirect(url_for('login'))
    username = session['username']
    user = User.query.filter_by(username=username).first()
    sup_scope = user.created_by if user.role == 'user' else (username if user.role == 'supervisor' else 'global')
    if request.method == 'POST':
        action = request.form.get('action_type')
        box = int(request.form.get('box_number', 0))
        if action == 'book' and user.balance >= 50.0 and not NumbersEmpireBooking.query.filter_by(supervisor_name=sup_scope, number=box).first():
            user.balance -= 50.0
            db.session.add(NumbersEmpireBooking(supervisor_name=sup_scope, username=username, number=box, booking_date=get_local_time()))
            db.session.add(PlayerActivity(username=username, supervisor_name=sup_scope, game_name='إمبراطورية الأرقام', bet_details=f'مربع #{box}', amount=50.0, outcome='قيد الانتظار', winning_number='---', timestamp=get_local_time()))
            db.session.commit()
            return jsonify({"success": True, "msg": "تم الحجز بنجاح"})
        elif action == 'admin_draw' and (user.role == 'admin' or user.role == 'supervisor'):
            winning_num = get_unified_math_outcome('empire', sup_scope, [], 1, 5)
            winner_b = NumbersEmpireBooking.query.filter_by(supervisor_name=sup_scope, number=winning_num).first()
            if winner_b:
                winner_u = User.query.filter_by(username=winner_b.username).first()
                if winner_u:
                    winner_u.balance += 200.0
                    db.session.add(PlayerActivity(username=winner_u.username, supervisor_name=sup_scope, game_name='إمبراطورية الأرقام', bet_details='جائزة كبرى', amount=200.0, outcome='ربح', winning_number=str(winning_num), timestamp=get_local_time()))
            NumbersEmpireBooking.query.filter_by(supervisor_name=sup_scope).delete()
            db.session.commit()
            return jsonify({"success": True, "msg": f"الرقم الفائز #{winning_num}"})
    bookings = {b.number: b.username for b in NumbersEmpireBooking.query.filter_by(supervisor_name=sup_scope).all()}
    return render_template_string(GAME_NUMBERS_EMPIRE_PAGE, t=get_t(), lang_key=session.get('lang', 'ar'), lang_bar=get_lang_bar(), username=username, role=user.role, bookings=bookings)

@app.route('/game_number_wheel', methods=['GET', 'POST'])
def game_number_wheel():
    if 'username' not in session: return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    sup_scope = user.created_by if user.role == 'user' else username
    if request.method == 'POST':
        nums = json.loads(request.form.get('selected_numbers', '[]'))
        cost = float(len(nums) * 1.0)
        if nums and user.balance >= cost:
            user.balance -= cost
            winning_num = get_unified_math_outcome('wheel', sup_scope, nums, 1, 20)
            if winning_num in nums:
                user.balance += 20.0
                outcome = 'ربح'
                msg = f"مبروك ربحت 20 USDD للرقم {winning_num}"
            else:
                outcome = 'خسارة'
                msg = f"حظ أوفر! الرقم الفائز {winning_num}"
            db.session.add(PlayerActivity(username=user.username, supervisor_name=sup_scope, game_name='عجلة الحظ', bet_details=str(nums), amount=cost, outcome=outcome, winning_number=str(winning_num), timestamp=get_local_time()))
            db.session.commit()
            return jsonify({"success": True, "msg": msg})
        return jsonify({"success": False, "msg": "رصيد غير كافي أو لم تختر أرقاماً!"})
    return render_template_string(GAME_NUMBER_WHEEL_PAGE, t=get_t(), lang_key=session.get('lang', 'ar'), lang_bar=get_lang_bar())

@app.route('/game_arrow_wheel', methods=['GET', 'POST'])
def game_arrow_wheel():
    if 'username' not in session: return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    sup_scope = user.created_by if user.role == 'user' else username
    if request.method == 'POST':
        if user.balance >= 1.0:
            user.balance -= 1.0
            r = random.random()
            prize = 1.0 if r < 0.70 else (2.0 if r < 0.75 else 0.0)
            user.balance += prize
            db.session.add(PlayerActivity(username=user.username, supervisor_name=sup_scope, game_name='رمي السهم', bet_details='رمية سهم', amount=1.0, outcome='ربح' if prize>0 else 'خسارة', winning_number=str(prize), timestamp=get_local_time()))
            db.session.commit()
            return jsonify({"success": True, "msg": f"النتيجة: ربحت {prize} USDD"})
        return jsonify({"success": False, "msg": "رصيد غير كافي!"})
    return render_template_string(GAME_ARROW_WHEEL_PAGE, t=get_t(), lang_key=session.get('lang', 'ar'), lang_bar=get_lang_bar())

@app.route('/game_reveal_and_win', methods=['GET', 'POST'])
def game_reveal_and_win():
    if 'username' not in session: return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    if request.method == 'POST':
        if user.balance >= 1.0:
            user.balance -= 1.0
            db.session.commit()
            return jsonify({"success": True, "revealed": ['🦁', '🦁', '7']})
        return jsonify({"success": False, "msg": "رصيد غير كافي!"})
    return render_template_string(GAME_REVEAL_PAGE, t=get_t(), lang_key=session.get('lang', 'ar'), lang_bar=get_lang_bar())

@app.route('/game_reveal_result_check', methods=['POST'])
def game_reveal_result_check():
    if 'username' not in session: return jsonify({"success": False})
    user = User.query.filter_by(username=session['username']).first()
    user.balance += 0.5
    db.session.commit()
    return jsonify({"success": True, "msg": "تم استرداد 0.5 USDD"})

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'username' not in session: return redirect(url_for('login'))
    username = session['username']
    if request.method == 'POST':
        msg = request.form.get('message', '').strip()
        if msg:
            db.session.add(ChatMessage(sender=username, recipient='admin1', message=msg, timestamp=get_local_time()))
            db.session.commit()
            return redirect(url_for('chat'))
    messages = ChatMessage.query.filter((ChatMessage.sender == username) | (ChatMessage.recipient == username)).all()
    return render_template_string(CHAT_PAGE, lang_bar=get_lang_bar(), username=username, messages=messages)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
