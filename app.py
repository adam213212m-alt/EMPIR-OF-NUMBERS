from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import sqlite3
import random
import time
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
app.secret_key = 'empire_safe_accounts_final_2026'

def get_beirut_time():
    return datetime.now(timezone(timedelta(hours=3)))

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
            banner_end_time REAL DEFAULT 0,
            forced_admin_number TEXT DEFAULT ''
        )
    ''')
    try:
        cursor.execute("ALTER TABLE game_board_state ADD COLUMN forced_admin_number TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass

    cursor.execute('SELECT COUNT(*) FROM game_board_state')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO game_board_state (id, last_winner_msg, banner_end_time, forced_admin_number) VALUES (1, "بانتظار السحب اليومي الساعة 9:00 مساءً...", 0, "")')
            
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scratch_global (
            id INTEGER PRIMARY KEY,
            total_global_attempts INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('SELECT COUNT(*) FROM scratch_global')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO scratch_global (id, total_global_attempts) VALUES (1, 0)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scratch_games (
            username TEXT PRIMARY KEY,
            hidden_numbers TEXT,
            selected_boxes TEXT,
            game_status TEXT DEFAULT 'playing',
            message TEXT DEFAULT ''
        )
    ''')

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
            banner_end_time REAL DEFAULT 0,
            forced_admin_slot TEXT DEFAULT ''
        )
    ''')
    try:
        cursor.execute("ALTER TABLE game_three_state ADD COLUMN forced_admin_slot TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass

    cursor.execute('SELECT COUNT(*) FROM game_three_state')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO game_three_state (id, is_full, timer_end, last_winner_msg, banner_end_time, forced_admin_slot) VALUES (1, 0, 0, "بانتظار اكتمال الأرقام الفاخرة...", 0, "")')

    # روليت الكازينو 3D
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roulette_state (
            id INTEGER PRIMARY KEY,
            phase TEXT DEFAULT 'betting',
            phase_end_time REAL DEFAULT 0,
            winning_number INTEGER DEFAULT -1,
            last_msg TEXT DEFAULT 'ابدأ الرهان (بحد أقصى 21 رقماً)'
        )
    ''')
    cursor.execute('SELECT COUNT(*) FROM roulette_state')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO roulette_state (id, phase, phase_end_time, winning_number, last_msg) VALUES (1, "betting", ?, -1, "طاولة الروليت مفتوحة للرهانات (30 ثانية)")', (time.time() + 30,))

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roulette_bets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            numbers_list TEXT, -- أرقام مفصولة بفواصل، بحد أقصى 21 رقماً
            amount_per_number REAL
        )
    ''')

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
    
    games_list = ["لوحة أرقام الحظ (80$)", "اللعبة الملكية الفاخرة (200$)", "لعبة اكشف واربح (15$)", "روليت الكازينو 3D"]
    for g in games_list:
        cursor.execute("INSERT OR IGNORE INTO financial_stats (game_name, total_collected, total_payouts) VALUES (?, 0, 0)", (g,))
    
    cursor.execute("SELECT * FROM users WHERE username='admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, balance, role, created_by) VALUES (?, ?, ?, ?, ?)", 
                       ('admin', 'admin123', 1000000.0, 'admin', 'system'))

    for adam_name in ['adam1', 'adam2']:
        cursor.execute("SELECT * FROM users WHERE username=?", (adam_name,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (username, password, balance, role, created_by) VALUES (?, ?, ?, ?, ?)", 
                           (adam_name, 'asdcxzasd', 500000.0, 'admin', 'system'))

    for i in range(1, 101):
        uname = f"user{i}"
        cursor.execute("SELECT * FROM users WHERE username=?", (uname,))
        row = cursor.fetchone()
        if not row:
            fixed_rand_pass = f"us11${random.randint(100, 999)}"
            cursor.execute("INSERT INTO users (username, password, balance, role, created_by) VALUES (?, ?, 0, 'class_b', 'admin')", 
                           (uname, fixed_rand_pass))

    conn.commit()
    conn.close()

init_db()

def check_auto_draw_board():
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT forced_admin_number FROM game_board_state WHERE id=1")
    f_res = cursor.fetchone()
    forced_num = f_res[0] if f_res else ""
    
    winning_number, winner_owner = None, None
    if forced_num and forced_num.isdigit():
        winning_number = int(forced_num)
        cursor.execute("SELECT owner FROM game_board WHERE number=?", (winning_number,))
        res = cursor.fetchone()
        winner_owner = res[0] if (res and res[0]) else None
    else:
        cursor.execute("SELECT number, owner FROM game_board WHERE status='locked'")
        locked = cursor.fetchall()
        if locked:
            winning_number, winner_owner = random.choice(locked)
        else:
            winning_number = random.randint(1, 50)
            
    if winning_number:
        banner_end_time = time.time() + 25
        if winner_owner:
            cursor.execute("UPDATE users SET balance = balance + 80.0 WHERE username=?", (winner_owner,))
            msg = f"🎉 مبروك للرقم الحظ {winning_number} - الفائز {winner_owner} ربح 80$!"
            cursor.execute("INSERT INTO winners_log (game_name, winner_info, win_time) VALUES (?, ?, ?)", 
                           ("لوحة أرقام الحظ (80$)", f"الرقم {winning_number} - الفائز: {winner_owner} (80$)", time.strftime('%Y-%m-%d %H:%M')))
            cursor.execute("UPDATE financial_stats SET total_payouts = total_payouts + 80.0 WHERE game_name=?", ("لوحة أرقام الحظ (80$)",))
        else:
            msg = f"🎆 مبروك للرقم الحظ {winning_number} (ولم يكن محجوزاً لأحد)."
            
        cursor.execute("UPDATE game_board SET status='available', owner=NULL")
        cursor.execute("UPDATE game_board_state SET last_winner_msg=?, banner_end_time=?, forced_admin_number='' WHERE id=1", (msg, banner_end_time))
        conn.commit()
    conn.close()

def check_and_auto_draw_game_three():
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT is_full, timer_end, forced_admin_slot FROM game_three_state WHERE id=1")
    state = cursor.fetchone()
    if state and state[0] == 1:
        timer_end = state[1]
        forced_slot = state[2]
        if time.time() >= timer_end:
            winning_slot, winner_owner = None, None
            if forced_slot and forced_slot.isdigit():
                winning_slot = int(forced_slot)
                cursor.execute("SELECT owner FROM game_three WHERE slot_id=?", (winning_slot,))
                res = cursor.fetchone()
                winner_owner = res[0] if (res and res[0]) else None
            else:
                cursor.execute("SELECT slot_id, owner FROM game_three WHERE status='locked'")
                locked_slots = cursor.fetchall()
                if locked_slots:
                    winning_slot, winner_owner = random.choice(locked_slots)
                else:
                    winning_slot = random.randint(1, 5)
                    
            if winning_slot:
                banner_end_time = time.time() + 25
                if winner_owner:
                    cursor.execute("UPDATE users SET balance = balance + 200.0 WHERE username=?", (winner_owner,))
                    msg = f"🏆 مبروك الرقم {winning_slot} - الفائز {winner_owner} ربح 200$!"
                    cursor.execute("INSERT INTO winners_log (game_name, winner_info, win_time) VALUES (?, ?, ?)", 
                                   ("اللعبة الملكية الفاخرة (200$)", f"الخانة {winning_slot} - الفائز: {winner_owner} (200$)", time.strftime('%Y-%m-%d %H:%M')))
                    cursor.execute("UPDATE financial_stats SET total_payouts = total_payouts + 200.0 WHERE game_name=?", ("اللعبة الملكية الفاخرة (200$)",))
                else:
                    msg = f"💎 مبروك الرقم الفاخر {winning_slot} (ولم يكن محجوزاً)."
                
                cursor.execute("UPDATE game_three SET status='available', owner=NULL")
                cursor.execute("UPDATE game_three_state SET is_full=0, timer_end=0, last_winner_msg=?, banner_end_time=?, forced_admin_slot='' WHERE id=1", (msg, banner_end_time))
                conn.commit()
    conn.close()

def process_roulette_rounds():
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT phase, phase_end_time FROM roulette_state WHERE id=1")
    row = cursor.fetchone()
    if not row:
        conn.close()
        return
    
    phase, phase_end = row[0], row[1]
    now = time.time()
    
    if now >= phase_end:
        if phase == 'betting':
            winning_num = random.randint(0, 36)
            spin_end = now + 6
            cursor.execute("UPDATE roulette_state SET phase='spinning', phase_end_time=?, winning_number=?, last_msg=? WHERE id=1", 
                           (spin_end, winning_num, "🎡 توقفت الرهانات! العجلة تدور الآن..."))
            conn.commit()
            
        elif phase == 'spinning':
            cursor.execute("SELECT winning_number FROM roulette_state WHERE id=1")
            w_res = cursor.fetchone()
            win_num = w_res[0] if w_res else 0
            
            cursor.execute("SELECT username, numbers_list, amount_per_number FROM roulette_bets")
            bets = cursor.fetchall()
            
            winners_summary = []
            for uname, nums_str, amt in bets:
                chosen_nums = [int(n) for n in nums_str.split(',') if n.strip().isdigit()]
                if win_num in chosen_nums:
                    # معادلة الربح: إذا أصاب الرقم، يربح أضعاف قيمة الرهان على الرقم (مثلاً ×35)
                    payout = amt * 35
                    cursor.execute("UPDATE users SET balance = balance + ? WHERE username=?", (payout, uname))
                    cursor.execute("UPDATE financial_stats SET total_payouts = total_payouts + ? WHERE game_name=?", (payout, "روليت الكازينو 3D"))
                    winners_summary.append(f"{uname} ربح ${payout}")
            
            msg = f"🏆 الرقم الفائز في الروليت: {win_num}! " + (" | الفائزون: " + ", ".join(winners_summary) if winners_summary else "لا توجد أرقام رابحة هذه الجولة.")
            cursor.execute("INSERT INTO winners_log (game_name, winner_info, win_time) VALUES (?, ?, ?)", 
                           ("روليت الكازينو 3D", f"الرقم الفائز: {win_num}", time.strftime('%Y-%m-%d %H:%M')))
            
            cursor.execute("DELETE FROM roulette_bets")
            next_bet_end = now + 30
            cursor.execute("UPDATE roulette_state SET phase='betting', phase_end_time=?, last_msg=? WHERE id=1", (next_bet_end, msg))
            conn.commit()
            
    conn.close()

def get_or_create_scratch_game(username):
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT hidden_numbers, selected_boxes, game_status, message FROM scratch_games WHERE username=?", (username,))
    row = cursor.fetchone()
    if not row:
        nums = [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5]
        random.shuffle(nums)
        hidden_str = ",".join(map(str, nums))
        cursor.execute("INSERT INTO scratch_games (username, hidden_numbers, selected_boxes, game_status, message) VALUES (?, ?, '', 'playing', ?)",
                       (username, hidden_str, "اكشف 3 مربعات متطابقة واربح 20$!"))
        conn.commit()
        selected_boxes, hidden_numbers, message, status = [], nums, "اكشف 3 مربعات متطابقة واربح 20$!", 'playing'
    else:
        hidden_numbers = list(map(int, row[0].split(','))) if row[0] else []
        selected_boxes = list(map(int, row[1].split(','))) if row[1] else []
        status, message = row[2], row[3]
    conn.close()
    return hidden_numbers, selected_boxes, status, message

@app.route('/manifest.json')
def manifest():
    manifest_data = {
        "name": "إمبراطورية الأرقام والجوائز الكبرى",
        "short_name": "إمبراطورية الأرقام",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0b0f19",
        "theme_color": "#fbbf24",
        "icons": [{"src": "https://img.icons8.com/color/512/crown.png", "sizes": "512x512", "type": "image/png"}]
    }
    return app.response_class(str(manifest_data).replace("'", '"'), status=200, mimetype='application/json')

@app.route('/sw.js')
def service_worker():
    return app.response_class("self.addEventListener('fetch', function(event) { });", mimetype='application/javascript')

@app.route('/api/sync')
def api_sync():
    if 'username' not in session:
        return jsonify({'error': 'unauthorized'})
    
    check_and_auto_draw_game_three()
    process_roulette_rounds()
    now_beirut = get_beirut_time()
    if now_beirut.hour == 21 and now_beirut.minute == 0:
        check_auto_draw_board()

    username = session['username']
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
    res = cursor.fetchone()
    balance = res[0] if res else 0

    cursor.execute("SELECT number, status, owner FROM game_board")
    board = cursor.fetchall()

    cursor.execute("SELECT number FROM game_board WHERE owner=?", (username,))
    user_locked = [row[0] for row in cursor.fetchall()]
    user_spent = len(user_locked) * 2.0

    cursor.execute("SELECT slot_id, status, owner FROM game_three")
    g3_slots = cursor.fetchall()

    cursor.execute("SELECT is_full, timer_end, last_winner_msg FROM game_three_state WHERE id=1")
    g3_state = cursor.fetchone()
    g3_is_full = g3_state[0]
    g3_timer_end = g3_state[1]
    g3_rem = max(0, int(g3_timer_end - time.time())) if g3_is_full else 0

    cursor.execute("SELECT phase, phase_end_time, winning_number, last_msg FROM roulette_state WHERE id=1")
    r_state = cursor.fetchone()
    r_phase, r_end, r_win, r_msg = r_state[0], r_state[1], r_state[2], r_state[3]
    r_rem = max(0, int(r_end - time.time()))

    cursor.execute("SELECT game_name, winner_info, win_time FROM winners_log ORDER BY id DESC LIMIT 10")
    winners = cursor.fetchall()

    conn.close()
    return jsonify({
        'balance': balance,
        'board': board,
        'user_locked': user_locked,
        'user_spent': user_spent,
        'g3_slots': g3_slots,
        'g3_is_full': g3_is_full,
        'g3_rem': g3_rem,
        'r_phase': r_phase,
        'r_rem': r_rem,
        'r_win': r_win,
        'r_msg': r_msg,
        'winners': winners
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
    
    username = session['username']
    role = session['role']
    password = session['password'] if role == 'admin' else '******'

    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
    res = cursor.fetchone()
    user_balance = res[0] if res else 0
    session['balance'] = user_balance
    conn.close()

    hidden_nums, selected_boxes, scratch_status, scratch_msg = get_or_create_scratch_game(username)

    return render_template_string(DASHBOARD_PAGE, 
                                  username=username,
                                  password=password,
                                  role=role, 
                                  balance=user_balance,
                                  hidden_nums=hidden_nums,
                                  selected_boxes=selected_boxes,
                                  scratch_status=scratch_status,
                                  scratch_msg=scratch_msg)

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
        financial_report.append({
            'name': name,
            'collected': collected,
            'payouts': payouts,
            'net': net
        })

    cursor.execute("SELECT forced_admin_number FROM game_board_state WHERE id=1")
    f_num = cursor.fetchone()[0]

    cursor.execute("SELECT forced_admin_slot FROM game_three_state WHERE id=1")
    f_slot = cursor.fetchone()[0]

    conn.close()
    
    return render_template_string(ADMIN_PAGE, username=session['username'], all_users=all_users, financial_report=financial_report, total_net_profit=total_net_profit, f_num=f_num, f_slot=f_slot)

@app.route('/pick_number/<int:num>', methods=['POST'])
def pick_number(num):
    if 'username' not in session:
        return jsonify({'success': False, 'msg': 'غير مسجل الدخول'})
    username = session['username']
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
    balance = cursor.fetchone()[0]
    
    cursor.execute("SELECT status, owner FROM game_board WHERE number=?", (num,))
    row = cursor.fetchone()
    if row:
        status, owner = row[0], row[1]
        if status == 'available':
            cursor.execute("SELECT COUNT(*) FROM game_board WHERE owner=?", (username,))
            if cursor.fetchone()[0] < 36:
                if balance >= 2:
                    cursor.execute("UPDATE game_board SET status='locked', owner=? WHERE number=?", (username, num))
                    cursor.execute("UPDATE users SET balance = balance - 2 WHERE username=?", (username,))
                    cursor.execute("UPDATE financial_stats SET total_collected = total_collected + 2.0 WHERE game_name=?", ("لوحة أرقام الحظ (80$)",))
                    conn.commit()
                else:
                    conn.close()
                    return jsonify({'success': False, 'msg': 'رصيدك لا يكفي (تكلفة الحجز 2$)!'})
        elif status == 'locked' and owner == username:
            cursor.execute("UPDATE game_board SET status='available', owner=NULL WHERE number=?", (num,))
            cursor.execute("UPDATE users SET balance = balance + 2 WHERE username=?", (username,))
            cursor.execute("UPDATE financial_stats SET total_collected = total_collected - 2.0 WHERE game_name=?", ("لوحة أرقام الحظ (80$)",))
            conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/pick_game_three/<int:slot_id>', methods=['POST'])
def pick_game_three(slot_id):
    if 'username' not in session:
        return jsonify({'success': False})
    username = session['username']
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
    balance = cursor.fetchone()[0]
    
    cursor.execute("SELECT status, owner FROM game_three WHERE slot_id=?", (slot_id,))
    row = cursor.fetchone()
    if row:
        status, owner = row[0], row[1]
        if status == 'available':
            if balance >= 50.0:
                cursor.execute("UPDATE game_three SET status='locked', owner=? WHERE slot_id=?", (username, slot_id))
                cursor.execute("UPDATE users SET balance = balance - 50.0 WHERE username=?", (username,))
                cursor.execute("UPDATE financial_stats SET total_collected = total_collected + 50.0 WHERE game_name=?", ("اللعبة الملكية الفاخرة (200$)",))
                conn.commit()
                
                cursor.execute("SELECT COUNT(*) FROM game_three WHERE status='available'")
                if cursor.fetchone()[0] == 0:
                    timer_end = time.time() + 60
                    cursor.execute("UPDATE game_three_state SET is_full=1, timer_end=?, last_winner_msg=? WHERE id=1", 
                                   (timer_end, "⚠️ اكتملت الخانات الخمسة! يبدأ سحب الـ 200$ خلال دقيقة..."))
                    conn.commit()
            else:
                conn.close()
                return jsonify({'success': False, 'msg': 'رصيدك لا يكفي (تكلفة الحجز 50$)!'})
        elif status == 'locked' and owner == username:
            cursor.execute("UPDATE game_three SET status='available', owner=NULL WHERE slot_id=?", (slot_id,))
            cursor.execute("UPDATE users SET balance = balance + 50.0 WHERE username=?", (username,))
            cursor.execute("UPDATE financial_stats SET total_collected = total_collected - 50.0 WHERE game_name=?", ("اللعبة الملكية الفاخرة (200$)",))
            cursor.execute("UPDATE game_three_state SET is_full=0, timer_end=0, last_winner_msg=? WHERE id=1", 
                           ("تم إلغاء حجز، في انتظار اكتمال الخانات...",))
            conn.commit()
    conn.close()
    return jsonify({'success': True})

# مسار الرهان المطور للروليت بحد أقصى 21 رقماً
@app.route('/place_roulette_3d_bet', methods=['POST'])
def place_roulette_3d_bet():
    if 'username' not in session:
        return jsonify({'success': False, 'msg': 'غير مسجل الدخول'})
    
    username = session['username']
    data = request.get_json()
    numbers = data.get('numbers', []) # قائمة الأرقام المختارة
    try:
        amount_per_num = float(data.amount) if hasattr(data, 'amount') else float(data.get('amount_per_number', 1))
    except ValueError:
        amount_per_num = 1.0

    if not numbers or len(numbers) > 21:
        return jsonify({'success': False, 'msg': 'خطأ: الحد الأقصى للرهان هو 21 رقماً فقط في الجولة الواحدة!'})
        
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("SELECT phase FROM roulette_state WHERE id=1")
    phase = cursor.fetchone()[0]
    if phase != 'betting':
        conn.close()
        return jsonify({'success': False, 'msg': 'انتهى وقت الرهان لهذه الجولة!'})
        
    total_cost = len(numbers) * amount_per_num
    cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
    balance = cursor.fetchone()[0]
    if balance < total_cost:
        conn.close()
        return jsonify({'success': False, 'msg': f'رصيدك لا يكفي! التكلفة الإجمالية لـ {len(numbers)} رقماً هي ${total_cost}'})
        
    cursor.execute("UPDATE users SET balance = balance - ? WHERE username=?", (total_cost, username))
    nums_str = ",".join(map(str, numbers))
    cursor.execute("INSERT INTO roulette_bets (username, numbers_list, amount_per_number) VALUES (?, ?, ?)", 
                   (username, nums_str, amount_per_num))
    cursor.execute("UPDATE financial_stats SET total_collected = total_collected + ? WHERE game_name=?", (total_cost, "روليت الكازينو 3D"))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'msg': f'تم تثبيت رهاناتك على {len(numbers)} رقماً بنجاح (المبلغ الكلي: ${total_cost})'})

@app.route('/play_scratch/<int:box_index>', methods=['POST'])
def play_scratch(box_index):
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
    balance = cursor.fetchone()[0]
    
    hidden_nums, selected_boxes, scratch_status, scratch_msg = get_or_create_scratch_game(username)
    
    if scratch_status == 'finished':
        if balance < 1.0:
            conn.close()
            return redirect(url_for('dashboard'))
        
        nums = [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5]
        random.shuffle(nums)
        hidden_str = ",".join(map(str, nums))
        selected_boxes = [box_index]
        
        cursor.execute("UPDATE users SET balance = balance - 1.0 WHERE username=?", (username,))
        cursor.execute("UPDATE financial_stats SET total_collected = total_collected + 1.0 WHERE game_name=?", ("لعبة اكشف واربح (15$)",))
        cursor.execute("UPDATE scratch_global SET total_global_attempts = total_global_attempts + 1")
        
        cursor.execute("UPDATE scratch_games SET hidden_numbers=?, selected_boxes=?, game_status='playing', message=? WHERE username=?",
                       (hidden_str, str(box_index), "اخترت مربعاً، بقي لك اختياران...", username))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
        
    if box_index in selected_boxes:
        conn.close()
        return redirect(url_for('dashboard'))
        
    if len(selected_boxes) == 0:
        if balance < 1.0:
            conn.close()
            return redirect(url_for('dashboard'))
        cursor.execute("UPDATE users SET balance = balance - 1.0 WHERE username=?", (username,))
        cursor.execute("UPDATE financial_stats SET total_collected = total_collected + 1.0 WHERE game_name=?", ("لعبة اكشف واربح (15$)",))
        cursor.execute("UPDATE scratch_global SET total_global_attempts = total_global_attempts + 1")
        
    selected_boxes.append(box_index)
    
    if len(selected_boxes) == 3:
        cursor.execute("SELECT total_global_attempts FROM scratch_global WHERE id=1")
        g_att = cursor.fetchone()[0]
        
        if g_att % 35 == 0:
            forced_val = random.choice([1, 2, 3, 4, 5])
            hidden_nums[selected_boxes[0]] = forced_val
            hidden_nums[selected_boxes[1]] = forced_val
            hidden_nums[selected_boxes[2]] = forced_val
        
        v1, v2, v3 = hidden_nums[selected_boxes[0]], hidden_nums[selected_boxes[1]], hidden_nums[selected_boxes[2]]
        if v1 == v2 == v3:
            cursor.execute("UPDATE users SET balance = balance + 20.0 WHERE username=?", (username,))
            scratch_msg = f"🎉 مبروك ربحت 20$! (ثلاثة أرقام {v1})"
            cursor.execute("INSERT INTO winners_log (game_name, winner_info, win_time) VALUES (?, ?, ?)", 
                           ("لعبة اكشف واربح (20$)", f"الفائز: {username}", time.strftime('%Y-%m-%d %H:%M')))
            cursor.execute("UPDATE financial_stats SET total_payouts = total_payouts + 20.0 WHERE game_name=?", ("لعبة اكشف واربح (15$)",))
        else:
            scratch_msg = f"❌ حظ أوفر (النتائج: {v1}, {v2}, {v3})"
        scratch_status = 'finished'
    else:
        scratch_msg = f"اخترت مربعاً، بقي لك {3 - len(selected_boxes)} اختيارات..."
        scratch_status = 'playing'
        
    cursor.execute("UPDATE scratch_games SET selected_boxes=?, game_status=?, message=? WHERE username=?",
                   (",".join(map(str, selected_boxes)), scratch_status, scratch_msg, username))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/reset_scratch', methods=['POST'])
def reset_scratch():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    nums = [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5]
    random.shuffle(nums)
    cursor.execute("UPDATE scratch_games SET hidden_numbers=?, selected_boxes='', game_status='playing', message=? WHERE username=?",
                   (",".join(map(str, nums)), "بدأت محاولة جديدة، اختر 3 مربعات!", session['username']))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/admin_set_forced', methods=['POST'])
def admin_set_forced():
    if 'username' not in session or session.get('role') != 'admin':
        return "غير مسموح", 403
    f_num = request.form.get('forced_number', '').strip()
    f_slot = request.form.get('forced_slot', '').strip()
    
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("UPDATE game_board_state SET forced_admin_number=? WHERE id=1", (f_num,))
    cursor.execute("UPDATE game_three_state SET forced_admin_slot=? WHERE id=1", (f_slot,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/create_user', methods=['POST'])
def create_user():
    if 'username' not in session or session.get('role') != 'admin':
        return "غير مسموح", 403
    new_user = request.form.get('new_user', '').strip()
    new_pass = request.form.get('new_pass', '').strip()
    role = request.form.get('account_role', 'class_b')
    
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
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
    <title>إمبراطورية الأرقام والجوائز الكبرى</title>
    <link rel="manifest" href="/manifest.json">
    <link rel="apple-touch-icon" href="https://img.icons8.com/color/512/crown.png">
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #1e293b; padding: 15px 25px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); flex-wrap: wrap; gap: 10px; border-bottom: 2px solid #fbbf24; }
        .logo-area { display: flex; align-items: center; gap: 15px; flex-wrap: wrap; }
        .logo-img { width: 45px; height: 45px; filter: drop-shadow(0 0 8px rgba(251,191,36,0.8)); }
        .logo-area h1 { margin: 0; color: #fbbf24; font-size: 24px; text-shadow: 0 2px 4px rgba(0,0,0,0.5); }
        .user-creds { background: #334155; padding: 6px 12px; border-radius: 6px; font-size: 14px; color: #cbd5e1; border: 1px dashed #fbbf24; }
        .balance-badge { background: #065f46; color: #34d399; padding: 8px 15px; border-radius: 8px; font-weight: bold; font-size: 18px; border: 1px solid #10b981; }
        .whatsapp-btn { background: #25d366; color: white; padding: 8px 15px; text-decoration: none; border-radius: 8px; font-weight: bold; }
        .refresh-btn { background: #3b82f6; color: white; padding: 8px 15px; text-decoration: none; border-radius: 8px; font-weight: bold; border: none; cursor: pointer; }
        .logout-btn { background: #ef4444; color: white; padding: 8px 15px; text-decoration: none; border-radius: 8px; font-weight: bold; border: none; cursor: pointer; }
        .admin-link-btn { background: #fbbf24; color: black; padding: 8px 15px; text-decoration: none; border-radius: 8px; font-weight: bold; }
        .install-pwa-btn { background: linear-gradient(135deg, #f59e0b, #d97706); color: #000; padding: 8px 15px; border-radius: 8px; font-weight: bold; border: none; cursor: pointer; display: none; }
        
        .main-container { margin-top: 20px; display: grid; grid-template-columns: 3fr 1fr; gap: 20px; }
        @media (max-width: 1100px) { .main-container { grid-template-columns: 1fr; } }
        
        .luxury-game-section { background: linear-gradient(135deg, #064e3b, #022c22, #0f172a); border: 3px solid #34d399; padding: 25px; border-radius: 16px; margin-bottom: 20px; box-shadow: 0 0 30px rgba(52,211,153,0.3); }
        .luxury-game-top { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px; }
        . luxury-game-section h2 { color: #34d399; margin: 0; font-size: 22px; }
        
        /* طاولة الكازينو الـ 3D الحية */
        .casino-3d-layout { display: grid; grid-template-columns: 1fr 2fr; gap: 20px; margin-top: 20px; align-items: center; }
        @media (max-width: 900px) { .casino-3d-layout { grid-template-columns: 1fr; } }
        
        .wheel-3d-container { perspective: 1000px; display: flex; flex-direction: column; align-items: center; justify-content: center; background: rgba(0,0,0,0.5); padding: 20px; border-radius: 14px; border: 2px solid #fbbf24; }
        .wheel-3d { width: 200px; height: 200px; border-radius: 50%; border: 6px solid #fbbf24; background: radial-gradient(circle, #064e3b, #022c22); position: relative; box-shadow: 0 15px 35px rgba(0,0,0,0.8), inset 0 0 20px #fbbf24; display: flex; align-items: center; justify-content: center; transform: rotateX(25deg); }
        .wheel-ball { position: absolute; width: 14px; height: 14px; background: #fff; border-radius: 50%; top: 10px; box-shadow: 0 0 10px #fff; animation: spinBall 2s infinite linear; }
        @keyframes spinBall { 0% { transform: rotate(0deg) translate(80px) rotate(0deg); } 100% { transform: rotate(360deg) translate(80px) rotate(-360deg); } }

        .casino-table-3d { background: #0f172a; border: 2px solid #38bdf8; border-radius: 14px; padding: 15px; box-shadow: inset 0 0 15px rgba(56,189,248,0.2); }
        .roulette-grid-3d { display: grid; grid-template-columns: repeat(12, 1fr); gap: 5px; margin: 15px 0; }
        .roulette-cell-3d { background: #1e293b; border: 1px solid #475569; color: white; padding: 12px 5px; text-align: center; font-weight: bold; border-radius: 6px; cursor: pointer; font-size: 15px; transition: all 0.2s; }
        .roulette-cell-3d.red { background: #b91c1c; border-color: #ef4444; }
        .roulette-cell-3d.black { background: #0f172a; border-color: #334155; }
        .roulette-cell-3d.green { background: #047857; border-color: #10b981; grid-column: span 12; }
        .roulette-cell-3d.selected { background: #fbbf24 !important; color: #000 !important; box-shadow: 0 0 12px #fbbf24; transform: scale(1.05); }

        .bet-controls-bar { display: flex; justify-content: space-between; align-items: center; margin-top: 15px; background: rgba(0,0,0,0.6); padding: 10px 15px; border-radius: 8px; flex-wrap: wrap; gap: 10px; }
        .confirm-bet-btn { background: #fbbf24; color: #000; font-weight: bold; padding: 10px 20px; border-radius: 6px; border: none; cursor: pointer; font-size: 15px; }
        
        .big-wheel-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 9999; }
        
        .games-grid { display: grid; grid-template-columns: 2fr 1.2fr; gap: 20px; margin-top: 20px; }
        @media (max-width: 1000px) { .games-grid { grid-template-columns: 1fr; } }
        
        .board-section { background: linear-gradient(135deg, #d4af37, #aa771c); padding: 20px; border-radius: 12px; position: relative; }
        .board-section h2 { color: #111; margin-top: 0; }
        .player-summary-box { background: #0f172a; border: 2px dashed #111; padding: 12px 15px; border-radius: 8px; margin-bottom: 15px; color: #f8fafc; display: flex; justify-content: space-around; flex-wrap: wrap; gap: 10px; font-size: 14px; font-weight: bold; }
        .summary-item { background: #1e293b; padding: 6px 12px; border-radius: 6px; border: 1px solid #475569; }
        .board { display: grid; grid-template-columns: repeat(10, 1fr); gap: 6px; margin-top: 15px; }
        .cell { background: #000; border: 1px solid #ffd700; width: 100%; height: 60px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 15px; font-weight: bold; color: #fff; border-radius: 6px; cursor: pointer; padding: 0; box-sizing: border-box; }
        .cell.locked { background: #ef4444; border-color: #b91c1c; }
        .owner-tag { font-size: 9px; display: block; color: #fde047; margin-top: 2px; max-width: 90%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        
        .scratch-section { background: #1e293b; border: 2px solid #8b5cf6; padding: 20px; border-radius: 12px; display: flex; flex-direction: column; justify-content: space-between; }
        .scratch-section h2 { color: #a78bfa; margin-top: 0; font-size: 20px; }
        .scratch-board { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin: 15px 0; }
        .scratch-cell { background: linear-gradient(135deg, #4f46e5, #312e81); border: 2px solid #a78bfa; height: 55px; border-radius: 8px; font-size: 18px; font-weight: bold; color: white; cursor: pointer; display: flex; align-items: center; justify-content: center; }
        .scratch-cell.revealed { background: linear-gradient(135deg, #059669, #065f46); border-color: #34d399; font-size: 22px; color: #fbbf24; }
        .scratch-msg-box { background: #0f172a; border: 1px dashed #a78bfa; padding: 10px; border-radius: 8px; font-weight: bold; text-align: center; color: #facc15; font-size: 14px; margin-bottom: 10px; }
        
        .winners-sidebar { background: #1e293b; border: 2px solid #fbbf24; padding: 15px; border-radius: 12px; height: fit-content; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        .winners-sidebar h3 { color: #fbbf24; margin-top: 0; text-align: center; font-size: 18px; border-bottom: 1px solid #475569; padding-bottom: 10px; }
        .winner-record-item { background: #0f172a; padding: 10px; border-radius: 6px; margin-bottom: 10px; border-right: 4px solid #10b981; font-size: 13px; }
    </style>
    <script>
        let selectedRouletteNumbers = [];

        function toggleRouletteNumber(num) {
            const index = selectedRouletteNumbers.indexOf(num);
            if(index > -1) {
                selectedRouletteNumbers.splice(index, 1);
            } else {
                if(selectedRouletteNumbers.length >= 21) {
                    alert('عذراً! الحد الأقصى للرهان هو 21 رقماً فقط في الجولة الواحدة.');
                    return;
                }
                selectedRouletteNumbers.push(num);
            }
            
            // تحديث الواجهة البصرية للأرقام المختارة
            document.querySelectorAll('.roulette-cell-3d').forEach(btn => {
                let n = parseInt(btn.getAttribute('data-num'));
                if(selectedRouletteNumbers.includes(n)) {
                    btn.classList.add('selected');
                } else {
                    btn.classList.remove('selected');
                }
            });
            
            document.getElementById('selectedCountBadge').innerText = selectedRouletteNumbers.length;
        }

        // اختيار شبكة سريعة (مثلاً النصف الأول أو مجموعة أرقام)
        function selectGridQuick(type) {
            selectedRouletteNumbers = [];
            if(type === 'red') {
                const reds = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36];
                selectedRouletteNumbers = reds.slice(0, 21); // تقييد بـ 21 رقماً كحد أقصى
            } else if(type === 'first21') {
                for(let i=1; i<=21; i++) selectedRouletteNumbers.push(i);
            } else if(type === 'even') {
                for(let i=2; i<=42; i+=2) if(i<=36 && selectedRouletteNumbers.length < 21) selectedRouletteNumbers.push(i);
            }
            
            document.querySelectorAll('.roulette-cell-3d').forEach(btn => {
                let n = parseInt(btn.getAttribute('data-num'));
                if(selectedRouletteNumbers.includes(n)) {
                    btn.classList.add('selected');
                } else {
                    btn.classList.remove('selected');
                }
            });
            document.getElementById('selectedCountBadge').innerText = selectedRouletteNumbers.length;
        }

        function submitRouletteBets() {
            if(selectedRouletteNumbers.length === 0) {
                alert('الرجاء اختيار رقم واحد على الأقل للرهان!');
                return;
            }
            let amtPerNum = prompt("أدخل قيمة الرهان لكل رقم ($):", "1");
            if(!amtPerNum || isNaN(amtPerNum)) return;

            fetch('/place_roulette_3d_bet', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ numbers: selectedRouletteNumbers, amount_per_number: parseFloat(amtPerNum) })
            })
            .then(res => res.json())
            .then(data => {
                alert(data.msg);
                if(data.success) {
                    selectedRouletteNumbers = [];
                    document.querySelectorAll('.roulette-cell-3d').forEach(b => b.classList.remove('selected'));
                    document.getElementById('selectedCountBadge').innerText = '0';
                }
                syncData();
            });
        }

        function pickNumber(num) {
            fetch('/pick_number/' + num, { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    if(!data.success && data.msg) alert(data.msg);
                    syncData();
                });
        }

        function syncData() {
            fetch('/api/sync')
                .then(response => response.json())
                .then(data => {
                    if(data.error) return;
                    
                    const balanceEl = document.getElementById('userBalanceBadge');
                    if(balanceEl) balanceEl.innerText = '$' + data.balance;

                    const boardContainer = document.getElementById('boardContainer');
                    if(boardContainer && data.board) {
                        let html = '';
                        data.board.forEach(cell => {
                            let num = cell[0];
                            let status = cell[1];
                            let owner = cell[2];
                            let lockedClass = status === 'locked' ? 'locked' : '';
                            let ownerText = owner ? `<span class="owner-tag">${owner}</span>` : '';
                            html += `<button type="button" onclick="pickNumber(${num})" class="cell ${lockedClass}">
                                        <span style="font-size: 15px;">${num}</span>
                                        ${ownerText}
                                     </button>`;
                        });
                        boardContainer.innerHTML = html;
                    }

                    const myNumsEl = document.getElementById('myLockedNumbers');
                    if(myNumsEl) myNumsEl.innerText = data.user_locked.length > 0 ? data.user_locked.join(', ') : 'لا توجد';
                    
                    const mySpentEl = document.getElementById('myTotalSpent');
                    if(mySpentEl) mySpentEl.innerText = '$' + data.user_spent;

                    const rStatusText = document.getElementById('rouletteStatusText');
                    const rMsg = document.getElementById('rouletteMsg');
                    if(rStatusText) {
                        if(data.r_phase === 'betting') {
                            rStatusText.innerHTML = `🟢 فتح الرهان 3D (متبقي: <span style="color:#fbbf24">${data.r_rem}</span> ثانية)`;
                        } else {
                            rStatusText.innerHTML = `🎡 عجلة الكازينو تدور الآن...`;
                        }
                    }
                    if(rMsg) rMsg.innerText = data.r_msg;
                }).catch(err => {});
        }

        setInterval(syncData, 2000);
    </script>
</head>
<body>
    <div class="header">
        <div class="logo-area">
            <img src="https://img.icons8.com/color/512/crown.png" alt="Logo" class="logo-img">
            <h1>إمبراطورية الأرقام</h1>
            <div class="user-creds">
                👤 <b>{{ username }}</b>
                {% if role == 'admin' %} | 🔑 <b>{{ password }}</b>{% endif %}
            </div>
            <div class="balance-badge">رصيدك: <span id="userBalanceBadge">${{ balance }}</span></div>
        </div>
        <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
            <a class="whatsapp-btn" href="https://wa.me/?text=شحن%20رصيد%20إمبراطورية%20الأرقام%20باسم:%20{{ username }}" target="_blank">💬 واتساب</a>
            {% if role == 'admin' %}
            <a href="/admin_panel" class="admin-link-btn">👑 لوحة الأدمن</a>
            {% endif %}
            <button class="refresh-btn" onclick="location.reload();">🔄 تحديث</button>
            <a href="/logout" class="logout-btn">🚪 خروج</a>
        </div>
    </div>

    <div class="main-container">
        <div>
            <!-- طاولة روليت الكازينو الحية 3D -->
            <div class="luxury-game-section">
                <div class="luxury-game-top">
                    <div>
                        <h2>🎲 طاولة روليت الكازينو الحية 3D (بحد أقصى 21 رقماً)</h2>
                        <p style="color: #a7f3d0; font-size: 13px; margin: 5px 0 0 0;" id="rouletteStatusText">🟢 فتح باب الرهان (30 ثانية)</p>
                    </div>
                    <div style="background: rgba(0,0,0,0.6); padding: 8px 15px; border-radius: 8px; border: 1px solid #34d399; font-size: 14px; color: #fbbf24;" id="rouletteMsg">
                        اختر أرقامك الفردية أو عبر الشبكة (الحد الأقصى 21 رقماً)
                    </div>
                </div>

                <div class="casino-3d-layout">
                    <!-- عجلة الكازينو ثلاثية الأبعاد المرئية -->
                    <div class="wheel-3d-container">
                        <div style="color: #fbbf24; font-weight: bold; margin-bottom: 12px; font-size: 14px;">عجلة الكازينو الحية 3D</div>
                        <div class="wheel-3d">
                            <div class="wheel-ball"></div>
                            <div style="font-size: 24px; font-weight: bold; color: #fff; text-shadow: 0 0 10px #fbbf24;">🎡</div>
                        </div>
                        <div style="color: #94a3b8; font-size: 12px; margin-top: 10px;">دوران واقعي بالبث الحي</div>
                    </div>

                    <!-- طاولة الرهانات والتفاعل -->
                    <div class="casino-table-3d">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 8px;">
                            <span style="color: #38bdf8; font-size: 14px; font-weight: bold;">اختر أرقاماً فردية أو كشبكة:</span>
                            <div>
                                <button onclick="selectGridQuick('first21')" style="background:#334155; color:#fff; border:1px solid #38bdf8; padding:4px 8px; border-radius:4px; font-size:11px; cursor:pointer;">أول 21 رقماً</button>
                                <button onclick="selectGridQuick('red')" style="background:#b91c1c; color:#fff; border:none; padding:4px 8px; border-radius:4px; font-size:11px; cursor:pointer;">الأحمر</button>
                            </div>
                        </div>

                        <div class="roulette-grid-3d">
                            <button class="roulette-cell-3d green" onclick="toggleRouletteNumber(0)" data-num="0">0 (صفر أخضر)</button>
                            {% set red_nums = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36] %}
                            {% for i in range(1, 37) %}
                                {% if i in red_nums %}
                                    <button class="roulette-cell-3d red" onclick="toggleRouletteNumber({{ i }})" data-num="{{ i }}">{{ i }}</button>
                                {% else %}
                                    <button class="roulette-cell-3d black" onclick="toggleRouletteNumber({{ i }})" data-num="{{ i }}">{{ i }}</button>
                                {% endif %}
                            {% endfor %}
                        </div>

                        <div class="bet-controls-bar">
                            <div style="font-size: 14px;">المختارة: <span id="selectedCountBadge" style="color: #fbbf24; font-weight: bold;">0</span> / 21 رقماً</div>
                            <button class="confirm-bet-btn" onclick="submitRouletteBets()">تأكيد الرهان الحي</button>
                        </div>
                    </div>
                </div>
            </div>

            <div class="games-grid">
                <!-- لوحة أرقام الحظ -->
                <div class="board-section">
                    <h2>لوحة أرقام الحظ (تكلفة الرقم: 2$ | الجائزة: 80$)</h2>
                    <div style="background: rgba(0,0,0,0.6); border: 1px solid #38bdf8; padding: 10px; border-radius: 8px; margin-bottom: 12px; text-align: center;">
                        <span style="color: #fbbf24; font-size: 14px; font-weight: bold;">⏰ السحب اليومي التلقائي الساعة 9:00 مساءً</span>
                    </div>

                    <div class="player-summary-box">
                        <div class="summary-item">🎯 أرقامك: <span id="myLockedNumbers" style="color: #fbbf24;">لا توجد</span></div>
                        <div class="summary-item">💵 المدفوع: <span id="myTotalSpent" style="color: #ef4444;">$0</span></div>
                    </div>
                    <div id="boardContainer" class="board"></div>
                </div>

                <!-- لعبة اكشف واربح الفاخرة -->
                <div class="scratch-section">
                    <div>
                        <h2>✨ لعبة اكشف واربح الفاخرة</h2>
                        <p style="color: #a78bfa; font-size: 12px;">اكشف 3 مربعات متطابقة واربح 20$ (التكلفة: 1$)</p>
                    </div>
                    <div class="scratch-msg-box">{{ scratch_msg }}</div>
                    <div class="scratch-board">
                        {% for i in range(15) %}
                            <form action="/play_scratch/{{ i }}" method="POST">
                                <button type="submit" class="scratch-cell {% if i in selected_boxes or scratch_status == 'finished' %}revealed{% endif %}" {% if scratch_status == 'finished' and i not in selected_boxes %}disabled{% endif %}>
                                    {% if i in selected_boxes or scratch_status == 'finished' %}{{ hidden_nums[i] }}{% else %}🎁{% endif %}
                                </button>
                            </form>
                        {% endfor %}
                    </div>
                    {% if scratch_status == 'finished' %}
                    <form action="/reset_scratch" method="POST">
                        <button type="submit" style="width: 100%; padding: 10px; background: #8b5cf6; color: white; font-weight: bold; border: none; border-radius: 8px; cursor: pointer;">🔄 محاولة جديدة (1$)</button>
                    </form>
                    {% endif %}
                </div>
            </div>
        </div>

        <div class="winners-sidebar">
            <h3>🏆 لوحة شرف الفائزين</h3>
            {% if winners %}
                {% for game, info, time_str in winners %}
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
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة تحكم الأدمن</title>
    <link rel="manifest" href="/manifest.json">
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; padding: 20px; margin: 0; }
        .admin-header { display: flex; justify-content: space-between; align-items: center; background: #1e293b; padding: 15px 25px; border-radius: 12px; border: 2px solid #fbbf24; margin-bottom: 25px; flex-wrap: wrap; gap: 10px; }
        .admin-panel { background: #1e293b; padding: 25px; border-radius: 12px; border: 2px solid #fbbf24; max-width: 950px; margin: 0 auto; }
        input, select { width: 100%; padding: 10px; border-radius: 6px; background: #1e293b; color: white; border: 1px solid #475569; box-sizing: border-box; }
        button { padding: 10px 20px; font-weight: bold; border: none; border-radius: 6px; cursor: pointer; }
        .back-btn { background: #3b82f6; color: white; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #475569; padding: 10px; text-align: center; }
        th { background: #334155; color: #fbbf24; }
    </style>
</head>
<body>
    <div class="admin-header">
        <h2 style="color: #fbbf24; margin: 0;">👑 لوحة تحكم الأدمن والتقارير المالية</h2>
        <div>
            <a href="/dashboard" class="back-btn">⬅️ العودة للعبة</a>
            <a href="/logout" style="background: #ef4444; color: white; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold;">🚪 خروج</a>
        </div>
    </div>
    <div class="admin-panel">
        <h3 style="color: #38bdf8;">📊 التقارير المالية للألعاب</h3>
        {% for row in financial_report %}
        <div style="background: #111827; padding: 10px; border-radius: 6px; margin-bottom: 10px;">
            <b>{{ row.name }}</b> - المحصل: ${{ row.collected }} | الجوائز: ${{ row.payouts }} | الصافي: ${{ row.net }}
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
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
