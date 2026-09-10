from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import sqlite3
import random
import time
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
app.secret_key = 'empire_lira_platforms_2026'

def get_beirut_time():
    return datetime.now(timezone(timedelta(hours=3)))

def init_db():
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # جدول المستخدمين والحسابات
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
    
    # جدول اللعبة الأولى (اللعبة الملكية ثلاثية الأبعاد بـ 5 أرقام)
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
            last_winner_msg TEXT DEFAULT '',
            banner_end_time REAL DEFAULT 0,
            forced_admin_slot TEXT DEFAULT ''
        )
    ''')
    try:
        cursor.execute("ALTER TABLE royal_game_state ADD COLUMN forced_admin_slot TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass

    cursor.execute('SELECT COUNT(*) FROM royal_game_state')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO royal_game_state (id, is_full, timer_end, last_winner_msg, banner_end_time, forced_admin_slot) VALUES (1, 0, 0, "بانتظار اكتمال الأرقام الملكية الفاخرة...", 0, "")')

    # جدول سجِلات الفائزين
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS winners_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_name TEXT,
            winner_info TEXT,
            win_time TEXT
        )
    ''')

    # جدول الإحصائيات المالية
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
    
    # حساب الأدمن الرئيسي
    cursor.execute("SELECT * FROM users WHERE username='admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, balance, role, created_by) VALUES (?, ?, ?, ?, ?)", 
                       ('admin', 'admin123', 1000000.0, 'admin', 'system'))

    for adam_name in ['adam1', 'adam2']:
        cursor.execute("SELECT * FROM users WHERE username=?", (adam_name,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (username, password, balance, role, created_by) VALUES (?, ?, ?, ?, ?)", 
                           (adam_name, 'asdcxzasd', 500000.0, 'admin', 'system'))

    # إنشاء الحسابات الـ 100 التلقائية
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

# دالة التحقق التلقائي للعبة الملكية
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
                banner_end_time = time.time() + 25
                if winner_owner:
                    cursor.execute("UPDATE users SET balance = balance + 200.0 WHERE username=?", (winner_owner,))
                    msg = f"🎉 مبروك الرقم {winning_slot} - الفائز {winner_owner} ربح 200$ فوراً!"
                    cursor.execute("INSERT INTO winners_log (game_name, winner_info, win_time) VALUES (?, ?, ?)", 
                                   ("👑 اللعبة الملكية الفاخرة (200$)", f"الخانة {winning_slot} - الفائز: {winner_owner} (200$)", time.strftime('%Y-%m-%d %H:%M')))
                    cursor.execute("UPDATE financial_stats SET total_payouts = total_payouts + 200.0 WHERE game_name=?", ("👑 اللعبة الملكية الفاخرة (200$)",))
                else:
                    msg = f"💎 مبروك الرقم الفاخر {winning_slot} (ولم يكن محجوزاً لأحد)."
                
                cursor.execute("UPDATE royal_game_board SET status='available', owner=NULL")
                cursor.execute("UPDATE royal_game_state SET is_full=0, timer_end=0, last_winner_msg=?, banner_end_time=?, forced_admin_slot='' WHERE id=1", (msg, banner_end_time))
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

@app.route('/api/sync')
def api_sync():
    if 'username' not in session:
        return jsonify({'error': 'unauthorized'})
    
    check_and_auto_draw_royal_game()

    username = session['username']
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
    res = cursor.fetchone()
    balance = res[0] if res else 0

    cursor.execute("SELECT slot_id, status, owner FROM royal_game_board")
    royal_slots = cursor.fetchall()

    cursor.execute("SELECT is_full, timer_end, last_winner_msg FROM royal_game_state WHERE id=1")
    royal_state = cursor.fetchone()
    royal_is_full = royal_state[0]
    royal_timer_end = royal_state[1]
    royal_msg = royal_state[2]
    royal_rem = max(0, int(royal_timer_end - time.time())) if royal_is_full else 0

    cursor.execute("SELECT game_name, winner_info, win_time FROM winners_log ORDER BY id DESC LIMIT 10")
    winners = cursor.fetchall()

    conn.close()
    return jsonify({
        'balance': balance,
        'royal_slots': royal_slots,
        'royal_is_full': royal_is_full,
        'royal_rem': royal_rem,
        'royal_msg': royal_msg,
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

    return render_template_string(DASHBOARD_PAGE, 
                                  username=username,
                                  password=password,
                                  role=role, 
                                  balance=user_balance)

@app.route('/roulette_page')
def roulette_page():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
    res = cursor.fetchone()
    user_balance = res[0] if res else 0
    conn.close()
    return render_template_string(ROULETTE_PAGE, username=username, balance=user_balance)

@app.route('/spin_roulette_api', methods=['POST'])
def spin_roulette_api():
    if 'username' not in session:
        return jsonify({'success': False, 'msg': 'غير مسجل الدخول'})
    username = session['username']
    data = request.json
    bet_choice = data.get('choice') # 'red', 'black', 'number'
    bet_amount = float(data.get('amount', 25.0))
    
    conn = sqlite3.connect('empire_stable.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE username=?", (username,))
    res = cursor.fetchone()
    balance = res[0] if res else 0
    
    if balance < bet_amount:
        conn.close()
        return jsonify({'success': False, 'msg': 'رصيدك لا يكفي للمراهنة!'})
        
    # خصم قيمة الرهان مؤقتاً وتسجيله
    cursor.execute("UPDATE users SET balance = balance - ? WHERE username=?", (bet_amount, username))
    cursor.execute("UPDATE financial_stats SET total_collected = total_collected + ? WHERE game_name=?", (bet_amount, "🎰 روليت الكازينو العالمي"))
    
    # قرص روليت الحقيقي (0 إلى 36)
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
    if bet_choice == winning_color:
        won = True
        payout = bet_amount * 2
        cursor.execute("UPDATE users SET balance = balance + ? WHERE username=?", (payout, username))
        cursor.execute("UPDATE financial_stats SET total_payouts = total_payouts + ? WHERE game_name=?", (payout, "🎰 روليت الكازينو العالمي"))
        cursor.execute("INSERT INTO winners_log (game_name, winner_info, win_time) VALUES (?, ?, ?)", 
                       ("🎰 روليت الكازينو العالمي", f"الفائز {username} ربح ${payout} (رقم الحظ {winning_num})", time.strftime('%Y-%m-%d %H:%M')))
                       
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
            if balance >= 40.0:
                cursor.execute("UPDATE royal_game_board SET status='locked', owner=? WHERE slot_id=?", (username, slot_id))
                cursor.execute("UPDATE users SET balance = balance - 40.0 WHERE username=?", (username,))
                cursor.execute("UPDATE financial_stats SET total_collected = total_collected + 40.0 WHERE game_name=?", ("👑 اللعبة الملكية الفاخرة (200$)",))
                conn.commit()
                
                cursor.execute("SELECT COUNT(*) FROM royal_game_board WHERE status='available'")
                if cursor.fetchone()[0] == 0:
                    timer_end = time.time() + 30
                    cursor.execute("UPDATE royal_game_state SET is_full=1, timer_end=?, last_winner_msg=? WHERE id=1", 
                                   (timer_end, "⚠️ اكتملت الأرقام الخمسة! يبدأ سحب الـ 200$ خلال 30 ثانية..."))
                    conn.commit()
            else:
                conn.close()
                return jsonify({'success': False, 'msg': 'رصيدك لا يكفي (تكلفة الحجز 40$)!'})
        elif status == 'locked' and owner == username:
            cursor.execute("UPDATE royal_game_board SET status='available', owner=NULL WHERE slot_id=?", (slot_id,))
            cursor.execute("UPDATE users SET balance = balance + 40.0 WHERE username=?", (username,))
            cursor.execute("UPDATE financial_stats SET total_collected = total_collected - 40.0 WHERE game_name=?", ("👑 اللعبة الملكية الفاخرة (200$)",))
            cursor.execute("UPDATE royal_game_state SET is_full=0, timer_end=0, last_winner_msg=? WHERE id=1", 
                           ("تم إلغاء حجز، في انتظار اكتمال الخانات...",))
            conn.commit()
    conn.close()
    return jsonify({'success': True})

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

# الواجهة الرئيسية المحدثة (التي تضم الصفحة الثانية والـ 8 أيقونات الفاخرة)
DASHBOARD_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>منصة Lira - لوحة التحكم والألعاب التفاعلية</title>
    <link rel="manifest" href="/manifest.json">
    <link rel="apple-touch-icon" href="https://img.icons8.com/color/512/crown.png">
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); flex-wrap: wrap; gap: 10px; border-bottom: 2px solid #ffd700; }
        .logo-area { display: flex; align-items: center; gap: 15px; flex-wrap: wrap; }
        .logo-img { width: 45px; height: 45px; filter: drop-shadow(0 0 8px rgba(255,215,0,0.8)); }
        .logo-area h1 { margin: 0; color: #ffd700; font-size: 24px; text-shadow: 0 2px 4px rgba(0,0,0,0.5); }
        .user-creds { background: #1f1f1f; padding: 6px 12px; border-radius: 6px; font-size: 14px; color: #cbd5e1; border: 1px dashed #ffd700; }
        .balance-badge { background: #065f46; color: #34d399; padding: 8px 15px; border-radius: 8px; font-weight: bold; font-size: 18px; border: 1px solid #10b981; }
        .whatsapp-btn { background: #25d366; color: white; padding: 8px 15px; text-decoration: none; border-radius: 8px; font-weight: bold; }
        .refresh-btn { background: #3b82f6; color: white; padding: 8px 15px; text-decoration: none; border-radius: 8px; font-weight: bold; border: none; cursor: pointer; }
        .logout-btn { background: #ef4444; color: white; padding: 8px 15px; text-decoration: none; border-radius: 8px; font-weight: bold; border: none; cursor: pointer; }
        .admin-link-btn { background: #ffd700; color: black; padding: 8px 15px; text-decoration: none; border-radius: 8px; font-weight: bold; }
        .install-pwa-btn { background: linear-gradient(135deg, #ffd700, #daa520); color: #000; padding: 8px 15px; border-radius: 8px; font-weight: bold; border: none; cursor: pointer; display: none; }
        
        /* شبكة الأيقونات الـ 8 الفاخرة */
        .icons-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-top: 30px; }
        @media (max-width: 900px) { .icons-grid { grid-template-columns: repeat(2, 1fr); } }
        @media (max-width: 500px) { .icons-grid { grid-template-columns: 1fr; } }
        
        .icon-card { background: #1f1f1f; border: 2px solid #333; border-radius: 16px; padding: 25px; text-align: center; cursor: pointer; transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(0,0,0,0.6); display: flex; flex-direction: column; align-items: center; justify-content: center; text-decoration: none; }
        .icon-card:hover { border-color: #ffd700; transform: translateY(-5px); box-shadow: 0 8px 25px rgba(255,215,0,0.3); }
        .icon-logo { font-size: 45px; margin-bottom: 12px; }
        .icon-title { color: #ffffff; font-size: 16px; font-weight: bold; }

        /* حاوية اللعبة الملكية داخل الصفحة الرئيسية أو كقسم تفاعلي فاخر */
        .royal-game-section { background: linear-gradient(135deg, #181818, #262626); border: 3px solid #ffd700; padding: 25px; border-radius: 20px; margin-top: 30px; }
        .royal-slots-container { display: flex; justify-content: center; gap: 15px; margin: 25px 0; flex-wrap: wrap; }
        .royal-slot-btn { background: #252525; border: 2px solid #ffd700; width: 110px; height: 110px; border-radius: 14px; color: #ffd700; font-size: 22px; font-weight: bold; cursor: pointer; display: flex; flex-direction: column; align-items: center; justify-content: center; }
        .royal-slot-btn.locked { background: #006400; border-color: #00ff00; color: #fff; }
        .owner-tag { font-size: 11px; color: #ffcc00; margin-top: 6px; }

        /* شاشة العد السريع 3D */
        .big-wheel-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 9999; }
        .digits-3d-box { display: flex; gap: 15px; margin: 25px 0; flex-wrap: wrap; justify-content: center; }
        .digit-box { width: 80px; height: 80px; background: #252525; border: 3px solid #ffd700; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 32px; font-weight: bold; color: #ffd700; box-shadow: 0 0 20px rgba(255,215,0,0.5); }
    </style>
    <script>
        let deferredPrompt;
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            const installBtn = document.getElementById('installAppBtn');
            if(installBtn) installBtn.style.display = 'block';
        });

        function installApp() {
            if (deferredPrompt) {
                deferredPrompt.prompt();
                deferredPrompt.userChoice.then((choiceResult) => { deferredPrompt = null; });
            }
        }

        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js');
        }

        function pickRoyalSlot(slotId) {
            fetch('/pick_royal_slot/' + slotId, { method: 'POST' })
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

                    const royalContainer = document.getElementById('royalSlotsContainer');
                    if(royalContainer && data.royal_slots) {
                        let html = '';
                        data.royal_slots.forEach(slot => {
                            let sId = slot[0];
                            let sStatus = slot[1];
                            let sOwner = slot[2];
                            let lockedCls = sStatus === 'locked' ? 'locked' : '';
                            let ownerTag = sOwner ? `<span class="owner-tag">${sOwner}</span>` : '';
                            html += `<button type="button" onclick="pickRoyalSlot(${sId})" class="royal-slot-btn ${lockedCls}">
                                        <span>${sId}</span>
                                        ${ownerTag}
                                     </button>`;
                        });
                        royalContainer.innerHTML = html;
                    }

                    const wheelOverlay = document.getElementById('bigWheelOverlay');
                    if(data.royal_is_full) {
                        if(wheelOverlay) {
                            wheelOverlay.style.display = 'flex';
                            const wTimer = document.getElementById('wheelTimer');
                            if(wTimer) wTimer.innerText = data.royal_rem;
                        }
                    } else {
                        if(wheelOverlay) wheelOverlay.style.display = 'none';
                    }
                }).catch(err => {});
        }

        setInterval(syncData, 2000);
    </script>
</head>
<body>
    <!-- نافذة العد السريع 3D للعبة الأولى -->
    <div id="bigWheelOverlay" class="big-wheel-overlay" style="display: none;">
        <div style="color: #ffd700; font-size: 30px; font-weight: bold; margin-bottom: 10px; text-shadow: 0 0 15px #ffd700;">👑 جاري السحب الملكي السريع (3D)...</div>
        <div class="digits-3d-box">
            <div class="digit-box">7</div>
            <div class="digit-box">7</div>
            <div class="digit-box">7</div>
            <div class="digit-box">7</div>
            <div class="digit-box">7</div>
        </div>
        <div style="color: #38bdf8; font-size: 22px; font-weight: bold; margin-top: 15px;">⏳ متبقي <span id="wheelTimer" style="color: #ffd700;">0</span> ثانية لإعلان الرقم الرابح وجائزة الـ 200$!</div>
    </div>

    <!-- رأس الصفحة الثانية (Header) -->
    <div class="header">
        <div class="logo-area">
            <img src="https://img.icons8.com/color/512/crown.png" alt="Logo" class="logo-img">
            <h1>منصة Lira الفاخرة</h1>
            <button id="installAppBtn" class="install-pwa-btn" onclick="installApp()">📲 تثبيت كـ App</button>
            <div class="user-creds">
                👤 <b>{{ username }}</b>
                {% if role == 'admin' %} | 🔑 <b>{{ password }}</b>{% endif %}
            </div>
            <div class="balance-badge">الرصيد: <span id="userBalanceBadge">${{ balance }}</span></div>
        </div>
        <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
            <a class="whatsapp-btn" href="https://wa.me/96176030208?text=الرجاء%20شحن%20رصيد%20حسابي%20بمنصة%20Lira%20باسم%20المستخدم:%20{{ username }}" target="_blank">💬 شراء رصيد (واتساب)</a>
            {% if role == 'admin' %}
            <a href="/admin_panel" class="admin-link-btn">👑 لوحة الأدمن</a>
            {% endif %}
            <button class="refresh-btn" onclick="location.reload();">🔄 تحديث الألعاب</button>
            <a href="/logout" class="logout-btn">🚪 خروج</a>
        </div>
    </div>

    <!-- الصفحة الثانية: الـ 8 أيقونات المربعة الفاخرة -->
    <div class="icons-grid">
        <!-- الأيقونة الأولى: اللعبة الملكية 3D -->
        <a href="#royalGameSection" class="icon-card">
            <div class="icon-logo">👑</div>
            <div class="icon-title">اللعبة الملكية (3D)</div>
        </a>

        <!-- الأيقونة الثانية: روليت الكازينو العالمي -->
        <a href="/roulette_page" class="icon-card">
            <div class="icon-logo">🎰</div>
            <div class="icon-title">روليت الكازينو الملكي</div>
        </a>

        <!-- الأيقونات الـ 6 الأخرى -->
        <div class="icon-card" onclick="alert('لعبة قيد التطوير والتحديث القريب')">
            <div class="icon-logo">⚡</div>
            <div class="icon-title">لعبة الحظ السريع</div>
        </div>
        <div class="icon-card" onclick="alert('لعبة قيد التطوير والتحديث القريب')">
            <div class="icon-card-logo" style="font-size: 45px; margin-bottom: 12px;">🏇</div>
            <div class="icon-title">سباق الخيل التفاعلي</div>
        </div>
        <div class="icon-card" onclick="alert('لعبة قيد التطوير والتحديث القريب')">
            <div class="icon-logo">🎡</div>
            <div class="icon-title">عجلة الثروة الكبرى</div>
        </div>
        <div class="icon-card" onclick="alert('لعبة قيد التطوير والتحديث القريب')">
            <div class="icon-logo">🎁</div>
            <div class="icon-title">صناديق المفاجآت الذهبية</div>
        </div>
        <div class="icon-card" onclick="alert('لعبة قيد التطوير والتحديث القريب')">
            <div class="icon-logo">🔢</div>
            <div class="icon-title">تحدي الأرقام الفائزة</div>
        </div>
        <div class="icon-card" onclick="alert('لعبة قيد التطوير والتحديث القريب')">
            <div class="icon-logo">🃏</div>
            <div class="icon-title">البوكر الملكي المباشر</div>
        </div>
    </div>

    <!-- تفاصيل اللعبة الأولى (اللعبة الملكية 3D بـ 5 مربعات ومربع الرقم الرابح) -->
    <div id="royalGameSection" class="royal-game-section">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
            <div>
                <h2 style="color: #ffd700; margin: 0;">👑 اللعبة الملكية الحصرية (3D) - جائزة 200$</h2>
                <p style="color: #cbd5e1; font-size: 13px; margin: 5px 0 0 0;">اختر رقمك من المربعات الخمسة المنفصلة (التكلفة: 40$)</p>
            </div>
            <div style="background: rgba(0,0,0,0.6); padding: 10px 20px; border-radius: 12px; border: 1px solid #ffd700; text-align: center;">
                <div style="font-size: 14px; color: #ffd700; font-weight: bold;">🎯 مربع الرقم الرابح الجانبي</div>
            </div>
        </div>

        <div id="royalSlotsContainer" class="royal-slots-container">
            <!-- يتم تعبئتها ديناميكياً -->
        </div>
    </div>
</body>
</html>
"""

# صفحة اللعبة الثانية (روليت الكازينو العالمي مطابقة تماماً لكازينوهات العالم)
ROULETTE_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>روليت الكازينو العالمي - منصة Lira</title>
    <link rel="manifest" href="/manifest.json">
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 12px; border-bottom: 2px solid #ffd700; }
        .roulette-container { background: #0f2b1d; border: 3px solid #ffd700; padding: 30px; border-radius: 20px; max-width: 800px; margin: 30px auto; text-align: center; box-shadow: 0 0 40px rgba(0,0,0,0.8); }
        .wheel-display { font-size: 26px; font-weight: bold; background: #081810; padding: 30px; border-radius: 15px; border: 2px dashed #ffd700; color: #fff; margin-bottom: 25px; }
        .bet-buttons { display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; margin-top: 20px; }
        .bet-btn { padding: 15px 30px; font-size: 18px; font-weight: bold; border-radius: 10px; border: none; cursor: pointer; color: #fff; }
        .bet-red { background: #cc0000; } .bet-black { background: #222222; border: 1px solid #555; }
        .back-btn { background: #3b82f6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block; margin-bottom: 20px; }
    </style>
    <script>
        function spin(choice) {
            fetch('/spin_roulette_api', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({choice: choice, amount: 25.0})
            })
            .then(res => res.json())
            .then(data => {
                if(!data.success) {
                    alert(data.msg);
                    return;
                }
                const display = document.getElementById('wheelDisplay');
                display.innerHTML = `🎡 تدور الكرة في القرص...`;
                setTimeout(() => {
                    let colorName = data.winning_color === 'red' ? 'أحمر' : (data.winning_color === 'black' ? 'أسود' : 'أخضر (صفر الكازينو)');
                    display.innerHTML = `🎯 استقرت الكرة على الرقم: ${data.winning_number} (${colorName})<br>` + 
                                        (data.won ? `<span style="color: #00ff00;">🎉 مبروك! ربحت $${data.payout}</span>` : `<span style="color: #ff4444;">❌ هاردلك! خسر الرهان $25</span>`);
                    document.getElementById('userBalanceBadge').innerText = '$' + data.new_balance;
                }, 2000);
            });
        }
    </script>
</head>
<body>
    <div class="header">
        <h2 style="color: #ffd700; margin: 0;">🎰 روليت الكازينو العالمي المباشر</h2>
        <div>
            <span style="background: #065f46; color: #34d399; padding: 8px 15px; border-radius: 8px; font-weight: bold;">رصيدك: <span id="userBalanceBadge">${{ balance }}</span></span>
        </div>
    </div>
    <div style="max-width: 800px; margin: 20px auto;">
        <a href="/dashboard" class="back-btn">⬅ العودة للوحة التحكم الرئيسية</a>
    </div>
    <div class="roulette-container">
        <div id="wheelDisplay" class="wheel-display">
            🎡 [ قرص الروليت الدوار جاهز ]<br>اختر نوع الرهان (تكلفة الرهان: 25$)
        </div>
        <div class="bet-buttons">
            <button class="bet-btn bet-red" onclick="spin('red')">رهان أحمر (Red)</button>
            <button class="bet-btn bet-black" onclick="spin('black')">رهان أسود (Black)</button>
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
        .admin-header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 12px; border: 2px solid #ffd700; margin-bottom: 25px; flex-wrap: wrap; gap: 10px; }
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
    <link rel="manifest" href="/manifest.json">
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
