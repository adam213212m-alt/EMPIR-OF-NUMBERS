from flask import Flask, render_template_string, request, redirect, url_for, session
import sqlite3
import random
import time
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
app.secret_key = 'empire_secret_key_2026'

def get_beirut_time():
    return datetime.now(timezone(timedelta(hours=3)))

def init_db():
    conn = sqlite3.connect('empire_v2.db')
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
        CREATE TABLE IF NOT EXISTS game_board (
            number INTEGER PRIMARY KEY,
            status TEXT DEFAULT 'available',
            owner TEXT DEFAULT NULL
        )
    ''')
    
    cursor.execute('SELECT COUNT(*) FROM game_board')
    if cursor.fetchone()[0] == 0:
        for i in range(1, 51):
            cursor.execute('INSERT INTO game_board (number, status) VALUES (?, ?)', (i, 'available'))

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_board_state (
            id INTEGER PRIMARY KEY,
            last_winner_msg TEXT DEFAULT '',
            banner_end_time REAL DEFAULT 0
        )
    ''')
    cursor.execute('SELECT COUNT(*) FROM game_board_state')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO game_board_state (id, last_winner_msg, banner_end_time) VALUES (1, "بانتظار السحب اليومي الساعة 9:00 مساءً...", 0)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_three (
            slot_id INTEGER PRIMARY KEY,
            status TEXT DEFAULT 'available',
            owner TEXT DEFAULT NULL
        )
    ''')
    cursor.execute('SELECT COUNT(*) FROM game_three')
    if cursor.fetchone()[0] == 0:
        for i in range(1, 6):
            cursor.execute('INSERT INTO game_three (slot_id, status) VALUES (?, ?)', (i, 'available'))

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_three_state (
            id INTEGER PRIMARY KEY,
            is_full INTEGER DEFAULT 0,
            timer_end REAL DEFAULT 0,
            last_winner_msg TEXT DEFAULT '',
            banner_end_time REAL DEFAULT 0
        )
    ''')
    cursor.execute('SELECT COUNT(*) FROM game_three_state')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO game_three_state (id, is_full, timer_end, last_winner_msg, banner_end_time) VALUES (1, 0, 0, "بانتظار اكتمال الأرقام الفاخرة...", 0)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS winners_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_name TEXT,
            winner_info TEXT,
            win_time TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS financial_stats (
            game_name TEXT PRIMARY KEY,
            total_collected REAL DEFAULT 0,
            total_payouts REAL DEFAULT 0
        )
    ''')
    
    games_list = ["لوحة أرقام الحظ (80$)", "اللعبة الملكية الفاخرة", "لعبة الـ 15 مربعاً (15$)"]
    for g in games_list:
        cursor.execute("INSERT OR IGNORE INTO financial_stats (game_name, total_collected, total_payouts) VALUES (?, 0, 0)", (g,))
    
    # إنشاء حساب الأدمن الإجباري
    cursor.execute("SELECT * FROM users WHERE username='admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, balance, role, created_by) VALUES (?, ?, ?, ?, ?)", 
                       ('admin', 'admin123', 1000000, 'admin', 'system'))
    
    conn.commit()
    conn.close()

init_db()

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        conn = sqlite3.connect('empire_v2.db')
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
    
    try:
        username = session['username']
        conn = sqlite3.connect('empire_v2.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
        res = cursor.fetchone()
        user_balance = res[0] if res else 0
        session['balance'] = user_balance
        
        cursor.execute("SELECT number, status, owner FROM game_board")
        board = cursor.fetchall()

        cursor.execute("SELECT number FROM game_board WHERE owner=?", (username,))
        user_locked_numbers = [row[0] for row in cursor.fetchall()]
        user_total_spent = len(user_locked_numbers) * 2.0

        cursor.execute("SELECT last_winner_msg, banner_end_time FROM game_board_state WHERE id=1")
        board_state = cursor.fetchone()
        board_last_winner_msg = board_state[0] if board_state else ""

        cursor.execute("SELECT slot_id, status, owner FROM game_three")
        game_three_slots = cursor.fetchall()

        cursor.execute("SELECT game_name, winner_info, win_time FROM winners_log ORDER BY id DESC LIMIT 10")
        winners_records = cursor.fetchall()

        conn.close()
    except Exception as e:
        session.clear()
        return redirect(url_for('login'))

    return render_template_string(DASHBOARD_PAGE, 
                                  username=username,
                                  password=session.get('password', ''),
                                  role=session.get('role', 'class_b'), 
                                  balance=user_balance, 
                                  board=board,
                                  user_locked_numbers=user_locked_numbers,
                                  user_total_spent=user_total_spent,
                                  board_last_winner_msg=board_last_winner_msg,
                                  game_three_slots=game_three_slots,
                                  winners_records=winners_records)

@app.route('/admin_panel')
def admin_panel():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('dashboard'))
    
    conn = sqlite3.connect('empire_v2.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, password, balance, role, created_by FROM users")
    all_users = cursor.fetchall()

    cursor.execute("SELECT game_name, total_collected, total_payouts FROM financial_stats")
    fin_data = cursor.fetchall()
    
    financial_report = []
    total_net_profit = 0
    for name, collected, payouts in fin_data:
        net = collected - payouts
        total_net_profit += net
        financial_report.append({
            'name': name,
            'collected': collected,
            'payouts': payouts,
            'net': net
        })

    conn.close()
    
    return render_template_string(ADMIN_PAGE, username=session['username'], all_users=all_users, financial_report=financial_report, total_net_profit=total_net_profit)

@app.route('/pick_number/<int:num>', methods=['POST'])
def pick_number(num):
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    conn = sqlite3.connect('empire_v2.db')
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
    balance = cursor.fetchone()[0]
    cursor.execute("SELECT status, owner FROM game_board WHERE number=?", (num,))
    row = cursor.fetchone()
    if row:
        status, owner = row[0], row[1]
        if status == 'available':
            cursor.execute("SELECT COUNT(*) FROM game_board WHERE owner=?", (username,))
            if cursor.fetchone()[0] < 36 and balance >= 2:
                cursor.execute("UPDATE game_board SET status='locked', owner=? WHERE number=?", (username, num))
                cursor.execute("UPDATE users SET balance = balance - 2 WHERE username=?", (username,))
                cursor.execute("UPDATE financial_stats SET total_collected = total_collected + 2.0 WHERE game_name=?", ("لوحة أرقام الحظ (80$)",))
                conn.commit()
        elif status == 'locked' and owner == username:
            cursor.execute("UPDATE game_board SET status='available', owner=NULL WHERE number=?", (num,))
            cursor.execute("UPDATE users SET balance = balance + 2 WHERE username=?", (username,))
            cursor.execute("UPDATE financial_stats SET total_collected = total_collected - 2.0 WHERE game_name=?", ("لوحة أرقام الحظ (80$)",))
            conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/pick_game_three/<int:slot_id>', methods=['POST'])
def pick_game_three(slot_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    conn = sqlite3.connect('empire_v2.db')
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
    balance = cursor.fetchone()[0]
    cursor.execute("SELECT status, owner FROM game_three WHERE slot_id=?", (slot_id,))
    row = cursor.fetchone()
    if row:
        status, owner = row[0], row[1]
        if status == 'available' and balance >= 50.0:
            cursor.execute("UPDATE game_three SET status='locked', owner=? WHERE slot_id=?", (username, slot_id))
            cursor.execute("UPDATE users SET balance = balance - 50.0 WHERE username=?", (username,))
            cursor.execute("UPDATE financial_stats SET total_collected = total_collected + 50.0 WHERE game_name=?", ("اللعبة الملكية الفاخرة",))
            conn.commit()
        elif status == 'locked' and owner == username:
            cursor.execute("UPDATE game_three SET status='available', owner=NULL WHERE slot_id=?", (slot_id,))
            cursor.execute("UPDATE users SET balance = balance + 50.0 WHERE username=?", (username,))
            cursor.execute("UPDATE financial_stats SET total_collected = total_collected - 50.0 WHERE game_name=?", ("اللعبة الملكية الفاخرة",))
            conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/create_user', methods=['POST'])
def create_user():
    if 'username' not in session or session.get('role') != 'admin':
        return "غير مسموح", 403
    new_user = request.form.get('new_user', '').strip()
    new_pass = request.form.get('new_pass', '').strip()
    role = request.form.get('account_role', 'class_b')
    conn = sqlite3.connect('empire_v2.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password, balance, role, created_by) VALUES (?, ?, 0, ?, ?)",
                       (new_user, new_pass, role, session['username']))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/recharge_user', methods=['POST'])
def recharge_user():
    if 'username' not in session or session.get('role') != 'admin':
        return "غير مسموح", 403
    conn = sqlite3.connect('empire_v2.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE username=?", (float(request.form['amount']), request.form['target_user']))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/withdraw_user', methods=['POST'])
def withdraw_user():
    if 'username' not in session or session.get('role') != 'admin':
        return "غير مسموح", 403
    target_user = request.form['target_user']
    amount = float(request.form['amount'])
    conn = sqlite3.connect('empire_v2.db')
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE username=?", (target_user,))
    res = cursor.fetchone()
    if res and res[0] >= amount:
        cursor.execute("UPDATE users SET balance = balance - ? WHERE username=?", (amount, target_user))
        cursor.execute("UPDATE users SET balance = balance + ? WHERE username='admin'", (amount,))
        conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

DASHBOARD_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>إمبراطورية الأرقام والجوائز الكبرى</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #1e293b; padding: 15px 25px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); flex-wrap: wrap; gap: 10px; border-bottom: 2px solid #fbbf24; }
        .logo-area { display: flex; align-items: center; gap: 15px; flex-wrap: wrap; }
        .logo-area h1 { margin: 0; color: #fbbf24; font-size: 24px; }
        .user-creds { background: #334155; padding: 6px 12px; border-radius: 6px; font-size: 14px; color: #cbd5e1; border: 1px dashed #fbbf24; }
        .balance-badge { background: #065f46; color: #34d399; padding: 8px 15px; border-radius: 8px; font-weight: bold; font-size: 18px; border: 1px solid #10b981; }
        .whatsapp-btn { background: #25d366; color: white; padding: 8px 15px; text-decoration: none; border-radius: 8px; font-weight: bold; }
        .refresh-btn { background: #3b82f6; color: white; padding: 8px 15px; text-decoration: none; border-radius: 8px; font-weight: bold; border: none; cursor: pointer; }
        .logout-btn { background: #ef4444; color: white; padding: 8px 15px; text-decoration: none; border-radius: 8px; font-weight: bold; border: none; cursor: pointer; }
        .admin-link-btn { background: #fbbf24; color: black; padding: 8px 15px; text-decoration: none; border-radius: 8px; font-weight: bold; }
        .main-container { margin-top: 20px; display: grid; grid-template-columns: 3fr 1fr; gap: 20px; }
        @media (max-width: 1100px) { .main-container { grid-template-columns: 1fr; } }
        .luxury-game-section { background: linear-gradient(135deg, #1e1b4b, #31103d, #0f172a); border: 3px solid #fbbf24; padding: 25px; border-radius: 16px; text-align: center; }
        .luxury-game-section h2 { color: #fbbf24; margin-top: 0; font-size: 26px; }
        .luxury-slots-container { display: flex; justify-content: center; gap: 15px; margin: 20px 0; flex-wrap: wrap; }
        .luxury-slot-form { display: flex; }
        .luxury-slot-btn { background: linear-gradient(145deg, #111827, #1f2937); border: 2px solid #fbbf24; width: 110px; height: 110px; border-radius: 14px; color: #fff; font-size: 20px; font-weight: bold; cursor: pointer; display: flex; flex-direction: column; align-items: center; justify-content: center; }
        .luxury-slot-btn.locked { background: linear-gradient(145deg, #991b1b, #7f1d1d); border-color: #f87171; }
        .luxury-owner { font-size: 11px; color: #fde047; margin-top: 6px; max-width: 90px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .board-section { background: linear-gradient(135deg, #d4af37, #aa771c); padding: 20px; border-radius: 12px; }
        .board-section h2 { color: #111; margin-top: 0; }
        .player-summary-box { background: #0f172a; border: 2px dashed #111; padding: 12px 15px; border-radius: 8px; margin-bottom: 15px; color: #f8fafc; display: flex; justify-content: space-around; flex-wrap: wrap; gap: 10px; font-size: 14px; font-weight: bold; }
        .summary-item { background: #1e293b; padding: 6px 12px; border-radius: 6px; border: 1px solid #475569; }
        .board { display: grid; grid-template-columns: repeat(10, 1fr); gap: 6px; margin-top: 15px; }
        .cell-form { display: flex; }
        .cell { background: #000; border: 1px solid #ffd700; width: 100%; height: 60px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 15px; font-weight: bold; color: #fff; border-radius: 6px; cursor: pointer; padding: 0; box-sizing: border-box; }
        .cell.locked { background: #ef4444; border-color: #b91c1c; }
        .owner-tag { font-size: 9px; display: block; color: #fde047; margin-top: 2px; max-width: 90%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .winners-sidebar { background: #1e293b; border: 2px solid #fbbf24; padding: 15px; border-radius: 12px; height: fit-content; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        .winners-sidebar h3 { color: #fbbf24; margin-top: 0; text-align: center; font-size: 18px; border-bottom: 1px solid #475569; padding-bottom: 10px; }
        .winner-record-item { background: #0f172a; padding: 10px; border-radius: 6px; margin-bottom: 10px; border-right: 4px solid #10b981; font-size: 13px; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo-area">
            <h1>👑 إمبراطورية الأرقام والجوائز الكبرى</h1>
            <div class="user-creds">👤 مستخدمك: <b>{{ username }}</b> | 🔑 الباسورد: <b>{{ password }}</b></div>
            <div class="balance-badge">رصيدك: ${{ balance }}</div>
        </div>
        <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
            <a class="whatsapp-btn" href="https://wa.me/?text=الرجاء%20منكم%20شحن%20رصيد%20حسابي%20بلعبة%20امبراطورية%20الارقام%20باسم%20المستخدم:%20{{ username }}" target="_blank">💬 اشحن عبر واتساب</a>
            {% if role == 'admin' %}
            <a href="/admin_panel" class="admin-link-btn">👑 لوحة تحكم الأدمن المستقلة</a>
            {% endif %}
            <button class="refresh-btn" onclick="location.reload();">🔄 تحديث</button>
            <a href="/logout" class="logout-btn">🚪 خروج</a>
        </div>
    </div>

    <div class="main-container">
        <div>
            <div class="luxury-game-section">
                <h2>💎 اللعبة الملكية الفاخرة (5 أرقام كبرى)</h2>
                <p style="color: #cbd5e1; font-size: 14px;">قيمة الرقم الواحد: 50$ | الجائزة الكبرى: 250$ فورية!</p>
                <div class="luxury-slots-container">
                    {% for slot_id, status, owner in game_three_slots %}
                    <form action="/pick_game_three/{{ slot_id }}" method="POST" class="luxury-slot-form">
                        <button type="submit" class="luxury-slot-btn {% if status == 'locked' %}locked{% endif %}">
                            <span style="font-size: 22px;">رقم {{ slot_id }}</span>
                            <span style="font-size: 11px; color: #38bdf8; margin-top: 4px;">50$</span>
                            {% if owner %}
                                <span class="luxury-owner">{{ owner }}</span>
                                {% if owner == username %}<span style="font-size: 9px; color: #34d399;">(حجزك)</span>{% endif %}
                            {% endif %}
                        </button>
                    </form>
                    {% endfor %}
                </div>
            </div>

            <div class="games-grid">
                <div class="board-section">
                    <h2>لوحة أرقام الحظ (تكلفة الرقم: 2$ | الجائزة: 80$)</h2>
                    <div class="player-summary-box">
                        <div class="summary-item">🎯 أرقامك: <span style="color: #fbbf24;">{% if user_locked_numbers %}{{ user_locked_numbers | join(', ') }}{% else %}لا توجد{% endif %}</span></div>
                        <div class="summary-item">💵 المدفوع: <span style="color: #ef4444;">${{ user_total_spent }}</span></div>
                    </div>
                    <div class="board">
                        {% for num, status, owner in board %}
                            <form action="/pick_number/{{ num }}" method="POST" class="cell-form">
                                <button type="submit" class="cell {% if status == 'locked' %}locked{% endif %}">
                                    <span style="font-size: 15px;">{{ num }}</span>
                                    {% if owner %}
                                        <span class="owner-tag">{{ owner }}</span>
                                    {% endif %}
                                </button>
                            </form>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>

        <div class="winners-sidebar">
            <h3>🏆 لوحة شرف الفائزين</h3>
            {% if winners_records %}
                {% for game, info, time_str in winners_records %}
                <div class="winner-record-item">
                    <div style="color: #fbbf24; font-weight: bold;">{{ game }}</div>
                    <div style="color: #e2e8f0; margin-top: 3px;">{{ info }}</div>
                </div>
                {% endfor %}
            {% else %}
                <p style="color: #94a3b8; text-align: center; font-size: 13px;">لا توجد سجلات فوز!</p>
            {% endif %}
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
    <title>لوحة تحكم الأدمن</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; padding: 20px; margin: 0; }
        .admin-header { display: flex; justify-content: space-between; align-items: center; background: #1e293b; padding: 15px 25px; border-radius: 12px; border: 2px solid #fbbf24; margin-bottom: 25px; flex-wrap: wrap; gap: 10px; }
        .admin-panel { background: #1e293b; padding: 25px; border-radius: 12px; border: 2px solid #fbbf24; max-width: 900px; margin: 0 auto; }
        input, select { width: 100%; padding: 10px; border-radius: 6px; background: #1e293b; color: white; border: 1px solid #475569; box-sizing: border-box; }
        button { padding: 10px 20px; font-weight: bold; border: none; border-radius: 6px; cursor: pointer; }
        .back-btn { background: #3b82f6; color: white; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="admin-header">
        <h2 style="color: #fbbf24; margin: 0;">👑 لوحة تحكم الأدمن</h2>
        <div>
            <a href="/dashboard" class="back-btn">⬅️ العودة للعبة</a>
            <a href="/logout" style="background: #ef4444; color: white; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold;">🚪 خروج</a>
        </div>
    </div>
    <div class="admin-panel">
        <h3 style="color: #38bdf8;">📊 التقارير المالية الشهرية</h3>
        {% for row in financial_report %}
        <div style="background: #111827; padding: 10px; border-radius: 6px; margin-bottom: 10px;">
            <b>{{ row.name }}</b> - المدفوع: ${{ row.collected }} | الجوائز: ${{ row.payouts }} | الصافي: ${{ row.net }}
        </div>
        {% endfor %}
        <h3 style="color: #34d399;">💎 صافي الربح الإجمالي: ${{ total_net_profit }}</h3>
    </div>
</body>
</html>
"""

LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>تسجيل الدخول - إمبراطورية الأرقام</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-box { background: #1e293b; padding: 40px; border-radius: 12px; box-shadow: 0 8px 16px rgba(0,0,0,0.5); width: 320px; text-align: center; border: 1px solid #334155; }
        input { width: 100%; padding: 12px; margin: 10px 0; border-radius: 6px; border: 1px solid #475569; background: #334155; color: white; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #fbbf24; color: black; font-weight: bold; border: none; border-radius: 6px; cursor: pointer; margin-top: 10px; font-size: 16px; }
        .error { color: #ef4444; margin-bottom: 12px; font-weight: bold; background: rgba(239,68,68,0.2); padding: 8px; border-radius: 6px; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2 style="color: #fbbf24; margin-top: 0;">👑 امبراطورية الأرقام</h2>
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
