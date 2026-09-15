from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = 'empire_of_numbers_secure_2026_key'

# --- إعداد قاعدة البيانات ---
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
    owner_name = db.Column(db.String(100), default='غير محدد')

class SystemVault(db.Model):
    __tablename__ = 'system_vault'
    id = db.Column(db.Integer, primary_key=True)
    vault_balance = db.Column(db.Float, default=1000000.0)

# --- تهيئة الجداول وحساب الآدمن الأساسي ---
with app.app_context():
    db.create_all()
    vault = SystemVault.query.get(1)
    if not vault:
        db.session.add(SystemVault(id=1, vault_balance=1000000.0))
    if not User.query.filter_by(username='admin1').first():
        db.session.add(User(username='admin1', password='admin123', balance=0.0, role='admin', owner_name='المشرف العام'))
        db.session.commit()

# --- قوالب HTML المستقرة والكاملة ---

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><title>امبراطورية الأرقام - دخول</title>
    <style>
        body { font-family: Tahoma, sans-serif; background: #0b0f19; color: #fff; display: flex; justify-content: center; align-items: center; height: 90vh; margin: 0; }
        .box { background: #141826; padding: 40px; border-radius: 20px; width: 350px; text-align: center; border: 2px solid #ffd700; box-shadow: 0 10px 30px rgba(0,0,0,0.8); }
        input { width: 100%; padding: 12px; margin: 10px 0; border-radius: 8px; border: 1px solid #444; background: #070a12; color: #fff; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: linear-gradient(135deg, #ffd700, #ff8c00); color: #000; font-weight: bold; border: none; border-radius: 8px; cursor: pointer; margin-top: 10px; font-size: 16px; }
        .error { color: #ef4444; margin-bottom: 10px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="box">
        <h2 style="color: #ffd700;">👑 امبراطورية الأرقام</h2>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="اسم المستخدم" required>
            <input type="password" name="password" placeholder="كلمة المرور" required>
            <button type="submit">دخول للبرنامج</button>
        </form>
    </div>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><title>لوحة التحكم الرئيسية</title>
    <style>
        body { font-family: Tahoma, sans-serif; background: #070a12; color: #fff; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #141826; padding: 15px 25px; border-radius: 12px; border-bottom: 3px solid #ffd700; flex-wrap: wrap; gap: 10px; }
        .card { background: #181f33; padding: 30px; border-radius: 15px; margin-top: 30px; text-align: center; border: 1px solid #38bdf8; }
        a.btn { background: #ef4444; color: #fff; padding: 8px 16px; text-decoration: none; border-radius: 8px; font-weight: bold; }
        a.admin-btn { background: #ffd700; color: #000; padding: 8px 16px; text-decoration: none; border-radius: 8px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h2 style="color: #ffd700; margin: 0;">👑 لوحة التحكم - امبراطورية الأرقام</h2>
        <div>
            <span>المستخدم: <b>{{ username }}</b></span> | 
            <span>الرصيد: <b style="color: #34d399;">{{ balance }} USDD</b></span>
            {% if username == 'admin1' %}
                | <a href="/admin_customers" class="admin-btn">👥 الزبائن</a>
                | <a href="/admin_accounting" class="admin-btn">📊 الخزنة</a>
            {% endif %}
            | <a href="/logout" class="btn">خروج</a>
        </div>
    </div>
    <div class="card">
        <h3 style="color: #38bdf8;">النظام يعمل بكفاءة واستقرار تام 🚀</h3>
        <p>تم تفعيل لوحات التحكم والمسارات بنجاح بدون أي أخطاء.</p>
    </div>
</body>
</html>
"""

ADMIN_CUSTOMERS_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><title>إدارة الزبائن</title>
    <style>
        body { font-family: Tahoma, sans-serif; background: #070a12; color: #fff; padding: 25px; text-align: center; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; background: #141826; border-radius: 10px; overflow: hidden; }
        th, td { border: 1px solid #333; padding: 12px; }
        th { background: #1f2937; color: #ffd700; }
        a.back { background: #3b82f6; color: #fff; padding: 10px 20px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block; margin-bottom: 20px; }
    </style>
</head>
<body>
    <h2>👥 إدارة الزبائن والحسابات</h2>
    <a href="/dashboard" class="back">🏠 العودة للرئيسية</a>
    <div style="max-width: 800px; margin: 0 auto;">
        <table>
            <tr><th>اسم المستخدم</th><th>اسم المالك</th><th>الرصيد</th></tr>
            {% for u in users %}
            <tr><td><b>{{ u.username }}</b></td><td>{{ u.owner_name }}</td><td style="color: #34d399;">{{ u.balance }} USDD</td></tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

ADMIN_ACCOUNTING_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><title>الخزنة والمحاسبة</title>
    <style>
        body { font-family: Tahoma, sans-serif; background: #070a12; color: #fff; padding: 25px; text-align: center; }
        .vault-box { background: #065f46; border: 2px solid #34d399; padding: 30px; border-radius: 15px; max-width: 500px; margin: 20px auto; }
        a.back { background: #3b82f6; color: #fff; padding: 10px 20px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block; margin-bottom: 20px; }
    </style>
</head>
<body>
    <h2>📊 برنامج المحاسبة والخزنة المركزية</h2>
    <a href="/dashboard" class="back">🏠 العودة للرئيسية</a>
    <div class="vault-box">
        <h3>🏦 رصيد الخزنة الأساسية</h3>
        <div style="font-size: 40px; font-weight: bold; color: #fff; margin-top: 10px;">{{ vault_balance }} USDD</div>
    </div>
</body>
</html>
"""

# --- مسارات التطبيق (Routes) ---

@app.route('/', methods=['GET', 'POST'])
def login():
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
            error = "اسم المستخدم أو كلمة المرور غير صحيحة!"
    return render_template_string(LOGIN_TEMPLATE, error=error)

@app.route('/dashboard')
def dashboard():
    if 'username' not in session: 
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    return render_template_string(DASHBOARD_TEMPLATE, username=user.username, balance=user.balance)

@app.route('/admin_customers')
def admin_customers():
    if 'username' not in session or session.get('username') != 'admin1': 
        return redirect(url_for('dashboard'))
    users = User.query.all()
    return render_template_string(ADMIN_CUSTOMERS_TEMPLATE, users=users)

@app.route('/admin_accounting')
def admin_accounting():
    if 'username' not in session or session.get('username') != 'admin1': 
        return redirect(url_for('dashboard'))
    vault = SystemVault.query.get(1)
    return render_template_string(ADMIN_ACCOUNTING_TEMPLATE, vault_balance=vault.vault_balance if vault else 0.0)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
