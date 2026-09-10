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

# API آمن تماماً وخالٍ من أي سحب عشوائي
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
        
        # 1. إذا كان في وضع التدوير (drawing) وانتهت الـ 15 ثانية -> الانتقال للإضاءة الذهبية (finished)
        if status == 'drawing' and current_time >= end_timestamp:
            cursor.execute("SELECT username FROM golden_number_bookings WHERE number=?", (winning_number,))
            winner = cursor.fetchone()
            if winner:
                winner_name = winner[0]
                # منح الجائزة الكبرى مرة واحدة فقط بدقة
                cursor.execute("UPDATE users SET balance = balance + 75.0 WHERE username=?", (winner_name,))
            
            # بقاء اللوحة مضاءة لمدة 30 ثانية
            new_lighting_end = current_time + 30
            cursor.execute("UPDATE game_draws SET status='finished', draw_end_timestamp=? WHERE game_name='golden_number'", (new_lighting_end,))
            conn.commit()
            status = 'finished'
            end_timestamp = new_lighting_end

        # 2. إذا كان في وضع الإضاءة (finished) وانتهت الـ 30 ثانية -> التوقف التام في وضع الاستعداد (idle) ودون سحب تلقائي أبداً
        elif status == 'finished' and current_time >= end_timestamp:
            cursor.execute("DELETE FROM golden_number_bookings")
            cursor.execute("UPDATE game_draws SET status='idle', winning_number=0, draw_end_timestamp=0 WHERE game_name='golden_number'")
            conn.commit()
            status = 'idle'
            end_timestamp = 0

        remaining = int(end_timestamp - current_time) if status in ['drawing', 'finished'] else 0
        if remaining < 0: remaining = 0
    else:
        winning_number = 0
        status = 'idle'
        remaining = 0

    cursor.execute("SELECT number, username FROM golden_number_bookings")
    bookings = {r[0]: r[1] for r in cursor.fetchall()}

    conn.close()

    return jsonify({
        "status": status,
        "winning_number": winning_number,
        "remaining_seconds": remaining,
        "bookings": bookings
    })

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
            cursor.execute("SELECT status FROM game_draws WHERE game_name='golden_number'")
            st = cursor.fetchone()[0]
            # حماية صارمة جداً: لا يتم السحب مطلقاً إلا إذا كانت اللوحة في وضع idle وبأمر يدوي بحت
            if st == 'idle':
                forced_num = request.form.get('forced_number')
                winning_num = int(forced_num) if forced_num else random.randint(1, 50)
                
                end_timestamp = time.time() + 15
                cursor.execute("UPDATE game_draws SET winning_number=?, status='drawing', draw_end_timestamp=? WHERE game_name='golden_number'",
                               (winning_num, end_timestamp))
                conn.commit()
                msg = f"تم بدء السحب الحماسي (15 ثانية) بواسطة المدير {username}..."
            else:
                msg = "عذراً، لا يمكن بدء سحب جديد الآن لأن اللوحة قيد السحب أو عرض الفائز!"

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
        .
