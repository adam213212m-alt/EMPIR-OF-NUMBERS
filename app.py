from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import sqlite3
import random
import time

app = Flask(__name__)
app.secret_key = 'lira_empire_secure_2026_key'

def init_db():
    conn = sqlite3.connect('lira_enterprise.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # جدول المستخدمين
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

    # خزنة الشركة الأساسية
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_vault (
            id INTEGER PRIMARY KEY,
            vault_balance REAL DEFAULT 1000000.0
        )
    ''')
    cursor.execute('SELECT COUNT(*) FROM system_vault')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO system_vault (id, vault_balance) VALUES (1, 1000000.0)')

    # جدول السجلات المالية والمحاسبة
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

    # جدول حجوزات لعبة الرقم الذهبي
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS golden_number_bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            number INTEGER,
            booking_date TEXT
        )
    ''')

    # جدول حالة سحب الرقم الذهبي (تم إضافة forced_winning_number)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_draw_state (
            id INTEGER PRIMARY KEY,
            winning_number INTEGER DEFAULT 0,
            status TEXT DEFAULT 'idle',
            draw_end_time REAL DEFAULT 0,
            forced_winning_number INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('SELECT COUNT(*) FROM game_draw_state')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO game_draw_state (id, winning_number, status, draw_end_time, forced_winning_number) VALUES (1, 0, "idle", 0, 0)')

    # إنشاء حساب المؤسس الرئيسي admin1 افتراضياً
    cursor.execute("SELECT * FROM users WHERE username='admin1'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, balance, role, created_by) VALUES ('admin1', 'admin123', 50000.0, 'admin', 'system')", ())
        cursor.execute("UPDATE system_vault SET vault_balance = vault_balance - 50000.0 WHERE id=1")

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
        conn = sqlite3.connect('lira_enterprise.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session.clear()
            session['username'] = user[1]
            session['balance'] = user[3]
            session['role'] = user[4]
            return redirect(url_for('dashboard'))
        else:
            error = "خطأ في اسم المستخدم أو كلمة المرور!"
    return render_template_string(LOGIN_PAGE, error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('lira_enterprise.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT balance, role FROM users WHERE username=?", (session['username'],))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return redirect(url_for('logout'))
    balance, role = row[0], row[1]
    return render_template_string(DASHBOARD_PAGE, username=session['username'], role=role, balance=balance)

@app.route('/api/golden_status')
def api_golden_status():
    conn = sqlite3.connect('lira_enterprise.db', check_same_thread=False)
    cursor = conn.cursor()
    current_time = time.time()
    cursor.execute("SELECT winning_number, status, draw_end_time FROM game_draw_state WHERE id=1")
    row = cursor.fetchone()
    
    if row:
        winning_number, status, end_time = row[0], row[1], row[2]
        if status == 'finished' and current_time >= end_time:
            cursor.execute("DELETE FROM golden_number_bookings")
            cursor.execute("UPDATE game_draw_state SET winning_number=0, status='idle', draw_end_time=0 WHERE id=1")
            conn.commit()
            status = 'idle'
            winning_number = 0

        remaining = int(end_time - current_time) if status == 'finished' else 0
        if remaining < 0: remaining = 0
    else:
        winning_number, status, remaining = 0, 'idle', 0

    cursor.execute("SELECT number, username FROM golden_number_bookings")
    bookings = {r[0]: r[1] for r in cursor.fetchall()}
    conn.close()

    return jsonify({
        "status": status,
        "winning_number": winning_number,
        "remaining_seconds": remaining,
        "bookings": bookings
    })

@app.route('/game_golden_number', methods=['GET', 'POST'])
def game_golden_number():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username, role = session['username'], session['role']
    conn = sqlite3.connect('lira_enterprise.db', check_same_thread=False)
    cursor = conn.cursor()
    
    msg = None
    if request.method == 'POST':
        # حجز رقم
        if 'book_number' in request.form:
            cursor.execute("SELECT status FROM game_draw_state WHERE id=1")
            if cursor.fetchone()[0] == 'idle':
                number = int(request.form.get('number'))
                cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
                bal = cursor.fetchone()[0]
                cost = 2.0
                if bal >= cost:
                    cursor.execute("SELECT * FROM golden_number_bookings WHERE number=?", (number,))
                    if not cursor.fetchone():
                        cursor.execute("UPDATE users SET balance = balance - ? WHERE username=?", (cost, username))
                        cursor.execute("INSERT INTO golden_number_bookings (username, number, booking_date) VALUES (?, ?, ?)", 
                                       (username, number, time.strftime('%Y-%m-%d')))
                        conn.commit()
                        msg = f"تم حجز الرقم {number} بنجاح مقابل 2$!"
                    else:
                        msg = f"عذراً، الرقم {number} محجوز مسبقاً!"
                else:
                    msg = "رصيدك غير كافٍ (التكلفة 2$)!"
            else:
                msg = "عذراً، جاري السحب حالياً!"

        # إلغاء حجز رقم (اللاعب نفسه أو admin1)
        elif 'cancel_number' in request.form:
            cursor.execute("SELECT status FROM game_draw_state WHERE id=1")
            if cursor.fetchone()[0] == 'idle':
                number = int(request.form.get('number'))
                cursor.execute("SELECT username FROM golden_number_bookings WHERE number=?", (number,))
                b_row = cursor.fetchone()
                if b_row and (b_row[0] == username or username == 'admin1'):
                    owner = b_row[0]
                    cursor.execute("DELETE FROM golden_number_bookings WHERE number=?", (number,))
                    # إعادة تكلفة الحجز (2$) لرصيد صاحب الحجز
                    cursor.execute("UPDATE users SET balance = balance + 2.0 WHERE username=?", (owner,))
                    conn.commit()
                    msg = f"تم التراجع عن حجز الرقم {number} وإعادة 2$ لحساب {owner}!"
                else:
                    msg = "لا يمكنك التراجع عن هذا الرقم!"
            else:
                msg = "لا يمكن التراجع أثناء عملية السحب!"

        # أمر السحب (بدء القرعة التي تستغرق 10 ثوانٍ)
        elif 'admin_execute_draw' in request.form and username == 'admin1':
            cursor.execute("SELECT number FROM golden_number_bookings")
            booked_list = [r[0] for r in cursor.fetchall()]
            if booked_list:
                cursor.execute("SELECT forced_winning_number FROM game_draw_state WHERE id=1")
                forced_num = cursor.fetchone()[0]

                if forced_num and forced_num in booked_list:
                    winning_num = forced_num
                else:
                    winning_num = random.choice(booked_list)
                
                cursor.execute("SELECT username FROM golden_number_bookings WHERE number=?", (winning_num,))
                winner_user = cursor.fetchone()[0]
                
                cursor.execute("UPDATE users SET balance = balance + 75.0 WHERE username=?", (winner_user,))
                cursor.execute("INSERT INTO financial_logs (action_type, admin_name, target_user, amount, log_time) VALUES ('جائزة الرقم الذهبي', 'admin1', ?, 75.0, ?)", 
                               (winner_user, time.strftime('%Y-%m-%d %H:%M')))
                
                # وقت انتهاء السحب بعد 10 ثوانٍ
                draw_duration = 10.0
                end_time = time.time() + draw_duration + 5 # 10 ثواني السحب + 5 ثواني إضاءة النتيجة
                cursor.execute("UPDATE game_draw_state SET winning_number=?, status='drawing', draw_end_time=? WHERE id=1", (winning_num, end_time))
                conn.commit()
                msg = f"بدأت قرعة الرقم الذهبي السريعة!"
            else:
                msg = "لا توجد أرقام محجوزة لإجراء السحب عليها حالياً!"

    cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
    balance = cursor.fetchone()[0]
    cursor.execute("SELECT number, username FROM golden_number_bookings")
    bookings = {r[0]: r[1] for r in cursor.fetchall()}
    cursor.execute("SELECT winning_number, status, forced_winning_number FROM game_draw_state WHERE id=1")
    draw_row = cursor.fetchone()
    winning_number, draw_status, forced_num = draw_row[0], draw_row[1], draw_row[2]

    # جلب إحصائيات اللاعب الحالية (الأرقام المحجوزة والمبلغ المصروف)
    cursor.execute("SELECT number FROM golden_number_bookings WHERE username=?", (username,))
    my_booked_nums = [r[0] for r in cursor.fetchall()]
    my_total_spent = len(my_booked_nums) * 2.0

    conn.close()
    return render_template_string(GAME_GOLDEN_PAGE, username=username, role=role, balance=balance, 
                                  bookings=bookings, winning_number=winning_number, draw_status=draw_status, 
                                  forced_num=forced_num, my_booked_nums=my_booked_nums, my_total_spent=my_total_spent, msg=msg)

@app.route('/admin_customers', methods=['GET', 'POST'])
def admin_customers():
    if 'username' not in session or session.get('username') != 'admin1':
        return redirect(url_for('dashboard'))
    
    conn = sqlite3.connect('lira_enterprise.db', check_same_thread=False)
    cursor = conn.cursor()
    msg = None

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'create_user':
            new_u = request.form.get('new_username', '').strip()
            new_p = request.form.get('new_password', '').strip()
            try:
                cursor.execute("INSERT INTO users (username, password, balance, role, created_by) VALUES (?, ?, 0, 'player', 'admin1')", (new_u, new_p))
                conn.commit()
                msg = f"تم إنشاء الحساب '{new_u}' بنجاح!"
            except sqlite3.IntegrityError:
                msg = "اسم المستخدم موجود مسبقاً!"

        elif action == 'sell_currency':
            target = request.form.get('target_user')
            amount = float(request.form.get('amount', 0))
            cursor.execute("SELECT vault_balance FROM system_vault WHERE id=1")
            vault_bal = cursor.fetchone()[0]
            if vault_bal >= amount and amount > 0:
                cursor.execute("UPDATE system_vault SET vault_balance = vault_balance - ? WHERE id=1", (amount,))
                cursor.execute("UPDATE users SET balance = balance + ? WHERE username=?", (amount, target))
                cursor.execute("INSERT INTO financial_logs (action_type, admin_name, target_user, amount, log_time) VALUES ('بيع عملات للزبون', 'admin1', ?, ?, ?)", 
                               (target, amount, time.strftime('%Y-%m-%d %H:%M')))
                conn.commit()
                msg = f"تم بيع رصيد بقيمة ${amount} للحساب {target} بنجاح!"
            else:
                msg = "رصيد الخزنة غير كافٍ أو المبلغ غير صالح!"

        elif action == 'buy_back_currency':
            target = request.form.get('target_user')
            amount = float(request.form.get('amount', 0))
            cursor.execute("SELECT balance FROM users WHERE username=?", (target,))
            user_bal = cursor.fetchone()
            if user_bal and user_bal[0] >= amount and amount > 0:
                cursor.execute("UPDATE users SET balance = balance - ? WHERE username=?", (amount, target))
                cursor.execute("UPDATE system_vault SET vault_balance = vault_balance + ? WHERE id=1", (amount,))
                cursor.execute("INSERT INTO financial_logs (action_type, admin_name, target_user, amount, log_time) VALUES ('شراء وإعادة للخزنة', 'admin1', ?, ?, ?)", 
                               (target, amount, time.strftime('%Y-%m-%d %H:%M')))
                conn.commit()
                msg = f"تم استرجاع رصيد بقيمة ${amount} من الحساب {target} إلى الخزنة بنجاح!"
            else:
                msg = "رصيد الزبون غير كافٍ أو المبلغ غير صالح!"

    cursor.execute("SELECT vault_balance FROM system_vault WHERE id=1")
    vault_balance = cursor.fetchone()[0]
    cursor.execute("SELECT username, password, balance, role FROM users")
    users_list = cursor.fetchall()
    conn.close()

    return render_template_string(ADMIN_CUSTOMERS_PAGE, vault_balance=vault_balance, users_list=users_list, msg=msg)

@app.route('/admin_games', methods=['GET', 'POST'])
def admin_games():
    if 'username' not in session or session.get('username') != 'admin1':
        return redirect(url_for('dashboard'))
    
    conn = sqlite3.connect('lira_enterprise.db', check_same_thread=False)
    cursor = conn.cursor()
    msg = None

    if request.method == 'POST':
        forced_num = request.form.get('forced_winning_number', '').strip()
        f_val = int(forced_num) if forced_num.isdigit() else 0
        cursor.execute("UPDATE game_draw_state SET forced_winning_number=? WHERE id=1", (f_val,))
        conn.commit()
        msg = f"تم تحديث الرقم المسبق للسحب إلى: {f_val if f_val > 0 else 'عشوائي'}"

    cursor.execute("SELECT forced_winning_number FROM game_draw_state WHERE id=1")
    forced_val = cursor.fetchone()[0]
    conn.close()

    return render_template_string(ADMIN_GAMES_PAGE, forced_val=forced_val, msg=msg)

@app.route('/admin_accounting')
def admin_accounting():
    if 'username' not in session or session.get('username') != 'admin1':
        return redirect(url_for('dashboard'))
    
    conn = sqlite3.connect('lira_enterprise.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT vault_balance FROM system_vault WHERE id=1")
    vault_balance = cursor.fetchone()[0]
    
    cursor.execute("SELECT action_type, admin_name, target_user, amount, log_time FROM financial_logs ORDER BY id DESC")
    logs = cursor.fetchall()
    
    cursor.execute("SELECT SUM(amount) FROM financial_logs WHERE action_type='بيع عملات للزبون'")
    sales_res = cursor.fetchone()[0]
    total_sales = sales_res if sales_res else 0.0

    cursor.execute("SELECT SUM(amount) FROM financial_logs WHERE action_type='جائزة الرقم الذهبي'")
    payout_res = cursor.fetchone()[0]
    total_payouts = payout_res if payout_res else 0.0

    net_profits = total_sales - total_payouts
    conn.close()

    return render_template_string(ADMIN_ACCOUNTING_PAGE, vault_balance=vault_balance, logs=logs, total_sales=total_sales, total_payouts=total_payouts, net_profits=net_profits)


# قوالب صفحات الـ HTML المحدثة

LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تسجيل الدخول - Lira ليرة</title>
    <link rel="manifest" href="/manifest.json">
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-box { background: linear-gradient(145deg, #1f1f1f, #121212); padding: 45px; border-radius: 20px; width: 360px; text-align: center; border: 3px solid #ffd700; box-shadow: 0 0 35px rgba(255,215,0,0.3); }
        .logo-title { font-size: 42px; font-weight: bold; color: #ffd700; text-shadow: 0 0 15px rgba(255,215,0,0.6); margin-bottom: 5px; }
        .logo-sub { font-size: 14px; color: #94a3b8; margin-bottom: 25px; }
        input { width: 100%; padding: 14px; margin: 10px 0; border-radius: 8px; border: 1px solid #444; background: #252525; color: white; box-sizing: border-box; font-size: 16px; }
        button { width: 100%; padding: 14px; background: linear-gradient(135deg, #ffd700, #b8860b); color: black; font-weight: bold; border: none; border-radius: 8px; cursor: pointer; margin-top: 15px; font-size: 18px; box-shadow: 0 4px 15px rgba(255,215,0,0.4); }
        .error { color: #ef4444; margin-bottom: 12px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="login-box">
        <div class="logo-title">👑 Lira</div>
        <div class="logo-sub">ليرة - المنصة التفاعلية الكبرى</div>
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

DASHBOARD_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lira ليرة - لوحة التحكم الرئيسية</title>
    <link rel="manifest" href="/manifest.json">
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 14px; box-shadow: 0 4px 15px rgba(0,0,0,0.6); flex-wrap: wrap; gap: 12px; border-bottom: 3px solid #ffd700; }
        .logo-area { display: flex; align-items: center; gap: 15px; flex-wrap: wrap; }
        .logo-badge { background: linear-gradient(135deg, #ffd700, #b8860b); color: #000; width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 26px; font-weight: bold; }
        .logo-area h1 { margin: 0; color: #ffd700; font-size: 26px; font-weight: bold; }
        .user-creds { background: #1f1f1f; padding: 8px 14px; border-radius: 8px; font-size: 14px; color: #cbd5e1; border: 1px dashed #ffd700; }
        .balance-badge { background: #065f46; color: #34d399; padding: 8px 15px; border-radius: 8px; font-weight: bold; font-size: 18px; border: 1px solid #10b981; }
        
        .nav-buttons { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
        .whatsapp-btn { background: #25d366; color: white; padding: 8px 15px; text-decoration: none; border-radius: 8px; font-weight: bold; }
        .logout-btn { background: #ef4444; color: white; padding: 8px 15px; text-decoration: none; border-radius: 8px; font-weight: bold; border: none; }
        .admin-link { background: #ffd700; color: black; padding: 8px 12px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 13px; }

        .icons-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 35px; }
        @media (max-width: 900px) { .icons-grid { grid-template-columns: repeat(2, 1fr); } }
        @media (max-width: 500px) { .icons-grid { grid-template-columns: 1fr; } }
        
        .icon-card { background: linear-gradient(145deg, #1f1f1f, #121212); border: 2px solid #b8860b; border-radius: 16px; padding: 30px; text-align: center; cursor: pointer; transition: all 0.3s ease; box-shadow: 0 4px 20px rgba(0,0,0,0.6); display: flex; flex-direction: column; align-items: center; justify-content: center; text-decoration: none; aspect-ratio: 1; }
        .icon-card:hover { border-color: #ffd700; transform: translateY(-5px); box-shadow: 0 8px 30px rgba(255,215,0,0.4); }
        .icon-logo { font-size: 60px; margin-bottom: 15px; filter: drop-shadow(0 0 10px rgba(255,215,0,0.6)); }
        .icon-title { color: #ffd700; font-size: 18px; font-weight: bold; text-shadow: 0 2px 4px rgba(0,0,0,0.8); }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo-area">
            <div class="logo-badge">👑</div>
            <h1>Lira | ليرة</h1>
            <div class="user-creds">👤 <b>{{ username }}</b></div>
            <div class="balance-badge">الرصيد: <span>${{ balance }}</span></div>
        </div>
        <div class="nav-buttons">
            <a class="whatsapp-btn" href="https://wa.me/96176030208?text=اريد%20شحن%20رصيد" target="_blank">💬 شحن رصيد (واتساب)</a>
            
            {% if username == 'admin1' %}
                <a href="/admin_customers" class="admin-link">👥 إدارة الزبائن والخزنة</a>
                <a href="/admin_games" class="admin-link">🎮 لوحة الألعاب</a>
                <a href="/admin_accounting" class="admin-link">📊 برنامج المحاسبة</a>
            {% endif %}
            
            <a href="/logout" class="logout-btn">🚪 تسجيل خروج</a>
        </div>
    </div>

    <div class="icons-grid">
        <a href="/game_golden_number" class="icon-card">
            <div class="icon-logo">🏆</div>
            <div class="icon-title">الرقم الذهبي</div>
        </a>
        <div class="icon-card" onclick="alert('اللعبة الثانية قيد التفعيل')">
            <div class="icon-logo">🎰</div>
            <div class="icon-title">روليت الحظ</div>
        </div>
        <div class="icon-card" onclick="alert('اللعبة الثالثة قيد التفعيل')">
            <div class="icon-logo">⚡</div>
            <div class="icon-title">التحدي السريع</div>
        </div>
        <div class="icon-card" onclick="alert('اللعبة الرابعة قيد التفعيل')">
            <div class="icon-logo">🏇</div>
            <div class="icon-title">سباق الخيل</div>
        </div>
        <div class="icon-card" onclick="alert('اللعبة الخامسة قيد التفعيل')">
            <div class="icon-logo">🎡</div>
            <div class="icon-title">عجلة الثروة</div>
        </div>
        <div class="icon-card" onclick="alert('اللعبة السادسة قيد التفعيل')">
            <div class="icon-logo">🎁</div>
            <div class="icon-title">الصناديق الذهبية</div>
        </div>
        <div class="icon-card" onclick="alert('اللعبة السابعة قيد التفعيل')">
            <div class="icon-logo">🔢</div>
            <div class="icon-title">تحدي الأرقام</div>
        </div>
        <div class="icon-card" onclick="alert('اللعبة الثامنة قيد التفعيل')">
            <div class="icon-logo">🃏</div>
            <div class="icon-title">البوكر الملكي</div>
        </div>
        <div class="icon-card" onclick="alert('اللعبة التاسعة قيد التفعيل')">
            <div class="icon-logo">💎</div>
            <div class="icon-title">المجوهرات الكبرى</div>
        </div>
    </div>
</body>
</html>
"""

GAME_GOLDEN_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لعبة الرقم الذهبي - Lira</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 12px; border-bottom: 2px solid #ffd700; flex-wrap: wrap; gap: 10px; }
        
        .user-stats-box { background: #18181b; border: 2px dashed #b8860b; padding: 15px; border-radius: 14px; margin-top: 20px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px; }

        .board-container { background: linear-gradient(135deg, #110d06, #000000); border: 5px solid #b8860b; padding: 25px; border-radius: 18px; margin-top: 20px; box-shadow: 0 0 35px rgba(184,134,11,0.4); text-align: center; }
        .board-grid { display: grid; grid-template-columns: repeat(10, 1fr); gap: 12px; margin-top: 20px; }
        @media(max-width: 768px) { .board-grid { grid-template-columns: repeat(5, 1fr); } }
        
        .number-box { background: #3d2314; border: 2px solid #8b5a2b; border-radius: 10px; height: 60px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 20px; font-weight: bold; color: #ffffff; cursor: pointer; transition: 0.3s; text-shadow: 0 2px 4px rgba(0,0,0,0.9); box-shadow: inset 0 2px 5px rgba(255,255,255,0.2), 0 4px 6px rgba(0,0,0,0.5); }
        .number-box:hover { background: #5c351e; transform: scale(1.06); }
        .number-box.booked { background: #7f1d1d !important; border-color: #ef4444 !important; color: #fca5a5 !important; }
        .number-box.my-booked { background: #1e3a8a !important; border-color: #3b82f6 !important; color: #93c5fd !important; }
        .number-box.winning { background: linear-gradient(135deg, #ffd700, #ff8c00) !important; color: #000 !important; border-color: #fff !important; transform: scale(1.2); box-shadow: 0 0 50px #ffd700; animation: pulse 0.5s infinite alternate; }
        @keyframes pulse { from { transform: scale(1); } to { transform: scale(1.22); } }

        .draw-panel { background: #18181b; border: 3px solid #ffd700; padding: 25px; border-radius: 16px; margin-top: 25px; text-align: center; box-shadow: 0 0 30px rgba(255,215,0,0.2); }
        .big-slot-screen { background: radial-gradient(circle, #3d2c00 0%, #000000 100%); border: 4px solid #ffd700; color: #ffd700; font-size: 70px; font-weight: bold; padding: 15px; width: 240px; margin: 15px auto; border-radius: 20px; box-shadow: 0 0 30px rgba(255,215,0,0.6); letter-spacing: 5px; }
        
        .win-badge { background: linear-gradient(135deg, #ffd700, #b8860b); color: #000; border: 3px solid #fff; padding: 20px; border-radius: 15px; margin: 20px auto; width: 90%; max-width: 500px; text-align: center; font-size: 24px; font-weight: bold; box-shadow: 0 0 40px rgba(255,215,0,0.8); }
        .back-btn { background: #3b82f6; color: white; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h2 style="color: #ffd700; margin: 0;">🏆 الرقم الذهبي (من 1 إلى 50)</h2>
        <div style="display: flex; gap: 15px; align-items: center;">
            <div style="color: #34d399; font-weight: bold; font-size: 18px;">الرصيد: ${{ balance }}</div>
            <a href="/dashboard" class="back-btn">⬅️ لوحة التحكم</a>
        </div>
    </div>

    {% if msg %}<div style="background: #065f46; color: #34d399; padding: 12px; border-radius: 8px; margin-top: 15px; text-align: center; font-weight: bold;">{{ msg }}</div>{% endif %}

    <!-- خانة ملخص حساب اللاعب (الأرقام المحجوزة والمبلغ المصروف) -->
    <div class="user-stats-box">
        <div>
            <b style="color: #ffd700;">👤 ملفك الشخصي في اللعبة:</b> <span style="color: #cbd5e1;">{{ username }}</span>
        </div>
        <div>
            <b style="color: #38bdf8;">أرقامك المحجوزة:</b> 
            <span style="color: #fff; font-family: monospace; background: #000; padding: 4px 8px; border-radius: 4px;">
                {% if my_booked_nums %}{{ my_booked_nums | join(', ') }}{% else %}لا توجد أرقام محجوزة{% endif %}
            </span>
        </div>
        <div>
            <b style="color: #34d399;">المبلغ المصروف:</b> <span style="color: #34d399; font-weight: bold;">${{ my_total_spent }}</span>
        </div>
    </div>

    <div class="board-container">
        <h3 style="color: #ffd700; margin-top: 0;">🎯 اختر أرقامك الحظ (تكلفة الحجز: 2$ | الجائزة الكبرى: 75$)</h3>
        <p style="font-size: 13px; color: #94a3b8;">ملاحظة: يمكنك الضغط على أي رقم حجزته لتتراجع عنه وتسترد أموالك فوراً!</p>
        
        <div class="board-grid">
            {% for i in range(1, 51) %}
                {% if i in bookings %}
                    {% if bookings[i] == username or username == 'admin1' %}
                        <!-- يمكنه التراجع لأنه حجزه أو أنه الـ admin1 -->
                        <form method="POST" style="margin: 0;">
                            <input type="hidden" name="number" value="{{ i }}">
                            <button type="submit" name="cancel_number" id="box-{{ i }}" class="number-box {% if bookings[i] == username %}my-booked{% else %}booked{% endif %}" style="width: 100%; height: 60px;" title="اضغط للتراجع واسترداد 2$">
                                {{ i }}<br><span style="font-size: 9px;">({{ bookings[i] }}) ❌</span>
                            </button>
                        </form>
                    {% else %}
                        <div id="box-{{ i }}" class="number-box booked">
                            {{ i }}<br><span style="font-size: 9px; color: #fca5a5;">({{ bookings[i] }})</span>
                        </div>
                    {% endif %}
                {% else %}
                    <form method="POST" style="margin: 0;">
                        <input type="hidden" name="number" value="{{ i }}">
                        <button type="submit" name="book_number" id="box-{{ i }}" class="number-box" style="width: 100%; height: 60px;" title="اضغط للحجز بـ 2$">
                            {{ i }}
                        </button>
                    </form>
                {% endif %}
            {% endfor %}
        </div>
    </div>

    <div class="draw-panel">
        <h3 style="color: #ffd700; margin-top: 0;">🎰 شاشة السحب والقرعة المباشرة</h3>
        <p id="statusText" style="color: #cbd5e1; font-size: 16px;">
            {% if draw_status == 'finished' %}🎉 تم إعلان الفائز بالرقم الذهبي!
            {% elif draw_status == 'drawing' %}⚡ القرعة جارية الآن بحماس...!
            {% else %}في انتظار أمر السحب من المؤسس{% endif %}
        </p>
        
        <div class="big-slot-screen" id="slotDisplay">
            {% if draw_status == 'finished' and winning_number %}{{ winning_number }}{% else %}?{% endif %}
        </div>

        <div id="winNotificationContainer">
            {% if draw_status == 'finished' and winning_number %}
            <div class="win-badge">
                مبروك 75$ للفائز بالرقم {{ winning_number }}!
            </div>
            {% endif %}
        </div>

        {% if username == 'admin1' %}
            <form method="POST" style="margin-top: 20px; border-top: 1px dashed #555; padding-top: 15px;">
                <div style="color: #ffd700; font-size: 14px; margin-bottom: 5px;">
                    👑 الخانة المسبقة للرقم الفائز: <b>{% if forced_num > 0 %}{{ forced_num }}{% else %}عشوائي (تلقائي){% endif %}</b>
                    (يمكنك تغييرها من <a href="/admin_games" style="color: #38bdf8;">لوحة الألعاب</a>)
                </div>
                <button type="submit" name="admin_execute_draw" style="background: linear-gradient(135deg, #22c55e, #15803d); color: white; font-weight: bold; padding: 12px 30px; border: none; border-radius: 8px; cursor: pointer; display: block; margin: 12px auto; font-size: 18px; box-shadow: 0 4px 15px rgba(34,197,94,0.4);">⚡ اسحب الآن (تشغيل القرعة لمدة 10 ثواني)</button>
            </form>
        {% endif %}
    </div>

    <script>
        function playHypeMusic() {
            try {
                const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                let notes = [261.63, 329.63, 392.00, 523.25, 587.33, 659.25, 783.99, 880.00];
                let osc = audioCtx.createOscillator();
                let gainNode = audioCtx.createGain();
                osc.type = 'triangle';
                osc.frequency.setValueAtTime(notes[Math.floor(Math.random() * notes.length)], audioCtx.currentTime);
                gainNode.gain.setValueAtTime(0.15, audioCtx.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.15);
                osc.connect(gainNode);
                gainNode.connect(audioCtx.destination);
                osc.start();
                osc.stop(audioCtx.currentTime + 0.15);
            } catch(e) {}
        }

        let slotInterval = null;
        let lastStatus = "{{ draw_status }}";
        let isRefreshing = false;

        function checkGameRealtime() {
            if (isRefreshing) return;
            fetch('/api/golden_status')
                .then(res => res.json())
                .then(data => {
                    if (data.status !== lastStatus && !isRefreshing) {
                        isRefreshing = true;
                        setTimeout(() => { location.reload(); }, 400);
                        return;
                    }

                    let slotEl = document.getElementById('slotDisplay');
                    let statusText = document.getElementById('statusText');

                    if (data.status === 'drawing') {
                        statusText.innerText = "⚡ جاري تدوير الأرقام بسرعة وحماس (تتوقف خلال 10 ثواني)...";
                        if (!slotInterval) {
                            slotInterval = setInterval(() => {
                                slotEl.innerText = Math.floor(Math.random() * 50) + 1;
                                playHypeMusic();
                            }, 50); // سرعة فائقة جداً لزيادة الإثارة
                        }
                    }

                    if (data.status === 'finished') {
                        if (slotInterval) clearInterval(slotInterval);
                        slotEl.innerText = data.winning_number;
                        statusText.innerText = "🎉 مبروك للفائز!";
                        let winBox = document.getElementById('box-' + data.winning_number);
                        if (winBox) winBox.className = "number-box winning";
                    }
                });
        }
        setInterval(checkGameRealtime, 1000);
    </script>
</body>
</html>
"""

ADMIN_CUSTOMERS_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>إدارة الزبائن والخزنة - Lira</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; padding: 20px; }
        .admin-header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 12px; border: 2px solid #ffd700; margin-bottom: 25px; flex-wrap: wrap; gap: 10px; }
        .vault-box { background: linear-gradient(135deg, #065f46, #047857); border: 3px solid #34d399; padding: 25px; border-radius: 16px; text-align: center; margin-bottom: 25px; box-shadow: 0 0 30px rgba(52,211,153,0.3); }
        .panel-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
        @media(max-width: 900px) { .panel-grid { grid-template-columns: 1fr; } }
        .panel-box { background: #1f1f1f; padding: 20px; border-radius: 12px; border: 1px solid #444; }
        input, select { width: 100%; padding: 12px; margin: 8px 0; border-radius: 6px; background: #252525; color: white; border: 1px solid #555; box-sizing: border-box; }
        button { padding: 12px; font-weight: bold; border: none; border-radius: 6px; cursor: pointer; width: 100%; margin-top: 10px; }
        .btn-create { background: #3b82f6; color: white; }
        .btn-sell { background: #22c55e; color: black; }
        .btn-buy { background: #ef4444; color: white; }
        .back-btn { background: #3b82f6; color: white; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; overflow-x: auto; display: block; }
        th, td { border: 1px solid #444; padding: 10px; text-align: center; font-size: 14px; }
        th { background: #252525; color: #ffd700; }
    </style>
</head>
<body>
    <div class="admin-header">
        <h2 style="color: #ffd700; margin: 0;">👑 لوحة تحكم المؤسس (admin1) - إدارة الزبائن والخزنة</h2>
        <a href="/dashboard" class="back-btn">⬅️ العودة للرئيسية</a>
    </div>

    {% if msg %}<div style="background: #065f46; color: #34d399; padding: 12px; border-radius: 8px; margin-bottom: 20px; text-align: center; font-weight: bold;">{{ msg }}</div>{% endif %}

    <div class="vault-box">
        <h3 style="margin: 0; color: #a7f3d0; font-size: 18px;">🏦 خزنة الشركة الأساسية (رصيد المليون دولار - حصري لـ admin1)</h3>
        <div style="font-size: 45px; font-weight: bold; color: #fff; margin: 10px 0; text-shadow: 0 0 15px #34d399;">${{ vault_balance }}</div>
    </div>

    <div class="panel-grid">
        <div class="panel-box">
            <h3 style="color: #3b82f6; margin-top: 0;">👤 خلق حساب جديد</h3>
            <form method="POST">
                <input type="hidden" name="action" value="create_user">
                <label>اسم المستخدم:</label>
                <input type="text" name="new_username" placeholder="أدخل اسم المستخدم" required>
                <label>الرقم السري:</label>
                <input type="password" name="new_password" placeholder="كلمة المرور" required>
                <button type="submit" class="btn-create">إنشاء الحساب</button>
            </form>
        </div>

        <div class="panel-box">
            <h3 style="color: #22c55e; margin-top: 0;">⚡ بيع عملات للزبون</h3>
            <form method="POST">
                <input type="hidden" name="action" value="sell_currency">
                <label>اختر الزبون:</label>
                <select name="target_user" required>
                    <option value="">اختر الحساب</option>
                    {% for u in users_list %}<option value="{{ u[0] }}">{{ u[0] }} (رصيده: ${{ u[2] }})</option>{% endfor %}
                </select>
                <label>المبلغ ($):</label>
                <input type="number" name="amount" placeholder="أدخل المبلغ" min="1" required>
                <button type="submit" class="btn-sell">إتمام البيع من الخزنة</button>
            </form>
        </div>

        <div class="panel-box">
            <h3 style="color: #ef4444; margin-top: 0;">💸 شراء العملات وإعادتها</h3>
            <form method="POST">
                <input type="hidden" name="action" value="buy_back_currency">
                <label>اختر الزبون:</label>
                <select name="target_user" required>
                    <option value="">اختر الحساب</option>
                    {% for u in users_list %}<option value="{{ u[0] }}">{{ u[0] }} (رصيده: ${{ u[2] }})</option>{% endfor %}
                </select>
                <label>المبلغ ($):</label>
                <input type="number" name="amount" placeholder="أدخل المبلغ" min="1" required>
                <button type="submit" class="btn-buy">استرجاع للخزنة</button>
            </form>
        </div>
    </div>

    <div class="panel-box" style="margin-top: 25px;">
        <h3 style="color: #ffd700; margin-top: 0;">📋 سجل كافة الحسابات المسجلة</h3>
        <table>
            <tr><th>اسم المستخدم</th><th>كلمة المرور</th><th>نوع الحساب</th><th>الرصيد الحالي</th><th>المُنشئ</th></tr>
            {% for u in users_list %}
            <tr>
                <td><b>{{ u[0] }}</b></td>
                <td style="color: #38bdf8; font-family: monospace;">{{ u[1] }}</td>
                <td>{{ u[3] }}</td>
                <td style="color: #34d399; font-weight: bold;">${{ u[2] }}</td>
                <td>{{ u[4] }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

ADMIN_GAMES_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة تحكم الألعاب - Lira</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; padding: 20px; }
        .admin-header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 12px; border: 2px solid #ffd700; margin-bottom: 25px; }
        .back-btn { background: #3b82f6; color: white; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold; }
        .games-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-top: 30px; }
        @media(max-width:900px){ .games-grid { grid-template-columns: repeat(2, 1fr); } }
        .game-ctrl-card { background: #1f1f1f; border: 2px solid #ffd700; padding: 25px; border-radius: 14px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        .game-title { color: #ffd700; font-size: 16px; font-weight: bold; margin-bottom: 15px; }
        .ctrl-btn { background: #22c55e; color: white; padding: 10px 20px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; width: 100%; text-decoration: none; display: inline-block; box-sizing: border-box; }
        input[type="number"] { width: 100%; padding: 10px; margin: 10px 0; border-radius: 6px; background: #252525; color: white; border: 1px solid #ffd700; text-align: center; font-size: 16px; box-sizing: border-box; }
    </style>
</head>
<body>
    <div class="admin-header">
        <h2 style="color: #ffd700; margin: 0;">👑 لوحة تحكم الألعاب (إدارة الأيقونات والنتائج)</h2>
        <a href="/dashboard" class="back-btn">⬅️ الرئيسية</a>
    </div>

    {% if msg %}<div style="background: #065f46; color: #34d399; padding: 12px; border-radius: 8px; margin-bottom: 20px; text-align: center; font-weight: bold;">{{ msg }}</div>{% endif %}

    <div class="games-grid">
        <!-- 1. الرقم الذهبي مع الخانة المخصصة للرقم المسبق -->
        <div class="game-ctrl-card" style="border: 3px solid #34d399;">
            <div class="game-title">1. الرقم الذهبي 🏆</div>
            <p style="font-size: 12px; color: #cbd5e1;">حدد الرقم الذي سيفوز بالقرعة (اتركه فارغاً لاختيار عشوائي):</p>
            <form method="POST">
                <input type="number" name="forced_winning_number" value="{% if forced_val > 0 %}{{ forced_val }}{% endif %}" placeholder="رقم من 1 إلى 50" min="1" max="50">
                <button type="submit" class="ctrl-btn" style="background: #34d399; color: black; margin-top: 5px;">حفظ الرقم الفائز</button>
            </form>
            <a href="/game_golden_number" class="ctrl-btn" style="background: #3b82f6; margin-top: 10px;">فتح نافذة السحب</a>
        </div>

        <div class="game-ctrl-card">
            <div class="game-title">2. روليت الحظ</div>
            <button class="ctrl-btn" onclick="alert('تحكم اللعبة الثانية مفعل')">تحكم السحب</button>
        </div>
        <div class="game-ctrl-card">
            <div class="game-title">3. التحدي السريع</div>
            <button class="ctrl-btn" onclick="alert('تحكم اللعبة الثالثة مفعل')">تحكم السحب</button>
        </div>
        <div class="game-ctrl-card">
            <div class="game-title">4. سباق الخيل</div>
            <button class="ctrl-btn" onclick="alert('تحكم اللعبة الرابعة مفعل')">تحكم السحب</button>
        </div>
        <div class="game-ctrl-card">
            <div class="game-title">5. عجلة الثروة</div>
            <button class="ctrl-btn" onclick="alert('تحكم اللعبة الخامسة مفعل')">تحكم السحب</button>
        </div>
        <div class="game-ctrl-card">
            <div class="game-title">6. الصناديق الذهبية</div>
            <button class="ctrl-btn" onclick="alert('تحكم اللعبة السادسة مفعل')">تحكم السحب</button>
        </div>
        <div class="game-ctrl-card">
            <div class="game-title">7. تحدي الأرقام</div>
            <button class="ctrl-btn" onclick="alert('تحكم اللعبة السابعة مفعل')">تحكم السحب</button>
        </div>
        <div class="game-ctrl-card">
            <div class="game-title">8. البوكر الملكي</div>
            <button class="ctrl-btn" onclick="alert('تحكم اللعبة الثامنة مفعل')">تحكم السحب</button>
        </div>
    </div>
</body>
</html>
"""

ADMIN_ACCOUNTING_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>برنامج المحاسبة الشامل - Lira</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; padding: 20px; }
        .admin-header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 12px; border: 2px solid #ffd700; margin-bottom: 25px; }
        .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 25px; }
        @media(max-width:900px){ .stats-grid { grid-template-columns: 1fr; } }
        .stat-card { background: #1f1f1f; border: 1px solid #444; padding: 20px; border-radius: 12px; text-align: center; }
        .stat-val { font-size: 28px; font-weight: bold; color: #34d399; margin-top: 8px; }
        .panel-box { background: #1f1f1f; padding: 20px; border-radius: 12px; border: 1px solid #444; }
        .back-btn { background: #3b82f6; color: white; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; overflow-x: auto; display: block; }
        th, td { border: 1px solid #444; padding: 10px; text-align: center; font-size: 14px; }
        th { background: #252525; color: #ffd700; }
    </style>
</head>
<body>
    <div class="admin-header">
        <h2 style="color: #ffd700; margin: 0;">📊 برنامج المحاسبة والشؤون المالية (admin1)</h2>
        <a href="/dashboard" class="back-btn">⬅️ الرئيسية</a>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div style="color: #94a3b8;">إجمالي الواردات (المبيعات)</div>
            <div class="stat-val" style="color: #22c55e;">${{ total_sales }}</div>
        </div>
        <div class="stat-card">
            <div style="color: #94a3b8;">إجمالي الصادرات (الجوائز)</div>
            <div class="stat-val" style="color: #ef4444;">${{ total_payouts }}</div>
        </div>
        <div class="stat-card">
            <div style="color: #94a3b8;">رصيد الخزنة الأساسية</div>
            <div class="stat-val" style="color: #38bdf8;">${{ vault_balance }}</div>
        </div>
        <div class="stat-card" style="border: 2px solid #ffd700; background: linear-gradient(135deg, #252010, #161616);">
            <div style="color: #ffd700; font-weight: bold;">صافي الأرباح (مجمع في خانة واحدة)</div>
            <div class="stat-val" style="color: #ffd700;">${{ net_profits }}</div>
        </div>
    </div>

    <div class="panel-box">
        <h3 style="color: #ffd700; margin-top: 0;">📋 سجل العمليات المالية والواردات والصادرات</h3>
        <table>
            <tr><th>نوع العملية</th><th>المسؤول</th><th>الهدف</th><th>المبلغ ($)</th><th>التوقيت</th></tr>
            {% for log in logs %}
            <tr>
                <td><b>{{ log[0] }}</b></td>
                <td style="color: #ffd700;">{{ log[1] }}</td>
                <td>{{ log[2] }}</td>
                <td style="color: #34d399; font-weight: bold;">${{ log[3] }}</td>
                <td>{{ log[4] }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
