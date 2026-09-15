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
    role = db.Column(db.String(20), nullable=False)
    created_by = db.Column(db.String(80), nullable=False)
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

class RouletteGlobalState(db.Model):
    __tablename__ = 'roulette_global_state'
    id = db.Column(db.Integer, primary_key=True)
    total_global_spins = db.Column(db.Integer, default=0)

class RevealAndWinGlobalState(db.Model):
    __tablename__ = 'reveal_and_win_global'
    id = db.Column(db.Integer, primary_key=True)
    total_spins = db.Column(db.Integer, default=0)

class Game20NumbersBooking(db.Model):
    __tablename__ = 'game_20_numbers_bookings'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80))
    number = db.Column(db.Integer)

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
    if not RouletteGlobalState.query.get(1):
        db.session.add(RouletteGlobalState(id=1, total_global_spins=0))
    if not RevealAndWinGlobalState.query.get(1):
        db.session.add(RevealAndWinGlobalState(id=1, total_spins=0))
    db.session.commit()

# --- قاموس الترجمات الشامل للغات الست ---
TRANSLATIONS = {
    'ar': {
        'dir': 'rtl', 'title': 'امبراطورية الأرقام', 'subtitle': 'منصة الألعاب التفاعلية الفائقة 12D',
        'login': 'دخول للبرنامج', 'username': 'اسم المستخدم', 'password': 'كلمة المرور', 'balance': 'الرصيد',
        'recharge': 'شحن رصيد', 'withdraw': 'سحب رصيد', 'change_pass': 'تغيير الباسورد', 'logout': 'خروج',
        'dashboard': 'لوحة التحكم', 'back_dash': '🏠 الرئيسية',
        'withdraw_warning': '⚠️ تنبيه: يتم خصم 10% رسوم تحويل من رصيدك.',
        'wish_withdraw': 'سحب عبر Wish Money', 'visa_withdraw': 'سحب عبر Visa مسبقة الدفع', 'usdt_withdraw': 'قبض عبر USDT',
        'success_msg': 'سنقوم بمراجعة طلبك في غضون دقيقة إلى 120 دقيقة وسيتم التحويل فوراً. أهلاً بكم!',
        'game1': 'الرقم الحنون', 'game2': 'روليت الحظ', 'game3': 'إمبراطورية الأرقام',
        'game4': 'عجلة الأرقام', 'game5': 'اكشف واربح', 'game6': 'لعبة 70 USDD',
        'cost': 'التكلفة', 'prize': 'الجائزة', 'book': 'حجز', 'cancel': 'تراجع', 'booked': 'محجوز',
        'spin': 'تدوير العجلة', 'reveal': 'اكشف الصناديق', 'draw_now': 'اسحب الآن (للآدمن)'
    },
    'en': {
        'dir': 'ltr', 'title': 'Empire of Numbers', 'subtitle': 'The Ultimate 12D Interactive Platform',
        'login': 'Login', 'username': 'Username', 'password': 'Password', 'balance': 'Balance',
        'recharge': 'Recharge Balance', 'withdraw': 'Withdraw Balance', 'change_pass': 'Change Password', 'logout': 'Logout',
        'dashboard': 'Dashboard', 'back_dash': '🏠 Home',
        'withdraw_warning': '⚠️ Notice: A 10% transfer fee will be deducted from your balance.',
        'wish_withdraw': 'Withdraw via Wish Money', 'visa_withdraw': 'Withdraw via Prepaid Visa', 'usdt_withdraw': 'Receive via USDT',
        'success_msg': 'We will review your request within 1 to 120 minutes and transfer immediately. Welcome!',
        'game1': 'Golden Number', 'game2': 'Lucky Roulette', 'game3': 'Numbers Empire',
        'game4': 'Wheel of Numbers', 'game5': 'Reveal & Win', 'game6': '70 USDD Game',
        'cost': 'Cost', 'prize': 'Prize', 'book': 'Book', 'cancel': 'Cancel', 'booked': 'Booked',
        'spin': 'Spin Wheel', 'reveal': 'Reveal Boxes', 'draw_now': 'Draw Now (Admin)'
    },
    'fr': {
        'dir': 'ltr', 'title': 'Empire des Nombres', 'subtitle': 'Plateforme Interactive 12D',
        'login': 'Connexion', 'username': "Nom d'utilisateur", 'password': 'Mot de passe', 'balance': 'Solde',
        'recharge': 'Recharger', 'withdraw': 'Retirer', 'change_pass': 'Changer le mot de passe', 'logout': 'Déconnexion',
        'dashboard': 'Tableau de bord', 'back_dash': '🏠 Accueil',
        'withdraw_warning': '⚠️ Avis : Frais de transfert 10%.',
        'wish_withdraw': 'Retrait Wish Money', 'visa_withdraw': 'Retrait Visa', 'usdt_withdraw': 'Recevoir USDT',
        'success_msg': 'Nous examinerons votre demande en 1 à 120 minutes.',
        'game1': 'Numéro d’Or', 'game2': 'Roulette de la Chance', 'game3': 'Empire des Nombres',
        'game4': 'Roue des Nombres', 'game5': 'Révéler & Gagner', 'game6': 'Jeu 70 USDD',
        'cost': 'Coût', 'prize': 'Prix', 'book': 'Réserver', 'cancel': 'Annuler', 'booked': 'Réservé',
        'spin': 'Tourner la roue', 'reveal': 'Révéler les boîtes', 'draw_now': 'Tirage (Admin)'
    },
    'fa': {
        'dir': 'rtl', 'title': 'امپراتوری اعداد', 'subtitle': 'پلتفرم فوق پیشرفته 12D',
        'login': 'ورود به برنامه', 'username': 'نام کاربری', 'password': 'رمز عبور', 'balance': 'موجودی',
        'recharge': 'شارژ حساب', 'withdraw': 'برداشت وجه', 'change_pass': 'تغییر رمز عبور', 'logout': 'خروج',
        'dashboard': 'داشبورد', 'back_dash': '🏠 صفحه اصلی',
        'withdraw_warning': '⚠️ توجه: ۱۰٪ کارمزد انتقال.',
        'wish_withdraw': 'برداشت Wish Money', 'visa_withdraw': 'برداشت ویزا کارت', 'usdt_withdraw': 'دریافت USDT',
        'success_msg': 'درخواست شما بررسی و واریز خواهد شد.',
        'game1': 'شماره طلایی', 'game2': 'رولت شانس', 'game3': 'امپراتوری اعداد',
        'game4': 'گردونه اعداد', 'game5': 'بگشای و ببر', 'game6': 'بازی 70 USDD',
        'cost': 'هزینه', 'prize': 'جایزه', 'book': 'رزرو', 'cancel': 'لغو', 'booked': 'رزرو شده',
        'spin': 'چرخش گردونه', 'reveal': 'باز کردن جعبه‌ها', 'draw_now': 'قرعه‌کشی (مدیر)'
    },
    'es': {
        'dir': 'ltr', 'title': 'Imperio de los Números', 'subtitle': 'Plataforma Interactiva 12D',
        'login': 'Iniciar Sesión', 'username': 'Usuario', 'password': 'Contraseña', 'balance': 'Saldo',
        'recharge': 'Recargar Saldo', 'withdraw': 'Retirar Saldo', 'change_pass': 'Cambiar Contraseña', 'logout': 'Cerrار Sesión',
        'dashboard': 'Panel Principal', 'back_dash': '🏠 Inicio',
        'withdraw_warning': '⚠️ Aviso: Comisión del 10%.',
        'wish_withdraw': 'Retirar Wish Money', 'visa_withdraw': 'Retirar Visa', 'usdt_withdraw': 'Recibir USDT',
        'success_msg': 'Revisaremos su solicitud en 1 a 120 minutos.',
        'game1': 'Número de Oro', 'game2': 'Ruleta de la Suerte', 'game3': 'Imperio de Números',
        'game4': 'Rueda de Números', 'game5': 'Descubre y Gana', 'game6': 'Juego 70 USDD',
        'cost': 'Costo', 'prize': 'Premio', 'book': 'Reservar', 'cancel': 'Cancelar', 'booked': 'Reservado',
        'spin': 'Girar Ruleta', 'reveal': 'Destapar Cajas', 'draw_now': 'Sorteo Ahora (Admin)'
    },
    'de': {
        'dir': 'ltr', 'title': 'Imperium der Zahlen', 'subtitle': 'Die 12D Gaming-Plattform',
        'login': 'Anmelden', 'username': 'Benutzername', 'password': 'Passwort', 'balance': 'Guthaben',
        'recharge': 'Guthaben aufladen', 'withdraw': 'Guthaben abheben', 'change_pass': 'Passwort ändern', 'logout': 'Abmelden',
        'dashboard': 'Dashboard', 'back_dash': '🏠 Startseite',
        'withdraw_warning': '⚠️ Hinweis: 10% Gebühr.',
        'wish_withdraw': 'Wish Money', 'visa_withdraw': 'Prepaid Visa', 'usdt_withdraw': 'USDT',
        'success_msg': 'Wir prüfen Ihre Anfrage in 1 bis 120 Minuten.',
        'game1': 'Goldene Nummer', 'game2': 'Glücksroulette', 'game3': 'Zahlenimperium',
        'game4': 'Zahlenrad', 'game5': 'Aufdecken & Gewinnen', 'game6': '70 USDD Spiel',
        'cost': 'Kosten', 'prize': 'Gewinn', 'book': 'Buchen', 'cancel': 'Abbrechen', 'booked': 'Gebucht',
        'spin': 'Rad drehen', 'reveal': 'Boxen aufdecken', 'draw_now': 'Ziehung (Admin)'
    }
}

def get_t():
    lang = session.get('lang', 'ar')
    return TRANSLATIONS.get(lang, TRANSLATIONS['ar'])

LANG_BAR = """
<div style="padding: 12px 25px; background: rgba(18, 18, 25, 0.95); backdrop-filter: blur(15px); display: flex; gap: 15px; justify-content: flex-end; border-bottom: 1px solid rgba(255,215,0,0.2); box-shadow: 0 4px 20px rgba(0,0,0,0.5);">
    <a href="/set_lang/ar" style="color:#ffd700; text-decoration:none; font-weight:bold; font-size:14px;">العربية</a> |
    <a href="/set_lang/en" style="color:#38bdf8; text-decoration:none; font-weight:bold; font-size:14px;">English</a> |
    <a href="/set_lang/fr" style="color:#f472b6; text-decoration:none; font-weight:bold; font-size:14px;">Français</a> |
    <a href="/set_lang/fa" style="color:#34d399; text-decoration:none; font-weight:bold; font-size:14px;">فارسی</a> |
    <a href="/set_lang/es" style="color:#fbbf24; text-decoration:none; font-weight:bold; font-size:14px;">Español</a> |
    <a href="/set_lang/de" style="color:#a78bfa; text-decoration:none; font-weight:bold; font-size:14px;">Deutsch</a>
</div>
"""

# --- تعريف جميع قوالب HTML في الأعلى تماماً قبل أي مسارات فلاسك ---

LOGIN_PAGE = LANG_BAR + """
<!DOCTYPE html>
<html lang="{{ t.dir }}" dir="{{ t.dir }}">
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

DASHBOARD_PAGE = LANG_BAR + """
<!DOCTYPE html>
<html lang="{{ t.dir }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ t.dashboard }} - 12D</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: radial-gradient(circle at center, #151928 0%, #070a12 100%); color: #fff; margin: 0; padding: 20px; min-height: 100vh; }
        .header { display: flex; justify-content: space-between; align-items: center; background: rgba(20, 24, 38, 0.9); padding: 18px 30px; border-radius: 18px; border-bottom: 3px solid #ffd700; flex-wrap: wrap; gap: 15px; }
        .financial-bar { display: flex; justify-content: space-between; max-width: 950px; margin: 30px auto; gap: 20px; }
        .fin-card { flex: 1; background: rgba(24,34,50,0.9); border: 2px solid rgba(56,189,248,0.5); padding: 22px; border-radius: 20px; text-align: center; }
        .fin-card button { background: #38bdf8; color: #070a12; padding: 14px 22px; font-weight: 900; border: none; border-radius: 12px; cursor: pointer; margin-top: 12px; width: 100%; font-size: 16px; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(5, 7, 12, 0.9); justify-content: center; align-items: center; z-index: 1000; }
        .modal-content { background: rgba(25, 30, 48, 0.95); padding: 35px; border-radius: 22px; border: 3px solid #ffd700; width: 440px; text-align: center; position: relative; }
        .icons-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 30px; max-width: 1000px; margin: 40px auto; }
        @media (max-width: 900px) { .icons-grid { grid-template-columns: repeat(2, 1fr); } }
        .icon-card { background: rgba(25,30,48,0.95); border: 3px solid rgba(184,134,11,0.6); border-radius: 28px; padding: 35px 20px; text-align: center; text-decoration: none; box-shadow: 0 20px 45px rgba(0,0,0,0.9); transition: 0.3s; }
        .icon-card:hover { border-color: #ffd700; transform: translateY(-8px); }
        .icon-logo { font-size: 75px; margin-bottom: 15px; }
        .icon-title { color: #ffd700; font-size: 21px; font-weight: 900; }
    </style>
</head>
<body>
    <div class="header">
        <div style="display:flex; gap:18px; align-items:center; flex-wrap:wrap;">
            <h2 style="color:#ffd700; margin:0;">👑 {{ t.title }} (12D)</h2>
            <div style="background:rgba(15,20,32,0.9); padding:8px 15px; border-radius:10px;">👤 <b>{{ username }}</b></div>
            <div style="background:rgba(6,95,70,0.8); color:#34d399; padding:8px 18px; border-radius:10px; font-weight:900;">{{ t.balance }}: <span id="liveBalance">{{ balance }}</span> USDD</div>
        </div>
        <div style="display:flex; gap:12px; flex-wrap:wrap;">
            <a href="/change_password" style="background:#8b5cf6; color:#fff; padding:10px 16px; text-decoration:none; border-radius:10px; font-weight:900;">{{ t.change_pass }}</a>
            {% if username == 'admin1' %}
                <a href="/admin_customers" style="background:#ffd700; color:#000; padding:10px 16px; text-decoration:none; border-radius:10px; font-weight:900;">👥 الزبائن</a>
                <a href="/admin_games" style="background:#ffd700; color:#000; padding:10px 16px; text-decoration:none; border-radius:10px; font-weight:900;">🎮 الألعاب</a>
                <a href="/admin_accounting" style="background:#ffd700; color:#000; padding:10px 16px; text-decoration:none; border-radius:10px; font-weight:900;">📊 الخزنة</a>
            {% endif %}
            <a href="/logout" style="background:#ef4444; color:#fff; padding:10px 16px; text-decoration:none; border-radius:10px; font-weight:900;">{{ t.logout }}</a>
        </div>
    </div>

    {% if msg %}<div style="background:rgba(6,95,70,0.9); color:#34d399; padding:18px; border-radius:14px; max-width:950px; margin:20px auto; text-align:center; font-weight:900;">{{ msg }}</div>{% endif %}

    <div class="financial-bar">
        <div class="fin-card">
            <h3 style="color:#38bdf8; margin:0; font-size:20px;">{{ t.recharge }}</h3>
            <button onclick="document.getElementById('rechargeM').style.display='flex'">{{ t.recharge }}</button>
        </div>
        <div class="fin-card" style="border-color:rgba(245,158,11,0.5);">
            <h3 style="color:#f59e0b; margin:0; font-size:20px;">{{ t.withdraw }}</h3>
            <button onclick="document.getElementById('withdrawM').style.display='flex'" style="background:linear-gradient(135deg,#f59e0b,#d97706); color:#070a12;">{{ t.withdraw }}</button>
        </div>
    </div>

    <div id="rechargeM" class="modal">
        <div class="modal-content">
            <span onclick="this.parentElement.parentElement.style.display='none'" style="position:absolute; top:12px; left:18px; cursor:pointer; font-size:26px; color:#aaa;">&times;</span>
            <h3 style="color:#38bdf8; margin-top:0; font-size:24px;">{{ t.recharge }}</h3>
            <form method="POST">
                <input type="hidden" name="action" value="redeem_card">
                <input type="text" name="card_code" placeholder="Card Code (EMP-..)" required style="width:100%; padding:14px; background:rgba(10,13,22,0.9); color:#fff; border:1px solid rgba(255,255,255,0.2); border-radius:12px; box-sizing:border-box; margin-bottom:15px; font-size:16px;">
                <button type="submit" style="width:100%; background:linear-gradient(135deg,#ffd700,#b8860b); color:#000; padding:14px; border:none; border-radius:12px; font-weight:900; cursor:pointer; font-size:18px;">تفعيل الكود</button>
            </form>
        </div>
    </div>

    <div id="withdrawM" class="modal">
        <div class="modal-content" style="width: 480px;">
            <span onclick="this.parentElement.parentElement.style.display='none'" style="position:absolute; top:12px; left:18px; cursor:pointer; font-size:26px; color:#aaa;">&times;</span>
            <h3 style="color:#f59e0b; margin-top:0; font-size:24px;">{{ t.withdraw }}</h3>
            <p style="color:#ef4444; font-size:13px; font-weight:900; background:rgba(239,68,68,0.15); padding:12px; border-radius:10px;">{{ t.withdraw_warning }}</p>
            <form method="POST" style="display:flex; flex-direction:column; gap:15px; margin-top:20px;">
                <button type="submit" name="action" value="withdraw_wish" style="background:#25d366; color:#fff; padding:14px; border:none; border-radius:12px; font-weight:900; cursor:pointer;">{{ t.wish_withdraw }}</button>
                <button type="submit" name="action" value="withdraw_visa" style="background:#3b82f6; color:#fff; padding:14px; border:none; border-radius:12px; font-weight:900; cursor:pointer;">{{ t.visa_withdraw }}</button>
            </form>
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

CHANGE_PASSWORD_PAGE = LANG_BAR + """
<!DOCTYPE html>
<html lang="{{ t.dir }}" dir="{{ t.dir }}">
<head><meta charset="UTF-8"><title>{{ t.change_pass }}</title></head>
<body style="font-family:'Segoe UI', Tahoma, sans-serif; background:radial-gradient(circle at center, #1a1c29 0%, #0b0f19 100%); color:#fff; display:flex; justify-content:center; align-items:center; height:85vh; margin:0;">
    <div style="background:rgba(20,24,38,0.9); padding:45px; border-radius:25px; border:2px solid #8b5cf6; width:380px; text-align:center;">
        <h3 style="color:#ffd700;">{{ t.change_pass }}</h3>
        {% if msg %}<p style="color:#34d399; font-weight:bold;">{{ msg }}</p>{% endif %}
        <form method="POST">
            <input type="password" name="old_password" placeholder="Old Password" required style="width:100%; padding:14px; margin:10px 0; background:rgba(10,13,22,0.9); color:#fff; border:1px solid #444; border-radius:10px;">
            <input type="password" name="new_password" placeholder="New Password" required style="width:100%; padding:14px; margin:10px 0; background:rgba(10,13,22,0.9); color:#fff; border:1px solid #444; border-radius:10px;">
            <input type="password" name="confirm_password" placeholder="Confirm Password" required style="width:100%; padding:14px; margin:10px 0; background:rgba(10,13,22,0.9); color:#fff; border:1px solid #444; border-radius:10px;">
            <button type="submit" style="width:100%; padding:14px; background:#8b5cf6; color:#fff; border:none; border-radius:10px; font-weight:900; cursor:pointer; margin-top:15px;">Update</button>
        </form>
        <a href="/dashboard" style="color:#38bdf8; display:inline-block; margin-top:20px; text-decoration:none; font-weight:bold;">{{ t.back_dash }}</a>
    </div>
</body>
</html>
"""

GAME_GOLDEN_PAGE = LANG_BAR + """
<!DOCTYPE html>
<html lang="{{ t.dir }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><title>{{ t.game1 }} - 12D</title>
    <style>
        body { font-family:'Segoe UI', Tahoma, sans-serif; background:radial-gradient(circle at center, #151928 0%, #070a12 100%); color:#fff; margin:0; padding:25px; }
        .card-3d { background:linear-gradient(135deg, rgba(31,26,15,0.95), rgba(13,13,13,0.95)); border:4px solid #ffd700; padding:35px; border-radius:30px; max-width:950px; margin:20px auto; box-shadow:0 30px 70px rgba(0,0,0,0.9); }
        .grid { display:grid; grid-template-columns:repeat(10, 1fr); gap:12px; margin-top:25px; }
        @media(max-width: 768px) { .grid { grid-template-columns:repeat(5, 1fr); } }
        .cell { background:linear-gradient(145deg, #7c3aed, #4c1d95); border:3px solid #a78bfa; border-radius:16px; height:80px; display:flex; flex-direction:column; align-items:center; justify-content:center; font-weight:900; cursor:pointer; color:#fff; font-size: 22px; }
        .cell.booked { background: #7f1d1d !important; border-color:#ef4444 !important; cursor:not-allowed; }
        .cell.my { background: #1e3a8a !important; border-color:#3b82f6 !important; }
    </style>
</head>
<body>
    <div style="display:flex; justify-content:space-between; align-items:center; max-width:950px; margin:0 auto; background:rgba(20,24,38,0.9); padding:15px 25px; border-radius:15px;">
        <h2 style="color:#ffd700; margin:0;">🏆 {{ t.game1 }}</h2>
        <a href="/dashboard" style="background:#3b82f6; color:#fff; padding:10px 18px; text-decoration:none; border-radius:10px; font-weight:900;">{{ t.back_dash }}</a>
        <div><b>{{ t.balance }}: <span id="liveBalance">{{ balance }}</span> USDD</b></div>
    </div>
    <div class="card-3d">
        <p style="text-align:center; color:#ffd700; font-size:20px; font-weight:900;">التكلفة: 20 USDD | الجائزة: 750 USDD</p>
        {% if msg %}<div style="background:rgba(6,95,70,0.9); color:#34d399; padding:15px; border-radius:12px; margin:15px 0; text-align:center; font-weight:900;">{{ msg }}</div>{% endif %}
        <div class="grid" id="numbersGrid">
            {% for i in range(1, 51) %}
                {% if i in bookings %}
                    {% if bookings[i] == username %}
                        <button type="button" onclick="handleAction('cancel', {{ i }})" class="cell my">{{ i }}<br><span style="font-size:12px;">تراجع</span></button>
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
                <button type="button" onclick="handleAction('admin_draw', 0)" style="background:#22c55e; color:#fff; font-weight:900; padding:18px 45px; border:none; border-radius:16px; cursor:pointer; font-size:20px;">⚡ اسحب الآن</button>
            </div>
        {% endif %}
    </div>
    <script>
        function handleAction(type, num) {
            let fd = new FormData();
            fd.append('action_type', type);
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

GAME_NUMBERS_EMPIRE_PAGE = LANG_BAR + """
<!DOCTYPE html>
<html lang="{{ t.dir }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ t.game3 }} - 12D</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: radial-gradient(circle at center, #151928 0%, #070a12 100%); color: #f8fafc; margin: 0; padding: 25px; text-align: center; }
        .empire-card { background: linear-gradient(135deg, rgba(31,26,15,0.95), rgba(13,13,13,0.95)); border: 4px solid #ffd700; padding: 40px; border-radius: 30px; max-width: 850px; margin: 20px auto; box-shadow: 0 30px 70px rgba(0,0,0,0.9); }
        .boxes-grid { display: flex; justify-content: center; gap: 20px; margin: 30px 0; flex-wrap: wrap; }
        .box-item { width: 120px; height: 130px; background: linear-gradient(145deg, #7c3aed, #4c1d95); border: 3px solid #ffd700; border-radius: 20px; color: #fff; font-size: 22px; font-weight: 900; cursor: pointer; display: flex; flex-direction: column; align-items: center; justify-content: center; transition: 0.3s; box-shadow: 0 10px 25px rgba(0,0,0,0.6); }
        .box-item.booked { background: #7f1d1d !important; border-color: #ef4444 !important; }
        .box-item.my { background: #1e3a8a !important; border-color: #3b82f6 !important; }
        .slot-box { font-size: 45px; font-weight: 900; color: #ffd700; background: #000; padding: 12px; border-radius: 14px; border: 3px solid #b8860b; display: inline-block; min-width: 130px; letter-spacing: 5px; }
    </style>
</head>
<body>
    <div style="display:flex; justify-content:space-between; align-items:center; max-width:850px; margin:0 auto; background:rgba(20,24,38,0.9); padding:15px 25px; border-radius:15px;">
        <h2 style="color:#ffd700; margin:0;">🏛️ {{ t.game3 }}</h2>
        <a href="/dashboard" style="background:#3b82f6; color:#fff; padding:10px 18px; text-decoration:none; border-radius:10px; font-weight:900;">{{ t.back_dash }}</a>
        <div><b>{{ t.balance }}: {{ balance }} USDD</b></div>
    </div>
    <div class="empire-card">
        <div style="background: rgba(30,58,138,0.9); border: 2px solid #38bdf8; padding: 15px; border-radius: 14px; margin-bottom: 20px;">
            <p style="margin: 0; font-size: 16px; font-weight: bold;">⏰ السحب على هذه اللعبة كل يوم الساعة 23 بتوقيت مدينة بيروت.</p>
        </div>
        <div style="background: #000; border: 3px solid #38bdf8; padding: 20px; border-radius: 20px; margin-bottom: 25px;">
            <div id="empireSlot" class="slot-box">--</div>
            <div id="empireAnnouncement" style="font-size: 18px; color: #34d399; margin-top: 12px; font-weight: 900;">في انتظار السحب الفاخر...</div>
        </div>
        <p style="color:#ffd700; font-size:20px; font-weight:900;">سعر الحجز: 500 USDD | الجائزة: 2000 USDD</p>
        {% if msg %}<div style="background:#065f46; color:#34d399; padding:15px; border-radius:12px; margin:15px 0; font-weight:900;">{{ msg }}</div>{% endif %}
        <div class="boxes-grid">
            {% for i in range(1, 6) %}
                {% if i in bookings %}
                    {% if bookings[i] == username %}
                        <button type="button" onclick="handleEmpireAction('cancel', {{ i }})" class="box-item my"><span>👑</span><span>رقم {{ i }}</span><span style="font-size:11px;">تراجع</span></button>
                    {% else %}
                        <div class="box-item booked"><span>👑</span><span>رقم {{ i }}</span><span style="font-size:11px;">{{ bookings[i] }}</span></div>
                    {% endif %}
                {% else %}
                    <button type="button" onclick="handleEmpireAction('book', {{ i }})" class="box-item"><span>👑</span><span>رقم {{ i }}</span><span style="font-size:11px;">500$</span></button>
                {% endif %}
            {% endfor %}
        </div>
        {% if username == 'admin1' %}
            <div style="background: rgba(15,23,42,0.9); border: 2px dashed #ffd700; padding: 20px; border-radius: 18px; margin-top: 30px;">
                <h4 style="color: #ffd700; margin-top: 0;">لوحة تحكم صاحب اللعبة (خاص بالآدمن)</h4>
                <input type="number" id="forcedWinningNum" placeholder="الرقم الفائز (1-5)" min="1" max="5" value="{{ forced_val if forced_val != 0 else '' }}" style="padding: 10px; width: 180px; background: #000; color: #fff; border: 1px solid #ffd700; border-radius: 8px; text-align: center;">
                <button type="button" onclick="executeEmpireAdminDraw()" style="background: #22c55e; color: #fff; padding: 12px 25px; font-weight: 900; border: none; border-radius: 8px; cursor: pointer; margin-right: 10px;">ابدأ السحب ⚡</button>
            </div>
        {% endif %}
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
        function executeEmpireAdminDraw() {
            let val = document.getElementById('forcedWinningNum').value;
            let fd = new FormData();
            fd.append('forced_winning_number', val);
            fetch('/game_numbers_empire_admin_set', {method: 'POST', body: fd}).then(res => res.json()).then(d => {
                let fd2 = new FormData();
                fd2.append('action_type', 'admin_draw');
                fetch('/game_numbers_empire', {method: 'POST', body: fd2}).then(res => res.json()).then(d2 => {
                    if(d2.msg) { alert(d2.msg); location.reload(); }
                });
            });
        }
    </script>
</body>
</html>
"""

GAME_NUMBER_WHEEL_PAGE = LANG_BAR + """
<!DOCTYPE html>
<html lang="{{ t.dir }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ t.game4 }} - 12D</title>
    <style>
        body { font-family:'Segoe UI', Tahoma, sans-serif; background: radial-gradient(circle at center, #151928 0%, #070a12 100%); color:#fff; text-align:center; padding:25px; }
        .wheel-container { background: linear-gradient(135deg, rgba(31,26,15,0.95), rgba(13,13,13,0.95)); border: 5px solid #ffd700; padding: 40px; border-radius: 35px; max-width: 700px; margin: 20px auto; box-shadow: 0 35px 80px rgba(0,0,0,0.9); }
        .wheel-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin: 20px auto; max-width: 500px; }
        .wheel-btn { background: #1f2937; border: 2px solid #ffd700; border-radius: 12px; padding: 15px; font-size: 18px; font-weight: 900; color: #fff; cursor: pointer; }
        .wheel-btn.selected { background: #d97706 !important; color: #000 !important; }
        .lion-box { background: #b45309; border: 2px solid #fff; border-radius: 12px; padding: 15px; font-size: 18px; font-weight: 900; grid-column: span 5; }
    </style>
</head>
<body>
    <div style="display:flex; justify-content:space-between; align-items:center; max-width:700px; margin:0 auto; background:rgba(20,24,38,0.9); padding:15px 25px; border-radius:15px;">
        <h2 style="color:#ffd700; margin:0;">🎡 {{ t.game4 }}</h2>
        <a href="/dashboard" style="background:#3b82f6; color:#fff; padding:10px 18px; text-decoration:none; border-radius:10px;">الرئيسية</a>
        <div><b>{{ t.balance }}: <span id="wheelBal">{{ balance }}</span> USDD</b></div>
    </div>
    <div class="wheel-container">
        <p style="color: #f59e0b; font-weight: bold; font-size: 16px;">🦁 هامش اللعبة: إذا أصبت الأسد تربح 100,000 USDD!</p>
        <div id="wheelSlot" style="font-size: 40px; font-weight: 900; color: #ffd700; background: #000; padding: 15px; border-radius: 12px; border: 2px solid #ffd700; display: inline-block; min-width: 120px; margin: 15px 0;">--</div>
        <div id="wheelMsg" style="font-size: 18px; font-weight: 900; color: #34d399; margin: 10px 0;">اختر حتى 10 أرقام (سعر الحجز 2 USDD، والربح 20 USDD)</div>
        <div class="wheel-grid">
            {% for n in range(1, 21) %}
                <button type="button" id="w_num_{{ n }}" onclick="toggleWheelNum({{ n }})" class="wheel-btn">{{ n }}</button>
            {% endfor %}
            <div class="lion-box">🦁 خانة رأس الأسد الكبرى</div>
        </div>
        <button type="button" onclick="spinWheel()" style="padding: 16px 45px; background: linear-gradient(135deg,#22c55e,#15803d); color: #fff; font-weight: 900; font-size: 20px; border: none; border-radius: 16px; cursor: pointer; margin-top: 20px;">تدوير العجلة 🎡</button>
    </div>
    <script>
        let wheelSelected = [];
        function toggleWheelNum(n) {
            let idx = wheelSelected.indexOf(n);
            if(idx > -1) {
                wheelSelected.splice(idx, 1);
                document.getElementById('w_num_' + n).classList.remove('selected');
            } else {
                if(wheelSelected.length >= 10) { alert("حد أقصى 10 أرقام!"); return; }
                wheelSelected.push(n);
                document.getElementById('w_num_' + n).classList.add('selected');
            }
        }
        function spinWheel() {
            if(wheelSelected.length === 0) { alert("اختر رقماً واحداً على الأقل!"); return; }
            let fd = new FormData();
            fd.append('selected_numbers', JSON.stringify(wheelSelected));
            fetch('/game_number_wheel', {method: 'POST', body: fd}).then(res => res.json()).then(d => {
                if(d.success) {
                    document.getElementById('wheelSlot').innerText = '#' + d.winning_num;
                    document.getElementById('wheelMsg').innerText = d.msg;
                    document.getElementById('wheelBal').innerText = d.balance;
                    wheelSelected.forEach(n => document.getElementById('w_num_' + n).classList.remove('selected'));
                    wheelSelected = [];
                }
            });
        }
    </script>
</body>
</html>
"""

GAME_REVEAL_AND_WIN_PAGE = LANG_BAR + """
<!DOCTYPE html>
<html lang="{{ t.dir }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ t.game5 }} - 12D</title>
    <style>
        body { font-family:'Segoe UI', Tahoma, sans-serif; background: radial-gradient(circle at center, #151928 0%, #070a12 100%); color:#fff; text-align:center; padding:25px; }
        .reveal-container { background: linear-gradient(135deg, rgba(31,31,31,0.95), rgba(17,17,17,0.95)); border: 5px solid #ffd700; padding: 40px; border-radius: 35px; max-width: 700px; margin: 20px auto; box-shadow: 0 35px 80px rgba(0,0,0,0.9); }
        .boxes-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin: 25px auto; max-width: 500px; }
        .box-cell { background: #7c3aed; border: 2px solid #ffd700; border-radius: 12px; height: 75px; font-size: 26px; font-weight: 900; color: #fff; display: flex; align-items: center; justify-content: center; }
    </style>
</head>
<body>
    <div style="display:flex; justify-content:space-between; align-items:center; max-width:700px; margin:0 auto; background:rgba(20,24,38,0.9); padding:15px 25px; border-radius:15px;">
        <h2 style="color:#ffd700; margin:0;">🎟️ {{ t.game5 }}</h2>
        <a href="/dashboard" style="background:#3b82f6; color:#fff; padding:10px 18px; text-decoration:none; border-radius:10px;">الرئيسية</a>
        <div><b>{{ t.balance }}: <span id="revealBal">{{ balance }}</span> USDD</b></div>
    </div>
    <div class="reveal-container">
        <p style="color: #ffd700; font-weight: bold; font-size: 16px;">🦁 طابق وجه الأسد واحصل على 1000 USDD! (تكلفة المحاولة 1 USDD)</p>
        <div id="revealMsg" style="font-size: 18px; font-weight: 900; color: #34d399; margin: 15px 0;">اضغط ابدأ المحاولة لفتح الصناديق الثلاثة</div>
        <div class="boxes-grid">
            {% for i in range(1, 16) %}
                <div class="box-cell" id="b_{{ i }}">📦</div>
            {% endfor %}
        </div>
        <button type="button" onclick="playReveal()" style="padding: 16px 45px; background: linear-gradient(135deg,#ffd700,#ff8c00); color: #000; font-weight: 900; font-size: 20px; border: none; border-radius: 16px; cursor: pointer; margin-top: 20px;">ابدأ المحاولة (1 USDD) 🎟️</button>
    </div>
    <script>
        function playReveal() {
            fetch('/game_reveal_and_win', {method: 'POST'}).then(res => res.json()).then(d => {
                if(d.success) {
                    document.getElementById('revealBal').innerText = d.balance;
                    document.getElementById('revealMsg').innerText = d.msg;
                    for(let i=1; i<=3; i++) {
                        document.getElementById('b_' + i).innerText = d.revealed[i-1];
                    }
                } else { alert(d.msg); }
            });
        }
    </script>
</body>
</html>
"""

GAME_20_NUMBERS_PAGE = LANG_BAR + """
<!DOCTYPE html>
<html lang="{{ t.dir }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لعبة 70 USDD - 12D</title>
    <style>
        body { font-family:'Segoe UI', Tahoma, sans-serif; background: radial-gradient(circle at center, #151928 0%, #070a12 100%); color:#fff; text-align:center; padding:25px; }
        .game20-container { background: linear-gradient(135deg, rgba(17,13,6,0.95), rgba(0,0,0,0.95)); border: 5px solid #b8860b; padding: 40px; border-radius: 35px; max-width: 750px; margin: 20px auto; box-shadow: 0 35px 80px rgba(0,0,0,0.9); }
        .grid-20 { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin: 25px auto; max-width: 550px; }
        .num-box-20 { background: #1f2937; border: 2px solid #ffd700; border-radius: 12px; height: 65px; font-size: 20px; font-weight: 900; color: #fff; cursor: pointer; display: flex; align-items: center; justify-content: center; }
        .num-box-20.selected { background: #d97706 !important; color: #000 !important; }
        .num-box-20.winning-glow { background: #fbbf24 !important; border: 3px solid #fff !important; box-shadow: 0 0 30px #ffd700; color: #000 !important; transform: scale(1.1); }
    </style>
</head>
<body>
    <div style="display:flex; justify-content:space-between; align-items:center; max-width:750px; margin:0 auto; background:rgba(20,24,38,0.9); padding:15px 25px; border-radius:15px;">
        <h2 style="color:#ffd700; margin:0;">💎 لعبة 70 USDD</h2>
        <a href="/dashboard" style="background:#3b82f6; color:#fff; padding:10px 18px; text-decoration:none; border-radius:10px;">الرئيسية</a>
        <div><b>{{ t.balance }}: <span id="bal20">{{ balance }}</span> USDD</b></div>
    </div>
    <div class="game20-container">
        <div id="slot20" style="font-size: 45px; font-weight: 900; color: #ffd700; background: #000; padding: 15px; border-radius: 14px; border: 3px solid #b8860b; display: inline-block; min-width: 130px; margin-bottom: 15px;">--</div>
        <div id="msg20" style="font-size: 18px; font-weight: 900; color: #34d399; margin: 12px 0;">اختر أرقامك (سعر الرقم 5 USDD والربح 70 USDD)</div>
        <div class="grid-20">
            {% for n in range(1, 21) %}
                <button type="button" id="n20_{{ n }}" onclick="toggle20({{ n }})" class="num-box-20">{{ n }}</button>
            {% endfor %}
        </div>
        <button type="button" onclick="spin20()" style="padding: 16px 45px; background: linear-gradient(135deg,#ffd700,#ff8c00); color: #000; font-weight: 900; font-size: 20px; border: none; border-radius: 16px; cursor: pointer; margin-top: 20px;">ابدأ السحب 🎰</button>
    </div>
    <script>
        let selected20 = [];
        function toggle20(n) {
            let idx = selected20.indexOf(n);
            if(idx > -1) {
                selected20.splice(idx, 1);
                document.getElementById('n20_' + n).classList.remove('selected');
            } else {
                selected20.push(n);
                document.getElementById('n20_' + n).classList.add('selected');
            }
        }
        function spin20() {
            if(selected20.length === 0) { alert("اختر رقماً واحداً على الأقل!"); return; }
            fetch('/game_20_numbers', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({selected_numbers: selected20})}).then(res => res.json()).then(d => {
                if(d.success) {
                    document.getElementById('slot20').innerText = '#' + d.winning_number;
                    document.getElementById('msg20').innerText = d.msg;
                    document.getElementById('bal20').innerText = d.balance;
                    let winB = document.getElementById('n20_' + d.winning_number);
                    if(winB) winB.classList.add('winning-gold-glow');
                    setTimeout(() => {
                        selected20.forEach(n => document.getElementById('n20_' + n).classList.remove('selected'));
                        if(winB) winB.classList.remove('winning-gold-glow');
                        selected20 = [];
                    }, 4000);
                }
            });
        }
    </script>
</body>
</html>
"""

ADMIN_CUSTOMERS_PAGE = LANG_BAR + """
<!DOCTYPE html>
<html lang="{{ t.dir }}" dir="{{ t.dir }}">
<head><meta charset="UTF-8"><title>إدارة الزبائن - 12D</title></head>
<body style="font-family:'Segoe UI', Tahoma, sans-serif; background:#151928; color:#fff; padding:30px; text-align:center;">
    <h2>👑 إدارة الزبائن والحسابات</h2>
    <a href="/dashboard" style="background:#3b82f6; color:#fff; padding:10px 18px; text-decoration:none; border-radius:10px;">الرئيسية</a>
    <div style="background:rgba(25,30,48,0.9); padding:30px; border-radius:20px; max-width:900px; margin:25px auto;">
        <table style="width:100%; border-collapse:collapse;">
            <tr style="background:#0a0d16; color:#ffd700;"><th style="padding:12px; border:1px solid #444;">User</th><th style="padding:12px; border:1px solid #444;">Owner</th><th style="padding:12px; border:1px solid #444;">Balance</th></tr>
            {% for u in users_list %}
            <tr><td style="padding:12px; border:1px solid #444;"><a href="/admin_customer_detail/{{ u.username }}" style="color:#38bdf8;">{{ u.username }}</a></td><td style="padding:12px; border:1px solid #444;">{{ u.owner_name }}</td><td style="padding:12px; border:1px solid #444; color:#34d399;">{{ u.balance }} USDD</td></tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

ADMIN_CUSTOMER_DETAIL_PAGE = LANG_BAR + """
<!DOCTYPE html>
<html lang="{{ t.dir }}" dir="{{ t.dir }}">
<head><meta charset="UTF-8"><title>ذاكرة الزبون</title></head>
<body style="font-family:'Segoe UI', Tahoma, sans-serif; background:#151928; color:#fff; padding:30px; text-align:center;">
    <h2>📂 تفاصيل: {{ user.username }}</h2>
    <a href="/admin_customers" style="background:#3b82f6; color:#fff; padding:10px 18px; text-decoration:none; border-radius:10px;">الرجوع</a>
</body>
</html>
"""

ADMIN_GAMES_PAGE = LANG_BAR + """
<!DOCTYPE html>
<html lang="{{ t.dir }}" dir="{{ t.dir }}">
<head><meta charset="UTF-8"><title>لوحة الألعاب</title></head>
<body style="font-family:'Segoe UI', Tahoma, sans-serif; background:#151928; color:#fff; text-align:center; padding:35px;">
    <h2>🎮 لوحة تحكم الألعاب والأرشيف</h2>
    <a href="/dashboard" style="background:#3b82f6; color:#fff; padding:10px 18px; text-decoration:none; border-radius:10px;">الرئيسية</a>
    <div style="background: rgba(15,23,42,0.95); border: 2px solid #38bdf8; padding: 25px; border-radius: 20px; max-width: 500px; margin: 25px auto;">
        <h3>📊 أرشيف العدادات العالمية</h3>
        <p>إجمالي النقرات: <b>{{ total_spins }}</b></p>
        <p style="color: #ffd700;">ناقص لجائزة 20$ (كل 40): <b>{{ rem_40 }} نقرات</b></p>
        <p style="color: #34d399;">ناقص لجائزة 100$ (كل 360): <b>{{ rem_360 }} نقرات</b></p>
    </div>
</body>
</html>
"""

ADMIN_ACCOUNTING_PAGE = LANG_BAR + """
<!DOCTYPE html>
<html lang="{{ t.dir }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>برنامج المحاسبة - 12D</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: #151928; color: #f8fafc; padding: 25px; text-align: center; }
        .panel-box { background: rgba(25,30,48,0.9); padding: 22px; border-radius: 16px; max-width: 500px; margin: 20px auto; border: 2px solid #ffd700; }
        input, select { width: 100%; padding: 12px; margin: 8px 0; border-radius: 10px; background: #0a0d16; color: white; border: 1px solid #444; box-sizing: border-box; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #444; padding: 12px; text-align: center; }
        th { background: #0a0d16; color: #ffd700; }
    </style>
</head>
<body>
    <h2>📊 برنامج المحاسبة والخزنة المركزية</h2>
    <a href="/dashboard" style="background:#3b82f6; color:#fff; padding:10px 18px; text-decoration:none; border-radius:10px; font-weight:900;">الرئيسية</a>
    
    {% if msg %}<div style="background: #065f46; color: #34d399; padding: 14px; border-radius: 12px; margin: 20px auto; max-width: 500px; font-weight: 900;">{{ msg }}</div>{% endif %}

    <div style="font-size: 35px; font-weight: 900; color: #34d399; margin: 20px 0;">🏦 الخزنة: {{ vault_balance }} USDD</div>

    <div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;">
        <!-- بيع عملات مباشر + فلتر -->
        <div class="panel-box">
            <h3 style="color: #22c55e;">⚡ بيع عملات مباشر للزبون</h3>
            <form method="POST">
                <input type="hidden" name="action" value="sell_currency">
                <label>فلتر البحث للأسماء:</label>
                <input type="text" id="filterSell" placeholder="ابحث عن اسم الزبون..." onkeyup="filterSelect('filterSell', 'selectSell')">
                <select name="target_user" id="selectSell" required>
                    <option value="">اختر الحساب</option>
                    {% for u in users_list %}<option value="{{ u.username }}">{{ u.username }} (رصيده: {{ u.balance }})</option>{% endfor %}
                </select>
                <label>المبلغ (USDD):</label><input type="number" name="amount" placeholder="المبلغ" min="1" required>
                <button type="submit" style="background:#22c55e; color:#000; padding:12px; font-weight:900; border:none; border-radius:8px; width:100%; cursor:pointer; margin-top:10px;">إتمام البيع</button>
            </form>
        </div>

        <!-- بيع باقة 1000 USDD + فلتر -->
        <div class="panel-box" style="border-color: #38bdf8;">
            <h3 style="color: #38bdf8;">💎 بيع باقة 1000 USDD</h3>
            <form method="POST">
                <input type="hidden" name="action" value="sell_1000">
                <label>فلتر البحث للأسماء:</label>
                <input type="text" id="filter1000" placeholder="ابحث عن اسم الزبون..." onkeyup="filterSelect('filter1000', 'select1000')">
                <select name="target_user" id="select1000" required>
                    <option value="">اختر الحساب</option>
                    {% for u in users_list %}<option value="{{ u.username }}">{{ u.username }} (رصيده: {{ u.balance }})</option>{% endfor %}
                </select>
                <button type="submit" style="background:#38bdf8; color:#000; padding:12px; font-weight:900; border:none; border-radius:8px; width:100%; cursor:pointer; margin-top:25px;">بيع 1000 USDD</button>
            </form>
        </div>

        <!-- استرجاع عملات + فلتر -->
        <div class="panel-box" style="border-color: #ef4444;">
            <h3 style="color: #ef4444;">💸 استرجاع العملات من الزبون</h3>
            <form method="POST">
                <input type="hidden" name="action" value="buy_back_currency">
                <label>فلتر البحث للأسماء:</label>
                <input type="text" id="filterBack" placeholder="ابحث عن اسم الزبون..." onkeyup="filterSelect('filterBack', 'selectBack')">
                <select name="target_user" id="selectBack" required>
                    <option value="">اختر الحساب</option>
                    {% for u in users_list %}<option value="{{ u.username }}">{{ u.username }} (رصيده: {{ u.balance }})</option>{% endfor %}
                </select>
                <label>المبلغ المراد استرجاعه:</label><input type="number" name="amount" placeholder="المبلغ" min="1" required>
                <button type="submit" style="background:#ef4444; color:#fff; padding:12px; font-weight:900; border:none; border-radius:8px; width:100%; cursor:pointer; margin-top:10px;">استرجاع للخزنة</button>
            </form>
        </div>
    </div>

    <!-- سجل العمليات مع فلتر -->
    <div style="background: rgba(25,30,48,0.9); padding: 30px; border-radius: 20px; max-width: 900px; margin: 30px auto;">
        <h3 style="color: #ffd700;">📋 سجل العمليات المالية</h3>
        <input type="text" id="logSearch" placeholder="🔍 فلتر البحث في السجل بالاسم أو نوع العملية..." onkeyup="filterLogs()" style="margin: 15px 0; padding: 12px; width: 100%;">
        <table id="logsTable">
            <tr><th>نوع العملية</th><th>المسؤول</th><th>الهدف</th><th>المبلغ</th><th>التوقيت</th></tr>
            {% for log in logs %}
            <tr><td><b>{{ log.action_type }}</b></td><td>{{ log.admin_name }}</td><td>{{ log.target_user }}</td><td style="color: #34d399;">{{ log.amount }} USDD</td><td>{{ log.log_time }}</td></tr>
            {% endfor %}
        </table>
    </div>

    <script>
        function filterSelect(inputId, selectId) {
            let filter = document.getElementById(inputId).value.toLowerCase();
            let select = document.getElementById(selectId);
            let options = select.getElementsByTagName('option');
            for (let i = 1; i < options.length; i++) {
                let txt = options[i].text.toLowerCase();
                options[i].style.display = txt.includes(filter) ? "" : "none";
            }
        }
        function filterLogs() {
            let input = document.getElementById('logSearch').value.toLowerCase();
            let trs = document.querySelectorAll('#logsTable tr');
            for (let i = 1; i < trs.length; i++) {
                let a = trs[i].getElementsByTagName('td')[0];
                let t = trs[i].getElementsByTagName('td')[2];
                if (a || t) {
                    let aText = a ? a.innerText.toLowerCase() : '';
                    let tText = t ? t.innerText.toLowerCase() : '';
                    trs[i].style.display = (aText.includes(input) || tText.includes(input)) ? "" : "none";
                }
            }
        }
    </script>
</body>
</html>
"""

GAME_ROULETTE_GLOBAL_PAGE = LANG_BAR + """
<!DOCTYPE html>
<html lang="{{ t.dir }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ t.game2 }} - 12D</title>
    <style>
        body { font-family:'Segoe UI', Tahoma, sans-serif; background:radial-gradient(circle at center, #151928 0%, #070a12 100%); color:#fff; margin:0; padding:15px; text-align: center; }
        .grand-prize-banner { background: linear-gradient(135deg, #ffd700, #ff8c00); color: #000; padding: 14px; border-radius: 14px; font-weight: 900; font-size: 20px; max-width: 850px; margin: 0 auto 15px auto; box-shadow: 0 0 25px rgba(255,215,0,0.6); border: 2px solid #fff; }
        .roulette-container { background: linear-gradient(135deg, #0e4c26 0%, #062e17 100%); border: 5px solid #b8860b; padding: 25px; border-radius: 25px; max-width: 850px; margin: 15px auto; box-shadow: 0 25px 60px rgba(0,0,0,0.9); }
        .slot-box { font-size: 45px; font-weight: 900; color: #ffd700; background: #000; padding: 10px; border-radius: 12px; border: 3px solid #b8860b; display: inline-block; min-width: 120px; }
        .table-scroll-wrapper { width: 100%; overflow-x: auto; margin: 15px 0; padding-bottom: 10px; }
        .roulette-vertical-table { display: flex; flex-direction: column; gap: 6px; max-width: 320px; margin: 0 auto; background: #09381b; padding: 15px; border-radius: 16px; border: 3px solid #ffd700; }
        .table-row { display: flex; gap: 6px; justify-content: center; }
        .num-btn { width: 65px; height: 60px; background: #111827; border: 2px solid #ffd700; border-radius: 10px; font-size: 20px; font-weight: 900; color: #fff; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: 0.2s; }
        .num-btn.selected { background: #d97706 !important; color: #000 !important; }
        .num-btn.winning-gold-glow { background: #fbbf24 !important; border: 4px solid #fff !important; box-shadow: 0 0 40px #ffd700 !important; color: #000 !important; transform: scale(1.15); }
        .btn-red { background: #dc2626 !important; }
        .btn-black { background: #1f2937 !important; }
        .btn-green { background: #059669 !important; width: 100%; height: 50px; }
        .action-btn { padding: 14px 22px; font-weight: 900; border-radius: 12px; border: none; cursor: pointer; color: #fff; }
    </style>
</head>
<body>
    <div style="display:flex; justify-content:space-between; align-items:center; max-width:850px; margin:0 auto; background:rgba(20,24,38,0.9); padding:12px 20px; border-radius:15px;">
        <h2 style="color:#ffd700; margin:0;">🎰 {{ t.game2 }}</h2>
        <a href="/dashboard" style="background:#3b82f6; color:#fff; padding:8px 16px; text-decoration:none; border-radius:8px;">الرئيسية</a>
        <div><b>{{ t.balance }}: <span id="liveRouletteBalance">{{ balance }}</span> USDD</b></div>
    </div>
    <div class="roulette-container">
        <div class="grand-prize-banner">🌟 الجائزة الكبرى 299000 usdd 🌟</div>
        <div id="rouletteTimer" style="font-size: 22px; font-weight: 900; color: #38bdf8; margin-bottom: 15px;">⏳ وقت اختيار الأرقام: 20 ثانية</div>
        <div id="rouletteSlot" class="slot-box">--</div>
        <div id="rouletteMsg" style="font-size: 17px; font-weight: 900; color: #34d399; margin: 12px 0;">انقر على الأرقام للخصم الفوري والرهان!</div>
        <div style="display: flex; justify-content: center; gap: 15px; margin-bottom: 15px;">
            <button type="button" onclick="selectColor('red')" class="action-btn" style="background: #dc2626;">🟥 حجز كل الأحمر</button>
            <button type="button" onclick="selectColor('black')" class="action-btn" style="background: #111827; border: 1px solid #ffd700;">⬛ حجز كل الأسود</button>
        </div>
        <div class="table-scroll-wrapper">
            <div class="roulette-vertical-table">
                <button type="button" id="num_0" onclick="toggleNumber(0)" class="num-btn btn-green">0</button>
                {% for row in [[1,2,3],[4,5,6],[7,8,9],[10,11,12],[13,14,15],[16,17,18],[19,20,21],[22,23,24],[25,26,27],[28,29,30],[31,32,33],[34,35,36]] %}
                    <div class="table-row">
                        {% for n in row %}
                            <button type="button" id="num_{{ n }}" onclick="toggleNumber({{ n }})" class="num-btn {{ 'btn-red' if n in [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36] else 'btn-black' }}">{{ n }}</button>
                        {% endfor %}
                    </div>
                {% endfor %}
            </div>
        </div>
        <div>
            <button type="button" onclick="undoLastAction()" class="action-btn" style="background: #ef4444;">🗑️ مسح (آخر نقرة)</button>
            <button type="button" onclick="repeatLastBet()" class="action-btn" style="background: #3b82f6;">🔄 تكرار الرهان</button>
        </div>
    </div>
    <script>
        let selectedNumbers = [];
        let actionStack = [];
        let maxAllowed = 21;
        let timeLeft = 20;
        const reds = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36];
        const blacks = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35];

        function toggleNumber(num) {
            let idx = selectedNumbers.indexOf(num);
            if(idx > -1) {
                fetch('/api/roulette_action', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({action: 'remove'})}).then(res => res.json()).then(d => {
                    if(d.success) document.getElementById('liveRouletteBalance').innerText = d.balance;
                });
                selectedNumbers.splice(idx, 1);
                actionStack.forEach(arr => { let i = arr.indexOf(num); if(i > -1) arr.splice(i, 1); });
                document.getElementById('num_' + num).classList.remove('selected');
            } else {
                if(selectedNumbers.length >= maxAllowed) { alert("حد أقصى 21 رقماً!"); return; }
                fetch('/api/roulette_action', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({action: 'add'})}).then(res => res.json()).then(d => {
                    if(d.success) {
                        document.getElementById('liveRouletteBalance').innerText = d.balance;
                        selectedNumbers.push(num);
                        actionStack.push([num]);
                        document.getElementById('num_' + num).classList.add('selected');
                    } else { alert("رصيدك لا يكفي!"); }
                });
            }
        }
        function selectColor(type) {
            let tNums = (type === 'red') ? reds : blacks;
            let newly = [];
            tNums.forEach(n => {
                if(!selectedNumbers.includes(n) && selectedNumbers.length < maxAllowed) {
                    selectedNumbers.push(n);
                    newly.push(n);
                    document.getElementById('num_' + n).classList.add('selected');
                }
            });
            if(newly.length > 0) {
                for(let i=0; i<newly.length; i++) {
                    fetch('/api/roulette_action', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({action: 'add'})}).then(res => res.json()).then(d => {
                        if(d.success) document.getElementById('liveRouletteBalance').innerText = d.balance;
                    });
                }
                actionStack.push(newly);
            }
        }
        function undoLastAction() {
            if(actionStack.length > 0) {
                let last = actionStack.pop();
                fetch('/api/roulette_action', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({action: 'clear', count: last.length})}).then(res => res.json()).then(d => {
                    if(d.success) document.getElementById('liveRouletteBalance').innerText = d.balance;
                });
                last.forEach(n => {
                    selectedNumbers = selectedNumbers.filter(i => i !== n);
                    document.getElementById('num_' + n).classList.remove('selected');
                });
            }
        }
        function repeatLastBet() {
            if(selectedNumbers.length > 0) undoLastAction();
            let last = localStorage.getItem('lastRouletteSelection');
            if(last) {
                let saved = JSON.parse(last);
                saved.forEach(n => toggleNumber(n));
            }
        }
        let timer = setInterval(() => {
            timeLeft--;
            document.getElementById('rouletteTimer').innerText = `⏳ وقت اختيار الأرقام: ${timeLeft} ثانية`;
            if(timeLeft <= 0) {
                clearInterval(timer);
                if(selectedNumbers.length > 0) spin();
                else { for(let i=0; i<5; i++) selectedNumbers.push(Math.floor(Math.random()*37)); spin(); }
            }
        }, 1000);

        function spin() {
            if(selectedNumbers.length === 0) return;
            localStorage.setItem('lastRouletteSelection', JSON.stringify(selectedNumbers));
            fetch('/game_roulette', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({selected_numbers: selectedNumbers})}).then(res => res.json()).then(d => {
                document.getElementById('rouletteSlot').innerText = d.winning_number;
                document.getElementById('rouletteMsg').innerText = d.msg;
                document.getElementById('liveRouletteBalance').innerText = d.balance;
                let wBtn = document.getElementById('num_' + d.winning_number);
                if(wBtn) wBtn.classList.add('winning-gold-glow');
                setTimeout(() => { location.reload(); }, 4000);
            });
        }
    </script>
</body>
</html>
"""

# --- جميع مسارات الفلاسك تأتي في الأسفل حصرياً بعد تعريف كافة القوالب ---

@app.route('/set_lang/<lang>')
def set_lang(lang):
    if lang in TRANSLATIONS:
        session['lang'] = lang
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
            session['lang'] = session.get('lang', 'ar')
            return redirect(url_for('dashboard'))
        else:
            error = "خطأ في اسم المستخدم أو كلمة المرور!" if t['dir'] == 'rtl' else "Invalid Username or Password!"
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
    msg = None
    if request.method == 'POST':
        action = request.form.get('action')
        vault = SystemVault.query.get(1)
        if action == 'redeem_card':
            card_code = request.form.get('card_code', '').strip()
            card = RechargeCard.query.filter_by(code=card_code, is_used=False).first()
            if card:
                if vault.vault_balance >= card.amount:
                    vault.vault_balance -= card.amount
                    user.balance += card.amount
                    card.is_used = True
                    card.used_by = user.username
                    db.session.add(FinancialLog(action_type='شحن عبر بطاقة كود', admin_name='system', target_user=user.username, amount=card.amount, log_time=get_local_time()))
                    db.session.commit()
                    msg = f"🎉 {card.amount} USDD"
                else: msg = "Error Vault"
            else: msg = "Invalid Code"
        elif action in ['withdraw_wish', 'withdraw_visa', 'withdraw_usdt']:
            msg = t['success_msg']

    return render_template_string(DASHBOARD_PAGE, t=t, username=user.username, role=user.role, balance=user.balance, msg=msg)

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'username' not in session: return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    t = get_t()
    msg = None
    if request.method == 'POST':
        old_p, new_p, confirm_p = request.form.get('old_password', ''), request.form.get('new_password', '').strip(), request.form.get('confirm_password', '').strip()
        if user.role != 'admin' and user.password != old_p: msg = "Old Password Error!"
        elif not new_p or new_p != confirm_p: msg = "Password Mismatch!"
        else:
            user.password = new_p
            db.session.commit()
            msg = "Updated Successfully!"
    return render_template_string(CHANGE_PASSWORD_PAGE, t=t, username=user.username, balance=user.balance, msg=msg)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
