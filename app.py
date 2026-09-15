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

class RouletteGlobalState(db.Model):
    __tablename__ = 'roulette_global_state'
    id = db.Column(db.Integer, primary_key=True)
    total_global_spins = db.Column(db.Integer, default=0)

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
    if not RouletteGlobalState.query.get(1):
        db.session.add(RouletteGlobalState(id=1, total_global_spins=0))
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
                    winner_u.balance += 75.0
                    vault.vault_balance -= 75.0
                    db.session.add(FinancialLog(action_type='جائزة الرقم الحنون', admin_name='admin1', target_user=winner_u.username, amount=75.0, log_time=get_local_time()))
            
            draw_state.winning_number = winning_num
            draw_state.status = 'finished'
            draw_state.draw_end_time = time.time() + 20.0
            draw_state.forced_winning_number = 0
            db.session.commit()
            return jsonify({"success": True, "msg": f"Winner: #{winning_num} | الرابح: {winner_name}"})

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

# --- لعبة روليت الحظ الحديثة والمطورة بالكامل (طاولة عمودية، حتى 21 رقم، زر تكرار الرهان، عداد 20 ثانية، جائزة 5x، ونقرات 40 و 360 الخاصة) ---
@app.route('/game_roulette', methods=['GET', 'POST'])
def game_roulette():
    if 'username' not in session: return redirect(url_for('login'))
    username = session['username']
    user = User.query.filter_by(username=username).first()
    vault = SystemVault.query.get(1)
    t = get_t()
    
    if request.method == 'POST':
        try:
            data = request.get_json(silent=True) or request.form
            selected_numbers = data.get('selected_numbers', [])
            if isinstance(selected_numbers, str):
                selected_numbers = json.loads(selected_numbers)
            selected_numbers = [int(n) for n in selected_numbers]
            bet_per_number = float(data.get('bet_amount', 1.0))
            total_bet = bet_per_number * len(selected_numbers)
            
            if total_bet > 0 and user.balance >= total_bet:
                user.balance -= total_bet
                vault.vault_balance += total_bet
                db.session.add(FinancialLog(action_type='مبيع رهان روليت 12D', admin_name='system', target_user=username, amount=total_bet, log_time=get_local_time()))
                
                # تتبع النقرات العالمية للروليت
                g_state = RouletteGlobalState.query.get(1)
                if not g_state:
                    g_state = RouletteGlobalState(id=1, total_global_spins=0)
                    db.session.add(g_state)
                g_state.total_global_spins += 1
                
                # التحقق من حدث كل 360 نقرة (جائزة 100$)
                is_360th_win = (g_state.total_global_spins % 360 == 0)
                # التحقق من حدث كل 40 نقرة (جائزة 20$)
                is_40th_win = (g_state.total_global_spins % 40 == 0)
                
                reds = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
                
                if is_360th_win and selected_numbers:
                    # جائزة الـ 100$ الكبرى للحدث العالمي 360
                    winning_num = random.choice(selected_numbers)
                    payout = 100.0
                    user.balance += payout
                    vault.vault_balance -= payout
                    db.session.add(FinancialLog(action_type='جائزة روليت الكبرى (النقرة 360 - 100$)', admin_name='system', target_user=username, amount=payout, log_time=get_local_time()))
                    msg = f"🌟 مبروك! النقرة رقم #{g_state.total_global_spins} في المنصة فازت بجائزة الـ 100$ الكبرى!"
                elif is_40th_win and selected_numbers:
                    # جائزة الـ 20$ للحدث العالمي 40
                    winning_num = random.choice(selected_numbers)
                    payout = 20.0
                    user.balance += payout
                    vault.vault_balance -= payout
                    db.session.add(FinancialLog(action_type='جائزة روليت السحب المميز (النقرة 40 - 20$)', admin_name='system', target_user=username, amount=payout, log_time=get_local_time()))
                    msg = f"🏆 تهانينا! أصابت النقرة رقم #{g_state.total_global_spins} وفزت بجائزة الـ 20$!"
                else:
                    # في العادة الخوارزمية تختار رقماً لم يختاره اللاعب (من الأرقام الأخرى) لضمان نسبة الشركة، وإن تصادف وجوده نطبق مضاعف 5x
                    all_nums = list(range(0, 37))
                    unselected_nums = [n for n in all_nums if n not in selected_numbers]
                    
                    if unselected_nums and random.random() < 0.75:
                        winning_num = random.choice(unselected_nums)
                    else:
                        winning_num = random.choice(all_nums)
                    
                    payout = 0
                    if winning_num in selected_numbers:
                        payout = bet_per_number * 5  # الجائزة بمضاعف 5x
                        user.balance += payout
                        vault.vault_balance -= payout
                        db.session.add(FinancialLog(action_type='جائزة روليت 5x', admin_name='system', target_user=username, amount=payout, log_time=get_local_time()))
                        msg = f"🎉 مبروك! استقر الروليت على رقمك المختار #{winning_num} وفزت بـ {payout} USDD (مضاعف 5x)!"
                    else:
                        msg = f"❌ حظ أوفر! الرقم الرابح هو #{winning_num}"
                
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
    
    # حساب النقرات المتبقية للأرشيف (للـ 40 وللـ 360)
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
            {{ t.cost }}: 2 USDD | {{ t.prize }}: 75 USDD (يتم السحب من 1 إلى 50 حتى لو لم تكن هناك رهانات)
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

# --- قالب لعبة روليت الحظ الحديثة والمطورة بالكامل (طاولة عمودية، حتى 21 رقم، زر تكرار الرهان، عداد 20 ثانية، جائزة 5x، ونقرات 40 و 360 الخاصة) ---
GAME_ROULETTE_GLOBAL_PAGE = LANG_BAR + """
<!DOCTYPE html>
<html lang="{{ t.dir }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ t.game2 }} - 12D</title>
    <style>
        body { font-family:'Segoe UI', Tahoma, sans-serif; background:radial-gradient(circle at center, #151928 0%, #070a12 100%); color:#fff; margin:0; padding:15px; text-align: center; }
        
        /* بانر اضرب اللمعة في أعلى اللعبة */
        .glow-banner { background: linear-gradient(135deg, #f59e0b, #fbbf24, #d97706); color: #000; padding: 14px; border-radius: 14px; font-weight: 900; font-size: 18px; max-width: 850px; margin: 0 auto 15px auto; box-shadow: 0 0 25px rgba(245,158,11,0.6); animation: pulseGlow 1.5s infinite alternate; border: 2px solid #fff; }
        @keyframes pulseGlow { 0% { transform: scale(1); box-shadow: 0 0 15px rgba(245,158,11,0.5); } 100% { transform: scale(1.02); box-shadow: 0 0 30px rgba(245,158,11,0.9); } }

        .roulette-container { background: linear-gradient(135deg, #0e4c26 0%, #062e17 100%); border: 5px solid #b8860b; padding: 25px; border-radius: 25px; max-width: 850px; margin: 15px auto; box-shadow: 0 25px 60px rgba(0,0,0,0.9); }
        .slot-box { font-size: 45px; font-weight: 900; color: #ffd700; background: #000; padding: 10px; border-radius: 12px; border: 3px solid #b8860b; display: inline-block; min-width: 120px; box-shadow: inset 0 0 15px rgba(255,215,0,0.6); letter-spacing: 4px; }
        
        /* طاولة روليت عمودية كازينوية */
        .table-scroll-wrapper { width: 100%; overflow-x: auto; margin: 15px 0; padding-bottom: 10px; }
        .roulette-vertical-table { display: flex; flex-direction: column; gap: 6px; max-width: 320px; margin: 0 auto; background: #09381b; padding: 15px; border-radius: 16px; border: 3px solid #ffd700; }
        .table-row { display: flex; gap: 6px; justify-content: center; }
        .num-btn { width: 65px; height: 60px; background: #111827; border: 2px solid #ffd700; border-radius: 10px; font-size: 20px; font-weight: 900; color: #fff; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: 0.2s; }
        .num-btn:hover { transform: scale(1.05); border-color: #fff; }
        .num-btn.selected { background: #d97706 !important; border-color: #fff !important; color: #000 !important; box-shadow: 0 0 15px #ffd700; }
        .btn-red { background: #dc2626 !important; }
        .btn-black { background: #1f2937 !important; }
        .btn-green { background: #059669 !important; width: 100%; height: 50px; }

        .action-control-bar { display: flex; justify-content: center; gap: 12px; margin-top: 20px; flex-wrap: wrap; }
        .action-btn { padding: 14px 25px; font-weight: 900; font-size: 16px; border-radius: 12px; border: none; cursor: pointer; box-shadow: 0 5px 15px rgba(0,0,0,0.5); }
        .btn-spin { background: linear-gradient(135deg, #ffd700, #ff8c00); color: #000; font-size: 20px; padding: 16px 40px; }
        .btn-repeat { background: #3b82f6; color: #fff; }
        .btn-clear { background: #ef4444; color: #fff; }
    </style>
</head>
<body>
    <div style="display:flex; justify-content:space-between; align-items:center; max-width:850px; margin:0 auto; background:rgba(20,24,38,0.9); padding:12px 20px; border-radius:15px; border:1px solid rgba(255,215,0,0.3); flex-wrap:wrap; gap:10px;">
        <h2 style="color:#ffd700; margin:0; font-size: 22px;">🎰 {{ t.game2 }} (Vertical 12D Casino)</h2>
        <div style="display:flex; gap:8px; align-items:center;">
            <button type="button" onclick="location.reload()" style="background:#0284c7; color:#fff; border:none; padding:8px 14px; border-radius:8px; font-weight:bold; cursor:pointer; font-size:14px;">🔄 تحديث</button>
            <a href="/dashboard" style="background:linear-gradient(135deg,#3b82f6,#1d4ed8); color:#fff; padding:8px 16px; text-decoration:none; border-radius:8px; font-weight:900; font-size:14px;">{{ t.back_dash }}</a>
        </div>
        <div style="font-size: 17px; width: 100%; text-align: left;"><b>{{ t.balance }}: <span id="liveRouletteBalance">{{ balance }}</span> USDD</b></div>
    </div>

    <div class="roulette-container">
        <!-- لافتة اضرب اللمعة المطلوبة -->
        <div class="glow-banner">✨ اضرب اللمعة واحصل على 100 USDD فورا!</div>

        <!-- عداد تنازلي للجولة (20 ثانية) -->
        <div id="rouletteTimer" style="font-size: 22px; font-weight: 900; color: #38bdf8; margin-bottom: 15px;">⏳ وقت اختيار الأرقام: 20 ثانية</div>

        <div id="rouletteSlot" class="slot-screen slot-box">--</div>
        
        <div id="rouletteMsg" style="font-size: 17px; font-weight: 900; color: #34d399; margin: 12px 0; min-height: 28px;">اختر حتى 21 رقماً من الطاولة أدناه وشارك في السحب (الجائزة بمضاعف 5x)!</div>

        <!-- طاولة الروليت الطولية (Vertical Table) مع الصفر بالأعلى والأرقام 1 إلى 36 بصفوف من 3 أرقام -->
        <div class="table-scroll-wrapper">
            <div class="roulette-vertical-table">
                <!-- زر الصفر الأخضر بالأعلى -->
                <button type="button" id="num_0" onclick="toggleNumber(0)" class="num-btn btn-green">0</button>
                
                <!-- صفوف الأرقام 1 إلى 36 (ثلاثة أعمدة) -->
                <div class="table-row">
                    <button type="button" id="num_1" onclick="toggleNumber(1)" class="num-btn btn-red">1</button>
                    <button type="button" id="num_2" onclick="toggleNumber(2)" class="num-btn btn-black">2</button>
                    <button type="button" id="num_3" onclick="toggleNumber(3)" class="num-btn btn-red">3</button>
                </div>
                <div class="table-row">
                    <button type="button" id="num_4" onclick="toggleNumber(4)" class="num-btn btn-black">4</button>
                    <button type="button" id="num_5" onclick="toggleNumber(5)" class="num-btn btn-red">5</button>
                    <button type="button" id="num_6" onclick="toggleNumber(6)" class="num-btn btn-black">6</button>
                </div>
                <div class="table-row">
                    <button type="button" id="num_7" onclick="toggleNumber(7)" class="num-btn btn-red">7</button>
                    <button type="button" id="num_8" onclick="toggleNumber(8)" class="num-btn btn-black">8</button>
                    <button type="button" id="num_9" onclick="toggleNumber(9)" class="num-btn btn-red">9</button>
                </div>
                <div class="table-row">
                    <button type="button" id="num_10" onclick="toggleNumber(10)" class="num-btn btn-black">10</button>
                    <button type="button" id="num_11" onclick="toggleNumber(11)" class="num-btn btn-black">11</button>
                    <button type="button" id="num_12" onclick="toggleNumber(12)" class="num-btn btn-red">12</button>
                </div>
                <div class="table-row">
                    <button type="button" id="num_13" onclick="toggleNumber(13)" class="num-btn btn-black">13</button>
                    <button type="button" id="num_14" onclick="toggleNumber(14)" class="num-btn btn-red">14</button>
                    <button type="button" id="num_15" onclick="toggleNumber(15)" class="num-btn btn-black">15</button>
                </div>
                <div class="table-row">
                    <button type="button" id="num_16" onclick="toggleNumber(16)" class="num-btn btn-red">16</button>
                    <button type="button" id="num_17" onclick="toggleNumber(17)" class="num-btn btn-black">17</button>
                    <button type="button" id="num_18" onclick="toggleNumber(18)" class="num-btn btn-red">18</button>
                </div>
                <div class="table-row">
                    <button type="button" id="num_19" onclick="toggleNumber(19)" class="num-btn btn-red">19</button>
                    <button type="button" id="num_20" onclick="toggleNumber(20)" class="num-btn btn-black">20</button>
                    <button type="button" id="num_21" onclick="toggleNumber(21)" class="num-btn btn-red">21</button>
                </div>
                <div class="table-row">
                    <button type="button" id="num_22" onclick="toggleNumber(22)" class="num-btn btn-black">22</button>
                    <button type="button" id="num_23" onclick="toggleNumber(23)" class="num-btn btn-red">23</button>
                    <button type="button" id="num_24" onclick="toggleNumber(24)" class="num-btn btn-black">24</button>
                </div>
                <div class="table-row">
                    <button type="button" id="num_25" onclick="toggleNumber(25)" class="num-btn btn-red">25</button>
                    <button type="button" id="num_26" onclick="toggleNumber(26)" class="num-btn btn-black">26</button>
                    <button type="button" id="num_27" onclick="toggleNumber(27)" class="num-btn btn-red">27</button>
                </div>
                <div class="table-row">
                    <button type="button" id="num_28" onclick="toggleNumber(28)" class="num-btn btn-black">28</button>
                    <button type="button" id="num_29" onclick="toggleNumber(29)" class="num-btn btn-black">29</button>
                    <button type="button" id="num_30" onclick="toggleNumber(30)" class="num-btn btn-red">30</button>
                </div>
                <div class="table-row">
                    <button type="button" id="num_31" onclick="toggleNumber(31)" class="num-btn btn-black">31</button>
                    <button type="button" id="num_32" onclick="toggleNumber(32)" class="num-btn btn-red">32</button>
                    <button type="button" id="num_33" onclick="toggleNumber(33)" class="num-btn btn-black">33</button>
                </div>
                <div class="table-row">
                    <button type="button" id="num_34" onclick="toggleNumber(34)" class="num-btn btn-red">34</button>
                    <button type="button" id="num_35" onclick="toggleNumber(35)" class="num-btn btn-black">35</button>
                    <button type="button" id="num_36" onclick="toggleNumber(36)" class="num-btn btn-red">36</button>
                </div>
            </div>
        </div>

        <!-- أزرار التحكم والرهان -->
        <div class="action-control-bar">
            <button type="button" onclick="clearSelection()" class="action-btn btn-clear">🗑️ مسح</button>
            <button type="button" onclick="repeatLastBet()" class="action-btn btn-repeat">🔄 تكرار الرهان السابق</button>
            <button type="button" onclick="spinRoulette()" class="action-btn btn-spin">🎰 ابدأ السحب</button>
        </div>
    </div>

    <script>
        history.pushState(null, null, location.href);
        window.onpopstate = function () {
            location.href = '/dashboard';
        };

        let selectedNumbers = [];
        let maxAllowed = 21;
        let timeLeft = 20;

        function toggleNumber(num) {
            let idx = selectedNumbers.indexOf(num);
            if(idx > -1) {
                selectedNumbers.splice(idx, 1);
                document.getElementById('num_' + num).classList.remove('selected');
            } else {
                if(selectedNumbers.length >= maxAllowed) {
                    alert("يمكنك اختيار كحد أقصى 21 رقماً في الجولة الواحدة!");
                    return;
                }
                selectedNumbers.push(num);
                document.getElementById('num_' + num).classList.add('selected');
            }
        }

        function clearSelection() {
            selectedNumbers.forEach(n => {
                let btn = document.getElementById('num_' + n);
                if(btn) btn.classList.remove('selected');
            });
            selectedNumbers = [];
        }

        function repeatLastBet() {
            clearSelection();
            let last = localStorage.getItem('lastRouletteSelection');
            if(last) {
                selectedNumbers = JSON.parse(last);
                selectedNumbers.forEach(n => {
                    let btn = document.getElementById('num_' + n);
                    if(btn) btn.classList.add('selected');
                });
            } else {
                alert("لا يوجد رهان سابق محفوظ!");
            }
        }

        // العداد التنازلي 20 ثانية لبدء الجولة واختيار الأرقام
        let roundTimerInterval = setInterval(() => {
            timeLeft--;
            let timerEl = document.getElementById('rouletteTimer');
            if(timerEl) {
                timerEl.innerText = `⏳ وقت اختيار الأرقام: ${timeLeft} ثانية`;
            }
            if(timeLeft <= 0) {
                clearInterval(roundTimerInterval);
                if(selectedNumbers.length > 0) {
                    spinRoulette();
                } else {
                    // اختيار 5 أرقام عشوائية تلقائياً إذا لم يختار اللاعب شيئاً وانتهى الوقت
                    for(let i=0; i<5; i++) {
                        let r = Math.floor(Math.random() * 37);
                        if(!selectedNumbers.includes(r)) selectedNumbers.push(r);
                    }
                    spinRoulette();
                }
            }
        }, 1000);

        function spinRoulette() {
            if(selectedNumbers.length === 0) {
                alert("يرجى اختيار رقم واحد على الأقل للمشاركة في السحب!");
                return;
            }

            localStorage.setItem('lastRouletteSelection', JSON.stringify(selectedNumbers));

            let formData = {
                'selected_numbers': selectedNumbers,
                'bet_amount': 2.0
            };

            let slot = document.getElementById('rouletteSlot');
            let msgBox = document.getElementById('rouletteMsg');
            msgBox.style.color = "#ffd700";
            msgBox.innerText = "🎲 جاري تدوير العجلة وسحب الأرقام العشوائية...";

            let counter = 0;
            let spinInterval = setInterval(() => {
                slot.innerText = Math.floor(Math.random() * 37);
                counter++;
                if(counter > 15) {
                    clearInterval(spinInterval);
                    
                    fetch('/game_roulette', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(formData)
                    }).then(res => res.json()).then(data => {
                        slot.innerText = data.winning_number;
                        msgBox.innerText = data.msg;
                        msgBox.style.color = data.success ? "#34d399" : "#ef4444";
                        
                        let balanceBadge = document.getElementById('liveRouletteBalance');
                        if(balanceBadge) balanceBadge.innerText = data.balance;

                        // إضاءة الرقم الرابح على الطاولة
                        let winBtn = document.getElementById('num_' + data.winning_number);
                        if(winBtn) {
                            winBtn.style.boxShadow = "0 0 35px #ffd700";
                            winBtn.style.border = "4px solid #fff";
                            setTimeout(() => {
                                winBtn.style.boxShadow = "none";
                                winBtn.style.border = "2px solid #ffd700";
                            }, 5000);
                        }

                        // إعادة تعيين المؤقت للجولة القادمة
                        setTimeout(() => {
                            clearSelection();
                            timeLeft = 20;
                            roundTimerInterval = setInterval(() => {
                                timeLeft--;
                                let timerEl = document.getElementById('rouletteTimer');
                                if(timerEl) timerEl.innerText = `⏳ وقت اختيار الأرقام: ${timeLeft} ثانية`;
                                if(timeLeft <= 0) {
                                    clearInterval(roundTimerInterval);
                                    if(selectedNumbers.length > 0) spinRoulette();
                                }
                            }, 1000);
                        }, 4000);

                    }).catch(err => {
                        msgBox.innerText = "حدث خطأ في الاتصال بالسيرفر!";
                    });
                }
            }, 80);
        }
    </script>
</body>
</html>
"""

# --- صفحة تحكم الآدمن مع عدادات النقرات للأرشيف والتقارير ---
ADMIN_GAMES_PAGE = LANG_BAR + """
<!DOCTYPE html>
<html lang="{{ t.dir }}" dir="{{ t.dir }}">
<head><meta charset="UTF-8"><title>لوحة الألعاب - 12D</title></head>
<body style="font-family:'Segoe UI', Tahoma, sans-serif; background:radial-gradient(circle at center, #151928 0%, #070a12 100%); color:#fff; text-align:center; padding:35px;">
    <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(20,24,38,0.9); padding:18px 25px; border-radius:16px; border:2px solid #ffd700; max-width:600px; margin:0 auto 30px auto;">
        <h2 style="color:#ffd700; margin:0;">🎮 لوحة تحكم الألعاب والأرشيف</h2>
        <a href="/dashboard" style="background:#3b82f6; color:#fff; padding:10px 18px; text-decoration:none; border-radius:10px; font-weight:900;">{{ t.back_dash }}</a>
    </div>

    <!-- أرشيف مراقبة النقرات للروليت والجوائز -->
    <div style="background: rgba(15,23,42,0.95); border: 2px solid #38bdf8; padding: 25px; border-radius: 20px; max-width: 500px; margin: 0 auto 25px auto; box-shadow: 0 10px 30px rgba(56,189,248,0.3);">
        <h3 style="color: #38bdf8; margin-top: 0; font-size: 20px;">📊 أرشيف العدادات العالمية للروليت</h3>
        <p style="font-size: 16px; margin: 8px 0;">إجمالي النقرات العالمية بالمنصة: <b>{{ total_spins }}</b></p>
        <p style="font-size: 16px; margin: 8px 0; color: #ffd700;">النقرات الناقصة لجائزة الـ 20$ (كل 40): <b>{{ rem_40 }} نقرات</b></p>
        <p style="font-size: 16px; margin: 8px 0; color: #34d399;">النقرات الناقصة لجائزة الـ 100$ (كل 360): <b>{{ rem_360 }} نقرات</b></p>
    </div>

    {% if msg %}<p style="color:#34d399; font-weight:900; background:rgba(52,211,153,0.15); padding:12px; border-radius:10px; max-width:500px; margin:0 auto 20px auto;">{{ msg }}</p>{% endif %}
    <div style="background:rgba(25,30,48,0.9); border:3px solid #ffd700; padding:35px; border-radius:22px; max-width:500px; margin:20px auto;">
        <form method="POST">
            <label style="color:#ffd700; font-weight:900; font-size:18px;">رقم فائز مسبق (الرقم الحنون - اتركه فارغاً للاختيار العشوائي):</label><br>
            <input type="number" name="forced_winning_number" value="{{ forced_val if forced_val != 0 else '' }}" min="0" max="50" style="padding:14px; margin:15px 0; background:rgba(10,13,22,0.9); color:#fff; border:1px solid rgba(255,255,255,0.2); border-radius:10px; width:80%; text-align:center; font-size:20px;">
            <br>
            <button type="submit" style="padding:14px 25px; background:#22c55e; color:#fff; font-weight:900; border:none; border-radius:10px; cursor:pointer; width:80%;">حفظ الإعدادات</button>
        </form>
    </div>
</body>
</html>
"""

ADMIN_CUSTOMERS_PAGE = LANG_BAR + """
<!DOCTYPE html>
<html lang="{{ t.dir }}" dir="{{ t.dir }}">
<head><meta charset="UTF-8"><title>إدارة الزبائن - 12D</title></head>
<body style="font-family:'Segoe UI', Tahoma, sans-serif; background:radial-gradient(circle at center, #151928 0%, #070a12 100%); color:#fff; padding:30px;">
    <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(20,24,38,0.9); padding:18px 25px; border-radius:16px; border:2px solid #ffd700; max-width:900px; margin:0 auto 25px auto;">
        <h2 style="color:#ffd700; margin:0;">👑 إدارة الزبائن والحسابات</h2>
        <a href="/dashboard" style="background:#3b82f6; color:#fff; padding:10px 18px; text-decoration:none; border-radius:10px; font-weight:900;">{{ t.back_dash }}</a>
    </div>
    {% if msg %}<p style="color:#34d399; text-align:center; font-weight:bold;">{{ msg }}</p>{% endif %}
    <div style="background:rgba(25,30,48,0.9); padding:30px; border-radius:20px; max-width:480px; margin:20px auto; border:2px solid #ffd700;">
        <h3 style="color:#38bdf8; margin-top:0;">خلق حساب جديد</h3>
        <form method="POST">
            <input type="hidden" name="action" value="create_user">
            <input type="text" name="new_username" placeholder="Username" required style="width:100%; padding:14px; margin:10px 0; background:rgba(10,13,22,0.9); color:#fff; border:1px solid rgba(255,255,255,0.2); border-radius:10px; box-sizing:border-box;">
            <input type="password" name="new_password" placeholder="Password" required style="width:100%; padding:14px; margin:10px 0; background:rgba(10,13,22,0.9); color:#fff; border:1px solid rgba(255,255,255,0.2); border-radius:10px; box-sizing:border-box;">
            <input type="text" name="new_owner" placeholder="Owner Name" required style="width:100%; padding:14px; margin:10px 0; background:rgba(10,13,22,0.9); color:#fff; border:1px solid rgba(255,255,255,0.2); border-radius:10px; box-sizing:border-box;">
            <button type="submit" style="width:100%; padding:14px; background:#3b82f6; color:#fff; font-weight:900; border:none; border-radius:10px; cursor:pointer;">إنشاء</button>
        </form>
    </div>
    <div style="background:rgba(25,30,48,0.9); padding:30px; border-radius:20px; max-width:900px; margin:25px auto;">
        <h3 style="color:#ffd700; margin-top:0;">سجل الحسابات</h3>
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
<head><meta charset="UTF-8"><title>ذاكرة الزبون - 12D</title></head>
<body style="font-family:'Segoe UI', Tahoma, sans-serif; background:radial-gradient(circle at center, #151928 0%, #070a12 100%); color:#fff; padding:30px;">
    <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(20,24,38,0.9); padding:18px 25px; border-radius:16px; border:2px solid #ffd700; max-width:900px; margin:0 auto 25px auto;">
        <h2 style="color:#ffd700; margin:0;">📂 ذاكرة وتفاصيل: {{ user.username }} ({{ user.owner_name }})</h2>
        <a href="/admin_customers" style="background:#3b82f6; color:#fff; padding:10px 18px; text-decoration:none; border-radius:10px; font-weight:900;">الرجوع للزبائن</a>
    </div>
    <div style="background:rgba(25,30,48,0.9); padding:30px; border-radius:20px; margin:20px auto; max-width:900px;">
        <h3 style="color:#38bdf8; margin-top:0;">سجل العمليات (توقيت بيروت)</h3>
        <table style="width:100%; border-collapse:collapse;">
            <tr style="background:rgba(10,13,22,0.9); color:#ffd700;"><th style="padding:12px; border:1px solid #444;">Action</th><th style="padding:12px; border:1px solid #444;">Amount</th><th style="padding:12px; border:1px solid #444;">Time</th></tr>
            {% for l in logs %}<tr style="text-align:center;"><td style="padding:12px; border:1px solid #444;">{{ l.action_type }}</td><td style="padding:12px; border:1px solid #444; color:#34d399; font-weight:900;">{{ l.amount }} USDD</td><td style="padding:12px; border:1px solid #444;">{{ l.log_time }}</td></tr>{% endfor %}
        </table>
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
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: radial-gradient(circle at center, #151928 0%, #070a12 100%); color: #f8fafc; padding: 25px; }
        .admin-header { display: flex; justify-content: space-between; align-items: center; background: rgba(20,24,38,0.9); padding: 18px 25px; border-radius: 16px; border: 2px solid #ffd700; margin-bottom: 30px; }
        .vault-box { background: linear-gradient(135deg, rgba(6,95,70,0.95), rgba(4,120,87,0.95)); border: 3px solid #34d399; padding: 30px; border-radius: 22px; text-align: center; margin-bottom: 30px; }
        .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }
        @media(max-width: 900px) { .stats-grid { grid-template-columns: repeat(2, 1fr); } }
        .stat-card { background: rgba(25,30,48,0.9); padding: 22px; border-radius: 16px; text-align: center; }
        .stat-val { font-size: 28px; font-weight: 900; color: #34d399; margin-top: 10px; }
        .panel-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px; }
        @media(max-width: 900px) { .panel-grid { grid-template-columns: 1fr; } }
        .panel-box { background: rgba(25,30,48,0.9); padding: 22px; border-radius: 16px; }
        input, select { width: 100%; padding: 14px; margin: 10px 0; border-radius: 10px; background: rgba(10,13,22,0.9); color: white; border: 1px solid rgba(255,255,255,0.2); box-sizing: border-box; }
        button { padding: 14px; font-weight: 900; border: none; border-radius: 10px; cursor: pointer; width: 100%; margin-top: 10px; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; display: block; overflow-x: auto; }
        th, td { border: 1px solid #444; padding: 12px; text-align: center; font-size: 14px; }
        th { background: rgba(10,13,22,0.9); color: #ffd700; }
    </style>
</head>
<body>
    <div class="admin-header">
        <h2 style="color: #ffd700; margin: 0;">📊 برنامج المحاسبة والخزنة المركزية (12D)</h2>
        <a href="/dashboard" style="background:#3b82f6; color:#fff; padding:10px 18px; text-decoration:none; border-radius:10px; font-weight:900;">{{ t.back_dash }}</a>
    </div>
    
    {% if msg %}<div style="background: rgba(6,95,70,0.9); color: #34d399; padding: 14px; border-radius: 12px; margin-bottom: 25px; text-align: center; font-weight: 900;">{{ msg }}</div>{% endif %}

    <div class="vault-box">
        <h3 style="margin: 0; color: #a7f3d0; font-size: 20px;">🏦 خزنة الشركة الأساسية (رصيد المليون USDD)</h3>
        <div style="font-size: 50px; font-weight: 900; color: #fff; margin: 15px 0;">{{ vault_balance }} USDD</div>
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
                <button type="submit" style="background:#ffd700; color:#000;">توليد كود بطاقة جديد</button>
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
                <button type="submit" style="background:#22c55e; color:#000;">إتمام البيع من الخزنة</button>
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
                <button type="submit" style="background:#ef4444; color:#fff;">استرجاع الرصيد للخزنة</button>
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

GAME_NUMBERS_EMPIRE_PAGE = LANG_BAR + """
<!DOCTYPE html>
<html lang="{{ t.dir }}" dir="{{ t.dir }}">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ t.game3 }} - 12D</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: radial-gradient(circle at center, #151928 0%, #070a12 100%); color: #f8fafc; margin: 0; padding: 25px; }
        .header { display: flex; justify-content: space-between; align-items: center; background: rgba(20,24,38,0.9); padding: 18px 25px; border-radius: 16px; border: 2px solid #ffd700; }
        .board-container { background: linear-gradient(135deg, rgba(17,13,6,0.95), rgba(0,0,0,0.95)); border: 5px solid #b8860b; padding: 30px; border-radius: 25px; margin-top: 25px; text-align: center; }
        .board-grid { display: grid; grid-template-columns: repeat(10, 1fr); gap: 14px; margin-top: 25px; }
        @media(max-width: 768px) { .board-grid { grid-template-columns: repeat(5, 1fr); } }
        .number-box { background: linear-gradient(145deg, #059669, #047857); border: 3px solid #34d399; border-radius: 16px; height: 75px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 20px; font-weight: 900; color: #ffffff; cursor: pointer; }
        .number-box.booked { background: linear-gradient(145deg, #7f1d1d, #450a0a) !important; border-color: #ef4444 !important; color: #fca5a5 !important; }
        .number-box.my-booked { background: linear-gradient(145deg, #1e3a8a, #172554) !important; border-color: #3b82f6 !important; color: #93c5fd !important; }
    </style>
</head>
<body>
    <div class="header">
        <h2 style="color: #ffd700; margin: 0;">🏛️ {{ t.game3 }} (12D Ultra)</h2>
        <div><a href="/dashboard" style="background:#3b82f6; color:#fff; padding:8px 15px; text-decoration:none; border-radius:8px; font-weight:bold;">{{ t.back_dash }}</a></div>
    </div>
    {% if msg %}<div style="background: rgba(6,95,70,0.9); color: #34d399; padding: 15px; border-radius: 12px; margin-top: 20px; text-align: center; font-weight: 900;">{{ msg }}</div>{% endif %}
    <div class="board-container">
        <h3 style="color: #ffd700; margin-top: 0; font-size: 22px;">🎯 إمبراطورية الأرقام (تكلفة الحجز: 2 USDD)</h3>
        <div class="board-grid">
            {% for i in range(1, 51) %}
                {% if i in bookings %}
                    {% if bookings[i] == username %}
                        <form method="POST" style="margin: 0;"><input type="hidden" name="number" value="{{ i }}"><button type="submit" name="cancel_number" class="number-box my-booked" style="width: 100%;">{{ i }}<br><span style="font-size: 10px;">(أنت)</span></button></form>
                    {% else %}
                        <div class="number-box booked">{{ i }}<br><span style="font-size: 10px;">({{ bookings[i] }})</span></div>
                    {% endif %}
                {% else %}
                    <form method="POST" style="margin: 0;"><input type="hidden" name="number" value="{{ i }}"><button type="submit" name="book_number" class="number-box" style="width: 100%;">{{ i }}</button></form>
                {% endif %}
            {% endfor %}
        </div>
    </div>
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
