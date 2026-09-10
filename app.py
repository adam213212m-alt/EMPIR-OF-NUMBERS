from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import sqlite3
import random
import time
from datetime import datetime, timezone, timedelta
import threading

app = Flask(__name__)
app.secret_key = 'empire_lira_clean_2026'

def init_db():
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
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

    # جدول خزنة البرنامج المركزية
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

    # جدول حجز الأرقام للعبة الرقم الذهبي
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS golden_number_bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            number INTEGER,
            draw_date TEXT
        )
    ''')

    # جدول حالة السحب والنتائج والعد التنازلي العام
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_draws (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_name TEXT UNIQUE,
            winning_number INTEGER,
            status TEXT,
            draw_time TEXT,
            draw_end_timestamp REAL DEFAULT 0
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM game_draws WHERE game_name='golden_number'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO game_draws (game_name, winning_number, status, draw_end_timestamp) VALUES ('golden_number', 0, 'idle', 0)")

    # إنشاء الـ 3 حسابات الرئيسية للمديرين إن لم تكن موجودة
    main_admins = ['admin1', 'admin2', 'admin3']
    for adm in main_admins:
        cursor.execute("SELECT * FROM users WHERE username=?", (adm,))
        user_exists = cursor.fetchone()
        if not user_exists:
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

# API عام وموحد يغذي كافة الحسابات واللاعبين بالحالة الحية والرقم الفائز فوراً
@app.route('/api/game_status')
def api_game_status():
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    
    current_time = time.time()
    cursor.execute("SELECT winning_number, status, draw_end_timestamp FROM game_draws WHERE game_name='golden_number'")
    row = cursor.fetchone()
    
    if row:
        winning_number = row[0]
        status = row[1]
        end_timestamp = row[2]
        
        # 1. انتهاء فترة الـ 15 ثانية للتدوير -> الانتقال لحالة الفوز ومنح الجائزة وتفعيل الإضاءة الذهبية لجميع الشاشات
        if status == 'drawing' and current_time >= end_timestamp:
            cursor.execute("SELECT username FROM golden_number_bookings WHERE number=?", (winning_number,))
            winner = cursor.fetchone()
            if winner:
                winner_name = winner[0]
                cursor.execute("UPDATE users SET balance = balance + 75.0 WHERE username=?", (winner_name,))
            
            # بقاء الرقم واللوحة مضاءة لمدة 30 ثانية أمام جميع الحسابات
            new_lighting_end = current_time + 30
            cursor.execute("UPDATE game_draws SET status='finished', draw_end_timestamp=? WHERE game_name='golden_number'", (new_lighting_end,))
            conn.commit()
            status = 'finished'
            end_timestamp = new_lighting_end

            # تصفير اللوحة تلقائياً بعد 30 ثانية لتصبح جاهزة للجولة التالية للجميع
            def reset_board_after_30s():
                time.sleep(30)
                c_conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
                c_cur = c_conn.cursor()
                c_cur.execute("DELETE FROM golden_number_bookings")
                c_cur.execute("UPDATE game_draws SET status='idle', winning_number=0, draw_end_timestamp=0 WHERE game_name='golden_number'")
                c_conn.commit()
                c_conn.close()
            threading.Thread(target=reset_board_after_30s, daemon=True).start()

        # 2. انتهاء فترة الـ 30 ثانية للإضاءة -> تصفير اللوحة وإعادتها لوضع الاستعداد لجميع اللاعبين
        elif status == 'finished' and current_time >= end_timestamp:
            cursor.execute("DELETE FROM golden_number_bookings")
            cursor.execute("UPDATE game_draws SET status='idle', winning_number=0, draw_end_timestamp=0 WHERE game_name='golden_number'")
            conn.commit()
            status = 'idle'

        remaining = int(end_timestamp - current_time) if status in ['drawing', 'finished'] else 0
        if remaining < 0: remaining = 0

    cursor.execute("SELECT number, username FROM golden_number_bookings")
    bookings = {r[0]: r[1] for r in cursor.fetchall()}

    conn.close()

    return jsonify({
        "status": status,
        "winning_number": winning_number,
        "remaining_seconds": remaining,
        "bookings": bookings
    })

# اللعبة الأولى: الرقم الذهبي
@app.route('/game_one_page', methods=['GET', 'POST'])
def game_one_page():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    role = session['role']
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    
    msg = None
    if request.method == 'POST':
        if 'book_number' in request.form:
            cursor.execute("SELECT status FROM game_draws WHERE game_name='golden_number'")
            current_status = cursor.fetchone()[0]
            if current_status == 'idle':
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
                        msg = f"عذراً، الرقم {number} محجوز مسبقاً من قبل لاعب آخر!"
                else:
                    msg = "رصيدك غير كافٍ لحجز هذا الرقم! يرجى شحن الرصيد."
            else:
                msg = "عذراً، جاري السحب حالياً! يرجى الانتظار للجولة القادمة."
        
        elif 'admin_draw' in request.form and role == 'admin':
            forced_num = request.form.get('forced_number')
            winning_num = int(forced_num) if forced_num else random.randint(1, 50)
            
            # بدء العد التنازلي لمدة 15 ثانية للتدوير لجميع اللاعبين
            end_timestamp = time.time() + 15
            cursor.execute("UPDATE game_draws SET winning_number=?, status='drawing', draw_end_timestamp=? WHERE game_name='golden_number'",
                           (winning_num, end_timestamp))
            conn.commit()
            msg = f"تم بدء السحب الحماسي (15 ثانية) لجميع الحسابات..."

    cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
    balance = cursor.fetchone()[0]

    cursor.execute("SELECT number, username FROM golden_number_bookings")
    bookings = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute("SELECT number FROM golden_number_bookings WHERE username=?", (username,))
    my_bookings = [r[0] for r in cursor.fetchall()]
    my_spent = len(my_bookings) * 2.0

    cursor.execute("SELECT winning_number, status FROM game_draws WHERE game_name='golden_number'")
    draw_info = cursor.fetchone()
    winning_number = draw_info[0] if draw_info else None
    game_status = draw_info[1] if draw_info else 'idle'

    conn.close()
    return render_template_string(GAME_ONE_PAGE, username=username, role=role, balance=balance, 
                                  bookings=bookings, my_bookings=my_bookings, my_spent=my_spent, 
                                  winning_number=winning_number, game_status=game_status, msg=msg)

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

# لوحة التحكم الخاصة بالمديرين
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
                cursor.execute("INSERT INTO financial_logs (action_type, admin_name, target_user, amount, log_time) VALUES ('بيع رصيد (من الخزنة)', ?, ?, ?, ?)", 
                               (current_admin, target_user, amount, time.strftime('%Y-%m-%d %H:%M')))
                conn.commit()
            elif action == 'buy_back' and user_row[0] >= amount:
                cursor.execute("UPDATE users SET balance = balance - ? WHERE username=?", (target_user, amount))
                cursor.execute("UPDATE system_vault SET vault_balance = vault_balance + ? WHERE id=1", (amount,))
                cursor.execute("INSERT INTO financial_logs (action_type, admin_name, target_user, amount, log_time) VALUES ('شراء رصيد (إلى الخزنة)', ?, ?, ?, ?)", 
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
        
        .icon-card { background: linear-gradient(145deg, #1f1f1f, #121212); border: 2px solid #b8860b; border-radius: 16px; padding: 25px; text-align: center; cursor: pointer; transition: all 0.3s ease; box-shadow: 0 4px 20px rgba(0,0,0,0.6); display: flex; flex-direction: column; align-items: center; justify-content: center; text-decoration: none; }
        .icon-card:hover { border-color: #ffd700; transform: translateY(-5px); box-shadow: 0 8px 30px rgba(255,215,0,0.4); background: linear-gradient(145deg, #252210, #161616); }
        .icon-logo { font-size: 55px; margin-bottom: 12px; filter: drop-shadow(0 0 10px rgba(255,215,0,0.6)); }
        .icon-title { color: #ffd700; font-size: 16px; font-weight: bold; text-shadow: 0 2px 4px rgba(0,0,0,0.8); }
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
            <div class="icon-logo">🏆</div>
            <div class="icon-title">الرقم الذهبي</div>
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

GAME_ONE_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>لعبة الرقم الذهبي - Lira</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 12px; border-bottom: 2px solid #ffd700; flex-wrap: wrap; gap: 10px; }
        .board-container { background: #120e06; border: 6px solid #b8860b; border-image: linear-gradient(to bottom right, #ffd700, #8b6508) 1; padding: 25px; border-radius: 16px; margin-top: 25px; box-shadow: 0 0 35px rgba(255,215,0,0.2); text-align: center; }
        .board-grid { display: grid; grid-template-columns: repeat(10, 1fr); gap: 10px; margin-top: 20px; }
        @media(max-width: 768px) { .board-grid { grid-template-columns: repeat(5, 1fr); } }
        
        .number-box { background: #000; border: 3px solid #ffd700; border-radius: 8px; height: 55px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 20px; font-weight: bold; color: #ffffff; cursor: pointer; transition: 0.3s; box-shadow: inset 0 0 10px rgba(255,215,0,0.3); }
        .number-box:hover { background: #1a1500; transform: scale(1.05); }
        .number-box.booked { background: #3b0000; border-color: #ef4444; color: #f87171; cursor: not-allowed; }
        
        /* إضاءة الرقم الفائز باللون الذهبي الفاخر لجميع الشاشات */
        .number-box.winning { background: linear-gradient(135deg, #ffd700, #ff8c00) !important; color: #000 !important; border-color: #ffffff !important; box-shadow: 0 0 60px #ffd700; transform: scale(1.18); font-weight: bold; animation: pulse 0.6s infinite alternate; }
        @keyframes pulse { from { transform: scale(1); } to { transform: scale(1.22); } }
        
        .draw-panel { background: #1f1f1f; border: 2px solid #ffd700; padding: 25px; border-radius: 16px; margin-top: 25px; text-align: center; }
        .big-winning-screen { background: radial-gradient(circle, #3d2c00 0%, #000000 100%); border: 4px solid #ffd700; color: #ffd700; font-size: 75px; font-weight: bold; padding: 20px; width: 280px; margin: 20px auto; border-radius: 20px; box-shadow: 0 0 45px rgba(255,215,0,0.7); letter-spacing: 6px; text-shadow: 0 0 25px #ffd700; }
        
        .win-badge { background: linear-gradient(135deg, #ffd700, #b8860b); color: #000; border: 4px solid #fff; padding: 25px; border-radius: 20px; margin: 25px auto; width: 90%; max-width: 550px; text-align: center; box-shadow: 0 0 55px rgba(255,215,0,0.9); animation: bounce 1s infinite alternate; }
        @keyframes bounce { from { transform: translateY(0); } to { transform: translateY(-8px); } }

        .my-stats { background: #162032; border: 1px solid #38bdf8; padding: 15px; border-radius: 10px; margin-top: 25px; }
        .back-btn { background: #3b82f6; color: white; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h2 style="color: #ffd700; margin: 0;">👑 لعبة الرقم الذهبي (من 1 إلى 50)</h2>
        <div style="display: flex; gap: 15px; align-items: center;">
            <div style="color: #34d399; font-weight: bold; font-size: 18px;">الرصيد: ${{ balance }}</div>
            <a href="/dashboard" class="back-btn">⬅️ العودة للرئيسية</a>
        </div>
    </div>

    {% if msg %}<div style="background: #065f46; color: #34d399; padding: 12px; border-radius: 8px; margin-top: 15px; text-align: center; font-weight: bold;">{{ msg }}</div>{% endif %}

    <div class="board-container">
        <h3 style="color: #ffd700; margin-top: 0;">🎯 اختر أرقامك (سعر الحجز: $2 للرقم | الجائزة الكبرى: $75)</h3>
        <div class="board-grid" id="boardGrid">
            {% for i in range(1, 51) %}
                {% if i in bookings %}
                    <div id="box-{{ i }}" class="number-box booked {% if game_status == 'finished' and winning_number == i %}winning{% endif %}">
                        {{ i }}<br><span style="font-size: 10px; color: #f87171;">({{ bookings[i] }})</span>
                    </div>
                {% else %}
                    <form method="POST" style="margin: 0;">
                        <input type="hidden" name="number" value="{{ i }}">
                        <button type="submit" name="book_number" id="box-{{ i }}" class="number-box" style="width: 100%; height: 55px;" title="اضغط للحجز بـ $2">
                            {{ i }}
                        </button>
                    </form>
                {% endif %}
            {% endfor %}
        </div>
    </div>

    <div class="draw-panel">
        <h3 style="color: #ffd700; margin: 0;">🎰 شاشة العرض الكبرى للسحب الحماسي</h3>
        <p id="drawStatusText" style="color: #cbd5e1; font-size: 16px; margin-top: 10px;">
            {% if game_status == 'drawing' %}⏳ جاري تدوير الـ 50 رقماً (15 ثانية)...{% elif game_status == 'finished' %}🎉 تم إعلان الرقم الفائز!{% else %}مفتوح لحجز المراهنات (إطلاق السحب يدوياً من المدير){% endif %}
        </p>
        
        <div class="big-winning-screen" id="slotDisplay">{% if game_status == 'finished' and winning_number %}{{ winning_number }}{% else %}?{% endif %}</div>

        <div id="countdownTimer" style="font-size: 26px; color: #ffd700; font-weight: bold; margin: 15px 0;"></div>

        <div id="winNotificationContainer">
            {% if game_status == 'finished' and winning_number %}
            <div class="win-badge">
                <div style="font-size: 28px; font-weight: bold; color: #000; text-shadow: 0 2px 4px rgba(255,255,255,0.4);">مبروك فاز الرقم {{ winning_number }} بمبلغ 75$</div>
                <div style="font-size: 18px; margin-top: 8px; color: #111; font-weight: bold;">الرقم مضاء باللون الذهبي لمدة 30 ثانية لجميع اللاعبين!</div>
            </div>
            {% endif %}
        </div>

        {% if role == 'admin' %}
            <form method="POST" style="margin-top: 20px; border-top: 1px dashed #444; padding-top: 15px;">
                <label style="color: #ffd700; font-weight: bold; font-size: 16px;">👑 (لوحة تحكم المدير) تحديد الرقم الفائز مسبقاً أو تركه عشوائياً:</label><br>
                <input type="number" name="forced_number" placeholder="رقم من 1 إلى 50 (اختياري)" min="1" max="50" style="padding: 10px; width: 220px; border-radius: 6px; background: #252525; color: white; border: 1px solid #ffd700; margin-top: 10px; text-align: center; font-size: 16px;">
                <button type="submit" name="admin_draw" id="drawBtn" style="background: linear-gradient(135deg, #22c55e, #15803d); color: white; font-weight: bold; padding: 14px 35px; border: none; border-radius: 8px; cursor: pointer; display: block; margin: 15px auto; font-size: 18px; box-shadow: 0 4px 15px rgba(34,197,94,0.4);">⚡ بدء السحب الآن (15 ثانية للجميع)</button>
            </form>
        {% endif %}
    </div>

    <div class="my-stats">
        <h3 style="color: #38bdf8; margin-top: 0;">👤 ملخص حسابك في اللعبة</h3>
        <p>الأرقام التي قمت بحجزها: <b style="color: #ffd700;">{% if my_bookings %}{{ my_bookings | join(', ') }}{% else %}لا توجد أرقام محجوزة حتى الآن{% endif %}</b></p>
        <p>إجمالي الرصيد الذي تم صرفه على الحجوزات: <b style="color: #ef4444;">${{ my_spent }}</b></p>
    </div>

    <!-- نظام التزامن الشامل لجميع الحسابات واللاعبين -->
    <script>
        function playHypeMusicNote() {
            try {
                const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                let notes = [261.63, 329.63, 392.00, 523.25, 587.33, 659.25, 783.99];
                let osc = audioCtx.createOscillator();
                let gainNode = audioCtx.createGain();
                osc.type = 'triangle';
                osc.frequency.setValueAtTime(notes[Math.floor(Math.random() * notes.length)], audioCtx.currentTime);
                gainNode.gain.setValueAtTime(0.12, audioCtx.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.2);
                osc.connect(gainNode);
                gainNode.connect(audioCtx.destination);
                osc.start();
                osc.stop(audioCtx.currentTime + 0.2);
            } catch(e) {}
        }

        let slotInterval = null;
        let lastStatus = "{{ game_status }}";

        function updateGameRealtime() {
            fetch('/api/game_status')
                .then(res => res.json())
                .then(data => {
                    let timerEl = document.getElementById('countdownTimer');
                    let slotEl = document.getElementById('slotDisplay');
                    let statusText = document.getElementById('drawStatusText');
                    let winContainer = document.getElementById('winNotificationContainer');

                    // تحديث المراهنات والحجوزات لجميع اللاعبين فوراً
                    for (let i = 1; i <= 50; i++) {
                        let box = document.getElementById('box-' + i);
                        if (box) {
                            if (data.bookings[i]) {
                                if (box.tagName === 'BUTTON' || box.tagName === 'FORM') {
                                    let parent = box.closest('form') || box;
                                    parent.outerHTML = `<div id="box-${i}" class="number-box booked">${i}<br><span style="font-size: 10px; color: #f87171;">(${data.bookings[i]})</span></div>`;
                                }
                            }
                        }
                    }

                    if (data.status === 'drawing') {
                        timerEl.innerText = "⏳ العد التنازلي للتدوير: " + data.remaining_seconds + " ثانية";
                        statusText.innerText = "جاري تدوير الـ 50 رقماً عشوائياً أمام الجميع...";
                        
                        if (!slotInterval) {
                            slotInterval = setInterval(() => {
                                slotEl.innerText = Math.floor(Math.random() * 50) + 1;
                                playHypeMusicNote();
                            }, 80);
                        }

                        if (data.remaining_seconds <= 0 && lastStatus !== 'finished') {
                            location.reload();
                        }
                    } else if (data.status === 'finished') {
                        if (slotInterval) clearInterval(slotInterval);
                        timerEl.innerText = "⏳ اللوحة مضاءة باللون الذهبي لجميع اللاعبين (" + data.remaining_seconds + " ثانية متبقية)";
                        slotEl.innerText = data.winning_number;
                        statusText.innerText = "الرقم الفائز بالقرعة:";

                        // إضاءة الرقم باللون الذهبي الفاخر لجميع الشاشات في نفس اللحظة
                        let winBox = document.getElementById('box-' + data.winning_number);
                        if (winBox) {
                            winBox.className = "number-box winning";
                        }

                        // ظهور رسالة الفوز الكبرى لجميع الحسابات
                        if (!winContainer.innerHTML.includes("مبروك فاز الرقم")) {
                            winContainer.innerHTML = `
                                <div class="win-badge">
                                    <div style="font-size: 28px; font-weight: bold; color: #000; text-shadow: 0 2px 4px rgba(255,255,255,0.4);">مبروك فاز الرقم ${data.winning_number} بمبلغ 75$</div>
                                    <div style="font-size: 18px; margin-top: 8px; color: #111; font-weight: bold;">الرقم مضاء باللون الذهبي لمدة 30 ثانية لجميع اللاعبين!</div>
                                </div>
                            `;
                        }

                        if (data.remaining_seconds <= 0) {
                            location.reload();
                        }
                    } else {
                        if (slotInterval) clearInterval(slotInterval);
                        timerEl.innerText = "";
                        if (lastStatus === 'finished') {
                            location.reload();
                        }
                    }
                    lastStatus = data.status;
                });
        }

        // استعلام دوري كل ثانية لضمان تطابق الرؤية والتزامن التام لجميع الحسابات
        setInterval(updateGameRealtime, 1000);
    </script>
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

    <div class="vault-box">
        <h3 style="margin: 0; color: #a7f3d0; font-size: 18px;">🏦 رصيد الخزنة المركزية (الشركة)</h3>
        <div style="font-size: 42px; font-weight: bold; color: #fff; margin: 10px 0; text-shadow: 0 0 15px #34d399;">${{ vault_balance }}</div>
    </div>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div class="panel-box">
            <h3 style="color: #22c55e; margin-top: 0;">⚡ بيع رصيد للحساب</h3>
            <form method="POST">
                <input type="hidden" name="action" value="sell">
                <label>اختر الحساب (مدير أو زبون):</label>
                <select name="target_user" required>
                    <option value="">اختر الحساب</option>
                    {% for u in users_list %}<option value="{{ u[0] }}">{{ u[0] }} ({{ u[3] }}) - رصيده: ${{ u[2] }}</option>{% endfor %}
                </select>
                <label>المبلغ ($):</label>
                <input type="number" name="amount" placeholder="أدخل المبلغ" min="1" required>
                <button type="submit" class="btn-sell">إتمام عملية البيع</button>
            </form>
        </div>

        <div class="panel-box">
            <h3 style="color: #ef4444; margin-top: 0;">💸 شراء رصيد وإرجاعه للخزنة</h3>
            <form method="POST">
                <input type="hidden" name="action" value="buy_back">
                <label>اختر الحساب (مدير أو زبون):</label>
                <select name="target_user" required>
                    <option value="">اختر الحساب</option>
                    {% for u in users_list %}<option value="{{ u[0] }}">{{ u[0] }} ({{ u[3] }}) - رصيده: ${{ u[2] }}</option>{% endfor %}
                </select>
                <label>المبلغ ($):</label>
                <input type="number" name="amount" placeholder="أدخل المبلغ" min="1" required>
                <button type="submit" class="btn-buy">إتمام الشراء للخزنة</button>
            </form>
        </div>
    </div>

    <div class="panel-box" style="margin-top: 20px;">
        <h3 style="color: #ffd700; margin-top: 0;">👥 جدول كافة الحسابات (المديرين والزبائن والـ player)</h3>
        <table>
            <tr><th>اسم المستخدم</th><th>كلمة المرور</th><th>نوع الحساب</th><th>الرصيد الحالي</th><th>أُنشئ بواسطة</th></tr>
            {% for u in users_list %}
            <tr>
                <td><b>{{ u[0] }}</b></td>
                <td style="color: #38bdf8; font-family: monospace;">{{ u[1] }}</td>
                <td><span style="padding: 3px 8px; border-radius: 4px; background: {% if u[3] == 'admin' %}#b8860b{% else %}#1f2937{% endif %};">{{ u[3] }}</span></td>
                <td style="color: #34d399; font-weight: bold;">${{ u[2] }}</td>
                <td>{{ u[4] }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>

    <div class="panel-box" style="margin-top: 20px;">
        <h3 style="color: #38bdf8; margin-top: 0;">📋 سجل العمليات المالية الأخيرة</h3>
        <table>
            <tr><th>نوع العملية</th><th>المدير المسؤول</th><th>الهدف</th><th>المبلغ</th><th>التوقيت</th></tr>
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
            <input type="text" name="new_pass" placeholder="كلمة المرور (الرمز السري)" required>
            <button type="submit">إنشاء الحساب</button>
        </form>
        <a href="/admin_panel" class="back-btn">⬅️ العودة لوحة الإدارة</a>
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
