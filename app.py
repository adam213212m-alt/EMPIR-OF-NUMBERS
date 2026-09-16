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
    db.session.commit()

# --- قاموس الترجمات (6 لغات) ---
TRANSLATIONS = {
    'ar': {
        'dir': 'rtl', 'title': 'امبراطورية الأرقام', 'subtitle': 'منصة الألعاب التفاعلية الفائقة 12D',
        'login': 'دخول للبرنامج', 'username': 'اسم المستخدم', 'password': 'كلمة المرور', 'balance': 'الرصيد',
        'recharge': 'شحن رصيد', 'withdraw': 'سحب رصيد', 'change_pass': 'تغيير الباسورد', 'logout': 'خروج',
        'dashboard': 'لوحة التحكم', 'back_dash': '🏠 الرئيسية', 'customers': 'الزبائن', 'accounting': 'المحاسبة والخزنة',
        'game_control': '🎮 غرفة تحكم الألعاب', 'chat': '💬 الدردشة الفورية',
        'game1': 'الرقم الحنون', 'game2': 'روليت الحظ', 'game3': 'إمبراطورية الأرقام', 'game4': 'عجلة الحظ', 'game5': 'اكشف واربح', 'game6': 'رمي السهم المتحركة'
    },
    'en': {
        'dir': 'ltr', 'title': 'Empire of Numbers', 'subtitle': 'Super Interactive 12D Gaming Platform',
        'login': 'Login', 'username': 'Username', 'password': 'Password', 'balance': 'Balance',
        'recharge': 'Recharge', 'withdraw': 'Withdraw', 'logout': 'Logout',
        'dashboard': 'Dashboard', 'customers': 'Customers', 'accounting': 'Vault & Accounting',
        'game_control': '🎮 Game Control', 'chat': '💬 Live Chat',
        'game1': 'The Tender Number', 'game2': 'Lucky Roulette', 'game3': 'Empire of Numbers', 'game4': 'Wheel of Fortune', 'game5': 'Reveal & Win', 'game6': 'Arrow Throw'
    },
    'fr': {
        'dir': 'ltr', 'title': 'Empire des Nombres', 'subtitle': 'Plateforme 12D',
        'login': 'Connexion', 'username': "Nom d'utilisateur", 'password': 'Mot de passe', 'balance': 'Solde',
        'recharge': 'Recharger', 'withdraw': 'Retirer', 'logout': 'Déconnexion',
        'dashboard': 'Tableau de bord', 'customers': 'Clients', 'accounting': 'Comptabilité',
        'game_control': '🎮 Contrôle', 'chat': '💬 Chat',
        'game1': 'Le Numéro Tendre', 'game2': 'Roulette', 'game3': 'Empire des Nombres', 'game4': 'Roue', 'game5': 'Révéler', 'game6': 'Flèche'
    },
    'de': {
        'dir': 'ltr', 'title': 'Imperium der Zahlen', 'subtitle': '12D Plattform',
        'login': 'Anmelden', 'username': 'Benutzername', 'password': 'Passwort', 'balance': 'Guthaben',
        'recharge': 'Aufladen', 'withdraw': 'Auszahlen', 'logout': 'Abmelden',
        'dashboard': 'Dashboard', 'customers': 'Kunden', 'accounting': 'Buchhaltung',
        'game_control': '🎮 Kontrolle', 'chat': '💬 Chat',
        'game1': 'Die Zarte Nummer', 'game2': 'Roulette', 'game3': 'Imperium', 'game4': 'Glücksrad', 'game5': 'Aufdecken', 'game6': 'Pfeilwurf'
    },
    'es': {
        'dir': 'ltr', 'title': 'Imperio de los Números', 'subtitle': 'Plataforma 12D',
        'login': 'Iniciar Sesión', 'username': 'Usuario', 'password': 'Contraseña', 'balance': 'Saldo',
        'recharge': 'Recargar', 'withdraw': 'Retirar', 'logout': 'Cerrar Sesión',
        'dashboard': 'Panel', 'customers': 'Clientes', 'accounting': 'Contabilidad',
        'game_control': '🎮 Control', 'chat': '💬 Chat',
        'game1': 'Número Tierno', 'game2': 'Ruleta', 'game3': 'Imperio', 'game4': 'Rueda', 'game5': 'Revelar', 'game6': 'Flecha'
    },
    'fa': {
        'dir': 'rtl', 'title': 'امپراتوری اعداد', 'subtitle': 'پلتفرم 12D',
        'login': 'ورود', 'username': 'نام کاربری', 'password': 'رمز عبور', 'balance': 'موجودی',
        'recharge': 'شارژ', 'withdraw': 'برداشت', 'logout': 'خروج',
        'dashboard': 'داشبورد', 'customers': 'مشتریان', 'accounting': 'حسابداری',
        'game_control': '🎮 کنترل بازی', 'chat': '💬 چت',
        'game1': 'عدد مهربان', 'game2': 'رولت', 'game3': 'امپراتوری', 'game4': 'گردونه', 'game5': 'کشف', 'game6': 'دارت'
    }
}

def get_t():
    lang = session.get('lang', 'ar')
    if lang not in TRANSLATIONS: lang = 'ar'
    return TRANSLATIONS[lang]

@app.route('/set_lang/<lang>')
def set_lang(lang):
    if lang in TRANSLATIONS:
        session['lang'] = lang
    return redirect(request.referrer or url_for('dashboard'))

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
        <a href="javascript:location.reload();" style="background: rgba(255,215,0,0.1); border: 1px solid #ffd700; color:#ffd700; padding: 6px 12px; text-decoration:none; border-radius:8px; font-weight:bold; font-size:14px;">🔄 تحديث</a>
        <button id="installBtn" onclick="installApp()" style="background: linear-gradient(135deg, #3b82f6, #1d4ed8); border: none; color: #fff; padding: 6px 14px; border-radius: 8px; font-weight: bold; cursor: pointer; display: none;">📲 تثبيت البرنامج</button>
    </div>
    <div style="display:flex; gap:15px; align-items:center;">
        <div style="background:rgba(6,95,70,0.8); color:#34d399; padding:6px 14px; border-radius:8px; font-weight:900;">الرصيد: <span id="globalLiveBalance">...</span> USDD</div>
        <a href="/chat" style="color:#38bdf8; text-decoration:none; font-weight:bold;">💬 الدردشة</a>
        <a href="/dashboard" style="color:#ffd700; text-decoration:none; font-weight:bold;">🏠 الرئيسية</a>
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
            deferredPrompt.userChoice.then((choiceResult) => {{ deferredPrompt = null; }});
        }} else {{
            alert("لتثبيت التطبيق على هاتفك، انقر على خيارات المتصفح واختر 'إضافة إلى الشاشة الرئيسية'.");
        }
    }}
    setInterval(() => {{
        fetch('/api/sync_balance').then(res => res.json()).then(data => {{
            let b = document.getElementById('globalLiveBalance');
            if(b && b.innerText !== String(data.balance)) b.innerText = data.balance;
        }}).catch(err => {{}});
    }}, 2000);
</script>
"""

@app.route('/sw.js')
def service_worker():
    return app.response_class("self.addEventListener('fetch', function(event) { });", mimetype='application/javascript')

@app.route('/api/sync_balance')
def sync_balance():
    if 'username' in session:
        u = User.query.filter_by(username=session['username']).first()
        return jsonify({'balance': u.balance if u else 0.0})
    return jsonify({'balance': 0.0})

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

# --- صفحات الواجهات الرئيسية (متضمنة QR Code، الزائر، والواتساب) ---
LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{{ t.title }}</title></head>
<body style="font-family:Tahoma; background:#1a1c29; color:#fff; display:flex; justify-content:center; align-items:center; min-height:95vh; margin:0; padding:15px;">
    <div style="background:rgba(20, 24, 38, 0.95); padding:35px; border-radius:25px; width:100%; max-width:400px; text-align:center; border:2px solid #ffd700; box-shadow:0 20px 50px rgba(0,0,0,0.8);">
        <h2 style="color:#ffd700; margin-top:0;">👑 {{ t.title }}</h2>
        {% if error %}<div style="color:#ef4444; margin-bottom:15px; font-weight:bold;">{{ error }}</div>{% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="{{ t.username }}" required style="width:100%; padding:14px; margin:10px 0; border-radius:12px; background:#0a0d16; color:#fff; border:1px solid #444; box-sizing:border-box;">
            <input type="password" name="password" placeholder="{{ t.password }}" required style="width:100%; padding:14px; margin:10px 0; border-radius:12px; background:#0a0d16; color:#fff; border:1px solid #444; box-sizing:border-box;">
            <button type="submit" style="width:100%; padding:14px; background:linear-gradient(135deg, #ffd700, #ff8c00); color:#000; font-weight:900; border:none; border-radius:12px; cursor:pointer; font-size:17px; margin-top:5px;">{{ t.login }}</button>
        </form>
        <div style="margin-top:20px; display:flex; flex-direction:column; gap:10px;">
            <a href="/guest_login" style="background:rgba(56,189,248,0.15); border:1px solid #38bdf8; color:#38bdf8; padding:12px; text-decoration:none; border-radius:12px; font-weight:bold; display:block;">👁️ تسجيل كزائر (تصفح المنصة)</a>
            <a href="https://wa.me/96176030208?text=مرحباً، أريد إنشاء حساب جديد في منصة امبراطورية الأرقام" target="_blank" style="background:rgba(34,197,94,0.15); border:1px solid #22c55e; color:#34d399; padding:12px; text-decoration:none; border-radius:12px; font-weight:bold; display:block;">💬 إنشاء حساب عبر واتساب</a>
        </div>
        <div style="margin-top:25px; background:#0a0d16; padding:12px; border-radius:15px; border:1px solid #444;">
            <p style="font-size:12px; color:#ffd700; margin:0 0 8px 0;">امسح الكود لفتح اللعبة عبر هاتفك:</p>
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=120x120&data={{ request.host_url }}" alt="QR Code" style="border-radius:8px; border:2px solid #ffd700;">
        </div>
    </div>
</body>
</html>
"""

DASHBOARD_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{{ t.dashboard }}</title>
<style>
    body { font-family: Tahoma; background: #070a12; color: #fff; margin: 0; padding: 20px; }
    .header { display: flex; justify-content: space-between; align-items: center; background: rgba(20, 24, 38, 0.9); padding: 18px 30px; border-radius: 18px; border-bottom: 3px solid #ffd700; flex-wrap: wrap; gap: 15px; }
    .icons-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; max-width: 1000px; margin: 30px auto; }
    @media (max-width: 768px) { .icons-grid { grid-template-columns: 1fr; } }
    .icon-card { background: rgba(25,30,48,0.95); border: 3px solid #b8860b; border-radius: 28px; padding: 25px 15px; text-align: center; text-decoration: none; box-shadow: 0 20px 45px rgba(0,0,0,0.9); display: block; transition: 0.3s; }
    .icon-card:hover { border-color: #ffd700; transform: translateY(-5px); }
</style>
</head>
<body>
    {{ lang_bar | safe }}
    <div class="header">
        <div style="display:flex; gap:18px; align-items:center; flex-wrap:wrap;">
            <h2 style="color:#ffd700; margin:0;">👑 {{ t.title }} (12D)</h2>
            <div style="background:rgba(15,20,32,0.9); padding:8px 15px; border-radius:10px;">👤 <b>{{ username }}</b></div>
            <div style="background:rgba(6,95,70,0.8); color:#34d399; padding:8px 18px; border-radius:10px; font-weight:900;">الرصيد: <span id="liveBalance">{{ balance }}</span> USDD</div>
        </div>
        <div style="display:flex; gap:12px; flex-wrap:wrap;">
            {% if username == 'admin1' %}
                <a href="/admin_game_control" style="background:#38bdf8; color:#000; padding:10px 16px; text-decoration:none; border-radius:10px; font-weight:900;">{{ t.game_control }}</a>
                <a href="/admin_chats" style="background:#38bdf8; color:#000; padding:10px 16px; text-decoration:none; border-radius:10px; font-weight:900;">💬 الدردشة</a>
                <a href="/admin_customers" style="background:#ffd700; color:#000; padding:10px 16px; text-decoration:none; border-radius:10px; font-weight:900;">👥 {{ t.customers }}</a>
                <a href="/admin_accounting" style="background:#ffd700; color:#000; padding:10px 16px; text-decoration:none; border-radius:10px; font-weight:900;">📊 {{ t.accounting }}</a>
            {% endif %}
            <a href="/logout" style="background:#ef4444; color:#fff; padding:10px 16px; text-decoration:none; border-radius:10px; font-weight:900;">{{ t.logout }}</a>
        </div>
    </div>

    <div class="icons-grid">
        <a href="/game_golden_number" class="icon-card"><div style="font-size:55px;">🏆</div><div style="color:#ffd700; font-size:18px; font-weight:900; margin-top:10px;">{{ t.game1 }}</div></a>
        <a href="/game_roulette" class="icon-card"><div style="font-size:55px;">🎰</div><div style="color:#ffd700; font-size:18px; font-weight:900; margin-top:10px;">{{ t.game2 }}</div></a>
        <a href="/game_numbers_empire" class="icon-card"><div style="font-size:55px;">🏛️</div><div style="color:#ffd700; font-size:18px; font-weight:900; margin-top:10px;">{{ t.game3 }}</div></a>
        <a href="/game_number_wheel" class="icon-card"><div style="font-size:55px;">🎡</div><div style="color:#ffd700; font-size:18px; font-weight:900; margin-top:10px;">{{ t.game4 }}</div></a>
        <a href="/game_reveal_and_win" class="icon-card"><div style="font-size:55px;">🎟️</div><div style="color:#ffd700; font-size:18px; font-weight:900; margin-top:10px;">{{ t.game5 }}</div></a>
        <a href="/game_arrow_wheel" class="icon-card"><div style="font-size:55px;">🎯</div><div style="color:#ffd700; font-size:18px; font-weight:900; margin-top:10px;">{{ t.game6 }}</div></a>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['username'] = user.username
            session['balance'] = user.balance
            session['role'] = user.role
            return redirect(url_for('dashboard'))
        else:
            error = 'اسم المستخدم أو كلمة المرور غير صحيحة'
    return render_template_string(LOGIN_PAGE, t=get_t(), error=error)

@app.route('/guest_login')
def guest_login():
    session.clear()
    session['username'] = 'زائر_' + ''.join(random.choices(string.digits, k=4))
    session['balance'] = 100.0  # رصيد ترحيبي تجريبي للزائر
    session['role'] = 'guest'
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    bal = user.balance if user else 0.0
    return render_template_string(DASHBOARD_PAGE, t=get_t(), username=session['username'], balance=bal, lang_bar=get_lang_bar())

# --- مسار اللعبة الأولى: الرقم الحنون ---
@app.route('/game_golden_number', methods=['GET', 'POST'])
def game_golden_number():
    if 'username' not in session: return redirect(url_for('login'))
    username = session['username']
    user = User.query.filter_by(username=username).first()

    if request.method == 'POST':
        action = request.form.get('action_type')
        if action == 'book':
            num = int(request.form.get('number'))
            existing = GoldenNumberBooking.query.filter_by(number=num).first()
            if existing: return jsonify({'success': False, 'msg': 'الرقم محجوز مسبقاً!'})
            if user.balance < 20.0: return jsonify({'success': False, 'msg': 'رصيد غير كافي لشحن الحجز (20 USDD)!'})
            
            user.balance -= 20.0
            vault = SystemVault.query.get(1)
            vault.vault_balance += 20.0
            db.session.add(GoldenNumberBooking(username=username, number=num, booking_date=get_local_time()))
            db.session.add(FinancialLog(action_type='مبيع رهان الرقم الحنون', admin_name='system', target_user=username, amount=20.0, log_time=get_local_time()))
            db.session.commit()
            return jsonify({'success': True})

        elif action == 'cancel':
            num = int(request.form.get('number'))
            booking = GoldenNumberBooking.query.filter_by(number=num, username=username).first()
            if booking:
                user.balance += 20.0
                vault = SystemVault.query.get(1)
                vault.vault_balance -= 20.0
                db.session.delete(booking)
                db.session.commit()
                return jsonify({'success': True})
            return jsonify({'success': False, 'msg': 'حجز غير موجود'})

        elif action == 'admin_draw' and username == 'admin1':
            player_choices = [b.number for b in GoldenNumberBooking.query.all()]
            winning_num = get_unified_math_outcome('الرقم الحنون', player_choices, 1, 50)
            
            winner_booking = GoldenNumberBooking.query.filter_by(number=winning_num).first()
            if winner_booking:
                winner_user = User.query.filter_by(username=winner_booking.username).first()
                if winner_user:
                    winner_user.balance += 700.0
                    vault = SystemVault.query.get(1)
                    vault.vault_balance -= 700.0
                    db.session.add(FinancialLog(action_type='جائزة الرقم الحنون', admin_name='admin1', target_user=winner_user.username, amount=700.0, log_time=get_local_time()))
                    db.session.commit()
            return jsonify({'winning_number': winning_num})

    bookings_list = GoldenNumberBooking.query.all()
    bookings_dict = {b.number: b.username for b in bookings_list}
    my_nums = [b.number for b in bookings_list if b.username == username]
    my_nums_str = ", ".join(map(str, my_nums)) if my_nums else "لا توجد أرقام محجوزة"
    my_total_cost = len(my_nums) * 20.0

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head><meta charset="UTF-8"><title>الرقم الحنون</title>
    <style>
        body { font-family: Tahoma; background: #151928; color: #fff; padding: 15px; text-align: center; }
        .card { background: rgba(25,30,48,0.95); border: 4px solid #ffd700; padding: 25px; border-radius: 30px; max-width: 950px; margin: 10px auto; }
        .grid { display: grid; grid-template-columns: repeat(10, 1fr); gap: 8px; margin-top: 15px; }
        @media(max-width: 768px){ .grid { grid-template-columns: repeat(5, 1fr); } }
        .cell { background: #7c3aed; border: 2px solid #a78bfa; border-radius: 12px; aspect-ratio: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; font-weight: 900; cursor: pointer; color: #fff; font-size: 16px; }
        .cell.booked { background: #7f1d1d; border-color: #ef4444; cursor: not-allowed; }
        .cell.my { background: #1e3a8a; border-color: #3b82f6; }
        .cell.winner-glow { background: #fbbf24 !important; color: #000 !important; border: 3px solid #fff !important; box-shadow: 0 0 25px #ffd700; }
    </style>
    </head>
    <body>
        {{ lang_bar | safe }}
        <div class="card">
            <h2>🏆 احجز رقم ب 20 usdd واربح 700 usdd فورا</h2>
            <div style="background:#000; border:4px solid #ffd700; padding:15px; border-radius:20px; display:inline-block; margin:10px 0;">
                <div id="slotScreen" style="font-size:45px; font-weight:900; color:#ffd700;">--</div>
            </div>
            <div id="winnerAnnouncement" style="font-size:17px; font-weight:900; color:#34d399; min-height:25px;"></div>
            <div class="grid">
                {% for i in range(1, 51) %}
                    {% if i in bookings %}
                        {% if bookings[i] == username %}
                            <button onclick="handleAction('cancel', {{ i }})" class="cell my" id="cell_{{ i }}">{{ i }}<br><span style="font-size:9px;">تراجع</span></button>
                        {% else %}
                            <div class="cell booked" id="cell_{{ i }}">{{ i }}<br><span style="font-size:9px;">{{ bookings[i] }}</span></div>
                        {% endif %}
                    {% else %}
                        <button onclick="handleAction('book', {{ i }})" class="cell" id="cell_{{ i }}">{{ i }}</button>
                    {% endif %}
                {% endfor %}
            </div>
            <div style="background:rgba(15,20,32,0.9); padding:12px; border-radius:15px; margin-top:20px; text-align:right;">
                <p><b>أرقامك:</b> <span style="color:#ffd700;">{{ my_nums_str }}</span> | <b>المخصوم:</b> <span style="color:#38bdf8;">{{ my_total_cost }} USDD</span></p>
            </div>
            {% if username == 'admin1' %}
                <button onclick="triggerDraw()" style="background:#22c55e; color:#fff; font-weight:900; padding:14px 30px; border:none; border-radius:12px; cursor:pointer; font-size:18px; margin-top:15px;">⚡ اسحب الآن (للآدمن)</button>
            {% endif %}
        </div>
        <script>
            function handleAction(actionType, num) {
                let fd = new FormData(); fd.append('action_type', actionType); fd.append('number', num);
                fetch('/game_golden_number', {method:'POST', body:fd}).then(r=>r.json()).then(d=>{
                    if(d.success) location.reload(); else alert(d.msg || "رصيد غير كافي!");
                });
            }
            function triggerDraw() {
                let fd = new FormData(); fd.append('action_type', 'admin_draw');
                fetch('/game_golden_number', {method:'POST', body:fd}).then(r=>r.json()).then(d=>{
                    if(d.winning_number) runAnim(d.winning_number);
                });
            }
            function runAnim(winNum) {
                let screen = document.getElementById('slotScreen');
                let ann = document.getElementById('winnerAnnouncement');
                let c = 0, intv = setInterval(()=>{
                    screen.innerText = '#' + Math.floor(Math.random()*50+1);
                    c++;
                    if(c > 20) {
                        clearInterval(intv);
                        screen.innerText = '#' + winNum;
                        ann.innerText = `مبروك ربحت اصبت الرقم ${winNum}`;
                        document.getElementById('cell_' + winNum).className = "cell winner-glow";
                        setTimeout(()=>location.reload(), 4000);
                    }
                }, 90);
            }
        </script>
    </body>
    </html>
    """, lang_bar=get_lang_bar(), bookings=bookings_dict, username=username, my_nums_str=my_nums_str, my_total_cost=my_total_cost)

# --- مسارات الألعاب الأخرى ولوحات الآدمن والدردشة ---
@app.route('/game_roulette')
def game_roulette():
    if 'username' not in session: return redirect(url_for('login'))
    return f"{get_lang_bar()}<div style='text-align:center; padding:50px; color:#fff; font-family:Tahoma;'><h2>🎰 روليت الحظ</h2><a href='/dashboard' style='color:#ffd700;'>🏠 عودة للرئيسية</a></div>"

@app.route('/game_numbers_empire')
def game_numbers_empire():
    if 'username' not in session: return redirect(url_for('login'))
    return f"{get_lang_bar()}<div style='text-align:center; padding:50px; color:#fff; font-family:Tahoma;'><h2>🏛️ إمبراطورية الأرقام</h2><a href='/dashboard' style='color:#ffd700;'>🏠 عودة للرئيسية</a></div>"

@app.route('/game_number_wheel')
def game_number_wheel():
    if 'username' not in session: return redirect(url_for('login'))
    return f"{get_lang_bar()}<div style='text-align:center; padding:50px; color:#fff; font-family:Tahoma;'><h2>🎡 عجلة الحظ</h2><a href='/dashboard' style='color:#ffd700;'>🏠 عودة للرئيسية</a></div>"

@app.route('/game_reveal_and_win')
def game_reveal_and_win():
    if 'username' not in session: return redirect(url_for('login'))
    return f"{get_lang_bar()}<div style='text-align:center; padding:50px; color:#fff; font-family:Tahoma;'><h2>🎟️ اكشف واربح</h2><a href='/dashboard' style='color:#ffd700;'>🏠 عودة للرئيسية</a></div>"

@app.route('/game_arrow_wheel')
def game_arrow_wheel():
    if 'username' not in session: return redirect(url_for('login'))
    return f"{get_lang_bar()}<div style='text-align:center; padding:50px; color:#fff; font-family:Tahoma;'><h2>🎯 رمي السهم المتحركة</h2><a href='/dashboard' style='color:#ffd700;'>🏠 عودة للرئيسية</a></div>"

@app.route('/admin_game_control', methods=['GET', 'POST'])
def admin_game_control():
    if session.get('username') != 'admin1': return redirect(url_for('dashboard'))
    msg = ""
    if request.method == 'POST':
        game_name = request.form.get('game_name')
        winning_num = int(request.form.get('winning_number'))
        for i in range(1, 51):
            db.session.add(GameFutureDraw(game_name=game_name, round_index=i, winning_number=winning_num))
        db.session.commit()
        msg = f"تم برمجة الـ 50 جولة القادمة للعبة {game_name} بنجاح!"
    return f"{get_lang_bar()}<div style='text-align:center; padding:30px; color:#fff; font-family:Tahoma;'><h2>🎮 غرفة تحكم الألعاب (50 جولة)</h2><p style='color:#34d399;'>{msg}</p><form method='POST'><select name='game_name' style='padding:10px; background:#0a0d16; color:#fff;'><option value='الرقم الحنون'>الرقم الحنون</option><option value='روليت الحظ'>روليت الحظ</option></select><input type='number' name='winning_number' placeholder='الرقم الرابح' required style='padding:10px; margin:10px; background:#0a0d16; color:#fff;'><br><button type='submit' style='background:#ffd700; color:#000; padding:10px 20px; font-weight:bold; border:none; border-radius:8px;'>حفظ الجولات</button></form><br><a href='/dashboard' style='color:#ffd700;'>🏠 عودة للرئيسية</a></div>"

@app.route('/admin_customers', methods=['GET', 'POST'])
def admin_customers():
    if session.get('username') != 'admin1': return redirect(url_for('dashboard'))
    msg = ""
    if request.method == 'POST':
        u = request.form.get('username')
        p = request.form.get('password')
        b = float(request.form.get('balance', 0))
        o = request.form.get('owner_name')
        if not User.query.filter_by(username=u).first():
            db.session.add(User(username=u, password=p, balance=b, owner_name=o, created_by='admin1'))
            db.session.commit()
            msg = "تم إنشاء الحساب بنجاح!"
        else:
            msg = "اسم المستخدم موجود مسبقاً!"
    users = User.query.all()
    return f"{get_lang_bar()}<div style='text-align:center; padding:20px; color:#fff; font-family:Tahoma;'><h2>👥 إدارة الزبائن</h2><p style='color:#34d399;'>{msg}</p><form method='POST'><input type='text' name='username' placeholder='يوزر' required style='padding:8px; margin:5px;'><input type='password' name='password' placeholder='باسورد' required style='padding:8px; margin:5px;'><input type='number' name='balance' placeholder='رصيد' style='padding:8px; margin:5px;'><input type='text' name='owner_name' placeholder='اسم المحل' style='padding:8px; margin:5px;'><br><button type='submit' style='background:#22c55e; color:#000; padding:10px 20px; font-weight:bold;'>إضافة لاعب</button></form><hr><ul style='list-style:none; padding:0;'>" + "".join([f"<li><b>{x.username}</b> ({x.owner_name}) - الرصيد: {x.balance} USDD</li>" for x in users]) + "</ul><a href='/dashboard' style='color:#ffd700;'>🏠 عودة</a></div>"

@app.route('/admin_accounting')
def admin_accounting():
    if session.get('username') != 'admin1': return redirect(url_for('dashboard'))
    vault = SystemVault.query.get(1)
    total_bets = db.session.query(db.func.sum(FinancialLog.amount)).filter(FinancialLog.action_type.like('%مبيع رهان%')).scalar() or 0.0
    total_payouts = db.session.query(db.func.sum(FinancialLog.amount)).filter(FinancialLog.action_type.like('%جائزة%')).scalar() or 0.0
    return f"{get_lang_bar()}<div style='text-align:center; padding:30px; color:#fff; font-family:Tahoma;'><h2>📊 المحاسبة والخزنة</h2><h3>🏦 الخزنة: {vault.vault_balance} USDD</h3><p>إجمالي الواردات: {total_bets} USDD | إجمالي الجوائز: {total_payouts} USDD</p><a href='/dashboard' style='color:#ffd700;'>🏠 عودة للرئيسية</a></div>"

@app.route('/admin_chats')
def admin_chats():
    if session.get('username') != 'admin1': return redirect(url_for('dashboard'))
    chats = ChatMessage.query.all()
    return f"{get_lang_bar()}<div style='text-align:center; padding:30px; color:#fff; font-family:Tahoma;'><h2>💬 لوحة إدارة الدردشة الفورية</h2><ul>" + "".join([f"<li><b>{c.sender}</b>: {c.message}</li>" for c in chats]) + "</ul><a href='/dashboard' style='color:#ffd700;'>🏠 عودة</a></div>"

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
    return f"{get_lang_bar()}<div style='text-align:center; padding:30px; color:#fff; font-family:Tahoma;'><h2>💬 غرفة الدردشة والدعم</h2><form method='POST'><input type='text' name='message' placeholder='اكتب رسالتك للإدارة...' required style='padding:10px; width:60%; background:#0a0d16; color:#fff;'><button type='submit' style='background:#38bdf8; color:#000; padding:10px 20px; font-weight:bold;'>إرسال</button></form><hr><div style='max-width:600px; margin:auto; text-align:right;'>" + "".join([f"<p><b>{c.sender}:</b> {c.message}</p>" for c in chats]) + "</div><a href='/dashboard' style='color:#ffd700;'>🏠 عودة</a></div>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
