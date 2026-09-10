from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import sqlite3
import random
import time
import os
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
app.secret_key = 'empire_safe_accounts_final_secure_2026'

DB_NAME = 'empire_stable.db'

def get_beirut_time():
    return datetime.now(timezone(timedelta(hours=3)))

def get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
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
            
        forced_num, last_draw_date = state['forced_admin_number'], state['last_draw_date']
        
        if last_draw_date == date_str:
            return

        winning_number, winner_owner = None, None
        if forced_num and forced_num.isdigit():
            winning_number = int(forced_num)
            cursor.execute("SELECT owner FROM game_board WHERE number=?", (winning_number,))
            res = cursor.fetchone()
            winner_owner = res['owner'] if (res and res['owner']) else None
        else:
            cursor.execute("SELECT number, owner FROM game_board WHERE status='locked'")
            locked = cursor.fetchall()
            if locked:
                chosen = random.choice(locked)
                winning_number, winner_owner = chosen['number'], chosen['owner']
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
        if state and state['is_full'] == 1:
            timer_end = state['timer_end']
            forced_slot = state['forced_admin_slot']
            if time.time() >= timer_end:
                winning_slot, winner_owner = None, None
                if forced_slot and forced_slot.isdigit():
                    winning_slot = int(forced_slot)
                    cursor.execute("SELECT owner FROM game_three WHERE slot_id=?", (winning_slot,))
                    res = cursor.fetchone()
                    winner_owner = res['owner'] if (res and res['owner']) else None
                else:
                    cursor.execute("SELECT slot_id, owner FROM game_three WHERE status='locked'")
                    locked_slots = cursor.fetchall()
                    if locked_slots:
                        chosen = random.choice(locked_slots)
                        winning_slot, winner_owner = chosen['slot_id'], chosen['owner']
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
            hidden_numbers = list(map(int, row['hidden_numbers'].split(','))) if row['hidden_numbers'] else []
            selected_boxes = list(map(int, row['selected_boxes'].split(','))) if row['selected_boxes'] else []
            return hidden_numbers, selected_boxes, row['game_status'], row['message']

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
        balance = res['balance'] if res else 0

        cursor.execute("SELECT number, status, owner FROM game_board")
        board = cursor.fetchall()

        cursor.execute("SELECT number FROM game_board WHERE owner=?", (username,))
        user_locked = [row['number'] for row in cursor.fetchall()]
        user_spent = len(user_locked) * 2.0

        cursor.execute("SELECT slot_id, status, owner FROM game_three")
        g3_slots = cursor.fetchall()

        cursor.execute("SELECT is_full, timer_end, last_winner_msg FROM game_three_state WHERE id=1")
        g3_state = cursor.fetchone()
        g3_is_full = g3_state['is_full']
        g3_timer_end = g3_state['timer_end']
        g3_msg = g3_state['last_winner_msg']
        g3_rem = max(0, int(g3_timer_end - time.time())) if g3_is_full else 0

        cursor.execute("SELECT last_winner_msg FROM game_board_state WHERE id=1")
        board_msg = cursor.fetchone()['last_winner_msg']

        cursor.execute("SELECT game_name, winner_info, win_time FROM winners_log ORDER BY id DESC LIMIT 10")
        winners = cursor.fetchall()

    return jsonify({
        'balance': balance,
        'board': [dict(row) for row in board],
        'user_locked': user_locked,
        'user_spent': user_spent,
        'g3_slots': [dict(row) for row in g3_slots],
        'g3_is_full': g3_is_full,
        'g3_rem': g
