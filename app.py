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

# غرفة التحكم للـ 50 جولة قادمة لكل لعبة
class GameFutureDraw(db.Model):
    __tablename__ = 'game_future_draws'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    game_name = db.Column(db.String(50), nullable=False)
    round_index = db.Column(db.Integer, nullable=False)
    winning_number = db.Column(db.Integer, nullable=False)

# حالة المحاولات العالمية للعبة اكشف واربح
class RevealAndWinGlobalState(db.Model):
    __tablename__ = 'reveal_and_win_global'
    id = db.Column(db.Integer, primary_key=True)
    total_spins = db.Column(db.Integer, default=0)

# نظام الدردشة الفورية والسرية
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

# --- تهيئة الجداول ---
with app.app_context():
    db.create_all()
    vault = SystemVault.query.get(1)
    if not vault:
        db.session.add(SystemVault(id=1, vault_balance=1000000.0))
    if not User.query.filter_by(username='admin1').first():
        db.session.add(User(username='admin1', password='admin123', balance=0.0, role='admin', created_by='system', owner_name='المشرف العام'))
    if not RevealAndWinGlobalState.query.get(1):
        db.session.add(RevealAndWinGlobalState(id=1, total_spins=0))
    db.session.commit()

# --- قاموس الترجمات (6 لغات) ---
TRANSLATIONS = {
    'ar': {
        'dir': 'rtl', 'title': 'امبراطورية الأرقام', 'subtitle': 'منصة الألعاب التفاعلية الفائقة 12D',
        'login': 'دخول للبرنامج', 'username': 'اسم المستخدم', 'password': 'كلمة المرور', 'balance': 'الرصيد',
        'recharge': 'شحن رصيد', 'withdraw': 'سحب رصيد', 'change_pass': 'تغيير الباسورد', 'logout': 'خروج',
        'dashboard': 'لوحة التحكم', 'back_dash': '🏠 الرئيسية', 'customers': 'الزبائن', 'accounting': 'المحاسبة والخزنة',
        'game_control': '🎮 غرفة تحكم الألعاب', 'chat': '💬 الدردشة الفورية',
        'game1': 'الرقم الحنون', 'game2': 'روليت الحظ', 'game3': 'إمبراطورية الأرقام', 'game4': 'عجلة الحظ', 'game5': 'اكشف واربح',
        'cost': 'التكلفة', 'prize': 'الجائزة', 'book': 'حجز', 'cancel': 'تراجع', 'booked': 'محجوز',
        'spin': 'تدوير العجلة', 'draw_now': 'اسحب الآن'
    },
    'en': {
        'dir': 'ltr', 'title': 'Empire of Numbers', 'subtitle': 'Super Interactive 12D Gaming Platform',
        'login': 'Login', 'username': 'Username', 'password': 'Password', 'balance': 'Balance',
        'recharge': 'Recharge', 'withdraw': 'Withdraw', 'change_pass': 'Change Password', 'logout': 'Logout',
        'dashboard': 'Dashboard', 'back_dash': '🏠 Home', 'customers': 'Customers', 'accounting': 'Vault & Accounting',
        'game_control': '🎮 Game Control', 'chat': '💬 Live Chat',
        'game1': 'The Tender Number', 'game2': 'Lucky Roulette', 'game3': 'Empire of Numbers', 'game4': 'Wheel of Fortune', 'game5': 'Reveal & Win',
        'cost': 'Cost', 'prize': 'Prize', 'book': 'Book', 'cancel': 'Cancel', 'booked': 'Booked',
        'spin': 'Spin Wheel', 'draw_now': 'Draw Now'
    },
    'fr': {
        'dir': 'ltr', 'title': 'Empire des Nombres', 'subtitle': 'Plateforme de Jeux Super Interactive 12D',
        'login': 'Connexion', 'username': "Nom d'utilisateur", 'password': 'Mot de passe', 'balance': 'Solde',
        'recharge': 'Recharger', 'withdraw': 'Retirer', 'change_pass': 'Changer le mot de passe', 'logout': 'Déconnexion',
        'dashboard': 'Tableau de bord', 'back_dash': '🏠 Accueil', 'customers': 'Clients', 'accounting': 'Comptabilité et Coffre',
        'game_control': '🎮 Contrôle des Jeux', 'chat': '💬 Chat en Direct',
        'game1': 'Le Numéro Tendre', 'game2': 'Roulette Chanceuse', 'game3': 'Empire des Nombres', 'game4': 'Roue de la Fortune', 'game5': 'Révéler & Gagner',
        'cost': 'Coût', 'prize': 'Prix', 'book': 'Réserver', 'cancel': 'Annuler', 'booked': 'Réservé',
        'spin': 'Tourner', 'draw_now': 'Tirer'
    },
    'de': {
        'dir': 'ltr', 'title': 'Imperium der Zahlen', 'subtitle': 'Super Interaktive 12D Gaming Plattform',
        'login': 'Anmelden', 'username': 'Benutzername', 'password': 'Passwort', 'balance': 'Guthaben',
        'recharge': 'Aufladen', 'withdraw': 'Auszahlen', 'change_pass': 'Passwort ändern', 'logout': 'Abmelden',
        'dashboard': 'Dashboard', 'back_dash': '🏠 Startseite', 'customers': 'Kunden', 'accounting': 'Buchhaltung',
        'game_control': '🎮 Spielkontrolle', 'chat': '💬 Live-Chat',
        'game1': 'Die Zarte Nummer', 'game2': 'Glücks-Roulette', 'game3': 'Imperium der Zahlen', 'game4': 'Glücksrad', 'game5': 'Aufdecken & Gewinnen',
        'cost': 'Kosten', 'prize': 'Gewinn', 'book': 'Buchen', 'cancel': 'Abbrechen', 'booked': 'Gebucht',
        'spin': 'Drehen', 'draw_now': 'Ziehen'
    },
    'es': {
        'dir': 'ltr', 'title': 'Imperio de los Números', 'subtitle': 'Plataforma de Juegos Super Interactiva 12D',
        'login': 'Iniciar Sesión', 'username': 'Nombre de usuario', 'password': 'Contraseña', 'balance': 'Saldo',
        'recharge': 'Recargar', 'withdraw': 'Retirar', 'change_pass': 'Cambiar Contraseña', 'logout': 'Cerrar Sesión',
        'dashboard': 'Panel', 'back_dash': '🏠 Inicio', 'customers': 'Clientes', 'accounting': 'Contabilidad',
        'game_control': '🎮 Control de Juegos', 'chat': '💬 Chat en Vivo',
        'game1': 'El Número Tierno', 'game2': 'Ruleta de la Suerte', 'game3': 'Empire of Numbers', 'game4': 'Rueda de la Fortuna', 'game5': 'Revelar y Ganar',
        'cost': 'Costo', 'prize': 'Premio', 'book': 'Reservar', 'cancel': 'Cancelar', 'booked': 'Reservado',
        'spin': 'Girar', 'draw_now': 'Sorteo'
    },
    'fa': {
        'dir': 'rtl', 'title': 'امپراتوری اعداد', 'subtitle': 'پلتفرم بازی‌های تعاملی فوق‌العاده 12D',
        'login': 'ورود به برنامه', 'username': 'نام کاربری', 'password': 'رمز عبور', 'balance': 'موجودی',
        'recharge': 'شارژ حساب', 'withdraw': 'برداشت وجه', 'change_pass': 'تغییر رمز عبور', 'logout': 'خروج',
        'dashboard': 'داشبورد', 'back_dash': '🏠 صفحه اصلی', 'customers': 'مشتریان', 'accounting': 'حسابداری و خزانه',
        'game_control': '🎮 کنترل بازی‌ها', 'chat': '💬 پشتیبانی و چت',
        'game1': 'عدد مهربان', 'game2': 'رولت شانس', 'game3': 'امپراتوری اعداد', 'game4': 'گردونه شانس', 'game5': 'کشف کن و برنده شو',
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
<div style="padding: 10px 25px; background: rgba(18, 18, 25, 0.95); display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,215,0,0.2);">
    <div>
        <select onchange="location.href='/set_lang/' + this.value" style="background:#1a1c29; color:#ffd700; border:1px solid #ffd700; padding:6px 12px; border-radius:8px; font-weight:bold; cursor:pointer;">
            <option value="ar" {ar_sel}>العربية 🇸🇦</option>
            <option value="en" {en_sel}>English 🇬🇧</option>
            <option value="fr" {fr_sel}>Français 🇫🇷</option>
            <option value="de" {de_sel}>Deutsch 🇩🇪</option>
            <option value="es" {es_sel}>Español 🇪🇸</option>
            <option value="fa" {fa_sel}>فارسی 🇮🇷</option>
        </select>
    </div>
    <div style="display:flex; gap:15px; align-items:center;">
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

def get_next_winning_number(game_name, default_min, default_max):
    future = GameFutureDraw.query.filter_by(game_name=game_name).order_by(GameFutureDraw.round_index.asc()).first()
    if future:
        win_num = future.winning_number
        db.session.delete(future)
        db.session.commit()
        return win_num
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
        .action-bar { display: flex; justify-content: center; align-items: center; gap: 20px; margin: 25px auto; max-width: 950px; flex-wrap: wrap; background: rgba(20,24,38,0.95); padding: 20px; border-radius: 20px; border: 2px solid rgba(255,215,0,0.4); }
        .dropdown { position: relative; display: inline-block; }
        .drop-btn { background: linear-gradient(135deg, #22c55e, #15803d); color: #fff; padding: 12px 25px; font-weight: 900; border: none; border-radius: 12px; cursor: pointer; font-size: 16px; }
        .drop-btn.withdraw { background: linear-gradient(135deg, #ef4444, #991b1b); }
        .dropdown-content { display: none; position: absolute; background: #1a1c29; min-width: 240px; box-shadow: 0px 8px 16px rgba(0,0,0,0.5); z-index: 10; border-radius: 12px; border: 1px solid #ffd700; overflow: hidden; right: 0; }
        .dropdown-content a { color: #fff; padding: 12px 16px; text-decoration: none; display: block; text-align: right; cursor: pointer; font-size: 14px; }
        .dropdown-content a:hover { background: #2d3748; color: #ffd700; }
        .dropdown:hover .dropdown-content { display: block; }
        .redeem-box { display: flex; gap: 8px; align-items: center; background: #0a0d16; padding: 8px 15px; border-radius: 12px; border: 1px solid #ffd700; }
        .redeem-box input { background: transparent; border: none; color: #fff; padding: 5px; outline: none; font-size: 14px; }
        .redeem-box button { background: #ffd700; color: #000; border: none; padding: 6px 14px; border-radius: 8px; font-weight: 900; cursor: pointer; }
        .icons-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 20px; max-width: 1200px; margin: 30px auto; }
        @media (max-width: 1000px) { .icons-grid { grid-template-columns: repeat(2, 1fr); } }
        .icon-card { background: rgba(25,30,48,0.95); border: 3px solid rgba(184,134,11,0.6); border-radius: 28px; padding: 30px 15px; text-align: center; text-decoration: none; box-shadow: 0 20px 45px rgba(0,0,0,0.9); transition: 0.3s; }
        .icon-card:hover { border-color: #ffd700; transform: translateY(-8px); }
        .icon-logo { font-size: 60px; margin-bottom: 12px; }
        .icon-title { color: #ffd700; font-size: 18px; font-weight: 900; }
        #usdtModal { display: none; position: fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); justify-content:center; align-items:center; z-index:100; }
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

    <!-- شريط الإجراءات والكودات -->
    <div class="action-bar">
        <div class="dropdown">
            <button class="drop-btn">💳 {{ t.recharge }} ▾</button>
            <div class="dropdown-content">
                <a onclick="rechargeWhish()">شحن عبر Whish في لبنان</a>
                <a onclick="rechargeGooglePlay()">شراء USDD من متجر غوغل</a>
            </div>
        </div>

        <div class="redeem-box">
            <form method="POST" style="display:flex; gap:5px; margin:0;">
                <input type="hidden" name="action" value="redeem_card">
                <input type="text" name="card_code" placeholder="ضع كود الشحن هنا..." required>
                <button type="submit">تفعيل</button>
            </form>
        </div>

        <div class="dropdown">
            <button class="drop-btn withdraw">💸 {{ t.withdraw }} ▾</button>
            <div class="dropdown-content">
                <a onclick="withdrawWhish('{{ username }}', '{{ password }}')">سحب عبر Whish في لبنان</a>
                <a onclick="withdrawVisa('{{ username }}', '{{ password }}')">استلام فيزا مسبقة الدفع</a>
                <a onclick="openUsdtModal()">سحب عبر محفظة USDT</a>
            </div>
        </div>
    </div>

    {% if msg %}<div style="background:#065f46; color:#34d399; padding:15px; border-radius:12px; max-width:600px; margin:15px auto; text-align:center; font-weight:900;">{{ msg }}</div>{% endif %}

    <div id="usdtModal">
        <div style="background:#1a1c29; padding:30px; border-radius:20px; border:2px solid #ffd700; width:350px; text-align:center;">
            <h3 style="color:#ffd700;">سحب عبر USDT</h3>
            <input type="text" id="usdtWalletInput" placeholder="أدخل عنوان محفظتك (USDT)..." style="width:100%; padding:12px; margin:15px 0; background:#0a0d16; color:#fff; border:1px solid #444; border-radius:8px; box-sizing:border-box;">
            <button onclick="submitUsdt()" style="background:#22c55e; color:#000; padding:10px 20px; font-weight:900; border:none; border-radius:8px; cursor:pointer;">إرسال طلب السحب</button>
            <button onclick="closeUsdtModal()" style="background:#ef4444; color:#fff; padding:10px 20px; font-weight:900; border:none; border-radius:8px; cursor:pointer; margin-right:5px;">إلغاء</button>
        </div>
    </div>

    <!-- الألعاب الخمسة: الرقم الحنون، روليت الحظ، إمبراطورية الأرقام الملكية، عجلة الحظ، واكشف واربح -->
    <div class="icons-grid">
        <a href="/game_golden_number" class="icon-card"><div class="icon-logo">🏆</div><div class="icon-title">{{ t.game1 }}</div></a>
        <a href="/game_roulette" class="icon-card"><div class="icon-logo">🎰</div><div class="icon-title">{{ t.game2 }}</div></a>
        <a href="/game_numbers_empire" class="icon-card"><div class="icon-logo">🏛️</div><div class="icon-title">{{ t.game3 }}</div></a>
        <a href="/game_number_wheel" class="icon-card"><div class="icon-logo">🎡</div><div class="icon-title">{{ t.game4 }}</div></a>
        <a href="/game_reveal_and_win" class="icon-card"><div class="icon-logo">🎟️</div><div class="icon-title">{{ t.game5 }}</div></a>
    </div>

    <script>
        function rechargeWhish() {
            let text = encodeURIComponent("مرحباً، أريد شحن رصيد في منصة امبراطورية الأرقام عبر Whish Money.");
            window.open(`https://wa.me/96170000000?text=${text}`, '_blank');
        }
        function rechargeGooglePlay() { alert("سيتم توجيهك لمتجر غوغل قريباً."); }
        function withdrawWhish(u, p) {
            let text = encodeURIComponent(`أريد سحب رصيدي عبر Whish.\\nيوزر: ${u}\\nباسورد: ${p}`);
            window.open(`https://wa.me/96170000000?text=${text}`, '_blank');
        }
        function withdrawVisa(u, p) {
            let text = encodeURIComponent(`أريد استلام فيزا مسبقة الدفع.\\nيوزر: ${u}\\nباسورد: ${p}`);
            window.open(`https://wa.me/96170000000?text=${text}`, '_blank');
        }
        function openUsdtModal() { document.getElementById('usdtModal').style.display = 'flex'; }
        function closeUsdtModal() { document.getElementById('usdtModal').style.display = 'none'; }
        function submitUsdt() {
            let w = document.getElementById('usdtWalletInput').value;
            if(!w) { alert("أدخل عنوان المحفظة!"); return; }
            alert("تم إرسال طلب السحب بنجاح!");
            closeUsdtModal();
        }
    </script>
</body>
</html>
"""

# --- قالب لعبة الرقم الحنون ---
GAME_GOLDEN_PAGE = """
<!DOCTYPE html>
<html lang="{{ lang_key }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><title>{{ t.game1 }}</title>
    <style>
        body { font-family: Tahoma; background: #151928; color: #fff; padding: 25px; text-align: center; margin: 0; }
        .card { background: rgba(25,30,48,0.95); border: 4px solid #ffd700; padding: 35px; border-radius: 30px; max-width: 950px; margin: 20px auto; box-shadow: 0 25px 60px rgba(0,0,0,0.8); }
        .header-box { background: linear-gradient(135deg, #1e3a8a, #1e1b4b); border: 2px solid #38bdf8; padding: 20px; border-radius: 18px; margin-bottom: 25px; }
        .draw-screen-box { background: #000; border: 4px solid #ffd700; padding: 20px; border-radius: 20px; margin-bottom: 10px; display: inline-block; min-width: 250px; }
        .slot-screen { font-size: 55px; font-weight: 900; color: #ffd700; letter-spacing: 5px; }
        .winner-msg { font-size: 19px; font-weight: 900; color: #34d399; margin-bottom: 20px; min-height: 25px; }
        .grid { display: grid; grid-template-columns: repeat(10, 1fr); gap: 12px; margin-top: 15px; }
        @media(max-width:768px){ .grid { grid-template-columns: repeat(5, 1fr); } }
        .cell { background: linear-gradient(145deg, #7c3aed, #4c1d95); border: 3px solid #a78bfa; border-radius: 16px; aspect-ratio: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; font-weight: 900; cursor: pointer; color: #fff; font-size: 20px; transition: 0.2s; }
        .cell:hover { border-color: #ffd700; transform: scale(1.05); }
        .cell.booked { background: linear-gradient(145deg, #7f1d1d, #450a0a) !important; border-color: #ef4444 !important; cursor: not-allowed; }
        .cell.my { background: linear-gradient(145deg, #1e3a8a, #172554) !important; border-color: #3b82f6 !important; }
        .cell.winner-glow { background: #fbbf24 !important; border: 4px solid #fff !important; box-shadow: 0 0 35px #ffd700; color: #000 !important; transform: scale(1.12); animation: pulse 0.8s infinite alternate; }
        @keyframes pulse { 0% { transform: scale(1.08); } 100% { transform: scale(1.15); } }
        .player-info-box { background: rgba(15,20,32,0.9); border: 2px solid #34d399; padding: 15px; border-radius: 15px; margin-top: 25px; text-align: right; }
        #insufficientBalanceModal { display: none; position: fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.85); justify-content:center; align-items:center; z-index:200; }
    </style>
</head>
<body>
    {{ lang_bar | safe }}
    <div class="card">
        <div class="header-box">
            <h2 style="color: #ffd700; margin: 0 0 10px 0; font-size: 24px;">احجز رقم ب 20 usdd واربح 700 usdd فورا</h2>
            <p style="color: #f8fafc; margin: 0; font-size: 18px; font-weight: bold;">السحب يوميا الساعة 22:00 بتوقيت مدينة بيروت</p>
        </div>

        <div class="draw-screen-box">
            <div id="slotScreen" class="slot-screen">--</div>
        </div>
        <div id="winnerAnnouncement" class="winner-msg"></div>

        <div id="insufficientBalanceModal">
            <div style="background:#1a1c29; padding:35px; border-radius:22px; border:3px solid #ef4444; width:400px; text-align:center; box-shadow:0 10px 30px rgba(0,0,0,0.9);">
                <h3 style="color:#ef4444; font-size:24px; margin-top:0;">⚠️ تنبيه الرصيد</h3>
                <p style="font-size:18px; color:#fff; font-weight:bold; margin:20px 0;">رصيدك غير كافي الرجاء الشحن</p>
                <button onclick="closeInsufficientModal()" style="background:#ffd700; color:#000; padding:12px 30px; font-weight:900; border:none; border-radius:10px; cursor:pointer; font-size:16px;">حسناً</button>
            </div>
        </div>

        <div class="grid" id="numbersGrid">
            {% for i in range(1, 51) %}
                {% if i in bookings %}
                    {% if bookings[i] == username %}
                        <button type="button" onclick="handleAction('cancel', {{ i }})" class="cell my" id="cell_{{ i }}">{{ i }}<br><span style="font-size:11px; color:#93c5fd;">تراجع</span></button>
                    {% else %}
                        <div class="cell booked" id="cell_{{ i }}">{{ i }}<br><span style="font-size:11px; color:#fca5a5;">{{ bookings[i] }}</span></div>
                    {% endif %}
                {% else %}
                    <button type="button" onclick="handleAction('book', {{ i }})" class="cell" id="cell_{{ i }}">{{ i }}</button>
                {% endif %}
            {% endfor %}
        </div>

        <div class="player-info-box">
            <h4 style="color: #34d399; margin-top: 0;">📋 لوحة حجوزاتي والخصم المالي</h4>
            <p style="margin: 5px 0; font-size: 16px;"><b>أرقامك المحجوزة:</b> <span style="color: #ffd700;">{{ my_nums_str }}</span></p>
            <p style="margin: 5px 0; font-size: 16px;"><b>القيمة المخصومة من حسابك:</b> <span style="color: #38bdf8;">{{ my_total_cost }} USDD</span></p>
        </div>

        {% if username == 'admin1' %}
            <div style="margin-top: 30px; text-align: center;">
                <button type="button" onclick="triggerDraw()" style="background: linear-gradient(135deg, #22c55e, #15803d); color: #fff; font-weight: 900; padding: 16px 40px; border: none; border-radius: 14px; cursor: pointer; font-size: 20px;">⚡ اسحب الآن (للآدمن)</button>
            </div>
        {% endif %}
    </div>

    <script>
        function handleAction(actionType, numberVal) {
            let fd = new FormData();
            fd.append('action_type', actionType);
            fd.append('number', numberVal);
            fetch('/game_golden_number', { method: 'POST', body: fd }).then(res => res.json()).then(data => {
                if(data.success) {
                    location.reload();
                } else {
                    if(data.msg && data.msg.includes("رصيد")) {
                        document.getElementById('insufficientBalanceModal').style.display = 'flex';
                    } else if(data.msg) {
                        alert(data.msg);
                    }
                }
            });
        }

        function closeInsufficientModal() {
            document.getElementById('insufficientBalanceModal').style.display = 'none';
        }

        function triggerDraw() {
            let fd = new FormData();
            fd.append('action_type', 'admin_draw');
            fetch('/game_golden_number', { method: 'POST', body: fd }).then(res => res.json()).then(data => {
                if(data.winning_number) {
                    runDrawAnimation(data.winning_number);
                } else if(data.msg) {
                    alert(data.msg);
                }
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
                    ann.innerText = `مبروك ربحت 700 usdd للرقم ${winningNum}`;
                    
                    let winCell = document.getElementById('cell_' + winningNum);
                    if(winCell) {
                        winCell.className = "cell winner-glow";
                        winCell.innerHTML = `${winningNum}<br><span style="font-size:12px; font-weight:900;">مبروك</span>`;
                    }

                    setTimeout(() => {
                        location.reload();
                    }, 5000);
                }
            }, 90);
        }
    </script>
</body>
</html>
"""

# --- قالب لعبة روليت الحظ ---
GAME_ROULETTE_PAGE = """
<!DOCTYPE html>
<html lang="{{ lang_key }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><title>{{ t.game2 }}</title>
    <style>
        body { font-family: Tahoma; background: #151928; color: #fff; padding: 20px; text-align: center; margin: 0; }
        .card { background: rgba(25,30,48,0.95); border: 4px solid #ffd700; padding: 25px; border-radius: 30px; max-width: 900px; margin: 15px auto; box-shadow: 0 25px 60px rgba(0,0,0,0.8); }
        .timer-box { font-size: 20px; font-weight: 900; color: #ffd700; background: #000; padding: 10px 20px; border-radius: 14px; border: 2px solid #38bdf8; margin-bottom: 15px; display: inline-block; }
        .spin-screen { font-size: 40px; font-weight: 900; color: #ffd700; background: #000; padding: 12px 25px; border-radius: 14px; border: 3px solid #b8860b; display: inline-block; margin-bottom: 15px; letter-spacing: 3px; }
        
        .roulette-table {
            display: grid;
            grid-template-columns: 70px repeat(12, 1fr);
            grid-template-rows: repeat(3, 65px);
            gap: 5px;
            max-width: 820px;
            margin: 20px auto;
            background: #065f46;
            padding: 15px;
            border-radius: 16px;
            border: 5px solid #b8860b;
        }
        .r-cell {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            border-radius: 8px;
            cursor: pointer;
            color: #fff;
            font-size: 18px;
            transition: 0.15s;
            user-select: none;
            border: 2px solid rgba(255,255,255,0.2);
        }
        .r-cell.zero {
            grid-row: span 3;
            background: #047857;
            border-color: #ffd700;
            font-size: 24px;
        }
        .r-cell.red { background: #dc2626; }
        .r-cell.black { background: #111827; }
        .r-cell:hover { transform: scale(1.06); border-color: #ffd700; }
        .r-cell.selected { border: 3px solid #ffd700 !important; box-shadow: 0 0 15px #ffd700; transform: scale(1.05); }
        .r-cell.winner-highlight { background: #fbbf24 !important; color: #000 !important; font-size: 22px; border: 4px solid #fff !important; box-shadow: 0 0 30px #ffd700; }

        .controls-grid { display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; margin-bottom: 15px; }
        .btn-ctrl { padding: 10px 16px; font-weight: 900; border-radius: 10px; border: none; cursor: pointer; font-size: 14px; }
        .btn-red { background: #dc2626; color: #fff; }
        .btn-black { background: #111827; color: #fff; border: 1px solid #555; }
        .btn-rand { background: #d97706; color: #000; }
        .btn-undo { background: #4b5563; color: #fff; }
        .btn-double { background: #3b82f6; color: #fff; }
    </style>
</head>
<body>
    {{ lang_bar | safe }}
    <div class="card">
        <h2 style="color:#ffd700; margin-top:0;">🎰 طاولة روليت الحظ العالمية</h2>
        <p><b>رصيدك: <span id="rouletteBal">{{ balance }}</span> USDD</b> (الرهان: 1 USDD | الربح: 20 USDD لكل مضاعف - حد أقصى 21 رقماً)</p>

        <div>
            <div id="timerBox" class="timer-box">⏳ وقت الرهان المتبقي: 15 ث</div>
        </div>

        <div>
            <div id="spinScreen" class="spin-screen">--</div>
        </div>
        <div id="rouletteMsg" style="font-weight:900; color:#34d399; margin-bottom:10px; min-height:22px;">اختر أرقامك من الطاولة أدناه</div>

        <div class="controls-grid">
            <button class="btn-ctrl btn-red" onclick="selectRed()">حجز كل الحمر</button>
            <button class="btn-ctrl btn-black" onclick="selectBlack()">حجز كل السود</button>
            <button class="btn-ctrl btn-rand" onclick="selectRandom10()">حجز 10 عشوائي</button>
            <button class="btn-ctrl btn-double" onclick="doubleBets()">دوبلت الرهانات (x2)</button>
            <button class="btn-ctrl btn-undo" onclick="undoLast()">تراجع عن الأخيرة</button>
        </div>

        <div class="roulette-table" id="rouletteTable">
            <div class="r-cell zero" onclick="toggleNum(0)" id="r_cell_0">
                <span>0</span>
                <span id="r_mult_0" style="font-size:11px; color:#ffd700;">0$</span>
            </div>

            {% set row1 = [3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36] %}
            {% set row2 = [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35] %}
            {% set row3 = [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34] %}
            {% set red_list = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36] %}

            {% for n in row1 %}
                {% set is_red = n in red_list %}
                <div class="r-cell {{ 'red' if is_red else 'black' }}" onclick="toggleNum({{ n }})" id="r_cell_{{ n }}">
                    <span>{{ n }}</span>
                    <span id="r_mult_{{ n }}" style="font-size:11px; color:#ffd700;">0$</span>
                </div>
            {% endfor %}

            {% for n in row2 %}
                {% set is_red = n in red_list %}
                <div class="r-cell {{ 'red' if is_red else 'black' }}" onclick="toggleNum({{ n }})" id="r_cell_{{ n }}">
                    <span>{{ n }}</span>
                    <span id="r_mult_{{ n }}" style="font-size:11px; color:#ffd700;">0$</span>
                </div>
            {% endfor %}

            {% for n in row3 %}
                {% set is_red = n in red_list %}
                <div class="r-cell {{ 'red' if is_red else 'black' }}" onclick="toggleNum({{ n }})" id="r_cell_{{ n }}">
                    <span>{{ n }}</span>
                    <span id="r_mult_{{ n }}" style="font-size:11px; color:#ffd700;">0$</span>
                </div>
            {% endfor %}
        </div>
    </div>

    <script>
        let bets = {};
        let actionHistory = [];
        let redNums = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36];
        let blackNums = [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35];
        let timeLeft = 15;
        let timerInterval = null;
        let gameActive = true;

        function startTimer() {
            timerInterval = setInterval(() => {
                timeLeft--;
                let tBox = document.getElementById('timerBox');
                if(tBox) tBox.innerText = `⏳ وقت الرهان المتبقي: ${timeLeft} ث`;
                if(timeLeft <= 0) {
                    clearInterval(timerInterval);
                    gameActive = false;
                    if(tBox) tBox.innerText = `🛑 انتهى وقت الرهان، بدء السحب...`;
                    setTimeout(executeDraw, 2000);
                }
            }, 1000);
        }
        startTimer();

        function getTotalBetsCount() {
            let count = 0;
            for(let k in bets) count += bets[k];
            return count;
        }

        function toggleNum(n) {
            if(!gameActive) { alert("انتهى وقت الرهان لهذه الجولة!"); return; }
            if(!bets[n] && getTotalBetsCount() >= 21) { alert("حد أقصى 21 رقماً في المرة الواحدة!"); return; }

            if(!bets[n]) bets[n] = 0;
            if(bets[n] >= 10) { alert("حد أقصى دوبلت 10 مرات للرقم الواحد!"); return; }

            bets[n]++;
            actionHistory.push(n);

            fetch('/game_roulette_bet', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({action:'add', number:n})})
            .then(res => res.json()).then(d => {
                if(d.success) {
                    document.getElementById('rouletteBal').innerText = d.balance;
                    updateUI();
                } else {
                    bets[n]--;
                    actionHistory.pop();
                    alert(d.msg || "رصيد غير كافي!");
                }
            });
        }

        function undoLast() {
            if(!gameActive) { alert("لا يمكن التراجع بعد بدء السحب!"); return; }
            if(actionHistory.length === 0) { alert("لا توجد خطوات للتراجع عنها!"); return; }
            let lastNum = actionHistory.pop();
            if(bets[lastNum]) {
                bets[lastNum]--;
                if(bets[lastNum] <= 0) delete bets[lastNum];
            }

            fetch('/game_roulette_bet', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({action:'remove', number:lastNum})})
            .then(res => res.json()).then(d => {
                if(d.success) {
                    document.getElementById('rouletteBal').innerText = d.balance;
                    updateUI();
                }
            });
        }

        function updateUI() {
            for(let i=0; i<=36; i++) {
                let cell = document.getElementById('r_cell_' + i);
                let badge = document.getElementById('r_mult_' + i);
                if(bets[i] && bets[i] > 0) {
                    cell.classList.add('selected');
                    badge.innerText = `x${bets[i]} (${bets[i]}$)`;
                } else {
                    cell.classList.remove('selected');
                    badge.innerText = `0$`;
                }
            }
        }

        function selectRed() {
            redNums.forEach(n => { if(getTotalBetsCount() < 21) toggleNum(n); });
        }
        function selectBlack() {
            blackNums.forEach(n => { if(getTotalBetsCount() < 21) toggleNum(n); });
        }
        function selectRandom10() {
            let all = []; for(let i=0; i<=36; i++) all.push(i);
            for(let i=0; i<10; i++) {
                if(getTotalBetsCount() >= 21) break;
                let r = all[Math.floor(Math.random()*all.length)];
                toggleNum(r);
            }
        }
        function doubleBets() {
            for(let k in bets) {
                if(bets[k] > 0 && bets[k] < 10) {
                    toggleNum(parseInt(k));
                }
            }
        }

        function executeDraw() {
            fetch('/game_roulette_draw', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({bets: bets})})
            .then(res => res.json()).then(data => {
                if(data.success) {
                    runSpinAnimation(data.winning_number, data.msg, data.balance);
                }
            });
        }

        function runSpinAnimation(winningNum, finalMsg, newBal) {
            let screen = document.getElementById('spinScreen');
            let msgEl = document.getElementById('rouletteMsg');
            let counter = 0;
            let interval = setInterval(() => {
                screen.innerText = '#' + Math.floor(Math.random() * 37);
                counter++;
                if(counter > 25) {
                    clearInterval(interval);
                    screen.innerText = '#' + winningNum;
                    msgEl.innerText = finalMsg;
                    document.getElementById('rouletteBal').innerText = newBal;

                    let winCell = document.getElementById('r_cell_' + winningNum);
                    if(winCell) {
                        winCell.className = "r-cell winner-highlight";
                    }

                    setTimeout(() => { location.reload(); }, 6000);
                }
            }, 80);
        }
    </script>
</body>
</html>
"""

# --- قالب لعبة إمبراطورية الأرقام الملكية ---
GAME_NUMBERS_EMPIRE_PAGE = """
<!DOCTYPE html>
<html lang="{{ lang_key }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><title>{{ t.game3 }}</title>
    <style>
        body { font-family: Tahoma; background: #151928; color: #fff; padding: 25px; text-align: center; }
        .card { background: rgba(25,30,48,0.95); border: 4px solid #ffd700; padding: 35px; border-radius: 30px; max-width: 800px; margin: 20px auto; }
        .boxes { display: flex; justify-content: center; gap: 20px; margin: 30px 0; flex-wrap: wrap; }
        .box { width: 120px; height: 130px; background: #7c3aed; border: 3px solid #ffd700; border-radius: 20px; color: #fff; font-size: 22px; font-weight: bold; cursor: pointer; display: flex; flex-direction: column; align-items: center; justify-content: center; }
        .box.booked { background: #7f1d1d; cursor: not-allowed; }
        .box.my { background: #1e3a8a; }
        .slot-box { font-size: 45px; font-weight: 900; color: #ffd700; background: #000; padding: 15px; border-radius: 14px; border: 3px solid #b8860b; display: inline-block; min-width: 150px; }
    </style>
</head>
<body>
    {{ lang_bar | safe }}
    <div class="card">
        <h2 style="color:#ffd700;">🏛️ إمبراطورية الأرقام الملكية (5 أرقام)</h2>
        <p style="font-size:18px; color:#ffd700;">سعر الحجز: 500 USDD | الجائزة الكبرى: 2000 USDD</p>

        <div style="background:#000; padding:20px; border-radius:20px; border:3px solid #38bdf8; margin:20px 0;">
            <div id="empireSlot" class="slot-box">--</div>
            <div id="empireAnnouncement" style="font-size:18px; color:#34d399; margin-top:10px; font-weight:900;">في انتظار السحب الفاخر...</div>
        </div>

        {% if msg %}<div style="background:#065f46; color:#34d399; padding:12px; border-radius:10px; margin:15px 0;">{{ msg }}</div>{% endif %}

        <div class="boxes">
            {% for i in range(1, 6) %}
                {% if i in bookings %}
                    {% if bookings[i] == username %}
                        <button onclick="empAction('cancel', {{ i }})" class="box my"><span>👑</span><span>رقم {{ i }}</span><span style="font-size:12px;">تراجع</span></button>
                    {% else %}
                        <div class="box booked"><span>👑</span><span>رقم {{ i }}</span><span style="font-size:12px;">{{ bookings[i] }}</span></div>
                    {% endif %}
                {% else %}
                    <button onclick="empAction('book', {{ i }})" class="box"><span>👑</span><span>رقم {{ i }}</span><span style="font-size:12px;">500$</span></button>
                {% endif %}
            {% endfor %}
        </div>

        {% if username == 'admin1' %}
            <div style="margin-top:25px;">
                <button onclick="empAction('admin_draw', 0)" style="background:#22c55e; color:#fff; padding:15px 35px; font-weight:bold; border:none; border-radius:12px; cursor:pointer; font-size:18px;">⚡ بدء السحب الملكي</button>
            </div>
        {% endif %}
    </div>
    <script>
        function empAction(type, box) {
            let fd = new FormData(); fd.append('action_type', type); fd.append('box_number', box);
            fetch('/game_numbers_empire', {method:'POST', body:fd}).then(r=>r.json()).then(d=>{
                if(d.winning_number) {
                    let screen = document.getElementById('empireSlot');
                    let ann = document.getElementById('empireAnnouncement');
                    screen.innerText = '#' + d.winning_number;
                    ann.innerText = d.msg;
                    setTimeout(() => { location.reload(); }, 5000);
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

# --- قالب لعبة عجلة الحظ المحدثة بالكامل حسب طلبك ---
GAME_WHEEL_PAGE = """
<!DOCTYPE html>
<html lang="{{ lang_key }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><title>{{ t.game4 }}</title>
    <style>
        body { font-family: Tahoma; background: #151928; color: #fff; padding: 25px; text-align: center; }
        .card { background: rgba(25,30,48,0.95); border: 4px solid #ffd700; padding: 35px; border-radius: 30px; max-width: 750px; margin: 20px auto; box-shadow: 0 25px 60px rgba(0,0,0,0.8); }
        .wheel-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin: 20px auto; max-width: 500px; }
        .wheel-btn { background: #1f2937; border: 2px solid #ffd700; border-radius: 12px; padding: 18px; font-size: 20px; font-weight: 900; color: #fff; cursor: pointer; transition: 0.2s; }
        .wheel-btn.selected { background: #d97706 !important; color: #000 !important; border-color: #fff !important; transform: scale(1.05); }
        .wheel-btn.winner-glow { background: #fbbf24 !important; color: #000 !important; border: 3px solid #fff !important; box-shadow: 0 0 30px #ffd700; transform: scale(1.12); }
        .spin-screen { font-size: 50px; font-weight: 900; color: #ffd700; background: #000; padding: 15px; border-radius: 15px; border: 3px solid #b8860b; display: inline-block; min-width: 160px; margin: 15px 0; letter-spacing: 4px; }
        .selection-box { background: rgba(15,20,32,0.9); border: 2px solid #38bdf8; padding: 15px; border-radius: 14px; margin-top: 20px; text-align: right; }
    </style>
</head>
<body>
    {{ lang_bar | safe }}
    <div class="card">
        <h2 style="color:#ffd700; margin-top:0;">🎡 عجلة الحظ (20 رقم)</h2>
        <p style="font-size:18px; color:#ffd700;">سعر الحجز للرقم: 1 USDD | الجائزة: 20 USDD (حد أقصى 10 أرقام)</p>

        <div>
            <div id="wheelSlot" class="spin-screen">--</div>
        </div>
        <div id="wheelMsg" style="font-size:18px; font-weight:900; color:#34d399; margin:10px 0;">اختر من 1 إلى 10 أرقام وابدأ السحب</div>

        <!-- قائمة حجز فاخرة بـ 20 رقم -->
        <div class="wheel-grid">
            {% for n in range(1, 21) %}
                <button type="button" id="w_num_{{ n }}" onclick="toggleWheelNum({{ n }})" class="wheel-btn">{{ n }}</button>
            {% endfor %}
        </div>

        <!-- خانة تكتب للاعب الأرقام المختارة وقيمتها -->
        <div class="selection-box">
            <h4 style="color: #38bdf8; margin-top:0;">📋 أرقامك المختارة وقيمة الرهان</h4>
            <p style="margin: 5px 0; font-size: 16px;"><b>الأرقام المحددة:</b> <span id="selectedListText" style="color: #ffd700;">لا توجد أرقام مختارة</span></p>
            <p style="margin: 5px 0; font-size: 16px;"><b>إجمالي قيمة الرهان:</b> <span id="totalCostText" style="color: #34d399;">0 USDD</span></p>
        </div>

        <button type="button" onclick="spinWheel()" style="padding: 16px 45px; background: linear-gradient(135deg,#22c55e,#15803d); color: #fff; font-weight: 900; font-size: 20px; border: none; border-radius: 16px; cursor: pointer; margin-top: 25px;">ابدأ السحب 🎡</button>
    </div>

    <script>
        let wheelSelected = [];

        function toggleWheelNum(n) {
            let idx = wheelSelected.indexOf(n);
            if(idx > -1) {
                wheelSelected.splice(idx, 1);
                document.getElementById('w_num_' + n).classList.remove('selected');
            } else {
                if(wheelSelected.length >= 10) { alert("لا يمكن اختيار أكثر من 10 أرقام في المحاولة الواحدة!"); return; }
                wheelSelected.push(n);
                document.getElementById('w_num_' + n).classList.add('selected');
            }
            updateSelectionBox();
        }

        function updateSelectionBox() {
            let txt = wheelSelected.length > 0 ? wheelSelected.join(', ') : 'لا توجد أرقام مختارة';
            let cost = wheelSelected.length * 1.0;
            document.getElementById('selectedListText').innerText = txt;
            document.getElementById('totalCostText').innerText = cost + ' USDD';
        }

        function spinWheel() {
            if(wheelSelected.length === 0) { alert("يرجى اختيار رقم واحد على الأقل قبل بدء السحب!"); return; }
            let fd = new FormData();
            fd.append('selected_numbers', JSON.stringify(wheelSelected));
            fetch('/game_number_wheel', {method: 'POST', body: fd}).then(res => res.json()).then(d => {
                if(d.success) {
                    runWheelAnimation(d.winning_num, d.msg, d.balance);
                } else {
                    alert(d.msg || "حدث خطأ أو رصيد غير كافي!");
                }
            });
        }

        function runWheelAnimation(winningNum, finalMsg, newBal) {
            let screen = document.getElementById('wheelSlot');
            let msgEl = document.getElementById('wheelMsg');
            let counter = 0;
            let interval = setInterval(() => {
                screen.innerText = '#' + Math.floor(Math.random() * 20 + 1);
                counter++;
                if(counter > 20) {
                    clearInterval(interval);
                    screen.innerText = '#' + winningNum;
                    msgEl.innerText = finalMsg;
                    document.getElementById('rouletteBal') ? document.getElementById('rouletteBal').innerText = newBal : null;

                    let winBtn = document.getElementById('w_num_' + winningNum);
                    if(winBtn) {
                        winBtn.className = "wheel-btn winner-glow";
                    }

                    setTimeout(() => { location.reload(); }, 5000);
                }
            }, 90);
        }
    </script>
</body>
</html>
"""

# --- قالب اللعبة الخامسة: اكشف واربح (5 صناديق، 3 نقرات، محاكاة الاحتمالات 1/100 و 50/100) ---
GAME_REVEAL_PAGE = """
<!DOCTYPE html>
<html lang="{{ lang_key }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><title>{{ t.game5 }}</title>
    <style>
        body { font-family: Tahoma; background: #151928; color: #fff; padding: 25px; text-align: center; }
        .card { background: rgba(25,30,48,0.95); border: 4px solid #ffd700; padding: 35px; border-radius: 30px; max-width: 750px; margin: 20px auto; box-shadow: 0 25px 60px rgba(0,0,0,0.8); }
        .boxes-grid { display: flex; justify-content: center; gap: 15px; margin: 30px 0; flex-wrap: wrap; }
        .box-cell { background: linear-gradient(145deg, #7c3aed, #4c1d95); border: 3px solid #ffd700; border-radius: 18px; width: 110px; height: 120px; font-size: 35px; font-weight: 900; color: #fff; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: 0.2s; user-select: none; }
        .box-cell:hover { transform: scale(1.05); border-color: #fff; }
        .box-cell.revealed { background: #1e1b4b !important; border-color: #38bdf8 !important; cursor: default; }
    </style>
</head>
<body>
    {{ lang_bar | safe }}
    <div class="card">
        <h2 style="color:#ffd700; margin-top:0;">🎟️ لعبة اكشف واربح</h2>
        <p style="font-size:18px; color:#ffd700;">تكلفة المحاولة: 2 USDD | الجائزة الكبرى: 100 USDD (تطابق 3 أسود)</p>
        <p style="font-size:15px; color:#38bdf8;">تطابق وجهين أسد يعيد لك 1 USDD من قيمة المراهنة!</p>

        <div id="revealMsg" style="font-size: 20px; font-weight: 900; color: #34d399; margin: 20px 0;">اضغط على "ابدأ المحاولة" ثم اختر 3 صناديق لكشفها</div>

        <!-- 5 صناديق فاخرة -->
        <div class="boxes-grid">
            {% for i in range(1, 6) %}
                <div class="box-cell" id="b_{{ i }}" onclick="clickBox({{ i }})">📦</div>
            {% endfor %}
        </div>

        <button type="button" id="startBtn" onclick="startReveal()" style="padding: 16px 45px; background: linear-gradient(135deg,#ffd700,#ff8c00); color: #000; font-weight: 900; font-size: 20px; border: none; border-radius: 16px; cursor: pointer; margin-top: 15px;">ابدأ المحاولة الجديدة (2 USDD) 🎟️</button>
    </div>

    <script>
        let sessionRevealed = [];
        let clicksCount = 0;
        let gameActive = false;

        function startReveal() {
            fetch('/game_reveal_and_win', {method: 'POST'})
            .then(res => res.json())
            .then(d => {
                if(d.success) {
                    document.getElementById('rouletteBal') ? document.getElementById('rouletteBal').innerText = d.balance : null;
                    sessionRevealed = d.revealed; // مصفوفة فيها 3 عناصر تم تحديدها خلف الكواليس
                    clicksCount = 0;
                    gameActive = true;
                    document.getElementById('revealMsg').innerText = "تم خصم 2 USDD! اختر 3 صناديق من الأخشاب لكشف محتواها الآن.";
                    document.getElementById('startBtn').style.display = 'none';

                    // إعادة تعيين الصناديق
                    for(let i=1; i<=5; i++) {
                        let cell = document.getElementById('b_' + i);
                        cell.innerText = "📦";
                        cell.classList.remove('revealed');
                    }
                } else {
                    alert(d.msg || "رصيد غير كافي!");
                }
            });
        }

        function clickBox(boxIdx) {
            if(!gameActive) { alert("يرجى الضغط على زر 'ابدأ المحاولة الجديدة' أولاً!"); return; }
            let cell = document.getElementById('b_' + boxIdx);
            if(cell.classList.contains('revealed')) return; // تم فتحه مسبقاً

            if(clicksCount < sessionRevealed.length) {
                cell.innerText = sessionRevealed[clicksCount];
                cell.classList.add('revealed');
                clicksCount++;

                if(clicksCount === sessionRevealed.length) {
                    gameActive = false;
                    // جلب النتيجة من الخادم أو فحصها
                    setTimeout(() => {
                        fetch('/game_reveal_result_check', {method: 'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({revealed: sessionRevealed})})
                        .then(res => res.json()).then(resData => {
                            document.getElementById('revealMsg').innerText = resData.msg;
                            document.getElementById('startBtn').style.display = 'inline-block';
                            document.getElementById('startBtn').innerText = "محاولة أخرى (2 USDD)";
                        });
                    }, 500);
                }
            }
        }
    </script>
</body>
</html>
"""

# --- بقية الصفحات وإدارة الزبائن ---
ADMIN_CUSTOMERS_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><title>إدارة الزبائن</title>
<style>body{font-family:Tahoma; background:#151928; color:#fff; padding:20px; text-align:center;} table{width:100%; border-collapse:collapse; margin-top:15px;} th, td{border:1px solid #444; padding:10px;} th{background:#0a0d16; color:#ffd700;} input{padding:10px; margin:5px; width:100%; box-sizing:border-box; background:#0a0d16; color:#fff; border:1px solid #444; border-radius:8px;}</style>
</head>
<body>
    {{ lang_bar | safe }}
    <h2>👥 إدارة الزبائن وحسابات اللاعبين</h2>
    {% if msg %}<div style="background:#065f46; color:#34d399; padding:12px; border-radius:10px; margin:15px auto; max-width:500px; font-weight:bold;">{{ msg }}</div>{% endif %}
    <div style="background:rgba(25,30,48,0.9); padding:25px; border-radius:16px; max-width:550px; margin:20px auto; border:2px solid #ffd700; text-align:right;">
        <h3 style="color:#ffd700; text-align:center; margin-top:0;">➕ إنشاء حساب لاعب جديد</h3>
        <form method="POST">
            <input type="hidden" name="action" value="create_player">
            <label>اسم المستخدم (Username):</label>
            <input type="text" name="username" required placeholder="أدخل اسم المستخدم...">
            <label>كلمة المرور (Password):</label>
            <input type="password" name="password" required placeholder="أدخل كلمة المرور...">
            <label>الرصيد الابتدائي (Balance):</label>
            <input type="number" name="balance" value="0.0" step="0.5" required>
            <label>اسم المالك / المحل (Owner Name):</label>
            <input type="text" name="owner_name" placeholder="مثال: مستشفى التلفونات...">
            <button type="submit" style="background:#22c55e; color:#000; padding:12px; font-weight:900; border:none; border-radius:10px; width:100%; cursor:pointer; margin-top:15px;">إنشاء الحساب الآن</button>
        </form>
    </div>
    <div style="background: rgba(25,30,48,0.9); padding: 25px; border-radius: 20px; max-width: 1000px; margin: 25px auto;">
        <h3 style="color:#ffd700;">📋 قائمة الحسابات واللاعبين</h3>
        <table>
            <tr><th>المستخدم</th><th>المالك / المحل</th><th>الدور</th><th>الرصيد</th><th>أُنشئ بواسطة</th></tr>
            {% for u in users_list %}
            <tr><td><b>{{ u.username }}</b></td><td>{{ u.owner_name }}</td><td>{{ u.role }}</td><td style="color:#34d399;">{{ u.balance }} USDD</td><td>{{ u.created_by }}</td></tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

ADMIN_ACCOUNTING_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><title>برنامج المحاسبة - 12D</title>
    <style>
        body { font-family: Tahoma; background: #151928; color: #f8fafc; padding: 25px; text-align: center; }
        .panel-box { background: rgba(25,30,48,0.9); padding: 22px; border-radius: 16px; max-width: 400px; margin: 15px auto; border: 2px solid #ffd700; text-align: right; }
        input, select { width: 100%; padding: 12px; margin: 8px 0; border-radius: 10px; background: #0a0d16; color: white; border: 1px solid #444; box-sizing: border-box; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #444; padding: 10px; text-align: center; }
        th { background: #0a0d16; color: #ffd700; }
        .stats-grid { display: flex; justify-content: center; gap: 15px; flex-wrap: wrap; margin: 20px 0; }
        .stat-card { background: rgba(24,34,50,0.9); border: 2px solid #38bdf8; padding: 20px; border-radius: 15px; flex: 1; min-width: 220px; text-align: center; }
    </style>
</head>
<body>
    {{ lang_bar | safe }}
    <h2>📊 برنامج المحاسبة والخزنة المركزية</h2>
    {% if msg %}<div style="background: #065f46; color: #34d399; padding: 14px; border-radius: 12px; margin: 20px auto; max-width: 500px; font-weight: 900;">{{ msg }}</div>{% endif %}
    <div style="font-size: 30px; font-weight: 900; color: #34d399; margin: 15px 0;">🏦 الخزنة المركزية: {{ vault_balance }} USDD</div>
    <div class="stats-grid" style="max-width: 1000px; margin: 20px auto;">
        <div class="stat-card" style="border-color: #ffd700;"><h4 style="color:#ffd700; margin:0;">💳 النقاط المباعة</h4><div style="font-size:24px; font-weight:bold; margin-top:10px;">{{ total_points_sold }} USDD</div></div>
        <div class="stat-card" style="border-color: #38bdf8;"><h4 style="color:#38bdf8; margin:0;">📥 الواردات (الرهانات)</h4><div style="font-size:24px; font-weight:bold; margin-top:10px;">{{ total_game_bets }} USDD</div></div>
        <div class="stat-card" style="border-color: #ef4444;"><h4 style="color:#ef4444; margin:0;">🎁 الجوائز</h4><div style="font-size:24px; font-weight:bold; margin-top:10px;">{{ total_payouts }} USDD</div></div>
        <div class="stat-card" style="border-color: #34d399;"><h4 style="color:#34d399; margin:0;">📈 صافي الأرباح</h4><div style="font-size:24px; font-weight:bold; margin-top:10px; color:#34d399;">{{ net_game_result }} USDD</div></div>
    </div>
    <div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;">
        <div class="panel-box">
            <h3 style="color: #22c55e; text-align:center;">⚡ بيع عملات مباشر</h3>
            <form method="POST">
                <input type="hidden" name="action" value="sell_currency">
                <label>اختر الحساب:</label>
                <select name="target_user" required><option value="">اختر الحساب</option>{% for u in users_list %}<option value="{{ u.username }}">{{ u.username }} (رصيده: {{ u.balance }})</option>{% endfor %}</select>
                <label>المبلغ:</label><input type="number" name="amount" min="1" required>
                <button type="submit" style="background:#22c55e; color:#000; padding:12px; font-weight:900; border:none; border-radius:8px; width:100%; cursor:pointer; margin-top:10px;">إتمام البيع</button>
            </form>
        </div>
        <div class="panel-box" style="border-color: #ef4444;">
            <h3 style="color: #ef4444; text-align:center;">💸 سحب رصيد من الزبون</h3>
            <form method="POST">
                <input type="hidden" name="action" value="buy_back_currency">
                <label>اختر الحساب:</label>
                <select name="target_user" required><option value="">اختر الحساب</option>{% for u in users_list %}<option value="{{ u.username }}">{{ u.username }} (رصيده: {{ u.balance }})</option>{% endfor %}</select>
                <label>المبلغ:</label><input type="number" name="amount" min="1" required>
                <button type="submit" style="background:#ef4444; color:#fff; padding:12px; font-weight:900; border:none; border-radius:8px; width:100%; cursor:pointer; margin-top:10px;">سحب للخزنة</button>
            </form>
        </div>
        <div class="panel-box" style="border-color: #ffd700;">
            <h3 style="color: #ffd700; text-align:center;">🎟️ توليد كودات الشحن</h3>
            <form method="POST">
                <input type="hidden" name="action" value="generate_card">
                <label>الفئة (USDD):</label>
                <select name="card_amount" required>
                    <option value="100">100 USDD</option>
                    <option value="200">200 USDD</option>
                    <option value="300">300 USDD</option>
                    <option value="500">500 USDD</option>
                    <option value="1000">1000 USDD</option>
                </select>
                <button type="submit" style="background:#ffd700; color:#000; padding:12px; font-weight:900; border:none; border-radius:8px; width:100%; cursor:pointer; margin-top:25px;">توليد الكود</button>
            </form>
        </div>
    </div>
    <div style="background: rgba(25,30,48,0.9); padding: 30px; border-radius: 20px; max-width: 900px; margin: 30px auto;">
        <h3 style="color: #ffd700;">🎫 كودات الشحن</h3>
        <table>
            <tr><th>الكود</th><th>الفئة</th><th>الحالة</th><th>استخدمه</th><th>وقت الإنشاء</th></tr>
            {% for c in cards %}
            <tr><td style="color:#38bdf8; font-family:monospace;"><b>{{ c.code }}</b></td><td>{{ c.amount }}</td><td>{{ 'مستخدم ❌' if c.is_used else 'متاح ✅' }}</td><td>{{ c.used_by if c.used_by else '---' }}</td><td>{{ c.created_at }}</td></tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

ADMIN_GAME_CONTROL_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><title>غرفة تحكم الألعاب</title>
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
                <option value="wheel">عجلة الحظ (1-20)</option>
                <option value="reveal">اكشف واربح</option>
            </select>
            <label>رقم الجولة القادمة (من 1 إلى 50):</label>
            <input type="number" name="round_index" min="1" max="50" required placeholder="رقم الجولة...">
            <label>الرقم الفائز المبرمج:</label>
            <input type="number" name="winning_number" required placeholder="الرقم الفائز...">
            <button type="submit" style="background:#22c55e; color:#000; padding:12px; font-weight:900; border:none; border-radius:8px; width:100%; cursor:pointer; margin-top:15px;">حفظ في غرفة التحكم ⚡</button>
        </form>
    </div>
</body>
</html>
"""

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
        .user-link.active { background: #3b82f6; color: #fff; }
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
                <input type="text" name="message" required placeholder="اكتب ردك للاعب..." style="flex:1; padding:12px; background:#0a0d16; color:#fff; border:1px solid #444; border-radius:8px;">
                <button type="submit" style="background:#22c55e; color:#000; font-weight:900; padding:0 20px; border:none; border-radius:8px; cursor:pointer;">إرسال الرد</button>
            </form>
            {% else %}
            <p style="color:#aaa; text-align:center; margin-top:150px;">اختر لاعباً من القائمة لعرض المحادثة السرية.</p>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

# --- مسارات الفلاسك والتوجيه ---

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
                db.session.add(FinancialLog(action_type='شحن عبر بطاقة كود', admin_name='system', target_user=user.username, amount=card.amount, log_time=get_local_time()))
                db.session.commit()
                msg = f"🎉 تم شحن {card.amount} USDD بنجاح!"
            else:
                msg = "⚠️ الكود غير صالح أو مستخدم مسبقاً!"
    return render_template_string(DASHBOARD_PAGE, t=t, lang_key=lang_key, lang_bar=get_lang_bar(), username=user.username, password=user.password, balance=user.balance, msg=msg)

@app.route('/game_golden_number', methods=['GET', 'POST'])
def game_golden_number():
    if 'username' not in session: return redirect(url_for('login'))
    username = session['username']
    user = User.query.filter_by(username=username).first()
    vault = SystemVault.query.get(1)
    t = get_t()
    lang_key = session.get('lang', 'ar')
    msg = None
    if request.method == 'POST':
        action = request.form.get('action_type')
        if action == 'book':
            num = int(request.form.get('number', 0))
            existing_booking = GoldenNumberBooking.query.filter_by(number=num).first()
            if existing_booking:
                return jsonify({"success": False, "msg": "هذا الرقم محجوز مسبقاً!"})
            if user.balance >= 20.0:
                user.balance -= 20.0
                vault.vault_balance += 20.0
                db.session.add(FinancialLog(action_type='مبيع رهان الرقم الحنون', admin_name='system', target_user=username, amount=20.0, log_time=get_local_time()))
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
                user.balance += 20.0
                vault.vault_balance -= 20.0
                db.session.add(FinancialLog(action_type='استرجاع رهان الرقم الحنون', admin_name='system', target_user=username, amount=20.0, log_time=get_local_time()))
                db.session.commit()
                return jsonify({"success": True, "msg": "تم التراجع عن الحجز واسترداد 20 USDD"})
            else:
                return jsonify({"success": False, "msg": "لا يمكنك إلغاء حجز لا يخصك!"})
        elif action == 'admin_draw' and username == 'admin1':
            winning_num = get_next_winning_number('golden', 1, 50)
            winner_b = GoldenNumberBooking.query.filter_by(number=winning_num).first()
            if winner_b:
                winner_u = User.query.filter_by(username=winner_b.username).first()
                if winner_u:
                    winner_u.balance += 700.0
                    vault.vault_balance -= 700.0
                    db.session.add(FinancialLog(action_type='جائزة الرقم الحنون', admin_name='admin1', target_user=winner_u.username, amount=700.0, log_time=get_local_time()))
            
            GoldenNumberBooking.query.delete()
            db.session.commit()
            return jsonify({"success": True, "winning_number": winning_num})
            
    bookings = {b.number: b.username for b in GoldenNumberBooking.query.all()}
    my_bookings_list = [b.number for b in GoldenNumberBooking.query.filter_by(username=username).all()]
    my_nums_str = ', '.join(map(str, my_bookings_list)) if my_bookings_list else 'لا يوجد حجوزات حالياً'
    my_total_cost = len(my_bookings_list) * 20.0

    return render_template_string(GAME_GOLDEN_PAGE, t=t, lang_key=lang_key, lang_bar=get_lang_bar(), username=username, balance=user.balance, bookings=bookings, my_nums_str=my_nums_str, my_total_cost=my_total_cost, msg=msg)

@app.route('/game_roulette_bet', methods=['POST'])
def game_roulette_bet():
    if 'username' not in session: return jsonify({"success": False})
    user = User.query.filter_by(username=session['username']).first()
    vault = SystemVault.query.get(1)
    data = request.get_json() or {}
    action = data.get('action')
    
    if action == 'add':
        if user.balance >= 1.0:
            user.balance -= 1.0
            vault.vault_balance += 1.0
            db.session.add(FinancialLog(action_type='مبيع رهان روليت الحظ', admin_name='system', target_user=user.username, amount=1.0, log_time=get_local_time()))
            db.session.commit()
            return jsonify({"success": True, "balance": user.balance})
        else:
            return jsonify({"success": False, "msg": "رصيد غير كافي!"})
    elif action == 'remove':
        user.balance += 1.0
        vault.vault_balance -= 1.0
        db.session.commit()
        return jsonify({"success": True, "balance": user.balance})
    return jsonify({"success": False})

@app.route('/game_roulette_draw', methods=['POST'])
def game_roulette_draw():
    if 'username' not in session: return jsonify({"success": False})
    user = User.query.filter_by(username=session['username']).first()
    vault = SystemVault.query.get(1)
    data = request.get_json() or {}
    bets = data.get('bets', {})

    winning_num = get_next_winning_number('roulette', 0, 36)
    
    total_payout = 0.0
    str_winning = str(winning_num)
    if str_winning in bets:
        mult = float(bets[str_winning])
        total_payout = mult * 20.0
        user.balance += total_payout
        vault.vault_balance -= total_payout
        db.session.add(FinancialLog(action_type='جائزة روليت الحظ', admin_name='system', target_user=user.username, amount=total_payout, log_time=get_local_time()))
        db.session.commit()
        msg = f"🎉 مبروك! ظهر الرقم الفائز #{winning_num} وفزت بـ {total_payout} USDD!"
    else:
        msg = f"❌ حظ أوفر! الرقم الفائز كان #{winning_num}"

    return jsonify({"success": True, "winning_number": winning_num, "msg": msg, "balance": user.balance})

@app.route('/game_roulette', methods=['GET'])
def game_roulette():
    if 'username' not in session: return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    t = get_t()
    lang_key = session.get('lang', 'ar')
    return render_template_string(GAME_ROULETTE_PAGE, t=t, lang_key=lang_key, lang_bar=get_lang_bar(), balance=user.balance)

@app.route('/game_numbers_empire', methods=['GET', 'POST'])
def game_numbers_empire():
    if 'username' not in session: return redirect(url_for('login'))
    username = session['username']
    user = User.query.filter_by(username=username).first()
    vault = SystemVault.query.get(1)
    t = get_t()
    lang_key = session.get('lang', 'ar')
    if request.method == 'POST':
        action = request.form.get('action_type')
        box = int(request.form.get('box_number', 0))
        if action == 'book' and user.balance >= 500.0 and not NumbersEmpireBooking.query.filter_by(number=box).first():
            user.balance -= 500.0
            vault.vault_balance += 500.0
            db.session.add(FinancialLog(action_type='مبيع رهان إمبراطورية الأرقام', admin_name='system', target_user=username, amount=500.0, log_time=get_local_time()))
            db.session.add(NumbersEmpireBooking(username=username, number=box, booking_date=get_local_time()))
            db.session.commit()
            return jsonify({"success": True, "msg": f"تم حجز المربع #{box}"})
        elif action == 'cancel':
            b = NumbersEmpireBooking.query.filter_by(number=box, username=username).first()
            if b:
                db.session.delete(b)
                user.balance += 500.0
                vault.vault_balance -= 500.0
                db.session.add(FinancialLog(action_type='استرجاع رهان إمبراطورية الأرقام', admin_name='system', target_user=username, amount=500.0, log_time=get_local_time()))
                db.session.commit()
                return jsonify({"success": True, "msg": "تم التراجع واسترداد 500 USDD"})
        elif action == 'admin_draw' and username == 'admin1':
            winning_num = get_next_winning_number('empire', 1, 5)
            winner_b = NumbersEmpireBooking.query.filter_by(number=winning_num).first()
            if winner_b:
                winner_u = User.query.filter_by(username=winner_b.username).first()
                if winner_u:
                    winner_u.balance += 2000.0
                    vault.vault_balance -= 2000.0
                    db.session.add(FinancialLog(action_type='جائزة إمبراطورية الأرقام', admin_name='admin1', target_user=winner_u.username, amount=2000.0, log_time=get_local_time()))
            msg = f"انتهى السحب الفاخر! الرقم الفائز الملكي: #{winning_num}"
            NumbersEmpireBooking.query.delete()
            db.session.commit()
            return jsonify({"success": True, "winning_number": winning_num, "msg": msg})
    bookings = {b.number: b.username for b in NumbersEmpireBooking.query.all()}
    return render_template_string(GAME_NUMBERS_EMPIRE_PAGE, t=t, lang_key=lang_key, lang_bar=get_lang_bar(), username=username, balance=user.balance, bookings=bookings)

@app.route('/game_number_wheel', methods=['GET', 'POST'])
def game_number_wheel():
    if 'username' not in session: return redirect(url_for('login'))
    username = session['username']
    user = User.query.filter_by(username=username).first()
    vault = SystemVault.query.get(1)
    t = get_t()
    lang_key = session.get('lang', 'ar')
    if request.method == 'POST':
        nums = json.loads(request.form.get('selected_numbers', '[]'))
        cost = float(len(nums) * 1.0)
        if nums and user.balance >= cost:
            user.balance -= cost
            vault.vault_balance += cost
            db.session.add(FinancialLog(action_type='مبيع رهان عجلة الحظ', admin_name='system', target_user=username, amount=cost, log_time=get_local_time()))
            
            winning_num = get_next_winning_number('wheel', 1, 20)
            if winning_num in nums:
                user.balance += 20.0
                vault.vault_balance -= 20.0
                db.session.add(FinancialLog(action_type='جائزة عجلة الحظ', admin_name='system', target_user=username, amount=20.0, log_time=get_local_time()))
                msg = f"مبروك ربحت 20 usdd للرقم {winning_num}"
            else:
                msg = "حظ اوفر"

            db.session.commit()
            return jsonify({"success": True, "winning_num": winning_num, "balance": user.balance, "msg": msg})
        else:
            return jsonify({"success": False, "msg": "رصيد غير كافي أو لم تختار أرقاماً!"})
    return render_template_string(GAME_WHEEL_PAGE, t=t, lang_key=lang_key, lang_bar=get_lang_bar(), balance=user.balance)

@app.route('/game_reveal_and_win', methods=['GET', 'POST'])
def game_reveal_and_win():
    if 'username' not in session: return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    vault = SystemVault.query.get(1)
    t = get_t()
    lang_key = session.get('lang', 'ar')
    
    state = RevealAndWinGlobalState.query.get(1)
    if not state:
        state = RevealAndWinGlobalState(id=1, total_spins=0)
        db.session.add(state)
        db.session.commit()

    if request.method == 'POST':
        if user.balance >= 2.0:
            user.balance -= 2.0
            vault.vault_balance += 2.0
            db.session.add(FinancialLog(action_type='مبيع رهان اكشف واربح', admin_name='system', target_user=user.username, amount=2.0, log_time=get_local_time()))
            
            state.total_spins += 1
            mod_val = state.total_spins % 100
            
            # تطابق 3 وجوه أسد مرة واحدة في كل 100 محاولة، و50 مرة لتطابق وجهين
            if mod_val == 0:
                revealed = ['🦁', '🦁', '🦁']
                session['reveal_outcome'] = 'win_3'
            elif mod_val <= 50:
                revealed = ['🦁', '🦁', random.choice(['7', '3'])]
                session['reveal_outcome'] = 'win_2'
            else:
                revealed = ['🦁', '7', '3']
                session['reveal_outcome'] = 'loss'

            db.session.commit()
            return jsonify({"success": True, "balance": user.balance, "revealed": revealed})
        else:
            return jsonify({"success": False, "msg": "رصيد غير كافي! تكلفة المحاولة 2 USDD"})

    return render_template_string(GAME_REVEAL_PAGE, t=t, lang_key=lang_key, lang_bar=get_lang_bar(), balance=user.balance)

@app.route('/game_reveal_result_check', methods=['POST'])
def game_reveal_result_check():
    if 'username' not in session: return jsonify({"success": False})
    user = User.query.filter_by(username=session['username']).first()
    vault = SystemVault.query.get(1)
    outcome = session.get('reveal_outcome', 'loss')
    
    if outcome == 'win_3':
        payout = 100.0
        user.balance += payout
        vault.vault_balance -= payout
        db.session.add(FinancialLog(action_type='جائزة اكشف واربح الكبرى', admin_name='system', target_user=user.username, amount=payout, log_time=get_local_time()))
        msg = "مبروك ربحت 100 USDD لتطابق ثلاثة وجوه أسد!"
    elif outcome == 'win_2':
        refund = 1.0
        user.balance += refund
        vault.vault_balance -= refund
        db.session.add(FinancialLog(action_type='استرجاع جزئي اكشف واربح', admin_name='system', target_user=user.username, amount=refund, log_time=get_local_time()))
        msg = "نجحت في تطابق وجهين أسد واسترددت 1 USDD!"
    else:
        msg = "حظ أوفر في المحاولة القادمة"

    db.session.commit()
    return jsonify({"success": True, "msg": msg, "balance": user.balance})

@app.route('/admin_game_control', methods=['GET', 'POST'])
def admin_game_control():
    if 'username' not in session or session.get('username') != 'admin1': return redirect(url_for('dashboard'))
    msg = None
    if request.method == 'POST':
        game_name = request.form.get('game_name')
        round_index = int(request.form.get('round_index', 1))
        winning_number = int(request.form.get('winning_number', 0))
        existing = GameFutureDraw.query.filter_by(game_name=game_name, round_index=round_index).first()
        if existing:
            existing.winning_number = winning_number
        else:
            db.session.add(GameFutureDraw(game_name=game_name, round_index=round_index, winning_number=winning_number))
        db.session.commit()
        msg = f"تمت برمجة الرقم {winning_number} للجولة #{round_index} في لعبة {game_name} بنجاح!"
    return render_template_string(ADMIN_GAME_CONTROL_PAGE, lang_bar=get_lang_bar(), msg=msg)

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
    messages = ChatMessage.query.filter(
        ((ChatMessage.sender == username) & (ChatMessage.recipient == 'admin1')) |
        ((ChatMessage.sender == 'admin1') & (ChatMessage.recipient == username))
    ).order_by(ChatMessage.id.asc()).all()
    return render_template_string(CHAT_PAGE, lang_bar=get_lang_bar(), username=username, messages=messages)

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
    chatting_users = db.session.query(ChatMessage.sender).filter(ChatMessage.sender != 'admin1').distinct().all()
    chatting_users = [u[0] for u in chatting_users]
    messages = []
    if active_user:
        messages = ChatMessage.query.filter(
            ((ChatMessage.sender == active_user) & (ChatMessage.recipient == 'admin1')) |
            ((ChatMessage.sender == 'admin1') & (ChatMessage.recipient == active_user))
        ).order_by(ChatMessage.id.asc()).all()
    return render_template_string(ADMIN_CHATS_PAGE, lang_bar=get_lang_bar(), chatting_users=chatting_users, active_user=active_user, messages=messages)

@app.route('/admin_customers', methods=['GET', 'POST'])
def admin_customers():
    if 'username' not in session or session.get('username') != 'admin1': return redirect(url_for('dashboard'))
    msg = None
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'create_player':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            balance = float(request.form.get('balance', 0.0))
            owner_name = request.form.get('owner_name', 'غير محدد').strip()
            if username and password and not User.query.filter_by(username=username).first():
                db.session.add(User(username=username, password=password, balance=balance, role='user', created_by=session['username'], owner_name=owner_name))
                db.session.add(FinancialLog(action_type='إنشاء حساب لاعب جديد', admin_name=session['username'], target_user=username, amount=balance, log_time=get_local_time()))
                db.session.commit()
                msg = f"تم إنشاء حساب اللاعب {username} بنجاح!"
            else:
                msg = "خطأ: اسم المستخدم موجود مسبقاً أو بيانات ناقصة!"
    return render_template_string(ADMIN_CUSTOMERS_PAGE, lang_bar=get_lang_bar(), users_list=User.query.all(), msg=msg)

@app.route('/admin_accounting', methods=['GET', 'POST'])
def admin_accounting():
    if 'username' not in session or session.get('username') != 'admin1': return redirect(url_for('dashboard'))
    vault = SystemVault.query.get(1)
    msg = None
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'sell_currency':
            target, amount = request.form.get('target_user'), float(request.form.get('amount', 0))
            if vault.vault_balance >= amount:
                vault.vault_balance -= amount
                User.query.filter_by(username=target).first().balance += amount
                db.session.add(FinancialLog(action_type='بيع عملات للزبون', admin_name='admin1', target_user=target, amount=amount, log_time=get_local_time()))
                db.session.commit()
                msg = "تم بيع العملات بنجاح!"
        elif action == 'buy_back_currency':
            target, amount = request.form.get('target_user'), float(request.form.get('amount', 0))
            u = User.query.filter_by(username=target).first()
            if u and u.balance >= amount:
                u.balance -= amount
                vault.vault_balance += amount
                db.session.add(FinancialLog(action_type='سحب رصيد من الزبون', admin_name='admin1', target_user=target, amount=amount, log_time=get_local_time()))
                db.session.commit()
                msg = "تم سحب الرصيد بنجاح!"
        elif action == 'generate_card':
            amount = float(request.form.get('card_amount', 100))
            if amount in [100.0, 200.0, 300.0, 500.0, 1000.0]:
                code_str = 'EMP-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8)) + f'-{int(amount)}'
                db.session.add(RechargeCard(code=code_str, amount=amount, is_used=False, created_at=get_local_time()))
                db.session.add(FinancialLog(action_type=f'توليد كود شحن فئة {int(amount)}', admin_name='admin1', target_user='system', amount=amount, log_time=get_local_time()))
                db.session.commit()
                msg = f"تم توليد الكود: {code_str}"
    logs = FinancialLog.query.order_by(FinancialLog.id.desc()).all()
    cards = RechargeCard.query.order_by(RechargeCard.id.desc()).all()
    tp_sold = db.session.query(db.func.sum(FinancialLog.amount)).filter(FinancialLog.action_type.in_(['بيع عملات للزبون', 'شحن عبر بطاقة كود'])).scalar() or 0.0
    tg_bets = db.session.query(db.func.sum(FinancialLog.amount)).filter(FinancialLog.action_type.like('%مبيع رهان%')).scalar() or 0.0
    tpayouts = db.session.query(db.func.sum(FinancialLog.amount)).filter(FinancialLog.action_type.like('%جائزة%')).scalar() or 0.0
    net = tg_bets - tpayouts
    return render_template_string(ADMIN_ACCOUNTING_TEMPLATE, lang_bar=get_lang_bar(), vault_balance=vault.vault_balance if vault else 0.0, logs=logs, cards=cards, total_points_sold=tp_sold, total_game_bets=tg_bets, total_payouts=tpayouts, net_game_result=net, users_list=User.query.all(), msg=msg)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
