from flask import Flask, render_template_string, request, redirect, url_for, session
import sqlite3
import random
import time

app = Flask(__name__)
app.secret_key = 'empire_of_numbers_secret_key'

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
            is_full INTEGER DEFAULT 0,
            timer_end REAL DEFAULT 0,
            last_winner_msg TEXT DEFAULT ''
        )
    ''')
    cursor.execute('SELECT COUNT(*) FROM game_board_state')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO game_board_state (id, is_full, timer_end, last_winner_msg) VALUES (1, 0, 0, "بانتظار اكتمال الـ 50 رقماً...")')
            
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
            last_winner_msg TEXT DEFAULT ''
        )
    ''')
    cursor.execute('SELECT COUNT(*) FROM game_three_state')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO game_three_state (id, is_full, timer_end, last_winner_msg) VALUES (1, 0, 0, "بانتظار اكتمال الأرقام الخمسة...")')
    
    cursor.execute("SELECT * FROM users WHERE role='admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, balance, role, created_by) VALUES (?, ?, ?, ?)", 
                       ('admin', 'admin123', 1000000, 'admin'))
    
    conn.commit()
    conn.close()

init_db()

def check_and_auto_draw_game_board():
    conn = sqlite3.connect('empire.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT is_full, timer_end FROM game_board_state WHERE id=1")
    state = cursor.fetchone()
    if state and state[0] == 1:
        timer_end = state[1]
        if time.time() >= timer_end:
            cursor.execute("SELECT number, owner FROM game_board WHERE status='locked'")
            locked_numbers = cursor.fetchall()
            if locked_numbers:
                winning_number, winner_owner = random.choice(locked_numbers)
                prize = 80.0
                if winner_owner:
                    cursor.execute("UPDATE users SET balance = balance + ? WHERE username=?", (prize, winner_owner))
                    msg = f"⚡ (سحب تلقائي) الكرة الفائزة رقم ({winning_number}) والمحظوظ الفائز هو: {winner_owner} بجائزة 80$!"
                else:
                    msg = f"⚡ (سحب تلقائي) الكرة الفائزة رقم ({winning_number}) ولم تكن محجوزة."
                
                cursor.execute("UPDATE game_board SET status='available', owner=NULL")
                cursor.execute("UPDATE game_board_state SET is_full=0, timer_end=0, last_winner_msg=? WHERE id=1", (msg,))
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
                prize = 200.0
                if winner_owner:
                    cursor.execute("UPDATE users SET balance = balance + ? WHERE username=?", (prize, winner_owner))
                    msg = f"⚡ (سحب تلقائي) الفائز باللعبة الفاخرة هو: {winner_owner} في الرقم ({winning_slot}) بجائزة 200$!"
                else:
                    msg = f"⚡ (سحب تلقائي) فاز الرقم ({winning_slot}) ولكنه لم يكن محجوزاً."
                
                cursor.execute("UPDATE game_three SET status='available', owner=NULL")
                cursor.execute("UPDATE game_three_state SET is_full=0, timer_end=0, last_winner_msg=? WHERE id=1", (msg,))
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
        selected_boxes = []
        hidden_numbers = nums
        message = "اختر 3 مربعات واكتشف حظك!"
        status = 'playing'
    else:
        hidden_numbers = list(map(int, row[0].split(','))) if row[0] else []
        selected_boxes = list(map(int, row[1].split(','))) if row[1] else []
        status = row[2]
        message = row[3]
        
    conn.close()
    return hidden_numbers, selected_boxes, status, message

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('empire.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session['username'] = user[1]
            session['password'] = user[2]
            session['role'] = user[4]
            session['balance'] = user[3]
            return redirect(url_for('dashboard'))
        else:
            error = 'اسم المستخدم أو كلمة المرور غير صحيحة'
    return render_template_string(LOGIN_PAGE, error=error)

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    check_and_auto_draw_game_board()
    check_and_auto_draw_game_three()
    
    username = session['username']
    conn = sqlite3.connect('empire.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
    res = cursor.fetchone()
    user_balance = res[0] if res else 0
    
    cursor.execute("SELECT number, status, owner FROM game_board")
    board = cursor.fetchall()

    cursor.execute("SELECT number FROM game_board WHERE owner=?", (username,))
    user_locked_numbers = [row[0] for row in cursor.fetchall()]
    user_total_spent = len(user_locked_numbers) * 2.0

    cursor.execute("SELECT is_full, timer_end, last_winner_msg FROM game_board_state WHERE id=1")
    board_state = cursor.fetchone()
    board_is_full = board_state[0]
    board_timer_end = board_state[1]
    board_last_winner_msg = board_state[2]

    cursor.execute("SELECT slot_id, status, owner FROM game_three")
    game_three_slots = cursor.fetchall()

    cursor.execute("SELECT is_full, timer_end, last_winner_msg FROM game_three_state WHERE id=1")
    g3_state = cursor.fetchone()
    g3_is_full = g3_state[0]
    g3_timer_end = g3_state[1]
    g3_last_winner = g3_state[2]
    
    all_users = []
    if session['role'] == 'admin':
        cursor.execute("SELECT username, password, balance, role, created_by FROM users")
        all_users = cursor.fetchall()
        
    conn.close()
    winning_num = session.get('winning_num', None)
    
    hidden_nums, selected_boxes, scratch_status, scratch_msg = get_or_create_scratch_game(username)
    
    current_time = time.time()
    board_remaining_time = max(0, int(board_timer_end - current_time)) if board_is_full else 0
    g3_remaining_time = max(0, int(g3_timer_end - current_time)) if g3_is_full else 0

    is_user_participant_in_board = len(user_locked_numbers) > 0

    return render_template_string(DASHBOARD_PAGE, 
                                  username=username,
                                  password=session.get('password', ''),
                                  role=session['role'], 
                                  balance=user_balance, 
                                  board=board,
                                  user_locked_numbers=user_locked_numbers,
                                  user_total_spent=user_total_spent,
                                  board_is_full=board_is_full,
                                  board_remaining_time=board_remaining_time,
                                  board_last_winner_msg=board_last_winner_msg,
                                  is_user_participant_in_board=is_user_participant_in_board,
                                  game_three_slots=game_three_slots,
                                  g3_is_full=g3_is_full,
                                  g3_remaining_time=g3_remaining_time,
                                  g3_last_winner=g3_last_winner,
                                  all_users=all_users,
                                  winning_num=winning_num,
                                  hidden_nums=hidden_nums,
                                  selected_boxes=selected_boxes,
                                  scratch_status=scratch_status,
                                  scratch_msg=scratch_msg)

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
    board_item = cursor.fetchone()
    status, owner = board_item[0], board_item[1]
    
    if status == 'available':
        cursor.execute("SELECT COUNT(*) FROM game_board WHERE owner=?", (username,))
        user_count = cursor.fetchone()[0]
        
        if user_count >= 36:
            conn.close()
            return redirect(url_for('dashboard'))
            
        if balance >= 2:
            cursor.execute("UPDATE game_board SET status='locked', owner=? WHERE number=?", (username, num))
            cursor.execute("UPDATE users SET balance = balance - 2 WHERE username=?", (username,))
            conn.commit()
            
            cursor.execute("SELECT COUNT(*) FROM game_board WHERE status='available'")
            available_count = cursor.fetchone()[0]
            if available_count == 0:
                timer_end = time.time() + 60
                cursor.execute("UPDATE game_board_state SET is_full=1, timer_end=?, last_winner_msg=? WHERE id=1", 
                               (timer_end, "⚠️ اكتملت لوحة الأرقام الـ 50! يبدأ السحب التلقائي خلال دقيقة..."))
                conn.commit()
                
    elif status == 'locked' and owner == username:
        cursor.execute("UPDATE game_board SET status='available', owner=NULL WHERE number=?", (num,))
        cursor.execute("UPDATE users SET balance = balance + 2 WHERE username=?", (username,))
        cursor.execute("UPDATE game_board_state SET is_full=0, timer_end=0, last_winner_msg=? WHERE id=1", 
                       ("تم إلغاء حجز، في انتظار اكتمال اللوحة...",))
        conn.commit()
        
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/pick_game_three/<int:slot_id>', methods=['POST'])
def pick_game_three(slot_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    slot_cost = 50.0
    
    conn = sqlite3.connect('empire.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
    balance = cursor.fetchone()[0]
    
    cursor.execute("SELECT status, owner FROM game_three WHERE slot_id=?", (slot_id,))
    item = cursor.fetchone()
    status, owner = item[0], item[1]
    
    if status == 'available' and balance >= slot_cost:
        cursor.execute("UPDATE game_three SET status='locked', owner=? WHERE slot_id=?", (username, slot_id))
        cursor.execute("UPDATE users SET balance = balance - ? WHERE username=?", (slot_cost, username))
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) FROM game_three WHERE status='available'")
        available_count = cursor.fetchone()[0]
        if available_count == 0:
            timer_end = time.time() + 60
            cursor.execute("UPDATE game_three_state SET is_full=1, timer_end=?, last_winner_msg=? WHERE id=1", 
                           (timer_end, "⚠️ اكتملت الخانات الخمسة! يتم السحب التلقائي خلال دقيقة..."))
            conn.commit()
            
    elif status == 'locked' and owner == username:
        cursor.execute("UPDATE game_three SET status='available', owner=NULL WHERE slot_id=?", (slot_id,))
        cursor.execute("UPDATE users SET balance = balance + ? WHERE username=?", (slot_cost, username))
        cursor.execute("UPDATE game_three_state SET is_full=0, timer_end=0, last_winner_msg=? WHERE id=1", 
                       ("تم إلغاء حجز، في انتظار اكتمال الخانات...",))
        conn.commit()
        
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/draw_winner', methods=['POST'])
def draw_winner():
    if 'username' not in session or session['role'] != 'admin':
        return "غير مسموح", 403
    
    forced_number = request.form.get('forced_number')
    conn = sqlite3.connect('empire.db')
    cursor = conn.cursor()
    
    winning_number = None
    winner_owner = None
    
    if forced_number and forced_number.isdigit():
        winning_number = int(forced_number)
        cursor.execute("SELECT owner FROM game_board WHERE number=?", (winning_number,))
        res = cursor.fetchone()
        if res and res[0]:
            winner_owner = res[0]
        else:
            winner_owner = "بدون مالك (رقم حر)"
    else:
        cursor.execute("SELECT number, owner FROM game_board WHERE status='locked'")
        locked_numbers = cursor.fetchall()
        if locked_numbers:
            winning_number, winner_owner = random.choice(locked_numbers)

    if winning_number:
        prize = 80.0 
        if winner_owner and winner_owner != "بدون مالك (رقم حر)":
            cursor.execute("UPDATE users SET balance = balance + ? WHERE username=?", (prize, winner_owner))
            msg = f"الكرة الفائزة رقم ({winning_number}) والمحظوظ الفائز هو: {winner_owner} بجائزة 80$!"
        else:
            msg = f"الكرة الفائزة رقم ({winning_number}) ولم تكن محجوزة لأحد."
            
        cursor.execute("UPDATE game_board SET status='available', owner=NULL")
        cursor.execute("UPDATE game_board_state SET is_full=0, timer_end=0, last_winner_msg=? WHERE id=1", (msg,))
        conn.commit()
        session['winning_num'] = winning_number
    else:
        cursor.execute("UPDATE game_board_state SET last_winner_msg=? WHERE id=1", ("يرجى تحديد رقم أو توفر أرقام محجوزة للسحب!",))
        conn.commit()
    
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/draw_game_three', methods=['POST'])
def draw_game_three():
    if 'username' not in session or session['role'] != 'admin':
        return "غير مسموح", 403
    
    forced_slot = request.form.get('forced_slot')
    conn = sqlite3.connect('empire.db')
    cursor = conn.cursor()
    
    winning_slot = None
    winner_owner = None
    
    if forced_slot and forced_slot.isdigit():
        winning_slot = int(forced_slot)
        cursor.execute("SELECT owner FROM game_three WHERE slot_id=?", (winning_slot,))
        res = cursor.fetchone()
        if res and res[0]:
            winner_owner = res[0]
        else:
            winner_owner = "بدون مالك"
    else:
        cursor.execute("SELECT slot_id, owner FROM game_three WHERE status='locked'")
        locked_slots = cursor.fetchall()
        if locked_slots:
            winning_slot, winner_owner = random.choice(locked_slots)

    if winning_slot:
        prize = 200.0
        if winner_owner and winner_owner != "بدون مالك":
            cursor.execute("UPDATE users SET balance = balance + ? WHERE username=?", (prize, winner_owner))
            msg = f"🏆 الفائز باللعبة الفاخرة هو: {winner_owner} في الرقم ({winning_slot}) بجائزة 200$!"
        else:
            msg = f"🏆 فاز الرقم الفاخر ({winning_slot}) ولكنه لم يكن محجوزاً لأحد."
            
        cursor.execute("UPDATE game_three SET status='available', owner=NULL")
        cursor.execute("UPDATE game_three_state SET is_full=0, timer_end=0, last_winner_msg=? WHERE id=1", (msg,))
        conn.commit()
    else:
        cursor.execute("UPDATE game_three_state SET last_winner_msg=? WHERE id=1", ("⚠️ لا توجد أرقام محجوزة حالياً للسحب!",))
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
        
    selected_boxes.append(box_index)
    
    if len(selected_boxes) == 3:
        val1 = hidden_nums[selected_boxes[0]]
        val2 = hidden_nums[selected_boxes[1]]
        val3 = hidden_nums[selected_boxes[2]]
        
        if val1 == val2 == val3:
            prize = 15
            cursor.execute("UPDATE users SET balance = balance + ? WHERE username=?", (prize, username))
            scratch_msg = f"🎉 مبروك ربحت 15$! (حصلت على ثلاثة أرقام {val1})"
        else:
            scratch_msg = f"❌ حظ أوفر في المحاولة القادمة (النتائج: {val1}, {val2}, {val3})"
            
        scratch_status = 'finished'
    else:
        remains = 3 - len(selected_boxes)
        scratch_msg = f"اخترت مربعاً، بقي لك {remains} اختيارات..."
        scratch_status = 'playing'
        
    sel_str = ",".join(map(str, selected_boxes))
    cursor.execute("UPDATE scratch_games SET selected_boxes=?, game_status=?, message=? WHERE username=?",
                   (sel_str, scratch_status, scratch_msg, username))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/reset_scratch', methods=['POST'])
def reset_scratch():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    conn = sqlite3.connect('empire.db')
    cursor = conn.cursor()
    nums = [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5]
    random.shuffle(nums)
    hidden_str = ",".join(map(str, nums))
    cursor.execute("UPDATE scratch_games SET hidden_numbers=?, selected_boxes='', game_status='playing', message=? WHERE username=?",
                   (hidden_str, "بدأت محاولة جديدة، اختر 3 مربعات!", username))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/create_user', methods=['POST'])
def create_user():
    if 'username' not in session or session['role'] != 'admin':
        return "غير مسموح", 403
    
    new_user = request.form['new_user']
    new_pass = request.form['new_pass']
    account_role = request.form['account_role']
    creator = session['username']
    
    if account_role not in ['class_a', 'class_b']:
        account_role = 'class_b'

    conn = sqlite3.connect('empire.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password, balance, role, created_by) VALUES (?, ?, ?, ?, ?)",
                       (new_user, new_pass, 0, account_role, creator))
        conn.commit()
    except:
        pass
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/recharge_user', methods=['POST'])
def recharge_user():
    if 'username' not in session or session['role'] != 'admin':
        return "غير مسموح", 403
    
    target_user = request.form['target_user']
    amount = float(request.form['amount'])
    
    conn = sqlite3.connect('empire.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance + ? WHERE username=?", (amount, target_user))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/withdraw_user', methods=['POST'])
def withdraw_user():
    if 'username' not in session or session['role'] != 'admin':
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
    return redirect(url_for('dashboard'))

DASHBOARD_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>إمبراطورية الأرقام والجوائز الكبرى</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #1e293b; padding: 15px 25px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); flex-wrap: wrap; gap: 10px; border-bottom: 2px solid #fbbf24; }
        .logo-area { display: flex; align-items: center; gap: 15px; }
        .logo-area h1 { margin: 0; color: #fbbf24; font-size: 24px; text-shadow: 0 2px 4px rgba(0,0,0,0.5); }
        .user-creds { background: #334155; padding: 6px 12px; border-radius: 6px; font-size: 14px; color: #cbd5e1; border: 1px dashed #fbbf24; }
        .balance-badge { background: #065f46; color: #34d399; padding: 8px 15px; border-radius: 8px; font-weight: bold; font-size: 18px; border: 1px solid #10b981; }
        .whatsapp-btn { background: #25d366; color: white; padding: 8px 15px; text-decoration: none; border-radius: 8px; font-weight: bold; }
        .refresh-btn { background: #3b82f6; color: white; padding: 8px 15px; text-decoration: none; border-radius: 8px; font-weight: bold; border: none; cursor: pointer; }
        
        .main-container { margin-top: 20px; display: flex; flex-direction: column; gap: 25px; }
        
        .participant-notification { background: linear-gradient(135deg, #b45309, #d97706); border: 2px solid #fde047; padding: 12px 20px; border-radius: 10px; font-weight: bold; color: #fff; text-align: center; margin-bottom: 15px; box-shadow: 0 0 15px rgba(245, 158, 11, 0.4); animation: pulseAlert 1.5s infinite; }
        @keyframes pulseAlert { 0% { opacity: 0.9; } 50% { opacity: 1; transform: scale(1.01); } 100% { opacity: 0.9; } }

        .luxury-game-section { background: linear-gradient(135deg, #1e1b4b, #31103d, #0f172a); border: 3px solid #fbbf24; padding: 25px; border-radius: 16px; box-shadow: 0 0 30px rgba(251, 191, 36, 0.25); text-align: center; }
        .luxury-game-section h2 { color: #fbbf24; margin-top: 0; font-size: 26px; text-shadow: 0 2px 4px rgba(0,0,0,0.6); }
        .luxury-slots-container { display: flex; justify-content: center; gap: 15px; margin: 20px 0; flex-wrap: wrap; }
        .luxury-slot-form { display: flex; }
        .luxury-slot-btn { background: linear-gradient(145deg, #111827, #1f2937); border: 2px solid #fbbf24; width: 110px; height: 110px; border-radius: 14px; color: #fff; font-size: 20px; font-weight: bold; cursor: pointer; display: flex; flex-direction: column; align-items: center; justify-content: center; transition: 0.3s; box-shadow: 0 6px 12px rgba(0,0,0,0.4); }
        .luxury-slot-btn.locked { background: linear-gradient(145deg, #991b1b, #7f1d1d); border-color: #f87171; }
        .luxury-slot-btn:hover { transform: translateY(-5px); box-shadow: 0 10px 20px rgba(251,191,36,0.3); }
        .luxury-owner { font-size: 11px; color: #fde047; margin-top: 6px; max-width: 90px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        
        .timer-box { background: rgba(15, 23, 42, 0.8); border: 1px solid #38bdf8; padding: 12px 20px; border-radius: 10px; display: inline-block; font-size: 16px; font-weight: bold; color: #38bdf8; margin-top: 10px; }
        
        .games-grid { display: grid; grid-template-columns: 2fr 1.2fr; gap: 20px; }
        @media (max-width: 1000px) { .games-grid { grid-template-columns: 1fr; } }
        
        .board-section { background: linear-gradient(135deg, #d4af37, #aa771c); padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(212, 175, 55, 0.3); }
        .board-section h2 { color: #111; text-shadow: 0 1px 2px rgba(255,255,255,0.4); margin-top: 0; }
        
        .player-summary-box { background: #0f172a; border: 2px dashed #111; padding: 12px 15px; border-radius: 8px; margin-bottom: 15px; color: #f8fafc; display: flex; justify-content: space-around; flex-wrap: wrap; gap: 10px; font-size: 14px; font-weight: bold; }
        .summary-item { background: #1e293b; padding: 6px 12px; border-radius: 6px; border: 1px solid #475569; }
        
        .board { display: grid; grid-template-columns: repeat(10, 1fr); gap: 6px; margin-top: 15px; }
        .cell-form { display: flex; }
        .cell { background: #000000; border: 1px solid #ffd700; width: 100%; height: 60px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 15px; font-weight: bold; color: #ffffff; border-radius: 6px; cursor: pointer; transition: 0.2s; padding: 0; box-sizing: border-box; }
        .cell.locked { background: #ef4444; border-color: #b91c1c; color: white; }
        .cell:hover { opacity: 0.85; transform: scale(1.03); }
        .owner-tag { font-size: 9px; display: block; color: #fde047; margin-top: 2px; max-width: 90%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        
        .scratch-section { background: #1e293b; border: 2px solid #8b5cf6; padding: 20px; border-radius: 12px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 0 15px rgba(139, 92, 246, 0.3); }
        .scratch-section h2 { color: #a78bfa; margin-top: 0; font-size: 20px; }
        .scratch-board { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin: 15px 0; }
        .scratch-cell { background: linear-gradient(135deg, #4f46e5, #312e81); border: 2px solid #a78bfa; height: 55px; border-radius: 8px; font-size: 18px; font-weight: bold; color: white; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: 0.2s; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
        .scratch-cell.revealed { background: linear-gradient(135deg, #059669, #065f46); border-color: #34d399; font-size: 22px; color: #fbbf24; }
        .scratch-cell:hover { transform: scale(1.05); }
        .scratch-msg-box { background: #0f172a; border: 1px dashed #a78bfa; padding: 10px; border-radius: 8px; font-weight: bold; text-align: center; color: #facc15; font-size: 14px; margin-bottom: 10px; }
        
        .lottery-section { background: #1e293b; padding: 20px; border-radius: 12px; text-align: center; display: flex; flex-direction: column; justify-content: space-between; }
        .roulette-wheel { position: relative; width: 130px; height: 130px; margin: 10px auto; border-radius: 50%; background: conic-gradient(#3b82f6 0deg 36deg, #ef4444 36deg 72deg, #22c55e 72deg 108deg, #eab308 108deg 144deg, #a855f7 144deg 180deg, #ec4899 180deg 216deg, #14b8a6 216deg 252deg, #f97316 252deg 288deg, #6366f1 288deg 324deg, #84cc16 324deg 360deg); border: 5px solid #fbbf24; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 20px rgba(251, 191, 36, 0.5); }
        .roulette-wheel.spinning { animation: spinWheel 1.5s cubic-bezier(0.15, 0.85, 0.35, 1) forwards; }
        @keyframes spinWheel { 
            0% { transform: rotate(0deg); } 
            100% { transform: rotate(1440deg); } 
        }
        .ball-inner { font-size: 20px; font-weight: bold; color: #1e293b; background: #ffffff; width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 3px solid #fbbf24; box-shadow: inset 0 0 10px rgba(0,0,0,0.3); }
        
        .admin-panel { background: #1e293b; padding: 20px; border-radius: 12px; margin-top: 10px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #475569; padding: 10px; text-align: center; }
        th { background: #334155; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo-area">
            <h1>👑 إمبراطورية الأرقام والجوائز الكبرى</h1>
            <div class="user-creds">
                👤 مستخدمك: <b>{{ username }}</b> | 🔑 الباسورد: <b>{{ password }}</b>
            </div>
            <div class="balance-badge">رصيدك: ${{ balance }}</div>
        </div>
        <div style="display: flex; gap: 10px; align-items: center;">
            <a class="whatsapp-btn" href="https://wa.me/?text=الرجاء%20منكم%20شحن%20رصيد%20حسابي%20بلعبة%20امبراطورية%20الارقام%20باسم%20المستخدم:%20{{ username }}" target="_blank">💬 اشحن عبر واتساب</a>
            <button class="refresh-btn" onclick="location.reload();">🔄 تحديث اللوحة</button>
        </div>
    </div>

    <div class="main-container">
        
        <!-- اللعبة الثالثة -->
        <div class="luxury-game-section">
            <h2>💎 اللعبة الملكية الفاخرة (5 أرقام كبرى)</h2>
            <p style="color: #cbd5e1; font-size: 14px;">قيمة الرقم الواحد: 50$ | الجائزة الكبرى للرقم الرابح: 200$ فورية!</p>
            
            <div class="timer-box" id="timerDisplayG3">
                {% if g3_is_full %}
                    ⏳ تنبيه اللعبة الفاخرة: اكتملت الخانات! السحب التلقائي خلال <span id="countdownG3">{{ g3_remaining_time }}</span> ثانية...
                {% else %}
                    ✨ {{ g3_last_winner }}
                {% endif %}
            </div>

            <div class="luxury-slots-container">
                {% for slot_id, status, owner in game_three_slots %}
                <form action="/pick_game_three/{{ slot_id }}" method="POST" class="luxury-slot-form">
                    <button type="submit" class="luxury-slot-btn {% if status == 'locked' %}locked{% endif %}">
                        <span style="font-size: 22px;">رقم {{ slot_id }}</span>
                        <span style="font-size: 11px; color: #38bdf8; margin-top: 4px;">50$</span>
                        {% if owner %}<span class="luxury-owner">{{ owner }}</span>{% endif %}
                    </button>
                </form>
                {% endfor %}
            </div>
        </div>

        <!-- قسم الألعاب الأولى والثانية -->
        <div class="games-grid">
            <!-- اللعبة الأولى -->
            <div class="board-section">
                <h2>لوحة أرقام الحظ (تكلفة الرقم: 2$ | الجائزة: 80$)</h2>
                
                {% if board_is_full and is_user_participant_in_board %}
                <div class="participant-notification">
                    🔔 تنبيه هام لك يا مشتركنا العزيز: لقد اكتملت اللوحة وبدأ العد التنازلي لإجراء السحب على جائزة 80$ خلال <span id="boardCountdownHeader">{{ board_remaining_time }}</span> ثانية!
                </div>
                {% endif %}

                <div class="timer-box" style="margin-bottom: 12px; width: 100%; box-sizing: border-box; text-align: center;">
                    {% if board_is_full %}
                        ⏳ تم اكتمال اللوحة بالكامل! السحب التلقائي خلال <span id="countdownBoard">{{ board_remaining_time }}</span> ثانية...
                    {% else %}
                        ✨ {{ board_last_winner_msg }}
                    {% endif %}
                </div>
                
                <div class="player-summary-box">
                    <div class="summary-item">🎯 أرقامك الحالية ({{ user_locked_numbers|length }}/36): <span style="color: #fbbf24;">{% if user_locked_numbers %}{{ user_locked_numbers | join(', ') }}{% else %}لا توجد{% endif %}</span></div>
                    <div class="summary-item">💵 إجمالي المدفوع: <span style="color: #ef4444;">${{ user_total_spent }}</span></div>
                    <div class="summary-item">💰 رصيدك المتبقي: <span style="color: #34d399;">${{ balance }}</span></div>
                </div>

                <p style="color: #111; font-size: 13px; font-weight: bold;">الحد الأقصى لكل حساب 36 رقماً فقط. السحب التلقائي مفعل عند اكتمال اللوحة.</p>
                <div class="board">
                    {% for num, status, owner in board %}
                        <form action="/pick_number/{{ num }}" method="POST" class="cell-form">
                            <button type="submit" class="cell {% if status == 'locked' %}locked{% endif %}">
                                <span style="font-size: 15px;">{{ num }}</span>
                                {% if owner %}<span class="owner-tag">{{ owner }}</span>{% endif %}
                            </button>
                        </form>
                    {% endfor %}
                </div>
            </div>

            <!-- اللعبة الثانية -->
            <div class="scratch-section">
                <div>
                    <h2>✨ لعبة الـ 15 مربعاً الفاخرة</h2>
                    <p style="color: #94a3b8; font-size: 12px;">اختر 3 مربعات (التكلفة: 1$ | الجائزة: 15$ عند مطابقة 3 أشكال)</p>
                </div>
                
                <div class="scratch-msg-box">
                    {{ scratch_msg }}
                </div>
                
                <div class="scratch-board">
                    {% for i in range(15) %}
                        <form action="/play_scratch/{{ i }}" method="POST">
                            <button type="submit" class="scratch-cell {% if i in selected_boxes or scratch_status == 'finished' %}revealed{% endif %}" {% if scratch_status == 'finished' and i not in selected_boxes %}disabled{% endif %}>
                                {% if i in selected_boxes or scratch_status == 'finished' %}
                                    {{ hidden_nums[i] }}
                                {% else %}
                                    🎁
                                {% endif %}
                            </button>
                        </form>
                    {% endfor %}
                </div>

                {% if scratch_status == 'finished' %}
                <form action="/reset_scratch" method="POST">
                    <button type="submit" style="width: 100%; padding: 10px; background: #8b5cf6; color: white; font-weight: bold; border: none; border-radius: 8px; cursor: pointer; font-size: 14px;">🔄 محاولة جديدة (1$)</button>
                </form>
                {% else %}
                <div style="font-size: 11px; color: #94a3b8; text-align: center;">كل محاولة مستقلة تماماً وتتجدد الأماكن عشوائياً.</div>
                {% endif %}
            </div>
        </div>

        <div class="lottery-section">
            <div>
                <h2>🔮 روليت الحظ السريع (اللعبة الأولى - 80$)</h2>
                <p style="color: #94a3b8; font-size: 12px;">السحب الآلي أو اليدوي لجائزة 80$</p>
            </div>
            <div class="roulette-wheel" id="rouletteWheel">
                <div class="ball-inner" id="ballDisplay">🎲</div>
            </div>
        </div>
    </div>

    {% if role == 'admin' %}
    <div class="admin-panel" style="border: 2px solid #fbbf24; margin-top: 20px;">
        <h3>👑 لوحة تحكم المؤسس (إنشاء الحسابات وتصنيفها كـ A أو B)</h3>
        
        <div style="background: #334155; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <h4 style="margin-top: 0; color: #38bdf8;">👤 إنشاء حساب جديد (وتحديد الفئة A أو B):</h4>
            <form action="/create_user" method="POST" style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
                <input type="text" name="new_user" placeholder="اسم المستخدم الجديد" required style="padding: 10px; border-radius: 6px; border: 1px solid #475569; background: #1e293b; color: white; flex: 1;">
                <input type="password" name="new_pass" placeholder="كلمة المرور" required style="padding: 10px; border-radius: 6px; border: 1px solid #475569; background: #1e293b; color: white; flex: 1;">
                <select name="account_role" required style="padding: 10px; border-radius: 6px; background: #1e293b; color: white; border: 1px solid #475569;">
                    <option value="class_b">فئة B</option>
                    <option value="class_a">فئة A</option>
                </select>
                <button type="submit" style="padding: 10px 20px; background: #3b82f6; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer;">إنشاء الحساب</button>
            </form>
        </div>

        <form action="/draw_game_three" method="POST" style="background: #111827; padding: 15px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #fbbf24;">
            <h4 style="margin-top: 0; color: #fbbf24;">💎 سحب اللعبة الملكية الثالثة (حدد الرقم الفائز بـ 200$):</h4>
            <div style="display: flex; gap: 10px; flex-wrap: wrap; align-items: center;">
                <select name="forced_slot" style="padding: 10px; border-radius: 6px; background: #1e293b; color: white; border: 1px solid #475569; flex: 1;">
                    <option value="">-- اختر الرقم الفائز للعبة الثالثة (أو عشوائي) --</option>
                    {% for i in range(1, 6) %}
                    <option value="{{ i }}">الرقم الفائز: {{ i }}</option>
                    {% endfor %}
                </select>
                <button type="submit" style="padding: 12px 25px; background: #fbbf24; color: black; font-weight: bold; border: none; border-radius: 8px; cursor: pointer; font-size: 15px;">🎰 سحب اللعبة الفاخرة وإعلان الفائز</button>
            </div>
        </form>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;">
            <div style="background: #334155; padding: 15px; border-radius: 8px;">
                <h4 style="margin-top: 0; color: #22c55e;">⚡ شحن رصيد لمستخدم:</h4>
                <form action="/recharge_user" method="POST" style="display: flex; flex-direction: column; gap: 10px;">
                    <select name="target_user" required style="padding: 10px; border-radius: 6px; background: #1e293b; color: white; border: 1px solid #475569;">
                        <option value="">اختر المستخدم</option>
                        {% for u in all_users %}
                        <option value="{{ u[0] }}">{{ u[0] }} (رصيده: ${{ u[2] }})</option>
                        {% endfor %}
                    </select>
                    <input type="number" name="amount" placeholder="المبلغ ($)" required style="padding: 10px; border-radius: 6px; border: 1px solid #475569; background: #1e293b; color: white;">
                    <button type="submit" style="padding: 10px; background: #22c55e; color: black; font-weight: bold; border: none; border-radius: 6px; cursor: pointer;">إضافة شحن</button>
                </form>
            </div>

            <div style="background: #334155; padding: 15px; border-radius: 8px;">
                <h4 style="margin-top: 0; color: #ef4444;">💸 سحب رصيد من مستخدم لحسابي:</h4>
                <form action="/withdraw_user" method="POST" style="display: flex; flex-direction: column; gap: 10px;">
                    <select name="target_user" required style="padding: 10px; border-radius: 6px; background: #1e293b; color: white; border: 1px solid #475569;">
                        <option value="">اختر المستخدم</option>
                        {% for u in all_users %}
                        {% if u[0] != 'admin' %}
                        <option value="{{ u[0] }}">{{ u[0] }} (رصيده: ${{ u[2] }})</option>
                        {% endif %}
                        {% endfor %}
                    </select>
                    <input type="number" name="amount" placeholder="المبلغ المراد سحبه ($)" required style="padding: 10px; border-radius: 6px; border: 1px solid #475569; background: #1e293b; color: white;">
                    <button type="submit" style="padding: 10px; background: #ef4444; color: white; font-weight: bold; border: none; border-radius: 6px; cursor: pointer;">سحب وتحويل لحسابي</button>
                </form>
            </div>
        </div>

        <form action="/draw_winner" method="POST" id="drawForm" style="background: #334155; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <h4 style="margin-top: 0; color: #fbbf24;">🎯 تحكم السحب للعبة الأولى (اختر الرقم الفائز بـ 80$ يدوياً):</h4>
            <div style="display: flex; gap: 10px; flex-wrap: wrap; align-items: center;">
                <select name="forced_number" style="padding: 10px; border-radius: 6px; background: #1e293b; color: white; border: 1px solid #475569; flex: 1;">
                    <option value="">-- اختر الرقم الفائز يدوياً (أو عشوائي) --</option>
                    {% for i in range(1, 51) %}
                    <option value="{{ i }}">رقم الفوز: {{ i }}</option>
                    {% endfor %}
                </select>
                <button type="submit" onclick="startRoulette(event)" style="padding: 12px 25px; background: #fbbf24; color: black; font-weight: bold; border: none; border-radius: 8px; cursor: pointer; font-size: 15px;">🎡 بدء السحب وإعلان الفائز</button>
            </div>
        </form>
        
        <h4>سجل كافة الحسابات والأرصدة والكلمات السرية:</h4>
        <table>
            <tr>
                <th>اسم المستخدم</th>
                <th>كلمة المرور</th>
                <th>الرصيد الحالي</th>
                <th>الفئة / الدور</th>
            </tr>
            {% for u in all_users %}
            <tr>
                <td><b>{{ u[0] }}</b></td>
                <td>{{ u[1] }}</td>
                <td><span style="color: #34d399; font-weight: bold;">${{ u[2] }}</span></td>
                <td>{{ u[3] }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
    {% endif %}

    <script>
        {% if board_is_full and board_remaining_time > 0 %}
        let boardTimeLeft = {{ board_remaining_time }};
        const countdownBoardEl = document.getElementById('countdownBoard');
        const boardHeaderEl = document.getElementById('boardCountdownHeader');
        const boardTimerInterval = setInterval(() => {
            boardTimeLeft--;
            if(countdownBoardEl) countdownBoardEl.innerText = boardTimeLeft;
            if(boardHeaderEl) boardHeaderEl.innerText = boardTimeLeft;
            if(boardTimeLeft <= 0) {
                clearInterval(boardTimerInterval);
                location.reload();
            }
        }, 1000);
        {% elif board_is_full and board_remaining_time <= 0 %}
        setTimeout(() => { location.reload(); }, 500);
        {% endif %}

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

        function startRoulette(event) {
            event.preventDefault();
            const wheel = document.getElementById('rouletteWheel');
            const ball = document.getElementById('ballDisplay');
            const selectBox = document.querySelector('select[name="forced_number"]');
            
            let targetNum = selectBox.value ? selectBox.value : (Math.floor(Math.random() * 50) + 1);

            wheel.classList.add('spinning');
            
            let interval = setInterval(() => {
                ball.innerText = Math.floor(Math.random() * 50) + 1;
            }, 80);

            setTimeout(() => {
                clearInterval(interval);
                wheel.classList.remove('spinning');
                ball.innerText = targetNum;
                
                setTimeout(() => {
                    document.getElementById('drawForm').submit();
                }, 800);
            }, 1500);
        }
    </script>
</body>
</html>
"""

LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>تسجيل الدخول - إمبراطورية الأرقام والجوائز الكبرى</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-box { background: #1e293b; padding: 40px; border-radius: 12px; box-shadow: 0 8px 16px rgba(0,0,0,0.5); width: 320px; text-align: center; border: 1px solid #334155; }
        input { width: 100%; padding: 12px; margin: 10px 0; border-radius: 6px; border: 1px solid #475569; background: #334155; color: white; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #fbbf24; color: black; font-weight: bold; border: none; border-radius: 6px; cursor: pointer; margin-top: 10px; font-size: 16px; }
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