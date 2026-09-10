from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import sqlite3
import time

app = Flask(__name__)
app.secret_key = 'empire_lira_clean_2026'

def init_db():
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    
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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_vault (
            id INTEGER PRIMARY KEY,
            vault_balance REAL DEFAULT 1000000.0
        )
    ''')
    cursor.execute('SELECT COUNT(*) FROM system_vault')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO system_vault (id, vault_balance) VALUES (1, 1000000.0)')

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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS golden_number_bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            number INTEGER,
            draw_date TEXT
        )
    ''')

    main_admins = ['admin1', 'admin2', 'admin3']
    for adm in main_admins:
        cursor.execute("SELECT * FROM users WHERE username=?", (adm,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (username, password, balance, role, created_by) VALUES (?, ?, 100000.0, 'admin', 'system')", 
                           (adm, 'admin123'))
            cursor.execute("UPDATE system_vault SET vault_balance = vault_balance - 100000.0 WHERE id=1")

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

@app.route('/game_one_page', methods=['GET', 'POST'])
def game_one_page():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username, role = session['username'], session['role']
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    
    msg = None
    if request.method == 'POST':
        if 'book_number' in request.form:
            number = int(request.form.get('number'))
            cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
            bal = cursor.fetchone()[0]
            cost = 2.0
            if bal >= cost:
                cursor.execute("SELECT * FROM golden_number_bookings WHERE number=?", (number,))
                if not cursor.fetchone():
                    cursor.execute("UPDATE users SET balance = balance - ? WHERE username=?", (cost, username))
                    cursor.execute("INSERT INTO golden_number_bookings (username, number, draw_date) VALUES (?, ?, ?)", 
                                   (username, number, time.strftime('%Y-%m-%d')))
                    conn.commit()
                    msg = f"تم حجز الرقم {number} بنجاح مقابل ${cost}!"
                else:
                    msg = f"عذراً، الرقم {number} محجوز مسبقاً!"
            else:
                msg = "رصيدك غير كافٍ لحجز هذا الرقم!"

    cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
    balance = cursor.fetchone()[0]

    cursor.execute("SELECT number, username FROM golden_number_bookings")
    bookings = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute("SELECT number FROM golden_number_bookings WHERE username=?", (username,))
    my_bookings = [r[0] for r in cursor.fetchall()]
    my_spent = len(my_bookings) * 2.0

    conn.close()
    return render_template_string(GAME_ONE_PAGE, username=username, role=role, balance=balance, 
                                  bookings=bookings, my_bookings=my_bookings, my_spent=my_spent, msg=msg)

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
        cursor.execute("SELECT balance, role FROM users WHERE username=?", (target_user,))
        user_row = cursor.fetchone()

        if user_row and amount > 0:
            if action == 'sell' and vault_bal >= amount:
                cursor.execute("UPDATE system_vault SET vault_balance = vault_balance - ? WHERE id=1", (amount,))
                cursor.execute("UPDATE users SET balance = balance + ? WHERE username=?", (amount, target_user))
                cursor.execute("INSERT INTO financial_logs (action_type, admin_name, target_user, amount, log_time) VALUES ('بيع رصيد', ?, ?, ?, ?)", 
                               (current_admin, target_user, amount, time.strftime('%Y-%m-%d %H:%M')))
                conn.commit()
            elif action == 'buy_back' and user_row[0] >= amount:
                cursor.execute("UPDATE users SET balance = balance - ? WHERE username=?", (target_user, amount))
                cursor.execute("UPDATE system_vault SET vault_balance = vault_balance + ? WHERE id=1", (amount,))
                cursor.execute("INSERT INTO financial_logs (action_type, admin_name, target_user, amount, log_time) VALUES ('شراء رصيد', ?, ?, ?, ?)", 
                               (current_admin, target_user, amount, time.strftime('%Y-%m-%d %H:%M')))
                conn.commit()
        return redirect(url_for('admin_panel'))

    cursor.execute("SELECT vault_balance FROM system_vault WHERE id=1")
    vault_balance = cursor.fetchone()[0]
    cursor.execute("SELECT username, password, balance, role, created_by FROM users")
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
            msg = f"تم إنشاء حساب الزبون '{new_user}' بنجاح!"
        except sqlite3.IntegrityError:
            msg = "خطأ: اسم المستخدم موجود مسبقاً!"
        conn.close()
    return render_template_string(CREATE_USER_PAGE, msg=msg)

# قوالب HTML و CSS المعدلة بدون أي أنظمة سحب
DASHBOARD_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Lira ليرة - لوحة التحكم</title>
    <link rel="manifest" href="/manifest.json">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
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
        .icon-card { background: linear-gradient(145deg, #1f1f1f, #121212); border: 2px solid #b8860b; border-radius: 16px; padding: 25px; text-align: center; cursor: pointer; transition: all 0.3s ease; display: flex; flex-direction: column; align-items: center; justify-content: center; text-decoration: none; }
        .icon-card:hover { border-color: #ffd700; transform: translateY(-5px); }
        .icon-logo { font-size: 55px; margin-bottom: 12px; }
        .icon-title { color: #ffd700; font-size: 16px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo-area">
            <div class="logo-badge">👑</div>
            <h1>Lira | ليرة</h1>
            <div class="user-creds">👤 <b>{{ username }}</b> {% if role == 'admin' %} | 🔑 <b>مدير النظام</b>{% endif %}</div>
            <div class="balance-badge">الرصيد: <span>${{ balance }}</span></div>
        </div>
        <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
            <a class="whatsapp-btn" href="https://wa.me/96176030208?text=شحن%20رصيد%20بمنصة%20Lira%20باسم:%20{{ username }}" target="_blank">💬 شراء رصيد</a>
            {% if role == 'admin' %}<a href="/admin_panel" class="admin-link-btn">👑 لوحة الإدارة</a>{% endif %}
            <a href="/logout" class="logout-btn">🚪 خروج</a>
        </div>
    </div>
    <div class="icons-grid">
        <a href="/game_one_page" class="icon-card">
            <div class="icon-logo">🏆</div>
            <div class="icon-title">لوحة الحجوزات (الرقم الذهبي)</div>
        </a>
        <a href="/game_two_page" class="icon-card">
            <div class="icon-logo">🎰</div>
            <div class="icon-title">اللعبة الثانية</div>
        </a>
    </div>
</body>
</html>
"""

GAME_ONE_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>لوحة الحجوزات - Lira</title>
    <link rel="manifest" href="/manifest.json">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 12px; border-bottom: 2px solid #ffd700; flex-wrap: wrap; gap: 10px; }
        .board-container { background: #120e06; border: 4px solid #b8860b; padding: 20px; border-radius: 16px; margin-top: 25px; text-align: center; }
        .board-grid { display: grid; grid-template-columns: repeat(10, 1fr); gap: 10px; margin-top: 20px; }
        @media(max-width: 768px) { .board-grid { grid-template-columns: repeat(5, 1fr); } }
        .number-box { background: #000; border: 3px solid #ffd700; border-radius: 8px; height: 55px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 20px; font-weight: bold; color: #ffffff; cursor: pointer; transition: 0.3s; }
        .number-box:hover { background: #1a1500; transform: scale(1.05); }
        .number-box.booked { background: #3b0000; border-color: #ef4444; color: #f87171; cursor: not-allowed; }
        .back-btn { background: #3b82f6; color: white; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold; }
        .my-stats { background: #162032; border: 1px solid #38bdf8; padding: 15px; border-radius: 10px; margin-top: 25px; }
    </style>
</head>
<body>
    <div class="header">
        <h2 style="color: #ffd700; margin: 0;">👑 لوحة الحجوزات الرقمية</h2>
        <div style="display: flex; gap: 15px; align-items: center;">
            <div style="color: #34d399; font-weight: bold;">الرصيد: ${{ balance }}</div>
            <a href="/dashboard" class="back-btn">⬅️ الرئيسية</a>
        </div>
    </div>

    {% if msg %}<div style="background: #065f46; color: #34d399; padding: 12px; border-radius: 8px; margin-top: 15px; text-align: center; font-weight: bold;">{{ msg }}</div>{% endif %}

    <div class="board-container">
        <h3 style="color: #ffd700; margin-top: 0;">🎯 اختر وحجز الأرقام (تكلفة الحجز: $2 للرقم)</h3>
        <div class="board-grid">
            {% for i in range(1, 51) %}
                {% if i in bookings %}
                    <div id="box-{{ i }}" class="number-box booked">
                        {{ i }}<br><span style="font-size: 10px; color: #f87171;">({{ bookings[i] }})</span>
                    </div>
                {% else %}
                    <form method="POST" style="margin: 0;">
                        <input type="hidden" name="number" value="{{ i }}">
                        <button type="submit" name="book_number" id="box-{{ i }}" class="number-box" style="width: 100%;" title="اضغط للحجز بـ $2">{{ i }}</button>
                    </form>
                {% endif %}
            {% endfor %}
        </div>
    </div>

    <div class="my-stats">
        <h3 style="color: #38bdf8; margin-top: 0;">👤 ملخص حسابك</h3>
        <p>الأرقام التي قمت بحجزها: <b style="color: #ffd700;">{% if my_bookings %}{{ my_bookings | join(', ') }}{% else %}لا توجد أرقام محجوزة{% endif %}</b></p>
        <p>إجمالي التكلفة المدفوعة للحجوزات: <b style="color: #ef4444;">${{ my_spent }}</b></p>
    </div>
</body>
</html>
"""

ADMIN_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة إدارة المديرين - Lira</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; padding: 20px; }
        .admin-header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 12px; border: 2px solid #ffd700; margin-bottom: 25px; flex-wrap: wrap; gap: 10px; }
        .vault-box { background: linear-gradient(135deg, #065f46, #047857); border: 3px solid #34d399; padding: 25px; border-radius: 16px; text-align: center; margin-bottom: 25px; }
        .panel-box { background: #1f1f1f; padding: 20px; border-radius: 12px; border: 1px solid #444; margin-bottom: 20px; }
        input, select { width: 100%; padding: 10px; margin: 8px 0; border-radius: 6px; background: #252525; color: white; border: 1px solid #555; box-sizing: border-box; }
        button { padding: 10px 20px; font-weight: bold; border: none; border-radius: 6px; cursor: pointer; width: 100%; margin-top: 10px; }
        .btn-sell { background: #22c55e; color: black; }
        .btn-buy { background: #ef4444; color: white; }
        .back-btn { background: #3b82f6; color: white; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; overflow-x: auto; display: block; }
        th, td { border: 1px solid #444; padding: 8px; text-align: center; font-size: 14px; }
        th { background: #252525; color: #ffd700; }
    </style>
</head>
<body>
    <div class="admin-header">
        <h2 style="color: #ffd700; margin: 0;">👑 لوحة الإدارة ({{ username }})</h2>
        <div>
            <a href="/create_user_page" class="back-btn" style="background: #10b981; margin-left: 10px;">➕ زبون جديد</a>
            <a href="/dashboard" class="back-btn">⬅️ الرئيسية</a>
        </div>
    </div>
    <div class="vault-box">
        <h3 style="margin: 0; color: #a7f3d0;">🏦 رصيد الخزنة المركزية</h3>
        <div style="font-size: 42px; font-weight: bold; color: #fff; margin: 10px 0;">${{ vault_balance }}</div>
    </div>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; @media(max-width:768px){grid-template-columns:1fr;}">
        <div class="panel-box">
            <h3 style="color: #22c55e; margin-top: 0;">⚡ بيع رصيد</h3>
            <form method="POST">
                <input type="hidden" name="action" value="sell">
                <select name="target_user" required>
                    <option value="">اختر الحساب</option>
                    {% for u in users_list %}<option value="{{ u[0] }}">{{ u[0] }} ({{ u[3] }}) - رصيده: ${{ u[2] }}</option>{% endfor %}
                </select>
                <input type="number" name="amount" placeholder="المبلغ ($)" min="1" required>
                <button type="submit" class="btn-sell">إتمام البيع</button>
            </form>
        </div>
        <div class="panel-box">
            <h3 style="color: #ef4444; margin-top: 0;">💸 شراء رصيد للخزنة</h3>
            <form method="POST">
                <input type="hidden" name="action" value="buy_back">
                <select name="target_user" required>
                    <option value="">اختر الحساب</option>
                    {% for u in users_list %}<option value="{{ u[0] }}">{{ u[0] }} ({{ u[3] }}) - رصيده: ${{ u[2] }}</option>{% endfor %}
                </select>
                <input type="number" name="amount" placeholder="المبلغ ($)" min="1" required>
                <button type="submit" class="btn-buy">إتمام الشراء</button>
            </form>
        </div>
    </div>
    <div class="panel-box" style="margin-top: 20px;">
        <h3 style="color: #ffd700; margin-top: 0;">👥 الحسابات المسجلة</h3>
        <table>
            <tr><th>المستخدم</th><th>الكلمة</th><th>النوع</th><th>الرصيد</th><th>المُنشئ</th></tr>
            {% for u in users_list %}
            <tr><td><b>{{ u[0] }}</b></td><td>{{ u[1] }}</td><td>{{ u[3] }}</td><td style="color:#34d399;">${{ u[2] }}</td><td>{{ u[4] }}</td></tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

CREATE_USER_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><title>إنشاء زبون - Lira</title>
<style>
body { font-family: Tahoma; background: #0b0f19; color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
.box { background: #1f1f1f; padding: 30px; border-radius: 12px; width: 320px; text-align: center; border: 1px solid #444; }
input { width: 100%; padding: 12px; margin: 10px 0; border-radius: 6px; background: #252525; color: white; border: 1px solid #555; box-sizing: border-box; }
button { width: 100%; padding: 12px; background: #10b981; color: white; font-weight: bold; border: none; border-radius: 6px; cursor: pointer; }
</style>
</head>
<body>
<div class="box">
    <h2 style="color: #ffd700;">➕ إنشاء زبون جديد</h2>
    {% if msg %}<div style="color: #34d399; margin-bottom:10px;">{{ msg }}</div>{% endif %}
    <form method="POST">
        <input type="text" name="new_user" placeholder="اسم المستخدم" required>
        <input type="text" name="new_pass" placeholder="كلمة المرور" required>
        <button type="submit">إنشاء الحساب</button>
    </form>
    <a href="/admin_panel" style="color: #3b82f6; display:inline-block; margin-top:15px; text-decoration:none;">⬅️ العودة</a>
</div>
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
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تسجيل الدخول - Lira</title>
    <link rel="manifest" href="/manifest.json">
    <style>
        body { font-family: Tahoma; background-color: #0b0f19; color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
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
