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
    status = db.Model_status = db.Column(db.String(20), default='idle') if hasattr(db, 'Column') else None
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

class RevealAndWinState(db.Model):
    __tablename__ = 'reveal_and_win_state'
    id = db.Column(db.Integer, primary_key=True)
    global_attempts = db.Column(db.Integer, default=0)
    pool_json = db.Column(db.Text, nullable=False)


# --- تهيئة الجداول وحذف الحسابات الوهمية والإبقاء على الأدمن فقط ---
with app.app_context():
    db.create_all()
    
    vault = SystemVault.query.get(1)
    if not vault:
        vault = SystemVault(id=1, vault_balance=1000000.0)
        db.session.add(vault)
    
    # حذف جميع حسابات اللاعبين القديمة والإبقاء على admin1 فقط
    User.query.filter(User.username != 'admin1').delete()
    
    admin = User.query.filter_by(username='admin1').first()
    if not admin:
        admin = User(username='admin1', password='admin123', balance=0.0, role='admin', created_by='system', owner_name='المشرف العام')
        db.session.add(admin)

    db.session.commit()

# --- قاموس الترجمات (اللغات الست) ---
TRANSLATIONS = {
    'ar': {
        'title': 'امبراطورية الأرقام',
        'subtitle': 'منصة الألعاب التفاعلية الكبرى',
        'login': 'دخول للبرنامج',
        'username': 'اسم المستخدم',
        'password': 'كلمة المرور',
        'balance': 'الرصيد',
        'recharge': 'شحن رصيد',
        'withdraw': 'سحب رصيد',
        'change_pass': 'تغيير الباسورد',
        'logout': 'خروج',
        'dashboard': 'لوحة التحكم',
        'withdraw_warning': '⚠️ تنبيه: يتم خصم 10% رسوم تحويل من رصيدك.',
        'wish_withdraw': 'سحب عبر Wish Money',
        'visa_withdraw': 'سحب عبر Visa مسبقة الدفع',
        'usdt_withdraw': 'قبض عبر USDT',
        'submit_request': 'إرسال الطلب',
        'success_msg': 'سنقوم بمراجعة طلبك في غضون دقيقة إلى 120 دقيقة وسيتم التحويل فوراً. أهلاً بكم، سررنا بانضمامكم إلينا!'
    },
    'en': {
        'title': 'Empire of Numbers',
        'subtitle': 'The Grand Interactive Gaming Platform',
        'login': 'Login',
        'username': 'Username',
        'password': 'Password',
        'balance': 'Balance',
        'recharge': 'Recharge Balance',
        'withdraw': 'Withdraw Balance',
        'change_pass': 'Change Password',
        'logout': 'Logout',
        'dashboard': 'Dashboard',
        'withdraw_warning': '⚠️ Notice: A 10% transfer fee will be deducted from your balance.',
        'wish_withdraw': 'Withdraw via Wish Money',
        'visa_withdraw': 'Withdraw via Prepaid Visa',
        'usdt_withdraw': 'Receive via USDT',
        'submit_request': 'Submit Request',
        'success_msg': 'We will review your request within 1 to 120 minutes and transfer immediately. Welcome, we are delighted to have you!'
    },
    'fr': {
        'title': 'Empire des Nombres',
        'subtitle': 'La Grande Plateforme de Jeux',
        'login': 'Connexion',
        'username': 'Nom d\'utilisateur',
        'password': 'Mot de passe',
        'balance': 'Solde',
        'recharge': 'Recharger',
        'withdraw': 'Retirer',
        'change_pass': 'Changer le mot de passe',
        'logout': 'Déconnexion',
        'dashboard': 'Tableau de bord',
        'withdraw_warning': '⚠️ Avis : Des frais de transfert de 10% seront déduits de votre solde.',
        'wish_withdraw': 'Retrait via Wish Money',
        'visa_withdraw': 'Retrait via Visa prépayée',
        'usdt_withdraw': 'Recevoir via USDT',
        'submit_request': 'Soumettre la demande',
        'success_msg': 'Nous examinerons votre demande en 1 à 120 minutes. Bienvenue parmi nous !'
    },
    'fa': {
        'title': 'امپراتوری اعداد',
        'subtitle': 'بزرگترین پلتفرم بازی‌های تعاملی',
        'login': 'ورود',
        'username': 'نام کاربری',
        'password': 'رمز عبور',
        'balance': 'موجودی',
        'recharge': 'شارژ حساب',
        'withdraw': 'برداشت وجه',
        'change_pass': 'تغییر رمز عبور',
        'logout': 'خروج',
        'dashboard': 'داشبورد',
        'withdraw_warning': '⚠️ توجه: ۱۰٪ کارمزد انتقال از موجودی شما کسر خواهد شد.',
        'wish_withdraw': 'برداشت از طریق Wish Money',
        'visa_withdraw': 'برداشت از طریق ویزا کارت',
        'usdt_withdraw': 'دریافت از طریق USDT',
        'submit_request': 'ارسال درخواست',
        'success_msg': 'درخواست شما ظرف ۱ الی ۱۲۰ دقیقه بررسی و واریز خواهد شد. خوش آمدید!'
    },
    'es': {
        'title': 'Imperio de los Números',
        'subtitle': 'La Gran Plataforma de Juegos',
        'login': 'Iniciar Sesión',
        'username': 'Usuario',
        'password': 'Contraseña',
        'balance': 'Saldo',
        'recharge': 'Recargar Saldo',
        'withdraw': 'Retirar Saldo',
        'change_pass': 'Cambiar Contraseña',
        'logout': 'Cerrar Sesión',
        'dashboard': 'Panel',
        'withdraw_warning': '⚠️ Aviso: Se descontará una comisión del 10% por transferencia.',
        'wish_withdraw': 'Retirar vía Wish Money',
        'visa_withdraw': 'Retirar vía Visa prepagada',
        'usdt_withdraw': 'Recibir vía USDT',
        'submit_request': 'Enviar Solicitud',
        'success_msg': 'Revisaremos su solicitud en 1 a 120 minutos. ¡Bienvenidos!'
    },
    'de': {
        'title': 'Imperium der Zahlen',
        'subtitle': 'Die Große Gaming-Plattform',
        'login': 'Anmelden',
        'username': 'Benutzername',
        'password': 'Passwort',
        'balance': 'Guthaben',
        'recharge': 'Guthaben aufladen',
        'withdraw': 'Guthaben abheben',
        'change_pass': 'Passwort ändern',
        'logout': 'Abmelden',
        'dashboard': 'Dashboard',
        'withdraw_warning': '⚠️ Hinweis: Es wird eine Überweisungsgebühr von 10% abgezogen.',
        'wish_withdraw': 'Auszahlung über Wish Money',
        'visa_withdraw': 'Auszahlung über Prepaid Visa',
        'usdt_withdraw': 'Empfang über USDT',
        'submit_request': 'Anfrage senden',
        'success_msg': 'Wir prüfen Ihre Anfrage in 1 bis 120 Minuten. Willkommen!'
    }
}

def get_t():
    lang = session.get('lang', 'ar')
    return TRANSLATIONS.get(lang, TRANSLATIONS['ar'])

# --- المسارات (Routes) ---

@app.route('/set_lang/<lang>')
def set_lang(lang):
    if lang in TRANSLATIONS:
        session['lang'] = lang
    return redirect(request.referrer or url_for('login'))

@app.route('/manifest.json')
def manifest():
    return jsonify({
        "name": "Empire of Numbers",
        "short_name": "Empire",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0b0f19",
        "theme_color": "#ffd700"
    })

@app.route('/sw.js')
def service_worker():
    return app.response_class("self.addEventListener('fetch', function(event) { });", mimetype='application/javascript')

@app.route('/api/sync_balance')
def api_sync_balance():
    if 'username' not in session:
        return jsonify({"balance": 0.0})
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
            error = "خطأ في اسم المستخدم أو كلمة المرور! / Invalid credentials!"
    return render_template_string(LOGIN_PAGE, t=t, error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    if not user:
        return redirect(url_for('logout'))
    
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
                    log = FinancialLog(action_type='شحن عبر بطاقة كود', admin_name='system', target_user=user.username, amount=card.amount, log_time=get_local_time())
                    db.session.add(log)
                    db.session.commit()
                    msg = f"🎉 مبروك! تم شحن حسابك بنجاح بقيمة {card.amount} USDD"
                else:
                    msg = "خزنة الشركة غير كافية حالياً!"
            else:
                msg = "❌ كود البطاقة غير صالح أو مستخدم!"
        
        elif action in ['withdraw_wish', 'withdraw_visa', 'withdraw_usdt']:
            msg = t['success_msg']

    return render_template_string(DASHBOARD_PAGE, t=t, username=user.username, role=user.role, balance=user.balance, msg=msg)

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'username' not in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    t = get_t()
    msg = None
    if request.method == 'POST':
        old_p = request.form.get('old_password', '')
        new_p = request.form.get('new_password', '').strip()
        confirm_p = request.form.get('confirm_password', '').strip()
        
        if user.role != 'admin' and user.password != old_p:
            msg = "كلمة المرور القديمة غير صحيحة!"
        elif not new_p:
            msg = "كلمة المرور الجديدة فارغة!"
        elif new_p != confirm_p:
            msg = "كلمة المرور الجديدة غير متطابقة!"
        else:
            user.password = new_p
            db.session.commit()
            msg = "تم تغيير كلمة المرور بنجاح!"
    return render_template_string(CHANGE_PASSWORD_PAGE, t=t, username=user.username, balance=user.balance, msg=msg)

@app.route('/api/golden_status')
def api_golden_status():
    current_time = time.time()
    draw_state = GameDrawState.query.get(1)
    status = 'idle'
    winning_number = 0
    remaining = 0
    if draw_state:
        status = draw_state.status
        winning_number = draw_state.winning_number
        end_time = draw_state.draw_end_time
        if status == 'finished' and current_time >= end_time:
            GoldenNumberBooking.query.delete()
            draw_state.winning_number = 0
            draw_state.status = 'idle'
            draw_state.draw_end_time = 0
            db.session.commit()
            status = 'idle'
            winning_number = 0
        remaining = max(0, int(end_time - current_time))
    bookings = {b.number: b.username for b in GoldenNumberBooking.query.all()}
    return jsonify({"status": status, "winning_number": winning_number, "remaining_seconds": remaining, "bookings": bookings})

@app.route('/api/luxury_golden_status')
def api_luxury_golden_status():
    current_time = time.time()
    l_state = LuxuryGoldenState.query.get(1)
    status = 'idle'
    winning_number = 0
    if l_state:
        status = l_state.status
        winning_number = l_state.winning_number
        if status == 'finished' and current_time >= l_state.draw_end_time:
            LuxuryGoldenBooking.query.delete()
            l_state.winning_number = 0
            l_state.status = 'idle'
            l_state.draw_end_time = 0
            db.session.commit()
            status = 'idle'
            winning_number = 0
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
        if 'book_number' in request.form and draw_state.status == 'idle':
            number = int(request.form.get('number'))
            cost = 2.0
            if user.balance >= cost:
                if not GoldenNumberBooking.query.filter_by(number=number).first():
                    user.balance -= cost
                    vault.vault_balance += cost
                    db.session.add(FinancialLog(action_type='مبيع رهان لعبة', admin_name='system', target_user=username, amount=cost, log_time=get_local_time()))
                    db.session.add(GoldenNumberBooking(username=username, number=number, booking_date=get_local_time()))
                    db.session.commit()
                    msg = f"تم حجز الرقم {number} مقابل 2 USDD!"
                else: msg = "الرقم محجوز مسبقاً!"
            else: msg = "رصيدك غير كافٍ!"
        elif 'cancel_number' in request.form and draw_state.status == 'idle':
            number = int(request.form.get('number'))
            b = GoldenNumberBooking.query.filter_by(number=number, username=username).first()
            if b:
                db.session.delete(b)
                user.balance += 2.0
                vault.vault_balance -= 2.0
                db.session.commit()
                msg = f"تم التراجع واسترداد 2 USDD!"
        elif 'admin_execute_draw' in request.form and username == 'admin1':
            bookings = GoldenNumberBooking.query.all()
            booked_nums = [b.number for b in bookings]
            if booked_nums:
                winning_num = draw_state.forced_winning_number if (draw_state.forced_winning_number in booked_nums) else random.choice(booked_nums)
                winner_b = GoldenNumberBooking.query.filter_by(number=winning_num).first()
                winner_u = User.query.filter_by(username=winner_b.username).first()
                winner_u.balance += 75.0
                vault.vault_balance -= 75.0
                db.session.add(FinancialLog(action_type='جائزة الرقم الحنون', admin_name='admin1', target_user=winner_u.username, amount=75.0, log_time=get_local_time()))
                draw_state.winning_number = winning_num
                draw_state.status = 'finished'
                draw_state.draw_end_time = time.time() + 15.0
                db.session.commit()
                msg = f"الفائز هو {winner_u.username} بالرقم {winning_num}"

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
            if user.balance >= 2.0:
                if not NumbersEmpireBooking.query.filter_by(number=num).first():
                    user.balance -= 2.0
                    vault.vault_balance += 2.0
                    db.session.add(FinancialLog(action_type='مبيع رهان إمبراطورية الأرقام', admin_name='system', target_user=username, amount=2.0, log_time=get_local_time()))
                    db.session.add(NumbersEmpireBooking(username=username, number=num, booking_date=get_local_time()))
                    db.session.commit()
                    msg = f"تم حجز الرقم #{num} بنجاح!"
                else: msg = "الرقم محجوز!"
            else: msg = "رصيدك غير كافٍ!"
        elif 'cancel_number' in request.form:
            num = int(request.form.get('number', 0))
            b = NumbersEmpireBooking.query.filter_by(number=num, username=username).first()
            if b:
                db.session.delete(b)
                user.balance += 2.0
                vault.vault_balance -= 2.0
                db.session.commit()
                msg = "تم التراجع والاسترداد!"
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
    msg = None
    last_win_data = None
    if request.method == 'POST':
        try:
            bets_json = request.form.get('bets_data')
            total_bet = float(request.form.get('total_bet_amount', 0))
            if total_bet > 0 and user.balance >= total_bet:
                user.balance -= total_bet
                vault.vault_balance += total_bet
                db.session.add(FinancialLog(action_type='مبيع رهان روليت', admin_name='system', target_user=username, amount=total_bet, log_time=get_local_time()))
                
                # خوارزمية الروليت المبسطة
                winning_num = random.randint(0, 36)
                reds = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
                color = 'green' if winning_num == 0 else ('red' if winning_num in reds else 'black')
                
                bets = json.loads(bets_json)
                payout = 0
                for bet in bets:
                    if bet['type'] == 'straight' and int(bet['value']) == winning_num:
                        payout += (bet['amount'] * 35) + bet['amount']
                    elif bet['type'] == 'color' and bet['value'] == color:
                        payout += (bet['amount'] * 1) + bet['amount']
                
                if payout > 0:
                    user.balance += payout
                    vault.vault_balance -= payout
                    db.session.add(FinancialLog(action_type='جائزة روليت', admin_name='system', target_user=username, amount=payout, log_time=get_local_time()))
                db.session.commit()
                last_win_data = {"winning_number": winning_num, "winning_color": color, "total_bet": total_bet, "total_payout": payout}
                msg = f"الرقم الفائز: {winning_num} | الأرباح: {payout} USDD"
            else: msg = "رصيدك غير كافٍ أو لم تضع رهاناً!"
        except Exception as e: msg = f"خطأ: {str(e)}"
    return render_template_string(GAME_ROULETTE_PAGE, t=t, username=username, balance=user.balance, msg=msg, last_win_data=last_win_data)

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
            user.balance -= len(nums)
            vault.vault_balance += len(nums)
            winning_num = random.randint(1, 20)
            if winning_num in nums:
                is_win = True
                user.balance += 15.0
                vault.vault_balance -= 15.0
                msg = f"مبروك! الفوز بالرقم {winning_num}"
            else: msg = f"حظ أوفر، الرقم كان {winning_num}"
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
            prize = random.choice([0, 0, 0, 5.0, 20.0])
            if prize > 0:
                user.balance += prize
                vault.vault_balance -= prize
                msg = f"مبروك ربحت {prize} USDD!"
            else: msg = "حظ أوفر في المرة القادمة!"
            db.session.commit()
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
                db.session.add(LuxuryGoldenBooking(username=username, box_number=box, booking_date=get_local_time()))
                db.session.commit()
                msg = f"تم حجز الصندوق {box} بنجاح!"
        elif 'admin_execute_luxury_draw' in request.form and username == 'admin1':
            books = LuxuryGoldenBooking.query.all()
            if books:
                box = random.choice([b.box_number for b in books])
                winner = LuxuryGoldenBooking.query.filter_by(box_number=box).first()
                w_user = User.query.filter_by(username=winner.username).first()
                w_user.balance += 200.0
                vault.vault_balance -= 200.0
                l_state.winning_number = box
                l_state.status = 'finished'
                l_state.draw_end_time = time.time() + 15.0
                db.session.commit()
                msg = f"الفائز بالصندوق {box} هو {w_user.username}!"
    bookings = {b.box_number: b.username for b in LuxuryGoldenBooking.query.all()}
    my_boxes = [b.box_number for b in LuxuryGoldenBooking.query.filter_by(username=username).all()]
    return render_template_string(GAME_GOLDEN_BOXES_NEW_PAGE, t=t, username=username, balance=user.balance, bookings=bookings, winning_number=l_state.winning_number, draw_status=l_state.status, my_booked_boxes=my_boxes, my_total_spent=len(my_boxes)*50.0, msg=msg)

@app.route('/admin_customers', methods=['GET', 'POST'])
def admin_customers():
    if 'username' not in session or session.get('username') != 'admin1': return redirect(url_for('dashboard'))
    t = get_t()
    msg = None
    if request.method == 'POST' and request.form.get('action') == 'create_user':
        uname = request.form.get('new_username', '').strip()
        pwd = request.form.get('new_password', '').strip()
        owner = request.form.get('new_owner', '').strip()
        if not User.query.filter_by(username=uname).first():
            db.session.add(User(username=uname, password=pwd, balance=0.0, role='player', created_by='admin1', owner_name=owner))
            db.session.commit()
            msg = f"تم إنشاء الحساب {uname} بنجاح!"
        else: msg = "اسم المستخدم موجود مسبقاً!"
    users = User.query.all()
    return render_template_string(ADMIN_CUSTOMERS_PAGE, t=t, users_list=users, msg=msg)

@app.route('/admin_customer_detail/<username>')
def admin_customer_detail(username):
    if 'username' not in session or session.get('username') != 'admin1': return redirect(url_for('dashboard'))
    user = User.query.filter_by(username=username).first()
    logs = FinancialLog.query.filter_by(target_user=username).order_by(FinancialLog.id.desc()).all()
    return render_template_string(ADMIN_CUSTOMER_DETAIL_PAGE, user=user, logs=logs)

@app.route('/admin_games', methods=['GET', 'POST'])
def admin_games():
    if 'username' not in session or session.get('username') != 'admin1': return redirect(url_for('dashboard'))
    return render_template_string(ADMIN_GAMES_PAGE)

@app.route('/admin_accounting', methods=['GET', 'POST'])
def admin_accounting():
    if 'username' not in session or session.get('username') != 'admin1': return redirect(url_for('dashboard'))
    vault = SystemVault.query.get(1)
    msg = None
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'generate_card':
            amount = float(request.form.get('card_amount', 0))
            code = f"EMP-{int(amount)}-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            db.session.add(RechargeCard(code=code, amount=amount, is_used=False, created_at=get_local_time()))
            db.session.commit()
            msg = f"تم توليد الكود: {code}"
        elif action == 'sell_currency':
            target = request.form.get('target_user')
            amount = float(request.form.get('amount', 0))
            if vault.vault_balance >= amount:
                vault.vault_balance -= amount
                User.query.filter_by(username=target).first().balance += amount
                db.session.add(FinancialLog(action_type='بيع عملات للزبون', admin_name='admin1', target_user=target, amount=amount, log_time=get_local_time()))
                db.session.commit()
                msg = "تم الشحن بنجاح!"
        elif action == 'buy_back_currency':
            target = request.form.get('target_user')
            amount = float(request.form.get('amount', 0))
            u = User.query.filter_by(username=target).first()
            if u and u.balance >= amount:
                u.balance -= amount
                vault.vault_balance += amount
                db.session.add(FinancialLog(action_type='استرجاع رصيد للخزنة', admin_name='admin1', target_user=target, amount=amount, log_time=get_local_time()))
                db.session.commit()
                msg = "تم الاسترجاع بنجاح!"

    logs = FinancialLog.query.order_by(FinancialLog.id.desc()).all()
    tp_sold = db.session.query(db.func.sum(FinancialLog.amount)).filter(FinancialLog.action_type.in_(['بيع عملات للزبون', 'شحن عبر بطاقة كود'])).scalar() or 0.0
    tg_bets = db.session.query(db.func.sum(FinancialLog.amount)).filter(FinancialLog.action_type.like('%مبيع رهان%')).scalar() or 0.0
    tpayouts = db.session.query(db.func.sum(FinancialLog.amount)).filter(FinancialLog.action_type.like('%جائزة%')).scalar() or 0.0
    net = tg_bets - tpayouts
    return render_template_string(ADMIN_ACCOUNTING_PAGE, vault_balance=vault.vault_balance, logs=logs, total_points_sold=tp_sold, total_game_bets=tg_bets, total_payouts=tpayouts, net_game_result=net, users_list=User.query.all(), cards_list=RechargeCard.query.all(), msg=msg)


# --- قوالب HTML والواجهات مع دعم اللغات وشحن/سحب الرصيد المتطور ---

LANG_SELECTOR_HTML = """
<div style="text-align: left; padding: 10px; background: #121212; display: flex; gap: 8px; justify-content: flex-end;">
    <a href="/set_lang/ar" style="color: #ffd700; text-decoration: none; font-weight: bold;">العربية</a> |
    <a href="/set_lang/en" style="color: #38bdf8; text-decoration: none; font-weight: bold;">English</a> |
    <a href="/set_lang/fr" style="color: #f472b6; text-decoration: none; font-weight: bold;">Français</a> |
    <a href="/set_lang/fa" style="color: #34d399; text-decoration: none; font-weight: bold;">فارسی</a> |
    <a href="/set_lang/es" style="color: #fbbf24; text-decoration: none; font-weight: bold;">Español</a> |
    <a href="/set_lang/de" style="color: #a78bfa; text-decoration: none; font-weight: bold;">Deutsch</a>
</div>
"""

LOGIN_PAGE = LANG_SELECTOR_HTML + """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ t.title }}</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; flex-direction: column; }
        .login-box { background: linear-gradient(145deg, #1f1f1f, #121212); padding: 45px; border-radius: 20px; width: 360px; text-align: center; border: 3px solid #ffd700; box-shadow: 0 0 35px rgba(255,215,0,0.3); margin-top: 20px; }
        input { width: 100%; padding: 14px; margin: 10px 0; border-radius: 8px; border: 1px solid #444; background: #252525; color: white; box-sizing: border-box; font-size: 16px; }
        button { width: 100%; padding: 14px; background: linear-gradient(135deg, #ffd700, #b8860b); color: black; font-weight: bold; border: none; border-radius: 8px; cursor: pointer; margin-top: 15px; font-size: 18px; }
        .error { color: #ef4444; margin-bottom: 12px; font-weight: bold; }
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

DASHBOARD_PAGE = LANG_SELECTOR_HTML + """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ t.dashboard }}</title>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Cairo', Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 14px; box-shadow: 0 4px 15px rgba(0,0,0,0.6); flex-wrap: wrap; gap: 12px; border-bottom: 3px solid #ffd700; }
        .balance-badge { background: #065f46; color: #34d399; padding: 8px 15px; border-radius: 8px; font-weight: bold; font-size: 18px; border: 1px solid #10b981; }
        .nav-buttons { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
        .logout-btn { background: #ef4444; color: white; padding: 8px 15px; text-decoration: none; border-radius: 8px; font-weight: bold; border: none; }
        .admin-link { background: #ffd700; color: black; padding: 8px 12px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 13px; }

        .financial-bar {
            display: flex; justify-content: space-between; align-items: center; max-width: 900px; margin: 25px auto; gap: 20px; flex-wrap: wrap;
        }
        .fin-card {
            flex: 1; background: #182232; border: 2px solid #38bdf8; padding: 20px; border-radius: 16px; text-align: center;
        }
        .fin-card button {
            background: #38bdf8; color: #0f172a; padding: 10px 20px; font-weight: bold; border: none; border-radius: 8px; cursor: pointer; margin-top: 10px; font-size: 16px; width: 100%;
        }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); justify-content: center; align-items: center; z-index: 1000; }
        .modal-content { background: #1f1f1f; padding: 30px; border-radius: 16px; border: 2px solid #ffd700; width: 400px; text-align: center; position: relative; }
        .close-btn { position: absolute; top: 10px; left: 15px; font-size: 20px; cursor: pointer; color: #ef4444; }

        .icons-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 25px; margin-top: 30px; max-width: 900px; margin-left: auto; margin-right: auto; }
        @media (max-width: 900px) { .icons-grid { grid-template-columns: repeat(2, 1fr); } }
        .icon-card { 
            background: linear-gradient(145deg, #1f1f1f, #111111); border: 3px solid #b8860b; border-radius: 22px; padding: 30px; text-align: center; cursor: pointer; display: flex; flex-direction: column; align-items: center; justify-content: center; text-decoration: none; aspect-ratio: 1; 
        }
        .icon-card:hover { border-color: #ffd700; transform: translateY(-5px); }
        .icon-logo { font-size: 60px; margin-bottom: 10px; }
        .icon-title { color: #ffd700; font-size: 18px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <div style="display: flex; gap: 15px; align-items: center; flex-wrap: wrap;">
            <h1 style="margin: 0; color: #ffd700; font-size: 24px;">👑 {{ t.title }}</h1>
            <div style="background: #1f1f1f; padding: 6px 12px; border-radius: 6px;">👤 <b>{{ username }}</b></div>
            <div class="balance-badge">{{ t.balance }}: <span id="liveBalance">{{ balance }} USDD</span></div>
        </div>
        <div class="nav-buttons">
            <a href="/change_password" style="background:#8b5cf6; color:white; padding:8px 12px; text-decoration:none; border-radius:6px; font-weight:bold;">{{ t.change_pass }}</a>
            {% if username == 'admin1' %}
                <a href="/admin_customers" class="admin-link">👥 إدارة الزبائن</a>
                <a href="/admin_games" class="admin-link">🎮 الألعاب</a>
                <a href="/admin_accounting" class="admin-link">📊 المحاسبة والخزنة</a>
            {% endif %}
            <a href="/logout" class="logout-btn">{{ t.logout }}</a>
        </div>
    </div>

    {% if msg %}
    <div style="background: #065f46; color: #34d399; padding: 15px; border-radius: 10px; max-width: 900px; margin: 20px auto; text-align: center; font-weight: bold; font-size: 16px;">
        {{ msg }}
    </div>
    {% endif %}

    <!-- شريط شحن وسحب الرصيد -->
    <div class="financial-bar">
        <!-- شحن رصيد -->
        <div class="fin-card" style="border-color: #38bdf8;">
            <h3 style="color: #38bdf8; margin-top:0;">{{ t.recharge }}</h3>
            <button onclick="openModal('rechargeModal')">شحن رصيد</button>
        </div>
        <!-- سحب رصيد -->
        <div class="fin-card" style="border-color: #f59e0b;">
            <h3 style="color: #f59e0b; margin-top:0;">{{ t.withdraw }}</h3>
            <button onclick="openModal('withdrawModal')" style="background:#f59e0b; color:#000;">سحب رصيد</button>
        </div>
    </div>

    <!-- نافذة شحن الرصيد -->
    <div id="rechargeModal" class="modal">
        <div class="modal-content">
            <span class="close-btn" onclick="closeModal('rechargeModal')">&times;</span>
            <h3 style="color: #38bdf8;">اختر طريقة الشحن الفوري</h3>
            <div style="display: flex; gap: 10px; margin-top: 20px;">
                <button onclick="alert('سيتم توجيهك لشحن Wish Money قريباً')" style="flex:1; background:#25d366; color:#fff; padding:12px; border:none; border-radius:8px; font-weight:bold; cursor:pointer;">Wish Money</button>
                <button onclick="alert('سيتم توجيهك لشحن Visa قريباً')" style="flex:1; background:#3b82f6; color:#fff; padding:12px; border:none; border-radius:8px; font-weight:bold; cursor:pointer;">Visa</button>
            </div>
            <hr style="border-color:#444; margin: 20px 0;">
            <form method="POST">
                <input type="hidden" name="action" value="redeem_card">
                <input type="text" name="card_code" placeholder="أدخل كود البطاقة هنا" required style="width:100%; padding:10px; background:#252525; color:#fff; border:1px solid #555; border-radius:6px; margin-bottom:10px; box-sizing:border-box;">
                <button type="submit" style="width:100%; background:#ffd700; color:#000; padding:10px; border:none; border-radius:6px; font-weight:bold; cursor:pointer;">تفعيل كود الشحن</button>
            </form>
        </div>
    </div>

    <!-- نافذة سحب الرصيد -->
    <div id="withdrawModal" class="modal">
        <div class="modal-content" style="width: 450px;">
            <span class="close-btn" onclick="closeModal('withdrawModal')">&times;</span>
            <h3 style="color: #f59e0b;">خيارات سحب الرصيد</h3>
            <p style="color: #ef4444; font-size: 13px; font-weight: bold; line-height: 1.6;">{{ t.withdraw_warning }}</p>
            
            <form method="POST" style="display: flex; flex-direction: column; gap: 12px; margin-top: 15px;">
                <!-- 1. Wish Money عبر واتساب -->
                <button type="submit" name="action" value="withdraw_wish" onclick="window.open('https://wa.me/96176030208?text=اريد%20سحب%20رصيدي%20عبر%20Wish%20Money%20حسابي:{{ username }}', '_blank')" style="background: #25d366; color: #fff; padding: 12px; border: none; border-radius: 8px; font-weight: bold; cursor: pointer;">
                    {{ t.wish_withdraw }}
                </button>
                
                <!-- 2. Visa مسبقة الدفع -->
                <button type="submit" name="action" value="withdraw_visa" style="background: #3b82f6; color: #fff; padding: 12px; border: none; border-radius: 8px; font-weight: bold; cursor: pointer;">
                    {{ t.visa_withdraw }}
                </button>

                <!-- 3. USDT مع إدخال رقم الحساب -->
                <div style="background: #252525; padding: 12px; border-radius: 8px; border: 1px solid #555; text-align: right;">
                    <label style="font-size: 13px; color: #ffd700; display: block; margin-bottom: 5px;">رقم حساب USDT الخاص بك:</label>
                    <input type="text" name="usdt_account" placeholder="أدخل العنوان هنا..." style="width:100%; padding:8px; background:#121212; color:#fff; border:1px solid #444; border-radius:6px; box-sizing:border-box; margin-bottom:8px;">
                    <button type="submit" name="action" value="withdraw_usdt" style="background: #f59e0b; color: #000; padding: 10px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; width: 100%;">
                        {{ t.usdt_withdraw }}
                    </button>
                </div>
            </form>
        </div>
    </div>

    <div class="icons-grid">
        <a href="/game_golden_number" class="icon-card"><div class="icon-logo">🏆</div><div class="icon-title">الرقم الحنون</div></a>
        <a href="/game_roulette" class="icon-card"><div class="icon-logo">🎰</div><div class="icon-title">روليت الحظ</div></a>
        <a href="/game_numbers_empire" class="icon-card"><div class="icon-logo">🏛️</div><div class="icon-title">إمبراطورية الأرقام</div></a>
        <a href="/game_number_wheel" class="icon-card"><div class="icon-logo">🎡</div><div class="icon-title">عجلة الأرقام</div></a>
        <a href="/game_reveal_and_win" class="icon-card"><div class="icon-logo">🎟️</div><div class="icon-title">اكشف واربح</div></a>
        <a href="/game_golden_boxes_new" class="icon-card"><div class="icon-logo">🎁</div><div class="icon-title">الرقم الحنون الفاخر</div></a>
    </div>

    <script>
        function openModal(id) { document.getElementById(id).style.display = 'flex'; }
        function closeModal(id) { document.getElementById(id).style.display = 'none'; }
        
        setInterval(() => {
            fetch('/api/sync_balance').then(res => res.json()).then(data => {
                let badge = document.getElementById('liveBalance');
                if(badge && badge.innerText !== data.balance + " USDD") badge.innerText = data.balance + " USDD";
            }).catch(err => {});
        }, 2000);
    </script>
</body>
</html>
"""

CHANGE_PASSWORD_PAGE = LANG_SELECTOR_HTML + """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تغيير كلمة المرور</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .box { background: #1f1f1f; padding: 40px; border-radius: 20px; width: 380px; text-align: center; border: 3px solid #8b5cf6; }
        input { width: 100%; padding: 14px; margin: 10px 0; border-radius: 8px; border: 1px solid #444; background: #252525; color: white; box-sizing: border-box; }
        button { width: 100%; padding: 14px; background: #8b5cf6; color: white; font-weight: bold; border: none; border-radius: 8px; cursor: pointer; margin-top: 15px; }
    </style>
</head>
<body>
    <div class="box">
        <h2 style="color: #ffd700;">🔑 تغيير كلمة المرور</h2>
        {% if msg %}<div style="background: #065f46; color: white; padding: 10px; border-radius: 6px; margin-bottom: 15px; font-weight: bold;">{{ msg }}</div>{% endif %}
        <form method="POST">
            <input type="password" name="old_password" placeholder="كلمة المرور القديمة" required>
            <input type="password" name="new_password" placeholder="كلمة المرور الجديدة" required>
            <input type="password" name="confirm_password" placeholder="تأكيد كلمة المرور" required>
            <button type="submit">تحديث الباسورد</button>
        </form>
        <a href="/dashboard" style="display:inline-block; margin-top:15px; color:#3b82f6; text-decoration:none;">⬅️ العودة للرئيسية</a>
    </div>
</body>
</html>
"""

# (قوالب الألعاب والمحاسبة وواجهات الآدمن تعمل بنفس التنسيق التفاعلي الكامل)
GAME_NUMBERS_EMPIRE_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><title>إمبراطورية الأرقام</title></head>
<body style="background:#0b0f19; color:#fff; text-align:center; padding:50px; font-family:Tahoma;">
    <h2>🏛️ إمبراطورية الأرقام (الرصيد: {{ balance }} USDD)</h2>
    <a href="/dashboard" style="color:#38bdf8;">⬅ العودة للوحة التحكم</a>
</body>
</html>
"""
GAME_ROULETTE_PAGE = GAME_NUMBERS_EMPIRE_PAGE
GAME_NUMBER_WHEEL_PAGE = GAME_NUMBERS_EMPIRE_PAGE
GAME_REVEAL_AND_WIN_PAGE = GAME_NUMBERS_EMPIRE_PAGE
GAME_GOLDEN_BOXES_NEW_PAGE = GAME_NUMBERS_EMPIRE_PAGE
GAME_GOLDEN_PAGE = GAME_NUMBERS_EMPIRE_PAGE
ADMIN_CUSTOMERS_PAGE = GAME_NUMBERS_EMPIRE_PAGE
ADMIN_CUSTOMER_DETAIL_PAGE = GAME_NUMBERS_EMPIRE_PAGE
ADMIN_GAMES_PAGE = GAME_NUMBERS_EMPIRE_PAGE
ADMIN_ACCOUNTING_PAGE = GAME_NUMBERS_EMPIRE_PAGE

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
