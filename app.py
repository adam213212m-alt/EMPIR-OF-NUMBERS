from flask import Flask, render_template_string, request, redirect, url_for, session
import sqlite3
import random
import time
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
app.secret_key = 'empire_of_numbers_secret_key'

def get_beirut_time():
    return datetime.now(timezone(timedelta(hours=3)))

def init_db():
    conn = sqlite3.connect('empire.db')
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
    try:
        cursor.execute("ALTER TABLE game_board_state ADD COLUMN banner_end_time REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    cursor.execute('SELECT COUNT(*) FROM game_board_state')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO game_board_state (id, last_winner_msg, banner_end_time) VALUES (1, "بانتظار السحب اليومي الساعة 9:00 مساءً...", 0)')
            
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
            banner_end_time REAL DEFAULT 0
        )
    ''')
    try:
        cursor.execute("ALTER TABLE game_three_state ADD COLUMN is_full INTEGER DEFAULT 0")
        cursor.execute("ALTER TABLE game_three_state ADD COLUMN timer_end REAL DEFAULT 0")
        cursor.execute("ALTER TABLE game_three_state ADD COLUMN banner_end_time REAL DEFAULT 0")
    except sqlite3.OperationalError:
        pass

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
    
    cursor.execute("SELECT * FROM users WHERE username='admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, balance, role, created_by) VALUES (?, ?, ?, ?, ?)", 
                       ('admin', 'admin123', 1000000, 'admin', 'system'))
    
    conn.commit()
    conn.close()

init_db()

def check_auto_draw_board(forced_number_from_admin=None):
    conn = sqlite3.connect('empire.db')
    cursor = conn.cursor()
    winning_number, winner_owner = None, None
    
    if forced_number_from_admin:
        winning_number = int(forced_number_from_admin)
        cursor.execute("SELECT owner FROM game_board WHERE number=?", (winning_number,))
        res = cursor.fetchone()
        winner_owner = res[0] if (res and res[0]) else None
    else:
        cursor.execute("SELECT number, owner FROM game_board WHERE status='locked'")
        locked = cursor.fetchall()
        if locked:
            winning_number, winner_owner = random.choice(locked)
            
    if winning_number:
        banner_end_time = time.time() + 15
        if winner_owner:
            cursor.execute("UPDATE users SET balance = balance + 80.0 WHERE username=?", (winner_owner,))
            msg = f"🎉 مبروك {winner_owner} - ربحت 80$ (الرقم {winning_number})! 🎉"
            cursor.execute("INSERT INTO winners_log (game_name, winner_info, win_time) VALUES (?, ?, ?)", 
                           ("لوحة أرقام الحظ (80$)", f"الرقم {winning_number} - الفائز: {winner_owner} (80$)", time.strftime('%Y-%m-%d %H:%M')))
            cursor.execute("UPDATE financial_stats SET total_payouts = total_payouts + 80.0 WHERE game_name=?", ("لوحة أرقام الحظ (80$)",))
        else:
            msg = f"🏆 فاز الرقم ({winning_number}) ولم يكن محجوزاً لأحد."
            
        cursor.execute("UPDATE game_board SET status='available', owner=NULL")
        cursor.execute("UPDATE game_board_state SET last_winner_msg=?, banner_end_time=? WHERE id=1", (msg, banner_end_time))
        conn.commit()
    conn.close()

def check_and_auto_draw_game_three():
    conn = sqlite3.connect('empire.db')
    cursor = conn.cursor()
    cursor.execute("SELECT is_full, timer_end FROM game_three_state WHERE id=1")
    state = cursor.fetchone()
    if state and state[0] == 1:
        timer_end = state[1]
        if time.time() >= timer_end:
            cursor.execute("SELECT slot_id, owner FROM game_three WHERE status='locked'")
            locked_slots = cursor.fetchall()
            if locked_slots:
                winning_slot, winner_owner = random.choice(locked_slots)
                banner_end_time = time.time() + 10
                if winner_owner:
                    cursor.execute("UPDATE users SET balance = balance + 250.0 WHERE username=?", (winner_owner,))
                    msg = f"🏆 {winner_owner} - 250$ WIN 🏆"
                    cursor.execute("INSERT INTO winners_log (game_name, winner_info, win_time) VALUES (?, ?, ?)", 
                                   ("اللعبة الملكية الفاخرة", f"الخانة {winning_slot} - الفائز: {winner_owner} (250$)", time.strftime('%Y-%m-%d %H:%M')))
                    cursor.execute("UPDATE financial_stats SET total_payouts = total_payouts + 250.0 WHERE game_name=?", ("اللعبة الملكية الفاخرة",))
                else:
                    msg = f"💎 فاز الرقم الفاخر ({winning_slot}) ولم يكن محجوزاً."
                
                cursor.execute("UPDATE game_three SET status='available', owner=NULL")
                cursor.execute("UPDATE game_three_state SET is_full=0, timer_end=0, last_winner_msg=?, banner_end_time=? WHERE id=1", (msg, banner_end_time))
                conn.commit()
    conn.close()

def get_or_create_scratch_game(username):
    conn = sqlite3.connect('empire.db')
    cursor = conn.cursor()
    cursor.execute("SELECT hidden_numbers, selected_boxes, game_status, message FROM scratch_games WHERE username=?", (username,))
    row = cursor.fetchone()
    if not row:
        nums = [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5]
        random.shuffle(nums)
        hidden_str = ",".join(map(str, nums))
        cursor.execute("INSERT INTO scratch_games (username, hidden_numbers, selected_boxes, game_status, message) VALUES (?, ?, '', 'playing', ?)",
                       (username, hidden_str, "اختر 3 مربعات واكتشف حظك!"))
        conn.commit()
        selected_boxes, hidden_numbers, message, status = [], nums, "اختر 3 مربعات واكتشف حظك!", 'playing'
    else:
        hidden_numbers = list(map(int, row[0].split(','))) if row[0] else []
        selected_boxes = list(map(int, row[1].split(','))) if row[1] else []
        status, message = row[2], row[3]
    conn.close()
    return hidden_numbers, selected_boxes, status, message

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        conn = sqlite3.connect('empire.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['username'] = user[1]
            session['password'] = user[2]
            session['balance'] = user[3]
            session['role'] = user[4]
            return redirect(url_for('dashboard'))
        else:
            error = 'اسم المستخدم أو كلمة المرور غير صحيحة'
            
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
        check_and_auto_draw_game_three()
        
        now_beirut = get_beirut_time()
        if now_beirut.hour == 21 and now_beirut.minute == 0:
            check_auto_draw_board(None)

        username = session['username']
        conn = sqlite3.connect('empire.db')
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
        board_banner_end = board_state[1] if board_state else 0
        show_board_banner = time.time() < board_banner_end

        cursor.execute("SELECT slot_id, status, owner FROM game_three")
        game_three_slots = cursor.fetchall()

        cursor.execute("SELECT is_full, timer_end, last_winner_msg, banner_end_time FROM game_three_state WHERE id=1")
        g3_state = cursor.fetchone()
        g3_is_full = g3_state[0]
        g3_timer_end = g3_state[1]
        g3_last_winner = g3_state[2]
        banner_end_time = g3_state[3]
        
        show_g3_banner = time.time() < banner_end_time
        current_time = time.time()
        g3_remaining_time = max(0, int(g3_timer_end - current_time)) if g3_is_full else 0

        cursor.execute("SELECT game_name, winner_info, win_time FROM winners_log ORDER BY id DESC LIMIT 10")
        winners_records = cursor.fetchall()

        conn.close()
    except Exception as e:
        session.clear()
        return redirect(url_for('login'))

    winning_num = session.get('winning_num', None)
    hidden_nums, selected_boxes, scratch_status, scratch_msg = get_or_create_scratch_game(username)

    return render_template_string(DASHBOARD_PAGE, 
                                  username=username,
                                  password=session.get('password', ''),
                                  role=session.get('role', 'class_b'), 
                                  balance=user_balance, 
                                  board=board,
                                  user_locked_numbers=user_locked_numbers,
                                  user_total_spent=user_total_spent,
                                  board_last_winner_msg=board_last_winner_msg,
                                  show_board_banner=show_board_banner,
                                  game_three_slots=game_three_slots,
                                  g3_is_full=g3_is_full,
                                  g3_remaining_time=g3_remaining_time,
                                  g3_last_winner=g3_last_winner,
                                  show_g3_banner=show_g3_banner,
                                  winners_records=winners_records,
                                  winning_num=winning_num,
                                  hidden_nums=hidden_nums,
                                  selected_boxes=selected_boxes,
                                  scratch_status=scratch_status,
                                  scratch_msg=scratch_msg)

@app.route('/admin_panel')
def admin_panel():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('dashboard'))
    
    conn = sqlite3.connect('empire.db')
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
    conn = sqlite3.connect('empire.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
    balance = cursor.fetchone()[0]
    
    cursor.execute("SELECT status, owner FROM game_board WHERE number=?", (num,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return redirect(url_for('dashboard'))
        
    status, owner = row[0], row[1]
    
    if status == 'available':
        cursor.execute("SELECT COUNT(*) FROM game_board WHERE owner=?", (username,))
        user_count = cursor.fetchone()[0]
        if user_count < 36 and balance >= 2:
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
    conn = sqlite3.connect('empire.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
    balance = cursor.fetchone()[0]
    
    cursor.execute("SELECT status, owner FROM game_three WHERE slot_id=?", (slot_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return redirect(url_for('dashboard'))
        
    status, owner = row[0], row[1]
    
    if status == 'available' and balance >= 50.0:
        cursor.execute("UPDATE game_three SET status='locked', owner=? WHERE slot_id=?", (username, slot_id))
        cursor.execute("UPDATE users SET balance = balance - 50.0 WHERE username=?", (username,))
        cursor.execute("UPDATE financial_stats SET total_collected = total_collected + 50.0 WHERE game_name=?", ("اللعبة الملكية الفاخرة",))
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) FROM game_three WHERE status='available'")
        if cursor.fetchone()[0] == 0:
            timer_end = time.time() + 60
            cursor.execute("UPDATE game_three_state SET is_full=1, timer_end=?, last_winner_msg=? WHERE id=1", 
                           (timer_end, "⚠️ اكتملت الخانات الخمسة! يبدأ سحب الـ 250$ خلال دقيقة..."))
            conn.commit()
            
    elif status == 'locked' and owner == username:
        cursor.execute("UPDATE game_three SET status='available', owner=NULL WHERE slot_id=?", (slot_id,))
        cursor.execute("UPDATE users SET balance = balance + 50.0 WHERE username=?", (username,))
        cursor.execute("UPDATE financial_stats SET total_collected = total_collected - 50.0 WHERE game_name=?", ("اللعبة الملكية الفاخرة",))
        cursor.execute("UPDATE game_three_state SET is_full=0, timer_end=0, last_winner_msg=? WHERE id=1", 
                       ("تم إلغاء حجز، في انتظار اكتمال الخانات...",))
        conn.commit()
        
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/play_scratch/<int:box_index>', methods=['POST'])
def play_scratch(box_index):
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    conn = sqlite3.connect('empire.db')
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
    balance = cursor.fetchone()[0]
    if balance < 1:
        conn.close()
        return redirect(url_for('dashboard'))
    
    hidden_nums, selected_boxes, scratch_status, scratch_msg = get_or_create_scratch_game(username)
    if scratch_status == 'finished':
        nums = [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5]
        random.shuffle(nums)
        hidden_str = ",".join(map(str, nums))
        selected_boxes = [box_index]
        cursor.execute("UPDATE users SET balance = balance - 1 WHERE username=?", (username,))
        cursor.execute("UPDATE financial_stats SET total_collected = total_collected + 1.0 WHERE game_name=?", ("لعبة الـ 15 مربعاً (15$)",))
        cursor.execute("UPDATE scratch_games SET hidden_numbers=?, selected_boxes=?, game_status='playing', message=? WHERE username=?",
                       (hidden_str, str(box_index), "اخترت مربعاً، بقي لك اختياران...", username))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
        
    if box_index in selected_boxes:
        conn.close()
        return redirect(url_for('dashboard'))
        
    if len(selected_boxes) == 0:
        cursor.execute("UPDATE users SET balance = balance - 1 WHERE username=?", (username,))
        cursor.execute("UPDATE financial_stats SET total_collected = total_collected + 1.0 WHERE game_name=?", ("لعبة الـ 15 مربعاً (15$)",))
        
    selected_boxes.append(box_index)
    if len(selected_boxes) == 3:
        v1, v2, v3 = hidden_nums[selected_boxes[0]], hidden_nums[selected_boxes[1]], hidden_nums[selected_boxes[2]]
        if v1 == v2 == v3:
            cursor.execute("UPDATE users SET balance = balance + 15 WHERE username=?", (username,))
            scratch_msg = f"🎉 مبروك ربحت 15$! (ثلاثة أرقام {v1})"
            cursor.execute("INSERT INTO winners_log (game_name, winner_info, win_time) VALUES (?, ?, ?)", 
                           ("لعبة الـ 15 مربعاً (15$)", f"الفائز: {username}", time.strftime('%Y-%m-%d %H:%M')))
            cursor.execute("UPDATE financial_stats SET total_payouts = total_payouts + 15.0 WHERE game_name=?", ("لعبة الـ 15 مربعاً (15$)",))
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
    conn = sqlite3.connect('empire.db')
    cursor = conn.cursor()
    nums = [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5]
    random.shuffle(nums)
    cursor.execute("UPDATE scratch_games SET hidden_numbers=?, selected_boxes='', game_status='playing', message=? WHERE username=?",
                   (",".join(map(str, nums)), "بدأت محاولة جديدة، اختر 3 مربعات!", session['username']))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/draw_winner', methods=['POST'])
def draw_winner():
    if 'username' not in session or session.get('role') != 'admin':
        return "غير مسموح", 403
    forced_number = request.form.get('forced_number')
    check_auto_draw_board(forced_number)
    return redirect(url_for('admin_panel'))

@app.route('/draw_game_three', methods=['POST'])
def draw_game_three():
    if 'username' not in session or session.get('role') != 'admin':
        return "غير مسموح", 403
    forced_slot = request.form.get('forced_slot')
    conn = sqlite3.connect('empire.db')
    cursor = conn.cursor()
    winning_slot, winner_owner = None, None
    
    if forced_slot and forced_slot.isdigit():
        winning_slot = int(forced_slot)
        cursor.execute("SELECT owner FROM game_three WHERE slot_id=?", (winning_slot,))
        res = cursor.fetchone()
        winner_owner = res[0] if (res and res[0]) else None
    else:
        cursor.execute("SELECT slot_id, owner FROM game_three WHERE status='locked'")
        locked = cursor.fetchall()
        if locked:
            winning_slot, winner_owner = random.choice(locked)
            
    if winning_slot:
        banner_end_time = time.time() + 10
        if winner_owner:
            cursor.execute("UPDATE users SET balance = balance + 250.0 WHERE username=?", (winner_owner,))
            msg = f"🏆 {winner_owner} - 250$ WIN 🏆"
            cursor.execute("INSERT INTO winners_log (game_name, winner_info, win_time) VALUES (?, ?, ?)", 
                           ("اللعبة الملكية الفاخرة", f"الخانة {winning_slot} - الفائز: {winner_owner} (250$)", time.strftime('%Y-%m-%d %H:%M')))
            cursor.execute("UPDATE financial_stats SET total_payouts = total_payouts + 250.0 WHERE game_name=?", ("اللعبة الملكية الفاخرة",))
        else:
            msg = f"💎 فاز الرقم الفاخر ({winning_slot}) ولم يكن محجوزاً."
            
        cursor.execute("UPDATE game_three SET status='available', owner=NULL")
        cursor.execute("UPDATE game_three_state SET is_full=0, timer_end=0, last_winner_msg=?, banner_end_time=? WHERE id=1", (msg, banner_end_time))
        conn.commit()
    else:
        cursor.execute("UPDATE game_three_state SET last_winner_msg=? WHERE id=1", ("⚠️ لا توجد أرقام محجوزة بالسحب الملكي!",))
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
    
    conn = sqlite3.connect('empire.db')
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
    conn = sqlite3.connect('empire.db')
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
    conn = sqlite3.connect('empire.db')
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
        
        .luxury-game-section { background: linear-gradient(135deg, #1e1b4b, #31103d, #0f172a); border: 3px solid #fbbf24; padding: 25px; border-radius: 16px; text-align: center; position: relative; overflow: hidden; }
        .luxury-game-section h2 { color: #fbbf24; margin-top: 0; font-size: 26px; }
        
        .winner-win-banner { background: linear-gradient(90deg, #d97706, #fbbf24, #d97706); color: #000; padding: 15px; font-weight: bold; font-size: 22px; border-radius: 10px; margin-bottom: 15px; box-shadow: 0 0 25px rgba(251,191,36,0.8); animation: pulseBanner 0.8s infinite alternate; border: 2px solid #fff; }
        @keyframes pulseBanner { 0% { transform: scale(1); } 100% { transform: scale(1.03); } }

        .luxury-slots-container { display: flex; justify-content: center; gap: 15px; margin: 20px 0; flex-wrap: wrap; }
        .luxury-slot-form { display: flex; }
        .luxury-slot-btn { background: linear-gradient(145deg, #111827, #1f2937); border: 2px solid #fbbf24; width: 110px; height: 110px; border-radius: 14px; color: #fff; font-size: 20px; font-weight: bold; cursor: pointer; display: flex; flex-direction: column; align-items: center; justify-content: center; }
        .luxury-slot-btn.locked { background: linear-gradient(145deg, #991b1b, #7f1d1d); border-color: #f87171; }
        .luxury-owner { font-size: 11px; color: #fde047; margin-top: 6px; max-width: 90px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        
        .timer-box { background: rgba(15, 23, 42, 0.8); border: 1px solid #38bdf8; padding: 12px 20px; border-radius: 10px; display: inline-block; font-size: 16px; font-weight: bold; color: #38bdf8; margin-top: 10px; width: 100%; box-sizing: border-box; text-align: center; }
        
        .games-grid { display: grid; grid-template-columns: 2fr 1.2fr; gap: 20px; margin-top: 20px; }
        @media (max-width: 1000px) { .games-grid { grid-template-columns: 1fr; } }
        
        .board-section { background: linear-gradient(135deg, #d4af37, #aa771c); padding: 20px; border-radius: 12px; }
        .board-section h2 { color: #111; margin-top: 0; }
        .player-summary-box { background: #0f172a; border: 2px dashed #111; padding: 12px 15px; border-radius: 8px; margin-bottom: 15px; color: #f8fafc; display: flex; justify-content: space-around; flex-wrap: wrap; gap: 10px; font-size: 14px; font-weight: bold; }
        .summary-item { background: #1e293b; padding: 6px 12px; border-radius: 6px; border: 1px solid #475569; }
        
        .board { display: grid; grid-template-columns: repeat(10, 1fr); gap: 6px; margin-top: 15px; }
        .cell-form { display: flex; }
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
        
        .roulette-container { background: #1e293b; padding: 20px; border-radius: 12px; text-align: center; margin-top: 20px; }
        .roulette-wheel { position: relative; width: 130px; height: 130px; margin: 10px auto; border-radius: 50%; background: conic-gradient(#3b82f6 0deg 72deg, #ef4444 72deg 144deg, #22c55e 144deg 216deg, #eab308 216deg 288deg, #a855f7 288deg 360deg); border: 5px solid #fbbf24; display: flex; align-items: center; justify-content: center; }
        .ball-inner { font-size: 20px; font-weight: bold; color: #1e293b; background: #ffffff; width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 3px solid #fbbf24; }
    </style>
    <script>
        {% if g3_is_full and g3_remaining_time > 0 %}
        let g3TimeLeft = {{ g3_remaining_time }};
        const countdownG3El = document.getElementById('countdownG3');
        const g3TimerInterval = setInterval(() => {
            g3TimeLeft--;
            if(countdownG3El) countdownG3El.innerText = g3TimeLeft;
            if(g3TimeLeft <= 0) {
                clearInterval(g3TimerInterval);
                location.reload();
            }
        }, 1000);
        {% elif g3_is_full and g3_remaining_time <= 0 %}
        setTimeout(() => { location.reload(); }, 500);
        {% endif %}

        setTimeout(() => {
            location.reload();
        }, 3000);
    </script>
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
            <!-- اللعبة الملكية الفاخرة -->
            <div class="luxury-game-section">
                <h2>💎 اللعبة الملكية الفاخرة (5 أرقام كبرى)</h2>
                
                {% if show_g3_banner %}
                <div class="winner-win-banner">
                    🏆 {{ g3_last_winner }} 🏆
                </div>
                {% else %}
                <p style="color: #cbd5e1; font-size: 14px;">قيمة الرقم الواحد: 50$ | الجائزة الكبرى: 250$ فورية!</p>
                <div class="timer-box">
                    {% if g3_is_full %}
                        ⏳ اكتملت الخانات الـ 5! تدور رولات السحب خلال <span id="countdownG3" style="color: #fbbf24; font-size: 18px;">{{ g3_remaining_time }}</span> ثانية...
                    {% else %}
                        ✨ حجز 5 خانات يبدأ عداد دقيقة السحب برولات الأرقام التفاعلية
                    {% endif %}
                </div>
                {% endif %}

                <div class="luxury-slots-container">
                    {% for slot_id, status, owner in game_three_slots %}
                    <form action="/pick_game_three/{{ slot_id }}" method="POST" class="luxury-slot-form">
                        <button type="submit" class="luxury-slot-btn {% if status == 'locked' %}locked{% endif %}">
                            <span style="font-size: 22px;">رقم {{ slot_id }}</span>
                            <span style="font-size: 11px; color: #38bdf8; margin-top: 4px;">50$</span>
                            {% if owner %}
                                <span class="luxury-owner">{{ owner }}</span>
                                {% if owner == username %}<span style="font-size: 9px; color: #34d399;">(حجزك - للتراجع)</span>{% endif %}
                            {% endif %}
                        </button>
                    </form>
                    {% endfor %}
                </div>
            </div>

            <div class="games-grid">
                <!-- لوحة أرقام الحظ -->
                <div class="board-section">
                    <h2>لوحة أرقام الحظ (تكلفة الرقم: 2$ | الجائزة: 80$)</h2>
                    
                    {% if show_board_banner %}
                    <div class="winner-win-banner" style="background: linear-gradient(90deg, #059669, #34d399, #059669); color: #fff;">
                        🎉 {{ board_last_winner_msg }} 🎉
                    </div>
                    {% else %}
                    <div class="timer-box" style="margin-bottom: 12px;">
                        ⏰ السحب اليومي التلقائي: الساعة 9:00 مساءً بتوقيت بيروت<br>
                        <span style="color: #fbbf24; font-size: 14px; margin-top: 5px; display: block;">✨ {{ board_last_winner_msg }}</span>
                    </div>
                    {% endif %}

                    <div class="player-summary-box">
                        <div class="summary-item">🎯 أرقامك المحجوزة: <span style="color: #fbbf24;">{% if user_locked_numbers %}{{ user_locked_numbers | join(', ') }}{% else %}لا توجد{% endif %}</span></div>
                        <div class="summary-item">💵 المدفوع: <span style="color: #ef4444;">${{ user_total_spent }}</span></div>
                        <div class="summary-item">💰 المتبقي: <span style="color: #34d399;">${{ balance }}</span></div>
                    </div>
                    <div class="board">
                        {% for num, status, owner in board %}
                            <form action="/pick_number/{{ num }}" method="POST" class="cell-form">
                                <button type="submit" class="cell {% if status == 'locked' %}locked{% endif %}">
                                    <span style="font-size: 15px;">{{ num }}</span>
                                    {% if owner %}
                                        <span class="owner-tag">{{ owner }}</span>
                                        {% if owner == username %}<span style="font-size: 8px; color: #34d399;">إلغاء حجزك</span>{% endif %}
                                    {% endif %}
                                </button>
                            </form>
                        {% endfor %}
                    </div>
                </div>

                <!-- لعبة الـ 15 مربعاً الفاخرة -->
                <div class="scratch-section">
                    <div>
                        <h2>✨ لعبة الـ 15 مربعاً الفاخرة</h2>
                        <p style="color: #94a3b8; font-size: 12px;">اختر 3 مربعات (التكلفة: 1$ | الجائزة: 15$)</p>
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

            <div class="roulette-container">
                <h2>🔮 روليت سحب الأرقام التفاعلي (رول بـ 5 خانات للسحب)</h2>
                <div class="roulette-wheel" id="rouletteWheel">
                    <div class="ball-inner" id="ballDisplay">🎲</div>
                </div>
            </div>
        </div>

        <!-- سجل الفائزين آخر 24 ساعة -->
        <div class="winners-sidebar">
            <h3>🏆 لوحة شرف الفائزين (آخر 24 ساعة)</h3>
            {% if winners_records %}
                {% for game, info, time_str in winners_records %}
                <div class="winner-record-item">
                    <div style="color: #fbbf24; font-weight: bold;">{{ game }}</div>
                    <div style="color: #e2e8f0; margin-top: 3px;">{{ info }}</div>
                    <div style="color: #94a3b8; font-size: 11px; margin-top: 3px;">⏱ {{ time_str }}</div>
                </div>
                {% endfor %}
            {% else %}
                <p style="color: #94a3b8; text-align: center; font-size: 13px;">لا توجد سجلات فوز مسجلة حالياً!</p>
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
    <title>لوحة تحكم الأدمن المستقلة</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; padding: 20px; margin: 0; }
        .admin-header { display: flex; justify-content: space-between; align-items: center; background: #1e293b; padding: 15px 25px; border-radius: 12px; border: 2px solid #fbbf24; margin-bottom: 25px; flex-wrap: wrap; gap: 10px; }
        .admin-panel { background: #1e293b; padding: 25px; border-radius: 12px; border: 2px solid #fbbf24; max-width: 900px; margin: 0 auto; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        input, select { width: 100%; padding: 10px; border-radius: 6px; background: #1e293b; color: white; border: 1px solid #475569; box-sizing: border-box; }
        button { padding: 10px 20px; font-weight: bold; border: none; border-radius: 6px; cursor: pointer; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #475569; padding: 12px; text-align: center; }
        th { background: #334155; color: #fbbf24; }
        .back-btn { background: #3b82f6; color: white; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold; }
        .manual-refresh-btn { background: #10b981; color: black; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold; cursor: pointer; }
        .finance-card { background: #111827; border: 1px solid #38bdf8; padding: 15px; border-radius: 8px; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="admin-header">
        <h2 style="color: #fbbf24; margin: 0;">👑 لوحة تحكم الأدمن المستقلة</h2>
        <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
            <button class="manual-refresh-btn" onclick="location.reload();">🔄 تحديث البيانات يدويًا</button>
            <a href="/dashboard" class="back-btn">⬅️ العودة للعبة الرئيسية</a>
            <a href="/logout" style="background: #ef4444; color: white; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold;">🚪 خروج</a>
        </div>
    </div>

    <div class="admin-panel">
        <h3 style="color: #38bdf8; border-bottom: 1px solid #475569; padding-bottom: 8px;">📊 التقارير المالية الشهرية (أرباح وخسائر الألعاب)</h3>
        
        <div style="display: grid; grid-template-columns: 1fr; gap: 15px; margin-bottom: 25px;">
            {% for row in financial_report %}
            <div class="finance-card">
                <h4 style="margin: 0 0 10px 0; color: #fbbf24;">🎮 {{ row.name }}</h4>
                <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 10px; font-size: 14px;">
                    <div>💵 المبلغ المدفوع من اللاعبين: <b style="color: #34d399;">${{ row.collected }}</b></div>
                    <div>🎁 المبلغ المدفوع للرابحين: <b style="color: #ef4444;">${{ row.payouts }}</b></div>
                    <div>📈 صافي الأرباح / الخسائر: <b style="color: {% if row.net >= 0 %}#34d399{% else %}#ef4444{% endif %};">${{ row.net }}</b></div>
                </div>
            </div>
            {% endfor %}
            
            <div style="background: linear-gradient(135deg, #065f46, #047857); padding: 15px; border-radius: 8px; border: 2px solid #34d399; text-align: center;">
                <h3 style="margin: 0; color: #fff;">💎 صافي الربح الشهري الإجمالي لجميع الألعاب: <span style="color: #fbbf24; font-size: 24px;">${{ total_net_profit }}</span></h3>
            </div>
        </div>

        <div style="background: #334155; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <h4 style="margin-top: 0; color: #38bdf8;">👤 إنشاء حساب جديد (لا يسمح بأسماء متشابهة):</h4>
            <form action="/create_user" method="POST" style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
                <div style="flex: 1;"><input type="text" name="new_user" placeholder="اسم المستخدم" required></div>
                <div style="flex: 1;"><input type="password" name="new_pass" placeholder="كلمة المرور" required></div>
                <div>
                    <select name="account_role">
                        <option value="class_b">فئة B</option>
                        <option value="class_a">فئة A</option>
                    </select>
                </div>
                <div><button type="submit" style="background: #3b82f6; color: white;">إنشاء الحساب</button></div>
            </form>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;">
            <form action="/recharge_user" method="POST" style="background: #334155; padding: 15px; border-radius: 8px; display: flex; flex-direction: column; gap: 10px;">
                <h4 style="margin: 0; color: #22c55e;">⚡ شحن رصيد للمستخدم:</h4>
                <select name="target_user" required>
                    <option value="">اختر المستخدم</option>
                    {% for u in all_users %}<option value="{{ u[0] }}">{{ u[0] }} (رصيده: ${{ u[2] }})</option>{% endfor %}
                </select>
                <input type="number" name="amount" placeholder="المبلغ ($)" required>
                <button type="submit" style="background: #22c55e; color: black;">تأكيد الشحن</button>
            </form>

            <form action="/withdraw_user" method="POST" style="background: #334155; padding: 15px; border-radius: 8px; display: flex; flex-direction: column; gap: 10px;">
                <h4 style="margin: 0; color: #ef4444;">💸 سحب رصيد وتحويله لحسابك:</h4>
                <select name="target_user" required>
                    <option value="">اختر المستخدم</option>
                    {% for u in all_users %}{% if u[0] != 'admin' %}<option value="{{ u[0] }}">{{ u[0] }} (رصيده: ${{ u[2] }})</option>{% endif %}{% endfor %}
                </select>
                <input type="number" name="amount" placeholder="المبلغ المراد سحبه ($)" required>
                <button type="submit" style="background: #ef4444; color: white;">سحب الرصيد</button>
            </form>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 25px;">
            <div style="background: #111827; padding: 15px; border-radius: 8px; border: 1px solid #fbbf24;">
                <h4 style="color: #fbbf24; margin-top: 0;">🎯 سحب الحظ اليومي (تحديد فائز سري خفية):</h4>
                <form action="/draw_winner" method="POST" style="display: flex; flex-direction: column; gap: 10px;">
                    <select name="forced_number">
                        <option value="">-- اختياري: حدد الرقم الفائز سرياً --</option>
                        {% for i in range(1, 51) %}<option value="{{ i }}">رقم الفوز: {{ i }}</option>{% endfor %}
                    </select>
                    <button type="submit" style="background: #fbbf24; color: black;">تنفيذ سحب الحظ الفوري</button>
                </form>
            </div>

            <div style="background: #111827; padding: 15px; border-radius: 8px; border: 1px solid #fbbf24;">
                <h4 style="color: #fbbf24; luxury-game-section; color: #fbbf24; margin-top: 0;">💎 اللعبة الملكية (تحديد فائز سري وخاص):</h4>
                <form action="/draw_game_three" method="POST" style="display: flex; flex-direction: column; gap: 10px;">
                    <select name="forced_slot">
                        <option value="">-- اختياري: حدد الخانة الفائزة سراً --</option>
                        {% for i in range(1, 6) %}<option value="{{ i }}">الخانة الفائزة: {{ i }}</option>{% endfor %}
                    </select>
                    <button type="submit" style="background: #fbbf24; color: black;">تنفيذ السحب الملكي الفاخر (250$)</button>
                </form>
            </div>
        </div>
        
        <h4 style="color: #38bdf8;">📋 جدول كافة الحسابات والأسماء والأرصدة والكلمات السرية المفعلة:</h4>
        <table>
            <tr>
                <th>اسم المستخدم</th>
                <th>كلمة المرور</th>
                <th>الرصيد الحالي</th>
                <th>الفئة / الدور</th>
                <th>أنشئ بواسطة</th>
            </tr>
            {% for u in all_users %}
            <tr>
                <td><b>{{ u[0] }}</b></td>
                <td><code style="background: #000; padding: 3px 6px; border-radius: 4px; color: #facc15;">{{ u[1] }}</code></td>
                <td><span style="color: #34d399; font-weight: bold;">${{ u[2] }}</span></td>
                <td>{{ u[3] }}</td>
                <td>{{ u[4] }}</td>
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
    <title>تسجيل الدخول - إمبراطورية الأرقام</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-box { background: #1e293b; padding: 40px; border-radius: 12px; box-shadow: 0 8px 16px rgba(0,0,0,0.5); width: 320px; text-align: center; border: 1px solid #334155; }
        input { width: 100%; padding: 12px; margin: 10px 0; border-radius: 6px; border: 1px solid #475569; background: #334155; color: white; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #fbbf24; color: black; font-weight: bold; border: none; border-radius: 6px; cursor: pointer; margin0-top: 10px; font-size: 16px; }
        .error { color: #ef4444; margin-bottom: 10px; font-weight: bold; }
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
