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

class GameDrawState(db.Model):
    __tablename__ = 'game_draw_state'
    id = db.Column(db.Integer, primary_key=True)
    winning_number = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='idle')
    draw_end_time = db.Column(db.Float, default=0)
    forced_winning_number = db.Column(db.Integer, default=0)

class UserLastBet(db.Model):
    __tablename__ = 'user_last_bets'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    bets_json = db.Column(db.Text, nullable=False)

class LuxuryGoldenBooking(db.Model):
    __tablename__ = 'luxury_golden_bookings'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80))
    box_number = db.Column(db.Integer)
    booking_date = db.Column(db.String(50))

class LuxuryGoldenState(db.Model):
    __tablename__ = 'luxury_golden_state'
    id = db.Column(db.Integer, primary_key=True)
    winning_number = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='idle')
    draw_end_time = db.Column(db.Float, default=0)
    forced_winning_number = db.Column(db.Integer, default=0)

# --- تهيئة الجداول وحفظ البيانات تماماً من الحذف ---
with app.app_context():
    db.create_all()
    vault = SystemVault.query.get(1)
    if not vault:
        db.session.add(SystemVault(id=1, vault_balance=1000000.0))
    
    if not User.query.filter_by(username='admin1').first():
        db.session.add(User(username='admin1', password='admin123', balance=0.0, role='admin', created_by='system', owner_name='المشرف العام'))

    if not GameDrawState.query.get(1):
        db.session.add(GameDrawState(id=1, winning_number=0, status='idle', draw_end_time=0, forced_winning_number=0))
    if not LuxuryGoldenState.query.get(1):
        db.session.add(LuxuryGoldenState(id=1, winning_number=0, status='idle', draw_end_time=0, forced_winning_number=0))
    db.session.commit()

# --- قاموس الترجمات الشامل للغات الست ---
TRANSLATIONS = {
    'ar': {
        'dir': 'rtl', 'title': 'امبراطورية الأرقام', 'subtitle': 'منصة الألعاب التفاعلية الفائقة 9D',
        'login': 'دخول للبرنامج', 'username': 'اسم المستخدم', 'password': 'كلمة المرور', 'balance': 'الرصيد',
        'recharge': 'شحن رصيد', 'withdraw': 'سحب رصيد', 'change_pass': 'تغيير الباسورد', 'logout': 'خروج',
        'dashboard': 'لوحة التحكم', 'back_dash': '⬅️ العودة للوحة التحكم',
        'withdraw_warning': '⚠️ تنبيه: يتم خصم 10% رسوم تحويل من رصيدك.',
        'wish_withdraw': 'سحب عبر Wish Money', 'visa_withdraw': 'سحب عبر Visa مسبقة الدفع', 'usdt_withdraw': 'قبض عبر USDT',
        'success_msg': 'سنقوم بمراجعة طلبك في غضون دقيقة إلى 120 دقيقة وسيتم التحويل فوراً. أهلاً بكم، سررنا بانضمامكم إلينا!',
        'game1': 'الرقم الحنون', 'game2': 'روليت الحظ', 'game3': 'إمبراطورية الأرقام',
        'game4': 'عجلة الأرقام', 'game5': 'اكشف واربح', 'game6': 'الرقم الحنون الفاخر',
        'cost': 'التكلفة', 'prize': 'الجائزة', 'book': 'حجز', 'cancel': 'تراجع', 'booked': 'محجوز',
        'spin': 'تدوير العجلة', 'reveal': 'اكشف الصناديق', 'draw_now': 'اسحب الآن (للآدمن)'
    },
    'en': {
        'dir': 'ltr', 'title': 'Empire of Numbers', 'subtitle': 'The Ultimate 9D Interactive Platform',
        'login': 'Login', 'username': 'Username', 'password': 'Password', 'balance': 'Balance',
        'recharge': 'Recharge Balance', 'withdraw': 'Withdraw Balance', 'change_pass': 'Change Password', 'logout': 'Logout',
        'dashboard': 'Dashboard', 'back_dash': '⬅️ Back to Dashboard',
        'withdraw_warning': '⚠️ Notice: A 10% transfer fee will be deducted from your balance.',
        'wish_withdraw': 'Withdraw via Wish Money', 'visa_withdraw': 'Withdraw via Prepaid Visa', 'usdt_withdraw': 'Receive via USDT',
        'success_msg': 'We will review your request within 1 to 120 minutes and transfer immediately. Welcome!',
        'game1': 'Golden Number', 'game2': 'Lucky Roulette', 'game3': 'Numbers Empire',
        'game4': 'Wheel of Numbers', 'game5': 'Reveal & Win', 'game6': 'Luxury Golden Box',
        'cost': 'Cost', 'prize': 'Prize', 'book': 'Book', 'cancel': 'Cancel', 'booked': 'Booked',
        'spin': 'Spin Wheel', 'reveal': 'Reveal Boxes', 'draw_now': 'Draw Now (Admin)'
    },
    'fr': {
        'dir': 'ltr', 'title': 'Empire des Nombres', 'subtitle': 'Plateforme Interactive 9D',
        'login': 'Connexion', 'username': "Nom d'utilisateur", 'password': 'Mot de passe', 'balance': 'Solde',
        'recharge': 'Recharger', 'withdraw': 'Retirer', 'change_pass': 'Changer le mot de passe', 'logout': 'Déconnexion',
        'dashboard': 'Tableau de bord', 'back_dash': '⬅️ Retour au tableau de bord',
        'withdraw_warning': '⚠️ Avis : Frais de transfert 10%.',
        'wish_withdraw': 'Retrait Wish Money', 'visa_withdraw': 'Retrait Visa', 'usdt_withdraw': 'Recevoir USDT',
        'success_msg': 'Nous examinerons votre demande en 1 à 120 minutes.',
        'game1': 'Numéro d’Or', 'game2': 'Roulette de la Chance', 'game3': 'Empire des Nombres',
        'game4': 'Roue des Nombres', 'game5': 'Révéler & Gagner', 'game6': 'Boîte Dorée de Luxe',
        'cost': 'Coût', 'prize': 'Prix', 'book': 'Réserver', 'cancel': 'Annuler', 'booked': 'Réservé',
        'spin': 'Tourner la roue', 'reveal': 'Révéler les boîtes', 'draw_now': 'Tirage (Admin)'
    },
    'fa': {
        'dir': 'rtl', 'title': 'امپراتوری اعداد', 'subtitle': 'پلتفرم فوق پیشرفته 9D',
        'login': 'ورود به برنامه', 'username': 'نام کاربری', 'password': 'رمز عبور', 'balance': 'موجودی',
        'recharge': 'شارژ حساب', 'withdraw': 'برداشت وجه', 'change_pass': 'تغییر رمز عبور', 'logout': 'خروج',
        'dashboard': 'داشبورد', 'back_dash': '⬅️ بازگشت به داشبورد',
        'withdraw_warning': '⚠️ توجه: ۱۰٪ کارمزد انتقال.',
        'wish_withdraw': 'برداشت Wish Money', 'visa_withdraw': 'برداشت ویزا کارت', 'usdt_withdraw': 'دریافت USDT',
        'success_msg': 'درخواست شما بررسی و واریز خواهد شد.',
        'game1': 'شماره طلایی', 'game2': 'رولت شانس', 'game3': 'امپراتوری اعداد',
        'game4': 'گردونه اعداد', 'game5': 'بگشای و ببر', 'game6': 'صندوق طلایی لوکس',
        'cost': 'هزینه', 'prize': 'جایزه', 'book': 'رزرو', 'cancel': 'لغو', 'booked': 'رزرو شده',
        'spin': 'چرخش گردونه', 'reveal': 'باز کردن جعبه‌ها', 'draw_now': 'قرعه‌کشی (مدیر)'
    },
    'es': {
        'dir': 'ltr', 'title': 'Imperio de los Números', 'subtitle': 'Plataforma Interactiva 9D',
        'login': 'Iniciar Sesión', 'username': 'Usuario', 'password': 'Contraseña', 'balance': 'Saldo',
        'recharge': 'Recargar Saldo', 'withdraw': 'Retirar Saldo', 'change_pass': 'Cambiar Contraseña', 'logout': 'Cerrar Sesión',
        'dashboard': 'Panel Principal', 'back_dash': '⬅️ Volver al Panel',
        'withdraw_warning': '⚠️ Aviso: Comisión del 10%.',
        'wish_withdraw': 'Retirar Wish Money', 'visa_withdraw': 'Retirar Visa', 'usdt_withdraw': 'Recibir USDT',
        'success_msg': 'Revisaremos su solicitud en 1 a 120 minutos.',
        'game1': 'Número de Oro', 'game2': 'Ruleta de la Suerte', 'game3': 'Imperio de Números',
        'game4': 'Rueda de Números', 'game5': 'Descubre y Gana', 'game6': 'Caja Dorada de Lujo',
        'cost': 'Costo', 'prize': 'Premio', 'book': 'Reservar', 'cancel': 'Cancelar', 'booked': 'Reservado',
        'spin': 'Girar Ruleta', 'reveal': 'Destapar Cajas', 'draw_now': 'Sorteo (Admin)'
    },
    'de': {
        'dir': 'ltr', 'title': 'Imperium der Zahlen', 'subtitle': 'Die 9D Gaming-Plattform',
        'login': 'Anmelden', 'username': 'Benutzername', 'password': 'Passwort', 'balance': 'Guthaben',
        'recharge': 'Guthaben aufladen', 'withdraw': 'Guthaben abheben', 'change_pass': 'Passwort ändern', 'logout': 'Abmelden',
        'dashboard': 'Dashboard', 'back_dash': '⬅️ Zurück zum Dashboard',
        'withdraw_warning': '⚠️ Hinweis: 10% Gebühr.',
        'wish_withdraw': 'Wish Money', 'visa_withdraw': 'Prepaid Visa', 'usdt_withdraw': 'USDT',
        'success_msg': 'Wir prüfen Ihre Anfrage in 1 bis 120 Minuten.',
        'game1': 'Goldene Nummer', 'game2': 'Glücksroulette', 'game3': 'Zahlenimperium',
        'game4': 'Zahlenrad', 'game5': 'Aufdecken & Gewinnen', 'game6': 'Goldene Luxusbox',
        'cost': 'Kosten', 'prize': 'Gewinn', 'book': 'Buchen', 'cancel': 'Abbrechen', 'booked': 'Gebucht',
        'spin': 'Rad drehen', 'reveal': 'Boxen aufdecken', 'draw_now': 'Ziehung (Admin)'
    }
}

def get_t():
    lang = session.get('lang', 'ar')
    return TRANSLATIONS.get(lang, TRANSLATIONS['ar'])

# --- شريط اللغات العام بتصميم زجاجي فاخر ---
LANG_BAR = """
<div style="padding: 12px 25px; background: rgba(18, 18, 25, 0.95); backdrop-filter: blur(15px); display: flex; gap: 15px; justify-content: flex-end; border-bottom: 1px solid rgba(255,215,0,0.2); box-shadow: 0 4px 20px rgba(0,0,0,0.5);">
    <a href="/set_lang/ar" style="color:#ffd700; text-decoration:none; font-weight:bold; font-size:14px; text-shadow:0 0 10px rgba(255,215,0,0.5);">العربية</a> |
    <a href="/set_lang/en" style="color:#38bdf8; text-decoration:none; font-weight:bold; font-size:14px; text-shadow:0 0 10px rgba(56,189,248,0.5);">English</a> |
    <a href="/set_lang/fr" style="color:#f472b6; text-decoration:none; font-weight:bold; font-size:14px; text-shadow:0 0 10px rgba(244,114,182,0.5);">Français</a> |
    <a href="/set_lang/fa" style="color:#34d399; text-decoration:none; font-weight:bold; font-size:14px; text-shadow:0 0 10px rgba(52,211,153,0.5);">فارسی</a> |
    <a href="/set_lang/es" style="color:#fbbf24; text-decoration:none; font-weight:bold; font-size:14px; text-shadow:0 0 10px rgba(251,191,36,0.5);">Español</a> |
    <a href="/set_lang/de" style="color:#a78bfa; text-decoration:none; font-weight:bold; font-size:14px; text-shadow:0 0 10px rgba(167,139,250,0.5);">Deutsch</a>
</div>
"""

# --- مسارات التطبيق (Routes) ---

@app.route('/set_lang/<lang>')
def set_lang(lang):
    if lang in TRANSLATIONS:
        session['lang'] = lang
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/manifest.json')
def manifest():
    return jsonify({"name": "Empire of Numbers 9D", "short_name": "Empire9D", "start_url": "/", "display": "standalone", "background_color": "#0b0f19", "theme_color": "#ffd700"})

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

@app.route('/api/golden_status')
def api_golden_status():
    current_time = time.time()
    draw_state = GameDrawState.query.get(1)
    status, winning_number, remaining, winner_username = 'idle', 0, 0, '---'
    if draw_state:
        status = draw_state.status
        winning_number = draw_state.winning_number
        if status == 'finished':
            log = FinancialLog.query.filter_by(action_type='جائزة الرقم الحنون').order_by(FinancialLog.id.desc()).first()
            if log:
                winner_username = log.target_user
        if status == 'finished' and current_time >= draw_state.draw_end_time:
            GoldenNumberBooking.query.delete()
            draw_state.winning_number, draw_state.status, draw_state.draw_end_time = 0, 'idle', 0
            db.session.commit()
            status, winning_number = 'idle', 0
        remaining = max(0, int(draw_state.draw_end_time - current_time)) if status == 'finished' else 0
    bookings = {b.number: b.username for b in GoldenNumberBooking.query.all()}
    
    username = session.get('username', '')
    user = User.query.filter_by(username=username).first() if username else None
    my_booked = [b.number for b in GoldenNumberBooking.query.filter_by(username=username).all()] if username else []
    
    return jsonify({
        "status": status,
        "winning_number": winning_number,
        "winner_username": winner_username,
        "remaining_seconds": remaining,
        "bookings": bookings,
        "my_booked_nums": my_booked,
        "my_total_spent": len(my_booked) * 2.0,
        "balance": user.balance if user else 0.0
    })

@app.route('/api/luxury_golden_status')
def api_luxury_golden_status():
    current_time = time.time()
    l_state = LuxuryGoldenState.query.get(1)
    status, winning_number = 'idle', 0
    if l_state:
        status, winning_number = l_state.status, l_state.winning_number
        if status == 'finished' and current_time >= l_state.draw_end_time:
            LuxuryGoldenBooking.query.delete()
            l_state.winning_number, l_state.status, l_state.draw_end_time = 0, 'idle', 0
            db.session.commit()
            status, winning_number = 'idle', 0
    bookings = {b.box_number: b.username for b in LuxuryGoldenBooking.query.all()}
    return jsonify({"status": status, "winning_number": winning_number, "bookings": bookings})

# --- الألعاب الست بصيغة 9D الفائقة ---

@app.route('/game_golden_number', methods=['GET', 'POST'])
def game_golden_number():
    if 'username' not in session: return redirect(url_for('login'))
    username = session['username']
    user = User.query.filter_by(username=username).first()
    vault = SystemVault.query.get(1)
    draw_state = GameDrawState.query.get(1)
    t = get_t()
    msg = None
    if request.method == 'POST':
        action_type = request.form.get('action_type')
        if action_type == 'book' and draw_state.status == 'idle':
            number = int(request.form.get('number', 0))
            if user.balance >= 2.0 and not GoldenNumberBooking.query.filter_by(number=number).first():
                user.balance -= 2.0
                vault.vault_balance += 2.0
                db.session.add(FinancialLog(action_type='مبيع رهان لعبة الرقم الحنون', admin_name='system', target_user=username, amount=2.0, log_time=get_local_time()))
                db.session.add(GoldenNumberBooking(username=username, number=number, booking_date=get_local_time()))
                db.session.commit()
                return jsonify({"success": True, "msg": f"تم حجز الرقم {number} مقابل 2 USDD!"})
            else:
                return jsonify({"success": False, "msg": "رصيد غير كافي أو الرقم محجوز مسبقاً!"})
        elif action_type == 'cancel' and draw_state.status == 'idle':
            number = int(request.form.get('number', 0))
            b = GoldenNumberBooking.query.filter_by(number=number, username=username).first()
            if b:
                db.session.delete(b)
                user.balance += 2.0
                vault.vault_balance -= 2.0
                db.session.add(FinancialLog(action_type='استرجاع رهان الرقم الحنون', admin_name='system', target_user=username, amount=2.0, log_time=get_local_time()))
                db.session.commit()
                return jsonify({"success": True, "msg": "تم التراجع واسترداد 2 USDD!"})
        elif action_type == 'admin_draw' and username == 'admin1':
            bookings = GoldenNumberBooking.query.all()
            booked_nums = [b.number for b in bookings]
            if booked_nums:
                winning_num = draw_state.forced_winning_number if (draw_state.forced_winning_number in booked_nums) else random.choice(booked_nums)
                winner_b = GoldenNumberBooking.query.filter_by(number=winning_num).first()
                winner_u = User.query.filter_by(username=winner_b.username).first()
                winner_u.balance += 75.0
                vault.vault_balance -= 75.0
                db.session.add(FinancialLog(action_type='جائزة الرقم الحنون', admin_name='admin1', target_user=winner_u.username, amount=75.0, log_time=get_local_time()))
                draw_state.winning_number, draw_state.status, draw_state.draw_end_time = winning_num, 'finished', time.time() + 20.0
                db.session.commit()
                return jsonify({"success": True, "msg": f"Winner: {winner_u.username} (#{winning_num})"})

    bookings = {b.number: b.username for b in GoldenNumberBooking.query.all()}
    my_nums = [b.number for b in GoldenNumberBooking.query.filter_by(username=username).all()]
    return render_template_string(GAME_GOLDEN_PAGE, t=t, username=username, balance=user.balance, bookings=bookings, winning_number=draw_state.winning_number, draw_status=draw_state.status, my_booked_nums=my_nums, my_total_spent=len(my_nums)*2.0, msg=msg)

@app.route('/game_numbers_empire', methods=['GET', 'POST'])
def game_numbers_empire():
    if 'username' not in session: return redirect(url_for('login'))
    username = session['username']
    user = User.query.filter_by(username=username).first()
    vault = SystemVault.query.get(1)
    t = get_t()
    msg = None
    if request.method == 'POST':
        if 'book_number' in request.form:
            num = int(request.form.get('number', 0))
            if user.balance >= 2.0 and not NumbersEmpireBooking.query.filter_by(number=num).first():
                user.balance -= 2.0
                vault.vault_balance += 2.0
                db.session.add(FinancialLog(action_type='مبيع رهان إمبراطورية الأرقام', admin_name='system', target_user=username, amount=2.0, log_time=get_local_time()))
                db.session.add(NumbersEmpireBooking(username=username, number=num, booking_date=get_local_time()))
                db.session.commit()
                msg = f"تم حجز الرقم #{num} بنجاح!"
        elif 'cancel_number' in request.form:
            num = int(request.form.get('number', 0))
            b = NumbersEmpireBooking.query.filter_by(number=num, username=username).first()
            if b:
                db.session.delete(b)
                user.balance += 2.0
                vault.vault_balance -= 2.0
                db.session.add(FinancialLog(action_type='استرجاع رهان إمبراطورية الأرقام', admin_name='system', target_user=username, amount=2.0, log_time=get_local_time()))
                db.session.commit()
                msg = "تم التراجع واسترداد 2 USDD!"
    bookings = {b.number: b.username for b in NumbersEmpireBooking.query.all()}
    my_nums = [b.number for b in NumbersEmpireBooking.query.filter_by(username=username).all()]
    return render_template_string(GAME_NUMBERS_EMPIRE_PAGE, t=t, username=username, balance=user.balance, bookings=bookings, my_booked_nums=my_nums, my_total_spent=len(my_nums)*2.0, msg=msg)

@app.route('/game_roulette', methods=['GET', 'POST'])
def game_roulette():
    if 'username' not in session: return redirect(url_for('login'))
    username = session['username']
    user = User.query.filter_by(username=username).first()
    vault = SystemVault.query.get(1)
    t = get_t()
    msg, last_win_data = None, None
    if request.method == 'POST':
        try:
            bets_json = request.form.get('bets_data')
            total_bet = float(request.form.get('total_bet_amount', 0))
            if total_bet > 0 and user.balance >= total_bet:
                user.balance -= total_bet
                vault.vault_balance += total_bet
                db.session.add(FinancialLog(action_type='مبيع رهان روليت 9D', admin_name='system', target_user=username, amount=total_bet, log_time=get_local_time()))
                winning_num = random.randint(0, 36)
                reds = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
                color = 'green' if winning_num == 0 else ('red' if winning_num in reds else 'black')
                bets = json.loads(bets_json)
                payout = 0
                for bet in bets:
                    if bet['type'] == 'straight' and int(bet['value']) == winning_num: payout += (bet['amount'] * 35) + bet['amount']
                    elif bet['type'] == 'color' and bet['value'] == color: payout += (bet['amount'] * 1) + bet['amount']
                if payout > 0:
                    user.balance += payout
                    vault.vault_balance -= payout
                    db.session.add(FinancialLog(action_type='جائزة روليت 9D', admin_name='system', target_user=username, amount=payout, log_time=get_local_time()))
                db.session.commit()
                last_win_data = {"winning_number": winning_num, "winning_color": color, "total_bet": total_bet, "total_payout": payout}
                msg = f"Winner: {winning_num} ({color}) | Payout: {payout} USDD"
        except Exception as e: msg = f"Error: {str(e)}"
    last_bets = UserLastBet.query.filter_by(username=username).first()
    return render_template_string(GAME_ROULETTE_PAGE, t=t, username=username, balance=user.balance, msg=msg, last_win_data=last_win_data, last_bets_json=last_bets.bets_json if last_bets else "[]")

@app.route('/game_number_wheel', methods=['GET', 'POST'])
def game_number_wheel():
    if 'username' not in session: return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    vault = SystemVault.query.get(1)
    t = get_t()
    msg, winning_num, is_win = None, None, False
    if request.method == 'POST':
        nums = json.loads(request.form.get('selected_numbers', '[]'))
        if nums and user.balance >= len(nums):
            bet_amt = float(len(nums))
            user.balance -= bet_amt
            vault.vault_balance += bet_amt
            db.session.add(FinancialLog(action_type='مبيع رهان عجلة الأرقام 9D', admin_name='system', target_user=user.username, amount=bet_amt, log_time=get_local_time()))
            winning_num = random.randint(1, 20)
            if winning_num in nums:
                is_win = True
                user.balance += 15.0
                vault.vault_balance -= 15.0
                db.session.add(FinancialLog(action_type='جائزة عجلة الأرقام 9D', admin_name='system', target_user=user.username, amount=15.0, log_time=get_local_time()))
                msg = f"Win! #{winning_num}"
            else: msg = f"Loss! #{winning_num}"
            db.session.commit()
    return render_template_string(GAME_NUMBER_WHEEL_PAGE, t=t, balance=user.balance, msg=msg, winning_num=winning_num, is_win=is_win)

@app.route('/game_reveal_and_win', methods=['GET', 'POST'])
def game_reveal_and_win():
    if 'username' not in session: return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    vault = SystemVault.query.get(1)
    t = get_t()
    msg, result_data = None, None
    if request.method == 'POST':
        if user.balance >= 1.0:
            user.balance -= 1.0
            vault.vault_balance += 1.0
            db.session.add(FinancialLog(action_type='مبيع رهان اكشف واربح 9D', admin_name='system', target_user=user.username, amount=1.0, log_time=get_local_time()))
            items = ['1', '3', '5', '7', '🦁']
            rev = random.sample(items, 3)
            prize = 20.0 if rev[0] == rev[1] == rev[2] else 0.0
            if prize > 0:
                user.balance += prize
                vault.vault_balance -= prize
                db.session.add(FinancialLog(action_type='جائزة اكشف واربح 9D', admin_name='system', target_user=user.username, amount=prize, log_time=get_local_time()))
                msg = f"Win {prize} USDD!"
            else: msg = "Try Again!"
            db.session.commit()
            result_data = {'revealed': {0: rev[0], 1: rev[1], 2: rev[2]}, 'prize': prize}
    return render_template_string(GAME_REVEAL_AND_WIN_PAGE, t=t, balance=user.balance, msg=msg, result_data=result_data)

@app.route('/game_golden_boxes_new', methods=['GET', 'POST'])
def game_golden_boxes_new():
    if 'username' not in session: return redirect(url_for('login'))
    username = session['username']
    user = User.query.filter_by(username=username).first()
    vault = SystemVault.query.get(1)
    l_state = LuxuryGoldenState.query.get(1)
    t = get_t()
    msg = None
    if request.method == 'POST':
        if 'book_box' in request.form:
            box = int(request.form.get('box_number'))
            if user.balance >= 50.0 and not LuxuryGoldenBooking.query.filter_by(box_number=box).first():
                user.balance -= 50.0
                vault.vault_balance += 50.0
                db.session.add(FinancialLog(action_type='مبيع رهان الرقم الفاخر 9D', admin_name='system', target_user=username, amount=50.0, log_time=get_local_time()))
                db.session.add(LuxuryGoldenBooking(username=username, box_number=box, booking_date=get_local_time()))
                db.session.commit()
                msg = f"Box #{box} (50 USDD)"
        elif 'admin_execute_luxury_draw' in request.form and username == 'admin1':
            books = LuxuryGoldenBooking.query.all()
            if books:
                box = random.choice([b.box_number for b in books])
                winner = LuxuryGoldenBooking.query.filter_by(box_number=box).first()
                w_user = User.query.filter_by(username=winner.username).first()
                w_user.balance += 200.0
                vault.vault_balance -= 200.0
                db.session.add(FinancialLog(action_type='جائزة الرقم الفاخر 9D', admin_name='admin1', target_user=w_user.username, amount=200.0, log_time=get_local_time()))
                l_state.winning_number, l_state.status, l_state.draw_end_time = box, 'finished', time.time() + 15.0
                db.session.commit()
                msg = f"Winner Box #{box} : {w_user.username}"
    bookings = {b.box_number: b.username for b in LuxuryGoldenBooking.query.all()}
    my_boxes = [b.box_number for b in LuxuryGoldenBooking.query.filter_by(username=username).all()]
    return render_template_string(GAME_GOLDEN_BOXES_NEW_PAGE, t=t, username=username, balance=user.balance, bookings=bookings, winning_number=l_state.winning_number, draw_status=l_state.status, my_booked_boxes=my_boxes, my_total_spent=len(my_boxes)*50.0, msg=msg)

@app.route('/admin_customers', methods=['GET', 'POST'])
def admin_customers():
    if 'username' not in session or session.get('username') != 'admin1': return redirect(url_for('dashboard'))
    t = get_t()
    msg = None
    if request.method == 'POST' and request.form.get('action') == 'create_user':
        uname, pwd, owner = request.form.get('new_username', '').strip(), request.form.get('new_password', '').strip(), request.form.get('new_owner', '').strip()
        if not User.query.filter_by(username=uname).first():
            db.session.add(User(username=uname, password=pwd, balance=0.0, role='player', created_by='admin1', owner_name=owner))
            db.session.commit()
            msg = f"Created: {uname}"
        else: msg = "Username exists!"
    return render_template_string(ADMIN_CUSTOMERS_PAGE, t=t, users_list=User.query.all(), msg=msg)

@app.route('/admin_customer_detail/<username>')
def admin_customer_detail(username):
    if 'username' not in session or session.get('username') != 'admin1': return redirect(url_for('dashboard'))
    t = get_t()
    user = User.query.filter_by(username=username).first()
    return render_template_string(ADMIN_CUSTOMER_DETAIL_PAGE, t=t, user=user, logs=FinancialLog.query.filter_by(target_user=username).order_by(FinancialLog.id.desc()).all(), golden_bookings=GoldenNumberBooking.query.filter_by(username=username).all(), empire_bookings=NumbersEmpireBooking.query.filter_by(username=username).all(), luxury_bookings=LuxuryGoldenBooking.query.filter_by(username=username).all())

@app.route('/admin_games', methods=['GET', 'POST'])
def admin_games():
    if 'username' not in session or session.get('username') != 'admin1': return redirect(url_for('dashboard'))
    draw_state = GameDrawState.query.get(1)
    t = get_t()
    msg = None
    if request.method == 'POST':
        draw_state.forced_winning_number = int(request.form.get('forced_winning_number', 0))
        db.session.commit()
        msg = "Updated!"
    return render_template_string(ADMIN_GAMES_PAGE, t=t, forced_val=draw_state.forced_winning_number, msg=msg)

@app.route('/admin_accounting', methods=['GET', 'POST'])
def admin_accounting():
    if 'username' not in session or session.get('username') != 'admin1': return redirect(url_for('dashboard'))
    vault = SystemVault.query.get(1)
    t = get_t()
    msg = None
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'generate_card':
            amount = float(request.form.get('card_amount', 0))
            code = f"EMP-{int(amount)}-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            db.session.add(RechargeCard(code=code, amount=amount, is_used=False, created_at=get_local_time()))
            db.session.commit()
            msg = f"Generated: {code}"
        elif action == 'sell_currency':
            target, amount = request.form.get('target_user'), float(request.form.get('amount', 0))
            if vault.vault_balance >= amount:
                vault.vault_balance -= amount
                User.query.filter_by(username=target).first().balance += amount
                db.session.add(FinancialLog(action_type='بيع عملات للزبون', admin_name='admin1', target_user=target, amount=amount, log_time=get_local_time()))
                db.session.commit()
                msg = "Done!"
        elif action == 'buy_back_currency':
            target, amount = request.form.get('target_user'), float(request.form.get('amount', 0))
            u = User.query.filter_by(username=target).first()
            if u and u.balance >= amount:
                u.balance -= amount
                vault.vault_balance += amount
                db.session.add(FinancialLog(action_type='استرجاع رصيد للخزنة', admin_name='admin1', target_user=target, amount=amount, log_time=get_local_time()))
                db.session.commit()
                msg = "Done!"

    logs = FinancialLog.query.order_by(FinancialLog.id.desc()).all()
    tp_sold = db.session.query(db.func.sum(FinancialLog.amount)).filter(FinancialLog.action_type.in_(['بيع عملات للزبون', 'شحن عبر بطاقة كود'])).scalar() or 0.0
    tg_bets = db.session.query(db.func.sum(FinancialLog.amount)).filter(FinancialLog.action_type.like('%مبيع رهان%')).scalar() or 0.0
    tpayouts = db.session.query(db.func.sum(FinancialLog.amount)).filter(FinancialLog.action_type.like('%جائزة%')).scalar() or 0.0
    net = tg_bets - tpayouts
    return render_template_string(ADMIN_ACCOUNTING_PAGE, t=t, vault_balance=vault.vault_balance, logs=logs, total_points_sold=tp_sold, total_game_bets=tg_bets, total_payouts=tpayouts, net_game_result=net, users_list=User.query.all(), cards_list=RechargeCard.query.order_by(RechargeCard.id.desc()).all(), msg=msg)


# --- قوالب HTML بتصميم 9D الفائق (Ultra-3D Glassmorphism & Neon) ---

LOGIN_PAGE = LANG_BAR + """
<!DOCTYPE html>
<html lang="{{ t.dir }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><title>{{ t.title }} - 9D</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: radial-gradient(circle at center, #1a1c29 0%, #0b0f19 100%); color: #f8fafc; display: flex; justify-content: center; align-items: center; height: 90vh; margin: 0; flex-direction: column; overflow: hidden; }
        .login-box { background: rgba(20, 24, 38, 0.85); backdrop-filter: blur(25px); padding: 50px; border-radius: 25px; width: 380px; text-align: center; border: 2px solid rgba(255,215,0,0.5); box-shadow: 0 30px 60px rgba(0,0,0,0.9), inset 0 0 20px rgba(255,215,0,0.2); transform: perspective(1000px) rotateX(8deg); }
        input { width: 100%; padding: 15px; margin: 12px 0; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); background: rgba(10, 13, 22, 0.8); color: white; box-sizing: border-box; font-size: 16px; outline: none; transition: 0.3s; }
        input:focus { border-color: #ffd700; box-shadow: 0 0 15px rgba(255,215,0,0.4); }
        button { width: 100%; padding: 15px; background: linear-gradient(135deg, #ffd700, #ff8c00); color: #000; font-weight: 900; border: none; border-radius: 12px; cursor: pointer; margin-top: 15px; font-size: 18px; box-shadow: 0 10px 30px rgba(255,215,0,0.5); transition: 0.3s; }
        button:hover { transform: translateY(-3px); box-shadow: 0 15px 35px rgba(255,215,0,0.8); }
        .error { color: #ef4444; margin-bottom: 15px; font-weight: bold; background: rgba(239,68,68,0.15); padding: 10px; border-radius: 8px; border: 1px solid #ef4444; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2 style="color: #ffd700; margin-top: 0; text-shadow: 0 0 20px rgba(255,215,0,0.6);">👑 {{ t.title }}</h2>
        <p style="color: #94a3b8; font-size: 13px; letter-spacing: 1px;">{{ t.subtitle }}</p>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="{{ t.username }}" required>
            <input type="password" name="password" placeholder="{{ t.password }}" required>
            <button type="submit">{{ t.login }}</button>
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
    <title>{{ t.dashboard }} - 9D</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: radial-gradient(circle at center, #151928 0%, #070a12 100%); color: #fff; margin: 0; padding: 20px; min-height: 100vh; }
        .header { display: flex; justify-content: space-between; align-items: center; background: rgba(20, 24, 38, 0.9); backdrop-filter: blur(20px); padding: 18px 30px; border-radius: 18px; border-bottom: 3px solid #ffd700; flex-wrap: wrap; gap: 15px; box-shadow: 0 15px 35px rgba(0,0,0,0.7); }
        .financial-bar { display: flex; justify-content: space-between; max-width: 950px; margin: 30px auto; gap: 20px; }
        .fin-card { flex: 1; background: linear-gradient(145deg, rgba(24,34,50,0.9), rgba(15,23,42,0.9)); backdrop-filter: blur(15px); border: 2px solid rgba(56,189,248,0.5); padding: 22px; border-radius: 20px; text-align: center; transform: perspective(1000px) rotateX(4deg); box-shadow: 0 20px 40px rgba(0,0,0,0.8); transition: 0.3s; }
        .fin-card:hover { transform: perspective(1000px) rotateX(0deg) translateY(-5px); border-color: #38bdf8; box-shadow: 0 25px 50px rgba(56,189,248,0.4); }
        .fin-card button { background: linear-gradient(135deg, #38bdf8, #0284c7); color: #070a12; padding: 14px 22px; font-weight: 900; border: none; border-radius: 12px; cursor: pointer; margin-top: 12px; font-size: 16px; width: 100%; box-shadow: 0 8px 20px rgba(56,189,248,0.4); transition: 0.3s; }
        .fin-card button:hover { transform: scale(1.02); }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(5, 7, 12, 0.9); backdrop-filter: blur(10px); justify-content: center; align-items: center; z-index: 1000; }
        .modal-content { background: rgba(25, 30, 48, 0.95); backdrop-filter: blur(20px); padding: 35px; border-radius: 22px; border: 3px solid #ffd700; width: 440px; text-align: center; position: relative; box-shadow: 0 30px 70px rgba(0,0,0,0.9); }
        .icons-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 30px; max-width: 1000px; margin: 40px auto; }
        @media (max-width: 900px) { .icons-grid { grid-template-columns: repeat(2, 1fr); } }
        .icon-card { background: linear-gradient(145deg, rgba(25,30,48,0.95), rgba(12,15,25,0.95)); border: 3px solid rgba(184,134,11,0.6); border-radius: 28px; padding: 35px 20px; text-align: center; text-decoration: none; transform: perspective(1200px) rotateX(10deg) translateZ(15px); box-shadow: 0 20px 45px rgba(0,0,0,0.9), inset 0 0 15px rgba(255,215,0,0.1); transition: 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
        .icon-card:hover { border-color: #ffd700; transform: perspective(1200px) rotateX(0deg) translateY(-12px) scale(1.05); box-shadow: 0 30px 70px rgba(255,215,0,0.4), inset 0 0 25px rgba(255,215,0,0.3); }
        .icon-logo { font-size: 75px; margin-bottom: 15px; filter: drop-shadow(0 10px 20px rgba(0,0,0,0.9)); transition: 0.3s; }
        .icon-card:hover .icon-logo { transform: scale(1.15) rotate(5deg); }
        .icon-title { color: #ffd700; font-size: 21px; font-weight: 900; text-shadow: 0 3px 10px rgba(0,0,0,0.9); letter-spacing: 0.5px; }
    </style>
</head>
<body>
    <div class="header">
        <div style="display:flex; gap:18px; align-items:center; flex-wrap:wrap;">
            <h2 style="color:#ffd700; margin:0; text-shadow: 0 0 15px rgba(255,215,0,0.5);">👑 {{ t.title }} (9D)</h2>
            <div style="background:rgba(15,20,32,0.9); padding:8px 15px; border-radius:10px; border:1px solid rgba(255,255,255,0.1);">👤 <b>{{ username }}</b></div>
            <div style="background:rgba(6,95,70,0.8); color:#34d399; padding:8px 18px; border-radius:10px; font-weight:900; border:1px solid #34d399; box-shadow: 0 0 15px rgba(52,211,153,0.3);">{{ t.balance }}: <span id="liveBalance">{{ balance }}</span> USDD</div>
        </div>
        <div style="display:flex; gap:12px; flex-wrap:wrap;">
            <a href="/change_password" style="background:#8b5cf6; color:#fff; padding:10px 16px; text-decoration:none; border-radius:10px; font-weight:900; box-shadow:0 5px 15px rgba(139,92,246,0.4);">{{ t.change_pass }}</a>
            {% if username == 'admin1' %}
                <a href="/admin_customers" style="background:#ffd700; color:#000; padding:10px 16px; text-decoration:none; border-radius:10px; font-weight:900; box-shadow:0 5px 15px rgba(255,215,0,0.4);">👥 الزبائن</a>
                <a href="/admin_games" style="background:#ffd700; color:#000; padding:10px 16px; text-decoration:none; border-radius:10px; font-weight:900; box-shadow:0 5px 15px rgba(255,215,0,0.4);">🎮 الألعاب</a>
                <a href="/admin_accounting" style="background:#ffd700; color:#000; padding:10px 16px; text-decoration:none; border-radius:10px; font-weight:900; box-shadow:0 5px 15px rgba(255,215,0,0.4);">📊 الخزنة</a>
            {% endif %}
            <a href="/logout" style="background:#ef4444; color:#fff; padding:10px 16px; text-decoration:none; border-radius:10px; font-weight:900; box-shadow:0 5px 15px rgba(239,68,68,0.4);">{{ t.logout }}</a>
        </div>
    </div>

    <!-- شريط إشعارات الفائز العام -->
    <div id="globalNotificationBanner" style="display:none; background: linear-gradient(135deg, #f59e0b, #d97706); color: #000; padding: 18px; border-radius: 14px; max-width: 950px; margin: 20px auto; text-align: center; font-weight: 900; font-size: 20px; box-shadow: 0 10px 30px rgba(245,158,11,0.6); border: 2px solid #fff; animation: pulseBanner 1.5s infinite;">
        🔔 <span id="globalNotificationText"></span>
    </div>

    {% if msg %}<div style="background:rgba(6,95,70,0.9); backdrop-filter:blur(10px); color:#34d399; padding:18px; border-radius:14px; max-width:950px; margin:20px auto; text-align:center; font-weight:900; border:1px solid #34d399; box-shadow:0 10px 30px rgba(0,0,0,0.6);">{{ msg }}</div>{% endif %}

    <div class="financial-bar">
        <div class="fin-card">
            <h3 style="color:#38bdf8; margin:0; font-size:20px;">{{ t.recharge }}</h3>
            <button onclick="document.getElementById('rechargeM').style.display='flex'">{{ t.recharge }}</button>
        </div>
        <div class="fin-card" style="border-color:rgba(245,158,11,0.5);">
            <h3 style="color:#f59e0b; margin:0; font-size:20px;">{{ t.withdraw }}</h3>
            <button onclick="document.getElementById('withdrawM').style.display='flex'" style="background:linear-gradient(135deg,#f59e0b,#d97706); color:#070a12; box-shadow:0 8px 20px rgba(245,158,11,0.4);">{{ t.withdraw }}</button>
        </div>
    </div>

    <div id="rechargeM" class="modal">
        <div class="modal-content">
            <span onclick="this.parentElement.parentElement.style.display='none'" style="position:absolute; top:12px; left:18px; cursor:pointer; font-size:26px; color:#aaa;">&times;</span>
            <h3 style="color:#38bdf8; margin-top:0; font-size:24px;">{{ t.recharge }}</h3>
            <div style="display:flex; gap:12px; margin:25px 0;">
                <button onclick="alert('{{ t.success_msg }}')" style="flex:1; background:#25d366; color:#fff; padding:14px; border:none; border-radius:12px; font-weight:900; cursor:pointer; box-shadow:0 5px 15px rgba(37,211,102,0.4);">Wish Money</button>
                <button onclick="alert('{{ t.success_msg }}')" style="flex:1; background:#3b82f6; color:#fff; padding:14px; border:none; border-radius:12px; font-weight:900; cursor:pointer; box-shadow:0 5px 15px rgba(59,130,246,0.4);">Visa</button>
            </div>
            <form method="POST">
                <input type="hidden" name="action" value="redeem_card">
                <input type="text" name="card_code" placeholder="Card Code (EMP-..)" required style="width:100%; padding:14px; background:rgba(10,13,22,0.9); color:#fff; border:1px solid rgba(255,255,255,0.2); border-radius:12px; box-sizing:border-box; margin-bottom:15px; font-size:16px;">
                <button type="submit" style="width:100%; background:linear-gradient(135deg,#ffd700,#b8860b); color:#000; padding:14px; border:none; border-radius:12px; font-weight:900; cursor:pointer; font-size:18px; box-shadow:0 8px 20px rgba(255,215,0,0.4);">تفعيل الكود</button>
            </form>
        </div>
    </div>

    <div id="withdrawM" class="modal">
        <div class="modal-content" style="width: 480px;">
            <span onclick="this.parentElement.parentElement.style.display='none'" style="position:absolute; top:12px; left:18px; cursor:pointer; font-size:26px; color:#aaa;">&times;</span>
            <h3 style="color:#f59e0b; margin-top:0; font-size:24px;">{{ t.withdraw }}</h3>
            <p style="color:#ef4444; font-size:13px; font-weight:900; background:rgba(239,68,68,0.15); padding:12px; border-radius:10px; border:1px solid #ef4444;">{{ t.withdraw_warning }}</p>
            <form method="POST" style="display:flex; flex-direction:column; gap:15px; margin-top:20px;">
                <button type="submit" name="action" value="withdraw_wish" onclick="window.open('https://wa.me/96176030208?text=Withdraw Wish: {{ username }}', '_blank'); alert('{{ t.success_msg }}');" style="background:#25d366; color:#fff; padding:14px; border:none; border-radius:12px; font-weight:900; cursor:pointer; box-shadow:0 5px 15px rgba(37,211,102,0.4);">{{ t.wish_withdraw }}</button>
                <button type="submit" name="action" value="withdraw_visa" onclick="alert('{{ t.success_msg }}')" style="background:#3b82f6; color:#fff; padding:14px; border:none; border-radius:12px; font-weight:900; cursor:pointer; box-shadow:0 5px 15px rgba(59,130,246,0.4);">{{ t.visa_withdraw }}</button>
                <div style="background:rgba(10,13,22,0.9); padding:15px; border-radius:12px; border:1px solid rgba(255,255,255,0.1); text-align:right;">
                    <label style="font-size:13px; color:#ffd700; font-weight:bold;">USDT Address:</label>
                    <input type="text" name="usdt_acc" placeholder="Address..." style="width:100%; padding:12px; background:rgba(5,7,12,0.9); color:#fff; border:1px solid rgba(255,255,255,0.2); border-radius:10px; box-sizing:border-box; margin:8px 0;">
                    <button type="submit" name="action" value="withdraw_usdt" onclick="alert('{{ t.success_msg }}')" style="width:100%; background:linear-gradient(135deg,#f59e0b,#d97706); color:#000; padding:12px; border:none; border-radius:10px; font-weight:900; cursor:pointer; box-shadow:0 5px 15px rgba(245,158,11,0.4);">{{ t.usdt_withdraw }}</button>
                </div>
            </form>
        </div>
    </div>

    <!-- شبكة الألعاب الفائقة 9D -->
    <div class="icons-grid">
        <a href="/game_golden_number" class="icon-card"><div class="icon-logo">🏆</div><div class="icon-title">{{ t.game1 }}</div></a>
        <a href="/game_roulette" class="icon-card"><div class="icon-logo">🎰</div><div class="icon-title">{{ t.game2 }}</div></a>
        <a href="/game_numbers_empire" class="icon-card"><div class="icon-logo">🏛️</div><div class="icon-title">{{ t.game3 }}</div></a>
        <a href="/game_number_wheel" class="icon-card"><div class="icon-logo">🎡</div><div class="icon-title">{{ t.game4 }}</div></a>
        <a href="/game_reveal_and_win" class="icon-card"><div class="icon-logo">🎟️</div><div class="icon-title">{{ t.game5 }}</div></a>
        <a href="/game_golden_boxes_new" class="icon-card"><div class="icon-logo">🎁</div><div class="icon-title">{{ t.game6 }}</div></a>
    </div>

    <style>
        @keyframes pulseBanner { 0% { transform: scale(1); } 50% { transform: scale(1.02); } 100% { transform: scale(1); } }
    </style>
    <script>
        setInterval(() => {
            fetch('/api/sync_balance').then(res => res.json()).then(data => {
                let badge = document.getElementById('liveBalance');
                if(badge && badge.innerText !== String(data.balance)) badge.innerText = data.balance;
            }).catch(err => {});

            fetch('/api/golden_status').then(res => res.json()).then(data => {
                let banner = document.getElementById('globalNotificationBanner');
                let text = document.getElementById('globalNotificationText');
                if(data.status === 'finished' && data.winning_number) {
                    text.innerText = `🎉 إشعار الفائز: الفائز في لعبة الرقم الحنون هو الرقم #${data.winning_number} والرابح هو الحساب (${data.winner_username})`;
                    banner.style.display = 'block';
                } else {
                    banner.style.display = 'none';
                }
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
    <div style="background:rgba(20,24,38,0.9); backdrop-filter:blur(25px); padding:45px; border-radius:25px; border:2px solid #8b5cf6; width:380px; text-align:center; box-shadow:0 25px 60px rgba(0,0,0,0.9); transform:perspective(1000px) rotateX(6deg);">
        <h3 style="color:#ffd700; margin-top:0; font-size:24px;">{{ t.change_pass }}</h3>
        {% if msg %}<p style="color:#34d399; font-weight:bold; background:rgba(52,211,153,0.15); padding:10px; border-radius:8px;">{{ msg }}</p>{% endif %}
        <form method="POST">
            <input type="password" name="old_password" placeholder="Old Password" required style="width:100%; padding:14px; margin:10px 0; background:rgba(10,13,22,0.9); color:#fff; border:1px solid rgba(255,255,255,0.2); border-radius:10px; box-sizing:border-box;">
            <input type="password" name="new_password" placeholder="New Password" required style="width:100%; padding:14px; margin:10px 0; background:rgba(10,13,22,0.9); color:#fff; border:1px solid rgba(255,255,255,0.2); border-radius:10px; box-sizing:border-box;">
            <input type="password" name="confirm_password" placeholder="Confirm Password" required style="width:100%; padding:14px; margin:10px 0; background:rgba(10,13,22,0.9); color:#fff; border:1px solid rgba(255,255,255,0.2); border-radius:10px; box-sizing:border-box;">
            <button type="submit" style="width:100%; padding:14px; background:linear-gradient(135deg,#8b5cf6,#6d28d9); color:#fff; border:none; border-radius:10px; font-weight:900; cursor:pointer; margin-top:15px; font-size:16px; box-shadow:0 8px 25px rgba(139,92,246,0.5);">Update</button>
        </form>
        <a href="/dashboard" style="color:#38bdf8; display:inline-block; margin-top:20px; text-decoration:none; font-weight:bold;">{{ t.back_dash }}</a>
    </div>
</body>
</html>
"""

# --- القالب المحدث للعبة الرقم الحنون (الرقم 1) مع صندوق الأرقام، تنبيه 22:00، وتحديث 9D فوري كل ثانيتين دون رجوع لأعلى الصفحة ---
GAME_GOLDEN_PAGE = LANG_BAR + """
<!DOCTYPE html>
<html lang="{{ t.dir }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><title>{{ t.game1 }} - 9D</title>
    <style>
        body { font-family:'Segoe UI', Tahoma, sans-serif; background:radial-gradient(circle at center, #151928 0%, #070a12 100%); color:#fff; margin:0; padding:25px; }
        .card-3d { background:linear-gradient(135deg, rgba(31,26,15,0.95), rgba(13,13,13,0.95)); backdrop-filter:blur(20px); border:4px solid #ffd700; padding:35px; border-radius:30px; max-width:950px; margin:20px auto; box-shadow:0 30px 70px rgba(0,0,0,0.9), inset 0 0 30px rgba(255,215,0,0.15); transform:perspective(1400px) rotateX(4deg); }
        .notice-box { background: linear-gradient(135deg, #1e3a8a, #1e1b4b); border: 2px solid #38bdf8; padding: 18px; border-radius: 16px; text-align: center; margin-bottom: 25px; box-shadow: 0 10px 25px rgba(56,189,248,0.3); }
        .my-box-panel { background: rgba(15,23,42,0.95); border: 2px solid #34d399; padding: 20px; border-radius: 18px; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px; box-shadow: 0 10px 25px rgba(52,211,153,0.2); }
        .grid { display:grid; grid-template-columns:repeat(10, 1fr); gap:12px; margin-top:25px; }
        @media(max-width: 768px) { .grid { grid-template-columns:repeat(5, 1fr); } }
        .cell { background:linear-gradient(145deg, #7c3aed, #4c1d95); border:3px solid #a78bfa; border-radius:16px; height:80px; display:flex; flex-direction:column; align-items:center; justify-content:center; font-weight:900; cursor:pointer; transform:perspective(1000px) rotateX(12deg) translateZ(15px); box-shadow:0 12px 25px rgba(0,0,0,0.8); transition:0.3s; color:#fff; font-size: 22px; }
        .cell:hover { transform:perspective(1000px) rotateX(0deg) translateY(-8px) translateZ(35px); border-color:#ffd700; box-shadow:0 20px 40px rgba(255,215,0,0.5); }
        .cell.booked { background: linear-gradient(145deg, #7f1d1d, #450a0a) !important; border-color:#ef4444 !important; cursor:not-allowed; }
        .cell.my { background: linear-gradient(145deg, #1e3a8a, #172554) !important; border-color:#3b82f6 !important; }
        .global-alert { display:none; background: linear-gradient(135deg, #f59e0b, #d97706); color: #000; padding: 20px; border-radius: 16px; text-align: center; font-weight: 900; font-size: 22px; margin-bottom: 25px; box-shadow: 0 10px 30px rgba(245,158,11,0.6); border: 2px solid #fff; }
    </style>
</head>
<body>
    <div style="display:flex; justify-content:space-between; align-items:center; max-width:950px; margin:0 auto; background:rgba(20,24,38,0.9); padding:15px 25px; border-radius:15px; border:1px solid rgba(255,215,0,0.3);">
        <h2 style="color:#ffd700; margin:0; font-size: 26px;">🏆 {{ t.game1 }} (9D Ultra)</h2>
        <div style="font-size: 18px;"><b>{{ t.balance }}: <span id="liveBalance">{{ balance }}</span> USDD</b> | <a href="/dashboard" style="color:#38bdf8; text-decoration:none; font-weight:bold;">{{ t.back_dash }}</a></div>
    </div>

    <div class="card-3d">
        <!-- إشعار الفائز العام -->
        <div id="gameAlertBox" class="global-alert">
            🔔 <span id="gameAlertText"></span>
        </div>

        <!-- تنبيه موعد السحب اليومي -->
        <div class="notice-box">
            <h3 style="color: #38bdf8; margin: 0 0 8px 0; font-size: 20px;">⏰ تنبيه موعد السحب اليومي</h3>
            <p style="color: #f8fafc; margin: 0; font-size: 16px; font-weight: bold;">تجري عملية السحب لهذه اللعبة <b>مرة واحدة يومياً عند الساعة 22:00 (10 مساءً) بتوقيت بيروت</b>.</p>
        </div>

        <!-- صندوق الأرقام التي حجزها اللاعب وقيمتها بالـ USDD -->
        <div class="my-box-panel">
            <div>
                <h4 style="color: #34d399; margin: 0 0 5px 0; font-size: 18px;">📦 صندوق أرقامك المحجوزة:</h4>
                <div id="myNumbersDisplay" style="font-size: 20px; font-weight: 900; color: #fff; font-family: monospace;">
                    {% if my_booked_nums %}{{ my_booked_nums | join(', ') }}{% else %}لا توجد أرقام محجوزة حالياً{% endif %}
                </div>
            </div>
            <div style="text-align: left;">
                <h4 style="color: #ffd700; margin: 0 0 5px 0; font-size: 18px;">💰 القيمة الإجمالية:</h4>
                <div id="mySpentDisplay" style="font-size: 22px; font-weight: 900; color: #34d399;">{{ my_total_spent }} USDD</div>
            </div>
        </div>

        <p style="text-align:center; color:#ffd700; font-size:20px; font-weight:900; text-shadow:0 0 10px rgba(255,215,0,0.4);">
            {{ t.cost }}: 2 USDD | {{ t.prize }}: 75 USDD
        </p>

        {% if msg %}<div id="actionMsg" style="background:rgba(6,95,70,0.9); color:#34d399; padding:15px; border-radius:12px; margin:15px 0; text-align:center; font-weight:900; font-size:18px; border:1px solid #34d399;">{{ msg }}</div>{% endif %}

        <!-- شبكة الأرقام (1 إلى 50) -->
        <div class="grid" id="numbersGrid">
            {% for i in range(1, 51) %}
                {% if i in bookings %}
                    {% if bookings[i] == username %}
                        <button type="button" onclick="handleAction('cancel', {{ i }})" class="cell my" style="width:100%;">
                            {{ i }}<br><span style="font-size:12px; color:#93c5fd;">{{ t.cancel }} (أنت)</span>
                        </button>
                    {% else %}
                        <div class="cell booked">{{ i }}<br><span style="font-size:12px; color:#fca5a5;">{{ bookings[i] }}</span></div>
                    {% endif %}
                {% else %}
                    <button type="button" onclick="handleAction('book', {{ i }})" class="cell" style="width:100%;">{{ i }}</button>
                {% endif %}
            {% endfor %}
        </div>

        {% if username == 'admin1' %}
            <div style="margin-top:35px; text-align:center;">
                <button type="button" onclick="handleAction('admin_draw', 0)" style="background:linear-gradient(135deg,#22c55e,#15803d); color:#fff; font-weight:900; padding:18px 45px; border:none; border-radius:16px; cursor:pointer; font-size:20px; box-shadow:0 12px 35px rgba(34,197,94,0.6);">⚡ {{ t.draw_now }}</button>
            </div>
        {% endif %}
    </div>

    <script>
        // إرسال الحجز والتراجع دون إعادة تحميل الصفحة أو العودة لأعلى الصفحة
        function handleAction(actionType, numberVal) {
            let formData = new FormData();
            formData.append('action_type', actionType);
            formData.append('number', numberVal);

            fetch('/game_golden_number', {
                method: 'POST',
                body: formData
            }).then(res => res.json()).then(data => {
                if(data.msg) {
                    let msgBox = document.getElementById('actionMsg');
                    if(!msgBox) {
                        msgBox = document.createElement('div');
                        msgBox.id = 'actionMsg';
                        msgBox.style = "background:rgba(6,95,70,0.9); color:#34d399; padding:15px; border-radius:12px; margin:15px 0; text-align:center; font-weight:900; font-size:18px; border:1px solid #34d399;";
                        document.querySelector('.card-3d').prepend(msgBox);
                    }
                    msgBox.innerText = data.msg;
                }
                updateGameData();
            }).catch(err => console.error(err));
        }

        // تحديث البيانات تلقائياً كل ثانيتين في "برمشت عين" دون تغيير موضع السكرول (Scroll)
        function updateGameData() {
            fetch('/api/golden_status').then(res => res.json()).then(data => {
                // تحديث الرصيد
                let badge = document.getElementById('liveBalance');
                if(badge && badge.innerText !== String(data.balance)) {
                    badge.innerText = data.balance;
                }

                // تحديث تنبيه الفائز العام
                let alertBox = document.getElementById('gameAlertBox');
                let alertText = document.getElementById('gameAlertText');
                if(data.status === 'finished' && data.winning_number) {
                    alertText.innerText = `🎉 إشعار الهواتف والمنصة: الفائز في لعبة الرقم الحنون هو الرقم #${data.winning_number} والرابح هو الحساب (${data.winner_username})`;
                    alertBox.style.display = 'block';
                } else {
                    alertBox.style.display = 'none';
                }

                // تحديث صندوق أرقام اللاعب
                let myNumDisplay = document.getElementById('myNumbersDisplay');
                let mySpentDisplay = document.getElementById('mySpentDisplay');
                if(myNumDisplay) {
                    myNumDisplay.innerText = data.my_booked_nums.length > 0 ? data.my_booked_nums.join(', ') : 'لا توجد أرقام محجوزة حالياً';
                }
                if(mySpentDisplay) {
                    mySpentDisplay.innerText = data.my_total_spent + ' USDD';
                }

                // تحديث الشبكة (1-50) ديناميكياً
                let grid = document.getElementById('numbersGrid');
                if(grid) {
                    let currentUsername = "{{ username }}";
                    let html = '';
                    for(let i = 1; i <= 50; i++) {
                        if(data.bookings[i]) {
                            let owner = data.bookings[i];
                            if(owner === currentUsername) {
                                html += `<button type="button" onclick="handleAction('cancel', ${i})" class="cell my" style="width:100%;">${i}<br><span style="font-size:12px; color:#93c5fd;">تراجع (أنت)</span></button>`;
                            } else {
                                html += `<div class="cell booked">${i}<br><span style="font-size:12px; color:#fca5a5;">${owner}</span></div>`;
                            }
                        } else {
                            html += `<button type="button" onclick="handleAction('book', ${i})" class="cell" style="width:100%;">${i}</button>`;
                        }
                    }
                    grid.innerHTML = html;
                }
            }).catch(err => {});
        }

        setInterval(updateGameData, 2000);
    </script>
</body>
</html>
"""

GAME_NUMBERS_EMPIRE_PAGE = LANG_BAR + """
<!DOCTYPE html>
<html lang="{{ t.dir }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ t.game3 }} - 9D</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: radial-gradient(circle at center, #151928 0%, #070a12 100%); color: #f8fafc; margin: 0; padding: 25px; }
        .header { display: flex; justify-content: space-between; align-items: center; background: rgba(20,24,38,0.9); backdrop-filter: blur(20px); padding: 18px 25px; border-radius: 16px; border: 2px solid #ffd700; box-shadow: 0 10px 30px rgba(0,0,0,0.7); }
        .user-stats-box { background: rgba(24,24,27,0.9); border: 2px dashed #b8860b; padding: 18px; border-radius: 16px; margin-top: 25px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px; }
        .board-container { background: linear-gradient(135deg, rgba(17,13,6,0.95), rgba(0,0,0,0.95)); backdrop-filter: blur(20px); border: 5px solid #b8860b; padding: 30px; border-radius: 25px; margin-top: 25px; text-align: center; transform: perspective(1400px) rotateX(4deg); box-shadow: 0 30px 70px rgba(0,0,0,0.9), inset 0 0 30px rgba(184,134,11,0.2); }
        .board-grid { display: grid; grid-template-columns: repeat(10, 1fr); gap: 14px; margin-top: 25px; }
        @media(max-width: 768px) { .board-grid { grid-template-columns: repeat(5, 1fr); } }
        .number-box { background: linear-gradient(145deg, #059669, #047857); border: 3px solid #34d399; border-radius: 16px; height: 75px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 20px; font-weight: 900; color: #ffffff; cursor: pointer; transform: perspective(1000px) rotateX(10deg) translateZ(15px); box-shadow: 0 10px 25px rgba(0,0,0,0.8); transition: 0.3s; }
        .number-box:hover { transform: perspective(1000px) rotateX(0deg) translateY(-6px) translateZ(30px); border-color: #ffd700; box-shadow: 0 20px 40px rgba(52,211,153,0.5); }
        .number-box.booked { background: linear-gradient(145deg, #7f1d1d, #450a0a) !important; border-color: #ef4444 !important; color: #fca5a5 !important; cursor: not-allowed; }
        .number-box.my-booked { background: linear-gradient(145deg, #1e3a8a, #172554) !important; border-color: #3b82f6 !important; color: #93c5fd !important; }
        .back-btn { background: #3b82f6; color: white; text-decoration: none; padding: 10px 18px; border-radius: 10px; font-weight: 900; box-shadow: 0 5px 15px rgba(59,130,246,0.4); }
    </style>
</head>
<body>
    <div class="header">
        <h2 style="color: #ffd700; margin: 0; text-shadow:0 0 10px rgba(255,215,0,0.5);">🏛️ {{ t.game3 }} (9D Ultra)</h2>
        <div style="display: flex; gap: 20px; align-items: center;">
            <div style="color: #34d399; font-weight: 900; font-size: 18px; text-shadow:0 0 10px rgba(52,211,153,0.4);">{{ t.balance }}: <span id="liveBalance">{{ balance }}</span> USDD</div>
            <a href="/dashboard" class="back-btn">{{ t.back_dash }}</a>
        </div>
    </div>
    {% if msg %}<div style="background: rgba(6,95,70,0.9); color: #34d399; padding: 15px; border-radius: 12px; margin-top: 20px; text-align: center; font-weight: 900; border:1px solid #34d399;">{{ msg }}</div>{% endif %}
    <div class="user-stats-box">
        <div><b style="color: #ffd700;">👤 {{ username }}:</b></div>
        <div><b style="color: #38bdf8;">أرقامك:</b> <span style="color: #fff; font-family: monospace; background: #000; padding: 6px 12px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.1);">{% if my_booked_nums %}{{ my_booked_nums | join(', ') }}{% else %}لا توجد{% endif %}</span></div>
        <div><b style="color: #34d399;">المصروف:</b> <span style="color: #34d399; font-weight: 900;">{{ my_total_spent }} USDD</span></div>
    </div>
    <div class="board-container">
        <h3 style="color: #ffd700; margin-top: 0; font-size: 22px; text-shadow:0 0 15px rgba(255,215,0,0.4);">🎯 اختر أرقام الحظ (تكلفة الحجز: 2 USDD)</h3>
        <div class="board-grid">
            {% for i in range(1, 51) %}
                {% if i in bookings %}
                    {% if bookings[i] == username %}
                        <form method="POST" style="margin: 0;">
                            <input type="hidden" name="number" value="{{ i }}">
                            <button type="submit" name="cancel_number" class="number-box my-booked" style="width: 100%;" title="تراجع واسترداد 2 USDD">
                                {{ i }}<br><span style="font-size: 10px;">(أنت) ❌</span>
                            </button>
                        </form>
                    {% else %}
                        <div class="number-box booked" title="محجوز بواسطة {{ bookings[i] }}">
                            {{ i }}<br><span style="font-size: 10px; color: #fca5a5;">({{ bookings[i] }})</span>
                        </div>
                    {% endif %}
                {% else %}
                    <form method="POST" style="margin: 0;">
                        <input type="hidden" name="number" value="{{ i }}">
                        <button type="submit" name="book_number" class="number-box" style="width: 100%;">{{ i }}</button>
                    </form>
                {% endif %}
            {% endfor %}
        </div>
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

GAME_ROULETTE_PAGE = LANG_BAR + """
<!DOCTYPE html>
<html lang="{{ t.dir }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><title>{{ t.game2 }} - 9D</title>
    <style>
        body { font-family:'Segoe UI', Tahoma, sans-serif; background:radial-gradient(circle at center, #151928 0%, #070a12 100%); color:#fff; text-align:center; padding:35px; }
        .roulette-9d { background:linear-gradient(145deg, rgba(6,78,59,0.95), rgba(2,44,34,0.95)); backdrop-filter:blur(25px); border:5px solid #ffd700; padding:50px; border-radius:35px; max-width:700px; margin:30px auto; transform:perspective(1400px) rotateX(5deg); box-shadow:0 35px 80px rgba(0,0,0,0.9), inset 0 0 35px rgba(255,215,0,0.3); }
        .wheel-circle { width:220px; height:220px; background:conic-gradient(#ef4444 0deg 36deg, #22c55e 36deg 72deg, #3b82f6 72deg 108deg, #eab308 108deg 144deg, #a855f7 144deg 180deg, #ec4899 180deg 216deg, #06b6d4 216deg 252deg, #f97316 252deg 288deg, #6366f1 288deg 324deg, #84cc16 324deg 360deg); border-radius:50%; margin:25px auto; border:6px solid #ffd700; box-shadow:0 0 40px rgba(255,215,0,0.6), inset 0 0 20px rgba(0,0,0,0.8); animation: spinGlow 10s linear infinite; }
        @keyframes spinGlow { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div style="display:flex; justify-content:space-between; align-items:center; max-width:700px; margin:0 auto; background:rgba(20,24,38,0.9); padding:15px 25px; border-radius:15px; border:1px solid rgba(255,215,0,0.3);">
        <h2 style="color:#ffd700; margin:0;">🎰 {{ t.game2 }} (9D Ultra)</h2>
        <div><b>{{ t.balance }}: {{ balance }} USDD</b> | <a href="/dashboard" style="color:#38bdf8; text-decoration:none; font-weight:bold;">{{ t.back_dash }}</a></div>
    </div>
    {% if msg %}<div style="background:rgba(6,95,70,0.9); color:#34d399; padding:15px; border-radius:12px; max-width:700px; margin:20px auto; font-weight:900; border:1px solid #34d399;">{{ msg }}</div>{% endif %}
    <div class="roulette-9d">
        <div class="wheel-circle"></div>
        <p style="color:#ffd700; font-size:18px; font-weight:bold; text-shadow:0 0 10px rgba(255,215,0,0.4);">التكلفة: 5 USDD | الجائزة تصل إلى 35x</p>
        <form method="POST">
            <input type="hidden" name="bets_data" value='[{"type": "straight", "value": 7, "amount": 5}]'>
            <input type="hidden" name="total_bet_amount" value="5">
            <button type="submit" style="padding:18px 45px; background:linear-gradient(135deg,#ffd700,#ff8c00); color:#000; font-weight:900; font-size:20px; border:none; border-radius:16px; cursor:pointer; box-shadow:0 12px 35px rgba(255,215,0,0.6); transition:0.3s;">🎡 {{ t.spin }} (5 USDD)</button>
        </form>
    </div>
</body>
</html>
"""

GAME_NUMBER_WHEEL_PAGE = LANG_BAR + """
<!DOCTYPE html>
<html lang="{{ t.dir }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><title>{{ t.game4 }} - 9D</title>
    <style>
        body { font-family:'Segoe UI', Tahoma, sans-serif; background:radial-gradient(circle at center, #151928 0%, #070a12 100%); color:#fff; text-align:center; padding:35px; }
        .wheel-9d { background:linear-gradient(145deg, rgba(31,26,15,0.95), rgba(13,13,13,0.95)); backdrop-filter:blur(25px); border:5px solid #ffd700; padding:50px; border-radius:35px; max-width:600px; margin:30px auto; transform:perspective(1400px) rotateX(5deg); box-shadow:0 35px 80px rgba(0,0,0,0.9), inset 0 0 35px rgba(255,215,0,0.3); }
        .neon-wheel { width:160px; height:160px; background:radial-gradient(circle,#ffd700,#b8860b); border-radius:50%; margin:25px auto; display:flex; align-items:center; justify-content:center; font-size:60px; box-shadow:0 0 50px rgba(255,215,0,0.8), inset 0 0 20px rgba(0,0,0,0.5); animation: pulseGlow 2s infinite alternate; }
        @keyframes pulseGlow { 0% { transform: scale(1); box-shadow: 0 0 30px rgba(255,215,0,0.6); } 100% { transform: scale(1.08); box-shadow: 0 0 60px rgba(255,215,0,0.9); } }
    </style>
</head>
<body>
    <div style="display:flex; justify-content:space-between; align-items:center; max-width:600px; margin:0 auto; background:rgba(20,24,38,0.9); padding:15px 25px; border-radius:15px; border:1px solid rgba(255,215,0,0.3);">
        <h2 style="color:#ffd700; margin:0;">🎡 {{ t.game4 }} (9D Ultra)</h2>
        <div><b>{{ t.balance }}: {{ balance }} USDD</b> | <a href="/dashboard" style="color:#38bdf8; text-decoration:none; font-weight:bold;">{{ t.back_dash }}</a></div>
    </div>
    {% if msg %}<div style="background:rgba(6,95,70,0.9); color:#34d399; padding:15px; border-radius:12px; max-width:600px; margin:20px auto; font-weight:900; border:1px solid #34d399;">{{ msg }}</div>{% endif %}
    <div class="wheel-9d">
        <div class="neon-wheel">🎡</div>
        <p style="color:#ffd700; font-size:18px; font-weight:bold; text-shadow:0 0 10px rgba(255,215,0,0.4);">التكلفة: 3 USDD | الجائزة: 15 USDD</p>
        <form method="POST">
            <input type="hidden" name="selected_numbers" value="[3, 8, 14]">
            <button type="submit" style="padding:18px 45px; background:linear-gradient(135deg,#22c55e,#15803d); color:#fff; font-weight:900; font-size:20px; border:none; border-radius:16px; cursor:pointer; box-shadow:0 12px 35px rgba(34,197,94,0.5); transition:0.3s;">🎯 {{ t.spin }} (3 USDD)</button>
        </form>
    </div>
</body>
</html>
"""

GAME_REVEAL_AND_WIN_PAGE = LANG_BAR + """
<!DOCTYPE html>
<html lang="{{ t.dir }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><title>{{ t.game5 }} - 9D</title>
    <style>
        body { font-family:'Segoe UI', Tahoma, sans-serif; background:radial-gradient(circle at center, #151928 0%, #070a12 100%); color:#fff; text-align:center; padding:35px; }
        .reveal-9d { background:linear-gradient(145deg, rgba(31,31,31,0.95), rgba(17,17,17,0.95)); backdrop-filter:blur(25px); border:5px solid #ffd700; padding:50px; border-radius:35px; max-width:600px; margin:30px auto; transform:perspective(1400px) rotateX(5deg); box-shadow:0 35px 80px rgba(0,0,0,0.9), inset 0 0 35px rgba(255,215,0,0.3); }
    </style>
</head>
<body>
    <div style="display:flex; justify-content:space-between; align-items:center; max-width:600px; margin:0 auto; background:rgba(20,24,38,0.9); padding:15px 25px; border-radius:15px; border:1px solid rgba(255,215,0,0.3);">
        <h2 style="color:#ffd700; margin:0;">🎟️ {{ t.game5 }} (9D Ultra)</h2>
        <div><b>{{ t.balance }}: {{ balance }} USDD</b> | <a href="/dashboard" style="color:#38bdf8; text-decoration:none; font-weight:bold;">{{ t.back_dash }}</a></div>
    </div>
    {% if msg %}<div style="background:rgba(6,95,70,0.9); color:#34d399; padding:15px; border-radius:12px; max-width:600px; margin:20px auto; font-weight:900; border:1px solid #34d399;">{{ msg }}</div>{% endif %}
    <div class="reveal-9d">
        <div style="font-size:80px; margin-bottom:20px; filter:drop-shadow(0 15px 25px rgba(0,0,0,0.9)); animation: floatIcon 3s ease-in-out infinite;">🎟️</div>
        {% if result_data %}
            <div style="font-size:35px; margin:20px 0; letter-spacing:15px; background:rgba(0,0,0,0.6); padding:15px; border-radius:14px; border:1px solid #ffd700;">
                {{ result_data.revealed.values() | list | join(' ') }}
            </div>
        {% endif %}
        <p style="color:#ffd700; font-size:18px; font-weight:bold; text-shadow:0 0 10px rgba(255,215,0,0.4);">التكلفة: 1 USDD | الجائزة: 20 USDD</p>
        <form method="POST">
            <button type="submit" style="padding:18px 45px; background:linear-gradient(135deg,#ffd700,#ff8c00); color:#000; font-weight:900; font-size:20px; border:none; border-radius:16px; cursor:pointer; box-shadow:0 12px 35px rgba(255,215,0,0.6); transition:0.3s;">🎟️ {{ t.reveal }} (1 USDD)</button>
        </form>
    </div>
    <style>@keyframes floatIcon { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-12px); } }</style>
</body>
</html>
"""

GAME_GOLDEN_BOXES_NEW_PAGE = LANG_BAR + """
<!DOCTYPE html>
<html lang="{{ t.dir }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><title>{{ t.game6 }} - 9D</title>
    <style>
        body { font-family:'Segoe UI', Tahoma, sans-serif; background:radial-gradient(circle at center, #151928 0%, #070a12 100%); color:#fff; text-align:center; padding:35px; }
        .boxes-9d { background:linear-gradient(135deg, rgba(17,13,6,0.95), rgba(0,0,0,0.95)); backdrop-filter:blur(25px); border:5px solid #b8860b; padding:50px; border-radius:35px; max-width:700px; margin:30px auto; transform:perspective(1400px) rotateX(5deg); box-shadow:0 35px 80px rgba(0,0,0,0.9), inset 0 0 35px rgba(184,134,11,0.3); }
        .box-9d { width:95px; height:95px; background:linear-gradient(145deg, #7c3aed, #4c1d95); border:3px solid #ffd700; border-radius:20px; color:#fff; font-size:26px; font-weight:900; cursor:pointer; transform:perspective(1000px) rotateX(12deg) translateZ(20px); box-shadow:0 15px 30px rgba(0,0,0,0.8); transition:0.3s; }
        .box-9d:hover { transform:perspective(1000px) rotateX(0deg) translateY(-8px) translateZ(40px); box-shadow:0 25px 50px rgba(255,215,0,0.6); border-color:#fff; }
    </style>
</head>
<body>
    <div style="display:flex; justify-content:space-between; align-items:center; max-width:700px; margin:0 auto; background:rgba(20,24,38,0.9); padding:15px 25px; border-radius:15px; border:1px solid rgba(255,215,0,0.3);">
        <h2 style="color:#ffd700; margin:0;">🎁 {{ t.game6 }} (9D Ultra)</h2>
        <div><b>{{ t.balance }}: {{ balance }} USDD</b> | <a href="/dashboard" style="color:#38bdf8; text-decoration:none; font-weight:bold;">{{ t.back_dash }}</a></div>
    </div>
    {% if msg %}<div style="background:rgba(6,95,70,0.9); color:#34d399; padding:15px; border-radius:12px; max-width:700px; margin:20px auto; font-weight:900; border:1px solid #34d399;">{{ msg }}</div>{% endif %}
    <div class="boxes-9d">
        <p style="color:#ffd700; font-size:18px; font-weight:bold; text-shadow:0 0 10px rgba(255,215,0,0.4);">{{ t.cost }}: 50 USDD | {{ t.prize }}: 200 USDD</p>
        <div style="display:flex; justify-content:center; gap:20px; margin:35px 0; flex-wrap:wrap;">
            {% for b in range(1, 6) %}
                <form method="POST" style="margin:0;">
                    <input type="hidden" name="box_number" value="{{ b }}">
                    <button type="submit" name="book_box" class="box-9d">📦 {{ b }}</button>
                </form>
            {% endfor %}
        </div>
        {% if username == 'admin1' %}
            <form method="POST"><button type="submit" name="admin_execute_luxury_draw" style="background:linear-gradient(135deg,#22c55e,#15803d); color:#fff; padding:16px 35px; border:none; border-radius:14px; font-weight:900; cursor:pointer; font-size:18px; box-shadow:0 10px 30px rgba(34,197,94,0.5);">⚡ {{ t.draw_now }}</button></form>
        {% endif %}
    </div>
</body>
</html>
"""

ADMIN_CUSTOMERS_PAGE = LANG_BAR + """
<!DOCTYPE html>
<html lang="{{ t.dir }}" dir="{{ t.dir }}">
<head><meta charset="UTF-8"><title>إدارة الزبائن - 9D</title></head>
<body style="font-family:'Segoe UI', Tahoma, sans-serif; background:radial-gradient(circle at center, #151928 0%, #070a12 100%); color:#fff; padding:30px;">
    <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(20,24,38,0.9); padding:18px 25px; border-radius:16px; border:2px solid #ffd700; max-width:900px; margin:0 auto 25px auto;">
        <h2 style="color:#ffd700; margin:0;">👑 إدارة الزبائن والحسابات</h2>
        <a href="/dashboard" style="background:#3b82f6; color:#fff; padding:10px 18px; text-decoration:none; border-radius:10px; font-weight:900; box-shadow:0 5px 15px rgba(59,130,246,0.4);">{{ t.back_dash }}</a>
    </div>
    {% if msg %}<p style="color:#34d399; text-align:center; font-weight:bold;">{{ msg }}</p>{% endif %}
    <div style="background:rgba(25,30,48,0.9); padding:30px; border-radius:20px; max-width:480px; margin:20px auto; border:2px solid #ffd700; box-shadow:0 20px 50px rgba(0,0,0,0.8);">
        <h3 style="color:#38bdf8; margin-top:0; font-size:22px;">خلق حساب جديد</h3>
        <form method="POST">
            <input type="hidden" name="action" value="create_user">
            <input type="text" name="new_username" placeholder="Username" required style="width:100%; padding:14px; margin:10px 0; background:rgba(10,13,22,0.9); color:#fff; border:1px solid rgba(255,255,255,0.2); border-radius:10px; box-sizing:border-box;">
            <input type="password" name="new_password" placeholder="Password" required style="width:100%; padding:14px; margin:10px 0; background:rgba(10,13,22,0.9); color:#fff; border:1px solid rgba(255,255,255,0.2); border-radius:10px; box-sizing:border-box;">
            <input type="text" name="new_owner" placeholder="Owner Name" required style="width:100%; padding:14px; margin:10px 0; background:rgba(10,13,22,0.9); color:#fff; border:1px solid rgba(255,255,255,0.2); border-radius:10px; box-sizing:border-box;">
            <button type="submit" style="width:100%; padding:14px; background:linear-gradient(135deg,#3b82f6,#1d4ed8); color:#fff; font-weight:900; border:none; border-radius:10px; cursor:pointer; margin-top:10px; font-size:16px; box-shadow:0 8px 20px rgba(59,130,246,0.4);">إنشاء</button>
        </form>
    </div>
    <div style="background:rgba(25,30,48,0.9); padding:30px; border-radius:20px; max-width:900px; margin:25px auto; box-shadow:0 20px 50px rgba(0,0,0,0.8); border:1px solid rgba(255,255,255,0.1);">
        <h3 style="color:#ffd700; margin-top:0; font-size:22px;">سجل الحسابات</h3>
        <table style="width:100%; border-collapse:collapse;">
            <tr style="background:rgba(10,13,22,0.9); color:#ffd700;"><th style="padding:12px; border:1px solid #444;">User</th><th style="padding:12px; border:1px solid #444;">Pass</th><th style="padding:12px; border:1px solid #444;">Owner</th><th style="padding:12px; border:1px solid #444;">Balance</th></tr>
            {% for u in users_list %}
            <tr style="text-align:center;"><td style="padding:12px; border:1px solid #444;"><a href="/admin_customer_detail/{{ u.username }}" style="color:#38bdf8; font-weight:900; text-decoration:none;">📂 {{ u.username }}</a></td><td style="padding:12px; border:1px solid #444;">{{ u.password }}</td><td style="padding:12px; border:1px solid #444;">{{ u.owner_name }}</td><td style="padding:12px; border:1px solid #444; color:#34d399; font-weight:900;">{{ u.balance }} USDD</td></tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

ADMIN_CUSTOMER_DETAIL_PAGE = LANG_BAR + """
<!DOCTYPE html>
<html lang="{{ t.dir }}" dir="{{ t.dir }}">
<head><meta charset="UTF-8"><title>ذاكرة الزبون - 9D</title></head>
<body style="font-family:'Segoe UI', Tahoma, sans-serif; background:radial-gradient(circle at center, #151928 0%, #070a12 100%); color:#fff; padding:30px;">
    <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(20,24,38,0.9); padding:18px 25px; border-radius:16px; border:2px solid #ffd700; max-width:900px; margin:0 auto 25px auto;">
        <h2 style="color:#ffd700; margin:0;">📂 ذاكرة وتفاصيل: {{ user.username }} ({{ user.owner_name }})</h2>
        <a href="/admin_customers" style="background:#3b82f6; color:#fff; padding:10px 18px; text-decoration:none; border-radius:10px; font-weight:900;">الرجوع للزبائن</a>
    </div>
    <div style="background:rgba(25,30,48,0.9); padding:30px; border-radius:20px; margin:20px auto; max-width:900px; box-shadow:0 20px 50px rgba(0,0,0,0.8); border:1px solid rgba(255,255,255,0.1);">
        <h3 style="color:#38bdf8; margin-top:0; font-size:22px;">سجل العمليات (توقيت بيروت)</h3>
        <table style="width:100%; border-collapse:collapse;">
            <tr style="background:rgba(10,13,22,0.9); color:#ffd700;"><th style="padding:12px; border:1px solid #444;">Action</th><th style="padding:12px; border:1px solid #444;">Amount</th><th style="padding:12px; border:1px solid #444;">Time</th></tr>
            {% for l in logs %}<tr style="text-align:center;"><td style="padding:12px; border:1px solid #444;">{{ l.action_type }}</td><td style="padding:12px; border:1px solid #444; color:#34d399; font-weight:900;">{{ l.amount }} USDD</td><td style="padding:12px; border:1px solid #444;">{{ l.log_time }}</td></tr>{% endfor %}
        </table>
    </div>
</body>
</html>
"""

ADMIN_GAMES_PAGE = LANG_BAR + """
<!DOCTYPE html>
<html lang="{{ t.dir }}" dir="{{ t.dir }}">
<head><meta charset="UTF-8"><title>لوحة الألعاب - 9D</title></head>
<body style="font-family:'Segoe UI', Tahoma, sans-serif; background:radial-gradient(circle at center, #151928 0%, #070a12 100%); color:#fff; text-align:center; padding:35px;">
    <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(20,24,38,0.9); padding:18px 25px; border-radius:16px; border:2px solid #ffd700; max-width:600px; margin:0 auto 30px auto;">
        <h2 style="color:#ffd700; margin:0;">🎮 لوحة تحكم الألعاب</h2>
        <a href="/dashboard" style="background:#3b82f6; color:#fff; padding:10px 18px; text-decoration:none; border-radius:10px; font-weight:900;">{{ t.back_dash }}</a>
    </div>
    {% if msg %}<p style="color:#34d399; font-weight:900; background:rgba(52,211,153,0.15); padding:12px; border-radius:10px; max-width:500px; margin:0 auto 20px auto;">{{ msg }}</p>{% endif %}
    <div style="background:rgba(25,30,48,0.9); border:3px solid #ffd700; padding:35px; border-radius:22px; max-width:500px; margin:20px auto; box-shadow:0 25px 60px rgba(0,0,0,0.8);">
        <form method="POST">
            <label style="color:#ffd700; font-weight:900; font-size:18px;">رقم فائز مسبق (الرقم الحنون):</label><br>
            <input type="number" name="forced_winning_number" value="{{ forced_val }}" min="0" max="50" style="padding:14px; margin:15px 0; background:rgba(10,13,22,0.9); color:#fff; border:1px solid rgba(255,255,255,0.2); border-radius:10px; width:80%; text-align:center; font-size:20px;">
            <br>
            <button type="submit" style="padding:14px 25px; background:linear-gradient(135deg,#22c55e,#15803d); color:#fff; font-weight:900; border:none; border-radius:10px; cursor:pointer; width:80%; font-size:16px; box-shadow:0 8px 20px rgba(34,197,94,0.4);">حفظ الرقم</button>
        </form>
    </div>
</body>
</html>
"""

ADMIN_ACCOUNTING_PAGE = LANG_BAR + """
<!DOCTYPE html>
<html lang="{{ t.dir }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>برنامج المحاسبة - 9D</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: radial-gradient(circle at center, #151928 0%, #070a12 100%); color: #f8fafc; padding: 25px; }
        .admin-header { display: flex; justify-content: space-between; align-items: center; background: rgba(20,24,38,0.9); padding: 18px 25px; border-radius: 16px; border: 2px solid #ffd700; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.7); }
        .vault-box { background: linear-gradient(135deg, rgba(6,95,70,0.95), rgba(4,120,87,0.95)); backdrop-filter: blur(20px); border: 3px solid #34d399; padding: 30px; border-radius: 22px; text-align: center; margin-bottom: 30px; box-shadow: 0 20px 50px rgba(0,0,0,0.8); }
        .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }
        @media(max-width: 900px) { .stats-grid { grid-template-columns: repeat(2, 1fr); } }
        .stat-card { background: rgba(25,30,48,0.9); border: 1px solid rgba(255,255,255,0.1); padding: 22px; border-radius: 16px; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.6); }
        .stat-val { font-size: 28px; font-weight: 900; color: #34d399; margin-top: 10px; }
        .panel-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px; }
        @media(max-width: 900px) { .panel-grid { grid-template-columns: 1fr; } }
        .panel-box { background: rgba(25,30,48,0.9); padding: 22px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 10px 25px rgba(0,0,0,0.6); }
        input, select { width: 100%; padding: 14px; margin: 10px 0; border-radius: 10px; background: rgba(10,13,22,0.9); color: white; border: 1px solid rgba(255,255,255,0.2); box-sizing: border-box; }
        button { padding: 14px; font-weight: 900; border: none; border-radius: 10px; cursor: pointer; width: 100%; margin-top: 10px; transition: 0.3s; }
        .btn-sell { background: #22c55e; color: #000; box-shadow:0 5px 15px rgba(34,197,94,0.4); }
        .btn-buy { background: #ef4444; color: white; box-shadow:0 5px 15px rgba(239,68,68,0.4); }
        .btn-card { background: #ffd700; color: #000; box-shadow:0 5px 15px rgba(255,215,0,0.4); }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; display: block; overflow-x: auto; }
        th, td { border: 1px solid #444; padding: 12px; text-align: center; font-size: 14px; }
        th { background: rgba(10,13,22,0.9); color: #ffd700; }
    </style>
</head>
<body>
    <div class="admin-header">
        <h2 style="color: #ffd700; margin: 0;">📊 برنامج المحاسبة والخزنة المركزية (9D)</h2>
        <a href="/dashboard" style="background:#3b82f6; color:#fff; padding:10px 18px; text-decoration:none; border-radius:10px; font-weight:900;">{{ t.back_dash }}</a>
    </div>
    
    {% if msg %}<div style="background: rgba(6,95,70,0.9); color: #34d399; padding: 14px; border-radius: 12px; margin-bottom: 25px; text-align: center; font-weight: 900; border:1px solid #34d399;">{{ msg }}</div>{% endif %}

    <div class="vault-box">
        <h3 style="margin: 0; color: #a7f3d0; font-size: 20px;">🏦 خزنة الشركة الأساسية (رصيد المليون USDD)</h3>
        <div style="font-size: 50px; font-weight: 900; color: #fff; margin: 15px 0; text-shadow:0 0 20px rgba(255,215,0,0.5);">{{ vault_balance }} USDD</div>
    </div>

    <div class="stats-grid">
        <div class="stat-card" style="border: 2px solid #38bdf8;">
            <div style="color: #38bdf8; font-weight: 900;">صندوق النقاط المباعة</div>
            <div class="stat-val" style="color: #38bdf8;">{{ total_points_sold }} USDD</div>
        </div>
        <div class="stat-card">
            <div style="color: #94a3b8;">صندوق رهانات الألعاب</div>
            <div class="stat-val" style="color: #22c55e;">{{ total_game_bets }} USDD</div>
        </div>
        <div class="stat-card">
            <div style="color: #94a3b8;">صندوق الجوائز المدفوعة</div>
            <div class="stat-val" style="color: #ef4444;">{{ total_payouts }} USDD</div>
        </div>
        <div class="stat-card" style="border: 2px solid #ffd700; background: linear-gradient(135deg, rgba(37,32,16,0.9), rgba(22,22,22,0.9));">
            <div style="color: #ffd700; font-weight: 900;">أرباح / خسارة الشركة</div>
            <div class="stat-val" style="color: {% if net_game_result >= 0 %}#34d399{% else %}#ef4444{% endif %};">
                {% if net_game_result > 0 %}+{{ net_game_result }}{% else %}{{ net_game_result }}{% endif %} USDD
            </div>
        </div>
    </div>

    <div class="panel-grid">
        <div class="panel-box" style="border: 2px dashed #ffd700;">
            <h3 style="color: #ffd700; margin-top: 0;">🎟️ خلق كودات بطاقات الشحن</h3>
            <form method="POST">
                <input type="hidden" name="action" value="generate_card">
                <label>فئة البطاقة:</label>
                <select name="card_amount" required>
                    <option value="10">10 USDD</option><option value="20">20 USDD</option><option value="50">50 USDD</option><option value="100">100 USDD</option>
                </select>
                <button type="submit" class="btn-card">توليد كود بطاقة جديد</button>
            </form>
        </div>

        <div class="panel-box">
            <h3 style="color: #22c55e; margin-top: 0;">⚡ بيع عملات مباشر للزبون</h3>
            <form method="POST">
                <input type="hidden" name="action" value="sell_currency">
                <label>اختر الزبون:</label>
                <select name="target_user" required>
                    <option value="">اختر الحساب</option>
                    {% for u in users_list %}<option value="{{ u.username }}">{{ u.username }} (رصيده: {{ u.balance }} USDD)</option>{% endfor %}
                </select>
                <label>المبلغ (USDD):</label><input type="number" name="amount" placeholder="المبلغ" min="1" required>
                <button type="submit" class="btn-sell">إتمام البيع من الخزنة</button>
            </form>
        </div>

        <div class="panel-box" style="border: 2px solid #ef4444;">
            <h3 style="color: #ef4444; margin-top: 0;">💸 استرجاع العملات من الزبون</h3>
            <form method="POST">
                <input type="hidden" name="action" value="buy_back_currency">
                <label>اختر الزبون:</label>
                <select name="target_user" required>
                    <option value="">اختر الحساب</option>
                    {% for u in users_list %}<option value="{{ u.username }}">{{ u.username }} (رصيده: {{ u.balance }} USDD)</option>{% endfor %}
                </select>
                <label>المبلغ المراد استرجاعه (USDD):</label><input type="number" name="amount" placeholder="المبلغ" min="1" required>
                <button type="submit" class="btn-buy">استرجاع الرصيد للخزنة</button>
            </form>
        </div>
    </div>

    <div class="panel-box" style="margin-bottom: 30px;">
        <h3 style="color: #38bdf8; margin-top: 0;">🎟️ سجل بطاقات الشحن والأكواد المُولدة</h3>
        <table>
            <tr><th>الكود</th><th>الفئة</th><th>الحالة</th><th>مستخدم من قِبل</th><th>تاريخ الإنشاء</th></tr>
            {% for card in cards_list %}
            <tr>
                <td><code style="color: #ffd700; font-size: 16px; font-weight:900;">{{ card.code }}</code></td>
                <td style="font-weight: 900;">{{ card.amount }} USDD</td>
                <td>
                    {% if card.is_used %}<span style="color: #ef4444; font-weight: 900;">مستخدمة ❌</span>
                    {% else %}<span style="color: #34d399; font-weight: 900;">متاحة للبيع ✅</span>{% endif %}
                </td>
                <td>{{ card.used_by if card.used_by else '---' }}</td>
                <td>{{ card.created_at }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>

    <div class="panel-box">
        <h3 style="color: #ffd700; margin-top: 0;">📋 سجل العمليات المالية</h3>
        <table>
            <tr><th>نوع العملية</th><th>المسؤول</th><th>الهدف</th><th>المبلغ (USDD)</th><th>التوقيت المحلي</th></tr>
            {% for log in logs %}
            <tr>
                <td><b>{{ log.action_type }}</b></td><td style="color: #ffd700; font-weight:900;">{{ log.admin_name }}</td><td>{{ log.target_user }}</td>
                <td style="color: #34d399; font-weight: 900;">{{ log.amount }} USDD</td><td>{{ log.log_time }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
