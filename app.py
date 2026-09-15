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
        'recharge': 'Recargar Saldo', 'withdraw': 'Retirar Saldo', 'change_pass': 'Cambiar Contraseña', 'logout': 'Cerrar Sesión',
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
                return jsonify({"success": False, "msg": "رصيد غير كافي أو المربع محجوز مسبقاً!"})
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

            winner_name = "لا يوجد رابح"
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
    return render_template_string(GAME_NUMBERS_EMPIRE_PAGE, t=t, username=username, balance=user.balance, bookings=bookings, winning_number=e_state.winning_number, draw_status=e_state.status, forced_val=e_state.forced_winning_number, msg=msg)

@app.route('/game_numbers_empire_admin_set', methods=['POST'])
def game_numbers_empire_admin_set():
    if 'username' not in session or session.get('username') != 'admin1': return jsonify({"success": False})
    forced_val = request.form.get('forced_winning_number', '').strip()
    e_state = NumbersEmpireState.query.get(1)
    if e_state:
        e_state.forced_winning_number = int(forced_val) if forced_val else 0
        db.session.commit()
    return jsonify({"success": True})

# --- لعبة عجلة الأرقام (Game 4) ---
@app.route('/game_number_wheel', methods=['GET', 'POST'])
def game_number_wheel():
    if 'username' not in session: return redirect(url_for('login'))
    username = session['username']
    user = User.query.filter_by(username=username).first()
    vault = SystemVault.query.get(1)
    t = get_t()
    
    if request.method == 'POST':
        try:
            data = request.get_json(silent=True) or request.form
            nums = data.get('selected_numbers', [])
            if isinstance(nums, str):
                nums = json.loads(nums)
            nums = [int(n) for n in nums]
            
            bet_amt = float(len(nums) * 2.0)
            if nums and user.balance >= bet_amt:
                user.balance -= bet_amt
                vault.vault_balance += bet_amt
                db.session.add(FinancialLog(action_type='مبيع رهان عجلة الأرقام 9D', admin_name='system', target_user=username, amount=bet_amt, log_time=get_local_time()))
                
                if random.random() < 0.85:
                    winning_num = random.choice(nums) if random.random() < 0.4 and nums else random.randint(1, 20)
                else:
                    winning_num = 21

                if winning_num in nums:
                    user.balance += 20.0
                    vault.vault_balance -= 20.0
                    db.session.add(FinancialLog(action_type='جائزة عجلة الأرقام 20 USDD', admin_name='system', target_user=username, amount=20.0, log_time=get_local_time()))
                    msg = f"مبروك للرقم #{winning_num} ربحت 20 USDD"
                else:
                    msg = f"توقفت العجلة عند الرقم #{winning_num}"
                
                db.session.commit()
                return jsonify({"success": True, "winning_num": winning_num, "balance": user.balance, "msg": msg})
        except Exception as e:
            return jsonify({"success": False, "msg": str(e)})

    return render_template_string(GAME_NUMBER_WHEEL_PAGE, t=t, balance=user.balance, username=username)

# --- لعبة اكشف واربح (Game 5) ---
@app.route('/game_reveal_and_win', methods=['GET', 'POST'])
def game_reveal_and_win():
    if 'username' not in session: return redirect(url_for('login'))
    username = session['username']
    user = User.query.filter_by(username=username).first()
    vault = SystemVault.query.get(1)
    t = get_t()
    
    if request.method == 'POST':
        if user.balance >= 1.0:
            user.balance -= 1.0
            vault.vault_balance += 1.0
            db.session.add(FinancialLog(action_type='مبيع رهان اكشف واربح', admin_name='system', target_user=username, amount=1.0, log_time=get_local_time()))
            
            r_state = RevealAndWinGlobalState.query.get(1)
            if not r_state:
                r_state = RevealAndWinGlobalState(id=1, total_spins=0)
                db.session.add(r_state)
            r_state.total_spins += 1
            
            cycle_pos = r_state.total_spins % 46
            prize = 0.0
            
            if cycle_pos > 0 and cycle_pos <= 20:
                rev = ['🦁', '🦁', '🦁' if random.random() > 0.5 else '7']
                prize = 0.50
                user.balance += prize
                vault.vault_balance -= prize
                db.session.add(FinancialLog(action_type='جائزة اكشف واربح (تطابق نصف دولار)', admin_name='system', target_user=username, amount=prize, log_time=get_local_time()))
                msg = "مبروك! تطابق شكلين وفزت بـ 0.50 USDD"
            else:
                rev = ['🦁', '3', '5']
                msg = "خسارة بدون تطابق (طابق وجه الأسد واحصل على 1000 USDD)"

            db.session.commit()
            return jsonify({"success": True, "balance": user.balance, "revealed": rev, "msg": msg})
        else:
            return jsonify({"success": False, "msg": "رصيد غير كافي (يحتاج 1 USDD)!"})

    return render_template_string(GAME_REVEAL_AND_WIN_PAGE, t=t, balance=user.balance, username=username)

# --- مسار الخصم الفوري عند النقر في الروليت ---
@app.route('/api/roulette_action', methods=['POST'])
def api_roulette_action():
    if 'username' not in session: return jsonify({"success": False})
    data = request.get_json() or request.form
    action = data.get('action')
    user = User.query.filter_by(username=session['username']).first()
    vault = SystemVault.query.get(1)
    
    if action == 'add':
        if user.balance >= 1.0:
            user.balance -= 1.0
            vault.vault_balance += 1.0
            db.session.commit()
            return jsonify({"success": True, "balance": user.balance})
        else:
            return jsonify({"success": False, "msg": "رصيدك لا يكفي!"})
    elif action == 'remove':
        user.balance += 1.0
        vault.vault_balance -= 1.0
        db.session.commit()
        return jsonify({"success": True, "balance": user.balance})
    elif action == 'clear':
        count = int(data.get('count', 0))
        if count > 0:
            user.balance += count * 1.0
            vault.vault_balance -= count * 1.0
            db.session.commit()
        return jsonify({"success": True, "balance": user.balance})
    return jsonify({"success": False})

# --- لعبة روليت الحظ (Game 2) ---
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
                    msg = f"🌟 مبروك! النقرة رقم #{g_state.total_global_spins} فازت بـ 100 USDD!"
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

# --- لعبة الـ 20 رقم الجديدة (Game 6) ---
@app.route('/game_20_numbers', methods=['GET', 'POST'])
def game_20_numbers():
    if 'username' not in session: return redirect(url_for('login'))
    username = session['username']
    user = User.query.filter_by(username=username).first()
    vault = SystemVault.query.get(1)
    t = get_t()
    
    if request.method == 'POST':
        try:
            data = request.get_json(silent=True) or request.form
            nums = data.get('selected_numbers', [])
            if isinstance(nums, str):
                nums = json.loads(nums)
            nums = [int(n) for n in nums]
            
            cost = float(len(nums) * 5.0)
            if nums and user.balance >= cost:
                user.balance -= cost
                vault.vault_balance += cost
                db.session.add(FinancialLog(action_type='مبيع رهان لعبة 70 USDD', admin_name='system', target_user=username, amount=cost, log_time=get_local_time()))
                
                all_20 = list(range(1, 21))
                unselected = [n for n in all_20 if n not in nums]
                if unselected and random.random() < 0.65:
                    winning_num = random.choice(unselected)
                else:
                    winning_num = random.choice(all_20)

                payout = 0
                if winning_num in nums:
                    payout = 70.0
                    user.balance += payout
                    vault.vault_balance -= payout
                    db.session.add(FinancialLog(action_type='جائزة لعبة 70 USDD', admin_name='system', target_user=username, amount=payout, log_time=get_local_time()))
                    msg = f"مبروك 70 USDD (الرقم الفائز #{winning_num})"
                else:
                    msg = f"الرقم الفائز #{winning_num} (حظ أوفر)"

                db.session.commit()
                return jsonify({"success": True, "winning_number": winning_num, "balance": user.balance, "msg": msg})
        except Exception as e:
            return jsonify({"success": False, "msg": str(e)})

    return render_template_string(GAME_20_NUMBERS_PAGE, t=t, balance=user.balance, username=username)

@app.route('/admin_customers', methods=['GET', 'POST'])
def admin_customers():
    if 'username' not in session or session.get('username') != 'admin1': return redirect(url_for('dashboard'))
    t = get_t()
    return render_template_string(ADMIN_CUSTOMERS_PAGE, t=t, users_list=User.query.all())

@app.route('/admin_customer_detail/<username>')
def admin_customer_detail(username):
    if 'username' not in session or session.get('username') != 'admin1': return redirect(url_for('dashboard'))
    t = get_t()
    user = User.query.filter_by(username=username).first()
    return render_template_string(ADMIN_CUSTOMER_DETAIL_PAGE, t=t, user=user)

@app.route('/admin_games', methods=['GET', 'POST'])
def admin_games():
    if 'username' not in session or session.get('username') != 'admin1': return redirect(url_for('dashboard'))
    t = get_t()
    g_state = RouletteGlobalState.query.get(1)
    total_spins = g_state.total_global_spins if g_state else 0
    rem_40 = 40 - (total_spins % 40)
    rem_360 = 360 - (total_spins % 360)
    return render_template_string(ADMIN_GAMES_PAGE, t=t, total_spins=total_spins, rem_40=rem_40, rem_360=rem_360)

@app.route('/admin_accounting', methods=['GET', 'POST'])
def admin_accounting():
    if 'username' not in session or session.get('username') != 'admin1': return redirect(url_for('dashboard'))
    vault = SystemVault.query.get(1)
    t = get_t()
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
    return render_template_string(ADMIN_ACCOUNTING_PAGE, t=t, vault_balance=vault.vault_balance, logs=logs, users_list=User.query.all(), msg=msg)

# --- قوالب إضافية للروليت ---
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

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
