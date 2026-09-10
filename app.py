from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import sqlite3
import random
import time

app = Flask(__name__)
app.secret_key = 'empire_lira_clean_2026'

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
            cursor.execute("INSERT INTO users (username, password, balance, role, created_by) VALUES (?, ?, 100000.0, 'admin', 'system')", 
                           (adm, 'admin123'))
            cursor.execute("UPDATE system_vault SET vault_balance = vault_balance - 100000.0 WHERE id=1")

    conn.commit()
    conn.close()

init_db()

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

@app.route('/api/game_status')
def api_game_status():
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    
    current_time = time.time()
    cursor.execute("SELECT winning_number, status, draw_end_timestamp FROM game_draws WHERE game_name='golden_number'")
    row = cursor.fetchone()
    
    if row:
        winning_number = row[0]
        status = row[1]
        end_timestamp = row[2]
        
        # انتهاء الـ 15 ثانية للتدوير -> الانتقال للإضاءة (finished)
        if status == 'drawing' and current_time >= end_timestamp:
            cursor.execute("SELECT username FROM golden_number_bookings WHERE number=?", (winning_number,))
            winner = cursor.fetchone()
            if winner:
                winner_name = winner[0]
                cursor.execute("UPDATE users SET balance = balance + 75.0 WHERE username=?", (winner_name,))
            
            new_lighting_end = current_time + 30
            cursor.execute("UPDATE game_draws SET status='finished', draw_end_timestamp=? WHERE game_name='golden_number'", (new_lighting_end,))
            conn.commit()
            status = 'finished'
            end_timestamp = new_lighting_end

        # انتهاء الـ 30 ثانية للإضاءة -> تصفير اللوحة تماماً والعودة لوضع الاستعداد (idle)
        elif status == 'finished' and current_time >= end_timestamp:
            cursor.execute("DELETE FROM golden_number_bookings")
            cursor.execute("UPDATE game_draws SET status='idle', winning_number=0, draw_end_timestamp=0 WHERE game_name='golden_number'")
            conn.commit()
            status = 'idle'
            end_timestamp = 0

        remaining = int(end_timestamp - current_time) if status in ['drawing', 'finished'] else 0
        if remaining < 0: remaining = 0
    else:
        winning_number = 0
        status = 'idle'
        remaining = 0

    cursor.execute("SELECT number, username FROM golden_number_bookings")
    bookings = {r[0]: r[1] for r in cursor.fetchall()}
    conn.close()

    return jsonify({
        "status": status,
        "winning_number": winning_number,
        "remaining_seconds": remaining,
        "bookings": bookings
    })

@app.route('/game_one_page', methods=['GET', 'POST'])
def game_one_page():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    role = session['role']
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    
    msg = None
    if request.method == 'POST':
        if 'book_number' in request.form:
            cursor.execute("SELECT status FROM game_draws WHERE game_name='golden_number'")
            current_status = cursor.fetchone()[0]
            if current_status == 'idle':
                number = int(request.form.get('number'))
                cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
                bal = cursor.fetchone()[0]
                
                cost = 2.0
                if bal >= cost:
                    cursor.execute("SELECT * FROM golden_number_bookings WHERE number=?", (number,))
                    if not cursor.fetchone():
                        cursor.execute("UPDATE users SET balance = balance - ? WHERE username=?", (cost, username))
                        cursor.execute("INSERT INTO golden_number_bookings (username, number, draw_date) VALUES (?, ?, ?)", 
                                       (username, number, time.strftime('%Y-%m-%d')))
                        conn.commit()
                        msg = f"تم حجز الرقم {number} بنجاح مقابل ${cost}!"
                    else:
                        msg = f"عذراً، الرقم {number} محجوز مسبقاً!"
                else:
                    msg = "رصيدك غير كافٍ!"
            else:
                msg = "عذراً، جاري السحب حالياً!"
        
        elif 'admin_draw' in request.form and role == 'admin':
            cursor.execute("SELECT status FROM game_draws WHERE game_name='golden_number'")
            st = cursor.fetchone()[0]
            if st == 'idle':
                forced_num = request.form.get('forced_number')
                winning_num = int(forced_num) if forced_num else random.randint(1, 50)
                
                end_timestamp = time.time() + 15
                cursor.execute("UPDATE game_draws SET winning_number=?, status='drawing', draw_end_timestamp=? WHERE game_name='golden_number'",
                               (winning_num, end_timestamp))
                conn.commit()
                msg = f"تم بدء السحب الحماسي (15 ثانية)..."
            else:
                msg = "عذراً، لا يمكن بدء سحب جديد الآن!"

    cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
    balance = cursor.fetchone()[0]

    cursor.execute("SELECT number, username FROM golden_number_bookings")
    bookings = {row[0]: row[1] for row in cursor.fetchall()}

    cursor.execute("SELECT number FROM golden_number_bookings WHERE username=?", (username,))
    my_bookings = [r[0] for r in cursor.fetchall()]
    my_spent = len(my_bookings) * 2.0

    cursor.execute("SELECT winning_number, status FROM game_draws WHERE game_name='golden_number'")
    draw_info = cursor.fetchone()
    winning_number = draw_info[0] if draw_info else None
    game_status = draw_info[1] if draw_info else 'idle'

    conn.close()
    return render_template_string(GAME_ONE_PAGE, username=username, role=role, balance=balance, 
                                  bookings=bookings, my_bookings=my_bookings, my_spent=my_spent, 
                                  winning_number=winning_number, game_status=game_status, msg=msg)

@app.route('/game_two_page')
def game_two_page():
    if 'username' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE username=?", (session['username'],))
    balance = cursor.fetchone()[0]
    conn.close()
    return render_template_string(GAME_TWO_PAGE, username=session['username'], balance=balance)

@app.route('/admin_panel', methods=['GET', 'POST'])
def admin_panel():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('dashboard'))
    
    current_admin = session['username']
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()

    if request.method == 'POST':
        action = request.form.get('action')
        target_user = request.form.get('target_user', '').strip()
        amount = float(request.form.get('amount', 0))

        cursor.execute("SELECT vault_balance FROM system_vault WHERE id=1")
        vault_bal = cursor.fetchone()[0]

        cursor.execute("SELECT balance, role FROM users WHERE username=?", (target_user,))
        user_row = cursor.fetchone()

        if user_row and amount > 0:
            if action == 'sell' and vault_bal >= amount:
                cursor.execute("UPDATE system_vault SET vault_balance = vault_balance - ? WHERE id=1", (amount,))
                cursor.execute("UPDATE users SET balance = balance + ? WHERE username=?", (amount, target_user))
                cursor.execute("INSERT INTO financial_logs (action_type, admin_name, target_user, amount, log_time) VALUES ('بيع رصيد', ?, ?, ?, ?)", 
                               (current_admin, target_user, amount, time.strftime('%Y-%m-%d %H:%M')))
                conn.commit()
            elif action == 'buy_back' and user_row[0] >= amount:
                cursor.execute("UPDATE users SET balance = balance - ? WHERE username=?", (target_user, amount))
                cursor.execute("UPDATE system_vault SET vault_balance = vault_balance + ? WHERE id=1", (amount,))
                cursor.execute("INSERT INTO financial_logs (action_type, admin_name, target_user, amount, log_time) VALUES ('شراء رصيد', ?, ?, ?, ?)", 
                               (current_admin, target_user, amount, time.strftime('%Y-%m-%d %H:%M')))
                conn.commit()

        return redirect(url_for('admin_panel'))

    cursor.execute("SELECT vault_balance FROM system_vault WHERE id=1")
    vault_balance = cursor.fetchone()[0]
    cursor.execute("SELECT username, password, balance, role, created_by FROM users")
    users_list = cursor.fetchall()
    cursor.execute("SELECT action_type, admin_name, target_user, amount, log_time FROM financial_logs ORDER BY id DESC LIMIT 15")
    logs = cursor.fetchall()
    conn.close()

    return render_template_string(ADMIN_PAGE, username=current_admin, vault_balance=vault_balance, users_list=users_list, logs=logs)

@app.route('/create_user_page', methods=['GET', 'POST'])
def create_user_page():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('dashboard'))
    msg = None
    if request.method == 'POST':
        new_user = request.form.get('new_user', '').strip()
        new_pass = request.form.get('new_pass', '').strip()
        conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password, balance, role, created_by) VALUES (?, ?, 0, 'player', ?)", 
                           (new_user, new_pass, session['username']))
            conn.commit()
            msg = f"تم إنشاء حساب الزبون '{new_user}' بنجاح!"
        except sqlite3.IntegrityError:
            msg = "خطأ: اسم المستخدم موجود مسبقاً!"
        conn.close()
    return render_template_string(CREATE_USER_PAGE, msg=msg)

DASHBOARD_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><title>Lira - لوحة التحكم</title>
<style>
body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; margin: 0; padding: 20px; }
.header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 12px; border-bottom: 2px solid #ffd700; flex-wrap: wrap; gap: 10px; }
.icons-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-top: 40px; }
@media (max-width: 900px) { .icons-grid { grid-template-columns: repeat(2, 1fr); } }
.icon-card { background: #1f1f1f; border: 2px solid #b8860b; border-radius: 16px; padding: 25px; text-align: center; cursor: pointer; text-decoration: none; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.icon-card:hover { border-color: #ffd700; transform: translateY(-3px); }
</style>
</head>
<body>
    <div class="header">
        <div>👑 <b>Lira | ليرة</b> &nbsp;|&nbsp; 👤 <b>{{ username }}</b> {% if role == 'admin' %} | 🔑 <b>مدير</b>{% endif %}</div>
        <div style="background: #065f46; padding: 6px 12px; border-radius: 6px; color: #34d399; font-weight: bold;">الرصيد: ${{ balance }}</div>
        <div>
            <a href="https://wa.me/96176030208?text=شحن%20رصيد%20باسم:%20{{ username }}" target="_blank" style="background:#25d366; color:#fff; padding:6px 12px; text-decoration:none; border-radius:6px; font-weight:bold;">واتساب</a>
            {% if role == 'admin' %}<a href="/admin_panel" style="background:#ffd700; color:#000; padding:6px 12px; text-decoration:none; border-radius:6px; font-weight:bold; margin-right:5px;">لوحة الخزنة</a>{% endif %}
            <a href="/logout" style="background:#ef4444; color:#fff; padding:6px 12px; text-decoration:none; border-radius:6px; font-weight:bold; margin-right:5px;">خروج</a>
        </div>
    </div>
    <div class="icons-grid">
        <a href="/game_one_page" class="icon-card">
            <div style="font-size: 50px;">🏆</div>
            <div style="color: #ffd700; font-weight: bold; margin-top: 10px;">الرقم الذهبي</div>
        </a>
        <a href="/game_two_page" class="icon-card">
            <div style="font-size: 50px;">🎰</div>
            <div style="color: #ffd700; font-weight: bold; margin-top: 10px;">اللعبة الثانية</div>
        </a>
    </div>
</body>
</html>
"""

GAME_ONE_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><title>لعبة الرقم الذهبي</title>
<style>
body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; margin: 0; padding: 20px; }
.header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 12px; border-bottom: 2px solid #ffd700; }
.board-grid { display: grid; grid-template-columns: repeat(10, 1fr); gap: 10px; margin-top: 20px; }
@media(max-width: 768px) { .board-grid { grid-template-columns: repeat(5, 1fr); } }
.number-box { background: #000; border: 3px solid #ffd700; border-radius: 8px; height: 50px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 18px; font-weight: bold; color: #fff; cursor: pointer; }
.number-box.booked { background: #3b0000; border-color: #ef4444; color: #f87171; cursor: not-allowed; }
.number-box.winning { background: linear-gradient(135deg, #ffd700, #ff8c00) !important; color: #000 !important; box-shadow: 0 0 50px #ffd700; transform: scale(1.15); font-weight: bold; animation: pulse 0.6s infinite alternate; }
@keyframes pulse { from { transform: scale(1); } to { transform: scale(1.2); } }
.big-screen { background: #000; border: 4px solid #ffd700; color: #ffd700; font-size: 65px; font-weight: bold; padding: 15px; width: 220px; margin: 15px auto; border-radius: 15px; text-align: center; box-shadow: 0 0 30px rgba(255,215,0,0.5); }
.win-badge { background: linear-gradient(135deg, #ffd700, #b8860b); color: #000; padding: 20px; border-radius: 15px; margin: 20px auto; width: 90%; max-width: 500px; text-align: center; font-weight: bold; font-size: 24px; box-shadow: 0 0 40px rgba(255,215,0,0.8); }
</style>
</head>
<body>
    <div class="header">
        <h2 style="color: #ffd700; margin: 0;">👑 لعبة الرقم الذهبي</h2>
        <div style="color: #34d399; font-weight: bold;">الرصيد: ${{ balance }} &nbsp;|&nbsp; <a href="/dashboard" style="color: #3b82f6; text-decoration: none;">الرئيسية</a></div>
    </div>
    {% if msg %}<div style="background: #065f46; color: #34d399; padding: 10px; border-radius: 6px; margin-top: 15px; text-align: center; font-weight: bold;">{{ msg }}</div>{% endif %}
    <div style="background: #120e06; border: 4px solid #b8860b; padding: 20px; border-radius: 14px; margin-top: 20px; text-align: center;">
        <h3 style="color: #ffd700; margin-top: 0;">اختر أرقامك (السعر: $2 | الجائزة: $75)</h3>
        <div class="board-grid">
            {% for i in range(1, 51) %}
                {% if i in bookings %}
                    <div id="box-{{ i }}" class="number-box booked {% if game_status == 'finished' and winning_number == i %}winning{% endif %}">
                        {{ i }}<br><span style="font-size: 9px; color: #f87171;">({{ bookings[i] }})</span>
                    </div>
                {% else %}
                    <form method="POST" style="margin: 0;">
                        <input type="hidden" name="number" value="{{ i }}">
                        <button type="submit" name="book_number" id="box-{{ i }}" class="number-box" style="width: 100%; height: 50px;">{{ i }}</button>
                    </form>
                {% endif %}
            {% endfor %}
        </div>
    </div>
    <div style="background: #1f1f1f; border: 2px solid #ffd700; padding: 20px; border-radius: 14px; margin-top: 20px; text-align: center;">
        <h3 style="color: #ffd700; margin: 0;">شاشة السحب الكبرى</h3>
        <p id="statusText" style="color: #cbd5e1; font-size: 15px;">{% if game_status == 'drawing' %}⏳ جاري تدوير الأرقام...{% elif game_status == 'finished' %}🎉 تم إعلان الرقم الفائز!{% else %}مفتوح لحجز المراهنات (في انتظار أمر المدير){% endif %}</p>
        <div class="big-screen" id="slotDisplay">{% if game_status == 'finished' and winning_number %}{{ winning_number }}{% else %}?{% endif %}</div>
        <div id="timerText" style="font-size: 22px; color: #ffd700; font-weight: bold; margin: 10px 0;"></div>
        <div id="winContainer">
            {% if game_status == 'finished' and winning_number %}
            <div class="win-badge">مبروك فاز الرقم {{ winning_number }} بمبلغ 75$</div>
            {% endif %}
        </div>
        {% if role == 'admin' %}
            <form method="POST" style="margin-top: 15px; border-top: 1px dashed #444; padding-top: 15px;">
                {% if game_status == 'idle' %}
                    <input type="number" name="forced_number" placeholder="رقم من 1 إلى 50 (اختياري)" min="1" max="50" style="padding: 8px; width: 200px; text-align: center; border-radius: 6px; background: #252525; color: #fff; border: 1px solid #ffd700;">
                    <button type="submit" name="admin_draw" style="background: #22c55e; color: #fff; font-weight: bold; padding: 10px 25px; border: none; border-radius: 6px; cursor: pointer; margin-top: 10px; display: block; margin-left: auto; margin-right: auto;">⚡ بدء السحب الآن (15 ثانية)</button>
                {% else %}
                    <div style="color: #f59e0b; font-weight: bold;">⏳ اللوحة قيد السحب أو عرض الفائز (زر السحب معطل لمنع التكرار)</div>
                {% endif %}
            </form>
        {% endif %}
    </div>
    <script>
        let slotInterval = null;
        let lastStatus = "{{ game_status }}";
        let isRefreshing = false;

        function checkStatus() {
            if (isRefreshing) return;
            fetch('/api/game_status')
                .then(res => res.json())
                .then(data => {
                    if (data.status !== lastStatus && !isRefreshing) {
                        isRefreshing = true;
                        setTimeout(() => { location.reload(); }, 400);
                        return;
                    }
                    let timerEl = document.getElementById('timerText');
                    let slotEl = document.getElementById('slotDisplay');
                    if (data.status === 'drawing') {
                        timerEl.innerText = "⏳ العد التنازلي: " + data.remaining_seconds + " ثانية";
                        if (!slotInterval) {
                            slotInterval = setInterval(() => {
                                slotEl.innerText = Math.floor(Math.random() * 50) + 1;
                            }, 80);
                        }
                    } else if (data.status === 'finished') {
                        if (slotInterval) clearInterval(slotInterval);
                        timerEl.innerText = "⏳ إضاءة الرقم الذهبي (" + data.remaining_seconds + " ثانية)";
                        slotEl.innerText = data.winning_number;
                        let winBox = document.getElementById('box-' + data.winning_number);
                        if (winBox) winBox.className = "number-box winning";
                    } else {
                        if (slotInterval) clearInterval(slotInterval);
                        timerEl.innerText = "";
                    }
                });
        }
        setInterval(checkStatus, 1000);
    </script>
</body>
</html>
"""

ADMIN_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><title>لوحة الإدارة</title>
<style>
body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; padding: 20px; }
.box { background: #1f1f1f; padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #444; }
input, select { width: 100%; padding: 10px; margin: 5px 0 15px 0; background: #252525; color: #fff; border: 1px solid #555; border-radius: 5px; box-sizing: border-box; }
button { width: 100%; padding: 10px; font-weight: bold; border: none; border-radius: 5px; cursor: pointer; }
table { width: 100%; border-collapse: collapse; margin-top: 10px; }
th, td { border: 1px solid #444; padding: 8px; text-align: center; }
th { background: #252525; color: #ffd700; }
</style>
</head>
<body>
    <div style="display:flex; justify-content:space-between; align-items:center; background:#121212; padding:15px; border-radius:10px; border:2px solid #ffd700; margin-bottom:20px;">
        <h2 style="color:#ffd700; margin:0;">👑 لوحة الإدارة العليا ({{ username }})</h2>
        <div>
            <a href="/create_user_page" style="background:#10b981; color:#fff; padding:8px 15px; text-decoration:none; border-radius:5px; font-weight:bold;">➕ إنشاء زبون</a>
            <a href="/dashboard" style="background:#3b82f6; color:#fff; padding:8px 15px; text-decoration:none; border-radius:5px; font-weight:bold; margin-right:10px;">الرئيسية</a>
        </div>
    </div>
    <div style="background:linear-gradient(135deg, #065f46, #047857); padding:20px; border-radius:10px; text-align:center; margin-bottom:20px; border:2px solid #34d399;">
        <h3 style="margin:0; color:#a7f3d0;">🏦 رصيد الخزنة المركزية</h3>
        <div style="font-size:36px; font-weight:bold; color:#fff; margin-top:5px;">${{ vault_balance }}</div>
    </div>
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px;">
        <div class="box">
            <h3 style="color:#22c55e; margin-top:0;">⚡ بيع رصيد للحساب</h3>
            <form method="POST">
                <input type="hidden" name="action" value="sell">
                <label>اختر الحساب:</label>
                <select name="target_user" required><option value="">اختر</option>{% for u in users_list %}<option value="{{ u[0] }}">{{ u[0] }} ({{ u[3] }}) - ${{ u[2] }}</option>{% endfor %}</select>
                <label>المبلغ ($):</label>
                <input type="number" name="amount" min="1" required>
                <button type="submit" style="background:#22c55e; color:#000;">إتمام البيع</button>
            </form>
        </div>
        <div class="box">
            <h3 style="color:#ef4444; margin-top:0;">💸 شراء رصيد للخزنة</h3>
            <form method="POST">
                <input type="hidden" name="action" value="buy_back">
                <label>اختر الحساب:</label>
                <select name="target_user" required><option value="">اختر</option>{% for u in users_list %}<option value="{{ u[0] }}">{{ u[0] }} ({{ u[3] }}) - ${{ u[2] }}</option>{% endfor %}</select>
                <label>المبلغ ($):</label>
                <input type="number" name="amount" min="1" required>
                <button type="submit" style="background:#ef4444; color:#fff;">إتمام الشراء</button>
            </form>
        </div>
    </div>
    <div class="box">
        <h3 style="color:#ffd700; margin-top:0;">👥 جدول كافة الحسابات</h3>
        <table>
            <tr><th>المستخدِم</th><th>الكلمة</th><th>النوع</th><th>الرصيد</th><th>أُنشئ بواسطة</th></tr>
            {% for u in users_list %}
            <tr><td><b>{{ u[0] }}</b></td><td style="color:#38bdf8;">{{ u[1] }}</td><td>{{ u[3] }}</td><td style="color:#34d399;">${{ u[2] }}</td><td>{{ u[4] }}</td></tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

CREATE_USER_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><title>إنشاء زبون</title>
<style>
body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
.box { background: #1f1f1f; padding: 30px; border-radius: 10px; width: 320px; text-align: center; border: 1px solid #444; }
input { width: 100%; padding: 10px; margin: 10px 0; background: #252525; color: #fff; border: 1px solid #555; border-radius: 5px; box-sizing: border-box; }
button { width: 100%; padding: 10px; background: #10b981; color: #fff; font-weight: bold; border: none; border-radius: 5px; cursor: pointer; }
</style>
</head>
<body>
    <div class="box">
        <h2 style="color: #ffd700; margin-top: 0;">➕ إنشاء حساب زبون</h2>
        {% if msg %}<div style="color:#34d399; font-weight:bold; margin-bottom:10px;">{{ msg }}</div>{% endif %}
        <form method="POST">
            <input type="text" name="new_user" placeholder="اسم المستخدم" required>
            <input type="text" name="new_pass" placeholder="كلمة المرور" required>
            <button type="submit">إنشاء الحساب</button>
        </form>
        <a href="/admin_panel" style="display:inline-block; margin-top:15px; color:#3b82f6; text-decoration:none;">⬅ العودة للوحة الإدارة</a>
    </div>
</body>
</html>
"""

GAME_TWO_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><title>اللعبة الثانية</title></head>
<body style="background:#0b0f19; color:#fff; text-align:center; padding:50px;">
    <h1>🎰 اللعبة الثانية قيد البرمجة</h1>
    <a href="/dashboard" style="color:#3b82f6; text-decoration:none;">⬅ العودة للرئيسية</a>
</body>
</html>
"""

LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><title>تسجيل الدخول</title>
<style>
body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
.box { background: #1f1f1f; padding: 35px; border-radius: 10px; width: 300px; text-align: center; border: 1px solid #333; }
input { width: 100%; padding: 10px; margin: 10px 0; background: #252525; color: #fff; border: 1px solid #444; border-radius: 5px; box-sizing: border-box; }
button { width: 100%; padding: 10px; background: #ffd700; color: #000; font-weight: bold; border: none; border-radius: 5px; cursor: pointer; }
</style>
</head>
<body>
    <div class="box">
        <h2 style="color: #ffd700; margin-top: 0;">👑 Lira | ليرة</h2>
        {% if error %}<div style="color:#ef4444; font-weight:bold; margin-bottom:10px;">{{ error }}</div>{% endif %}
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
