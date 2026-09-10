from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import sqlite3
import random
import time
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
app.secret_key = 'empire_lira_platforms_2026'

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
        CREATE TABLE IF NOT EXISTS royal_game_board (
            slot_id INTEGER PRIMARY KEY,
            status TEXT DEFAULT 'available',
            owner TEXT DEFAULT NULL
        )
    ''')
    cursor.execute('SELECT COUNT(*) FROM royal_game_board')
    if cursor.fetchone()[0] == 0:
        for i in range(1, 6):
            cursor.execute('INSERT INTO royal_game_board (slot_id, status) VALUES (?, ?)', (i, 'available'))

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS royal_game_state (
            id INTEGER PRIMARY KEY,
            is_full INTEGER DEFAULT 0,
            timer_end REAL DEFAULT 0,
            winning_number INTEGER DEFAULT 0,
            last_winner_msg TEXT DEFAULT '',
            banner_end_time REAL DEFAULT 0,
            forced_admin_slot TEXT DEFAULT ''
        )
    ''')
    try:
        cursor.execute("ALTER TABLE royal_game_state ADD COLUMN winning_number INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    cursor.execute('SELECT COUNT(*) FROM royal_game_state')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO royal_game_state (id, is_full, timer_end, winning_number, last_winner_msg, banner_end_time, forced_admin_slot) VALUES (1, 0, 0, 0, "بانتظار اكتمال الأرقام الملكية الفاخرة...", 0, "")')

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
    
    games_list = ["👑 اللعبة الملكية الفاخرة (200$)", "🎰 روليت الكازينو العالمي"]
    for g in games_list:
        cursor.execute("INSERT OR IGNORE INTO financial_stats (game_name, total_collected, total_payouts) VALUES (?, 0, 0)", (g,))
    
    cursor.execute("SELECT * FROM users WHERE username='admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, balance, role, created_by) VALUES (?, ?, ?, ?, ?)", 
                       ('admin', 'admin123', 1000000.0, 'admin', 'system'))

    for i in range(1, 101):
        uname = f"user{i}"
        cursor.execute("SELECT * FROM users WHERE username=?", (uname,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (username, password, balance, role, created_by) VALUES (?, ?, 0, 'class_b', 'admin')", 
                           (uname, f"us11${random.randint(100, 999)}"))

    conn.commit()
    conn.close()

init_db()

def check_and_auto_draw_royal_game():
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT is_full, timer_end, forced_admin_slot FROM royal_game_state WHERE id=1")
    state = cursor.fetchone()
    if state and state[0] == 1:
        timer_end = state[1]
        forced_slot = state[2]
        if time.time() >= timer_end:
            winning_slot, winner_owner = None, None
            if forced_slot and forced_slot.isdigit():
                winning_slot = int(forced_slot)
                cursor.execute("SELECT owner FROM royal_game_board WHERE slot_id=?", (winning_slot,))
                res = cursor.fetchone()
                winner_owner = res[0] if (res and res[0]) else None
            else:
                cursor.execute("SELECT slot_id, owner FROM royal_game_board WHERE status='locked'")
                locked_slots = cursor.fetchall()
                if locked_slots:
                    winning_slot, winner_owner = random.choice(locked_slots)
                else:
                    winning_slot = random.randint(1, 5)
                    
            if winning_slot:
                banner_end_time = time.time() + 35
                if winner_owner:
                    cursor.execute("UPDATE users SET balance = balance + 200.0 WHERE username=?", (winner_owner,))
                    msg = f"🎉 مبروك للفائز {winner_owner} - ربح الرقم {winning_slot} جائزة 200$!"
                    cursor.execute("INSERT INTO winners_log (game_name, winner_info, win_time) VALUES (?, ?, ?)", 
                                   ("👑 اللعبة الملكية الفاخرة (200$)", f"الخانة {winning_slot} - الفائز: {winner_owner} (200$)", time.strftime('%Y-%m-%d %H:%M')))
                    cursor.execute("UPDATE financial_stats SET total_payouts = total_payouts + 200.0 WHERE game_name=?", ("👑 اللعبة الملكية الفاخرة (200$)",))
                else:
                    msg = f"💎 انتهى السحب على الرقم {winning_slot} (ولم يكن محجوزاً)."
                
                cursor.execute("UPDATE royal_game_board SET status='available', owner=NULL")
                cursor.execute("UPDATE royal_game_state SET is_full=0, timer_end=0, winning_number=?, last_winner_msg=?, banner_end_time=?, forced_admin_slot='' WHERE id=1", (winning_slot, msg, banner_end_time))
                conn.commit()
    conn.close()

@app.route('/manifest.json')
def manifest():
    manifest_data = {
        "name": "منصة Lira والألعاب الملكية",
        "short_name": "Lira App",
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

@app.route('/api/sync_royal')
def api_sync_royal():
    if 'username' not in session:
        return jsonify({'error': 'unauthorized'})
    check_and_auto_draw_royal_game()
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("SELECT balance FROM users WHERE username=?", (session['username'],))
    balance = cursor.fetchone()[0]

    cursor.execute("SELECT slot_id, status, owner FROM royal_game_board")
    royal_slots = cursor.fetchall()

    cursor.execute("SELECT is_full, timer_end, winning_number, last_winner_msg FROM royal_game_state WHERE id=1")
    state = cursor.fetchone()
    conn.close()
    
    return jsonify({
        'balance': balance,
        'royal_slots': royal_slots,
        'is_full': state[0],
        'timer_end': state[1],
        'rem': max(0, int(state[1] - time.time())) if state[0] else 0,
        'winning_number': state[2],
        'msg': state[3]
    })

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

@app.route('/royal_game_page')
def royal_game_page():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE username=?", (session['username'],))
    balance = cursor.fetchone()[0]
    conn.close()
    return render_template_string(ROYAL_GAME_PAGE, username=session['username'], balance=balance)

@app.route('/pick_royal_slot/<int:slot_id>', methods=['POST'])
def pick_royal_slot(slot_id):
    if 'username' not in session:
        return jsonify({'success': False})
    username = session['username']
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
    balance = cursor.fetchone()[0]
    
    cursor.execute("SELECT status, owner FROM royal_game_board WHERE slot_id=?", (slot_id,))
    row = cursor.fetchone()
    if row:
        status, owner = row[0], row[1]
        if status == 'available':
            if balance >= 50.0:
                cursor.execute("UPDATE royal_game_board SET status='locked', owner=? WHERE slot_id=?", (username, slot_id))
                cursor.execute("UPDATE users SET balance = balance - 50.0 WHERE username=?", (username,))
                cursor.execute("UPDATE financial_stats SET total_collected = total_collected + 50.0 WHERE game_name=?", ("👑 اللعبة الملكية الفاخرة (200$)",))
                conn.commit()
                
                cursor.execute("SELECT COUNT(*) FROM royal_game_board WHERE status='available'")
                if cursor.fetchone()[0] == 0:
                    timer_end = time.time() + 30 # عد تنازلي دقيق بـ 30 ثانية
                    winning_slot = random.randint(1, 5)
                    cursor.execute("UPDATE royal_game_state SET is_full=1, timer_end=?, winning_number=?, last_winner_msg=? WHERE id=1", 
                                   (timer_end, winning_slot, "⚠️ اكتملت الأرقام! يبدأ العد التنازلي للسحب..."))
                    conn.commit()
            else:
                conn.close()
                return jsonify({'success': False, 'msg': 'رصيدك لا يكفي (تكلفة الحجز 50$)!'})
        elif status == 'locked' and owner == username:
            # التراجع المباشر من صاحب الحساب لنفسه واسترداد الـ 50$
            cursor.execute("UPDATE royal_game_board SET status='available', owner=NULL WHERE slot_id=?", (slot_id,))
            cursor.execute("UPDATE users SET balance = balance + 50.0 WHERE username=?", (username,))
            cursor.execute("UPDATE financial_stats SET total_collected = total_collected - 50.0 WHERE game_name=?", ("👑 اللعبة الملكية الفاخرة (200$)",))
            cursor.execute("UPDATE royal_game_state SET is_full=0, timer_end=0, last_winner_msg=? WHERE id=1", 
                           ("قام اللاعب بالتراجع عن رهانه واسترد رصيده.",))
            conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/roulette_page')
def roulette_page():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE username=?", (session['username'],))
    balance = cursor.fetchone()[0]
    conn.close()
    return render_template_string(ROULETTE_PAGE, username=session['username'], balance=balance)

@app.route('/spin_roulette_api', methods=['POST'])
def spin_roulette_api():
    if 'username' not in session:
        return jsonify({'success': False, 'msg': 'غير مسجل الدخول'})
    username = session['username']
    data = request.json
    bet_type = data.get('type')
    bet_value = data.get('value')
    bet_amount = float(data.get('amount', 25.0))
    
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
    balance = cursor.fetchone()[0]
    
    if balance < bet_amount:
        conn.close()
        return jsonify({'success': False, 'msg': 'رصيدك لا يكفي للمراهنة!'})
        
    cursor.execute("UPDATE users SET balance = balance - ? WHERE username=?", (bet_amount, username))
    cursor.execute("UPDATE financial_stats SET total_collected = total_collected + ? WHERE game_name=?", (bet_amount, "🎰 روليت الكازينو العالمي"))
    
    winning_num = random.randint(0, 36)
    red_numbers = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
    
    if winning_num == 0:
        winning_color = 'green'
    elif winning_num in red_numbers:
        winning_color = 'red'
    else:
        winning_color = 'black'
        
    won = False
    payout = 0
    
    if bet_type == 'color':
        if bet_value == winning_color:
            won = True
            payout = bet_amount * 2
    elif bet_type == 'parity':
        if winning_num != 0:
            is_even = (winning_num % 2 == 0)
            if (bet_value == 'even' and is_even) or (bet_value == 'odd' and not is_even):
                won = True
                payout = bet_amount * 2
    elif bet_type == 'number':
        if int(bet_value) == winning_num:
            won = True
            payout = bet_amount * 35
            
    if won:
        cursor.execute("UPDATE users SET balance = balance + ? WHERE username=?", (payout, username))
        cursor.execute("UPDATE financial_stats SET total_payouts = total_payouts + ? WHERE game_name=?", (payout, "🎰 روليت الكازينو العالمي"))
        cursor.execute("INSERT INTO winners_log (game_name, winner_info, win_time) VALUES (?, ?, ?)", 
                       ("🎰 روليت الكازينو العالمي", f"الفائز {username} ربح ${payout} (الرقم {winning_num})", time.strftime('%Y-%m-%d %H:%M')))
                       
    conn.commit()
    cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
    new_balance = cursor.fetchone()[0]
    conn.close()
    
    return jsonify({
        'success': True,
        'winning_number': winning_num,
        'winning_color': winning_color,
        'won': won,
        'payout': payout,
        'new_balance': new_balance
    })

@app.route('/admin_panel')
def admin_panel():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('dashboard'))
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
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
        financial_report.append({'name': name, 'collected': collected, 'payouts': payouts, 'net': net})
    cursor.execute("SELECT forced_admin_slot FROM royal_game_state WHERE id=1")
    f_slot = cursor.fetchone()[0]
    conn.close()
    return render_template_string(ADMIN_PAGE, username=session['username'], all_users=all_users, financial_report=financial_report, total_net_profit=total_net_profit, f_slot=f_slot)

@app.route('/admin_set_forced', methods=['POST'])
def admin_set_forced():
    if 'username' not in session or session.get('role') != 'admin':
        return "غير مسموح", 403
    f_slot = request.form.get('forced_slot', '').strip()
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("UPDATE royal_game_state SET forced_admin_slot=? WHERE id=1", (f_slot,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/recharge_user', methods=['POST'])
def recharge_user():
    if 'username' not in session or session.get('role') != 'admin':
        return "غير مسموح", 403
    amt = float(request.form['amount'])
    t_user = request.form['target_user']
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance - ? WHERE username='admin'", (amt,))
    cursor.execute("UPDATE users SET balance = balance + ? WHERE username=?", (amt, t_user))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/withdraw_user', methods=['POST'])
def withdraw_user():
    if 'username' not in session or session.get('role') != 'admin':
        return "غير مسموح", 403
    t_user = request.form['target_user']
    amount = float(request.form['amount'])
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE username=?", (t_user,))
    res = cursor.fetchone()
    if res and res[0] >= amount:
        cursor.execute("UPDATE users SET balance = balance - ? WHERE username=?", (amount, t_user))
        cursor.execute("UPDATE users SET balance = balance + ? WHERE username='admin'", (amount,))
        conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/change_password', methods=['POST'])
def change_password():
    if 'username' not in session or session.get('role') != 'admin':
        return "غير مسموح", 403
    t_user = request.form['target_user']
    new_pass = request.form['new_password'].strip()
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password=? WHERE username=?", (new_pass, t_user))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

DASHBOARD_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>منصة Lira - لوحة التحكم والألعاب</title>
    <link rel="manifest" href="/manifest.json">
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); flex-wrap: wrap; gap: 10px; border-bottom: 2px solid #ffd700; }
        .logo-area { display: flex; align-items: center; gap: 15px; flex-wrap: wrap; }
        .logo-img { width: 45px; height: 45px; }
        .logo-area h1 { margin: 0; color: #ffd700; font-size: 24px; }
        .user-creds { background: #1f1f1f; padding: 6px 12px; border-radius: 6px; font-size: 14px; color: #cbd5e1; border: 1px dashed #ffd700; }
        .balance-badge { background: #065f46; color: #34d399; padding: 8px 15px; border-radius: 8px; font-weight: bold; font-size: 18px; border: 1px solid #10b981; }
        .whatsapp-btn { background: #25d366; color: white; padding: 8px 15px; text-decoration: none; border-radius: 8px; font-weight: bold; }
        .refresh-btn { background: #3b82f6; color: white; padding: 8px 15px; text-decoration: none; border-radius: 8px; font-weight: bold; border: none; cursor: pointer; }
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
            <img src="https://img.icons8.com/color/512/crown.png" alt="Logo" class="logo-img">
            <h1>منصة Lira الفاخرة</h1>
            <div class="user-creds">👤 <b>{{ username }}</b> {% if role == 'admin' %} | 🔑 <b>{{ role }}</b>{% endif %}</div>
            <div class="balance-badge">الرصيد: <span id="userBalanceBadge">${{ balance }}</span></div>
        </div>
        <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
            <a class="whatsapp-btn" href="https://wa.me/96176030208?text=الرجاء%20شحن%20رصيد%20حسابي%20بمنصة%20Lira%20باسم%20المستخدم:%20{{ username }}" target="_blank">💬 شراء رصيد (واتساب)</a>
            {% if role == 'admin' %}<a href="/admin_panel" class="admin-link-btn">👑 لوحة الأدمن</a>{% endif %}
            <button class="refresh-btn" onclick="location.reload();">🔄 تحديث</button>
            <a href="/logout" class="logout-btn">🚪 خروج</a>
        </div>
    </div>

    <div class="icons-grid">
        <a href="/royal_game_page" class="icon-card">
            <div class="icon-logo">👑</div>
            <div class="icon-title">اللعبة الملكية (3D)</div>
        </a>
        <a href="/roulette_page" class="icon-card">
            <div class="icon-logo">🎰</div>
            <div class="icon-title">روليت الكازينو الملكي</div>
        </a>
        <div class="icon-card" onclick="alert('لعبة قيد التفعيل قريباً')">
            <div class="icon-logo">⚡</div>
            <div class="icon-title">لعبة الحظ السريع</div>
        </div>
        <div class="icon-card" onclick="alert('لعبة قيد التفعيل قريباً')">
            <div class="icon-logo">🏇</div>
            <div class="icon-title">سباق الخيل التفاعلي</div>
        </div>
        <div class="icon-card" onclick="alert('لعبة قيد التفعيل قريباً')">
            <div class="icon-logo">🎡</div>
            <div class="icon-title">عجلة الثروة الكبرى</div>
        </div>
        <div class="icon-card" onclick="alert('لعبة قيد التفعيل قريباً')">
            <div class="icon-logo">🎁</div>
            <div class="icon-title">صناديق المفاجآت الذهبية</div>
        </div>
        <div class="icon-card" onclick="alert('لعبة قيد التفعيل قريباً')">
            <div class="icon-logo">🔢</div>
            <div class="icon-title">تحدي الأرقام الفائزة</div>
        </div>
        <div class="icon-card" onclick="alert('لعبة قيد التفعيل قريباً')">
            <div class="icon-logo">🃏</div>
            <div class="icon-title">البوكر الملكي المباشر</div>
        </div>
    </div>
</body>
</html>
"""

ROYAL_GAME_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>اللعبة الملكية - منصة Lira</title>
    <link rel="manifest" href="/manifest.json">
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 12px; border-bottom: 2px solid #ffd700; }
        .back-btn { background: #3b82f6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block; margin-bottom: 20px; }
        
        .royal-box { background: linear-gradient(135deg, #181818, #262626); border: 3px solid #ffd700; padding: 30px; border-radius: 20px; max-width: 850px; margin: 0 auto; text-align: center; }
        .slots-container { display: flex; justify-content: center; gap: 20px; margin: 30px 0; flex-wrap: wrap; }
        .slot-btn { background: #252525; border: 3px solid #ffd700; width: 120px; height: 120px; border-radius: 16px; color: #ffd700; font-size: 26px; font-weight: bold; cursor: pointer; display: flex; flex-direction: column; align-items: center; justify-content: center; transition: 0.2s; position: relative; }
        .slot-btn.locked { background: #006400; border-color: #00ff00; color: #fff; box-shadow: 0 0 15px rgba(0,255,0,0.5); }
        .owner-tag { font-size: 11px; color: #ffcc00; margin-top: 4px; max-width: 100px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

        /* شريط العد التنازلي الواضح والفاخر */
        .countdown-banner { background: linear-gradient(90deg, #991b1b, #b91c1c, #991b1b); border: 2px solid #ef4444; color: #fff; padding: 15px; border-radius: 12px; font-size: 20px; font-weight: bold; margin-bottom: 20px; box-shadow: 0 0 20px rgba(239,68,68,0.7); display: none; text-align: center; }

        /* عجلة الحظ الدائرية والنقطة الثابتة */
        .wheel-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.92); display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 9999; }
        .wheel-outer { position: relative; width: 260px; height: 260px; border-radius: 50%; border: 8px solid #ffd700; background: #111; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 50px rgba(255,215,0,0.8); }
        .pointer-dot { position: absolute; top: -20px; width: 0; height: 0; border-left: 12px solid transparent; border-right: 12px solid transparent; border-top: 25px solid #ef4444; z-index: 20; filter: drop-shadow(0 0 5px #ef4444); }
        .spinning-wheel-text { font-size: 50px; font-weight: bold; color: #ffd700; animation: spinAnim 0.3s infinite linear; }
        @keyframes spinAnim { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

        /* نافذة الفوز المذهبة والمنبثقة */
        .win-popup { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.88); display: flex; align-items: center; justify-content: center; z-index: 10000; }
        .win-card { background: linear-gradient(135deg, #1f1f1f, #332700); border: 4px solid #ffd700; padding: 40px; border-radius: 20px; text-align: center; box-shadow: 0 0 70px rgba(255,215,0,0.95); width: 420px; animation: popUp 0.4s ease-out; }
        @keyframes popUp { 0% { transform: scale(0.5); opacity: 0; } 100% { transform: scale(1); opacity: 1; } }
    </style>
    <script>
        const currentUser = "{{ username }}";

        function pickSlot(slotId, status, owner) {
            if (status === 'locked' && owner === currentUser) {
                if(!confirm("هل تريد حقاً التراجع عن حجز هذا الرقم واسترداد مبلغ 50$ إلى رصيدك؟")) return;
            }
            fetch('/pick_royal_slot/' + slotId, { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    if(!data.success && data.msg) alert(data.msg);
                    syncRoyal();
                });
        }

        function syncRoyal() {
            fetch('/api/sync_royal')
                .then(res => res.json())
                .then(data => {
                    if(data.error) return;
                    document.getElementById('userBalanceBadge').innerText = '$' + data.balance;

                    let html = '';
                    data.royal_slots.forEach(slot => {
                        let sId = slot[0], status = slot[1], owner = slot[2];
                        let lockedCls = status === 'locked' ? 'locked' : '';
                        let ownerTag = owner ? `<span class="owner-tag">👤 ${owner}</span>` : '<span style="font-size:11px; color:#38bdf8;">متاح 50$</span>';
                        let actionTitle = (status === 'locked' && owner === currentUser) ? 'اضغط للتراجع واسترداد الـ 50$' : 'اختر الرقم';
                        
                        html += `<button type="button" title="${actionTitle}" onclick="pickSlot(${sId}, '${status}', '${owner}')" class="slot-btn ${lockedCls}">
                                    <span>${sId}</span>
                                    ${ownerTag}
                                 </button>`;
                    });
                    document.getElementById('slotsContainer').innerHTML = html;

                    const countBanner = document.getElementById('countdownBanner');
                    const wheel = document.getElementById('wheelOverlay');
                    const winModal = document.getElementById('winModal');

                    if(data.is_full) {
                        countBanner.style.display = 'block';
                        document.getElementById('remTimerText').innerText = data.rem;
                        wheel.style.display = 'flex';
                        let rndNum = Math.floor(Math.random() * 5) + 1;
                        document.getElementById('spinningDigit').innerText = rndNum;
                    } else {
                        countBanner.style.display = 'none';
                        wheel.style.display = 'none';
                        if(data.winning_number > 0 && data.rem > 0) {
                            winModal.style.display = 'flex';
                            document.getElementById('winningNumText').innerText = data.winning_number;
                        } else {
                            winModal.style.display = 'none';
                        }
                    }
                });
        }
        setInterval(syncRoyal, 1500);
    </script>
</head>
<body>
    <div class="header">
        <h2 style="color: #ffd700; margin: 0;">👑 اللعبة الملكية الحصرية (3D)</h2>
        <div><span class="balance-badge" style="background:#065f46; color:#34d399; padding:8px 15px; border-radius:8px; font-weight:bold;">الرصيد: <span id="userBalanceBadge">${{ balance }}</span></span></div>
    </div>
    
    <div style="max-width: 850px; margin: 20px auto;">
        <a href="/dashboard" class="back-btn">⬅ العودة للوحة التحكم الرئيسية</a>
    </div>

    <!-- عجلة الحظ الدائرية والنقطة الثابتة الحمراء -->
    <div id="wheelOverlay" class="wheel-overlay" style="display: none;">
        <div style="color: #ffd700; font-size: 26px; font-weight: bold; margin-bottom: 25px; text-shadow: 0 0 10px #ffd700;">🎡 العجلة تدور بوضوح.. انتظر الرقم الرابح تحت السهم!</div>
        <div class="wheel-outer">
            <div class="pointer-dot"></div>
            <div id="spinningDigit" class="spinning-wheel-text">7</div>
        </div>
        <div style="color: #38bdf8; font-size: 18px; margin-top: 25px;">جاري سحب الجائزة الكبرى (200$)...</div>
    </div>

    <!-- نافذة الفوز الفخمة والمنبثقة -->
    <div id="winModal" class="win-popup" style="display: none;">
        <div class="win-card">
            <div style="font-size: 55px; margin-bottom: 10px;">🎉</div>
            <h2 style="color: #ffd700; margin: 0; font-size: 32px; text-shadow: 0 0 10px #ffd700;">مبروووك!</h2>
            <div style="font-size: 18px; color: #cbd5e1; margin-top: 10px;">الرقم الفائز:</div>
            <div id="winningNumText" style="font-size: 50px; font-weight: bold; color: #fff; margin: 5px 0;">3</div>
            <div style="font-size: 28px; font-weight: bold; color: #34d399; background: rgba(0,100,0,0.6); padding: 12px; border-radius: 10px; border: 2px solid #00ff00; box-shadow: 0 0 15px #00ff00;">200$</div>
            <p style="color: #38bdf8; font-size: 13px; margin-top: 15px;">تم تحويل جائزة الـ 200$ إلى رصيد الفائز مباشرة!</p>
        </div>
    </div>

    <div class="royal-box">
        <h2 style="color: #ffd700; margin-top: 0;">اختر رقمك الملكي (قيمة الحجز: 50$ | الجائزة: 200$)</h2>
        <p style="color: #cbd5e1; font-size: 14px; margin-bottom: 20px;">الرقم يُحجز لمرة واحدة فقط لشخص واحد، ويمكنك الضغط على رقمك المحجوز في أي وقت للتراجع واسترداد أموالك.</p>
        
        <!-- شريط العد التنازلي الفاخر (يظهر عند اكتمال الأرقام) -->
        <div id="countdownBanner" class="countdown-banner">
            ⏳ اكتملت الأرقام! سيتم السحب وإعلان الفائز خلال <span id="remTimerText" style="color: #ffd700; font-size: 24px;">30</span> ثانية!
        </div>

        <div id="slotsContainer" class="slots-container"></div>
    </div>
</body>
</html>
"""

ROULETTE_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>روليت الكازينو العالمي - منصة Lira</title>
    <link rel="manifest" href="/manifest.json">
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #071f14; color: #f8fafc; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #04120c; padding: 15px 25px; border-radius: 12px; border-bottom: 2px solid #ffd700; }
        .back-btn { background: #3b82f6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block; margin-bottom: 20px; }
        
        .roulette-arena { background: #0b2e1f; border: 4px solid #ffd700; padding: 30px; border-radius: 20px; max-width: 900px; margin: 0 auto; text-align: center; box-shadow: 0 0 50px rgba(0,0,0,0.9); }
        .wheel-screen { font-size: 24px; font-weight: bold; background: #04120c; padding: 25px; border-radius: 15px; border: 2px solid #ffd700; color: #fff; margin-bottom: 25px; box-shadow: inset 0 0 20px rgba(0,0,0,0.8); }
        
        .table-grid { display: grid; grid-template-columns: repeat(12, 1fr); gap: 6px; margin: 20px 0; }
        .r-cell { background: #111; border: 1px solid #ffd700; height: 50px; font-weight: bold; font-size: 16px; color: #fff; border-radius: 6px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
        .r-cell.red { background: #dc2626; }
        .r-cell.black { background: #1f2937; }
        .r-cell.green { background: #16a34a; }

        .bet-options { display: flex; justify-content: center; gap: 15px; flex-wrap: wheel; margin-top: 25px; }
        .casino-btn { padding: 12px 25px; font-size: 16px; font-weight: bold; border-radius: 8px; border: none; cursor: pointer; color: white; }
        .btn-red { background: #dc2626; }
        .btn-black { background: #1f2937; border: 1px solid #555; }
        .btn-green { background: #16a34a; }
    </style>
    <script>
        function playRoulette(type, val) {
            fetch('/spin_roulette_api', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({type: type, value: val, amount: 25.0})
            })
            .then(res => res.json())
            .then(data => {
                if(!data.success) {
                    alert(data.msg);
                    return;
                }
                const screen = document.getElementById('wheelScreen');
                screen.innerHTML = `🎡 تدور عجلة الروليت داخل الكازينو...`;
                setTimeout(() => {
                    let colName = data.winning_color === 'red' ? 'أحمر' : (data.winning_color === 'black' ? 'أسود' : 'أخضر (صفر الكازينو)');
                    screen.innerHTML = `🎯 استقرت الكرة على: الرقم ${data.winning_number} (${colName})<br>` +
                                       (data.won ? `<span style="color: #4ade80;">🎉 مبروك! ربحت $${data.payout}</span>` : `<span style="color: #f87171;">❌ هاردلك! خسر الرهان $25</span>`);
                    document.getElementById('userBalanceBadge').innerText = '$' + data.new_balance;
                }, 2000);
            });
        }
    </script>
</head>
<body>
    <div class="header">
        <h2 style="color: #ffd700; margin: 0;">🎰 طاولة روليت الكازينو العالمي المباشر</h2>
        <div><span style="background: #065f46; color: #34d399; padding: 8px 15px; border-radius: 8px; font-weight: bold;">الرصيد: <span id="userBalanceBadge">${{ balance }}</span></span></div>
    </div>
    
    <div style="max-width: 900px; margin: 20px auto;">
        <a href="/dashboard" class="back-btn">⬅ العودة للوحة التحكم الرئيسية</a>
    </div>

    <div class="roulette-arena">
        <div id="wheelScreen" class="wheel-screen">
            🎡 [ طاولة الروليت جاهزة ]<br>اختر نوع الرهان أو الرقم (قيمة الرهان: 25$)
        </div>

        <div style="color: #ffd700; font-weight: bold; margin-bottom: 10px;">اختر رهان الألوان أو الصفر:</div>
        <div class="bet-options">
            <button class="casino-btn btn-red" onclick="playRoulette('color', 'red')">رهان أحمر (x2)</button>
            <button class="casino-btn btn-black" onclick="playRoulette('color', 'black')">رهان أسود (x2)</button>
            <button class="casino-btn btn-green" onclick="playRoulette('number', 0)">رهان الصفر 0 (x35)</button>
        </div>

        <div style="color: #ffd700; font-weight: bold; margin: 25px 0 10px 0;">أو اختر رقماً مباشراً (ربح مضاعف x35):</div>
        <div class="table-grid">
            <script>
                for(let i=0; i<=36; i++) {
                    let c = (i === 0) ? 'green' : ([1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36].includes(i) ? 'red' : 'black');
                    document.write(`<div class="r-cell ${c}" onclick="playRoulette('number', ${i})">${i}</div>`);
                }
            </script>
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
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة تحكم الأدمن</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; padding: 20px; margin: 0; }
        .admin-header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 12px; border: 2px solid #ffd700; margin-bottom: 25px; }
        .admin-panel { background: #1f1f1f; padding: 25px; border-radius: 12px; border: 2px solid #ffd700; max-width: 950px; margin: 0 auto; }
        input, select { width: 100%; padding: 10px; border-radius: 6px; background: #252525; color: white; border: 1px solid #475569; box-sizing: border-box; }
        button { padding: 10px 20px; font-weight: bold; border: none; border-radius: 6px; cursor: pointer; }
        .back-btn { background: #3b82f6; color: white; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #475569; padding: 10px; text-align: center; }
        th { background: #252525; color: #ffd700; }
    </style>
</head>
<body>
    <div class="admin-header">
        <h2 style="color: #ffd700; margin: 0;">👑 لوحة تحكم الأدمن والتحقّم بالرصيد</h2>
        <div>
            <a href="/dashboard" class="back-btn">⬅️ العودة للمنصة</a>
            <a href="/logout" style="background: #ef4444; color: white; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold;">🚪 خروج</a>
        </div>
    </div>
    <div class="admin-panel">
        <h3 style="color: #38bdf8;">📊 التقارير المالية</h3>
        {% for row in financial_report %}
        <div style="background: #111827; padding: 10px; border-radius: 6px; margin-bottom: 10px;">
            <b>{{ row.name }}</b> - المدفوع: ${{ row.collected }} | الجوائز: ${{ row.payouts }} | الصافي: ${{ row.net }}
        </div>
        {% endfor %}
        <h3 style="color: #34d399;">💎 صافي الربح الإجمالي: ${{ total_net_profit }}</h3>

        <hr style="border-color: #475569; margin: 20px 0;">

        <h3 style="color: #ffd700;">🎯 التحكم المسبق بالرقم الموجه (اللعبة الملكية)</h3>
        <form action="/admin_set_forced" method="POST" style="margin-bottom: 25px;">
            <div style="background: #111827; padding: 15px; border-radius: 8px;">
                <label style="display:block; margin-bottom:5px; color:#38bdf8;">الخانة الفائزة باللعبة الملكية (1 إلى 5):</label>
                <input type="number" name="forced_slot" value="{{ f_slot }}" min="1" max="5" placeholder="عشوائية إن فارغة">
                <button type="submit" style="background: #ffd700; color: black; margin-top: 10px; width: 100%;">حفظ الخانة الموجهة</button>
            </div>
        </form>

        <hr style="border-color: #475569; margin: 20px 0;">

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 25px;">
            <form action="/recharge_user" method="POST" style="background: #111827; padding: 15px; border-radius: 8px;">
                <h4 style="color: #22c55e; margin-top:0;">⚡ شحن رصيد للحسابات:</h4>
                <select name="target_user" required style="margin-bottom: 10px;">
                    <option value="">اختر الحساب</option>
                    {% for u in all_users %}<option value="{{ u[0] }}">{{ u[0] }} (رصيده: ${{ u[2] }})</option>{% endfor %}
                </select>
                <input type="number" name="amount" placeholder="المبلغ ($)" required style="margin-bottom: 10px;">
                <button type="submit" style="background: #22c55e; color: black; width: 100%;">شحن الحساب</button>
            </form>

            <form action="/withdraw_user" method="POST" style="background: #111827; padding: 15px; border-radius: 8px;">
                <h4 style="color: #ef4444; margin-top:0;">💸 سحب رصيد من الحساب:</h4>
                <select name="target_user" required style="margin-bottom: 10px;">
                    <option value="">اختر الحساب</option>
                    {% for u in all_users %}{% if u[0] != 'admin' %}<option value="{{ u[0] }}">{{ u[0] }} (رصيده: ${{ u[2] }})</option>{% endif %}{% endfor %}
                </select>
                <input type="number" name="amount" placeholder="المبلغ ($)" required style="margin-bottom: 10px;">
                <button type="submit" style="background: #ef4444; color: white; width: 100%;">استرجاع الرصيد</button>
            </form>
        </div>

        <h3 style="color: #38bdf8;">📋 جدول كافة الحسابات والأسماء والأرصدة</h3>
        <table>
            <tr><th>المستخدم</th><th>كلمة المرور</th><th>الرصيد</th><th>الفئة</th></tr>
            {% for u in all_users %}
            <tr>
                <td><b>{{ u[0] }}</b></td>
                <td><code>{{ u[1] }}</code></td>
                <td><span style="color: #34d399;">${{ u[2] }}</span></td>
                <td>{{ u[3] }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تسجيل الدخول - منصة Lira</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-box { background: #1f1f1f; padding: 40px; border-radius: 12px; box-shadow: 0 8px 16px rgba(0,0,0,0.5); width: 320px; text-align: center; border: 1px solid #333; }
        input { width: 100%; padding: 12px; margin: 10px 0; border-radius: 6px; border: 1px solid #444; background: #252525; color: white; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #ffd700; color: black; font-weight: bold; border: none; border-radius: 6px; cursor: pointer; margin-top: 10px; font-size: 16px; }
        .error { color: #ef4444; margin-bottom: 12px; font-weight: bold; background: rgba(239,68,68,0.2); padding: 8px; border-radius: 6px; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2 style="color: #ffd700; margin-top: 0;">👑 منصة Lira</h2>
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
