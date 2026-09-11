from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import sqlite3
import random
import time

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
        import json
        boxes_json = json.dumps(initial_nums)
        cursor.execute('INSERT INTO golden_boxes_state (id, total_attempts, boxes_data, game_status) VALUES (1, 0, ?, "playing")', (boxes_json,))

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


# لعبة الصناديق الذهبية مع الخصم الفوري عند بدء المحاولة
@app.route('/game_golden_boxes', methods=['GET', 'POST'])
def game_golden_boxes():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    conn = sqlite3.connect('lira_enterprise.db', check_same_thread=False)
    cursor = conn.cursor()
    
    import json
    msg = None
    result_text = None
    revealed_nums = []

    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'open_three_boxes':
            selected_indices = request.form.getlist('box_indices')
            
            if len(selected_indices) == 3:
                selected_indices = [int(idx) for idx in selected_indices]
                
                # التحقق من الرصيد والخصم الفوري بقيمة 1$ عند بدء المحاولة
                cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
                bal = cursor.fetchone()[0]
                cost = 1.0
                
                if bal >= cost:
                    cursor.execute("SELECT total_attempts, boxes_data FROM golden_boxes_state WHERE id=1")
                    state_row = cursor.fetchone()
                    total_att, boxes_json = state_row[0], state_row[1]
                    boxes = json.loads(boxes_json)
                    
                    # خصم 1$ فورا عند بداية المحاولة
                    cursor.execute("UPDATE users SET balance = balance - ? WHERE username=?", (cost, username))
                    
                    # زيادة محاولات النظام التراكمية
                    total_att += 1
                    
                    revealed_nums = [boxes[idx] for idx in selected_indices]
                    
                    # البرمجة الداخلية: كل 36 محاولة تفوز تلقائياً بتطابق الأرقام
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


# لوحات الأدمن
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

    total_sales = sales_res
    total_payouts = payout_res1 + payout_res2
    net_profits = total_sales - total_payouts
    conn.close()

    return render_template_string(ADMIN_ACCOUNTING_PAGE, vault_balance=vault_balance, logs=logs, total_sales=total_sales, total_payouts=total_payouts, net_profits=net_profits)


# قوالب الـ HTML

LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تسجيل الدخول - Lira ليرة</title>
    <link rel="manifest" href="/manifest.json">
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
        <div class="logo-title">👑 Lira</div>
        <div class="logo-sub">ليرة - المنصة التفاعلية الكبرى</div>
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
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lira ليرة - لوحة التحكم الرئيسية</title>
    <link rel="manifest" href="/manifest.json">
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
            <div class="logo-badge">👑</div>
            <h1>Lira | ليرة</h1>
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
        <a href="/game_golden_number" class="icon-card">
            <div class="icon-logo">🏆</div>
            <div class="icon-title">الرقم الذهبي</div>
        </a>
        <div class="icon-card" onclick="alert('اللعبة الثانية قيد التفعيل')">
            <div class="icon-logo">🎰</div>
            <div class="icon-title">روليت الحظ</div>
        </div>
        <div class="icon-card" onclick="alert('اللعبة الثالثة قيد التفعيل')">
            <div class="icon-logo">⚡</div>
            <div class="icon-title">التحدي السريع</div>
        </div>
        <div class="icon-card" onclick="alert('اللعبة الرابعة قيد التفعيل')">
            <div class="icon-logo">🏇</div>
            <div class="icon-title">سباق الخيل</div>
        </div>
        <div class="icon-card" onclick="alert('اللعبة الخامسة قيد التفعيل')">
            <div class="icon-logo">🎡</div>
            <div class="icon-title">عجلة الثروة</div>
        </div>
        <a href="/game_golden_boxes" class="icon-card">
            <div class="icon-logo">🎁</div>
            <div class="icon-title">الصناديق الذهبية</div>
        </a>
        <div class="icon-card" onclick="alert('اللعبة السابعة قيد التفعيل')">
            <div class="icon-logo">🔢</div>
            <div class="icon-title">تحدي الأرقام</div>
        </div>
        <div class="icon-card" onclick="alert('اللعبة الثامنة قيد التفعيل')">
            <div class="icon-logo">🃏</div>
            <div class="icon-title">البوكر الملكي</div>
        </div>
        <div class="icon-card" onclick="alert('اللعبة التاسعة قيد التفعيل')">
            <div class="icon-logo">💎</div>
            <div class="icon-title">المجوهرات الكبرى</div>
        </div>
    </div>
</body>
</html>
"""

GAME_GOLDEN_BOXES_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لعبة الصناديق الذهبية - Lira</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 12px; border-bottom: 2px solid #ffd700; flex-wrap: wrap; gap: 10px; }
        
        .boxes-container { background: linear-gradient(135deg, #1f1a0f, #0d0d0d); border: 5px solid #ffd700; padding: 30px; border-radius: 20px; margin-top: 25px; box-shadow: 0 0 40px rgba(255,215,0,0.3); text-align: center; }
        .boxes-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 15px; margin-top: 25px; }
        @media(max-width: 768px) { .boxes-grid { grid-template-columns: repeat(3, 1fr); } }

        .box-card { background: linear-gradient(145deg, #b8860b, #daa520); border: 3px solid #fff; border-radius: 14px; height: 105px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 20px; font-weight: bold; color: #000; cursor: pointer; transition: 0.3s; box-shadow: 0 6px 15px rgba(0,0,0,0.6); user-select: none; }
        .box-card:hover { transform: scale(1.05); }
        .box-card.selected { background: linear-gradient(145deg, #22c55e, #15803d) !important; color: #fff !important; border-color: #ffd700 !important; box-shadow: 0 0 20px #22c55e; }

        .revealed-icons-row { display: flex; justify-content: center; gap: 12px; margin-top: 20px; flex-wrap: wrap; }
        .mini-icon { background: #252525; border: 2px solid #ffd700; color: #ffd700; width: 60px; height: 60px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: bold; box-shadow: 0 4px 10px rgba(0,0,0,0.7); }

        .play-btn { background: linear-gradient(135deg, #ffd700, #b8860b); color: #000; font-size: 20px; font-weight: bold; padding: 15px 40px; border: none; border-radius: 12px; cursor: pointer; box-shadow: 0 5px 20px rgba(255,215,0,0.4); margin-top: 25px; }
        .play-btn:hover { transform: scale(1.05); }

        .result-banner { background: #18181b; border: 3px solid #ffd700; padding: 20px; border-radius: 14px; margin-top: 25px; text-align: center; font-size: 22px; font-weight: bold; }
        .back-btn { background: #3b82f6; color: white; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h2 style="color: #ffd700; margin: 0;">🎁 لعبة الصناديق الذهبية (15 صندوقاً)</h2>
        <div style="display: flex; gap: 15px; align-items: center;">
            <div style="color: #34d399; font-weight: bold; font-size: 18px;">الرصيد: ${{ balance }}</div>
            <a href="/dashboard" class="back-btn">⬅️ لوحة التحكم</a>
        </div>
    </div>

    {% if msg %}<div style="background: #065f46; color: #34d399; padding: 12px; border-radius: 8px; margin-top: 15px; text-align: center; font-weight: bold;">{{ msg }}</div>{% endif %}

    <div class="boxes-container">
        <h3 style="color: #ffd700; margin-top: 0;">📦 انقر على 3 صناديق لكشف أرقامها وطابقها (تكلفة المحاولة: 1$ تُخصم فور البدء)</h3>
        <p style="color: #cbd5e1; font-size: 15px;">الصناديق المختارة: <b id="selectionCount" style="color: #38bdf8;">0</b> / 3</p>

        {% if session.get('username') == 'admin1' %}
            <p style="font-size: 14px; color: #38bdf8; background: #000; padding: 8px; border-radius: 6px; display: inline-block;">👑 [لوحة الآدمن] محاولات النظام الكلية التراكمية: <b>{{ total_att }}</b></p>
        {% endif %}

        <form method="POST" id="gameForm">
            <input type="hidden" name="action" value="open_three_boxes">
            <div id="hiddenInputsContainer"></div>

            <div class="boxes-grid">
                {% for i in range(15) %}
                    <div class="box-card" id="box-{{ i }}" onclick="toggleBox({{ i }})">
                        <span id="box-icon-{{ i }}">📦</span>
                        <span id="box-text-{{ i }}" style="font-size: 12px; margin-top: 5px;">صندوق {{ i+1 }}</span>
                        <span id="box-val-{{ i }}" style="display:none; color: #ffd700; font-size: 22px; margin-top: 4px;">{{ boxes[i] }}</span>
                    </div>
                {% endfor %}
            </div>

            <!-- زر بدء المحاولة المباشر بدون عبارة إتمام -->
            <button type="submit" class="play-btn" id="submitBtn" style="display:none;">🎰 بدء المحاولة (بـ 1$)</button>
        </form>

        <h4 style="color: #ffd700; margin-top: 25px;">🔍 الأيقونة الصغيرة لعرض الأرقام الثلاثة المكشوفة:</h4>
        <div class="revealed-icons-row">
            {% if revealed_nums %}
                <div class="mini-icon">{{ revealed_nums[0] }}</div>
                <div class="mini-icon">{{ revealed_nums[1] }}</div>
                <div class="mini-icon">{{ revealed_nums[2] }}</div>
            {% else %}
                <div class="mini-icon">?</div>
                <div class="mini-icon">?</div>
                <div class="mini-icon">?</div>
            {% endif %}
        </div>
    </div>

    {% if result_text %}
    <div class="result-banner" style="{% if 'فزت' in result_text %}background: linear-gradient(135deg, #ffd700, #ff8c00); color: #000; border-color: #fff; box-shadow: 0 0 30px #ffd700;{% else %}color: #fca5a5; border-color: #ef4444;{% endif %}">
        {{ result_text }}
    </div>
    {% endif %}

    {% if session.get('username') == 'admin1' %}
        <div style="text-align: center; margin-top: 20px;">
            <form method="POST">
                <input type="hidden" name="action" value="reset_game">
                <button type="submit" style="background: #ef4444; color: white; padding: 10px 20px; font-weight: bold; border: none; border-radius: 8px; cursor: pointer;">🔄 (أداة الآدمن) إعادة خلط الصناديق وتصفير العداد</button>
            </form>
        </div>
    {% endif %}

    <script>
        let selectedBoxes = [];

        function toggleBox(index) {
            let boxEl = document.getElementById('box-' + index);
            let iconEl = document.getElementById('box-icon-' + index);
            let textEl = document.getElementById('box-text-' + index);
            let valEl = document.getElementById('box-val-' + index);

            let idxInArr = selectedBoxes.indexOf(index);
            if (idxInArr > -1) {
                selectedBoxes.splice(idxInArr, 1);
                boxEl.classList.remove('selected');
                iconEl.innerText = "📦";
                textEl.style.display = "block";
                valEl.style.display = "none";
            } else {
                if (selectedBoxes.length < 3) {
                    selectedBoxes.push(index);
                    boxEl.classList.add('selected');
                    iconEl.innerText = "🔓";
                    textEl.style.display = "none";
                    valEl.style.display = "block";
                } else {
                    alert("يمكنك اختيار 3 صناديق فقط للمحاولة!");
                }
            }

            document.getElementById('selectionCount').innerText = selectedBoxes.length;

            let container = document.getElementById('hiddenInputsContainer');
            container.innerHTML = "";
            selectedBoxes.forEach(boxIdx => {
                let input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'box_indices';
                input.value = boxIdx;
                container.appendChild(input);
            });

            if (selectedBoxes.length === 3) {
                document.getElementById('submitBtn').style.display = "inline-block";
            } else {
                document.getElementById('submitBtn').style.display = "none";
            }
        }
    </script>
</body>
</html>
"""

GAME_GOLDEN_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لعبة الرقم الذهبي - Lira</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 12px; border-bottom: 2px solid #ffd700; flex-wrap: wrap; gap: 10px; }
        .user-stats-box { background: #18181b; border: 2px dashed #b8860b; padding: 15px; border-radius: 14px; margin-top: 20px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px; }
        .board-container { background: linear-gradient(135deg, #110d06, #000000); border: 5px solid #b8860b; padding: 25px; border-radius: 18px; margin-top: 20px; box-shadow: 0 0 35px rgba(184,134,11,0.4); text-align: center; }
        .board-grid { display: grid; grid-template-columns: repeat(10, 1fr); gap: 12px; margin-top: 20px; }
        @media(max-width: 768px) { .board-grid { grid-template-columns: repeat(5, 1fr); } }
        .number-box { background: #3d2314; border: 2px solid #8b5a2b; border-radius: 10px; height: 60px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 20px; font-weight: bold; color: #ffffff; cursor: pointer; transition: 0.3s; text-shadow: 0 2px 4px rgba(0,0,0,0.9); box-shadow: inset 0 2px 5px rgba(255,255,255,0.2), 0 4px 6px rgba(0,0,0,0.5); }
        .number-box:hover { background: #5c351e; transform: scale(1.06); }
        .number-box.booked { background: #7f1d1d !important; border-color: #ef4444 !important; color: #fca5a5 !important; cursor: not-allowed; }
        .number-box.my-booked { background: #1e3a8a !important; border-color: #3b82f6 !important; color: #93c5fd !important; }
        .number-box.winning { background: linear-gradient(135deg, #ffd700, #ff8c00) !important; color: #000 !important; border-color: #fff !important; transform: scale(1.2); box-shadow: 0 0 50px #ffd700; animation: pulse 0.5s infinite alternate; }
        @keyframes pulse { from { transform: scale(1); } to { transform: scale(1.22); } }
        .draw-panel { background: #18181b; border: 3px solid #ffd700; padding: 25px; border-radius: 16px; margin-top: 25px; text-align: center; box-shadow: 0 0 30px rgba(255,215,0,0.2); }
        .big-slot-screen { background: radial-gradient(circle, #3d2c00 0%, #000000 100%); border: 4px solid #ffd700; color: #ffd700; font-size: 70px; font-weight: bold; padding: 15px; width: 240px; margin: 15px auto; border-radius: 20px; box-shadow: 0 0 30px rgba(255,215,0,0.6); letter-spacing: 5px; }
        .win-badge { background: linear-gradient(135deg, #ffd700, #b8860b); color: #000; border: 3px solid #fff; padding: 20px; border-radius: 15px; margin: 20px auto; width: 90%; max-width: 500px; text-align: center; font-size: 24px; font-weight: bold; box-shadow: 0 0 40px rgba(255,215,0,0.8); }
        .back-btn { background: #3b82f6; color: white; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h2 style="color: #ffd700; margin: 0;">🏆 الرقم الذهبي (من 1 إلى 50)</h2>
        <div style="display: flex; gap: 15px; align-items: center;">
            <div style="color: #34d399; font-weight: bold; font-size: 18px;">الرصيد: ${{ balance }}</div>
            <a href="/dashboard" class="back-btn">⬅️ لوحة التحكم</a>
        </div>
    </div>
    {% if msg %}<div style="background: #065f46; color: #34d399; padding: 12px; border-radius: 8px; margin-top: 15px; text-align: center; font-weight: bold;">{{ msg }}</div>{% endif %}
    <div class="user-stats-box">
        <div><b style="color: #ffd700;">👤 حسابك الحالي:</b> <span style="color: #cbd5e1;">{{ username }}</span></div>
        <div><b style="color: #38bdf8;">أرقامك المحجوزة:</b> <span style="color: #fff; font-family: monospace; background: #000; padding: 4px 8px; border-radius: 4px;">{% if my_booked_nums %}{{ my_booked_nums | join(', ') }}{% else %}لا توجد أرقام محجوزة{% endif %}</span></div>
        <div><b style="color: #34d399;">المبلغ المصروف:</b> <span style="color: #34d399; font-weight: bold;">${{ my_total_spent }}</span></div>
    </div>
    <div class="board-container">
        <h3 style="color: #ffd700; margin-top: 0;">🎯 اختر أرقامك الحظ (تكلفة الحجز: 2$ | الجائزة الكبرى: 75$)</h3>
        <div class="board-grid">
            {% for i in range(1, 51) %}
                {% if i in bookings %}
                    {% if bookings[i] == username %}
                        <form method="POST" style="margin: 0;">
                            <input type="hidden" name="number" value="{{ i }}">
                            <button type="submit" name="cancel_number" id="box-{{ i }}" class="number-box my-booked" style="width: 100%; height: 60px;" title="اضغط للتراجع واسترداد 2$">
                                {{ i }}<br><span style="font-size: 9px;">(أنت) ❌</span>
                            </button>
                        </form>
                    {% else %}
                        <div id="box-{{ i }}" class="number-box booked" title="محجوز بواسطة {{ bookings[i] }}">
                            {{ i }}<br><span style="font-size: 9px; color: #fca5a5;">({{ bookings[i] }})</span>
                        </div>
                    {% endif %}
                {% else %}
                    <form method="POST" style="margin: 0;">
                        <input type="hidden" name="number" value="{{ i }}">
                        <button type="submit" name="book_number" id="box-{{ i }}" class="number-box" style="width: 100%; height: 60px;">
                            {{ i }}
                        </button>
                    </form>
                {% endif %}
            {% endfor %}
        </div>
    </div>
    <div class="draw-panel">
        <h3 style="color: #ffd700; margin-top: 0;">🎰 شاشة السحب والقرعة الفورية</h3>
        <p id="statusText" style="color: #cbd5e1; font-size: 16px;">{% if draw_status == 'finished' %}🎉 تم إعلان الفائز بالرقم الذهبي فوراً!{% else %}في انتظار ضغط زر السحب الفوري من المؤسس{% endif %}</p>
        <div class="big-slot-screen" id="slotDisplay">{% if draw_status == 'finished' and winning_number %}{{ winning_number }}{% else %}?{% endif %}</div>
        <div id="winNotificationContainer">
            {% if draw_status == 'finished' and winning_number %}
            <div class="win-badge">مبروك 75$ للفائز بالرقم {{ winning_number }}!</div>
            {% endif %}
        </div>
        {% if username == 'admin1' %}
            <form method="POST" style="margin-top: 20px; border-top: 1px dashed #555; padding-top: 15px;">
                <button type="submit" name="admin_execute_draw" style="background: linear-gradient(135deg, #22c55e, #15803d); color: white; font-weight: bold; padding: 12px 30px; border: none; border-radius: 8px; cursor: pointer; display: block; margin: 12px auto; font-size: 18px;">⚡ اسحب الآن</button>
            </form>
        {% endif %}
    </div>
    <script>
        let lastStatus = "{{ draw_status }}";
        let isRefreshing = false;
        function checkGameRealtime() {
            if (isRefreshing) return;
            fetch('/api/golden_status')
                .then(res => res.json())
                .then(data => {
                    if (data.status !== lastStatus && !isRefreshing) {
                        isRefreshing = true;
                        setTimeout(() => { location.reload(); }, 200);
                        return;
                    }
                    let slotEl = document.getElementById('slotDisplay');
                    let statusText = document.getElementById('statusText');
                    if (data.status === 'finished') {
                        slotEl.innerText = data.winning_number;
                        statusText.innerText = "🎉 تم إعلان الفائز فوراً!";
                        let winBox = document.getElementById('box-' + data.winning_number);
                        if (winBox) winBox.className = "number-box winning";
                    }
                });
        }
        setInterval(checkGameRealtime, 1000);
    </script>
</body>
</html>
"""

ADMIN_CUSTOMERS_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>إدارة الزبائن والخزنة - Lira</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; padding: 20px; }
        .admin-header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 12px; border: 2px solid #ffd700; margin-bottom: 25px; flex-wrap: wrap; gap: 10px; }
        .vault-box { background: linear-gradient(135deg, #065f46, #047857); border: 3px solid #34d399; padding: 25px; border-radius: 16px; text-align: center; margin-bottom: 25px; }
        .panel-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
        @media(max-width: 900px) { .panel-grid { grid-template-columns: 1fr; } }
        .panel-box { background: #1f1f1f; padding: 20px; border-radius: 12px; border: 1px solid #444; }
        input, select { width: 100%; padding: 12px; margin: 8px 0; border-radius: 6px; background: #252525; color: white; border: 1px solid #555; box-sizing: border-box; }
        button { padding: 12px; font-weight: bold; border: none; border-radius: 6px; cursor: pointer; width: 100%; margin-top: 10px; }
        .btn-create { background: #3b82f6; color: white; }
        .btn-sell { background: #22c55e; color: black; }
        .btn-buy { background: #ef4444; color: white; }
        .back-btn { background: #3b82f6; color: white; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; display: block; overflow-x: auto; }
        th, td { border: 1px solid #444; padding: 10px; text-align: center; font-size: 14px; }
        th { background: #252525; color: #ffd700; }
    </style>
</head>
<body>
    <div class="admin-header">
        <h2 style="color: #ffd700; margin: 0;">👑 لوحة تحكم المؤسس (admin1) - إدارة الزبائن والخزنة</h2>
        <a href="/dashboard" class="back-btn">⬅️ العودة للرئيسية</a>
    </div>
    {% if msg %}<div style="background: #065f46; color: #34d399; padding: 12px; border-radius: 8px; margin-bottom: 20px; text-align: center; font-weight: bold;">{{ msg }}</div>{% endif %}
    <div class="vault-box">
        <h3 style="margin: 0; color: #a7f3d0; font-size: 18px;">🏦 خزنة الشركة الأساسية (رصيد المليون دولار - حصري لـ admin1)</h3>
        <div style="font-size: 45px; font-weight: bold; color: #fff; margin: 10px 0;">${{ vault_balance }}</div>
    </div>
    <div class="panel-grid">
        <div class="panel-box">
            <h3 style="color: #3b82f6; margin-top: 0;">👤 خلق حساب جديد</h3>
            <form method="POST">
                <input type="hidden" name="action" value="create_user">
                <label>اسم المستخدم:</label>
                <input type="text" name="new_username" placeholder="أدخل اسم المستخدم" required>
                <label>الرقم السري:</label>
                <input type="password" name="new_password" placeholder="كلمة المرور" required>
                <button type="submit" class="btn-create">إنشاء الحساب</button>
            </form>
        </div>
        <div class="panel-box">
            <h3 style="color: #22c55e; margin-top: 0;">⚡ بيع عملات للزبون</h3>
            <form method="POST">
                <input type="hidden" name="action" value="sell_currency">
                <label>اختر الزبون:</label>
                <select name="target_user" required>
                    <option value="">اختر الحساب</option>
                    {% for u in users_list %}<option value="{{ u[0] }}">{{ u[0] }} (رصيده: ${{ u[2] }})</option>{% endfor %}
                </select>
                <label>المبلغ ($):</label>
                <input type="number" name="amount" placeholder="أدخل المبلغ" min="1" required>
                <button type="submit" class="btn-sell">إتمام البيع من الخزنة</button>
            </form>
        </div>
        <div class="panel-box">
            <h3 style="color: #ef4444; margin-top: 0;">💸 شراء العملات وإعادتها</h3>
            <form method="POST">
                <input type="hidden" name="action" value="buy_back_currency">
                <label>اختر الزبون:</label>
                <select name="target_user" required>
                    <option value="">اختر الحساب</option>
                    {% for u in users_list %}<option value="{{ u[0] }}">{{ u[0] }} (رصيده: ${{ u[2] }})</option>{% endfor %}
                </select>
                <label>المبلغ ($):</label>
                <input type="number" name="amount" placeholder="أدخل المبلغ" min="1" required>
                <button type="submit" class="btn-buy">استرجاع للخزنة</button>
            </form>
        </div>
    </div>
    <div class="panel-box" style="margin-top: 25px;">
        <h3 style="color: #ffd700; margin-top: 0;">📋 سجل كافة الحسابات المسجلة</h3>
        <table>
            <tr><th>اسم المستخدم</th><th>كلمة المرور</th><th>نوع الحساب</th><th>الرصيد الحالي</th><th>المُنشئ</th></tr>
            {% for u in users_list %}
            <tr>
                <td><b>{{ u[0] }}</b></td>
                <td style="color: #38bdf8; font-family: monospace;">{{ u[1] }}</td>
                <td>{{ u[3] }}</td>
                <td style="color: #34d399; font-weight: bold;">${{ u[2] }}</td>
                <td>{{ u[4] }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

ADMIN_GAMES_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة تحكم الألعاب - Lira</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; padding: 20px; }
        .admin-header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 12px; border: 2px solid #ffd700; margin-bottom: 25px; }
        .back-btn { background: #3b82f6; color: white; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold; }
        .games-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-top: 30px; }
        @media(max-width:900px){ .games-grid { grid-template-columns: repeat(2, 1fr); } }
        .game-ctrl-card { background: #1f1f1f; border: 2px solid #ffd700; padding: 25px; border-radius: 14px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        .game-title { color: #ffd700; font-size: 16px; font-weight: bold; margin-bottom: 15px; }
        .ctrl-btn { background: #22c55e; color: white; padding: 10px 20px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; width: 100%; text-decoration: none; display: inline-block; box-sizing: border-box; }
        input[type="number"] { width: 100%; padding: 10px; margin: 10px 0; border-radius: 6px; background: #252525; color: white; border: 1px solid #ffd700; text-align: center; font-size: 16px; box-sizing: border-box; }
    </style>
</head>
<body>
    <div class="admin-header">
        <h2 style="color: #ffd700; margin: 0;">👑 لوحة تحكم الألعاب (إدارة الأيقونات والنتائج)</h2>
        <a href="/dashboard" class="back-btn">⬅️ الرئيسية</a>
    </div>
    {% if msg %}<div style="background: #065f46; color: #34d399; padding: 12px; border-radius: 8px; margin-bottom: 20px; text-align: center; font-weight: bold;">{{ msg }}</div>{% endif %}
    <div class="games-grid">
        <div class="game-ctrl-card" style="border: 3px solid #34d399;">
            <div class="game-title">1. الرقم الذهبي 🏆</div>
            <form method="POST">
                <input type="number" name="forced_winning_number" value="{% if forced_val > 0 %}{{ forced_val }}{% endif %}" placeholder="رقم من 1 إلى 50" min="1" max="50">
                <button type="submit" class="ctrl-btn" style="background: #34d399; color: black; margin-top: 5px;">حفظ الرقم الفائز</button>
            </form>
            <a href="/game_golden_number" class="ctrl-btn" style="background: #3b82f6; margin-top: 10px;">فتح نافذة السحب</a>
        </div>
        <div class="game-ctrl-card" style="border: 3px solid #ffd700;">
            <div class="game-title">6. الصناديق الذهبية 🎁</div>
            <p style="font-size: 12px; color: #cbd5e1;">إدارة وتنظيم لعبة الصناديق ومحاولاتها التراكمية:</p>
            <a href="/game_golden_boxes" class="ctrl-btn" style="background: #ffd700; color: black; margin-top: 10px;">إدارة الصناديق الذهبية</a>
        </div>
    </div>
</body>
</html>
"""

ADMIN_ACCOUNTING_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>برنامج المحاسبة الشامل - Lira</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; padding: 20px; }
        .admin-header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 12px; border: 2px solid #ffd700; margin-bottom: 25px; }
        .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 25px; }
        @media(max-width:900px){ .stats-grid { grid-template-columns: 1fr; } }
        .stat-card { background: #1f1f1f; border: 1px solid #444; padding: 20px; border-radius: 12px; text-align: center; }
        .stat-val { font-size: 28px; font-weight: bold; color: #34d399; margin-top: 8px; }
        .panel-box { background: #1f1f1f; padding: 20px; border-radius: 12px; border: 1px solid #444; }
        .back-btn { background: #3b82f6; color: white; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; display: block; overflow-x: auto; }
        th, td { border: 1px solid #444; padding: 10px; text-align: center; font-size: 14px; }
        th { background: #252525; color: #ffd700; }
    </style>
</head>
<body>
    <div class="admin-header">
        <h2 style="color: #ffd700; margin: 0;">📊 برنامج المحاسبة والشؤون المالية (admin1)</h2>
        <a href="/dashboard" class="back-btn">⬅️ الرئيسية</a>
    </div>
    <div class="stats-grid">
        <div class="stat-card">
            <div style="color: #94a3b8;">إجمالي الواردات (المبيعات)</div>
            <div class="stat-val" style="color: #22c55e;">${{ total_sales }}</div>
        </div>
        <div class="stat-card">
            <div style="color: #94a3b8;">إجمالي الصادرات (الجوائز)</div>
            <div class="stat-val" style="color: #ef4444;">${{ total_payouts }}</div>
        </div>
        <div class="stat-card">
            <div style="color: #94a3b8;">رصيد الخزنة الأساسية</div>
            <div class="stat-val" style="color: #38bdf8;">${{ vault_balance }}</div>
        </div>
        <div class="stat-card" style="border: 2px solid #ffd700; background: linear-gradient(135deg, #252010, #161616);">
            <div style="color: #ffd700; font-weight: bold;">صافي الأرباح (مجمع في خانة واحدة)</div>
            <div class="stat-val" style="color: #ffd700;">${{ net_profits }}</div>
        </div>
    </div>
    <div class="panel-box">
        <h3 style="color: #ffd700; margin-top: 0;">📋 سجل العمليات المالية والواردات والصادرات</h3>
        <table>
            <tr><th>نوع العملية</th><th>المسؤول</th><th>الهدف</th><th>المبلغ ($)</th><th>التوقيت</th></tr>
            {% for log in logs %}
            <tr>
                <td><b>{{ log[0] }}</b></td>
                <td style="color: #ffd700;">{{ log[1] }}</td>
                <td>{{ log[2] }}</td>
                <td style="color: #34d399; font-weight: bold;">${{ log[3] }}</td>
                <td>{{ log[4] }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
