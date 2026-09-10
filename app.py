from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import sqlite3
import random
import time
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
app.secret_key = 'empire_lira_clean_2026'

def init_db():
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # جدول المستخدمين (محفوظ بالكامل ولا يتأثر بالتحديثات)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            balance REAL DEFAULT 0,
            role TEXT,
            created_by TEXT
        )
    ''')

    # جدول خزنة البرنامج المركزية (مليون دولار خاص بالبرنامج)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_vault (
            id INTEGER PRIMARY KEY,
            vault_balance REAL DEFAULT 1000000.0
        )
    ''')
    cursor.execute('SELECT COUNT(*) FROM system_vault')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO system_vault (id, vault_balance) VALUES (1, 1000000.0)')

    # سجل الحركات المالية
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS financial_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_type TEXT,
            admin_name TEXT,
            target_user TEXT,
            amount REAL,
            log_time TEXT
        )
    ''')
    
    # إنشاء الـ 3 حسابات الرئيسية المسؤولة (admin1, admin2, admin3) إن لم تكن موجودة
    main_admins = ['admin1', 'admin2', 'admin3']
    for adm in main_admins:
        cursor.execute("SELECT * FROM users WHERE username=?", (adm,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (username, password, balance, role, created_by) VALUES (?, ?, 0.0, 'admin', 'system')", 
                           (adm, 'admin123'))

    conn.commit()
    conn.close()

init_db()

@app.route('/manifest.json')
def manifest():
    manifest_data = {
        "name": "Lira ليرة الألعاب التفاعلية",
        "short_name": "Lira",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0b0f19",
        "theme_color": "#ffd700",
        "icons": [{"src": "https://img.icons8.com/color/512/crown.png", "sizes": "512x512", "type": "image/png"}]
    }
    return app.response_class(str(manifest_data).replace("'", '"'), status=200, mimetype='application/json')

@app.route('/sw.js')
def service_worker():
    return app.response_class("self.addEventListener('fetch', function(event) { });", mimetype='application/javascript')

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session.clear()
            session['username'] = user[1]
            session['password'] = user[2]
            session['balance'] = user[3]
            session['role'] = user[4]
            return redirect(url_for('dashboard'))
        else:
            error = f"خطأ: اسم المستخدم '{username}' أو كلمة المرور غير صحيحة!"
    return render_template_string(LOGIN_PAGE, error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE username=?", (session['username'],))
    balance = cursor.fetchone()[0]
    conn.close()
    return render_template_string(DASHBOARD_PAGE, username=session['username'], role=session['role'], balance=balance)

@app.route('/game_one_page')
def game_one_page():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE username=?", (session['username'],))
    balance = cursor.fetchone()[0]
    conn.close()
    return render_template_string(GAME_ONE_PAGE, username=session['username'], balance=balance)

@app.route('/game_two_page')
def game_two_page():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE username=?", (session['username'],))
    balance = cursor.fetchone()[0]
    conn.close()
    return render_template_string(GAME_TWO_PAGE, username=session['username'], balance=balance)

# لوحة التحكم الخاصة بـ admin1, admin2, admin3 (تم تصحيح الخطأ البرمجي هنا)
@app.route('/admin_panel', methods=['GET', 'POST'])
def admin_panel():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('dashboard'))
    
    current_admin = session['username']
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()

    if request.method == 'POST':
        action = request.form.get('action')
        target_user = request.form.get('target_user', '').strip()
        amount = float(request.form.get('amount', 0))

        cursor.execute("SELECT vault_balance FROM system_vault WHERE id=1")
        vault_bal = cursor.fetchone()[0]

        cursor.execute("SELECT balance FROM users WHERE username=?", (target_user,))
        user_row = cursor.fetchone()

        if user_row and amount > 0:
            if action == 'sell' and vault_bal >= amount:
                cursor.execute("UPDATE system_vault SET vault_balance = vault_balance - ? WHERE id=1", (amount,))
                cursor.execute("UPDATE users SET balance = balance + ? WHERE username=?", (amount, target_user))
                cursor.execute("INSERT INTO financial_logs (action_type, admin_name, target_user, amount, log_time) VALUES ('بيع رصيد (من الخزنة)', ?, ?, ?, ?)", 
                               (current_admin, target_user, amount, time.strftime('%Y-%m-%d %H:%M')))
                conn.commit()
            elif action == 'buy_back' and user_row[0] >= amount:
                cursor.execute("UPDATE users SET balance = balance - ? WHERE username=?", (amount, target_user))
                cursor.execute("UPDATE system_vault SET vault_balance = vault_balance + ? WHERE id=1", (amount,))
                cursor.execute("INSERT INTO financial_logs (action_type, admin_name, target_user, amount, log_time) VALUES ('شراء رصيد (إلى الخزنة)', ?, ?, ?, ?)", 
                               (current_admin, target_user, amount, time.strftime('%Y-%m-%d %H:%M')))
                conn.commit()

        return redirect(url_for('admin_panel'))

    cursor.execute("SELECT vault_balance FROM system_vault WHERE id=1")
    vault_balance = cursor.fetchone()[0]

    # جلب قائمة الزبائن وأرصدتهم
    cursor.execute("SELECT username, balance, created_by FROM users WHERE role != 'admin'")
    users_list = cursor.fetchall()

    cursor.execute("SELECT action_type, admin_name, target_user, amount, log_time FROM financial_logs ORDER BY id DESC LIMIT 15")
    logs = cursor.fetchall()

    conn.close()
    return render_template_string(ADMIN_PAGE, username=current_admin, vault_balance=vault_balance, users_list=users_list, logs=logs)

@app.route('/create_user_page', methods=['GET', 'POST'])
def create_user_page():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('dashboard'))
    msg = None
    if request.method == 'POST':
        new_user = request.form.get('new_user', '').strip()
        new_pass = request.form.get('new_pass', '').strip()
        conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password, balance, role, created_by) VALUES (?, ?, 0, 'player', ?)", 
                           (new_user, new_pass, session['username']))
            conn.commit()
            msg = f"تم إنشاء حساب الزبون '{new_user}' وحفظه في القاعدة بنجاح!"
        except sqlite3.IntegrityError:
            msg = "خطأ: اسم المستخدم موجود مسبقاً!"
        conn.close()
    return render_template_string(CREATE_USER_PAGE, msg=msg)

DASHBOARD_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lira ليرة - لوحة التحكم</title>
    <link rel="manifest" href="/manifest.json">
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); flex-wrap: wrap; gap: 10px; border-bottom: 2px solid #ffd700; }
        .logo-area { display: flex; align-items: center; gap: 15px; flex-wrap: wrap; }
        .logo-badge { background: linear-gradient(135deg, #ffd700, #b8860b); color: #000; width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 26px; }
        .logo-area h1 { margin: 0; color: #ffd700; font-size: 26px; font-weight: bold; }
        .user-creds { background: #1f1f1f; padding: 6px 12px; border-radius: 6px; font-size: 14px; color: #cbd5e1; border: 1px dashed #ffd700; }
        .balance-badge { background: #065f46; color: #34d399; padding: 8px 15px; border-radius: 8px; font-weight: bold; font-size: 18px; border: 1px solid #10b981; }
        .whatsapp-btn { background: #25d366; color: white; padding: 8px 15px; text-decoration: none; border-radius: 8px; font-weight: bold; }
        .logout-btn { background: #ef4444; color: white; padding: 8px 15px; text-decoration: none; border-radius: 8px; font-weight: bold; border: none; cursor: pointer; }
        .admin-link-btn { background: #ffd700; color: black; padding: 8px 15px; text-decoration: none; border-radius: 8px; font-weight: bold; }
        
        .icons-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-top: 40px; }
        @media (max-width: 900px) { .icons-grid { grid-template-columns: repeat(2, 1fr); } }
        @media (max-width: 500px) { .icons-grid { grid-template-columns: 1fr; } }
        
        .icon-card { background: #1f1f1f; border: 2px solid #333; border-radius: 16px; padding: 30px; text-align: center; cursor: pointer; transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(0,0,0,0.6); display: flex; flex-direction: column; align-items: center; justify-content: center; text-decoration: none; }
        .icon-card:hover { border-color: #ffd700; transform: translateY(-5px); box-shadow: 0 8px 25px rgba(255,215,0,0.3); }
        .icon-logo { font-size: 50px; margin-bottom: 12px; }
        .icon-title { color: #ffffff; font-size: 16px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo-area">
            <div class="logo-badge">👑</div>
            <h1>Lira | ليرة</h1>
            <div class="user-creds">👤 <b>{{ username }}</b> {% if role == 'admin' %} | 🔑 <b>مدير النظام</b>{% endif %}</div>
            <div class="balance-badge">الرصيد الشخصي: <span>${{ balance }}</span></div>
        </div>
        <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
            <a class="whatsapp-btn" href="https://wa.me/96176030208?text=الرجاء%20شحن%20رصيد%20حسابي%20بمنصة%20Lira%20باسم%20المستخدم:%20{{ username }}" target="_blank">💬 شراء رصيد (واتساب)</a>
            {% if role == 'admin' %}<a href="/admin_panel" class="admin-link-btn">👑 لوحة إدارة المديرين (الخزنة)</a>{% endif %}
            <a href="/logout" class="logout-btn">🚪 خروج</a>
        </div>
    </div>

    <div class="icons-grid">
        <a href="/game_one_page" class="icon-card">
            <div class="icon-logo">👑</div>
            <div class="icon-title">اللعبة الأولى (الملكية)</div>
        </a>
        <a href="/game_two_page" class="icon-card">
            <div class="icon-logo">🎰</div>
            <div class="icon-title">اللعبة الثانية (الروليت)</div>
        </a>
        <div class="icon-card" onclick="alert('قيد الإنشاء والتصميم')">
            <div class="icon-logo">⚡</div>
            <div class="icon-title">لعبة الحظ السريع</div>
        </div>
        <div class="icon-card" onclick="alert('قيد الإنشاء والتصميم')">
            <div class="icon-logo">🏇</div>
            <div class="icon-title">سباق الخيل التفاعلي</div>
        </div>
        <div class="icon-card" onclick="alert('قيد الإنشاء والتصميم')">
            <div class="icon-logo">🎡</div>
            <div class="icon-title">عجلة الثروة الكبرى</div>
        </div>
        <div class="icon-card" onclick="alert('قيد الإنشاء والتصميم')">
            <div class="icon-logo">🎁</div>
            <div class="icon-title">صناديق المفاجآت الذهبية</div>
        </div>
        <div class="icon-card" onclick="alert('قيد الإنشاء والتصميم')">
            <div class="icon-logo">🔢</div>
            <div class="icon-title">تحدي الأرقام الفائزة</div>
        </div>
        <div class="icon-card" onclick="alert('قيد الإنشاء والتصميم')">
            <div class="icon-logo">🃏</div>
            <div class="icon-title">البوكر الملكي المباشر</div>
        </div>
    </div>
</body>
</html>
"""

ADMIN_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>لوحة إدارة المديرين والخزنة - Lira</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; padding: 20px; }
        .admin-header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 12px; border: 2px solid #ffd700; margin-bottom: 25px; flex-wrap: wrap; gap: 10px; }
        .vault-box { background: linear-gradient(135deg, #065f46, #047857); border: 3px solid #34d399; padding: 25px; border-radius: 16px; text-align: center; margin-bottom: 25px; box-shadow: 0 0 30px rgba(52,211,153,0.3); }
        .panel-box { background: #1f1f1f; padding: 20px; border-radius: 12px; border: 1px solid #444; margin-bottom: 20px; }
        input, select { width: 100%; padding: 10px; margin: 8px 0; border-radius: 6px; background: #252525; color: white; border: 1px solid #555; box-sizing: border-box; }
        button { padding: 10px 20px; font-weight: bold; border: none; border-radius: 6px; cursor: pointer; width: 100%; margin-top: 10px; }
        .btn-sell { background: #22c55e; color: black; }
        .btn-buy { background: #ef4444; color: white; }
        .back-btn { background: #3b82f6; color: white; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #444; padding: 8px; text-align: center; font-size: 14px; }
        th { background: #252525; color: #ffd700; }
    </style>
</head>
<body>
    <div class="admin-header">
        <h2 style="color: #ffd700; margin: 0;">👑 لوحة الإدارة العليا ({{ username }})</h2>
        <div>
            <a href="/create_user_page" class="back-btn" style="background: #10b981; margin-left: 10px;">➕ إنشاء حساب زبون جديد</a>
            <a href="/dashboard" class="back-btn">⬅️ العودة للرئيسية</a>
        </div>
    </div>

    <!-- خزنة المليون دولار -->
    <div class="vault-box">
        <h3 style="margin: 0; color: #a7f3d0; font-size: 18px;">🏦 رصيد الخزنة المركزية (الشركة)</h3>
        <div style="font-size: 42px; font-weight: bold; color: #fff; margin: 10px 0; text-shadow: 0 0 15px #34d399;">${{ vault_balance }}</div>
        <p style="margin: 0; font-size: 13px; color: #e2e8f0;">يتم البيع للزبائن والشراء منهم حصرياً عبر حسابات (admin1, admin2, admin3).</p>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <!-- نافذة البيع للزبائن -->
        <div class="panel-box">
            <h3 style="color: #22c55e; margin-top: 0;">⚡ بيع رصيد للزبون (من خزنة الشركة)</h3>
            <form method="POST">
                <input type="hidden" name="action" value="sell">
                <label>اختر الزبون:</label>
                <select name="target_user" required>
                    <option value="">اختر الزبون</option>
                    {% for u in users_list %}<option value="{{ u[0] }}">{{ u[0] }} (رصيده: ${{ u[1] }})</option>{% endfor %}
                </select>
                <label>المبلغ ($):</label>
                <input type="number" name="amount" placeholder="أدخل المبلغ" min="1" required>
                <button type="submit" class="btn-sell">إتمام عملية البيع للزبون</button>
            </form>
        </div>

        <!-- نافذة الشراء من الزبائن -->
        <div class="panel-box">
            <h3 style="color: #ef4444; margin-top: 0;">💸 شراء رصيد من الزبون (إلى خزنة الشركة)</h3>
            <form method="POST">
                <input type="hidden" name="action" value="buy_back">
                <label>اختر الزبون:</label>
                <select name="target_user" required>
                    <option value="">اختر الزبون</option>
                    {% for u in users_list %}<option value="{{ u[0] }}">{{ u[0] }} (رصيده: ${{ u[1] }})</option>{% endfor %}
                </select>
                <label>المبلغ ($):</label>
                <input type="number" name="amount" placeholder="أدخل المبلغ" min="1" required>
                <button type="submit" class="btn-buy">إتمام الشراء وإرجاع الرصيد للخزنة</button>
            </form>
        </div>
    </div>

    <!-- جدول إدارة وعرض كافة الحسابات والزبائن المسجلين -->
    <div class="panel-box" style="margin-top: 20px;">
        <h3 style="color: #ffd700; margin-top: 0;">👥 جدول كافة حسابات الزبائن المنشأة وأرصدتهم</h3>
        <table>
            <tr><th>اسم الزبون</th><th>الرصيد الحالي</th><th>أُنشئ بواسطة المدير</th></tr>
            {% if users_list %}
                {% for u in users_list %}
                <tr>
                    <td><b>{{ u[0] }}</b></td>
                    <td style="color: #34d399; font-weight: bold;">${{ u[1] }}</td>
                    <td>{{ u[2] }}</td>
                </tr>
                {% endfor %}
            {% else %}
                <tr><td colspan="3" style="color: #94a3b8;">لا توجد حسابات زبائن مسجلة حتى الآن! اضغط على "إنشاء حساب زبون جديد" بالأعلى.</td></tr>
            {% endif %}
        </table>
    </div>

    <!-- سجل العمليات المالية للمديرين -->
    <div class="panel-box" style="margin-top: 20px;">
        <h3 style="color: #38bdf8; margin-top: 0;">📋 سجل العمليات المالية الأخيرة</h3>
        <table>
            <tr><th>نوع العملية</th><th>المدير المسؤول</th><th>الزبون</th><th>المبلغ</th><th>التوقيت</th></tr>
            {% for log in logs %}
            <tr>
                <td><b>{{ log[0] }}</b></td>
                <td style="color: #ffd700;">{{ log[1] }}</td>
                <td>{{ log[2] }}</td>
                <td style="color: #34d399;">${{ log[3] }}</td>
                <td>{{ log[4] }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

CREATE_USER_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>إنشاء حساب زبون جديد - Lira</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .box { background: #1f1f1f; padding: 40px; border-radius: 12px; width: 350px; text-align: center; border: 1px solid #444; }
        input { width: 100%; padding: 12px; margin: 10px 0; border-radius: 6px; border: 1px solid #555; background: #252525; color: white; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #10b981; color: white; font-weight: bold; border: none; border-radius: 6px; cursor: pointer; margin-top: 10px; }
        .back-btn { background: #3b82f6; color: white; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold; display: inline-block; margin-top: 15px; }
        .msg { color: #34d399; font-weight: bold; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="box">
        <h2 style="color: #ffd700; margin-top: 0;">➕ إنشاء حساب زبون جديد</h2>
        {% if msg %}<div class="msg">{{ msg }}</div>{% endif %}
        <form method="POST">
            <input type="text" name="new_user" placeholder="اسم المستخدم (مثال: customer1)" required>
            <input type="password" name="new_pass" placeholder="كلمة المرور" required>
            <button type="submit">إنشاء الحساب</button>
        </form>
        <a href="/admin_panel" class="back-btn">⬅️ العودة لوحة الإدارة</a>
    </div>
</body>
</html>
"""

GAME_ONE_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><title>اللعبة الأولى</title></head>
<body style="background:#0b0f19; color:#fff; text-align:center; padding:50px;">
    <h1>👑 اللعبة الأولى قيد البرمجة</h1>
    <a href="/dashboard" style="color:#3b82f6;">⬅ العودة للرئيسية</a>
</body>
</html>
"""

GAME_TWO_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><title>اللعبة الثانية</title></head>
<body style="background:#0b0f19; color:#fff; text-align:center; padding:50px;">
    <h1>🎰 اللعبة الثانية قيد البرمجة</h1>
    <a href="/dashboard" style="color:#3b82f6;">⬅ العودة للرئيسية</a>
</body>
</html>
"""

LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>تسجيل الدخول - Lira</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-box { background: #1f1f1f; padding: 40px; border-radius: 12px; width: 320px; text-align: center; border: 1px solid #333; }
        input { width: 100%; padding: 12px; margin: 10px 0; border-radius: 6px; border: 1px solid #444; background: #252525; color: white; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #ffd700; color: black; font-weight: bold; border: none; border-radius: 6px; cursor: pointer; margin-top: 10px; }
        .error { color: #ef4444; margin-bottom: 12px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2 style="color: #ffd700; margin-top: 0;">👑 Lira | ليرة</h2>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="اسم المستخدم" required>
            <input type="password" name="password" placeholder="كلمة المرور" required>
            <button type="submit">دخول</button>
        </form>
    </div>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
