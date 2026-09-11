from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import sqlite3
import random
import time
import json

app = Flask(__name__)
app.secret_key = 'lira_empire_secure_2026_key'

def init_db():
    conn = sqlite3.connect('lira_enterprise.db', check_same_thread=False)
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
            booking_date TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_draw_state (
            id INTEGER PRIMARY KEY,
            winning_number INTEGER DEFAULT 0,
            status TEXT DEFAULT 'idle',
            draw_end_time REAL DEFAULT 0,
            forced_winning_number INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('SELECT COUNT(*) FROM game_draw_state')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO game_draw_state (id, winning_number, status, draw_end_time, forced_winning_number) VALUES (1, 0, "idle", 0, 0)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS golden_boxes_state (
            id INTEGER PRIMARY KEY,
            total_attempts INTEGER DEFAULT 0,
            boxes_data TEXT,
            game_status TEXT DEFAULT 'playing'
        )
    ''')
    cursor.execute('SELECT COUNT(*) FROM golden_boxes_state')
    if cursor.fetchone()[0] == 0:
        initial_nums = [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5]
        random.shuffle(initial_nums)
        boxes_json = json.dumps(initial_nums)
        cursor.execute('INSERT INTO golden_boxes_state (id, total_attempts, boxes_data, game_status) VALUES (1, 0, ?, "playing")', (boxes_json,))

    # جدول سجلات الروليت الجديد
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roulette_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            bet_details TEXT,
            winning_number INTEGER,
            payout REAL,
            log_time TEXT
        )
    ''')

    cursor.execute("SELECT * FROM users WHERE username='admin1'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, balance, role, created_by) VALUES ('admin1', 'admin123', 50000.0, 'admin', 'system')", ())
        cursor.execute("UPDATE system_vault SET vault_balance = vault_balance - 50000.0 WHERE id=1")

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
        conn = sqlite3.connect('lira_enterprise.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session.clear()
            session['username'] = user[1]
            session['balance'] = user[3]
            session['role'] = user[4]
            return redirect(url_for('dashboard'))
        else:
            error = "خطأ في اسم المستخدم أو كلمة المرور!"
    return render_template_string(LOGIN_PAGE, error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('lira_enterprise.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT balance, role FROM users WHERE username=?", (session['username'],))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return redirect(url_for('logout'))
    balance, role = row[0], row[1]
    return render_template_string(DASHBOARD_PAGE, username=session['username'], role=role, balance=balance)

@app.route('/api/golden_status')
def api_golden_status():
    conn = sqlite3.connect('lira_enterprise.db', check_same_thread=False)
    cursor = conn.cursor()
    current_time = time.time()
    cursor.execute("SELECT winning_number, status, draw_end_time FROM game_draw_state WHERE id=1")
    row = cursor.fetchone()
    
    if row:
        winning_number, status, end_time = row[0], row[1], row[2]
        if status == 'finished' and current_time >= end_time:
            cursor.execute("DELETE FROM golden_number_bookings")
            cursor.execute("UPDATE game_draw_state SET winning_number=0, status='idle', draw_end_time=0 WHERE id=1")
            conn.commit()
            status = 'idle'
            winning_number = 0

        remaining = int(end_time - current_time) if status == 'finished' else 0
        if remaining < 0: remaining = 0
    else:
        winning_number, status, remaining = 0, 'idle', 0

    cursor.execute("SELECT number, username FROM golden_number_bookings")
    bookings = {r[0]: r[1] for r in cursor.fetchall()}
    conn.close()

    return jsonify({
        "status": status,
        "winning_number": winning_number,
        "remaining_seconds": remaining,
        "bookings": bookings
    })

@app.route('/game_golden_number', methods=['GET', 'POST'])
def game_golden_number():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username, role = session['username'], session['role']
    conn = sqlite3.connect('lira_enterprise.db', check_same_thread=False)
    cursor = conn.cursor()
    
    msg = None
    if request.method == 'POST':
        if 'book_number' in request.form:
            cursor.execute("SELECT status FROM game_draw_state WHERE id=1")
            if cursor.fetchone()[0] == 'idle':
                number = int(request.form.get('number'))
                cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
                bal = cursor.fetchone()[0]
                cost = 2.0
                if bal >= cost:
                    cursor.execute("SELECT * FROM golden_number_bookings WHERE number=?", (number,))
                    if not cursor.fetchone():
                        cursor.execute("UPDATE users SET balance = balance - ? WHERE username=?", (cost, username))
                        cursor.execute("INSERT INTO golden_number_bookings (username, number, booking_date) VALUES (?, ?, ?)", 
                                       (username, number, time.strftime('%Y-%m-%d')))
                        conn.commit()
                        msg = f"تم حجز الرقم {number} بنجاح مقابل 2$!"
                    else:
                        msg = f"عذراً، الرقم {number} محجوز مسبقاً!"
                else:
                    msg = "رصيدك غير كافٍ (التكلفة 2$)!"
            else:
                msg = "عذراً، جاري السحب حالياً!"

        elif 'cancel_number' in request.form:
            cursor.execute("SELECT status FROM game_draw_state WHERE id=1")
            if cursor.fetchone()[0] == 'idle':
                number = int(request.form.get('number'))
                cursor.execute("SELECT username FROM golden_number_bookings WHERE number=?", (number,))
                b_row = cursor.fetchone()
                if b_row and b_row[0] == username:
                    cursor.execute("DELETE FROM golden_number_bookings WHERE number=?", (number,))
                    cursor.execute("UPDATE users SET balance = balance + 2.0 WHERE username=?", (username,))
                    conn.commit()
                    msg = f"تم التراجع عن حجز الرقم {number} الخاص بك واسترداد 2$!"
                else:
                    msg = "عذراً، لا يمكنك التراجع إلا عن الأرقام التي حجزتها بنفسك فقط!"
            else:
                msg = "لا يمكن التراجع أثناء عملية السحب!"

        elif 'admin_execute_draw' in request.form and username == 'admin1':
            cursor.execute("SELECT number FROM golden_number_bookings")
            booked_list = [r[0] for r in cursor.fetchall()]
            if booked_list:
                cursor.execute("SELECT forced_winning_number FROM game_draw_state WHERE id=1")
                forced_num = cursor.fetchone()[0]

                if forced_num and forced_num in booked_list:
                    winning_num = forced_num
                else:
                    winning_num = random.choice(booked_list)
                
                cursor.execute("SELECT username FROM golden_number_bookings WHERE number=?", (winning_num,))
                winner_user = cursor.fetchone()[0]
                
                cursor.execute("UPDATE users SET balance = balance + 75.0 WHERE username=?", (winner_user,))
                cursor.execute("INSERT INTO financial_logs (action_type, admin_name, target_user, amount, log_time) VALUES ('جائزة الرقم الذهبي', 'admin1', ?, 75.0, ?)", 
                               (winner_user, time.strftime('%Y-%m-%d %H:%M')))
                
                end_time = time.time() + 15.0
                cursor.execute("UPDATE game_draw_state SET winning_number=?, status='finished', draw_end_time=? WHERE id=1", (winning_num, end_time))
                conn.commit()
                msg = f"تم السحب فوراً! الفائز هو {winner_user} بالرقم {winning_num}"
            else:
                msg = "لا توجد أرقام محجوزة لإجراء السحب عليها حالياً!"

    cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
    balance = cursor.fetchone()[0]
    cursor.execute("SELECT number, username FROM golden_number_bookings")
    bookings = {r[0]: r[1] for r in cursor.fetchall()}
    cursor.execute("SELECT winning_number, status, forced_winning_number FROM game_draw_state WHERE id=1")
    draw_row = cursor.fetchone()
    winning_number, draw_status, forced_num = draw_row[0], draw_row[1], draw_row[2]

    cursor.execute("SELECT number FROM golden_number_bookings WHERE username=?", (username,))
    my_booked_nums = [r[0] for r in cursor.fetchall()]
    my_total_spent = len(my_booked_nums) * 2.0

    conn.close()
    return render_template_string(GAME_GOLDEN_PAGE, username=username, role=role, balance=balance, 
                                  bookings=bookings, winning_number=winning_number, draw_status=draw_status, 
                                  forced_num=forced_num, my_booked_nums=my_booked_nums, my_total_spent=my_total_spent, msg=msg)

@app.route('/game_golden_boxes', methods=['GET', 'POST'])
def game_golden_boxes():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    conn = sqlite3.connect('lira_enterprise.db', check_same_thread=False)
    cursor = conn.cursor()
    
    msg = None
    result_text = None
    revealed_nums = []

    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'open_three_boxes':
            selected_indices = request.form.getlist('box_indices')
            
            if len(selected_indices) == 3:
                selected_indices = [int(idx) for idx in selected_indices]
                cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
                bal = cursor.fetchone()[0]
                cost = 1.0
                
                if bal >= cost:
                    cursor.execute("SELECT total_attempts, boxes_data FROM golden_boxes_state WHERE id=1")
                    state_row = cursor.fetchone()
                    total_att, boxes_json = state_row[0], state_row[1]
                    boxes = json.loads(boxes_json)
                    
                    cursor.execute("UPDATE users SET balance = balance - ? WHERE username=?", (cost, username))
                    total_att += 1
                    revealed_nums = [boxes[idx] for idx in selected_indices]
                    
                    if total_att >= 36 or (total_att % 36 == 0):
                        winning_val = random.randint(1, 5)
                        revealed_nums = [winning_val, winning_val, winning_val]
                        total_att = 0
                        is_win = True
                    else:
                        is_win = (revealed_nums[0] == revealed_nums[1] == revealed_nums[2])

                    cursor.execute("UPDATE golden_boxes_state SET total_attempts=? WHERE id=1", (total_att,))
                    
                    if is_win:
                        cursor.execute("UPDATE users SET balance = balance + 20.0 WHERE username=?", (username,))
                        cursor.execute("INSERT INTO financial_logs (action_type, admin_name, target_user, amount, log_time) VALUES ('جائزة الصناديق الذهبية', 'system', ?, 20.0, ?)", 
                                       (username, time.strftime('%Y-%m-%d %H:%M')))
                        conn.commit()
                        result_text = f"مبروك لقد فزت ب 20$ (الأرقام المكشوفة: {revealed_nums[0]} - {revealed_nums[1]} - {revealed_nums[2]})"
                    else:
                        conn.commit()
                        result_text = f"حظ أوفر (الأرقام المكشوفة: {revealed_nums[0]} - {revealed_nums[1]} - {revealed_nums[2]})"
                else:
                    msg = "رصيدك غير كافٍ (تكلفة المحاولة 1$)!"
            else:
                msg = "يرجى اختيار 3 صناديق تماماً!"

        elif action == 'reset_game' and username == 'admin1':
            new_nums = [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5]
            random.shuffle(new_nums)
            cursor.execute("UPDATE golden_boxes_state SET total_attempts=0, boxes_data=? WHERE id=1", (json.dumps(new_nums),))
            conn.commit()
            msg = "تم إعادة خلط الصناديق وتصفير عداد النظام بنجاح!"

    cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
    balance = cursor.fetchone()[0]
    cursor.execute("SELECT total_attempts, boxes_data FROM golden_boxes_state WHERE id=1")
    state_row = cursor.fetchone()
    total_att = state_row[0]
    boxes = json.loads(state_row[1])

    conn.close()
    return render_template_string(GAME_GOLDEN_BOXES_PAGE, username=username, balance=balance, total_att=total_att, boxes=boxes, result_text=result_text, revealed_nums=revealed_nums, msg=msg)

@app.route('/game_roulette', methods=['GET', 'POST'])
def game_roulette():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    conn = sqlite3.connect('lira_enterprise.db', check_same_thread=False)
    cursor = conn.cursor()
    
    msg = None
    last_win_data = None

    if request.method == 'POST':
        try:
            bets_json = request.form.get('bets_data')
            total_bet_amount = float(request.form.get('total_bet_amount', 0))
            
            if total_bet_amount > 0:
                cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
                user_bal = cursor.fetchone()[0]
                
                if user_bal >= total_bet_amount:
                    cursor.execute("UPDATE users SET balance = balance - ? WHERE username=?", (total_bet_amount, username))
                    cursor.execute("UPDATE system_vault SET vault_balance = vault_balance + ? WHERE id=1", (total_bet_amount,))
                    
                    wheel_numbers = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26]
                    winning_number = random.choice(wheel_numbers)
                    
                    reds = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
                    if winning_number == 0: winning_color = 'green'
                    elif winning_number in reds: winning_color = 'red'
                    else: winning_color = 'black'

                    bets = json.loads(bets_json)
                    total_payout = 0
                    
                    for bet in bets:
                        b_type, b_val, b_amount = bet['type'], bet['value'], bet['amount']
                        won = False
                        multiplier = 0
                        
                        if b_type == 'straight' and int(b_val) == winning_number:
                            won = True; multiplier = 35
                        elif b_type == 'color' and str(b_val) == winning_color:
                            won = True; multiplier = 1
                        elif b_type == 'dozen':
                            if b_val == 1 and 1 <= winning_number <= 12: won = True; multiplier = 2
                            elif b_val == 2 and 13 <= winning_number <= 24: won = True; multiplier = 2
                            elif b_val == 3 and 25 <= winning_number <= 36: won = True; multiplier = 2
                        elif b_type == 'even_odd':
                            if winning_number != 0:
                                if b_val == 'even' and winning_number % 2 == 0: won = True; multiplier = 1
                                if b_val == 'odd' and winning_number % 2 != 0: won = True; multiplier = 1

                        if won:
                            total_payout += (b_amount * multiplier) + b_amount

                    if total_payout > 0:
                        cursor.execute("UPDATE users SET balance = balance + ? WHERE username=?", (total_payout, username))
                        cursor.execute("UPDATE system_vault SET vault_balance = vault_balance - ? WHERE id=1", (total_payout,))
                        cursor.execute("INSERT INTO financial_logs (action_type, admin_name, target_user, amount, log_time) VALUES ('جائزة روليت الحظ', 'system', ?, ?, ?)", 
                                       (username, total_payout, time.strftime('%Y-%m-%d %H:%M')))

                    conn.commit()
                    last_win_data = {
                        "winning_number": winning_number,
                        "winning_color": winning_color,
                        "total_bet": total_bet_amount,
                        "total_payout": total_payout
                    }
                    msg = f"تم تدوير العجلة! الرقم الفائز هو: {winning_number} ({winning_color}). إجمالي الأرباح: ${total_payout}"
                else:
                    msg = "رصيدك غير كافٍ لتغطية قيمة الرهانات!"
            else:
                msg = "يرجى وضع رهان واحد على الأقل على الطاولة قبل التدوير!"
        except Exception as e:
            msg = f"حدث خطأ أثناء معالجة الرهان: {str(e)}"

    cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
    balance = cursor.fetchone()[0]
    conn.close()
    
    return render_template_string(GAME_ROULETTE_PAGE, username=username, balance=balance, msg=msg, last_win_data=last_win_data)

@app.route('/admin_customers', methods=['GET', 'POST'])
def admin_customers():
    if 'username' not in session or session.get('username') != 'admin1':
        return redirect(url_for('dashboard'))
    
    conn = sqlite3.connect('lira_enterprise.db', check_same_thread=False)
    cursor = conn.cursor()
    msg = None

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'create_user':
            new_u = request.form.get('new_username', '').strip()
            new_p = request.form.get('new_password', '').strip()
            try:
                cursor.execute("INSERT INTO users (username, password, balance, role, created_by) VALUES (?, ?, 0, 'player', 'admin1')", (new_u, new_p))
                conn.commit()
                msg = f"تم إنشاء الحساب '{new_u}' بنجاح!"
            except sqlite3.IntegrityError:
                msg = "اسم المستخدم موجود مسبقاً!"

        elif action == 'sell_currency':
            target = request.form.get('target_user')
            amount = float(request.form.get('amount', 0))
            cursor.execute("SELECT vault_balance FROM system_vault WHERE id=1")
            vault_bal = cursor.fetchone()[0]
            if vault_bal >= amount and amount > 0:
                cursor.execute("UPDATE system_vault SET vault_balance = vault_balance - ? WHERE id=1", (amount,))
                cursor.execute("UPDATE users SET balance = balance + ? WHERE username=?", (amount, target))
                cursor.execute("INSERT INTO financial_logs (action_type, admin_name, target_user, amount, log_time) VALUES ('بيع عملات للزبون', 'admin1', ?, ?, ?)", 
                               (target, amount, time.strftime('%Y-%m-%d %H:%M')))
                conn.commit()
                msg = f"تم بيع رصيد بقيمة ${amount} للحساب {target} بنجاح!"
            else:
                msg = "رصيد الخزنة غير كافٍ أو المبلغ غير صالح!"

        elif action == 'buy_back_currency':
            target = request.form.get('target_user')
            amount = float(request.form.get('amount', 0))
            cursor.execute("SELECT balance FROM users WHERE username=?", (target,))
            user_bal = cursor.fetchone()
            if user_bal and user_bal[0] >= amount and amount > 0:
                cursor.execute("UPDATE users SET balance = balance - ? WHERE username=?", (amount, target))
                cursor.execute("UPDATE system_vault SET vault_balance = vault_balance + ? WHERE id=1", (amount,))
                cursor.execute("INSERT INTO financial_logs (action_type, admin_name, target_user, amount, log_time) VALUES ('شراء وإعادة للخزنة', 'admin1', ?, ?, ?)", 
                               (target, amount, time.strftime('%Y-%m-%d %H:%M')))
                conn.commit()
                msg = f"تم استرجاع رصيد بقيمة ${amount} من الحساب {target} إلى الخزنة بنجاح!"
            else:
                msg = "رصيد الزبون غير كافٍ أو المبلغ غير صالح!"

    cursor.execute("SELECT vault_balance FROM system_vault WHERE id=1")
    vault_balance = cursor.fetchone()[0]
    cursor.execute("SELECT username, password, balance, role FROM users")
    users_list = cursor.fetchall()
    conn.close()

    return render_template_string(ADMIN_CUSTOMERS_PAGE, vault_balance=vault_balance, users_list=users_list, msg=msg)

@app.route('/admin_games', methods=['GET', 'POST'])
def admin_games():
    if 'username' not in session or session.get('username') != 'admin1':
        return redirect(url_for('dashboard'))
    
    conn = sqlite3.connect('lira_enterprise.db', check_same_thread=False)
    cursor = conn.cursor()
    msg = None

    if request.method == 'POST':
        forced_num = request.form.get('forced_winning_number', '').strip()
        f_val = int(forced_num) if forced_num.isdigit() else 0
        cursor.execute("UPDATE game_draw_state SET forced_winning_number=? WHERE id=1", (f_val,))
        conn.commit()
        msg = f"تم تحديث الرقم المسبق للسحب إلى: {f_val if f_val > 0 else 'عشوائي'}"

    cursor.execute("SELECT forced_winning_number FROM game_draw_state WHERE id=1")
    forced_val = cursor.fetchone()[0]
    conn.close()

    return render_template_string(ADMIN_GAMES_PAGE, forced_val=forced_val, msg=msg)

@app.route('/admin_accounting')
def admin_accounting():
    if 'username' not in session or session.get('username') != 'admin1':
        return redirect(url_for('dashboard'))
    
    conn = sqlite3.connect('lira_enterprise.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT vault_balance FROM system_vault WHERE id=1")
    vault_balance = cursor.fetchone()[0]
    
    cursor.execute("SELECT action_type, admin_name, target_user, amount, log_time FROM financial_logs ORDER BY id DESC")
    logs = cursor.fetchall()
    
    cursor.execute("SELECT SUM(amount) FROM financial_logs WHERE action_type='بيع عملات للزبون'")
    sales_res = cursor.fetchone()[0] or 0.0

    cursor.execute("SELECT SUM(amount) FROM financial_logs WHERE action_type='جائزة الرقم الذهبي'")
    payout_res1 = cursor.fetchone()[0] or 0.0

    cursor.execute("SELECT SUM(amount) FROM financial_logs WHERE action_type='جائزة الصناديق الذهبية'")
    payout_res2 = cursor.fetchone()[0] or 0.0

    cursor.execute("SELECT SUM(amount) FROM financial_logs WHERE action_type='جائزة روليت الحظ'")
    payout_res3 = cursor.fetchone()[0] or 0.0

    total_sales = sales_res
    total_payouts = payout_res1 + payout_res2 + payout_res3
    net_profits = total_sales - total_payouts
    conn.close()

    return render_template_string(ADMIN_ACCOUNTING_PAGE, vault_balance=vault_balance, logs=logs, total_sales=total_sales, total_payouts=total_payouts, net_profits=net_profits)


# --- القوالب وتصاميم الـ HTML ---

LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تسجيل الدخول - Lira ليرة</title><link rel="manifest" href="/manifest.json">
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-box { background: linear-gradient(145deg, #1f1f1f, #121212); padding: 45px; border-radius: 20px; width: 360px; text-align: center; border: 3px solid #ffd700; box-shadow: 0 0 35px rgba(255,215,0,0.3); }
        .logo-title { font-size: 42px; font-weight: bold; color: #ffd700; text-shadow: 0 0 15px rgba(255,215,0,0.6); margin-bottom: 5px; }
        .logo-sub { font-size: 14px; color: #94a3b8; margin-bottom: 25px; }
        input { width: 100%; padding: 14px; margin: 10px 0; border-radius: 8px; border: 1px solid #444; background: #252525; color: white; box-sizing: border-box; font-size: 16px; }
        button { width: 100%; padding: 14px; background: linear-gradient(135deg, #ffd700, #b8860b); color: black; font-weight: bold; border: none; border-radius: 8px; cursor: pointer; margin-top: 15px; font-size: 18px; box-shadow: 0 4px 15px rgba(255,215,0,0.4); }
        .error { color: #ef4444; margin-bottom: 12px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="login-box">
        <div class="logo-title">👑 Lira</div><div class="logo-sub">ليرة - المنصة التفاعلية الكبرى</div>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="اسم المستخدم" required>
            <input type="password" name="password" placeholder="كلمة المرور" required>
            <button type="submit">دخول للبرنامج</button>
        </form>
    </div>
</body>
</html>
"""

DASHBOARD_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lira ليرة - لوحة التحكم الرئيسية</title><link rel="manifest" href="/manifest.json">
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 14px; box-shadow: 0 4px 15px rgba(0,0,0,0.6); flex-wrap: wrap; gap: 12px; border-bottom: 3px solid #ffd700; }
        .logo-area { display: flex; align-items: center; gap: 15px; flex-wrap: wrap; }
        .logo-badge { background: linear-gradient(135deg, #ffd700, #b8860b); color: #000; width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 26px; font-weight: bold; }
        .logo-area h1 { margin: 0; color: #ffd700; font-size: 26px; font-weight: bold; }
        .user-creds { background: #1f1f1f; padding: 8px 14px; border-radius: 8px; font-size: 14px; color: #cbd5e1; border: 1px dashed #ffd700; }
        .balance-badge { background: #065f46; color: #34d399; padding: 8px 15px; border-radius: 8px; font-weight: bold; font-size: 18px; border: 1px solid #10b981; }
        .nav-buttons { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
        .whatsapp-btn { background: #25d366; color: white; padding: 8px 15px; text-decoration: none; border-radius: 8px; font-weight: bold; }
        .logout-btn { background: #ef4444; color: white; padding: 8px 15px; text-decoration: none; border-radius: 8px; font-weight: bold; border: none; }
        .admin-link { background: #ffd700; color: black; padding: 8px 12px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 13px; }
        .icons-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 35px; }
        @media (max-width: 900px) { .icons-grid { grid-template-columns: repeat(2, 1fr); } }
        @media (max-width: 500px) { .icons-grid { grid-template-columns: 1fr; } }
        .icon-card { background: linear-gradient(145deg, #1f1f1f, #121212); border: 2px solid #b8860b; border-radius: 16px; padding: 30px; text-align: center; cursor: pointer; transition: all 0.3s ease; box-shadow: 0 4px 20px rgba(0,0,0,0.6); display: flex; flex-direction: column; align-items: center; justify-content: center; text-decoration: none; aspect-ratio: 1; }
        .icon-card:hover { border-color: #ffd700; transform: translateY(-5px); box-shadow: 0 8px 30px rgba(255,215,0,0.4); }
        .icon-logo { font-size: 60px; margin-bottom: 15px; filter: drop-shadow(0 0 10px rgba(255,215,0,0.6)); }
        .icon-title { color: #ffd700; font-size: 18px; font-weight: bold; text-shadow: 0 2px 4px rgba(0,0,0,0.8); }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo-area">
            <div class="logo-badge">👑</div><h1>Lira | ليرة</h1>
            <div class="user-creds">👤 <b>{{ username }}</b></div>
            <div class="balance-badge">الرصيد: <span>${{ balance }}</span></div>
        </div>
        <div class="nav-buttons">
            <a class="whatsapp-btn" href="https://wa.me/96176030208?text=اريد%20شحن%20رصيد" target="_blank">💬 شحن رصيد (واتساب)</a>
            {% if username == 'admin1' %}
                <a href="/admin_customers" class="admin-link">👥 إدارة الزبائن والخزنة</a>
                <a href="/admin_games" class="admin-link">🎮 لوحة الألعاب</a>
                <a href="/admin_accounting" class="admin-link">📊 برنامج المحاسبة</a>
            {% endif %}
            <a href="/logout" class="logout-btn">🚪 تسجيل خروج</a>
        </div>
    </div>
    <div class="icons-grid">
        <a href="/game_golden_number" class="icon-card"><div class="icon-logo">🏆</div><div class="icon-title">الرقم الذهبي</div></a>
        <a href="/game_roulette" class="icon-card"><div class="icon-logo">🎰</div><div class="icon-title">روليت الحظ</div></a>
        <div class="icon-card" onclick="alert('اللعبة الثالثة قيد التفعيل')"><div class="icon-logo">⚡</div><div class="icon-title">التحدي السريع</div></div>
        <div class="icon-card" onclick="alert('اللعبة الرابعة قيد التفعيل')"><div class="icon-logo">🏇</div><div class="icon-title">سباق الخيل</div></div>
        <div class="icon-card" onclick="alert('اللعبة الخامسة قيد التفعيل')"><div class="icon-logo">🎡</div><div class="icon-title">عجلة الثروة</div></div>
        <a href="/game_golden_boxes" class="icon-card"><div class="icon-logo">🎁</div><div class="icon-title">الصناديق الذهبية</div></a>
        <div class="icon-card" onclick="alert('اللعبة السابعة قيد التفعيل')"><div class="icon-logo">🔢</div><div class="icon-title">تحدي الأرقام</div></div>
        <div class="icon-card" onclick="alert('اللعبة الثامنة قيد التفعيل')"><div class="icon-logo">🃏</div><div class="icon-title">البوكر الملكي</div></div>
        <div class="icon-card" onclick="alert('اللعبة التاسعة قيد التفعيل')"><div class="icon-logo">💎</div><div class="icon-title">المجوهرات الكبرى</div></div>
    </div>
</body>
</html>
"""

GAME_ROULETTE_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>روليت الحظ الاحترافية - Lira</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; margin: 0; padding: 15px; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 12px 20px; border-radius: 12px; border-bottom: 2px solid #ffd700; flex-wrap: wrap; gap: 10px; }
        .game-layout { display: flex; flex-direction: column; gap: 20px; margin-top: 20px; align-items: center; }
        .wheel-screen { background: #18181b; border: 4px solid #ffd700; padding: 20px; border-radius: 18px; text-align: center; width: 100%; max-width: 450px; box-shadow: 0 0 30px rgba(255,215,0,0.3); }
        .roulette-ball-box { font-size: 50px; font-weight: bold; background: radial-gradient(circle, #2d2300 0%, #000 100%); border: 3px solid #ffd700; border-radius: 50%; width: 110px; height: 110px; display: flex; align-items: center; justify-content: center; margin: 10px auto; color: #ffd700; box-shadow: inset 0 0 15px rgba(255,215,0,0.5); }
        .table-container { background: #064e3b; border: 5px solid #b8860b; padding: 15px; border-radius: 16px; overflow-x: auto; width: 100%; max-width: 650px; box-shadow: 0 0 30px rgba(0,0,0,0.8); }
        .grid-board { display: grid; grid-template-columns: repeat(13, 1fr); gap: 4px; text-align: center; }
