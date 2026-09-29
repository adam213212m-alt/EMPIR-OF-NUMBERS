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

class PlayerActivity(db.Model):
    __tablename__ = 'player_activities'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), nullable=False)
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
    username = db.Column(db.String(80))
    number = db.Column(db.Integer)
    booking_date = db.Column(db.String(50))

class NumbersEmpireBooking(db.Model):
    __tablename__ = 'numbers_empire_bookings'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
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
        'dir': 'rtl', 'title': 'امبراطورية الأرقام', 'subtitle': 'منصة الألعاب التفاعلية الفائقة 12D',
        'login': 'دخول للبرنامج', 'username': 'اسم المستخدم', 'password': 'كلمة المرور', 'balance': 'الرصيد',
        'recharge': 'شحن رصيد', 'withdraw': 'سحب رصيد', 'change_pass': 'تغيير الباسورد', 'logout': 'خروج',
        'dashboard': 'لوحة التحكم', 'back_dash': '🏠 الرئيسية', 'customers': 'الزبائن', 'accounting': 'المحاسبة والخزنة',
        'game_control': '🎮 إدارة الألعاب', 'chat': '💬 الدردشة الفورية',
        'game1': 'الرقم الحنون', 'game2': 'روليت الحظ', 'game3': 'إمبراطورية الأرقام', 'game4': 'عجلة الحظ', 'game5': 'اكشف واربح', 'game6': 'رمي السهم المتحركة',
        'cost': 'التكلفة', 'prize': 'الجائزة', 'book': 'حجز', 'cancel': 'تراجع', 'booked': 'محجوز',
        'spin': 'تدوير العجلة', 'draw_now': 'اسحب الآن'
    },
    'en': {
        'dir': 'ltr', 'title': 'Empire of Numbers', 'subtitle': 'Super Interactive 12D Gaming Platform',
        'login': 'Login', 'username': 'Username', 'password': 'Password', 'balance': 'Balance',
        'recharge': 'Recharge', 'withdraw': 'Withdraw', 'change_pass': 'Change Password', 'logout': 'Logout',
        'dashboard': 'Dashboard', 'back_dash': '🏠 Home', 'customers': 'Customers', 'accounting': 'Vault & Accounting',
        'game_control': '🎮 Game Control', 'chat': '💬 Live Chat',
        'game1': 'The Tender Number', 'game2': 'Lucky Roulette', 'game3': 'Empire of Numbers', 'game4': 'Wheel of Fortune', 'game5': 'Reveal & Win', 'game6': 'Animated Arrow Throw',
        'cost': 'Cost', 'prize': 'Prize', 'book': 'Book', 'cancel': 'Cancel', 'booked': 'Booked',
        'spin': 'Spin Wheel', 'draw_now': 'Draw Now'
    },
    'fr': {
        'dir': 'ltr', 'title': 'Empire des Nombres', 'subtitle': 'Plateforme de Jeux Super Interactive 12D',
        'login': 'Connexion', 'username': "Nom d'utilisateur", 'password': 'Mot de passe', 'balance': 'Solde',
        'recharge': 'Recharger', 'withdraw': 'Retirer', 'change_pass': 'Changer le mot de passe', 'logout': 'Déconnexion',
        'dashboard': 'Tableau de bord', 'back_dash': '🏠 Accueil', 'customers': 'Clients', 'accounting': 'Comptabilité et Coffre',
        'game_control': '🎮 Contrôle des Jeux', 'chat': '💬 Chat en Direct',
        'game1': 'Le Numéro Tendre', 'game2': 'Roulette Chanceuse', 'game3': 'Empire des Nombres', 'game4': 'Roue de la Fortune', 'game5': 'Révéler & Gagner', 'game6': 'Lancer de Flèche',
        'cost': 'Coût', 'prize': 'Prix', 'book': 'Réserver', 'cancel': 'Annuler', 'booked': 'Réservé',
        'spin': 'Tourner', 'draw_now': 'Tirer'
    },
    'de': {
        'dir': 'ltr', 'title': 'Imperium der Zahlen', 'subtitle': 'Super Interaktive 12D Gaming Plattform',
        'login': 'Anmelden', 'username': 'Benutzername', 'password': 'Passwort', 'balance': 'Guthaben',
        'recharge': 'Aufladen', 'withdraw': 'Auszahlen', 'change_pass': 'Passwort ändern', 'logout': 'Abmelden',
        'dashboard': 'Dashboard', 'back_dash': '🏠 Startseite', 'customers': 'Kunden', 'accounting': 'Buchhaltung',
        'game_control': '🎮 Spielkontrolle', 'chat': '💬 Live-Chat',
        'game1': 'Die Zarte Nummer', 'game2': 'Glücks-Roulette', 'game3': 'Imperium der Zahlen', 'game4': 'Glücksrad', 'game5': 'Aufdecken & Gewinnen', 'game6': 'Pfeilwurf',
        'cost': 'Kosten', 'prize': 'Gewinn', 'book': 'Buchen', 'cancel': 'Abbrechen', 'booked': 'Gebucht',
        'spin': 'Drehen', 'draw_now': 'Ziehen'
    },
    'es': {
        'dir': 'ltr', 'title': 'Imperio de los Números', 'subtitle': 'Plataforma de Juegos Super Interactiva 12D',
        'login': 'Iniciar Sesión', 'username': 'Nombre de usuario', 'password': 'Contraseña', 'balance': 'Saldo',
        'recharge': 'Recargar', 'withdraw': 'Retirar', 'change_pass': 'Cambiar Contraseña', 'logout': 'Cerrar Sesión',
        'dashboard': 'Panel', 'back_dash': '🏠 Inicio', 'customers': 'Clientes', 'accounting': 'Contabilidad',
        'game_control': '🎮 Control de Juegos', 'chat': '💬 Chat en Vivo',
        'game1': 'El Número Tierno', 'game2': 'Ruleta de la Suerte', 'game3': 'Empire of Numbers', 'game4': 'Rueda de la Fortuna', 'game5': 'Revelar y Ganar', 'game6': 'Lanzamiento de Flecha',
        'cost': 'Costo', 'prize': 'Premio', 'book': 'Reservar', 'cancel': 'Cancelar', 'booked': 'Reservado',
        'spin': 'Girar', 'draw_now': 'Sorteo'
    },
    'fa': {
        'dir': 'rtl', 'title': 'امپراتوری اعداد', 'subtitle': 'پلتفرم بازی‌های تعاملی فوق‌العاده 12D',
        'login': 'ورود به برنامه', 'username': 'نام کاربری', 'password': 'رمز عبور', 'balance': 'موجودی',
        'recharge': 'شارژ حساب', 'withdraw': 'برداشت وجه', 'change_pass': 'تغییر رمز عبور', 'logout': 'خروج',
        'dashboard': 'داشبورد', 'back_dash': '🏠 صفحه اصلی', 'customers': 'مشتریان', 'accounting': 'حسابداری و خزانه',
        'game_control': '🎮 کنترل بازی‌ها', 'chat': '💬 پشتیبانی و چت',
        'game1': 'عدد مهربان', 'game2': 'رولت شانس', 'game3': 'امپراتوری اعداد', 'game4': 'گردونه شانس', 'game5': 'کشف کن و برنده شو', 'game6': 'پرتاب دارت متحرک',
        'cost': 'هزینه', 'prize': 'جایزه', 'book': 'رزرو', 'cancel': 'لغو', 'booked': 'رزرو شده',
        'spin': 'چرخش', 'draw_now': 'قرعه‌کشی'
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
    fr_sel = 'selected' if curr == 'fr' else ''
    de_sel = 'selected' if curr == 'de' else ''
    es_sel = 'selected' if curr == 'es' else ''
    fa_sel = 'selected' if curr == 'fa' else ''

    return f"""
<div style="padding: 10px 25px; background: rgba(18, 18, 25, 0.95); display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,215,0,0.2); flex-wrap: wrap; gap: 10px; box-sizing: border-box; width: 100%;">
    <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
        <select onchange="location.href='/set_lang/' + this.value" style="background:#1a1c29; color:#ffd700; border:1px solid #ffd700; padding:6px 12px; border-radius:8px; font-weight:bold; cursor:pointer;">
            <option value="ar" {ar_sel}>العربية 🇸🇦</option>
            <option value="en" {en_sel}>English 🇬🇧</option>
            <option value="fr" {fr_sel}>Français 🇫🇷</option>
            <option value="de" {de_sel}>Deutsch 🇩🇪</option>
            <option value="es" {es_sel}>Español 🇪🇸</option>
            <option value="fa" {fa_sel}>فارسی 🇮🇷</option>
        </select>
        <a href="javascript:location.reload();" title="تحديث الصفحة" style="background: rgba(255,215,0,0.1); border: 1px solid #ffd700; color:#ffd700; padding: 6px 12px; text-decoration:none; border-radius:8px; font-weight:bold; font-size:14px; display: flex; align-items: center; gap: 5px;">🔄 تحديث</a>
    </div>
    <div style="display:flex; gap:15px; align-items:center; flex-wrap: wrap;">
        <div style="background:rgba(6,95,70,0.8); color:#34d399; padding:6px 14px; border-radius:8px; font-weight:900; font-size:14px;">الرصيد: <span id="globalLiveBalance">...</span> USDD</div>
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

def get_unified_math_outcome(game_name, player_choices, min_val, max_val):
    future = GameFutureDraw.query.filter_by(game_name=game_name).order_by(GameFutureDraw.round_index.asc()).first()
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
    <div style="background:rgba(20, 24, 38, 0.9); padding:40px 30px; border-radius:25px; width:100%; max-width:380px; text-align:center; border:2px solid rgba(255,215,0,0.5); box-sizing:border-box;">
        <h2 style="color:#ffd700; margin-top:0;">👑 {{ t.title }}</h2>
        {% if error %}<div style="color:#ef4444; margin-bottom:15px; font-weight:bold;">{{ error }}</div>{% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="{{ t.username }}" required style="width:100%; padding:14px; margin:10px 0; border-radius:12px; background:rgba(10, 13, 22, 0.8); color:#fff; border:1px solid #444; box-sizing:border-box; font-size:15px;">
            <input type="password" name="password" placeholder="{{ t.password }}" required style="width:100%; padding:14px; margin:10px 0; border-radius:12px; background:rgba(10, 13, 22, 0.8); color:#fff; border:1px solid #444; box-sizing:border-box; font-size:15px;">
            <button type="submit" style="width:100%; padding:14px; background:linear-gradient(135deg, #ffd700, #ff8c00); color:#000; font-weight:900; border:none; border-radius:12px; cursor:pointer; font-size:17px; margin-top:5px;">{{ t.login }}</button>
        </form>
        <div style="margin-top:20px; border-top:1px solid rgba(255,215,0,0.2); padding-top:15px;">
            <a href="/guest_login" style="background:rgba(59,130,246,0.2); border:1px solid #3b82f6; color:#38bdf8; padding:12px; border-radius:12px; text-decoration:none; font-weight:bold; display:block; font-size:14px; box-sizing:border-box;">👁️ دخول زائر (تصفح الألعاب بـ 10 USDD)</a>
        </div>
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
        .header { display: flex; justify-content: space-between; align-items: center; background: rgba(20, 24, 38, 0.9); padding: 15px 20px; border-radius: 18px; border-bottom: 3px solid #ffd700; flex-wrap: wrap; gap: 15px; box-sizing: border-box; width: 100%; }
        .icons-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; max-width: 1000px; margin: 25px auto; box-sizing: border-box; width: 100%; }
        @media (max-width: 768px) { .icons-grid { grid-template-columns: repeat(1, 1fr); max-width: 100%; padding: 0 5px; } }
        .icon-card { background: rgba(25,30,48,0.95); border: 3px solid rgba(184,134,11,0.6); border-radius: 24px; padding: 25px 10px; text-align: center; text-decoration: none; box-shadow: 0 15px 35px rgba(0,0,0,0.8); transition: 0.3s; box-sizing: border-box; display: block; width: 100%; }
        .icon-card:hover { border-color: #ffd700; transform: translateY(-5px); }
        .icon-logo { font-size: 45px; margin-bottom: 8px; }
        .icon-title { color: #ffd700; font-size: 17px; font-weight: 900; }
    </style>
</head>
<body>
    {{ lang_bar | safe }}
    <div class="header">
        <div style="display:flex; gap:15px; align-items:center; flex-wrap:wrap;">
            <h2 style="color:#ffd700; margin:0; font-size:20px;">👑 {{ t.title }} (12D)</h2>
            <div style="background:rgba(15,20,32,0.9); padding:6px 12px; border-radius:10px; font-size:14px;">👤 <b>{{ username }}</b> ({{ owner_name }})</div>
            <div style="background:rgba(6,95,70,0.8); color:#34d399; padding:6px 15px; border-radius:10px; font-weight:900; font-size:14px;">{{ t.balance }}: <span id="liveBalance">{{ balance }}</span> USDD</div>
        </div>
        <div style="display:flex; gap:10px; flex-wrap:wrap;">
            {% if role == 'admin' %}
                <a href="/admin_accounting" style="background:#ffd700; color:#000; padding:8px 12px; text-decoration:none; border-radius:10px; font-weight:900; font-size:13px;">📊 لوحة الآدمن والخزنة</a>
                <a href="/admin_game_control" style="background:#38bdf8; color:#000; padding:8px 12px; text-decoration:none; border-radius:10px; font-weight:900; font-size:13px;">🎮 إدارة الألعاب</a>
            {% elif role == 'supervisor' %}
                <a href="/supervisor_dashboard" style="background:#22c55e; color:#000; padding:8px 12px; text-decoration:none; border-radius:10px; font-weight:900; font-size:13px;">👥 لوحة إدارة المشرف</a>
            {% endif %}
            <a href="/logout" style="background:#ef4444; color:#fff; padding:8px 12px; text-decoration:none; border-radius:10px; font-weight:900; font-size:13px;">{{ t.logout }}</a>
        </div>
    </div>

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

SUPERVISOR_DASHBOARD_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة تحكم المشرف - {{ supervisor.username }}</title>
    <style>
        body { font-family: Tahoma; background: #151928; color: #fff; padding: 15px; text-align: center; box-sizing: border-box; margin:0; }
        .box { background: rgba(25,30,48,0.9); padding: 20px; border-radius: 18px; max-width: 600px; margin: 15px auto; border: 2px solid #22c55e; text-align: right; box-sizing: border-box; }
        input, select { width: 100%; padding: 10px; margin: 6px 0; border-radius: 8px; background: #0a0d16; color: #fff; border: 1px solid #444; box-sizing: border-box; font-size: 14px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }
        th, td { border: 1px solid #444; padding: 8px; text-align: center; }
        th { background: #0a0d16; color: #ffd700; }
    </style>
</head>
<body>
    {{ lang_bar | safe }}
    <h2 style="color:#22c55e; font-size:20px;">👥 لوحة إدارة المشرف المستأجر: {{ supervisor.username }}</h2>
    <div style="font-size:18px; font-weight:bold; color:#34d399; margin:10px 0;">رصيدك المتاح للبيع: {{ supervisor.balance }} USDD</div>
    <a href="/dashboard" style="background:#38bdf8; color:#000; padding:8px 16px; text-decoration:none; border-radius:10px; font-weight:900; font-size:13px;">الرئيسية والألعاب</a>

    {% if msg %}<div style="background:#065f46; color:#34d399; padding:10px; border-radius:10px; margin:15px auto; max-width:500px; font-weight:bold; font-size:14px;">{{ msg }}</div>{% endif %}

    <div class="box">
        <h3 style="color:#ffd700; margin-top:0; font-size:17px; text-align:center;">➕ إنشاء حساب لاعب جديد تحت إدارتك</h3>
        <form method="POST">
            <input type="hidden" name="action" value="create_player">
            <label>اسم المستخدم للاعب:</label>
            <input type="text" name="username" required placeholder="اسم المستخدم...">
            <label>كلمة المرور:</label>
            <input type="password" name="password" required placeholder="كلمة المرور...">
            <label>اسم المحل / الزبون:</label>
            <input type="text" name="owner_name" placeholder="اسم المحل...">
            <button type="submit" style="background:#22c55e; color:#000; font-weight:900; padding:12px; border:none; border-radius:8px; width:100%; cursor:pointer; margin-top:10px;">إنشاء اللاعب</button>
        </form>
    </div>

    <div class="box" style="border-color:#38bdf8;">
        <h3 style="color:#38bdf8; margin-top:0; font-size:17px; text-align:center;">💳 بيع رصيد (شحن) أو سحب من لاعب</h3>
        <form method="POST">
            <input type="hidden" name="action" value="transfer_balance">
            <label>اختر اللاعب:</label>
            <select name="target_user" required>
                <option value="">اختر اللاعب</option>
                {% for p in players %}
                <option value="{{ p.username }}">{{ p.username }} (رصيده: {{ p.balance }})</option>
                {% endfor %}
            </select>
            <label>المبلغ:</label>
            <input type="number" name="amount" min="1" required placeholder="المبلغ...">
            <label>نوع العملية:</label>
            <select name="transfer_type" required>
                <option value="sell">شحن (خصم من رصيدك وإضافته للاعب)</option>
                <option value="withdraw">سحب (خصم من اللاعب وإضافته لرصيدك)</option>
            </select>
            <button type="submit" style="background:#38bdf8; color:#000; font-weight:900; padding:12px; border:none; border-radius:8px; width:100%; cursor:pointer; margin-top:10px;">تنفيذ العملية</button>
        </form>
    </div>

    <div style="background: rgba(25,30,48,0.9); padding: 20px; border-radius: 20px; max-width: 900px; margin: 20px auto; overflow-x:auto; box-sizing:border-box;">
        <h3 style="color:#ffd700; font-size:17px;">📋 قائمة لاعبيك المسجلين (لعالمك الخاص)</h3>
        <table>
            <tr><th>اسم اللاعب</th><th>المحل</th><th>الرصيد</th></tr>
            {% for p in players %}
            <tr><td><b>{{ p.username }}</b></td><td>{{ p.owner_name }}</td><td style="color:#34d399;">{{ p.balance }} USDD</td></tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

ADMIN_SUPERVISORS_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>إدارة المشرفين والتمويل</title>
    <style>
        body { font-family: Tahoma; background: #151928; color: #fff; padding: 15px; text-align: center; box-sizing: border-box; margin:0; }
        .box { background: rgba(25,30,48,0.9); padding: 20px; border-radius: 18px; max-width: 500px; margin: 15px auto; border: 2px solid #ffd700; text-align: right; box-sizing: border-box; }
        input, select { width: 100%; padding: 10px; margin: 6px 0; border-radius: 8px; background: #0a0d16; color: #fff; border: 1px solid #444; box-sizing: border-box; font-size: 14px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }
        th, td { border: 1px solid #444; padding: 8px; text-align: center; }
        th { background: #0a0d16; color: #ffd700; }
    </style>
</head>
<body>
    {{ lang_bar | safe }}
    <h2 style="color:#ffd700; font-size:20px;">👑 لوحة الآدمن: إدارة وتأجير المنصة للمشرفين</h2>
    <div style="font-size:18px; font-weight:bold; color:#34d399; margin:10px 0;">🏦 الخزنة المركزية: {{ vault_balance }} USDD</div>
    <a href="/dashboard" style="background:#38bdf8; color:#000; padding:8px 16px; text-decoration:none; border-radius:10px; font-weight:900; font-size:13px;">الرئيسية</a>

    {% if msg %}<div style="background:#065f46; color:#34d399; padding:10px; border-radius:10px; margin:15px auto; max-width:500px; font-weight:bold; font-size:14px;">{{ msg }}</div>{% endif %}

    <div class="box">
        <h3 style="color:#ffd700; margin-top:0; font-size:17px; text-align:center;">➕ إنشاء حساب مشرف جديد (مستأجر)</h3>
        <form method="POST">
            <input type="hidden" name="action" value="create_supervisor">
            <label>اسم المشرف:</label>
            <input type="text" name="username" required placeholder="اسم المشرف...">
            <label>كلمة المرور:</label>
            <input type="password" name="password" required placeholder="كلمة المرور...">
            <label>اسم الشركة / الوكيل:</label>
            <input type="text" name="owner_name" placeholder="اسم الوكيل...">
            <button type="submit" style="background:#ffd700; color:#000; font-weight:900; padding:12px; border:none; border-radius:8px; width:100%; cursor:pointer; margin-top:10px;">إنشاء المشرف</button>
        </form>
    </div>

    <div class="box" style="border-color:#38bdf8;">
        <h3 style="color:#38bdf8; margin-top:0; font-size:17px; text-align:center;">💳 بيع رصيد لمشرف (تمويل)</h3>
        <form method="POST">
            <input type="hidden" name="action" value="sell_to_supervisor">
            <label>اختر المشرف:</label>
            <select name="target_sup" required>
                <option value="">اختر المشرف</option>
                {% for s in supervisors %}
                <option value="{{ s.username }}">{{ s.username }} (رصيده: {{ s.balance }})</option>
                {% endfor %}
            </select>
            <label>المبلغ (USDD):</label>
            <input type="number" name="amount" min="1" required placeholder="المبلغ...">
            <button type="submit" style="background:#38bdf8; color:#000; font-weight:900; padding:12px; border:none; border-radius:8px; width:100%; cursor:pointer; margin-top:10px;">إتمام بيع الرصيد</button>
        </form>
    </div>

    <div style="background: rgba(25,30,48,0.9); padding: 20px; border-radius: 20px; max-width: 900px; margin: 20px auto; overflow-x:auto; box-sizing:border-box;">
        <h3 style="color:#ffd700; font-size:17px;">📋 قائمة المشرفين المستأجرين</h3>
        <table>
            <tr><th>المشرف</th><th>الوكيل</th><th>الرصيد المتاح</th></tr>
            {% for s in supervisors %}
            <tr><td><b>{{ s.username }}</b></td><td>{{ s.owner_name }}</td><td style="color:#34d399;">{{ s.balance }} USDD</td></tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

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
        .player-info-box { background: rgba(15,20,32,0.9); border: 2px solid #34d399; padding: 10px; border-radius: 12px; margin-top: 15px; text-align: right; box-sizing: border-box; font-size: 14px; }
        #insufficientBalanceModal { display: none; position: fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.85); justify-content:center; align-items:center; z-index:200; box-sizing: border-box; padding: 15px; }
    </style>
</head>
<body>
    {{ lang_bar | safe }}
    <div class="card">
        <div class="header-box">
            <h2 style="color: #ffd700; margin: 0 0 6px 0; font-size: 18px;">احجز رقم ب 2 usdd واربح 70 usdd فورا</h2>
            <p style="color: #f8fafc; margin: 0; font-size: 14px; font-weight: bold;">لوحة المشرف: <span style="color:#38bdf8;">{{ sup_name }}</span></p>
        </div>

        <div class="draw-screen-box"><div id="slotScreen" class="slot-screen">--</div></div>
        <div id="winnerAnnouncement" class="winner-msg"></div>

        <div id="insufficientBalanceModal">
            <div style="background:#1a1c29; padding:25px; border-radius:20px; border:3px solid #ef4444; width:100%; max-width:380px; text-align:center; box-sizing: border-box;">
                <h3 style="color:#ef4444; font-size:20px; margin-top:0;">⚠️ تنبيه</h3>
                <p id="modalErrorText" style="font-size:15px; color:#fff; font-weight:bold; margin:12px 0;">رصيدك غير كافي أو أن الزائر لا يحق له الحجز!</p>
                <button onclick="closeInsufficientModal()" style="background:#ffd700; color:#000; padding:8px 20px; font-weight:900; border:none; border-radius:10px; cursor:pointer; font-size:14px;">حسناً</button>
            </div>
        </div>

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

        {% if role == 'supervisor' or username == 'admin1' %}
            <div style="margin-top:20px;">
                <button type="button" onclick="triggerDraw()" style="background: linear-gradient(135deg, #22c55e, #15803d); color: #fff; font-weight: 900; padding: 12px 25px; border: none; border-radius: 12px; cursor: pointer; font-size: 16px;">⚡ السحب الخاص بلوحتك</button>
            </div>
        {% endif %}
    </div>

    <script>
        function handleAction(actionType, numberVal) {
            let fd = new FormData(); fd.append('action_type', actionType); fd.append('number', numberVal);
            fetch('/game_golden_number', { method: 'POST', body: fd }).then(res => res.json()).then(data => {
                if(data.success) { location.reload(); }
                else {
                    if(data.msg) {
                        document.getElementById('modalErrorText').innerText = data.msg;
                        document.getElementById('insufficientBalanceModal').style.display = 'flex';
                    }
                }
            });
        }
        function closeInsufficientModal() { document.getElementById('insufficientBalanceModal').style.display = 'none'; }
        function triggerDraw() {
            let fd = new FormData(); fd.append('action_type', 'admin_draw');
            fetch('/game_golden_number', { method: 'POST', body: fd }).then(res => res.json()).then(data => {
                if(data.winning_number) {
                    document.getElementById('slotScreen').innerText = '#' + data.winning_number;
                    document.getElementById('winnerAnnouncement').innerText = data.msg;
                    setTimeout(() => location.reload(), 5000);
                } else if(data.msg) { alert(data.msg); }
            });
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
        @media(max-width: 768px) { .roulette-table { grid-template-columns: 30px repeat(12, minmax(26px, 1fr)); grid-template-rows: repeat(3, 38px); padding: 4px; gap: 2px; } }
        .r-cell { display: flex; flex-direction: column; align-items: center; justify-content: center; font-weight: bold; border-radius: 5px; cursor: pointer; color: #fff; font-size: 14px; transition: 0.15s; user-select: none; border: 1px solid rgba(255,255,255,0.2); box-sizing: border-box; }
        @media(max-width: 768px) { .r-cell { font-size: 11px; } }
        .r-cell.zero { grid-row: span 3; background: #047857; border-color: #ffd700; font-size: 18px; }
        .r-cell.red { background: #dc2626; }
        .r-cell.black { background: #111827; }
        .r-cell:hover { transform: scale(1.04); border-color: #ffd700; }
        .r-cell.selected { border: 2px solid #ffd700 !important; box-shadow: 0 0 8px #ffd700; }
        .r-cell.winner-highlight { background: #fbbf24 !important; color: #000 !important; font-size: 16px; border: 2px solid #fff !important; box-shadow: 0 0 20px #ffd700; }
        .controls-grid { display: flex; gap: 6px; justify-content: center; flex-wrap: wrap; margin-bottom: 10px; box-sizing: border-box; }
        .btn-ctrl { padding: 8px 10px; font-weight: 900; border-radius: 8px; border: none; cursor: pointer; font-size: 12px; }
        .btn-red { background: #dc2626; color: #fff; }
        .btn-black { background: #111827; color: #fff; border: 1px solid #555; }
        .btn-rand { background: #d97706; color: #000; }
        .btn-undo { background: #4b5563; color: #fff; }
        .btn-double { background: #3b82f6; color: #fff; }
        .btn-repeat { background: #8b5cf6; color: #fff; }
    </style>
</head>
<body>
    {{ lang_bar | safe }}
    <div class="card">
        <h2 style="color:#ffd700; margin-top:0; font-size: 20px;">🎰 طاولة روليت الحظ العالمية</h2>
        <p style="font-size: 13px; margin: 5px 0;"><b>رصيدك: <span id="rouletteBal">{{ balance }}</span> USDD</b></p>
        <div><div id="timerBox" class="timer-box">⏳ وقت الرهان المتبقي: 15 ث</div></div>
        <div><div id="spinScreen" class="spin-screen">--</div></div>
        <div class="total-bet-display">🎯 إجمالي الرهان الحالي: <span id="currentTotalBet">0</span> USDD</div>
        <div id="rouletteMsg" style="font-weight:900; color:#34d399; margin-bottom:8px; min-height:18px; font-size: 13px;">اختر أرقامك من الطاولة أدناه</div>
        
        <div class="controls-grid">
            <button class="btn-ctrl btn-red" onclick="selectRed()">حجز كل الحمر</button>
            <button class="btn-ctrl btn-black" onclick="selectBlack()">حجز كل السود</button>
            <button class="btn-ctrl btn-rand" onclick="selectRandom10()">حجز 10 عشوائي</button>
            <button class="btn-ctrl btn-double" onclick="doubleBets()">دوبلت الرهانات (x2)</button>
            <button class="btn-ctrl btn-repeat" onclick="repeatLastRoundBets()">إعادة الرهان السابق</button>
            <button class="btn-ctrl btn-undo" onclick="undoLast()">تراجع عن الأخيرة</button>
        </div>

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
        let bets = {}; let actionHistory = []; let lastRoundBets = {};
        let redNums = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36];
        let blackNums = [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35];
        let timeLeft = 15; let timerInterval = null; let gameActive = true;
        
        function startTimer() {
            timerInterval = setInterval(() => {
                timeLeft--;
                let tBox = document.getElementById('timerBox');
                if(tBox) tBox.innerText = `⏳ وقت الرهان المتبقي: ${timeLeft} ث`;
                if(timeLeft <= 0) { clearInterval(timerInterval); gameActive = false; if(tBox) tBox.innerText = `🛑 انتهى وقت الرهان، بدء السحب...`; setTimeout(executeDraw, 2000); }
            }, 1000);
        }
        startTimer();

        function getTotalBetsCount() { let count = 0; for(let k in bets) count += bets[k]; return count; }
        function updateTotalBetDisplay() { let total = 0; for(let k in bets) total += bets[k]; document.getElementById('currentTotalBet').innerText = total; }

        function toggleNum(n) {
            if(!gameActive) { alert("انتهى وقت الرهان!"); return; }
            if(!bets[n] && getTotalBetsCount() >= 21) { alert("حد أقصى 21 رقماً!"); return; }
            if(!bets[n]) bets[n] = 0;
            if(bets[n] >= 10) { alert("حد أقصى دوبلت 10 مرات!"); return; }
            bets[n]++; actionHistory.push(n);
            fetch('/game_roulette_bet', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({action:'add', number:n})})
            .then(res => res.json()).then(d => {
                if(d.success) { document.getElementById('rouletteBal').innerText = d.balance; updateUI(); }
                else { bets[n]--; actionHistory.pop(); alert(d.msg || "رصيد غير كافي!"); }
            });
        }

        function undoLast() {
            if(!gameActive) { alert("لا يمكن التراجع بعد بدء السحب!"); return; }
            if(actionHistory.length === 0) return;
            let lastNum = actionHistory.pop();
            if(bets[lastNum]) { bets[lastNum]--; if(bets[lastNum] <= 0) delete bets[lastNum]; }
            fetch('/game_roulette_bet', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({action:'remove', number:lastNum})})
            .then(res => res.json()).then(d => { if(d.success) { document.getElementById('rouletteBal').innerText = d.balance; updateUI(); } });
        }

        function updateUI() {
            for(let i=0; i<=36; i++) {
                let cell = document.getElementById('r_cell_' + i); let badge = document.getElementById('r_mult_' + i);
                if(bets[i] && bets[i] > 0) { cell.classList.add('selected'); badge.innerText = `x${bets[i]} (${bets[i]}$)`; }
                else { cell.classList.remove('selected'); badge.innerText = `0$`; }
            }
            updateTotalBetDisplay();
        }

        function selectRed() { redNums.forEach(n => { if(getTotalBetsCount() < 21) toggleNum(n); }); }
        function selectBlack() { blackNums.forEach(n => { if(getTotalBetsCount() < 21) toggleNum(n); }); }
        function selectRandom10() {
            let all = []; for(let i=0; i<=36; i++) all.push(i);
            for(let i=0; i<10; i++) { if(getTotalBetsCount() >= 21) break; let r = all[Math.floor(Math.random()*all.length)]; toggleNum(r); }
        }
        function doubleBets() { for(let k in bets) { if(bets[k] > 0 && bets[k] < 10) { toggleNum(parseInt(k)); } } }
        function repeatLastRoundBets() {
            if(!gameActive) return;
            for(let k in lastRoundBets) { let cnt = lastRoundBets[k]; for(let i=0; i<cnt; i++) { if(getTotalBetsCount() < 21) toggleNum(parseInt(k)); } }
        }

        function executeDraw() {
            lastRoundBets = Object.assign({}, bets);
            fetch('/game_roulette_draw', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({bets: bets})})
            .then(res => res.json()).then(data => { if(data.success) { runSpinAnimation(data.winning_number, data.msg, data.balance); } });
        }

        function runSpinAnimation(winningNum, finalMsg, newBal) {
            let screen = document.getElementById('spinScreen'); let msgEl = document.getElementById('rouletteMsg');
            let counter = 0;
            let interval = setInterval(() => {
                screen.innerText = '#' + Math.floor(Math.random() * 37); counter++;
                if(counter > 25) {
                    clearInterval(interval); screen.innerText = '#' + winningNum; msgEl.innerText = finalMsg;
                    document.getElementById('rouletteBal').innerText = newBal;
                    let winCell = document.getElementById('r_cell_' + winningNum);
                    if(winCell) { winCell.className = "r-cell winner-highlight"; }
                    setTimeout(() => { location.reload(); }, 6000);
                }
            }, 80);
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
        .box { width: 95px; height: 110px; background: linear-gradient(145deg, #581c87, #3b0764); border: 3px solid #ffd700; border-radius: 18px; color: #ffd700; font-size: 17px; font-weight: 900; cursor: pointer; display: flex; flex-direction: column; align-items: center; justify-content: center; box-sizing: border-box; transition: 0.3s; box-shadow: 0 8px 20px rgba(0,0,0,0.7); }
        .box:hover { border-color: #fff; transform: translateY(-3px); }
        .box.booked { background: linear-gradient(145deg, #7f1d1d, #450a0a) !important; border-color: #ef4444 !important; color: #fca5a5 !important; cursor: not-allowed; }
        .box.my { background: linear-gradient(145deg, #1e3a8a, #172554) !important; border-color: #60a5fa !important; color: #93c5fd !important; }
        .slot-box { font-size: 38px; font-weight: 900; color: #ffd700; background: #000; padding: 12px; border-radius: 15px; border: 3px solid #b8860b; display: inline-block; min-width: 140px; box-sizing: border-box; }
    </style>
</head>
<body>
    {{ lang_bar | safe }}
    <div class="card">
        <h2 style="color:#ffd700; font-size: 20px; margin-top:0;">🏛️ إمبراطورية الأرقام الخاصة بالمشرف: <span style="color:#38bdf8;">{{ sup_name }}</span></h2>
        <p style="font-size:14px; color:#fde047; margin:5px 0;">سعر الحجز: 50 USDD | الجائزة الكبرى: 200 USDD</p>

        <div style="background:#05030a; padding:15px; border-radius:18px; border:3px solid #ffd700; margin:12px 0; box-sizing: border-box;">
            <div id="empireSlot" class="slot-box">--</div>
            <div id="empireAnnouncement" style="font-size:15px; color:#34d399; margin-top:8px; font-weight:900;">في انتظار السحب الملكي...</div>
        </div>

        <div class="boxes">
            {% for i in range(1, 6) %}
                {% if i in bookings %}
                    {% if bookings[i] == username %}
                        <button onclick="empAction('cancel', {{ i }})" class="box my" id="emp_box_{{ i }}"><span>👑</span><span>رقم {{ i }}</span><span style="font-size:11px; margin-top:4px;">تراجع</span></button>
                    {% else %}
                        <div class="box booked" id="emp_box_{{ i }}"><span>👑</span><span>رقم {{ i }}</span><span style="font-size:10px; margin-top:4px;">{{ bookings[i] }}</span></div>
                    {% endif %}
                {% else %}
                    <button onclick="empAction('book', {{ i }})" class="box" id="emp_box_{{ i }}"><span>👑</span><span>رقم {{ i }}</span><span style="font-size:11px; margin-top:4px; color:#fef08a;">50$</span></button>
                {% endif %}
            {% endfor %}
        </div>

        {% if role == 'supervisor' or username == 'admin1' %}
            <div style="margin-top:20px;">
                <button onclick="empAction('admin_draw', 0)" style="background: linear-gradient(135deg, #22c55e, #15803d); color: #fff; padding: 12px 25px; font-weight: 900; border: none; border-radius: 12px; cursor: pointer; font-size: 16px;">⚡ بدء السحب الخاص بلوحتك</button>
            </div>
        {% endif %}
    </div>

    <script>
        function empAction(type, box) {
            let fd = new FormData(); fd.append('action_type', type); fd.append('box_number', box);
            fetch('/game_numbers_empire', {method:'POST', body:fd}).then(r=>r.json()).then(d=>{
                if(d.winning_number) {
                    alert("الرقم الفائز هو: #" + d.winning_number + " - " + d.msg);
                    location.reload();
                } else {
                    if(d.msg) alert(d.msg);
                    location.reload();
                }
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
        @media(max-width: 768px){ .wheel-grid { grid-template-columns: repeat(5, 1fr); gap: 5px; } }
        .wheel-btn { background: #1f2937; border: 2px solid #ffd700; border-radius: 10px; padding: 10px 5px; font-size: 16px; font-weight: 900; color: #fff; cursor: pointer; transition: 0.2s; box-sizing: border-box; width: 100%; aspect-ratio: 1; display:flex; align-items:center; justify-content:center; }
        .wheel-btn.selected { background: #d97706 !important; color: #000 !important; border-color: #fff !important; transform: scale(1.05); }
        .spin-screen { font-size: 38px; font-weight: 900; color: #ffd700; background: #000; padding: 10px 15px; border-radius: 12px; border: 3px solid #b8860b; display: inline-block; min-width: 140px; margin: 10px 0; letter-spacing: 2px; max-width: 100%; box-sizing: border-box; }
        .selection-box { background: rgba(15,20,32,0.9); border: 2px solid #38bdf8; padding: 10px; border-radius: 12px; margin-top: 12px; text-align: right; box-sizing: border-box; font-size: 14px; }
    </style>
</head>
<body>
    {{ lang_bar | safe }}
    <div class="card">
        <h2 style="color:#ffd700; margin-top:0; font-size: 20px;">🎡 عجلة الحظ (20 رقم)</h2>
        <p style="font-size:14px; color:#ffd700; margin:5px 0;">سعر الحجز للرقم: 1 USDD | الجائزة: 20 USDD (حد أقصى 10 أرقام)</p>
        <div><div id="wheelSlot" class="spin-screen">--</div></div>
        <div id="wheelMsg" style="font-size:14px; font-weight:900; color:#34d399; margin:6px 0;">اختر من 1 إلى 10 أرقام وابدأ السحب</div>
        <div class="wheel-grid">
            {% for n in range(1, 21) %}
                <button type="button" id="w_num_{{ n }}" onclick="toggleWheelNum({{ n }})" class="wheel-btn">{{ n }}</button>
            {% endfor %}
        </div>
        <div class="selection-box">
            <h4 style="color: #38bdf8; margin-top:0; font-size: 14px;">📋 أرقامك المختارة وقيمة الرهان</h4>
            <p style="margin: 4px 0;"><b>الأرقام المحددة:</b> <span id="selectedListText" style="color: #ffd700;">لا توجد أرقام مختارة</span></p>
            <p style="margin: 4px 0;"><b>إجمالي الرهان:</b> <span id="totalCostText" style="color: #34d399;">0 USDD</span></p>
        </div>
        <button type="button" onclick="spinWheel()" style="padding: 12px 35px; background: linear-gradient(135deg,#22c55e,#15803d); color: #fff; font-weight: 900; font-size: 16px; border: none; border-radius: 14px; cursor: pointer; margin-top: 15px;">ابدأ السحب 🎡</button>
    </div>
    <script>
        let wheelSelected = [];
        function toggleWheelNum(n) {
            let idx = wheelSelected.indexOf(n);
            if(idx > -1) { wheelSelected.splice(idx, 1); document.getElementById('w_num_' + n).classList.remove('selected'); }
            else {
                if(wheelSelected.length >= 10) { alert("حد أقصى 10 أرقام!"); return; }
                wheelSelected.push(n); document.getElementById('w_num_' + n).classList.add('selected');
            }
            let cost = wheelSelected.length * 1.0;
            document.getElementById('selectedListText').innerText = wheelSelected.length > 0 ? wheelSelected.join(', ') : 'لا توجد أرقام مختارة';
            document.getElementById('totalCostText').innerText = cost + ' USDD';
        }
        function spinWheel() {
            if(wheelSelected.length === 0) { alert("اختر رقماً واحداً على الأقل!"); return; }
            let fd = new FormData(); fd.append('selected_numbers', JSON.stringify(wheelSelected));
            fetch('/game_number_wheel', {method: 'POST', body: fd}).then(res => res.json()).then(d => {
                if(d.success) {
                    document.getElementById('wheelSlot').innerText = '#' + d.winning_num;
                    document.getElementById('wheelMsg').innerText = d.msg;
                    setTimeout(() => location.reload(), 4000);
                } else { alert(d.msg || "رصيد غير كافي!"); }
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
        .box-cell { background: linear-gradient(145deg, #7c3aed, #4c1d95); border: 3px solid #ffd700; border-radius: 15px; width: 85px; height: 95px; font-size: 30px; font-weight: 900; color: #fff; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: 0.2s; user-select: none; box-sizing: border-box; }
        .box-cell.revealed { background: #1e1b4b !important; border-color: #38bdf8 !important; cursor: default; }
    </style>
</head>
<body>
    {{ lang_bar | safe }}
    <div class="card">
        <h2 style="color:#ffd700; margin-top:0; font-size: 20px;">🎟️ لعبة اكشف واربح</h2>
        <p style="font-size:14px; color:#ffd700; margin:5px 0;">تكلفة المحاولة: 1 USDD | الجائزة الكبرى: 100 USDD</p>
        <div id="revealMsg" style="font-size: 15px; font-weight: 900; color: #34d399; margin: 12px 0;">اضغط ابدأ ثم اختر 3 صناديق</div>
        <div class="boxes-grid">
            {% for i in range(1, 6) %}<div class="box-cell" id="b_{{ i }}" onclick="clickBox({{ i }})">📦</div>{% endfor %}
        </div>
        <button type="button" id="startBtn" onclick="startReveal()" style="padding: 12px 35px; background: linear-gradient(135deg,#ffd700,#ff8c00); color: #000; font-weight: 900; font-size: 16px; border: none; border-radius: 14px; cursor: pointer; margin-top: 10px;">ابدأ المحاولة (1 USDD)</button>
    </div>
    <script>
        let sessionRevealed = []; let clicksCount = 0; let gameActive = false;
        function startReveal() {
            fetch('/game_reveal_and_win', {method: 'POST'}).then(res => res.json()).then(d => {
                if(d.success) {
                    sessionRevealed = d.revealed; clicksCount = 0; gameActive = true;
                    document.getElementById('revealMsg').innerText = "اختر 3 صناديق الآن!";
                    document.getElementById('startBtn').style.display = 'none';
                    for(let i=1; i<=5; i++) { let c = document.getElementById('b_' + i); c.innerText = "📦"; c.classList.remove('revealed'); }
                } else { alert(d.msg || "رصيد غير كافي!"); }
            });
        }
        function clickBox(idx) {
            if(!gameActive) return;
            let c = document.getElementById('b_' + idx);
            if(c.classList.contains('revealed')) return;
            if(clicksCount < sessionRevealed.length) {
                c.innerText = sessionRevealed[clicksCount]; c.classList.add('revealed'); clicksCount++;
                if(clicksCount === sessionRevealed.length) {
                    gameActive = false;
                    setTimeout(() => {
                        fetch('/game_reveal_result_check', {method: 'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({revealed: sessionRevealed})})
                        .then(res => res.json()).then(resData => {
                            document.getElementById('revealMsg').innerText = resData.msg;
                            document.getElementById('startBtn').style.display = 'inline-block';
                        });
                    }, 500);
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
        <p style="font-size:14px; color:#ffd700; margin:5px 0;">تكلفة المحاولة: 1 USDD</p>
        <div id="arrowScreen" style="font-size:28px; font-weight:900; color:#ffd700; background:#000; padding:15px; border-radius:12px; border:2px solid #38bdf8; margin:15px 0;">🎯 جاهز للرمي</div>
        <div id="arrowMsg" style="font-size: 15px; font-weight: 900; color: #34d399; margin: 10px 0;"></div>
        <button type="button" onclick="throwArrow()" style="padding: 14px 35px; background: linear-gradient(135deg,#22c55e,#15803d); color: #fff; font-weight: 900; font-size: 18px; border: none; border-radius: 14px; cursor: pointer;">🎯 ارم السهم (1 USDD)</button>
    </div>
    <script>
        function throwArrow() {
            fetch('/game_arrow_wheel', {method: 'POST'}).then(res => res.json()).then(d => {
                if(d.success) {
                    document.getElementById('arrowScreen').innerText = d.hit_target;
                    document.getElementById('arrowMsg').innerText = d.msg;
                } else { alert(d.msg || "رصيد غير كافي!"); }
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
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>الدردشة والدعم</title>
    <style>
        body { font-family: Tahoma; background: #151928; color: #fff; padding: 10px; text-align: center; box-sizing:border-box; margin:0; }
        .chat-box { background: rgba(25,30,48,0.95); border: 2px solid #ffd700; border-radius: 20px; max-width: 650px; margin: 15px auto; padding: 15px; text-align: right; box-sizing:border-box; width:100%; }
        .messages-area { height: 320px; background: #0a0d16; border: 1px solid #444; border-radius: 12px; padding: 12px; overflow-y: scroll; margin-bottom: 12px; display: flex; flex-direction: column; gap: 8px; box-sizing:border-box; }
        .msg { padding: 8px 12px; border-radius: 10px; max-width: 85%; font-size: 14px; word-break: break-word; box-sizing:border-box; }
        .msg.user { background: #1e3a8a; align-self: flex-start; }
        .msg.admin { background: #065f46; align-self: flex-end; }
        input, button { padding: 10px; border-radius: 8px; border: 1px solid #444; font-size:14px; box-sizing:border-box; }
    </style>
</head>
<body>
    {{ lang_bar | safe }}
    <h2 style="font-size:20px;">💬 غرفة الدردشة والدعم الفني</h2>
    <a href="/dashboard" style="background:#3b82f6; color:#fff; padding:8px 16px; text-decoration:none; border-radius:10px; font-weight:900; font-size:14px;">الرئيسية</a>
    <div class="chat-box">
        <div class="messages-area" id="msgArea">
            {% for m in messages %}
            <div class="msg {% if m.sender == username %}user{% else %}admin{% endif %}">
                <b style="font-size:11px; color:#ffd700;">{{ m.sender }}:</b><br>
                <span>{{ m.message }}</span>
            </div>
            {% endfor %}
        </div>
        <form method="POST" style="display:flex; gap:8px; flex-wrap:wrap;">
            <input type="text" name="message" required placeholder="اكتب رسالتك..." style="flex:1; min-width:200px; background:#0a0d16; color:#fff;">
            <button type="submit" style="background:#22c55e; color:#000; font-weight:900; cursor:pointer;">إرسال</button>
        </form>
    </div>
    <script>let area = document.getElementById('msgArea'); area.scrollTop = area.scrollHeight;</script>
</body>
</html>
"""

# --- Routes Logic ---

@app.route('/set_lang/<lang>')
def set_lang(lang):
    if lang in TRANSLATIONS: session['lang'] = lang
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/api/sync_balance')
def api_sync_balance():
    if 'username' not in session: return jsonify({"balance": 0.0})
    user = User.query.filter_by(username=session['username']).first()
    return jsonify({"balance": user.balance if user else 0.0})

@app.route('/guest_login')
def guest_login():
    guest_name = 'guest_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
    u = User(username=guest_name, password='guest_password', balance=10.0, role='user', created_by='system', owner_name='زائر تصفح')
    db.session.add(u)
    db.session.commit()
    session.clear()
    session['username'] = guest_name
    session['balance'] = 10.0
    session['role'] = 'user'
    return redirect(url_for('dashboard'))

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
    if not user: return redirect(url_for('logout'))
    t = get_t()
    return render_template_string(DASHBOARD_PAGE, t=t, lang_key=session.get('lang', 'ar'), lang_bar=get_lang_bar(), username=user.username, balance=user.balance, role=user.role, owner_name=user.owner_name)

# --- لوحة تحكم المشرف (Supervisor) ---
@app.route('/supervisor_dashboard', methods=['GET', 'POST'])
def supervisor_dashboard():
    if 'username' not in session: return redirect(url_for('login'))
    sup = User.query.filter_by(username=session['username'], role='supervisor').first()
    if not sup: return redirect(url_for('dashboard'))
    msg = None
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'create_player':
            uname = request.form.get('username', '').strip()
            pwd = request.form.get('password', '').strip()
            owner = request.form.get('owner_name', 'زبون تابع للمشرف').strip()
            if uname and pwd and not User.query.filter_by(username=uname).first():
                new_p = User(username=uname, password=pwd, balance=0.0, role='user', created_by=sup.username, owner_name=owner)
                db.session.add(new_p)
                db.session.commit()
                msg = f"تم إنشاء اللاعب {uname} بنجاح!"
            else:
                msg = "خطأ: اسم المستخدم موجود مسبقاً أو بيانات ناقصة!"
        elif action == 'transfer_balance':
            target_uname = request.form.get('target_user')
            amount = float(request.form.get('amount', 0))
            t_type = request.form.get('transfer_type')
            target_user = User.query.filter_by(username=target_uname, created_by=sup.username).first()
            if target_user:
                if t_type == 'sell':
                    if sup.balance >= amount:
                        sup.balance -= amount
                        target_user.balance += amount
                        db.session.commit()
                        msg = f"تم شحن {amount} USDD لللاعب {target_user.username} بنجاح!"
                    else:
                        msg = "رصيدك غير كافي لشحن هذا المبلغ!"
                elif t_type == 'withdraw':
                    if target_user.balance >= amount:
                        target_user.balance -= amount
                        sup.balance += amount
                        db.session.commit()
                        msg = f"تم سحب {amount} USDD من اللاعب {target_user.username} بنجاح!"
                    else:
                        msg = "رصيد اللاعب غير كافي!"
    players = User.query.filter_by(created_by=sup.username, role='user').all()
    return render_template_string(SUPERVISOR_DASHBOARD_PAGE, lang_bar=get_lang_bar(), supervisor=sup, players=players, msg=msg)

# --- لوحة الآدمن لإنشاء المشرفين وتمويلهم ---
@app.route('/admin_accounting', methods=['GET', 'POST'])
def admin_accounting():
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
                msg = f"تم إنشاء المشرف {uname} بنجاح!"
            else:
                msg = "خطأ: اسم المشرف موجود مسبقاً!"
        elif action == 'sell_to_supervisor':
            target_sup = request.form.get('target_sup')
            amount = float(request.form.get('amount', 0))
            sup_user = User.query.filter_by(username=target_sup, role='supervisor').first()
            if sup_user and vault.vault_balance >= amount:
                vault.vault_balance -= amount
                sup_user.balance += amount
                db.session.commit()
                msg = f"تم تمويل المشرف {sup_user.username} بـ {amount} USDD بنجاح!"
            else:
                msg = "خطأ في الرصيد أو المشرف غير موجود!"
    supervisors = User.query.filter_by(role='supervisor').all()
    return render_template_string(ADMIN_SUPERVISORS_PAGE, lang_bar=get_lang_bar(), vault_balance=vault.vault_balance if vault else 0.0, supervisors=supervisors, msg=msg)

@app.route('/admin_game_control', methods=['GET'])
def admin_game_control():
    if 'username' not in session or session.get('username') != 'admin1': return redirect(url_for('dashboard'))
    return "<h2 style='text-align:center;color:gold;background:#151928;padding:50px;'>غرفة التحكم بالألعاب مفعلة وجاهزة! <a href='/dashboard'>الرئيسية</a></h2>"

# --- ألعاب معزولة لكل مشرف ---
def get_player_supervisor(username):
    user = User.query.filter_by(username=username).first()
    if not user: return 'admin1'
    if user.role == 'supervisor': return user.username
    if user.role == 'admin': return 'admin1'
    creator = User.query.filter_by(username=user.created_by).first()
    if creator and creator.role == 'supervisor':
        return creator.username
    return 'admin1'

@app.route('/game_golden_number', methods=['GET', 'POST'])
def game_golden_number():
    if 'username' not in session: return redirect(url_for('login'))
    username = session['username']
    user = User.query.filter_by(username=username).first()
    sup_name = get_player_supervisor(username)
    t = get_t()
    if username.startswith('guest_'):
        if request.method == 'POST': return jsonify({"success": False, "msg": "حسابات الزوار لا يمكنها المشاركة في هذه اللعبة!"})

    if request.method == 'POST':
        action = request.form.get('action_type')
        if action == 'book':
            num = int(request.form.get('number', 0))
            existing = GoldenNumberBooking.query.filter_by(number=num).first() # لعزل الحجوزات
            if existing: return jsonify({"success": False, "msg": "هذا الرقم محجوز مسبقاً!"})
            if user.balance >= 2.0:
                user.balance -= 2.0
                db.session.add(GoldenNumberBooking(username=username, number=num, booking_date=get_local_time()))
                db.session.commit()
                return jsonify({"success": True})
            else:
                return jsonify({"success": False, "msg": "رصيد غير كافي"})
        elif action == 'cancel':
            num = int(request.form.get('number', 0))
            b = GoldenNumberBooking.query.filter_by(number=num, username=username).first()
            if b:
                db.session.delete(b)
                user.balance += 2.0
                db.session.commit()
                return jsonify({"success": True, "msg": "تم الاسترداد"})
            return jsonify({"success": False, "msg": "خطأ في التراجع"})
        elif action == 'admin_draw':
            winning_num = random.randint(1, 50)
            winner_b = GoldenNumberBooking.query.filter_by(number=winning_num).first()
            msg = f"الرقم الفائز هو #{winning_num}"
            if winner_b:
                winner_u = User.query.filter_by(username=winner_b.username).first()
                if winner_u:
                    winner_u.balance += 70.0
                    msg = f"الفائز بالرقم #{winning_num} هو اللاعب {winner_u.username} وربح 70 USDD!"
            GoldenNumberBooking.query.delete()
            db.session.commit()
            return jsonify({"success": True, "winning_number": winning_num, "msg": msg})
    bookings = {b.number: b.username for b in GoldenNumberBooking.query.all()}
    my_list = [b.number for b in GoldenNumberBooking.query.filter_by(username=username).all()]
    return render_template_string(GAME_GOLDEN_PAGE, t=t, lang_key=session.get('lang', 'ar'), lang_bar=get_lang_bar(), username=username, balance=user.balance, bookings=bookings, my_nums_str=', '.join(map(str, my_list)) if my_list else 'لا يوجد', my_total_cost=len(my_list)*2.0, sup_name=sup_name, role=user.role)

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
    elif data.get('action') == 'remove':
        user.balance += 1.0
        db.session.commit()
        return jsonify({"success": True, "balance": user.balance})
    return jsonify({"success": False})

@app.route('/game_roulette_draw', methods=['POST'])
def game_roulette_draw():
    if 'username' not in session: return jsonify({"success": False})
    user = User.query.filter_by(username=session['username']).first()
    data = request.get_json() or {}
    bets = data.get('bets', {})
    winning_num = random.randint(0, 36)
    payout = 0.0
    if str(winning_num) in bets:
        payout = float(bets[str(winning_num)]) * 20.0
        user.balance += payout
        db.session.commit()
        msg = f"🎉 مبروك! ظهر الرقم #{winning_num} وفزت بـ {payout} USDD!"
    else:
        msg = f"❌ حظ أوفر! الرقم الفائز كان #{winning_num}"
    return jsonify({"success": True, "winning_number": winning_num, "msg": msg, "balance": user.balance})

@app.route('/game_roulette')
def game_roulette():
    if 'username' not in session: return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    return render_template_string(GAME_ROULETTE_PAGE, t=get_t(), lang_key=session.get('lang', 'ar'), lang_bar=get_lang_bar(), balance=user.balance)

@app.route('/game_numbers_empire', methods=['GET', 'POST'])
def game_numbers_empire():
    if 'username' not in session: return redirect(url_for('login'))
    username = session['username']
    user = User.query.filter_by(username=username).first()
    sup_name = get_player_supervisor(username)
    if username.startswith('guest_'):
        if request.method == 'POST': return jsonify({"success": False, "msg": "حسابات الزوار لا يمكنها المشاركة في هذه اللعبة!"})

    if request.method == 'POST':
        action = request.form.get('action_type')
        box = int(request.form.get('box_number', 0))
        if action == 'book' and user.balance >= 50.0 and not NumbersEmpireBooking.query.filter_by(number=box).first():
            user.balance -= 50.0
            db.session.add(NumbersEmpireBooking(username=username, number=box, booking_date=get_local_time()))
            db.session.commit()
            return jsonify({"success": True, "msg": f"تم الحجز بالمربع #{box}"})
        elif action == 'cancel':
            b = NumbersEmpireBooking.query.filter_by(number=box, username=username).first()
            if b:
                db.session.delete(b)
                user.balance += 50.0
                db.session.commit()
                return jsonify({"success": True, "msg": "تم التراجع"})
        elif action == 'admin_draw':
            winning_num = random.randint(1, 5)
            winner_b = NumbersEmpireBooking.query.filter_by(number=winning_num).first()
            msg = f"فاز الرقم #{winning_num} بجائزة 200 USDD"
            if winner_b:
                winner_u = User.query.filter_by(username=winner_b.username).first()
                if winner_u:
                    winner_u.balance += 200.0
                    msg = f"الفائز بالرقم #{winning_num} هو {winner_u.username} وربح 200 USDD!"
            NumbersEmpireBooking.query.delete()
            db.session.commit()
            return jsonify({"success": True, "winning_number": winning_num, "msg": msg})
    bookings = {b.number: b.username for b in NumbersEmpireBooking.query.all()}
    return render_template_string(GAME_NUMBERS_EMPIRE_PAGE, t=get_t(), lang_key=session.get('lang', 'ar'), lang_bar=get_lang_bar(), username=username, balance=user.balance, bookings=bookings, sup_name=sup_name, role=user.role)

@app.route('/game_number_wheel', methods=['GET', 'POST'])
def game_number_wheel():
    if 'username' not in session: return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    if request.method == 'POST':
        nums = json.loads(request.form.get('selected_numbers', '[]'))
        cost = float(len(nums) * 1.0)
        if nums and user.balance >= cost:
            user.balance -= cost
            winning_num = random.randint(1, 20)
            msg = "حظ اوفر"
            if winning_num in nums:
                user.balance += 20.0
                msg = f"مبروك ربحت 20 USDD للرقم {winning_num}"
            db.session.commit()
            return jsonify({"success": True, "winning_num": winning_num, "balance": user.balance, "msg": msg})
        return jsonify({"success": False, "msg": "رصيد غير كافي!"})
    return render_template_string(GAME_NUMBER_WHEEL_PAGE, t=get_t(), lang_key=session.get('lang', 'ar'), lang_bar=get_lang_bar())

@app.route('/game_arrow_wheel', methods=['POST'])
def game_arrow_wheel():
    if 'username' not in session: return jsonify({"success": False})
    user = User.query.filter_by(username=session['username']).first()
    if user.balance >= 1.0:
        user.balance -= 1.0
        rand_val = random.random()
        if rand_val < 0.70: prize, label, msg = 1.0, 'استرداد 1$', "استرددت 1 USDD"
        elif rand_val < 0.75: prize, label, msg = 2.0, 'دوبل 2$', "🎉 ربحت 2 USDD"
        elif rand_val < 0.85: prize, label, msg = 0.5, 'نصف 0.5$', "استرددت 0.5 USDD"
        else: prize, label, msg = 0.0, 'حظ أوفر', "حظ أوفر!"
        user.balance += prize
        db.session.commit()
        return jsonify({"success": True, "hit_target": label, "msg": msg, "balance": user.balance})
    return jsonify({"success": False, "msg": "رصيد غير كافي!"})

@app.route('/game_arrow_wheel', methods=['GET'])
def game_arrow_wheel_get():
    if 'username' not in session: return redirect(url_for('login'))
    return render_template_string(GAME_ARROW_WHEEL_PAGE, t=get_t(), lang_key=session.get('lang', 'ar'), lang_bar=get_lang_bar())

@app.route('/game_reveal_and_win', methods=['POST'])
def game_reveal_and_win():
    if 'username' not in session: return jsonify({"success": False})
    user = User.query.filter_by(username=session['username']).first()
    if user.balance >= 1.0:
        user.balance -= 1.0
        db.session.commit()
        revealed = ['🦁', '🦁', random.choice(['7', '3'])] if random.random() < 0.5 else ['🦁', '7', '3']
        random.shuffle(revealed)
        session['reveal_res'] = revealed
        return jsonify({"success": True, "balance": user.balance, "revealed": revealed})
    return jsonify({"success": False, "msg": "رصيد غير كافي!"})

@app.route('/game_reveal_result_check', methods=['POST'])
def game_reveal_result_check():
    if 'username' not in session: return jsonify({"success": False})
    user = User.query.filter_by(username=session['username']).first()
    rev = session.get('reveal_res', [])
    lions = rev.count('🦁')
    if lions == 3:
        user.balance += 100.0; msg = "مبروك ربحت 100 USDD!"
    elif lions == 2:
        user.balance += 0.5; msg = "استرددت 0.5 USDD!"
    else:
        msg = "حظ أوفر!"
    db.session.commit()
    return jsonify({"success": True, "msg": msg, "balance": user.balance})

@app.route('/game_reveal_and_win', methods=['GET'])
def game_reveal_get():
    if 'username' not in session: return redirect(url_for('login'))
    return render_template_string(GAME_REVEAL_PAGE, t=get_t(), lang_key=session.get('lang', 'ar'), lang_bar=get_lang_bar())

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
    messages = ChatMessage.query.filter(((ChatMessage.sender == username) & (ChatMessage.recipient == 'admin1')) | ((ChatMessage.sender == 'admin1') & (ChatMessage.recipient == username))).all()
    return render_template_string(CHAT_PAGE, lang_bar=get_lang_bar(), username=username, messages=messages)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
