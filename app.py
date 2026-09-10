from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import sqlite3
import random
import time
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
app.secret_key = 'empire_safe_accounts_final_secure_2026'

def get_beirut_time():
    return datetime.now(timezone(timedelta(hours=3)))

def get_db():
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
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
                forced_admin_number TEXT DEFAULT '',
                last_draw_date TEXT DEFAULT ''
            )
        ''')
        try:
            cursor.execute("ALTER TABLE game_board_state ADD COLUMN last_draw_date TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass

        cursor.execute('SELECT COUNT(*) FROM game_board_state')
        if cursor.fetchone()[0] == 0:
            cursor.execute('INSERT INTO game_board_state (id, last_winner_msg, banner_end_time, forced_admin_number, last_draw_date) VALUES (1, "بانتظار السحب اليومي الساعة 9:00 مساءً...", 0, "", "")')
                
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
        
        cursor.execute('SELECT COUNT(*) FROM game_three_state')
        if cursor.fetchone()[0] == 0:
            cursor.execute('INSERT INTO game_three_state (id, is_full, timer_end, last_winner_msg, banner_end_time, forced_admin_slot) VALUES (1, 0, 0, "بانتظار اكتمال الأرقام الفاخرة...", 0, "")')

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
        
        games_list = ["لوحة أرقام الحظ (80$)", "اللعبة الملكية الفاخرة (200$)", "لعبة اكشف واربح (15$)"]
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
            if not cursor.fetchone():
                fixed_rand_pass = f"us11${random.randint(100, 999)}"
                cursor.execute("INSERT INTO users (username, password, balance, role, created_by) VALUES (?, ?, 0, 'class_b', 'admin')", 
                               (uname, fixed_rand_pass))
        conn.commit()

init_db()

def check_auto_draw_board():
    with get_db() as conn:
        cursor = conn.cursor()
        now_beirut = get_beirut_time()
        date_str = now_beirut.strftime('%Y-%m-%d')
        
        cursor.execute("SELECT forced_admin_number, last_draw_date FROM game_board_state WHERE id=1")
        state = cursor.fetchone()
        if not state:
            return
            
        forced_num, last_draw_date = state[0], state[1]
        
        # التأكد من عدم السحب مرتين في نفس اليوم
        if last_draw_date == date_str:
            return

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
            cursor.execute("UPDATE game_board_state SET last_winner_msg=?, banner_end_time=?, forced_admin_number='', last_draw_date=? WHERE id=1", (msg, banner_end_time, date_str))
            conn.commit()

def check_and_auto_draw_game_three():
    with get_db() as conn:
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

def get_or_create_scratch_game(username):
    with get_db() as conn:
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
            return nums, [], 'playing', "اكشف 3 مربعات متطابقة واربح 20$!"
        else:
            hidden_numbers = list(map(int, row[0].split(','))) if row[0] else []
            selected_boxes = list(map(int, row[1].split(','))) if row[1] else []
            return hidden_numbers, selected_boxes, row[2], row[3]

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
    now_beirut = get_beirut_time()
    if now_beirut.hour == 21 and now_beirut.minute == 0:
        check_auto_draw_board()

    username = session['username']
    with get_db() as conn:
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
        g3_msg = g3_state[2]
        g3_rem = max(0, int(g3_timer_end - time.time())) if g3_is_full else 0

        cursor.execute("SELECT last_winner_msg FROM game_board_state WHERE id=1")
        board_msg = cursor.fetchone()[0]

        cursor.execute("SELECT game_name, winner_info, win_time FROM winners_log ORDER BY id DESC LIMIT 10")
        winners = cursor.fetchall()

    return jsonify({
        'balance': balance,
        'board': [dict(row) for row in board],
        'user_locked': user_locked,
        'user_spent': user_spent,
        'g3_slots': [dict(row) for row in g3_slots],
        'g3_is_full': g3_is_full,
        'g3_rem': g3_rem,
        'g3_msg': g3_msg,
        'board_msg': board_msg,
        'winners': [dict(row) for row in winners]
    })

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            user = cursor.fetchone()
        
        if user:
            session.clear()
            session['username'] = user['username']
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
    
    username = session['username']
    role = session['role']

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
        res = cursor.fetchone()
        user_balance = res[0] if res else 0

    hidden_nums, selected_boxes, scratch_status, scratch_msg = get_or_create_scratch_game(username)

    return render_template_string(DASHBOARD_PAGE, 
                                  username=username,
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
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, password, balance, role, created_by FROM users")
        all_users = cursor.fetchall()

        cursor.execute("SELECT game_name, total_collected, total_payouts FROM financial_stats")
        fin_data = cursor.fetchall()
        
        financial_report = []
        total_net_profit = 0
        for row in fin_data:
            net = row['total_collected'] - row['total_payouts']
            total_net_profit += net
            financial_report.append({
                'name': row['game_name'],
                'collected': row['total_collected'],
                'payouts': row['total_payouts'],
                'net': net
            })

        cursor.execute("SELECT forced_admin_number FROM game_board_state WHERE id=1")
        f_num = cursor.fetchone()[0]

        cursor.execute("SELECT forced_admin_slot FROM game_three_state WHERE id=1")
        f_slot = cursor.fetchone()[0]
    
    return render_template_string(ADMIN_PAGE, username=session['username'], all_users=all_users, financial_report=financial_report, total_net_profit=total_net_profit, f_num=f_num, f_slot=f_slot)

@app.route('/pick_number/<int:num>', methods=['POST'])
def pick_number(num):
    if 'username' not in session:
        return jsonify({'success': False, 'msg': 'غير مسجل الدخول'})
    username = session['username']
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
        balance = cursor.fetchone()[0]
        
        cursor.execute("SELECT status, owner FROM game_board WHERE number=?", (num,))
        row = cursor.fetchone()
        if row:
            status, owner = row['status'], row['owner']
            if status == 'available':
                cursor.execute("SELECT COUNT(*) FROM game_board WHERE owner=?", (username,))
                if cursor.fetchone()[0] < 36:
                    if balance >= 2:
                        cursor.execute("UPDATE game_board SET status='locked', owner=? WHERE number=?", (username, num))
                        cursor.execute("UPDATE users SET balance = balance - 2 WHERE username=?", (username,))
                        cursor.execute("UPDATE financial_stats SET total_collected = total_collected + 2.0 WHERE game_name=?", ("لوحة أرقام الحظ (80$)",))
                        conn.commit()
                    else:
                        return jsonify({'success': False, 'msg': 'رصيدك لا يكفي (تكلفة الحجز 2$)!'})
            elif status == 'locked' and owner == username:
                cursor.execute("UPDATE game_board SET status='available', owner=NULL WHERE number=?", (num,))
                cursor.execute("UPDATE users SET balance = balance + 2 WHERE username=?", (username,))
                cursor.execute("UPDATE financial_stats SET total_collected = total_collected - 2.0 WHERE game_name=?", ("لوحة أرقام الحظ (80$)",))
                conn.commit()
    return jsonify({'success': True})

@app.route('/pick_game_three/<int:slot_id>', methods=['POST'])
def pick_game_three(slot_id):
    if 'username' not in session:
        return jsonify({'success': False})
    username = session['username']
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
        balance = cursor.fetchone()[0]
        
        cursor.execute("SELECT status, owner FROM game_three WHERE slot_id=?", (slot_id,))
        row = cursor.fetchone()
        if row:
            status, owner = row['status'], row['owner']
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
                    return jsonify({'success': False, 'msg': 'رصيدك لا يكفي (تكلفة الحجز 50$)!'})
            elif status == 'locked' and owner == username:
                cursor.execute("UPDATE game_three SET status='available', owner=NULL WHERE slot_id=?", (slot_id,))
                cursor.execute("UPDATE users SET balance = balance + 50.0 WHERE username=?", (username,))
                cursor.execute("UPDATE financial_stats SET total_collected = total_collected - 50.0 WHERE game_name=?", ("اللعبة الملكية الفاخرة (200$)",))
                cursor.execute("UPDATE game_three_state SET is_full=0, timer_end=0, last_winner_msg=? WHERE id=1", 
                               ("تم إلغاء حجز، في انتظار اكتمال الخانات...",))
                conn.commit()
    return jsonify({'success': True})

@app.route('/play_scratch/<int:box_index>', methods=['POST'])
def play_scratch(box_index):
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
        balance = cursor.fetchone()[0]
        
    hidden_nums, selected_boxes, scratch_status, scratch_msg = get_or_create_scratch_game(username)
    
    with get_db() as conn:
        cursor = conn.cursor()
        if scratch_status == 'finished':
            if balance < 1.0:
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
            return redirect(url_for('dashboard'))
            
        if box_index in selected_boxes:
            return redirect(url_for('dashboard'))
            
        if len(selected_boxes) == 0:
            if balance < 1.0:
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
    return redirect(url_for('dashboard'))

@app.route('/reset_scratch', methods=['POST'])
def reset_scratch():
    if 'username' not in session:
        return redirect(url_for('login'))
    with get_db() as conn:
        cursor = conn.cursor()
        nums = [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5]
        random.shuffle(nums)
        cursor.execute("UPDATE scratch_games SET hidden_numbers=?, selected_boxes='', game_status='playing', message=? WHERE username=?",
                       (",".join(map(str, nums)), "بدأت محاولة جديدة، اختر 3 مربعات!", session['username']))
        conn.commit()
    return redirect(url_for('dashboard'))

@app.route('/admin_set_forced', methods=['POST'])
def admin_set_forced():
    if 'username' not in session or session.get('role') != 'admin':
        return "غير مسموح", 403
    f_num = request.form.get('forced_number', '').strip()
    f_slot = request.form.get('forced_slot', '').strip()
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE game_board_state SET forced_admin_number=? WHERE id=1", (f_num,))
        cursor.execute("UPDATE game_three_state SET forced_admin_slot=? WHERE id=1", (f_slot,))
        conn.commit()
    return redirect(url_for('admin_panel'))

@app.route('/create_user', methods=['POST'])
def create_user():
    if 'username' not in session or session.get('role') != 'admin':
        return "غير مسموح", 403
    new_user = request.form.get('new_user', '').strip()
    new_pass = request.form.get('new_pass', '').strip()
    role = request.form.get('account_role', 'class_b')
    
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password, balance, role, created_by) VALUES (?, ?, 0, ?, ?)",
                           (new_user, new_pass, role, session['username']))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
    return redirect(url_for('admin_panel'))

@app.route('/recharge_user', methods=['POST'])
def recharge_user():
    if 'username' not in session or session.get('role') != 'admin':
        return "غير مسموح", 403
    amt = float(request.form['amount'])
    t_user = request.form['target_user']
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = balance - ? WHERE username='admin'", (amt,))
        cursor.execute("UPDATE users SET balance = balance + ? WHERE username=?", (amt, t_user))
        conn.commit()
    return redirect(url_for('admin_panel'))

@app.route('/withdraw_user', methods=['POST'])
def withdraw_user():
    if 'username' not in session or session.get('role') != 'admin':
        return "غير مسموح", 403
    t_user = request.form['target_user']
    amount = float(request.form['amount'])
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE username=?", (t_user,))
        res = cursor.fetchone()
        if res and res[0] >= amount:
            cursor.execute("UPDATE users SET balance = balance - ? WHERE username=?", (amount, t_user))
            cursor.execute("UPDATE users SET balance = balance + ? WHERE username='admin'", (amount,))
            conn.commit()
    return redirect(url_for('admin_panel'))

@app.route('/change_password', methods=['POST'])
def change_password():
    if 'username' not in session or session.get('role') != 'admin':
        return "غير مسموح", 403
    t_user = request.form['target_user']
    new_pass = request.form['new_password'].strip()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password=? WHERE username=?", (new_pass, t_user))
        conn.commit()
    return redirect(url_for('admin_panel'))

# القوالب الأمامية تظل كما هي بنفس التصميم المتطور (DASHBOARD_PAGE, ADMIN_PAGE, LOGIN_PAGE)
DASHBOARD_PAGE = """...""" # (نفس قالب الواجهة السابق)
ADMIN_PAGE = """..."""       # (نفس قالب الأدمن السابق)
LOGIN_PAGE = """..."""       # (نفس قالب الدخول السابق)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
