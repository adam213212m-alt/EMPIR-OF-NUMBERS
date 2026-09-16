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
    }
}

def get_t():
    lang = session.get('lang', 'ar')
    if lang not in TRANSLATIONS: lang = 'ar'
    return TRANSLATIONS[lang]

LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{{ t.title }} - 12D</title></head>
<body style="font-family:'Segoe UI', Tahoma, sans-serif; background:radial-gradient(circle at center, #1a1c29 0%, #0b0f19 100%); color:#fff; display:flex; justify-content:center; align-items:center; min-height:95vh; margin:0; box-sizing:border-box; padding:15px;">
    <div style="background:rgba(20, 24, 38, 0.9); padding:35px; border-radius:25px; width:100%; max-width:400px; text-align:center; border:2px solid rgba(255,215,0,0.5); box-sizing:border-box; box-shadow:0 20px 50px rgba(0,0,0,0.8);">
        <h2 style="color:#ffd700; margin-top:0;">👑 {{ t.title }}</h2>
        {% if error %}<div style="color:#ef4444; margin-bottom:15px; font-weight:bold;">{{ error }}</div>{% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="{{ t.username }}" required style="width:100%; padding:14px; margin:10px 0; border-radius:12px; background:rgba(10, 13, 22, 0.8); color:#fff; border:1px solid #444; box-sizing:border-box;">
            <input type="password" name="password" placeholder="{{ t.password }}" required style="width:100%; padding:14px; margin:10px 0; border-radius:12px; background:rgba(10, 13, 22, 0.8); color:#fff; border:1px solid #444; box-sizing:border-box;">
            <button type="submit" style="width:100%; padding:14px; background:linear-gradient(135deg, #ffd700, #ff8c00); color:#000; font-weight:900; border:none; border-radius:12px; cursor:pointer; font-size:17px; margin-top:5px;">{{ t.login }}</button>
        </form>
        <div style="margin-top:20px; display:flex; flex-direction:column; gap:10px;">
            <a href="/guest_login" style="background:rgba(56,189,248,0.15); border:1px solid #38bdf8; color:#38bdf8; padding:12px; text-decoration:none; border-radius:12px; font-weight:bold; font-size:15px; display:block;">👁️ تسجيل كزائر (تصفح المنصة)</a>
            <a href="https://wa.me/96176030208?text=مرحباً، أريد إنشاء حساب جديد في منصة امبراطورية الأرقام" target="_blank" style="background:rgba(34,197,94,0.15); border:1px solid #22c55e; color:#34d399; padding:12px; text-decoration:none; border-radius:12px; font-weight:bold; font-size:15px; display:block;">💬 إنشاء حساب عبر واتساب</a>
        </div>
        <div style="margin-top:25px; background:#0a0d16; padding:12px; border-radius:15px; border:1px solid #444;">
            <p style="font-size:12px; color:#ffd700; margin:0 0 8px 0;">امسح الكود لفتح اللعبة عبر هاتفك:</p>
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=120x120&data={{ request.host_url }}" alt="QR Code" style="border-radius:8px; border:2px solid #ffd700;">
        </div>
    </div>
</body>
</html>
"""

# --- مسار الصفحة الرئيسية (يعالج خطأ 404 تماماً) ---
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
    guest_name = 'زائر_' + ''.join(random.choices(string.digits, k=4))
    session['username'] = guest_name
    session['balance'] = 0.0
    session['role'] = 'guest'
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    bal = user.balance if user else 0.0
    return f"<h1>لوحة التحكم - أهلاً {session['username']}</h1><p>الرصيد: {bal}</p><a href='/logout'>خروج</a>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
