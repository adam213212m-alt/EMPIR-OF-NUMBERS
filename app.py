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

# --- الترجمات ---
TRANSLATIONS = {
    'ar': {
        'dir': 'rtl', 'title': 'امبراطورية الأرقام', 'subtitle': 'منصة الألعاب التفاعلية الفائقة 12D',
        'login': 'دخول للبرنامج', 'username': 'اسم المستخدم', 'password': 'كلمة المرور', 'balance': 'الرصيد',
        'recharge': 'شحن رصيد', 'withdraw': 'سحب رصيد', 'logout': 'خروج',
        'dashboard': 'لوحة التحكم', 'customers': 'الزبائن', 'accounting': 'المحاسبة والخزنة',
        'game_control': '🎮 غرفة تحكم الألعاب', 'chat': '💬 الدردشة الفورية',
        'game1': 'الرقم الحنون', 'game2': 'روليت الحظ', 'game3': 'إمبراطورية الأرقام', 'game4': 'عجلة الحظ', 'game5': 'اكشف واربح', 'game6': 'رمي السهم المتحركة'
    }
}

def get_t():
    return TRANSLATIONS['ar']

def get_lang_bar():
    return """
<div style="padding: 10px 25px; background: rgba(18, 18, 25, 0.95); display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,215,0,0.2);">
    <div style="display: flex; align-items: center; gap: 12px;">
        <a href="javascript:location.reload();" style="background: rgba(255,215,0,0.1); border: 1px solid #ffd700; color:#ffd700; padding: 6px 12px; text-decoration:none; border-radius:8px; font-weight:bold;">🔄 تحديث</a>
        <button id="installBtn" onclick="installApp()" style="background: linear-gradient(135deg, #3b82f6, #1d4ed8); border: none; color: #fff; padding: 6px 14px; border-radius: 8px; font-weight: bold; cursor: pointer; display: none;">📲 تثبيت البرنامج</button>
    </div>
    <div style="display:flex; gap:15px; align-items:center;">
        <div style="background:rgba(6,95,70,0.8); color:#34d399; padding:6px 14px; border-radius:8px; font-weight:900;">الرصيد: <span id="globalLiveBalance">...</span> USDD</div>
        <a href="/dashboard" style="color:#ffd700; text-decoration:none; font-weight:bold;">🏠 الرئيسية</a>
    </div>
</div>
<script>
    let deferredPrompt;
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredPrompt = e;
        let btn = document.getElementById('installBtn');
        if(btn) btn.style.display = 'flex';
    });
    function installApp() {
        if (deferredPrompt) {
            deferredPrompt.prompt();
            deferredPrompt.userChoice.then((choiceResult) => {
                deferredPrompt = null;
            });
        } else {
            alert("لتثبيت التطبيق، انقر على خيارات المتصفح واختر 'إضافة إلى الشاشة الرئيسية'.");
        }
    }
    setInterval(() => {
        fetch('/api/sync_balance').then(res => res.json()).then(data => {
            let b = document.getElementById('globalLiveBalance');
            if(b && b.innerText !== String(data.balance)) b.innerText = data.balance;
        }).catch(err => {});
    }, 2000);
</script>
"""

@app.route('/api/sync_balance')
def sync_balance():
    if 'username' in session:
        u = User.query.filter_by(username=session['username']).first()
        return jsonify({'balance': u.balance if u else 0.0})
    return jsonify({'balance': 0.0})

LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>امبراطورية الأرقام</title></head>
<body style="font-family:Tahoma; background:#1a1c29; color:#fff; display:flex; justify-content:center; align-items:center; min-height:95vh; margin:0; padding:15px;">
    <div style="background:rgba(20, 24, 38, 0.95); padding:35px; border-radius:25px; width:100%; max-width:400px; text-align:center; border:2px solid #ffd700; box-shadow:0 20px 50px rgba(0,0,0,0.8);">
        <h2 style="color:#ffd700; margin-top:0;">👑 امبراطورية الأرقام</h2>
        {% if error %}<div style="color:#ef4444; margin-bottom:15px; font-weight:bold;">{{ error }}</div>{% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="اسم المستخدم" required style="width:100%; padding:14px; margin:10px 0; border-radius:12px; background:#0a0d16; color:#fff; border:1px solid #444; box-sizing:border-box;">
            <input type="password" name="password" placeholder="كلمة المرور" required style="width:100%; padding:14px; margin:10px 0; border-radius:12px; background:#0a0d16; color:#fff; border:1px solid #444; box-sizing:border-box;">
            <button type="submit" style="width:100%; padding:14px; background:linear-gradient(135deg, #ffd700, #ff8c00); color:#000; font-weight:900; border:none; border-radius:12px; cursor:pointer; font-size:17px; margin-top:5px;">دخول للبرنامج</button>
        </form>
        <div style="margin-top:20px; display:flex; flex-direction:column; gap:10px;">
            <a href="/guest_login" style="background:rgba(56,189,248,0.15); border:1px solid #38bdf8; color:#38bdf8; padding:12px; text-decoration:none; border-radius:12px; font-weight:bold; display:block;">👁️ تسجيل كزائر (تصفح المنصة)</a>
            <a href="https://wa.me/96176030208?text=مرحباً، أريد إنشاء حساب جديد" target="_blank" style="background:rgba(34,197,94,0.15); border:1px solid #22c55e; color:#34d399; padding:12px; text-decoration:none; border-radius:12px; font-weight:bold; display:block;">💬 إنشاء حساب عبر واتساب</a>
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
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>لوحة التحكم</title>
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
            <h2 style="color:#ffd700; margin:0;">👑 امبراطورية الأرقام (12D)</h2>
            <div style="background:rgba(15,20,32,0.9); padding:8px 15px; border-radius:10px;">👤 <b>{{ username }}</b></div>
            <div style="background:rgba(6,95,70,0.8); color:#34d399; padding:8px 18px; border-radius:10px; font-weight:900;">الرصيد: <span id="liveBalance">{{ balance }}</span> USDD</div>
        </div>
        <div style="display:flex; gap:12px; flex-wrap:wrap;">
            {% if username == 'admin1' %}
                <a href="/admin_customers" style="background:#ffd700; color:#000; padding:10px 16px; text-decoration:none; border-radius:10px; font-weight:900;">👥 الزبائن</a>
                <a href="/admin_accounting" style="background:#ffd700; color:#000; padding:10px 16px; text-decoration:none; border-radius:10px; font-weight:900;">📊 المحاسبة</a>
            {% endif %}
            <a href="/logout" style="background:#ef4444; color:#fff; padding:10px 16px; text-decoration:none; border-radius:10px; font-weight:900;">خروج</a>
        </div>
    </div>

    <div class="icons-grid">
        <a href="/game_golden_number" class="icon-card"><div style="font-size:55px;">🏆</div><div style="color:#ffd700; font-size:18px; font-weight:900; margin-top:10px;">الرقم الحنون</div></a>
        <a href="/game_roulette" class="icon-card"><div style="font-size:55px;">🎰</div><div style="color:#ffd700; font-size:18px; font-weight:900; margin-top:10px;">روليت الحظ</div></a>
        <a href="/game_numbers_empire" class="icon-card"><div style="font-size:55px;">🏛️</div><div style="color:#ffd700; font-size:18px; font-weight:900; margin-top:10px;">إمبراطورية الأرقام</div></a>
        <a href="/game_number_wheel" class="icon-card"><div style="font-size:55px;">🎡</div><div style="color:#ffd700; font-size:18px; font-weight:900; margin-top:10px;">عجلة الحظ</div></a>
        <a href="/game_reveal_and_win" class="icon-card"><div style="font-size:55px;">🎟️</div><div style="color:#ffd700; font-size:18px; font-weight:900; margin-top:10px;">اكشف واربح</div></a>
        <a href="/game_arrow_wheel" class="icon-card"><div style="font-size:55px;">🎯</div><div style="color:#ffd700; font-size:18px; font-weight:900; margin-top:10px;">رمي السهم المتحركة</div></a>
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
    return render_template_string(LOGIN_PAGE, error=error)

@app.route('/guest_login')
def guest_login():
    session.clear()
    session['username'] = 'زائر_' + ''.join(random.choices(string.digits, k=4))
    session['balance'] = 0.0
    session['role'] = 'guest'
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    bal = user.balance if user else 0.0
    return render_template_string(DASHBOARD_PAGE, username=session['username'], balance=bal)

# مسارات الألعاب الأساسية (كإطارات مؤقتة لتكتمل المنصة)
@app.route('/game_golden_number')
def game_golden_number():
    if 'username' not in session: return redirect(url_for('login'))
    return f"{get_lang_bar()}<div style='text-align:center; padding:50px; color:#fff; font-family:Tahoma;'><h2>🏆 لعبة الرقم الحنون</h2><a href='/dashboard' style='color:#ffd700;'>🏠 عودة للرئيسية</a></div>"

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

@app.route('/admin_customers')
def admin_customers():
    if session.get('username') != 'admin1': return redirect(url_for('dashboard'))
    users = User.query.all()
    return f"{get_lang_bar()}<div style='text-align:center; padding:30px; color:#fff; font-family:Tahoma;'><h2>👥 إدارة الزبائن</h2><ul>" + "".join([f"<li>{u.username} - الرصيد: {u.balance}</li>" for u in users]) + "</ul><a href='/dashboard' style='color:#ffd700;'>🏠 عودة للرئيسية</a></div>"

@app.route('/admin_accounting')
def admin_accounting():
    if session.get('username') != 'admin1': return redirect(url_for('dashboard'))
    return f"{get_lang_bar()}<div style='text-align:center; padding:30px; color:#fff; font-family:Tahoma;'><h2>📊 المحاسبة والخزنة</h2><a href='/dashboard' style='color:#ffd700;'>🏠 عودة للرئيسية</a></div>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
