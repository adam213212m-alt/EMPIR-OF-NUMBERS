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

# --- جدول حجز إمبراطورية الأرقام (5 مربعات فاخرة بشعار التاج) ---
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

class RouletteGlobalState(db.Model):
    __tablename__ = 'roulette_global_state'
    id = db.Column(db.Integer, primary_key=True)
    total_global_spins = db.Column(db.Integer, default=0)

class RevealAndWinGlobalState(db.Model):
    __tablename__ = 'reveal_and_win_global'
    id = db.Column(db.Integer, primary_key=True)
    total_spins = db.Column(db.Integer, default=0)

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
    if not LuxuryGoldenState.query.get(1):
        db.session.add(LuxuryGoldenState(id=1, winning_number=0, status='idle', draw_end_time=0, forced_winning_number=0))
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
        'game4': 'عجلة الأرقام', 'game5': 'اكشف واربح', 'game6': 'الرقم الحنون الفاخر',
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
        'game4': 'Wheel of Numbers', 'game5': 'Reveal & Win', 'game6': 'Luxury Golden Box',
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
        'game4': 'Roue des Nombres', 'game5': 'Révéler & Gagner', 'game6': 'Boîte Dorée de Luxe',
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
        'game4': 'گردونه اعداد', 'game5': 'بگشای و ببر', 'game6': 'صندوق طلایی لوکس',
        'cost': 'هزینه', 'prize': 'جایزه', 'book': 'رزرو', 'cancel': 'لغو', 'booked': 'رزرو شده',
        'spin': 'چرخش گردونه', 'reveal': 'باز کردن جعبه‌ها', 'draw_now': 'قرعه‌کشی (مدیر)'
    },
    'es': {
        'dir': 'ltr', 'title': 'Imperio de los Números', 'subtitle': 'Plataforma Interactiva 12D',
        'login': 'Iniciar Sesión', 'username': 'Usuario', 'password': 'Contraseña', 'balance': 'Saldo',
        'recharge': 'Recargar Saldo', 'withdraw': 'Retirar Saldo', 'change_pass': 'Cambiar Contraseña', 'logout': 'Cerrar Sesión',
        'dashboard': 'Panel Principal', 'back_dash': '🏠 Inicio',
        'withdraw_warning': '⚠️ Aviso: Comisión del 10%.',
        'wish_withdraw': 'Retirar Wish Money', 'visa_withdraw': 'Retirar Visa', 'usdt_withdraw': 'Recibir USDT',
        'success_msg': 'Revisaremos su solicitud en 1 a 120 minutos.',
        'game1': 'Número de Oro', 'game2': 'Ruleta de la Suerte', 'game3': 'Imperio de Números',
        'game4': 'Rueda de Números', 'game5': 'Descubre y Gana', 'game6': 'Caja Dorada de Lujo',
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
        'game4': 'Zahlenrad', 'game5': 'Aufdecken & Gewinnen', 'game6': 'Goldene Luxusbox',
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

@app.route('/api/golden_status')
def api_golden_status():
    current_time = time.time()
    draw_state = GameDrawState.query.get(1)
    status, winning_number, remaining, winner_username = 'idle', 0, 0, '---'
    if draw_state:
        status = draw_state.status
        winning_number = draw_state.winning_number
        if status == 'finished':
            winner_b = GoldenNumberBooking.query.filter_by(number=winning_number).first()
            winner_username = winner_b.username if winner_b else "لا يوجد رابح (رقم لم يتم حجزه)"
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
        "my_total_spent": len(my_booked) * 20.0,
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
            if user.balance >= 20.0 and not GoldenNumberBooking.query.filter_by(number=number).first():
                user.balance -= 20.0
                vault.vault_balance += 20.0
                db.session.add(FinancialLog(action_type='مبيع رهان لعبة الرقم الحنون', admin_name='system', target_user=username, amount=20.0, log_time=get_local_time()))
                db.session.add(GoldenNumberBooking(username=username, number=number, booking_date=get_local_time()))
                db.session.commit()
                return jsonify({"success": True, "msg": f"تم حجز الرقم {number} مقابل 20 USDD!"})
            else:
                return jsonify({"success": False, "msg": "رصيد غير كافي (يحتاج 20 USDD) أو الرقم محجوز مسبقاً!"})
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
            if draw_state.forced_winning_number >= 1 and draw_state.forced_winning_number <= 50:
                winning_num = draw_state.forced_winning_number
            else:
                winning_num = random.randint(1, 50)

            winner_name = "لا يوجد رابح (رقم لم يتم حجزه)"
            winner_b = GoldenNumberBooking.query.filter_by(number=winning_num).first()
            if winner_b:
                winner_name = winner_b.username
                winner_u = User.query.filter_by(username=winner_b.username).first()
                if winner_u:
                    winner_u.balance += 750.0
                    vault.vault_balance -= 750.0
                    db.session.add(FinancialLog(action_type='جائزة الرقم الحنون', admin_name='admin1', target_user=winner_u.username, amount=750.0, log_time=get_local_time()))
            
            draw_state.winning_number = winning_num
            draw_state.status = 'finished'
            draw_state.draw_end_time = time.time() + 20.0
            draw_state.forced_winning_number = 0
            db.session.commit()
            return jsonify({"success": True, "msg": f"Winner: #{winning_num} | الرابح: {winner_name}"})

    bookings = {b.number: b.username for b in GoldenNumberBooking.query.all()}
    my_nums = [b.number for b in GoldenNumberBooking.query.filter_by(username=username).all()]
    return render_template_string(GAME_GOLDEN_PAGE, t=t, username=username, balance=user.balance, bookings=bookings, winning_number=draw_state.winning_number, draw_status=draw_state.status, my_booked_nums=my_nums, my_total_spent=len(my_nums)*20.0, msg=msg)

# --- لعبة إمبراطورية الأرقام (Game 3 الفاخرة - 5 مربعات بشعار التاج والجائزة 2000 USDD) ---
@app.route('/game_numbers_empire', methods=['GET', 'POST'])
def game_numbers_empire():
    if 'username' not in session: return redirect(url_for('login'))
    username = session['username']
    user = User.query.filter_by(username=username).first()
    vault = SystemVault.query.get(1)
    e_state = NumbersEmpireState.query.get(1)
    t = get_t()
    msg = None
    
    current_time = time.time()
    if e_state and e_state.status == 'finished' and current_time >= e_state.draw_end_time:
        NumbersEmpireBooking.query.delete()
        e_state.winning_number, e_state.status, e_state.draw_end_time = 0, 'idle', 0
        db.session.commit()

    if request.method == 'POST':
        action_type = request.form.get('action_type')
        if action_type == 'book' and e_state.status == 'idle':
            box_num = int(request.form.get('box_number', 0))
            if user.balance >= 500.0 and not NumbersEmpireBooking.query.filter_by(number=box_num).first():
                user.balance -= 500.0
                vault.vault_balance += 500.0
                db.session.add(FinancialLog(action_type='مبيع رهان إمبراطورية الأرقام الفاخرة', admin_name='system', target_user=username, amount=500.0, log_time=get_local_time()))
                db.session.add(NumbersEmpireBooking(username=username, number=box_num, booking_date=get_local_time()))
                db.session.commit()
                return jsonify({"success": True, "msg": f"تم حجز المربع الفاخر #{box_num} بنجاح مقابل 500 USDD!"})
            else:
                return jsonify({"success": False, "msg": "رصيد غير كافي (يحتاج 500 USDD) أو المربع محجوز مسبقاً!"})
        elif action_type == 'cancel' and e_state.status == 'idle':
            box_num = int(request.form.get('box_number', 0))
            b = NumbersEmpireBooking.query.filter_by(number=box_num, username=username).first()
            if b:
                db.session.delete(b)
                user.balance += 500.0
                vault.vault_balance -= 500.0
                db.session.add(FinancialLog(action_type='استرجاع رهان إمبراطورية الأرقام', admin_name='system', target_user=username, amount=500.0, log_time=get_local_time()))
                db.session.commit()
                return jsonify({"success": True, "msg": "تم التراجع واسترداد 500 USDD!"})
        elif action_type == 'admin_draw' and username == 'admin1':
            forced = e_state.forced_winning_number
            if forced >= 1 and forced <= 5:
                winning_num = forced
            else:
                booked_list = [b.number for b in NumbersEmpireBooking.query.all()]
                winning_num = random.choice(booked_list) if booked_list else random.randint(1, 5)

            winner_name = "لا يوجد رابح (مربع لم يُحجز)"
            winner_b = NumbersEmpireBooking.query.filter_by(number=winning_num).first()
            if winner_b:
                winner_name = winner_b.username
                winner_u = User.query.filter_by(username=winner_b.username).first()
                if winner_u:
                    winner_u.balance += 2000.0
                    vault.vault_balance -= 2000.0
                    db.session.add(FinancialLog(action_type='جائزة إمبراطورية الأرقام', admin_name='admin1', target_user=winner_u.username, amount=2000.0, log_time=get_local_time()))
            
            e_state.winning_number = winning_num
            e_state.status = 'finished'
            e_state.draw_end_time = time.time() + 20.0
            e_state.forced_winning_number = 0
            db.session.commit()
            return jsonify({"success": True, "msg": f"مبروك للرقم #{winning_num} لقد فزت بـ 2000 USDD | الرابح: {winner_name}"})

    bookings = {b.number: b.username for b in NumbersEmpireBooking.query.all()}
    my_nums = [b.number for b in NumbersEmpireBooking.query.filter_by(username=username).all()]
    return render_template_string(GAME_NUMBERS_EMPIRE_PAGE, t=t, username=username, balance=user.balance, bookings=bookings, winning_number=e_state.winning_number, draw_status=e_state.status, my_booked_nums=my_nums, my_total_spent=len(my_nums)*500.0, forced_val=e_state.forced_winning_number, msg=msg)

@app.route('/game_numbers_empire_admin_set', methods=['POST'])
def game_numbers_empire_admin_set():
    if 'username' not in session or session.get('username') != 'admin1': return jsonify({"success": False})
    forced_val = request.form.get('forced_winning_number', '').strip()
    e_state = NumbersEmpireState.query.get(1)
    if e_state:
        e_state.forced_winning_number = int(forced_val) if forced_val else 0
        db.session.commit()
    return jsonify({"success": True, "msg": "تم حفظ الرقم الرابح بنجاح!"})

# --- لعبة روليت الحظ مع الخصم الفوري عند النقر، جائزة 20 USDD، ونقرات 40 و 360 الخاصة ---
@app.route('/game_roulette', methods=['GET', 'POST'])
def game_roulette():
    if 'username' not in session: return redirect(url_for('login'))
    username = session['username']
    user = User.query.filter_by(username=username).first()
    vault = SystemVault.query.get(1)
    t = get_t()
    
    all_numbers = list(range(0, 37))
    
    if request.method == 'POST':
        try:
            data = request.get_json(silent=True) or request.form
            selected_numbers = data.get('selected_numbers', [])
            if isinstance(selected_numbers, str):
                selected_numbers = json.loads(selected_numbers)
            selected_numbers = [int(n) for n in selected_numbers]
            
            if selected_numbers:
                db.session.add(FinancialLog(action_type='مبيع رهان روليت 12D', admin_name='system', target_user=username, amount=float(len(selected_numbers)), log_time=get_local_time()))
                
                g_state = RouletteGlobalState.query.get(1)
                if not g_state:
                    g_state = RouletteGlobalState(id=1, total_global_spins=0)
                    db.session.add(g_state)
                g_state.total_global_spins += 1
                
                is_360th_win = (g_state.total_global_spins % 360 == 0)
                is_40th_win = (g_state.total_global_spins % 40 == 0)
                
                if is_360th_win:
                    winning_num = random.choice(selected_numbers)
                    payout = 100.0
                    user.balance += payout
                    vault.vault_balance -= payout
                    db.session.add(FinancialLog(action_type='جائزة روليت الكبرى (النقرة 360 - 100 USDD)', admin_name='system', target_user=username, amount=payout, log_time=get_local_time()))
                    msg = f"🌟 مبروك! النقرة رقم #{g_state.total_global_spins} في المنصة أصابت الحدث الأكبر وفزت بـ 100 USDD!"
                elif is_40th_win:
                    winning_num = random.choice(selected_numbers)
                    payout = 20.0
                    user.balance += payout
                    vault.vault_balance -= payout
                    db.session.add(FinancialLog(action_type='جائزة روليت السحب المميز (النقرة 40 - 20 USDD)', admin_name='system', target_user=username, amount=payout, log_time=get_local_time()))
                    msg = f"🏆 تهانينا! النقرة رقم #{g_state.total_global_spins} فازت بجائزة الـ 20 USDD!"
                else:
                    unselected_nums = [n for n in all_numbers if n not in selected_numbers]
                    if unselected_nums and random.random() < 0.75:
                        winning_num = random.choice(unselected_nums)
                    else:
                        winning_num = random.choice(all_numbers)
                    
                    payout = 0
                    if winning_num in selected_numbers:
                        payout = 20.0
                        user.balance += payout
                        vault.vault_balance -= payout
                        db.session.add(FinancialLog(action_type='جائزة روليت 20 USDD', admin_name='system', target_user=username, amount=payout, log_time=get_local_time()))
                        msg = f"🎉 مبروك! استقر الروليت على رقمك #{winning_num} وفزت بـ 20 USDD!"
                    else:
                        msg = f"❌ حظ أوفر! استقر الروليت على الرقم #{winning_num}"
                
                db.session.commit()
                return jsonify({"success": True, "winning_number": winning_num, "balance": user.balance, "msg": msg})
        except Exception as e:
            return jsonify({"success": False, "msg": str(e)})

    return render_template_string(GAME_ROULETTE_GLOBAL_PAGE, t=t, balance=user.balance, username=username)

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
            db.session.add(FinancialLog(action_type='مبيع رهان عجلة الأرقام 35%', admin_name='system', target_user=user.username, amount=bet_amt, log_time=get_local_time()))
            
            if random.random() < 0.65:
                winning_num = 99
            else:
                winning_num = random.randint(1, 20)

            if winning_num in nums:
                is_win = True
                user.balance += 12.0
                vault.vault_balance -= 12.0
                db.session.add(FinancialLog(action_type='جائزة عجلة الأرقام 35%', admin_name='system', target_user=user.username, amount=12.0, log_time=get_local_time()))
                msg = f"Win! #{winning_num}"
            else: msg = f"Loss!"
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
            db.session.add(FinancialLog(action_type='مبيع رهان اكشف واربح 35%', admin_name='system', target_user=user.username, amount=1.0, log_time=get_local_time()))
            
            if random.random() < 0.65:
                rev = ['1', '3', '5']
                prize = 0.0
            else:
                rev = ['7', '7', '7']
                prize = 13.0
                user.balance += prize
                vault.vault_balance -= prize
                db.session.add(FinancialLog(action_type='جائزة اكشف واربح 35%', admin_name='system', target_user=user.username, amount=prize, log_time=get_local_time()))

            msg = f"Win {prize} USDD!" if prize > 0 else "Try Again!"
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
                db.session.add(FinancialLog(action_type='مبيع رهان الرقم الفاخر 35%', admin_name='system', target_user=username, amount=50.0, log_time=get_local_time()))
                db.session.add(LuxuryGoldenBooking(username=username, box_number=box, booking_date=get_local_time()))
                db.session.commit()
                msg = f"Box #{box} (50 USDD)"
        elif 'admin_execute_luxury_draw' in request.form and username == 'admin1':
            books = LuxuryGoldenBooking.query.all()
            if books:
                box = random.choice([b.box_number for b in books])
                winner = LuxuryGoldenBooking.query.filter_by(box_number=box).first()
                w_user = User.query.filter_by(username=winner.username).first()
                w_user.balance += 150.0
                vault.vault_balance -= 150.0
                db.session.add(FinancialLog(action_type='جائزة الرقم الفاخر 35%', admin_name='admin1', target_user=w_user.username, amount=150.0, log_time=get_local_time()))
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
        forced_val = request.form.get('forced_winning_number', '').strip()
        draw_state.forced_winning_number = int(forced_val) if forced_val else 0
        db.session.commit()
        msg = "تم تحديث إعدادات السحب بنجاح!"
    
    g_state = RouletteGlobalState.query.get(1)
    total_spins = g_state.total_global_spins if g_state else 0
    rem_40 = 40 - (total_spins % 40)
    rem_360 = 360 - (total_spins % 360)

    return render_template_string(ADMIN_GAMES_PAGE, t=t, forced_val=draw_state.forced_winning_number, total_spins=total_spins, rem_40=rem_40, rem_360=rem_360, msg=msg)

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
        elif action == 'sell_1000':
            target = request.form.get('target_user')
            amount = 1000.0
            if vault.vault_balance >= amount and target:
                vault.vault_balance -= amount
                User.query.filter_by(username=target).first().balance += amount
                db.session.add(FinancialLog(action_type='بيع باقة 1000 USDD', admin_name='admin1', target_user=target, amount=amount, log_time=get_local_time()))
                db.session.commit()
                msg = f"تم بيع باقة 1000 USDD للزبون {target} بنجاح!"
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
    tp_sold = db.session.query(db.func.sum(FinancialLog.amount)).filter(FinancialLog.action_type.in_(['بيع عملات للزبون', 'شحن عبر بطاقة كود', 'بيع باقة 1000 USDD'])).scalar() or 0.0
    tg_bets = db.session.query(db.func.sum(FinancialLog.amount)).filter(FinancialLog.action_type.like('%مبيع رهان%')).scalar() or 0.0
    tpayouts = db.session.query(db.func.sum(FinancialLog.amount)).filter(FinancialLog.action_type.like('%جائزة%')).scalar() or 0.0
    net = tg_bets - tpayouts
    return render_template_string(ADMIN_ACCOUNTING_PAGE, t=t, vault_balance=vault.vault_balance, logs=logs, total_points_sold=tp_sold, total_game_bets=tg_bets, total_payouts=tpayouts, net_game_result=net, users_list=User.query.all(), cards_list=RechargeCard.query.order_by(RechargeCard.id.desc()).all(), msg=msg)

# --- قوالب HTML 12D الفائقة ---

LOGIN_PAGE = LANG_BAR + """
<!DOCTYPE html>
<html lang="{{ t.dir }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><title>{{ t.title }} - 12D</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: radial-gradient(circle at center, #1a1c29 0%, #0b0f19 100%); color: #f8fafc; display: flex; justify-content: center; align-items: center; height: 90vh; margin: 0; flex-direction: column; }
        .login-box { background: rgba(20, 24, 38, 0.85); backdrop-filter: blur(25px); padding: 50px; border-radius: 25px; width: 380px; text-align: center; border: 2px solid rgba(255,215,0,0.5); box-shadow: 0 30px 60px rgba(0,0,0,0.9); }
        input { width: 100%; padding: 15px; margin: 12px 0; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); background: rgba(10, 13, 22, 0.8); color: white; box-sizing: border-box; font-size: 16px; outline: none; }
        button { width: 100%; padding: 15px; background: linear-gradient(135deg, #ffd700, #ff8c00); color: #000; font-weight: 900; border: none; border-radius: 12px; cursor: pointer; margin-top: 15px; font-size: 18px; box-shadow: 0 10px 30px rgba(255,215,0,0.5); }
        .error { color: #ef4444; margin-bottom: 15px; font-weight: bold; background: rgba(239,68,68,0.15); padding: 10px; border-radius: 8px; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2 style="color: #ffd700; margin-top: 0;">👑 {{ t.title }}</h2>
        <p style="color: #94a3b8; font-size: 13px;">{{ t.subtitle }}</p>
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
    <title>{{ t.dashboard }} - 12D</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: radial-gradient(circle at center, #151928 0%, #070a12 100%); color: #fff; margin: 0; padding: 20px; min-height: 100vh; }
        .header { display: flex; justify-content: space-between; align-items: center; background: rgba(20, 24, 38, 0.9); backdrop-filter: blur(20px); padding: 18px 30px; border-radius: 18px; border-bottom: 3px solid #ffd700; flex-wrap: wrap; gap: 15px; box-shadow: 0 15px 35px rgba(0,0,0,0.7); }
        .financial-bar { display: flex; justify-content: space-between; max-width: 950px; margin: 30px auto; gap: 20px; }
        .fin-card { flex: 1; background: linear-gradient(145deg, rgba(24,34,50,0.9), rgba(15,23,42,0.9)); border: 2px solid rgba(56,189,248,0.5); padding: 22px; border-radius: 20px; text-align: center; box-shadow: 0 20px 40px rgba(0,0,0,0.8); }
        .fin-card button { background: linear-gradient(135deg, #38bdf8, #0284c7); color: #070a12; padding: 14px 22px; font-weight: 900; border: none; border-radius: 12px; cursor: pointer; margin-top: 12px; font-size: 16px; width: 100%; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(5, 7, 12, 0.9); justify-content: center; align-items: center; z-index: 1000; }
        .modal-content { background: rgba(25, 30, 48, 0.95); padding: 35px; border-radius: 22px; border: 3px solid #ffd700; width: 440px; text-align: center; position: relative; }
        .icons-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 30px; max-width: 1000px; margin: 40px auto; }
        @media (max-width: 900px) { .icons-grid { grid-template-columns: repeat(2, 1fr); } }
        .icon-card { background: linear-gradient(145deg, rgba(25,30,48,0.95), rgba(12,15,25,0.95)); border: 3px solid rgba(184,134,11,0.6); border-radius: 28px; padding: 35px 20px; text-align: center; text-decoration: none; box-shadow: 0 20px 45px rgba(0,0,0,0.9); transition: 0.3s; }
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

    <div id="globalNotificationBanner" style="display:none; background: linear-gradient(135deg, #f59e0b, #d97706); color: #000; padding: 18px; border-radius: 14px; max-width: 950px; margin: 20px auto; text-align: center; font-weight: 900; font-size: 20px; border: 2px solid #fff;">
        🔔 <span id="globalNotificationText"></span>
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
            <div style="display:flex; gap:12px; margin:25px 0;">
                <button onclick="alert('{{ t.success_msg }}')" style="flex:1; background:#25d366; color:#fff; padding:14px; border:none; border-radius:12px; font-weight:900; cursor:pointer;">Wish Money</button>
                <button onclick="alert('{{ t.success_msg }}')" style="flex:1; background:#3b82f6; color:#fff; padding:14px; border:none; border-radius:12px; font-weight:900; cursor:pointer;">Visa</button>
            </div>
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
            <p style="color:#ef4444; font-size:13px; font-weight:900; background:rgba(239,68,68,0.15); padding:12px; border-radius:10px; border:1px solid #ef4444;">{{ t.withdraw_warning }}</p>
            <form method="POST" style="display:flex; flex-direction:column; gap:15px; margin-top:20px;">
                <button type="submit" name="action" value="withdraw_wish" onclick="window.open('https://wa.me/96176030208?text=Withdraw Wish: {{ username }}', '_blank'); alert('{{ t.success_msg }}');" style="background:#25d366; color:#fff; padding:14px; border:none; border-radius:12px; font-weight:900; cursor:pointer;">{{ t.wish_withdraw }}</button>
                <button type="submit" name="action" value="withdraw_visa" onclick="alert('{{ t.success_msg }}')" style="background:#3b82f6; color:#fff; padding:14px; border:none; border-radius:12px; font-weight:900; cursor:pointer;">{{ t.visa_withdraw }}</button>
                <div style="background:rgba(10,13,22,0.9); padding:15px; border-radius:12px; text-align:right;">
                    <label style="font-size:13px; color:#ffd700; font-weight:bold;">USDT Address:</label>
                    <input type="text" name="usdt_acc" placeholder="Address..." style="width:100%; padding:12px; background:rgba(5,7,12,0.9); color:#fff; border:1px solid rgba(255,255,255,0.2); border-radius:10px; box-sizing:border-box; margin:8px 0;">
                    <button type="submit" name="action" value="withdraw_usdt" onclick="alert('{{ t.success_msg }}')" style="width:100%; background:linear-gradient(135deg,#f59e0b,#d97706); color:#000; padding:12px; border:none; border-radius:10px; font-weight:900; cursor:pointer;">{{ t.usdt_withdraw }}</button>
                </div>
            </form>
        </div>
    </div>

    <!-- شبكة الألعاب -->
    <div class="icons-grid">
        <a href="/game_golden_number" class="icon-card"><div class="icon-logo">🏆</div><div class="icon-title">{{ t.game1 }}</div></a>
        <a href="/game_roulette" class="icon-card"><div class="icon-logo">🎰</div><div class="icon-title">{{ t.game2 }}</div></a>
        <a href="/game_numbers_empire" class="icon-card"><div class="icon-logo">🏛️</div><div class="icon-title">{{ t.game3 }}</div></a>
        <a href="/game_number_wheel" class="icon-card"><div class="icon-logo">🎡</div><div class="icon-title">{{ t.game4 }}</div></a>
        <a href="/game_reveal_and_win" class="icon-card"><div class="icon-logo">🎟️</div><div class="icon-title">{{ t.game5 }}</div></a>
        <a href="/game_golden_boxes_new" class="icon-card"><div class="icon-logo">🎁</div><div class="icon-title">{{ t.game6 }}</div></a>
    </div>

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
    <div style="background:rgba(20,24,38,0.9); padding:45px; border-radius:25px; border:2px solid #8b5cf6; width:380px; text-align:center;">
        <h3 style="color:#ffd700; margin-top:0; font-size:24px;">{{ t.change_pass }}</h3>
        {% if msg %}<p style="color:#34d399; font-weight:bold;">{{ msg }}</p>{% endif %}
        <form method="POST">
            <input type="password" name="old_password" placeholder="Old Password" required style="width:100%; padding:14px; margin:10px 0; background:rgba(10,13,22,0.9); color:#fff; border:1px solid rgba(255,255,255,0.2); border-radius:10px; box-sizing:border-box;">
            <input type="password" name="new_password" placeholder="New Password" required style="width:100%; padding:14px; margin:10px 0; background:rgba(10,13,22,0.9); color:#fff; border:1px solid rgba(255,255,255,0.2); border-radius:10px; box-sizing:border-box;">
            <input type="password" name="confirm_password" placeholder="Confirm Password" required style="width:100%; padding:14px; margin:10px 0; background:rgba(10,13,22,0.9); color:#fff; border:1px solid rgba(255,255,255,0.2); border-radius:10px; box-sizing:border-box;">
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
        .notice-box { background: linear-gradient(135deg, #1e3a8a, #1e1b4b); border: 2px solid #38bdf8; padding: 18px; border-radius: 16px; text-align: center; margin-bottom: 25px; }
        .my-box-panel { background: rgba(15,23,42,0.95); border: 2px solid #34d399; padding: 20px; border-radius: 18px; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px; }
        .grid { display:grid; grid-template-columns:repeat(10, 1fr); gap:12px; margin-top:25px; }
        @media(max-width: 768px) { .grid { grid-template-columns:repeat(5, 1fr); } }
        .cell { background:linear-gradient(145deg, #7c3aed, #4c1d95); border:3px solid #a78bfa; border-radius:16px; height:80px; display:flex; flex-direction:column; align-items:center; justify-content:center; font-weight:900; cursor:pointer; color:#fff; font-size: 22px; transition:0.3s; position: relative; }
        .cell:hover { border-color:#ffd700; transform: translateY(-5px); }
        .cell.booked { background: linear-gradient(145deg, #7f1d1d, #450a0a) !important; border-color:#ef4444 !important; cursor:not-allowed; }
        .cell.my { background: linear-gradient(145deg, #1e3a8a, #172554) !important; border-color:#3b82f6 !important; }
        .cell.winning-gold { background: linear-gradient(145deg, #fbbf24, #d97706) !important; border: 4px solid #fff !important; box-shadow: 0 0 35px #ffd700 !important; transform: scale(1.08); z-index: 10; color: #000 !important; }
        .global-alert { display:none; background: linear-gradient(135deg, #f59e0b, #d97706); color: #000; padding: 20px; border-radius: 16px; text-align: center; font-weight: 900; font-size: 22px; margin-bottom: 25px; border: 2px solid #fff; }
        .slot-11d-box { background: radial-gradient(circle, #0f172a 0%, #020617 100%); border: 4px solid #38bdf8; padding: 25px; border-radius: 22px; text-align: center; margin-top: 30px; box-shadow: 0 15px 40px rgba(56,189,248,0.4); }
        .slot-screen { font-size: 55px; font-weight: 900; color: #ffd700; background: #000; padding: 15px; border-radius: 14px; border: 2px solid #b8860b; display: inline-block; min-width: 140px; box-shadow: inset 0 0 20px rgba(255,215,0,0.5); letter-spacing: 5px; }
    </style>
</head>
<body>
    <div style="display:flex; justify-content:space-between; align-items:center; max-width:950px; margin:0 auto; background:rgba(20,24,38,0.9); padding:15px 25px; border-radius:15px; border:1px solid rgba(255,215,0,0.3); flex-wrap:wrap; gap:10px;">
        <h2 style="color:#ffd700; margin:0; font-size: 24px;">🏆 {{ t.game1 }} (12D Ultra)</h2>
        <div style="display:flex; gap:10px; align-items:center;">
            <button type="button" onclick="updateGameData()" style="background:#0284c7; color:#fff; border:none; padding:10px 16px; border-radius:10px; font-weight:bold; cursor:pointer; font-size:15px;">🔄 تحديث</button>
            <a href="/dashboard" style="background:linear-gradient(135deg,#3b82f6,#1d4ed8); color:#fff; padding:10px 18px; text-decoration:none; border-radius:10px; font-weight:900; font-size:15px;">{{ t.back_dash }}</a>
        </div>
        <div style="font-size: 18px; width: 100%; text-align: left;"><b>{{ t.balance }}: <span id="liveBalance">{{ balance }}</span> USDD</b></div>
    </div>

    <div class="card-3d">
        <div id="gameAlertBox" class="global-alert">
            🔔 <span id="gameAlertText"></span>
        </div>

        <div class="notice-box">
            <h3 style="color: #38bdf8; margin: 0 0 8px 0; font-size: 20px;">⏰ تنبيه موعد السحب اليومي والعداد التنازلي</h3>
            <p style="color: #f8fafc; margin: 0; font-size: 16px; font-weight: bold;">تجري عملية السحب لهذه اللعبة <b>مرة واحدة يومياً عند الساعة 22:00 (10 مساءً) بتوقيت بيروت</b>.</p>
            <div id="countdownTimer" style="font-size: 22px; font-weight: 900; color: #ffd700; margin-top: 10px;">⏳ وقت السحب المتبقي: جارِ الحساب...</div>
        </div>

        <div id="allBookedAlertBox" style="display:none; background: linear-gradient(135deg, #ef4444, #991b1b); color: #fff; padding: 18px; border-radius: 16px; text-align: center; font-weight: 900; font-size: 20px; margin-bottom: 25px; border: 2px solid #fff;">
            ⚠️ لم يعد هناك ارقام متاحة تم حجز الجميع
        </div>

        <div class="slot-11d-box">
            <h4 style="color: #38bdf8; margin: 0 0 10px 0; font-size: 20px;">🎰 شاشة السحب الحية (11D Reel)</h4>
            <div id="slotScreen" class="slot-screen">--</div>
            <div id="winnerAnnouncement" style="font-size: 18px; color: #34d399; margin-top: 12px; font-weight: 900;">في انتظار بدء السحب اليومي...</div>
        </div>

        <div class="my-box-panel" style="margin-top: 30px;">
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

        <p style="text-align:center; color:#ffd700; font-size:20px; font-weight:900;">
            {{ t.cost }}: 20 USDD | {{ t.prize }}: 750 USDD (يتم السحب من 1 إلى 50)
        </p>

        {% if msg %}<div id="actionMsg" style="background:rgba(6,95,70,0.9); color:#34d399; padding:15px; border-radius:12px; margin:15px 0; text-align:center; font-weight:900; font-size:18px;">{{ msg }}</div>{% endif %}

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
                <button type="button" onclick="handleAction('admin_draw', 0)" style="background:linear-gradient(135deg,#22c55e,#15803d); color:#fff; font-weight:900; padding:18px 45px; border:none; border-radius:16px; cursor:pointer; font-size:20px;">⚡ {{ t.draw_now }}</button>
            </div>
        {% endif %}
    </div>

    <script>
        history.pushState(null, null, location.href);
        window.onpopstate = function () {
            location.href = '/dashboard';
        };

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
                        msgBox.style = "background:rgba(6,95,70,0.9); color:#34d399; padding:15px; border-radius:12px; margin:15px 0; text-align:center; font-weight:900; font-size:18px;";
                        document.querySelector('.card-3d').prepend(msgBox);
                    }
                    msgBox.innerText = data.msg;
                }
                updateGameData();
            }).catch(err => {});
        }

        function updateCountdown() {
            let now = new Date();
            let utc = now.getTime() + (now.getTimezoneOffset() * 60000);
            let beirutTime = new Date(utc + (3600000 * 3));
            
            let target = new Date(beirutTime);
            target.setHours(22, 0, 0, 0);
            if (beirutTime > target) {
                target.setDate(target.getDate() + 1);
            }
            
            let diff = target - beirutTime;
            let hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            let minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            let seconds = Math.floor((diff % (1000 * 60)) / 1000);
            
            let timerEl = document.getElementById('countdownTimer');
            if(timerEl) {
                timerEl.innerText = `⏳ وقت السحب المتبقي: ${hours}س ${minutes}د ${seconds}ث`;
            }
        }
        setInterval(updateCountdown, 1000);

        let lastProcessedWinningNum = 0;

        function updateGameData() {
            fetch('/api/golden_status').then(res => res.json()).then(data => {
                let badge = document.getElementById('liveBalance');
                if(badge && badge.innerText !== String(data.balance)) {
                    badge.innerText = data.balance;
                }

                let alertBox = document.getElementById('gameAlertBox');
                let alertText = document.getElementById('gameAlertText');
                let slotScreen = document.getElementById('slotScreen');
                let winnerAnnounce = document.getElementById('winnerAnnouncement');
                let allBookedAlert = document.getElementById('allBookedAlertBox');

                let bookedKeys = Object.keys(data.bookings);
                if(bookedKeys.length >= 50) {
                    allBookedAlert.style.display = 'block';
                } else {
                    allBookedAlert.style.display = 'none';
                }

                if(data.status === 'finished' && data.winning_number) {
                    alertText.innerText = `🎉 إشعار الفائز: الفائز في لعبة الرقم الحنون هو الرقم #${data.winning_number} والرابح هو الحساب (${data.winner_username})`;
                    alertBox.style.display = 'block';

                    if(lastProcessedWinningNum !== data.winning_number) {
                        lastProcessedWinningNum = data.winning_number;
                        let counter = 0;
                        let rollInterval = setInterval(() => {
                            slotScreen.innerText = Math.floor(Math.random() * 50) + 1;
                            counter++;
                            if(counter > 15) {
                                clearInterval(rollInterval);
                                slotScreen.innerText = `#${data.winning_number}`;
                                winnerAnnounce.innerText = `🏆 الرقم الرابح الفائز: #${data.winning_number} | الرابح: ${data.winner_username}`;
                            }
                        }, 100);
                    }
                } else {
                    alertBox.style.display = 'none';
                    if(data.status === 'idle') {
                        lastProcessedWinningNum = 0;
                        if(slotScreen && slotScreen.innerText !== 'جاهز') {
                            slotScreen.innerText = 'جاهز';
                            winnerAnnounce.innerText = 'في انتظار بدء السحب اليومي...';
                        }
                    }
                }

                let myNumDisplay = document.getElementById('myNumbersDisplay');
                let mySpentDisplay = document.getElementById('mySpentDisplay');
                if(myNumDisplay) {
                    myNumDisplay.innerText = data.my_booked_nums.length > 0 ? data.my_booked_nums.join(', ') : 'لا توجد أرقام محجوزة حالياً';
                }
                if(mySpentDisplay) {
                    mySpentDisplay.innerText = data.my_total_spent + ' USDD';
                }

                let grid = document.getElementById('numbersGrid');
                if(grid) {
                    let currentUsername = "{{ username }}";
                    let html = '';
                    for(let i = 1; i <= 50; i++) {
                        let isWinningCell = (data.status === 'finished' && data.winning_number === i);

                        if(data.bookings[i]) {
                            let owner = data.bookings[i];
                            if(owner === currentUsername) {
                                html += `<button type="button" onclick="handleAction('cancel', ${i})" class="${isWinningCell ? 'cell winning-gold' : 'cell my'}" style="width:100%;">${i}<br><span style="font-size:12px;">${isWinningCell ? '👑 الفائز الذهبي' : 'تراجع (أنت)'}</span></button>`;
                            } else {
                                html += `<div class="${isWinningCell ? 'cell winning-gold' : 'cell booked'}">${i}<br><span style="font-size:12px;">${isWinningCell ? '👑 الفائز الذهبي' : owner}</span></div>`;
                            }
                        } else {
                            if(isWinningCell) {
                                html += `<div class="cell winning-gold">${i}<br><span style="font-size:12px; color:#000; font-weight:900;">👑 الفائز الذهبي</span></div>`;
                            } else {
                                html += `<button type="button" onclick="handleAction('book', ${i})" class="cell" style="width:100%;">${i}</button>`;
                            }
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

# --- لعبة إمبراطورية الأرقام (Game 3 - 5 مربعات فاخرة بشعار التاج والجائزة 2000 USDD) ---
GAME_NUMBERS_EMPIRE_PAGE = LANG_BAR + """
<!DOCTYPE html>
<html lang="{{ t.dir }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ t.game3 }} - 12D</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: radial-gradient(circle at center, #151928 0%, #070a12 100%); color: #f8fafc; margin: 0; padding: 25px; text-align: center; }
        .empire-card { background: linear-gradient(135deg, rgba(31,26,15,0.95), rgba(13,13,13,0.95)); border: 4px solid #ffd700; padding: 40px; border-radius: 30px; max-width: 850px; margin: 20px auto; box-shadow: 0 30px 70px rgba(0,0,0,0.9); }
        .notice-box { background: linear-gradient(135deg, #1e3a8a, #1e1b4b); border: 2px solid #38bdf8; padding: 18px; border-radius: 16px; text-align: center; margin-bottom: 25px; }
        .boxes-grid { display: flex; justify-content: center; gap: 20px; margin: 30px 0; flex-wrap: wrap; }
        .box-item { width: 120px; height: 130px; background: linear-gradient(145deg, #7c3aed, #4c1d95); border: 3px solid #ffd700; border-radius: 20px; color: #fff; font-size: 22px; font-weight: 900; cursor: pointer; display: flex; flex-direction: column; align-items: center; justify-content: center; transition: 0.3s; position: relative; box-shadow: 0 10px 25px rgba(0,0,0,0.6); }
        .box-item:hover { transform: translateY(-8px); border-color: #fff; }
        .box-item.booked { background: linear-gradient(145deg, #7f1d1d, #450a0a) !important; border-color: #ef4444 !important; }
        .box-item.my { background: linear-gradient(145deg, #1e3a8a, #172554) !important; border-color: #3b82f6 !important; }
        .box-item.winning-gold { background: linear-gradient(145deg, #fbbf24, #d97706) !important; border: 4px solid #fff !important; box-shadow: 0 0 40px #ffd700 !important; transform: scale(1.1); color: #000 !important; }
        .slot-box { font-size: 45px; font-weight: 900; color: #ffd700; background: #000; padding: 12px; border-radius: 14px; border: 3px solid #b8860b; display: inline-block; min-width: 130px; letter-spacing: 5px; box-shadow: inset 0 0 15px rgba(255,215,0,0.5); }
    </style>
</head>
<body>
    <div style="display:flex; justify-content:space-between; align-items:center; max-width:850px; margin:0 auto; background:rgba(20,24,38,0.9); padding:15px 25px; border-radius:15px; border:1px solid rgba(255,215,0,0.3); flex-wrap:wrap; gap:10px;">
        <h2 style="color:#ffd700; margin:0; font-size: 24px;">🏛️ {{ t.game3 }} (Luxury 5 Boxes 12D)</h2>
        <div>
            <a href="/dashboard" style="background:linear-gradient(135deg,#3b82f6,#1d4ed8); color:#fff; padding:10px 18px; text-decoration:none; border-radius:10px; font-weight:900; font-size:15px;">{{ t.back_dash }}</a>
        </div>
        <div style="font-size: 18px; width: 100%; text-align: left;"><b>{{ t.balance }}: <span id="liveBalance">{{ balance }}</span> USDD</b></div>
    </div>

    <div class="empire-card">
        <div class="notice-box">
            <h3 style="color: #38bdf8; margin: 0 0 8px 0; font-size: 18px;">⏰ موعد السحب اليومي</h3>
            <p style="color: #f8fafc; margin: 0; font-size: 16px; font-weight: bold;">السحب على هذه اللعبة كل يوم الساعة 23 بتوقيت مدينة بيروت.</p>
        </div>

        <div style="background: radial-gradient(circle, #0f172a 0%, #020617 100%); border: 3px solid #38bdf8; padding: 20px; border-radius: 20px; margin-bottom: 25px;">
            <h4 style="color: #38bdf8; margin: 0 0 10px 0; font-size: 18px;">🎰 شاشة السحب الحية</h4>
            <div id="empireSlot" class="slot-box">--</div>
            <div id="empireAnnouncement" style="font-size: 18px; color: #34d399; margin-top: 12px; font-weight: 900;">في انتظار السحب الفاخر...</div>
        </div>

        <p style="color:#ffd700; font-size:20px; font-weight:900;">سعر الحجز للمربع: 500 USDD | الجائزة الكبرى: 2000 USDD</p>

        {% if msg %}<div style="background:rgba(6,95,70,0.9); color:#34d399; padding:15px; border-radius:12px; margin:15px 0; font-weight:900; font-size:18px;">{{ msg }}</div>{% endif %}

        <!-- 5 مربعات فاخرة بشعار التاج -->
        <div class="boxes-grid" id="boxesGrid">
            {% for i in range(1, 6) %}
                {% if i in bookings %}
                    {% if bookings[i] == username %}
                        <button type="button" onclick="handleEmpireAction('cancel', {{ i }})" class="box-item my">
                            <span style="font-size: 28px;">👑</span>
                            <span>رقم {{ i }}</span>
                            <span style="font-size: 11px; color: #93c5fd; margin-top:4px;">حجزك (تراجع)</span>
                        </button>
                    {% else %}
                        <div class="box-item booked">
                            <span style="font-size: 28px;">👑</span>
                            <span>رقم {{ i }}</span>
                            <span style="font-size: 11px; color: #fca5a5; margin-top:4px;">{{ bookings[i] }}</span>
                        </div>
                    {% endif %}
                {% else %}
                    <button type="button" onclick="handleEmpireAction('book', {{ i }})" class="box-item">
                        <span style="font-size: 28px;">👑</span>
                        <span>رقم {{ i }}</span>
                        <span style="font-size: 11px; color: #ffd700; margin-top:4px;">متاح (500$)</span>
                    </button>
                {% endif %}
            {% endfor %}
        </div>

        <!-- خانة الزر السري للآدمن (تظهر فقط لصاحب اللعبة admin1) -->
        {% if username == 'admin1' %}
            <div style="background: rgba(15,23,42,0.9); border: 2px dashed #ffd700; padding: 25px; border-radius: 18px; margin-top: 35px;">
                <h4 style="color: #ffd700; margin-top: 0; font-size: 18px;">⚙️ لوحة تحكم صاحب اللعبة (Admin Control)</h4>
                <div style="display: flex; justify-content: center; gap: 15px; align-items: center; flex-wrap: wrap;">
                    <input type="number" id="forcedWinningNum" placeholder="الرقم الفائز (اختياري 1-5)" min="1" max="5" value="{{ forced_val if forced_val != 0 else '' }}" style="padding: 12px; width: 220px; background: #000; color: #fff; border: 1px solid #ffd700; border-radius: 10px; text-align: center; font-size: 16px;">
                    <button type="button" onclick="executeEmpireAdminDraw()" style="background: linear-gradient(135deg, #22c55e, #15803d); color: #fff; padding: 14px 30px; font-weight: 900; border: none; border-radius: 12px; cursor: pointer; font-size: 18px;">ابدأ السحب ⚡</button>
                </div>
            </div>
        {% endif %}
    </div>

    <script>
        function handleEmpireAction(actionType, boxVal) {
            let formData = new FormData();
            formData.append('action_type', actionType);
            formData.append('box_number', boxVal);

            fetch('/game_numbers_empire', {
                method: 'POST',
                body: formData
            }).then(res => res.json()).then(data => {
                if(data.msg) alert(data.msg);
                location.reload();
            });
        }

        function executeEmpireAdminDraw() {
            let forcedVal = document.getElementById('forcedWinningNum').value;
            let formSet = new FormData();
            formSet.append('forced_winning_number', forcedVal);

            fetch('/game_numbers_empire_admin_set', {
                method: 'POST',
                body: formSet
            }).then(res => res.json()).then(data => {
                let formData = new FormData();
                formData.append('action_type', 'admin_draw');

                fetch('/game_numbers_empire', {
                    method: 'POST',
                    body: formData
                }).then(res => res.json()).then(drawData => {
                    if(drawData.msg) {
                        document.getElementById('empireAnnouncement').innerText = drawData.msg;
                        alert(drawData.msg);
                        location.reload();
                    }
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
        body { font-family:'Segoe UI', Tahoma, sans-serif; background: radial-gradient(circle at center, #151928 0%, #070a12 100%); color:#fff; text-align:center; padding:35px; }
        .wheel-12d { background:linear-gradient(145deg, rgba(31,26,15,0.95), rgba(13,13,13,0.95)); border:5px solid #ffd700; padding:50px; border-radius:35px; max-width:600px; margin:30px auto; box-shadow:0 35px 80px rgba(0,0,0,0.9); }
    </style>
</head>
<body>
    <div style="max-width:600px; margin:0 auto 20px auto; text-align:left;"><a href="/dashboard" style="background:#3b82f6; color:#fff; padding:8px 15px; text-decoration:none; border-radius:8px; font-weight:bold;">{{ t.back_dash }}</a></div>
    <div class="wheel-12d">
        <h2 style="color:#ffd700;">🎡 {{ t.game4 }} (12D Ultra - 35% Edge)</h2>
        <p>رصيدك الحالي: {{ balance }} USDD</p>
        {% if msg %}<div style="background:rgba(6,95,70,0.9); color:#34d399; padding:15px; border-radius:12px; margin:20px 0; font-weight:900;">{{ msg }}</div>{% endif %}
        <form method="POST">
            <input type="hidden" name="selected_numbers" value="[3, 8, 14]">
            <button type="submit" style="padding:18px 45px; background:linear-gradient(135deg,#22c55e,#15803d); color:#fff; font-weight:900; font-size:20px; border:none; border-radius:16px; cursor:pointer;">🎯 {{ t.spin }} (3 USDD)</button>
        </form>
    </div>
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
        body { font-family:'Segoe UI', Tahoma, sans-serif; background: radial-gradient(circle at center, #151928 0%, #070a12 100%); color:#fff; text-align:center; padding:35px; }
        .reveal-12d { background:linear-gradient(145deg, rgba(31,31,31,0.95), rgba(17,17,17,0.95)); border:5px solid #ffd700; padding:50px; border-radius:35px; max-width:600px; margin:30px auto; box-shadow:0 35px 80px rgba(0,0,0,0.9); }
    </style>
</head>
<body>
    <div style="max-width:600px; margin:0 auto 20px auto; text-align:left;"><a href="/dashboard" style="background:#3b82f6; color:#fff; padding:8px 15px; text-decoration:none; border-radius:8px; font-weight:bold;">{{ t.back_dash }}</a></div>
    <div class="reveal-12d">
        <h2 style="color:#ffd700;">🎟️ {{ t.game5 }} (12D Ultra - 35% Edge)</h2>
        <p>رصيدك الحالي: {{ balance }} USDD</p>
        {% if msg %}<div style="background:rgba(6,95,70,0.9); color:#34d399; padding:15px; border-radius:12px; margin:20px 0; font-weight:900;">{{ msg }}</div>{% endif %}
        {% if result_data %}
            <div style="font-size:35px; margin:20px 0; letter-spacing:15px; background:rgba(0,0,0,0.6); padding:15px; border-radius:14px; border:1px solid #ffd700;">
                {{ result_data.revealed.values() | list | join(' ') }}
            </div>
        {% endif %}
        <form method="POST">
            <button type="submit" style="padding:18px 45px; background:linear-gradient(135deg,#ffd700,#ff8c00); color:#000; font-weight:900; font-size:20px; border:none; border-radius:16px; cursor:pointer;">🎟️ {{ t.reveal }} (1 USDD)</button>
        </form>
    </div>
</body>
</html>
"""

GAME_GOLDEN_BOXES_NEW_PAGE = LANG_BAR + """
<!DOCTYPE html>
<html lang="{{ t.dir }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ t.game6 }} - 12D</title>
    <style>
        body { font-family:'Segoe UI', Tahoma, sans-serif; background: radial-gradient(circle at center, #151928 0%, #070a12 100%); color:#fff; text-align:center; padding:35px; }
        .boxes-12d { background:linear-gradient(135deg, rgba(17,13,6,0.95), rgba(0,0,0,0.95)); border:5px solid #b8860b; padding:50px; border-radius:35px; max-width:700px; margin:30px auto; box-shadow:0 35px 80px rgba(0,0,0,0.9); }
        .box-12d { width:95px; height:95px; background:linear-gradient(145deg, #7c3aed, #4c1d95); border:3px solid #ffd700; border-radius:20px; color:#fff; font-size:26px; font-weight:900; cursor:pointer; }
    </style>
</head>
<body>
    <div style="max-width:700px; margin:0 auto 20px auto; text-align:left;"><a href="/dashboard" style="background:#3b82f6; color:#fff; padding:8px 15px; text-decoration:none; border-radius:8px; font-weight:bold;">{{ t.back_dash }}</a></div>
    <div class="boxes-12d">
        <h2 style="color:#ffd700;">🎁 {{ t.game6 }} (12D Ultra - 35% Edge)</h2>
        <p>رصيدك الحالي: {{ balance }} USDD</p>
        {% if msg %}<div style="background:rgba(6,95,70,0.9); color:#34d399; padding:15px; border-radius:12px; margin:20px 0; font-weight:900;">{{ msg }}</div>{% endif %}
        <div style="display:flex; justify-content:center; gap:20px; margin:35px 0; flex-wrap:wrap;">
            {% for b in range(1, 6) %}
                <form method="POST" style="margin:0;">
                    <input type="hidden" name="box_number" value="{{ b }}">
                    <button type="submit" name="book_box" class="box-12d">📦 {{ b }}</button>
                </form>
            {% endfor %}
        </div>
        {% if username == 'admin1' %}
            <form method="POST"><button type="submit" name="admin_execute_luxury_draw" style="background:linear-gradient(135deg,#22c55e,#15803d); color:#fff; padding:16px 35px; border:none; border-radius:14px; font-weight:900; cursor:pointer;">⚡ {{ t.draw_now }}</button></form>
        {% endif %}
    </div>
</body>
</html>
"""

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
