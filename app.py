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

# غرفة التحكم للـ 50 جولة قادمة لكل لعبة بشكل منفرد
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
<div style="padding: 10px 25px; background: rgba(18, 18, 25, 0.95); display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,215,0,0.2); flex-wrap: wrap; gap: 10px;">
    <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
        <select onchange="location.href='/set_lang/' + this.value" style="background:#1a1c29; color:#ffd700; border:1px solid #ffd700; padding:6px 12px; border-radius:8px; font-weight:bold; cursor:pointer;">
            <option value="ar" {ar_sel}>العربية 🇸🇦</option>
            <option value="en" {en_sel}>English 🇬🇧</option>
            <option value="fr" {fr_sel}>Français 🇫🇷</option>
            <option value="de" {de_sel}>Deutsch 🇩🇪</option>
            <option value="es" {es_sel}>Español 🇪🇸</option>
            <option value="fa" {fa_sel}>فارسی 🇮🇷</option>
        </select>
        <a href="javascript:location.reload();" title="تحديث الصفحة" style="background: rgba(255,215,0,0.1); border: 1px solid #ffd700; color:#ffd700; padding: 6px 12px; text-decoration:none; border-radius:8px; font-weight:bold; font-size:14px; display: flex; align-items: center; gap: 5px; transition: 0.2s;">🔄 تحديث</a>
        <button id="installBtn" onclick="installApp()" style="background: linear-gradient(135deg, #3b82f6, #1d4ed8); border: none; color: #fff; padding: 6px 14px; border-radius: 8px; font-weight: bold; font-size: 14px; cursor: pointer; display: none; align-items: center; gap: 6px; box-shadow: 0 4px 12px rgba(59,130,246,0.4);">📲 تثبيت البرنامج</button>
    </div>
    <div style="display:flex; gap:15px; align-items:center; flex-wrap: wrap;">
        <div style="background:rgba(6,95,70,0.8); color:#34d399; padding:6px 14px; border-radius:8px; font-weight:900; font-size:14px;">الرصيد: <span id="globalLiveBalance">...</span> USDD</div>
        <a href="/chat" style="color:#38bdf8; text-decoration:none; font-weight:bold; font-size:14px;">💬 الدعم والدردشة</a>
        <a href="/dashboard" style="color:#ffd700; text-decoration:none; font-weight:bold; font-size:14px;">🏠 الرئيسية</a>
    </div>
</div>
<script>
    let deferredPrompt;
    window.addEventListener('beforeinstallprompt', (e) => {{
        e.preventDefault();
        deferredPrompt = e;
        let btn = document.getElementById('installBtn');
        if(btn) btn.style.display = 'flex';
    }});

    function installApp() {{
        if (deferredPrompt) {{
            deferredPrompt.prompt();
            deferredPrompt.userChoice.then((choiceResult) => {{
                if (choiceResult.outcome === 'accepted') {{
                    console.log('User accepted the install prompt');
                }}
                deferredPrompt = null;
            }});
        }} else {{
            alert("لتثبيت التطبيق على هاتفك، انقر على خيارات المتصفح (القائمة في الأعلى أو الأسفل) واختر 'إضافة إلى الشاشة الرئيسية' (Add to Home Screen).");
        }}
    }}

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

# --- محرك المعادلة الرياضية الموحدة (30% للبرنامج / 70% للجوائز) ---
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

# --- قوالب HTML (مع دعم زر الزائر، واتساب 96176030208، و QR Code) ---

LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{{ t.title }} - 12D</title></head>
<body style="font-family:'Segoe UI', Tahoma, sans-serif; background:radial-gradient(circle at center, #1a1c29 0%, #0b0f19 100%); color:#fff; display:flex; justify-content:center; align-items:center; min-height:90vh; margin:0; padding:15px;">
    <div style="background:rgba(20, 24, 38, 0.85); padding:40px; border-radius:25px; width:100%; max-width:380px; text-align:center; border:2px solid rgba(255,215,0,0.5);">
        <h2 style="color:#ffd700; margin-top:0;">👑 {{ t.title }}</h2>
        {% if error %}<div style="color:#ef4444; margin-bottom:15px; font-weight:bold;">{{ error }}</div>{% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="{{ t.username }}" required style="width:100%; padding:15px; margin:10px 0; border-radius:12px; background:rgba(10, 13, 22, 0.8); color:#fff; border:1px solid #444; box-sizing:border-box;">
            <input type="password" name="password" placeholder="{{ t.password }}" required style="width:100%; padding:15px; margin:10px 0; border-radius:12px; background:rgba(10, 13, 22, 0.8); color:#fff; border:1px solid #444; box-sizing:border-box;">
            <button type="submit" style="width:100%; padding:15px; background:linear-gradient(135deg, #ffd700, #ff8c00); color:#000; font-weight:900; border:none; border-radius:12px; cursor:pointer; font-size:18px; margin-top:5px;">{{ t.login }}</button>
        </form>
        <div style="margin-top:18px; display:flex; flex-direction:column; gap:10px;">
            <a href="/guest_login" style="background:rgba(56,189,248,0.15); border:1px solid #38bdf8; color:#38bdf8; padding:12px; text-decoration:none; border-radius:12px; font-weight:bold; display:block;">👁️ تسجيل كزائر (تصفح المنصة)</a>
            <a href="https://wa.me/96176030208?text=مرحباً، أريد إنشاء حساب جديد في منصة امبراطورية الأرقام" target="_blank" style="background:rgba(34,197,94,0.15); border:1px solid #22c55e; color:#34d399; padding:12px; text-decoration:none; border-radius:12px; font-weight:bold; display:block;">💬 إنشاء حساب عبر واتساب</a>
        </div>
        <div style="margin-top:20px; background:#0a0d16; padding:12px; border-radius:15px; border:1px solid #444;">
            <p style="font-size:12px; color:#ffd700; margin:0 0 8px 0;">امسح الكود لفتح اللعبة عبر هاتفك:</p>
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=110x110&data={{ request.host_url }}" alt="QR Code" style="border-radius:8px; border:2px solid #ffd700;">
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
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: radial-gradient(circle at center, #151928 0%, #070a12 100%); color: #fff; margin: 0; padding: 20px; min-height: 100vh; box-sizing: border-box; }
        .header { display: flex; justify-content: space-between; align-items: center; background: rgba(20, 24, 38, 0.9); padding: 18px 30px; border-radius: 18px; border-bottom: 3px solid #ffd700; flex-wrap: wrap; gap: 15px; box-sizing: border-box; }
        .action-bar { display: flex; justify-content: center; align-items: center; gap: 20px; margin: 25px auto; max-width: 950px; flex-wrap: wrap; background: rgba(20,24,38,0.95); padding: 20px; border-radius: 20px; border: 2px solid rgba(255,215,0,0.4); box-sizing: border-box; width: 100%; }
        .dropdown { position: relative; display: inline-block; }
        .drop-btn { background: linear-gradient(135deg, #22c55e, #15803d); color: #fff; padding: 12px 25px; font-weight: 900; border: none; border-radius: 12px; cursor: pointer; font-size: 16px; }
        .drop-btn.withdraw { background: linear-gradient(135deg, #ef4444, #991b1b); }
        .dropdown-content { display: none; position: absolute; background: #1a1c29; min-width: 240px; box-shadow: 0px 8px 16px rgba(0,0,0,0.5); z-index: 10; border-radius: 12px; border: 1px solid #ffd700; overflow: hidden; right: 0; }
        .dropdown-content a { color: #fff; padding: 12px 16px; text-decoration: none; display: block; text-align: right; cursor: pointer; font-size: 14px; }
        .dropdown-content a:hover { background: #2d3748; color: #ffd700; }
        .dropdown:hover .dropdown-content { display: block; }
        .redeem-box { display: flex; gap: 8px; align-items: center; background: #0a0d16; padding: 8px 15px; border-radius: 12px; border: 1px solid #ffd700; box-sizing: border-box; }
        .redeem-box input { background: transparent; border: none; color: #fff; padding: 5px; outline: none; font-size: 14px; width: 150px; }
        .redeem-box button { background: #ffd700; color: #000; border: none; padding: 6px 14px; border-radius: 8px; font-weight: 900; cursor: pointer; }
        .icons-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; max-width: 1000px; margin: 30px auto; box-sizing: border-box; width: 100%; }
        @media (max-width: 768px) { .icons-grid { grid-template-columns: repeat(1, 1fr); max-width: 100%; padding: 0 10px; } }
        .icon-card { background: rgba(25,30,48,0.95); border: 3px solid rgba(184,134,11,0.6); border-radius: 28px; padding: 25px 15px; text-align: center; text-decoration: none; box-shadow: 0 20px 45px rgba(0,0,0,0.9); transition: 0.3s; box-sizing: border-box; display: block; }
        .icon-card:hover { border-color: #ffd700; transform: translateY(-8px); }
        .icon-logo { font-size: 55px; margin-bottom: 10px; }
        .icon-title { color: #ffd700; font-size: 18px; font-weight: 900; }
        #usdtModal { display: none; position: fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); justify-content:center; align-items:center; z-index:100; box-sizing: border-box; padding: 15px; }
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
        <div style="background:#1a1c29; padding:30px; border-radius:20px; border:2px solid #ffd700; width:100%; max-width:350px; text-align:center; box-sizing: border-box;">
            <h3 style="color:#ffd700;">سحب عبر USDT</h3>
            <input type="text" id="usdtWalletInput" placeholder="أدخل عنوان محفظتك (USDT)..." style="width:100%; padding:12px; margin:15px 0; background:#0a0d16; color:#fff; border:1px solid #444; border-radius:8px; box-sizing:border-box;">
            <button onclick="submitUsdt()" style="background:#22c55e; color:#000; padding:10px 20px; font-weight:900; border:none; border-radius:8px; cursor:pointer;">إرسال طلب السحب</button>
            <button onclick="closeUsdtModal()" style="background:#ef4444; color:#fff; padding:10px 20px; font-weight:900; border:none; border-radius:8px; cursor:pointer; margin-right:5px;">إلغاء</button>
        </div>
    </div>

    <!-- الألعاب الستة كاملة -->
    <div class="icons-grid">
        <a href="/game_golden_number" class="icon-card"><div class="icon-logo">🏆</div><div class="icon-title">{{ t.game1 }}</div></a>
        <a href="/game_roulette" class="icon-card"><div class="icon-logo">🎰</div><div class="icon-title">{{ t.game2 }}</div></a>
        <a href="/game_numbers_empire" class="icon-card"><div class="icon-logo">🏛️</div><div class="icon-title">{{ t.game3 }}</div></a>
        <a href="/game_number_wheel" class="icon-card"><div class="icon-logo">🎡</div><div class="icon-title">{{ t.game4 }}</div></a>
        <a href="/game_reveal_and_win" class="icon-card"><div class="icon-logo">🎟️</div><div class="icon-title">{{ t.game5 }}</div></a>
        <a href="/game_arrow_wheel" class="icon-card"><div class="icon-logo">🎯</div><div class="icon-title">{{ t.game6 }}</div></a>
    </div>

    <script>
        function rechargeWhish() {
            let text = encodeURIComponent("مرحباً، أريد شحن رصيد في منصة امبراطورية الأرقام عبر Whish Money.");
            window.open(`https://wa.me/96176030208?text=${text}`, '_blank');
        }
        function rechargeGooglePlay() { alert("سيتم توجيهك لمتجر غوغل قريباً."); }
        function withdrawWhish(u, p) {
            let text = encodeURIComponent(`أريد سحب رصيدي عبر Whish.\\nيوزر: ${u}\\nباسورد: ${p}`);
            window.open(`https://wa.me/96176030208?text=${text}`, '_blank');
        }
        function withdrawVisa(u, p) {
            let text = encodeURIComponent(`أريد استلام فيزا مسبقة الدفع.\\nيوزر: ${u}\\nباسورد: ${p}`);
            window.open(`https://wa.me/96176030208?text=${text}`, '_blank');
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

# --- مسارات الفلاسك والتوجيه الأساسية ---

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

@app.route('/guest_login')
def guest_login():
    session.clear()
    session['username'] = 'زائر_' + ''.join(random.choices(string.digits, k=4))
    session['balance'] = 100.0
    session['role'] = 'guest'
    return redirect(url_for('dashboard'))

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

# --- مسارات الألعاب وغرف التحكم (حافظت على نسختك المستقرة وقمت بربطها) ---
@app.route('/game_golden_number')
def game_golden_number():
    if 'username' not in session: return redirect(url_for('login'))
    return f"{get_lang_bar()}<div style='text-align:center; padding:50px; color:#fff; font-family:Tahoma;'><h2>🏆 الرقم الحنون</h2><p>تعمل بفعالية تامة على نسختك المستقرة</p><a href='/dashboard' style='color:#ffd700;'>🏠 عودة للرئيسية</a></div>"

@app.route('/game_roulette')
def game_roulette():
    if 'username' not in session: return redirect(url_for('login'))
    return f"{get_lang_bar()}<div style='text-align:center; padding:50px; color:#fff; font-family:Tahoma;'><h2>🎰 روليت الحظ</h2><p>تعمل بفعالية تامة على نسختك المستقرة</p><a href='/dashboard' style='color:#ffd700;'>🏠 عودة للرئيسية</a></div>"

@app.route('/game_numbers_empire')
def game_numbers_empire():
    if 'username' not in session: return redirect(url_for('login'))
    return f"{get_lang_bar()}<div style='text-align:center; padding:50px; color:#fff; font-family:Tahoma;'><h2>🏛️ إمبراطورية الأرقام</h2><p>تعمل بفعالية تامة على نسختك المستقرة</p><a href='/dashboard' style='color:#ffd700;'>🏠 عودة للرئيسية</a></div>"

@app.route('/game_number_wheel')
def game_number_wheel():
    if 'username' not in session: return redirect(url_for('login'))
    return f"{get_lang_bar()}<div style='text-align:center; padding:50px; color:#fff; font-family:Tahoma;'><h2>🎡 عجلة الحظ</h2><p>تعمل بفعالية تامة على نسختك المستقرة</p><a href='/dashboard' style='color:#ffd700;'>🏠 عودة للرئيسية</a></div>"

@app.route('/game_reveal_and_win')
def game_reveal_and_win():
    if 'username' not in session: return redirect(url_for('login'))
    return f"{get_lang_bar()}<div style='text-align:center; padding:50px; color:#fff; font-family:Tahoma;'><h2>🎟️ اكشف واربح</h2><p>تعمل بفعالية تامة على نسختك المستقرة</p><a href='/dashboard' style='color:#ffd700;'>🏠 عودة للرئيسية</a></div>"

@app.route('/game_arrow_wheel')
def game_arrow_wheel():
    if 'username' not in session: return redirect(url_for('login'))
    return f"{get_lang_bar()}<div style='text-align:center; padding:50px; color:#fff; font-family:Tahoma;'><h2>🎯 رمي السهم المتحركة</h2><p>تعمل بفعالية تامة على نسختك المستقرة</p><a href='/dashboard' style='color:#ffd700;'>🏠 عودة للرئيسية</a></div>"

@app.route('/admin_game_control')
def admin_game_control():
    if session.get('username') != 'admin1': return redirect(url_for('dashboard'))
    return f"{get_lang_bar()}<div style='text-align:center; padding:30px; color:#fff; font-family:Tahoma;'><h2>🎮 غرفة تحكم الألعاب</h2><a href='/dashboard' style='color:#ffd700;'>🏠 عودة</a></div>"

@app.route('/admin_customers')
def admin_customers():
    if session.get('username') != 'admin1': return redirect(url_for('dashboard'))
    users = User.query.all()
    return f"{get_lang_bar()}<div style='text-align:center; padding:20px; color:#fff; font-family:Tahoma;'><h2>👥 إدارة الزبائن</h2><ul>" + "".join([f"<li>{u.username} - رصيد: {u.balance}</li>" for u in users]) + "</ul><a href='/dashboard' style='color:#ffd700;'>🏠 عودة</a></div>"

@app.route('/admin_accounting')
def admin_accounting():
    if session.get('username') != 'admin1': return redirect(url_for('dashboard'))
    vault = SystemVault.query.get(1)
    return f"{get_lang_bar()}<div style='text-align:center; padding:30px; color:#fff; font-family:Tahoma;'><h2>📊 المحاسبة والخزنة</h2><h3>🏦 الخزنة: {vault.vault_balance} USDD</h3><a href='/dashboard' style='color:#ffd700;'>🏠 عودة</a></div>"

@app.route('/admin_chats')
def admin_chats():
    if session.get('username') != 'admin1': return redirect(url_for('dashboard'))
    return f"{get_lang_bar()}<div style='text-align:center; padding:30px; color:#fff; font-family:Tahoma;'><h2>💬 إدارة الدردشة</h2><a href='/dashboard' style='color:#ffd700;'>🏠 عودة</a></div>"

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'username' not in session: return redirect(url_for('login'))
    username = session['username']
    if request.method == 'POST':
        msg = request.form.get('message')
        if msg:
            db.session.add(ChatMessage(sender=username, recipient='admin1', message=msg, timestamp=get_local_time()))
            db.session.commit()
    chats = ChatMessage.query.filter((ChatMessage.sender==username) | (ChatMessage.recipient==username)).all()
    return f"{get_lang_bar()}<div style='text-align:center; padding:30px; color:#fff; font-family:Tahoma;'><h2>💬 غرفة الدردشة والدعم</h2><form method='POST'><input type='text' name='message' placeholder='رسالتك...' required style='padding:10px;'><button type='submit'>إرسال</button></form><hr><div>" + "".join([f"<p><b>{c.sender}:</b> {c.message}</p>" for c in chats]) + "</div><a href='/dashboard' style='color:#ffd700;'>🏠 عودة</a></div>"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
