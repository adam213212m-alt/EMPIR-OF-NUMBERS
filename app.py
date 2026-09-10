from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import sqlite3
import random
import time
import datetime
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
app.secret_key = 'empire_lira_clean_2026'

DB_NAME = 'empire_stable.db'

def get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
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
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (username, password, balance, role, created_by) VALUES (?,?, 100000.0, 'admin', 'system')",
                           (adm, 'admin123'))
            cursor.execute("UPDATE system_vault SET vault_balance = vault_balance - 100000.0 WHERE id=1")

    conn.commit()
    conn.close()

init_db()

# دالة السحب التلقائي الساعة 9 مساء
def auto_draw():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM game_draws WHERE game_name='golden_number'")
    st = cursor.fetchone()[0]
    if st == 'idle':
        winning_num = random.randint(1, 50)
        end_timestamp = time.time() + 15
        cursor.execute("UPDATE game_draws SET winning_number=?, status='drawing', draw_end_timestamp=? WHERE game_name='golden_number'",
                       (winning_num, end_timestamp))
        conn.commit()
        print(f"[AUTO DRAW] تم السحب التلقائي على الرقم: {winning_num}")
    conn.close()

scheduler = BackgroundScheduler(timezone="Asia/Beirut")
scheduler.add_job(func=auto_draw, trigger="cron", hour=21, minute=0)
scheduler.start()

@app.route('/manifest.json')
def manifest():
    manifest_data = '{"name": "Lira ليرة", "short_name": "Lira", "start_url": "/", "display": "standalone", "background_color": "#0b0f19", "theme_color": "#ffd700"}'
    return app.response_class(manifest_data, status=200, mimetype='application/json')

@app.route('/sw.js')
def service_worker():
    return app.response_class("self.addEventListener('fetch', function(event) { });", mimetype='application/javascript')

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session.clear()
            session['username'] = user['username']
            session['password'] = user['password']
            session['balance'] = user['balance']
            session['role'] = user['role']
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
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE username=?", (session['username'],))
    row = cursor.fetchone()
    balance = row['balance'] if row else 0
    conn.close()
    return render_template_string(DASHBOARD_PAGE, username=session['username'], role=session['role'], balance=balance)

LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><title>تسجيل الدخول</title></head>
<body style="background:#0b0f19; color:#fff; text-align:center; padding:50px;">
    <h2>تسجيل الدخول</h2>
    {% if error %}<p style="color:red;">{{ error }}</p>{% endif %}
    <form method="POST">
        <input type="text" name="username" placeholder="اسم المستخدم" required><br><br>
        <input type="password" name="password" placeholder="كلمة المرور" required><br><br>
        <button type="submit">دخول</button>
    </form>
</body>
</html>
"""

DASHBOARD_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><title>لوحة التحكم</title></head>
<body style="background:#0b0f19; color:#fff; text-align:center; padding:50px;">
    <h1>مرحباً {{ username }}</h1>
    <p>الرصيد: ${{ balance }}</p>
    <a href="/logout" style="color:red;">تسجيل الخروج</a>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
