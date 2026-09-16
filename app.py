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

class NumbersEmpireState(db.Model):
    __tablename__ = 'numbers_empire_state'
    id = db.Column(db.Integer, primary_key=True)
    winning_number = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='idle')
    draw_end_time = db.Column(db.Float, default=0)
    forced_winning_number = db.Column(db.Integer, default=0)

class GameDrawState(db.Model):
    __tablename__ = 'game_draw_state'
    id = db.Column(db.Integer, primary_key=True)
    winning_number = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='idle')
    draw_end_time = db.Column(db.Float, default=0)
    forced_winning_number = db.Column(db.Integer, default=0)

# --- تهيئة الجداول وحفظ البيانات ---
with app.app_context():
    db.create_all()
    vault = SystemVault.query.get(1)
    if not vault:
        db.session.add(SystemVault(id=1, vault_balance=1000000.0))
    if not User.query.filter_by(username='admin1').first():
        db.session.add(User(username='admin1', password='admin123', balance=0.0, role='admin', created_by='system', owner_name='المشرف العام'))
    if not GameDrawState.query.get(1):
        db.session.add(GameDrawState(id=1, winning_number=0, status='idle', draw_end_time=0, forced_winning_number=0))
    if not NumbersEmpireState.query.get(1):
        db.session.add(NumbersEmpireState(id=1, winning_number=0, status='idle', draw_end_time=0, forced_winning_number=0))
    db.session.commit()

# --- قاموس الترجمات الشامل (6 لغات) ---
TRANSLATIONS = {
    'ar': {
        'dir': 'rtl', 'title': 'امبراطورية الأرقام', 'subtitle': 'منصة الألعاب التفاعلية الفائقة 12D',
        'login': 'دخول للبرنامج', 'username': 'اسم المستخدم', 'password': 'كلمة المرور', 'balance': 'الرصيد',
        'recharge': 'شحن رصيد', 'withdraw': 'سحب رصيد', 'change_pass': 'تغيير الباسورد', 'logout': 'خروج',
        'dashboard': 'لوحة التحكم', 'back_dash': '🏠 الرئيسية', 'customers': 'الزبائن', 'accounting': 'المحاسبة والخزنة',
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
        'game1': 'The Tender Number', 'game2': 'Lucky Roulette', 'game3': 'Empire of Numbers',
        'game4': 'Number Wheel', 'game5': 'Reveal & Win', 'game6': '70 USDD Game',
        'cost': 'Cost', 'prize': 'Prize', 'book': 'Book', 'cancel': 'Cancel', 'booked': 'Booked',
        'spin': 'Spin Wheel', 'reveal': 'Reveal Boxes', 'draw_now': 'Draw Now'
    },
    'fr': {
        'dir': 'ltr', 'title': 'Empire des Nombres', 'subtitle': 'Plateforme de Jeux Super Interactive 12D',
        'login': 'Connexion', 'username': "Nom d'utilisateur", 'password': 'Mot de passe', 'balance': 'Solde',
        'recharge': 'Recharger', 'withdraw': 'Retirer', 'change_pass': 'Changer le mot de passe', 'logout': 'Déconnexion',
        'dashboard': 'Tableau de bord', 'back_dash': '🏠 Accueil', 'customers': 'Clients', 'accounting': 'Comptabilité et Coffre',
        'game1': 'Le Numéro Tendre', 'game2': 'Roulette Chanceuse', 'game3': 'Empire des Nombres',
        'game4': 'Roue des Nombres', 'game5': 'Révéler et Gagner', 'game6': 'Jeu 70 USDD',
        'cost': 'Coût', 'prize': 'Prix', 'book': 'Réserver', 'cancel': 'Annuler', 'booked': 'Réservé',
        'spin': 'Tourner la roue', 'reveal': 'Révéler les boîtes', 'draw_now': 'Tirer maintenant'
    },
    'de': {
        'dir': 'ltr', 'title': 'Imperium der Zahlen', 'subtitle': 'Super Interaktive 12D Gaming Plattform',
        'login': 'Anmelden', 'username': 'Benutzername', 'password': 'Passwort', 'balance': 'Guthaben',
        'recharge': 'Aufladen', 'withdraw': 'Auszahlen', 'change_pass': 'Passwort ändern', 'logout': 'Abmelden',
        'dashboard': 'Dashboard', 'back_dash': '🏠 Startseite', 'customers': 'Kunden', 'accounting': 'Buchhaltung & Tresor',
        'game1': 'Die Zarte Nummer', 'game2': 'Glücks-Roulette', 'game3': 'Imperium der Zahlen',
        'game4': 'Zahlenrad', 'game5': 'Aufdecken & Gewinnen', 'game6': '70 USDD Spiel',
        'cost': 'Kosten', 'prize': 'Gewinn', 'book': 'Buchen', 'cancel': 'Abbrechen', 'booked': 'Gebucht',
        'spin': 'Rad drehen', 'reveal': 'Boxen aufdecken', 'draw_now': 'Jetzt ziehen'
    },
    'es': {
        'dir': 'ltr', 'title': 'Imperio de los Números', 'subtitle': 'Plataforma de Juegos Super Interactiva 12D',
        'login': 'Iniciar Sesión', 'username': 'Nombre de usuario', 'password': 'Contraseña', 'balance': 'Saldo',
        'recharge': 'Recargar', 'withdraw': 'Retirar', 'change_pass': 'Cambiar Contraseña', 'logout': 'Cerrar Sesión',
        'dashboard': 'Panel', 'back_dash': '🏠 Inicio', 'customers': 'Clientes', 'accounting': 'Contabilidad y Bóveda',
        'game1': 'El Número Tierno', 'game2': 'Ruleta de la Suerte', 'game3': 'Imperio de los Números',
        'game4': 'Rueda Numérica', 'game5': 'Revelar y Ganar', 'game6': 'Juego 70 USDD',
        'cost': 'Costo', 'prize': 'Premio', 'book': 'Reservar', 'cancel': 'Cancelar', 'booked': 'Reservado',
        'spin': 'Girar Rueda', 'reveal': 'Revelar Cajas', 'draw_now': 'Sorteo'
    },
    'fa': {
        'dir': 'rtl', 'title': 'امپراتوری اعداد', 'subtitle': 'پلتفرم بازی‌های تعاملی فوق‌العاده 12D',
        'login': 'ورود به برنامه', 'username': 'نام کاربری', 'password': 'رمز عبور', 'balance': 'موجودی',
        'recharge': 'شارژ حساب', 'withdraw': 'برداشت وجه', 'change_pass': 'تغییر رمز عبور', 'logout': 'خروج',
        'dashboard': 'داشبورد', 'back_dash': '🏠 صفحه اصلی', 'customers': 'مشتریان', 'accounting': 'حسابداری و خزانه',
        'game1': 'عدد مهربان', 'game2': 'رولت شانس', 'game3': 'امپراتوری اعداد',
        'game4': 'گردونه اعداد', 'game5': 'کشف کن و برنده شو', 'game6': 'بازی 70 USDD',
        'cost': 'هزینه', 'prize': 'جایزه', 'book': 'رزرو', 'cancel': 'لغو', 'booked': 'رزرو شده',
        'spin': 'چرخش گردونه', 'reveal': 'کشف جعبه‌ها', 'draw_now': 'قرعه‌کشی'
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
            <option value="fr" {'selected' if curr=='fr' else ''}>Français 🇫🇷</option>
            <option value="de" {'selected' if curr=='de' else ''}>Deutsch 🇩🇪</option>
            <option value="es" {'selected' if curr=='es' else ''}>Español 🇪🇸</option>
            <option value="fa" {'selected' if curr=='fa' else ''}>فارسی 🇮🇷</option>
        </select>
    </div>
    <div>
        <a href="/dashboard" style="color:#ffd700; text-decoration:none; font-weight:bold; font-size:14px;">🏠 الرئيسية</a>
    </div>
</div>
"""

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

GAME_GOLDEN_PAGE = """
<!DOCTYPE html>
<html lang="{{ lang_key }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><title>{{ t.game1 }} - 12D</title>
    <style>
        body { font-family:'Segoe UI', Tahoma, sans-serif; background:radial-gradient(circle at center, #151928 0%, #070a12 100%); color:#fff; margin:0; padding:25px; }
        .card-3d { background:linear-gradient(135deg, rgba(31,26,15,0.95), rgba(13,13,13,0.95)); border:4px solid #ffd700; padding:35px; border-radius:30px; max-width:950px; margin:20px auto; box-shadow:0 30px 70px rgba(0,0,0,0.9); }
        .grid { display:grid; grid-template-columns:repeat(10, 1fr); gap:12px; margin-top:25px; }
        .cell { background:linear-gradient(145deg, #7c3aed, #4c1d95); border:3px solid #a78bfa; border-radius:16px; height:80px; display:flex; flex-direction:column; align-items:center; justify-content:center; font-weight:900; cursor:pointer; color:#fff; font-size: 22px; transition:0.3s; }
        .cell.booked { background: #7f1d1d !important; border-color:#ef4444 !important; cursor:not-allowed; }
        .cell.my { background: #1e3a8a !important; border-color:#3b82f6 !important; }
    </style>
</head>
<body>
    {{ lang_bar | safe }}
    <div style="display:flex; justify-content:space-between; align-items:center; max-width:950px; margin:15px auto; background:rgba(20,24,38,0.9); padding:15px 25px; border-radius:15px;">
        <h2 style="color:#ffd700; margin:0;">🏆 {{ t.game1 }}</h2>
        <div><b>{{ t.balance }}: <span id="liveBalance">{{ balance }}</span> USDD</b></div>
    </div>
    <div class="card-3d">
        <p style="text-align:center; color:#ffd700; font-size:20px; font-weight:900;">{{ t.cost }}: 20 USDD | {{ t.prize }}: 750 USDD</p>
        <div class="grid">
            {% for i in range(1, 51) %}
                {% if i in bookings %}
                    {% if bookings[i] == username %}
                        <button type="button" onclick="handleAction('cancel', {{ i }})" class="cell my">{{ i }}<br><span style="font-size:12px;">{{ t.cancel }}</span></button>
                    {% else %}
                        <div class="cell booked">{{ i }}<br><span style="font-size:12px;">{{ bookings[i] }}</span></div>
                    {% endif %}
                {% else %}
                    <button type="button" onclick="handleAction('book', {{ i }})" class="cell">{{ i }}</button>
                {% endif %}
            {% endfor %}
        </div>
        {% if username == 'admin1' %}
            <div style="margin-top:35px; text-align:center;">
                <button type="button" onclick="handleAction('admin_draw', 0)" style="background:#22c55e; color:#fff; font-weight:900; padding:15px 35px; border:none; border-radius:12px; cursor:pointer; font-size:18px;">⚡ {{ t.draw_now }}</button>
            </div>
        {% endif %}
    </div>
    <script>
        function handleAction(actionType, num) {
            let fd = new FormData();
            fd.append('action_type', actionType);
            fd.append('number', num);
            fetch('/game_golden_number', {method: 'POST', body: fd}).then(res => res.json()).then(d => {
                if(d.msg) alert(d.msg);
                location.reload();
            });
        }
    </script>
</body>
</html>
"""

GAME_NUMBERS_EMPIRE_PAGE = """
<!DOCTYPE html>
<html lang="{{ lang_key }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><title>{{ t.game3 }}</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: #151928; color: #f8fafc; margin: 0; padding: 25px; text-align: center; }
        .empire-card { background: rgba(25,30,48,0.95); border: 4px solid #ffd700; padding: 40px; border-radius: 30px; max-width: 850px; margin: 20px auto; }
        .boxes-grid { display: flex; justify-content: center; gap: 20px; margin: 30px 0; flex-wrap: wrap; }
        .box-item { width: 120px; height: 130px; background: #7c3aed; border: 3px solid #ffd700; border-radius: 20px; color: #fff; font-size: 22px; font-weight: 900; cursor: pointer; display: flex; flex-direction: column; align-items: center; justify-content: center; }
        .box-item.booked { background: #7f1d1d !important; border-color: #ef4444 !important; }
        .box-item.my { background: #1e3a8a !important; border-color: #3b82f6 !important; }
    </style>
</head>
<body>
    {{ lang_bar | safe }}
    <div class="empire-card">
        <h2 style="color:#ffd700;">🏛️ {{ t.game3 }}</h2>
        <p><b>{{ t.balance }}: {{ balance }} USDD</b></p>
        <div class="boxes-grid">
            {% for i in range(1, 6) %}
                {% if i in bookings %}
                    {% if bookings[i] == username %}
                        <button type="button" onclick="handleEmpireAction('cancel', {{ i }})" class="box-item my"><span>👑</span><span>{{ i }}</span></button>
                    {% else %}
                        <div class="box-item booked"><span>👑</span><span>{{ i }}</span><span style="font-size:11px;">{{ bookings[i] }}</span></div>
                    {% endif %}
                {% else %}
                    <button type="button" onclick="handleEmpireAction('book', {{ i }})" class="box-item"><span>👑</span><span>{{ i }}</span></button>
                {% endif %}
            {% endfor %}
        </div>
    </div>
    <script>
        function handleEmpireAction(type, box) {
            let fd = new FormData();
            fd.append('action_type', type);
            fd.append('box_number', box);
            fetch('/game_numbers_empire', {method: 'POST', body: fd}).then(res => res.json()).then(d => {
                if(d.msg) alert(d.msg);
                location.reload();
            });
        }
    </script>
</body>
</html>
"""

GAME_NUMBER_WHEEL_PAGE = """
<!DOCTYPE html>
<html lang="{{ lang_key }}" dir="{{ t.dir }}">
<head><meta charset="UTF-8"><title>{{ t.game4 }}</title>
<style>body{background:#151928;color:#fff;text-align:center;padding:25px;font-family:Tahoma;} .grid{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;max-width:400px;margin:20px auto;} .btn{padding:15px;background:#1f2937;color:#fff;border:2px solid #ffd700;border-radius:10px;font-weight:bold;cursor:pointer;} .btn.selected{background:#d97706;color:#000;}</style>
</head>
<body>
    {{ lang_bar | safe }}
    <div style="max-width:600px;margin:30px auto;background:#1e2336;padding:30px;border-radius:20px;border:3px solid #ffd700;">
        <h2 style="color:#ffd700;">🎡 {{ t.game4 }}</h2>
        <p><b>{{ t.balance }}: <span id="bal">{{ balance }}</span> USDD</b></p>
        <div class="grid">
            {% for n in range(1, 21) %}
            <button onclick="toggle({{ n }})" id="btn_{{ n }}" class="btn">{{ n }}</button>
            {% endfor %}
        </div>
        <button onclick="spin()" style="padding:15px 35px;background:#22c55e;color:#fff;font-weight:bold;border:none;border-radius:12px;cursor:pointer;">{{ t.spin }}</button>
    </div>
    <script>
        let sel = [];
        function toggle(n) {
            let i = sel.indexOf(n);
            if(i > -1) { sel.splice(i,1); document.getElementById('btn_'+n).classList.remove('selected'); }
            else { sel.push(n); document.getElementById('btn_'+n).classList.add('selected'); }
        }
        function spin() {
            if(sel.length===0){alert("اختر رقمأً واحداً على الأقل!");return;}
            let fd = new FormData(); fd.append('selected_numbers', JSON.stringify(sel));
            fetch('/game_number_wheel', {method:'POST', body:fd}).then(r=>r.json()).then(d=>{
                alert(d.msg); location.reload();
            });
        }
    </script>
</body>
</html>
"""

GAME_REVEAL_AND_WIN_PAGE = """
<!DOCTYPE html>
<html lang="{{ lang_key }}" dir="{{ t.dir }}">
<head><meta charset="UTF-8"><title>{{ t.game5 }}</title>
<style>body{background:#151928;color:#fff;text-align:center;padding:25px;font-family:Tahoma;}</style>
</head>
<body>
    {{ lang_bar | safe }}
    <div style="max-width:600px;margin:30px auto;background:#1e2336;padding:30px;border-radius:20px;border:3px solid #ffd700;">
        <h2 style="color:#ffd700;">🎟️ {{ t.game5 }}</h2>
        <p><b>{{ t.balance }}: <span id="bal">{{ balance }}</span> USDD</b></p>
        <button onclick="play()" style="padding:16px 40px;background:#ffd700;color:#000;font-weight:900;border:none;border-radius:15px;cursor:pointer;font-size:18px;">{{ t.reveal }}</button>
    </div>
    <script>
        function play() {
            fetch('/game_reveal_and_win', {method:'POST'}).then(r=>r.json()).then(d=>{
                alert(d.msg); location.reload();
            });
        }
    </script>
</body>
</html>
"""

GAME_20_NUMBERS_PAGE = """
<!DOCTYPE html>
<html lang="{{ lang_key }}" dir="{{ t.dir }}">
<head><meta charset="UTF-8"><title>{{ t.game6 }}</title>
<style>body{background:#151928;color:#fff;text-align:center;padding:25px;font-family:Tahoma;} .grid{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;max-width:400px;margin:20px auto;} .btn{padding:15px;background:#1f2937;color:#fff;border:2px solid #ffd700;border-radius:10px;font-weight:bold;cursor:pointer;} .btn.selected{background:#d97706;color:#000;}</style>
</head>
<body>
    {{ lang_bar | safe }}
    <div style="max-width:600px;margin:30px auto;background:#1e2336;padding:30px;border-radius:20px;border:3px solid #ffd700;">
        <h2 style="color:#ffd700;">💎 {{ t.game6 }}</h2>
        <p><b>{{ t.balance }}: <span id="bal">{{ balance }}</span> USDD</b></p>
        <div class="grid">
            {% for n in range(1, 21) %}
            <button onclick="toggle({{ n }})" id="btn20_{{ n }}" class="btn">{{ n }}</button>
            {% endfor %}
        </div>
        <button onclick="spin20()" style="padding:15px 35px;background:#ffd700;color:#000;font-weight:bold;border:none;border-radius:12px;cursor:pointer;">{{ t.spin }}</button>
    </div>
    <script>
        let sel = [];
        function toggle(n) {
            let i = sel.indexOf(n);
            if(i > -1) { sel.splice(i,1); document.getElementById('btn20_'+n).classList.remove('selected'); }
            else { sel.push(n); document.getElementById('btn20_'+n).classList.add('selected'); }
        }
        function spin20() {
            if(sel.length===0){alert("اختر رقماً واحداً على الأقل!");return;}
            fetch('/game_20_numbers', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({selected_numbers:sel})}).then(r=>r.json()).then(d=>{
                alert(d.msg); location.reload();
            });
        }
    </script>
</body>
</html>
"""

GAME_ROULETTE_GLOBAL_PAGE = """
<!DOCTYPE html>
<html lang="{{ lang_key }}" dir="{{ t.dir }}">
<head><meta charset="UTF-8"><title>{{ t.game2 }}</title></head>
<body style="background:#151928;color:#fff;text-align:center;padding:25px;font-family:Tahoma;">
    {{ lang_bar | safe }}
    <div style="max-width:600px;margin:30px auto;background:#1e2336;padding:30px;border-radius:20px;border:3px solid #ffd700;">
        <h2 style="color:#ffd700;">🎰 {{ t.game2 }}</h2>
        <p><b>{{ t.balance }}: {{ balance }} USDD</b></p>
        <button onclick="spinR()" style="padding:15px 35px;background:#22c55e;color:#fff;font-weight:bold;border:none;border-radius:12px;cursor:pointer;">{{ t.spin }}</button>
    </div>
    <script>
        function spinR() {
            fetch('/game_roulette', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({selected_numbers:[1,2,3]})}).then(r=>r.json()).then(d=>{
                alert(d.msg); location.reload();
            });
        }
    </script>
</body>
</html>
"""

# --- صفحة إدارة الزبائن المحدثة (تتضمن إنشاء حساب لاعب جديد مع كافة المعلومات) ---
ADMIN_CUSTOMERS_PAGE = """
<!DOCTYPE html>
<html lang="{{ lang_key }}" dir="{{ t.dir }}">
<head><meta charset="UTF-8"><title>إدارة الزبائن</title>
<style>body{font-family:Tahoma; background:#151928; color:#fff; padding:20px; text-align:center;} table{width:100%; border-collapse:collapse; margin-top:15px;} th, td{border:1px solid #444; padding:10px;} th{background:#0a0d16; color:#ffd700;} input{padding:10px; margin:5px; width:100%; box-sizing:border-box; background:#0a0d16; color:#fff; border:1px solid #444; border-radius:8px;}</style>
</head>
<body>
    {{ lang_bar | safe }}
    <h2>👥 إدارة الزبائن وحسابات اللاعبين</h2>
    
    {% if msg %}<div style="background:#065f46; color:#34d399; padding:12px; border-radius:10px; margin:15px auto; max-width:500px; font-weight:bold;">{{ msg }}</div>{% endif %}

    <!-- نموذج إنشاء حساب لاعب جديد مع كافة المعلومات اللازمة -->
    <div style="background:rgba(25,30,48,0.9); padding:25px; border-radius:16px; max-width:550px; margin:20px auto; border:2px solid #ffd700; text-align:{{ 'right' if t.dir=='rtl' else 'left' }};">
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

# --- صفحة المحاسبة المحدثة (كودات الشحن للفئات 100، 200، 300، 500، 1000 وبدون بيع 1000 مباشر) ---
ADMIN_ACCOUNTING_TEMPLATE = """
<!DOCTYPE html>
<html lang="{{ lang_key }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>برنامج المحاسبة - 12D</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: #151928; color: #f8fafc; padding: 25px; text-align: center; }
        .panel-box { background: rgba(25,30,48,0.9); padding: 22px; border-radius: 16px; max-width: 500px; margin: 20px auto; border: 2px solid #ffd700; text-align: right; }
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
        <div class="stat-card" style="border-color: #ffd700;">
            <h4 style="color:#ffd700; margin:0;">💳 النقاط المباعة</h4>
            <div style="font-size:24px; font-weight:bold; margin-top:10px; color:#fff;">{{ total_points_sold }} USDD</div>
        </div>
        <div class="stat-card" style="border-color: #38bdf8;">
            <h4 style="color:#38bdf8; margin:0;">📥 الواردات (الرهانات)</h4>
            <div style="font-size:24px; font-weight:bold; margin-top:10px; color:#fff;">{{ total_game_bets }} USDD</div>
        </div>
        <div class="stat-card" style="border-color: #ef4444;">
            <h4 style="color:#ef4444; margin:0;">🎁 الجوائز</h4>
            <div style="font-size:24px; font-weight:bold; margin-top:10px; color:#fff;">{{ total_payouts }} USDD</div>
        </div>
        <div class="stat-card" style="border-color: #34d399;">
            <h4 style="color:#34d399; margin:0;">📈 صافي أرباح الشركة</h4>
            <div style="font-size:24px; font-weight:bold; margin-top:10px; color:#34d399;">{{ net_game_result }} USDD</div>
        </div>
    </div>

    <div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;">
        <!-- بيع عملات مباشر -->
        <div class="panel-box">
            <h3 style="color: #22c55e; text-align:center;">⚡ بيع عملات مباشر</h3>
            <form method="POST">
                <input type="hidden" name="action" value="sell_currency">
                <label>اختر الحساب:</label>
                <select name="target_user" required>
                    <option value="">اختر الحساب</option>
                    {% for u in users_list %}<option value="{{ u.username }}">{{ u.username }} (رصيده: {{ u.balance }})</option>{% endfor %}
                </select>
                <label>المبلغ (USDD):</label><input type="number" name="amount" min="1" required>
                <button type="submit" style="background:#22c55e; color:#000; padding:12px; font-weight:900; border:none; border-radius:8px; width:100%; cursor:pointer; margin-top:10px;">إتمام البيع</button>
            </form>
        </div>

        <!-- توليد كودات الشحن بالفئات المطلوبة (100، 200، 300، 500، 1000) -->
        <div class="panel-box" style="border-color: #ffd700;">
            <h3 style="color: #ffd700; text-align:center;">🎟️ توليد كودات الشحن</h3>
            <form method="POST">
                <input type="hidden" name="action" value="generate_card">
                <label>اختر فئة كود الشحن (USDD):</label>
                <select name="card_amount" required>
                    <option value="100">100 USDD</option>
                    <option value="200">200 USDD</option>
                    <option value="300">300 USDD</option>
                    <option value="500">500 USDD</option>
                    <option value="1000">1000 USDD</option>
                </select>
                <button type="submit" style="background:#ffd700; color:#000; padding:12px; font-weight:900; border:none; border-radius:8px; width:100%; cursor:pointer; margin-top:25px;">توليد كود الشحن 🎫</button>
            </form>
        </div>
    </div>

    <!-- جدول كودات الشحن المولدة -->
    <div style="background: rgba(25,30,48,0.9); padding: 30px; border-radius: 20px; max-width: 900px; margin: 30px auto;">
        <h3 style="color: #ffd700;">🎫 كودات الشحن النشطة والمستخدمة</h3>
        <table>
            <tr><th>الكود</th><th>الفئة</th><th>الحالة</th><th>استخدمه</th><th>وقت الإنشاء</th></tr>
            {% for c in cards %}
            <tr>
                <td style="color:#38bdf8; font-family:monospace; font-size:16px;"><b>{{ c.code }}</b></td>
                <td>{{ c.amount }} USDD</td>
                <td>{{ 'مستخدم ❌' if c.is_used else 'متاح للاتصال ✅' }}</td>
                <td>{{ c.used_by if c.used_by else '---' }}</td>
                <td>{{ c.created_at }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>

    <!-- سجل العمليات المالية -->
    <div style="background: rgba(25,30,48,0.9); padding: 30px; border-radius: 20px; max-width: 900px; margin: 30px auto;">
        <h3 style="color: #ffd700;">📋 سجل العمليات المالية</h3>
        <table>
            <tr><th>نوع العملية</th><th>المسؤول</th><th>الهدف</th><th>المبلغ</th><th>التوقيت</th></tr>
            {% for log in logs %}
            <tr><td><b>{{ log.action_type }}</b></td><td>{{ log.admin_name }}</td><td>{{ log.target_user }}</td><td style="color: #34d399;">{{ log.amount }} USDD</td><td>{{ log.log_time }}</td></tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

CHANGE_PASSWORD_PAGE = """
<!DOCTYPE html>
<html lang="{{ lang_key }}" dir="{{ t.dir }}">
<head><meta charset="UTF-8"><title>{{ t.change_pass }}</title></head>
<body style="font-family:Tahoma; background:#151928; color:#fff; text-align:center; padding:50px;">
    {{ lang_bar | safe }}
    <h3>{{ t.change_pass }}</h3>
    <a href="/dashboard">{{ t.back_dash }}</a>
</body>
</html>
"""

# --- المسارات وتوجيه اللغات ---

@app.route('/set_lang/<lang>')
def set_lang(lang):
    if lang in TRANSLATIONS: session['lang'] = lang
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/manifest.json')
def manifest():
    return jsonify({"name": "Empire of Numbers 12D", "short_name": "Empire12D", "start_url": "/", "display": "standalone", "background_color": "#0b0f19", "theme_color": "#ffd700"})

@app.route('/sw.js')
def service_worker():
    return app.response_class("self.addEventListener('fetch', function(event) { });", mimetype='application/javascript')

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
    return render_template_string(DASHBOARD_PAGE, t=t, lang_key=lang_key, lang_bar=get_lang_bar(), username=user.username, role=user.role, balance=user.balance)

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'username' not in session: return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    t = get_t()
    lang_key = session.get('lang', 'ar')
    return render_template_string(CHANGE_PASSWORD_PAGE, t=t, lang_key=lang_key, lang_bar=get_lang_bar(), username=user.username, balance=user.balance)

# --- مسارات الألعاب ---

@app.route('/game_golden_number', methods=['GET', 'POST'])
def game_golden_number():
    if 'username' not in session: return redirect(url_for('login'))
    username = session['username']
    user = User.query.filter_by(username=username).first()
    vault = SystemVault.query.get(1)
    draw_state = GameDrawState.query.get(1)
    t = get_t()
    lang_key = session.get('lang', 'ar')
    if request.method == 'POST':
        action_type = request.form.get('action_type')
        if action_type == 'book' and draw_state.status == 'idle':
            number = int(request.form.get('number', 0))
            if user.balance >= 20.0 and not GoldenNumberBooking.query.filter_by(number=number).first():
                user.balance -= 20.0
                vault.vault_balance += 20.0
                db.session.add(FinancialLog(action_type='مبيع رهان الرقم الحنون', admin_name='system', target_user=username, amount=20.0, log_time=get_local_time()))
                db.session.add(GoldenNumberBooking(username=username, number=number, booking_date=get_local_time()))
                db.session.commit()
                return jsonify({"success": True, "msg": f"تم حجز الرقم {number} مقابل 20 USDD!"})
            else:
                return jsonify({"success": False, "msg": "رصيد غير كافي أو محجوز!"})
        elif action_type == 'cancel' and draw_state.status == 'idle':
            number = int(request.form.get('number', 0))
            b = GoldenNumberBooking.query.filter_by(number=number, username=username).first()
            if b:
                db.session.delete(b)
                user.balance += 20.0
                vault.vault_balance -= 20.0
                db.session.add(FinancialLog(action_type='استرجاع رهان الرقم الحنون', admin_name='system', target_user=username, amount=20.0, log_time=get_local_time()))
                db.session.commit()
                return jsonify({"success": True, "msg": "تم التراجع واسترداد 20 USDD!"})
        elif action_type == 'admin_draw' and username == 'admin1':
            winning_num = random.randint(1, 50)
            draw_state.winning_number = winning_num
            draw_state.status = 'finished'
            winner_b = GoldenNumberBooking.query.filter_by(number=winning_num).first()
            if winner_b:
                winner_u = User.query.filter_by(username=winner_b.username).first()
                if winner_u:
                    winner_u.balance += 750.0
                    vault.vault_balance -= 750.0
                    db.session.add(FinancialLog(action_type='جائزة الرقم الحنون', admin_name='admin1', target_user=winner_u.username, amount=750.0, log_time=get_local_time()))
            db.session.commit()
            return jsonify({"success": True, "msg": f"Winner: #{winning_num}"})
    bookings = {b.number: b.username for b in GoldenNumberBooking.query.all()}
    return render_template_string(GAME_GOLDEN_PAGE, t=t, lang_key=lang_key, lang_bar=get_lang_bar(), username=username, balance=user.balance, bookings=bookings)

@app.route('/game_numbers_empire', methods=['GET', 'POST'])
def game_numbers_empire():
    if 'username' not in session: return redirect(url_for('login'))
    username = session['username']
    user = User.query.filter_by(username=username).first()
    vault = SystemVault.query.get(1)
    t = get_t()
    lang_key = session.get('lang', 'ar')
    if request.method == 'POST':
        action_type = request.form.get('action_type')
        if action_type == 'book':
            box_num = int(request.form.get('box_number', 0))
            if user.balance >= 500.0 and not NumbersEmpireBooking.query.filter_by(number=box_num).first():
                user.balance -= 500.0
                vault.vault_balance += 500.0
                db.session.add(FinancialLog(action_type='مبيع رهان إمبراطورية الأرقام', admin_name='system', target_user=username, amount=500.0, log_time=get_local_time()))
                db.session.add(NumbersEmpireBooking(username=username, number=box_num, booking_date=get_local_time()))
                db.session.commit()
                return jsonify({"success": True, "msg": f"تم حجز المربع #{box_num}"})
        elif action_type == 'cancel':
            box_num = int(request.form.get('box_number', 0))
            b = NumbersEmpireBooking.query.filter_by(number=box_num, username=username).first()
            if b:
                db.session.delete(b)
                user.balance += 500.0
                vault.vault_balance -= 500.0
                db.session.commit()
                return jsonify({"success": True, "msg": "تم التراجع واسترداد 500 USDD"})
    bookings = {b.number: b.username for b in NumbersEmpireBooking.query.all()}
    return render_template_string(GAME_NUMBERS_EMPIRE_PAGE, t=t, lang_key=lang_key, lang_bar=get_lang_bar(), username=username, balance=user.balance, bookings=bookings)

@app.route('/game_number_wheel', methods=['GET', 'POST'])
def game_number_wheel():
    if 'username' not in session: return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    vault = SystemVault.query.get(1)
    t = get_t()
    lang_key = session.get('lang', 'ar')
    if request.method == 'POST':
        data = request.get_json(silent=True) or request.form
        nums = data.get('selected_numbers', [])
        if isinstance(nums, str): nums = json.loads(nums)
        nums = [int(n) for n in nums]
        cost = float(len(nums) * 2.0)
        if nums and user.balance >= cost:
            user.balance -= cost
            vault.vault_balance += cost
            winning_num = random.choice(nums) if random.random() < 0.4 else random.randint(1, 20)
            if winning_num in nums:
                user.balance += 20.0
                vault.vault_balance -= 20.0
                msg = f"مبروك ربحت 20 USDD (الرقم #{winning_num})"
            else:
                msg = f"توقفت العجلة عند #{winning_num}"
            db.session.commit()
            return jsonify({"success": True, "balance": user.balance, "msg": msg})
    return render_template_string(GAME_NUMBER_WHEEL_PAGE, t=t, lang_key=lang_key, lang_bar=get_lang_bar(), balance=user.balance)

@app.route('/game_reveal_and_win', methods=['GET', 'POST'])
def game_reveal_and_win():
    if 'username' not in session: return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    vault = SystemVault.query.get(1)
    t = get_t()
    lang_key = session.get('lang', 'ar')
    if request.method == 'POST':
        if user.balance >= 1.0:
            user.balance -= 1.0
            vault.vault_balance += 1.0
            user.balance += 0.50
            vault.vault_balance -= 0.50
            db.session.commit()
            return jsonify({"success": True, "balance": user.balance, "msg": "مبروك فزت بـ 0.50 USDD"})
        else:
            return jsonify({"success": False, "msg": "رصيد غير كافي!"})
    return render_template_string(GAME_REVEAL_AND_WIN_PAGE, t=t, lang_key=lang_key, lang_bar=get_lang_bar(), balance=user.balance)

@app.route('/game_roulette', methods=['GET', 'POST'])
def game_roulette():
    if 'username' not in session: return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    t = get_t()
    lang_key = session.get('lang', 'ar')
    if request.method == 'POST':
        return jsonify({"success": True, "msg": "تم السحب", "balance": user.balance})
    return render_template_string(GAME_ROULETTE_GLOBAL_PAGE, t=t, lang_key=lang_key, lang_bar=get_lang_bar(), balance=user.balance)

@app.route('/game_20_numbers', methods=['GET', 'POST'])
def game_20_numbers():
    if 'username' not in session: return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    vault = SystemVault.query.get(1)
    t = get_t()
    lang_key = session.get('lang', 'ar')
    if request.method == 'POST':
        data = request.get_json(silent=True) or request.form
        nums = data.get('selected_numbers', [])
        if isinstance(nums, str): nums = json.loads(nums)
        nums = [int(n) for n in nums]
        cost = float(len(nums) * 5.0)
        if nums and user.balance >= cost:
            user.balance -= cost
            vault.vault_balance += cost
            winning_num = random.choice(nums) if random.random() < 0.4 else random.randint(1, 20)
            if winning_num in nums:
                user.balance += 70.0
                vault.vault_balance -= 70.0
                msg = f"مبروك 70 USDD (الرقم #{winning_num})"
            else:
                msg = f"الرقم الفائز #{winning_num}"
            db.session.commit()
            return jsonify({"success": True, "balance": user.balance, "msg": msg})
    return render_template_string(GAME_20_NUMBERS_PAGE, t=t, lang_key=lang_key, lang_bar=get_lang_bar(), balance=user.balance)

# --- مسارات الإدارة (الزبائن والمحاسبة وتوليد الكودات) ---

@app.route('/admin_customers', methods=['GET', 'POST'])
def admin_customers():
    if 'username' not in session or session.get('username') != 'admin1': return redirect(url_for('dashboard'))
    t = get_t()
    lang_key = session.get('lang', 'ar')
    msg = None
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'create_player':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            balance = float(request.form.get('balance', 0.0))
            owner_name = request.form.get('owner_name', 'غير محدد').strip()
            if username and password:
                if not User.query.filter_by(username=username).first():
                    new_user = User(
                        username=username,
                        password=password,
                        balance=balance,
                        role='user',
                        created_by=session['username'],
                        owner_name=owner_name
                    )
                    db.session.add(new_user)
                    db.session.add(FinancialLog(action_type='إنشاء حساب لاعب جديد', admin_name=session['username'], target_user=username, amount=balance, log_time=get_local_time()))
                    db.session.commit()
                    msg = f"تم إنشاء حساب اللاعب {username} بنجاح!"
                else:
                    msg = "اسم المستخدم موجود مسبقاً!"
            else:
                msg = "يرجى ملء كافة الحقول الإجبارية!"
    users_list = User.query.all()
    return render_template_string(ADMIN_CUSTOMERS_PAGE, t=t, lang_key=lang_key, lang_bar=get_lang_bar(), users_list=users_list, msg=msg)

@app.route('/admin_accounting', methods=['GET', 'POST'])
def admin_accounting():
    if 'username' not in session or session.get('username') != 'admin1': return redirect(url_for('dashboard'))
    vault = SystemVault.query.get(1)
    t = get_t()
    lang_key = session.get('lang', 'ar')
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
        elif action == 'generate_card':
            amount = float(request.form.get('card_amount', 100))
            if amount in [100.0, 200.0, 300.0, 500.0, 1000.0]:
                code_str = 'EMP-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8)) + f'-{int(amount)}'
                new_card = RechargeCard(code=code_str, amount=amount, is_used=False, created_at=get_local_time())
                db.session.add(new_card)
                db.session.add(FinancialLog(action_type=f'توليد كود شحن فئة {int(amount)}', admin_name='admin1', target_user='system', amount=amount, log_time=get_local_time()))
                db.session.commit()
                msg = f"تم توليد كود شحن بقيمة {int(amount)} بنجاح: {code_str}"

    logs = FinancialLog.query.order_by(FinancialLog.id.desc()).all()
    cards = RechargeCard.query.order_by(RechargeCard.id.desc()).all()
    
    tp_sold = db.session.query(db.func.sum(FinancialLog.amount)).filter(FinancialLog.action_type.in_(['بيع عملات للزبون', 'شحن عبر بطاقة كود'])).scalar() or 0.0
    tg_bets = db.session.query(db.func.sum(FinancialLog.amount)).filter(FinancialLog.action_type.like('%مبيع رهان%')).scalar() or 0.0
    tpayouts = db.session.query(db.func.sum(FinancialLog.amount)).filter(FinancialLog.action_type.like('%جائزة%')).scalar() or 0.0
    net = tg_bets - tpayouts

    return render_template_string(ADMIN_ACCOUNTING_TEMPLATE, t=t, lang_key=lang_key, lang_bar=get_lang_bar(), vault_balance=vault.vault_balance if vault else 0.0, logs=logs, cards=cards, total_points_sold=tp_sold, total_game_bets=tg_bets, total_payouts=tpayouts, net_game_result=net, users_list=User.query.all(), msg=msg)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
