from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify, json, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import random
import time
import os

app = Flask(__name__)
app.secret_key = 'empire_of_numbers_secure_2026_key'

# إعداد قاعدة البيانات عبر SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///empire_numbers.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- تعريف نماذج قاعدة البيانات (Models) ---

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    role = db.Column(db.String(20), nullable=False)
    created_by = db.Column(db.String(80), nullable=False)
    owner_name = db.Column(db.String(100), default='غير محدد')

class SystemVault(db.Model):
    __tablename__ = 'system_vault'
    id = db.Column(db.Integer, primary_key=True)
    vault_balance = db.Column(db.Float, default=1000000.0)

class FinancialLog(db.Model):
    __tablename__ = 'financial_logs'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    action_type = db.Column(db.String(100))
    admin_name = db.Column(db.String(80))
    target_user = db.Column(db.String(80))
    amount = db.Column(db.Float)
    log_time = db.Column(db.String(50))

class GoldenNumberBooking(db.Model):
    __tablename__ = 'golden_number_bookings'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80))
    number = db.Column(db.Integer)
    booking_date = db.Column(db.String(50))

class GameDrawState(db.Model):
    __tablename__ = 'game_draw_state'
    id = db.Column(db.Integer, primary_key=True)
    winning_number = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='idle')
    draw_end_time = db.Column(db.Float, default=0)
    forced_winning_number = db.Column(db.Integer, default=0)

class BalloonState(db.Model):
    __tablename__ = 'balloon_state'
    id = db.Column(db.Integer, primary_key=True)
    attempts_since_last_win = db.Column(db.Integer, default=0)
    sequence_index = db.Column(db.Integer, default=0)

class UserLastBet(db.Model):
    __tablename__ = 'user_last_bets'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    bets_json = db.Column(db.Text, nullable=False)

class LuxuryGoldenBooking(db.Model):
    __tablename__ = 'luxury_golden_bookings'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80))
    box_number = db.Column(db.Integer)
    booking_date = db.Column(db.String(50))

class LuxuryGoldenState(db.Model):
    __tablename__ = 'luxury_golden_state'
    id = db.Column(db.Integer, primary_key=True)
    winning_number = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='idle')
    draw_end_time = db.Column(db.Float, default=0)
    forced_winning_number = db.Column(db.Integer, default=0)

class RevealAndWinState(db.Model):
    __tablename__ = 'reveal_and_win_state'
    id = db.Column(db.Integer, primary_key=True)
    global_attempts = db.Column(db.Integer, default=0)
    pool_json = db.Column(db.Text, nullable=False)


# إنشاء الجداول وتثبيت الحسابات الـ 15 الثابتة وتصفير الأرصدة وجعل رصيد الشركة مليون دولار
with app.app_context():
    db.create_all()
    
    vault = SystemVault.query.get(1)
    if vault:
        vault.vault_balance = 1000000.0
    else:
        vault = SystemVault(id=1, vault_balance=1000000.0)
        db.session.add(vault)
    
    if not GameDrawState.query.get(1):
        draw_state = GameDrawState(id=1, winning_number=0, status='idle', draw_end_time=0, forced_winning_number=0)
        db.session.add(draw_state)
        
    if not BalloonState.query.get(1):
        balloon_state = BalloonState(id=1, attempts_since_last_win=0, sequence_index=0)
        db.session.add(balloon_state)

    if not LuxuryGoldenState.query.get(1):
        l_state = LuxuryGoldenState(id=1, winning_number=0, status='idle', draw_end_time=0, forced_winning_number=0)
        db.session.add(l_state)

    if not RevealAndWinState.query.get(1):
        outcomes = ['WIN_3'] * 1 + ['WIN_2'] * 20 + ['LOSE'] * 25
        random.shuffle(outcomes)
        r_state = RevealAndWinState(id=1, global_attempts=0, pool_json=json.dumps(outcomes))
        db.session.add(r_state)
        
    admin = User.query.filter_by(username='admin1').first()
    if not admin:
        admin = User(username='admin1', password='admin123', balance=0.0, role='admin', created_by='system', owner_name='المشرف العام')
        db.session.add(admin)
    else:
        admin.balance = 0.0

    fixed_accounts = [
        ("ahmad_t", "pass123", "أحمد الطفيلي"),
        ("mohammad_9", "pass456", "محمد الحسين"),
        ("ali_z", "pass789", "علي زعيتر"),
        ("hassan_m", "pass321", "حسن المصري"),
        ("ibrahim_k", "pass654", "إبراهيم خليل"),
        ("khaled_s", "pass987", "خالد سلامة"),
        ("bilal_n", "pass111", "بلال ناصر"),
        ("hussein_b", "pass222", "حسين بركات"),
        ("rami_d", "pass333", "رامي ديب"),
        ("samer_h", "pass444", "سامر حيدر"),
        ("ziad_m", "pass555", "زياد منصور"),
        ("fadi_r", "pass666", "فادي رعد"),
        ("omar_t", "pass777", "عمر طفيلي"),
        ("george_k", "pass888", "جورج خوري"),
        ("charbel_s", "pass999", "شربل سابا")
    ]

    for uname, pwd, oname in fixed_accounts:
        acc = User.query.filter_by(username=uname).first()
        if not acc:
            acc = User(username=uname, password=pwd, balance=0.0, role='player', created_by='admin1', owner_name=oname)
            db.session.add(acc)
        else:
            acc.password = pwd
            acc.owner_name = oname

    User.query.update({User.balance: 0.0})
    db.session.commit()


# --- المسارات (Routes) والمنطق البرمجي ---

@app.route('/manifest.json')
def manifest():
    manifest_data = {
        "name": "امبراطورية الأرقام - المنصة التفاعلية الكبرى",
        "short_name": "امبراطورية الأرقام",
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

@app.route('/download')
def download_app():
    try:
        return send_from_directory('static', 'empire.apk', as_attachment=True)
    except Exception:
        return redirect("https://wa.me/96176030208?text=اريد%20تحميل%20تطبيق%20امبراطورية%20الأرقام")

# API التحديث الخلفي الصامت (لإرسال الرصيد المحدث لكل الحسابات برمشة)
@app.route('/api/sync_balance')
def api_sync_balance():
    if 'username' not in session:
        return jsonify({"balance": 0.0})
    user = User.query.filter_by(username=session['username']).first()
    return jsonify({"balance": user.balance if user else 0.0})

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session.clear()
            session['username'] = user.username
            session['balance'] = user.balance
            session['role'] = user.role
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
    user = User.query.filter_by(username=session['username']).first()
    if not user:
        return redirect(url_for('logout'))
    return render_template_string(DASHBOARD_PAGE, username=user.username, role=user.role, balance=user.balance, password=user.password)

@app.route('/api/golden_status')
def api_golden_status():
    current_time = time.time()
    draw_state = GameDrawState.query.get(1)
    status = 'idle'
    winning_number = 0
    remaining = 0
    
    if draw_state:
        status = draw_state.status
        winning_number = draw_state.winning_number
        end_time = draw_state.draw_end_time
        
        if status == 'finished' and current_time >= end_time:
            GoldenNumberBooking.query.delete()
            draw_state.winning_number = 0
            draw_state.status = 'idle'
            draw_state.draw_end_time = 0
            db.session.commit()
            status = 'idle'
            winning_number = 0
        
        remaining = int(end_time - current_time) if status == 'finished' else 0
        if remaining < 0: remaining = 0

    bookings_records = GoldenNumberBooking.query.all()
    bookings = {b.number: b.username for b in bookings_records}

    return jsonify({
        "status": status,
        "winning_number": winning_number,
        "remaining_seconds": remaining,
        "bookings": bookings
    })

@app.route('/api/luxury_golden_status')
def api_luxury_golden_status():
    current_time = time.time()
    l_state = LuxuryGoldenState.query.get(1)
    status = 'idle'
    winning_number = 0
    if l_state:
        status = l_state.status
        winning_number = l_state.winning_number
        if status == 'finished' and current_time >= l_state.draw_end_time:
            LuxuryGoldenBooking.query.delete()
            l_state.winning_number = 0
            l_state.status = 'idle'
            l_state.draw_end_time = 0
            db.session.commit()
            status = 'idle'
            winning_number = 0
    bookings = {b.box_number: b.username for b in LuxuryGoldenBooking.query.all()}
    return jsonify({"status": status, "winning_number": winning_number, "bookings": bookings})

@app.route('/game_golden_number', methods=['GET', 'POST'])
def game_golden_number():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    user = User.query.filter_by(username=username).first()
    vault = SystemVault.query.get(1)
    draw_state = GameDrawState.query.get(1)
    msg = None
    
    if request.method == 'POST':
        if 'book_number' in request.form:
            if draw_state.status == 'idle':
                number = int(request.form.get('number'))
                cost = 2.0
                if user.balance >= cost:
                    existing_booking = GoldenNumberBooking.query.filter_by(number=number).first()
                    if not existing_booking:
                        user.balance -= cost
                        vault.vault_balance += cost
                        log_sale = FinancialLog(action_type='مبيع رهان لعبة', admin_name='system', target_user=username, amount=cost, log_time=time.strftime('%Y-%m-%d %H:%M'))
                        db.session.add(log_sale)

                        new_booking = GoldenNumberBooking(username=username, number=number, booking_date=time.strftime('%Y-%m-%d'))
                        db.session.add(new_booking)
                        db.session.commit()
                        msg = f"تم حجز الرقم {number} بنجاح مقابل 2$!"
                    else:
                        msg = f"عذراً، الرقم {number} محجوز مسبقاً!"
                else:
                    msg = "رصيدك غير كافٍ (التكلفة 2$)!"
            else:
                msg = "عذراً، جاري السحب حالياً!"

        elif 'cancel_number' in request.form:
            if draw_state.status == 'idle':
                number = int(request.form.get('number'))
                booking = GoldenNumberBooking.query.filter_by(number=number).first()
                if booking and booking.username == username:
                    db.session.delete(booking)
                    user.balance += 2.0
                    vault.vault_balance -= 2.0
                    db.session.commit()
                    msg = f"تم التراجع عن حجز الرقم {number} الخاص بك واسترداد 2$!"
                else:
                    msg = "عذراً، لا يمكنك التراجع إلا عن الأرقام التي حجزتها بنفسك فقط!"
            else:
                msg = "لا يمكن التراجع أثناء عملية السحب!"

        elif 'admin_execute_draw' in request.form and username == 'admin1':
            bookings_list = GoldenNumberBooking.query.all()
            booked_nums = [b.number for b in bookings_list]
            if booked_nums:
                forced_num = draw_state.forced_winning_number
                if forced_num and forced_num in booked_nums:
                    winning_num = forced_num
                else:
                    winning_num = random.choice(booked_nums)
                
                winner_booking = GoldenNumberBooking.query.filter_by(number=winning_num).first()
                winner_user = User.query.filter_by(username=winner_booking.username).first()
                
                winner_user.balance += 75.0
                vault.vault_balance -= 75.0
                log = FinancialLog(action_type='جائزة الرقم الحنون', admin_name='admin1', target_user=winner_user.username, amount=75.0, log_time=time.strftime('%Y-%m-%d %H:%M'))
                db.session.add(log)
                
                draw_state.winning_number = winning_num
                draw_state.status = 'finished'
                draw_state.draw_end_time = time.time() + 15.0
                db.session.commit()
                msg = f"تم السحب فوراً! الفائز هو {winner_user.username} بالرقم {winning_num}"
            else:
                msg = "لا توجد أرقام محجوزة لإجراء السحب عليها حالياً!"

    bookings_records = GoldenNumberBooking.query.all()
    bookings = {b.number: b.username for b in bookings_records}
    my_bookings = GoldenNumberBooking.query.filter_by(username=username).all()
    my_booked_nums = [b.number for b in my_bookings]
    my_total_spent = len(my_booked_nums) * 2.0

    return render_template_string(GAME_GOLDEN_PAGE, username=username, role=user.role, balance=user.balance, password=user.password,
                                  bookings=bookings, winning_number=draw_state.winning_number, draw_status=draw_state.status, 
                                  forced_num=draw_state.forced_winning_number, my_booked_nums=my_booked_nums, my_total_spent=my_total_spent, msg=msg)

@app.route('/game_balloon_pop', methods=['GET', 'POST'])
def game_balloon_pop():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    user = User.query.filter_by(username=username).first()
    vault = SystemVault.query.get(1)
    balloon = BalloonState.query.get(1)
    
    msg = None
    win_result = None
    is_popped = False
    is_win = False

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'play_balloon':
            cost = 1.0
            if user.balance >= cost:
                user.balance -= cost
                vault.vault_balance += cost
                
                log_sale = FinancialLog(action_type='مبيع رهان لعبة', admin_name='system', target_user=username, amount=cost, log_time=time.strftime('%Y-%m-%d %H:%M'))
                db.session.add(log_sale)
                
                balloon.attempts_since_last_win += 1
                sequence = [6, 4, 7, 3, 4, 5]
                current_target = sequence[balloon.sequence_index]
                
                if balloon.attempts_since_last_win >= current_target:
                    is_win = True
                    is_popped = False
                    balloon.attempts_since_last_win = 0
                    balloon.sequence_index = (balloon.sequence_index + 1) % len(sequence)
                else:
                    is_win = False
                    is_popped = True

                if is_win:
                    prize = 3.0
                    user.balance += prize
                    vault.vault_balance -= prize
                    log = FinancialLog(action_type='جائزة تحدي البالون', admin_name='system', target_user=username, amount=prize, log_time=time.strftime('%Y-%m-%d %H:%M'))
                    db.session.add(log)
                    db.session.commit()
                    win_result = f"🎉 ممتاز! قمت بنفخ البالون بنجاح دون أن ينفجر وفزت بـ ${prize}!"
                else:
                    db.session.commit()
                    win_result = "💥 بوووم! نفخت البالون بقوة زائدة فانفجر! حظ أوفر في المرة القادمة."
            else:
                msg = "رصيدك غير كافٍ للبدء (تكلفة المحاولة 1$)!"

    return render_template_string(GAME_BALLOON_PAGE, username=username, balance=user.balance, password=user.password, msg=msg, win_result=win_result, is_popped=is_popped, is_win=is_win)

@app.route('/game_roulette', methods=['GET', 'POST'])
def game_roulette():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    user = User.query.filter_by(username=username).first()
    vault = SystemVault.query.get(1)
    
    msg = None
    last_win_data = None

    if request.method == 'POST':
        try:
            bets_json = request.form.get('bets_data')
            total_bet_amount = float(request.form.get('total_bet_amount', 0))
            
            if total_bet_amount > 0:
                if user.balance >= total_bet_amount:
                    user.balance -= total_bet_amount
                    vault.vault_balance += total_bet_amount
                    
                    log_sale = FinancialLog(action_type='مبيع رهان لعبة', admin_name='system', target_user=username, amount=total_bet_amount, log_time=time.strftime('%Y-%m-%d %H:%M'))
                    db.session.add(log_sale)
                    
                    last_bet_entry = UserLastBet.query.filter_by(username=username).first()
                    if not last_bet_entry:
                        last_bet_entry = UserLastBet(username=username, bets_json=bets_json)
                        db.session.add(last_bet_entry)
                    else:
                        last_bet_entry.bets_json = bets_json
                    
                    wheel_numbers = [0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26]
                    reds = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
                    bets = json.loads(bets_json)
                    
                    target_total_payout = total_bet_amount * 0.80
                    scored_outcomes = []
                    for num in wheel_numbers:
                        if num == 0: color = 'green'
                        elif num in reds: color = 'red'
                        else: color = 'black'
                        
                        payout_for_num = 0
                        for bet in bets:
                            b_type, b_val, b_amount = bet['type'], bet['value'], bet['amount']
                            won = False
                            multiplier = 0
                            if b_type == 'straight' and int(b_val) == num:
                                won = True; multiplier = 35
                            elif b_type == 'color' and str(b_val) == color:
                                won = True; multiplier = 1
                            elif b_type == 'dozen':
                                if b_val == 1 and 1 <= num <= 12: won = True; multiplier = 2
                                elif b_val == 2 and 13 <= num <= 24: won = True; multiplier = 2
                                elif b_val == 3 and 25 <= num <= 36: won = True; multiplier = 2
                            elif b_type == 'even_odd':
                                if num != 0:
                                    if b_val == 'even' and num % 2 == 0: won = True; multiplier = 1
                                    if b_val == 'odd' and num % 2 != 0: won = True; multiplier = 1

                            if won:
                                payout_for_num += (b_amount * multiplier) + b_amount
                        
                        diff = abs(payout_for_num - target_total_payout)
                        scored_outcomes.append((num, color, payout_for_num, diff))
                    
                    scored_outcomes.sort(key=lambda x: x[3])
                    best_candidates = scored_outcomes[:min(5, len(scored_outcomes))]
                    chosen = random.choice(best_candidates)
                    
                    winning_number = chosen[0]
                    winning_color = chosen[1]
                    total_payout = chosen[2]

                    if total_payout > 0:
                        user.balance += total_payout
                        vault.vault_balance -= total_payout
                        log = FinancialLog(action_type='جائزة روليت الحظ', admin_name='system', target_user=username, amount=total_payout, log_time=time.strftime('%Y-%m-%d %H:%M'))
                        db.session.add(log)

                    db.session.commit()
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

    user_last_bet_record = UserLastBet.query.filter_by(username=username).first()
    last_bets_json = user_last_bet_record.bets_json if user_last_bet_record else "[]"

    return render_template_string(GAME_ROULETTE_PAGE, username=username, balance=user.balance, password=user.password, msg=msg, last_win_data=last_win_data, last_bets_json=last_bets_json)

@app.route('/game_number_wheel', methods=['GET', 'POST'])
def game_number_wheel():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    user = User.query.filter_by(username=username).first()
    vault = SystemVault.query.get(1)
    
    msg = None
    winning_num = None
    is_win = False
    payout = 0.0

    if request.method == 'POST':
        try:
            selected_nums_json = request.form.get('selected_numbers', '[]')
            selected_numbers = json.loads(selected_nums_json)
            
            if not selected_numbers or len(selected_numbers) == 0:
                msg = "يرجى اختيار رقم واحد على الأقل للبدء!"
            elif len(selected_numbers) > 15:
                msg = "الحد الأقصى المسموح به للرهان هو 15 رقماً!"
            else:
                total_bet = float(len(selected_numbers))
                if user.balance >= total_bet:
                    user.balance -= total_bet
                    vault.vault_balance += total_bet

                    log_sale = FinancialLog(action_type='مبيع رهان لعبة', admin_name='system', target_user=username, amount=total_bet, log_time=time.strftime('%Y-%m-%d %H:%M'))
                    db.session.add(log_sale)

                    winning_num = random.randint(1, 20)
                    
                    if winning_num in selected_numbers:
                        is_win = True
                        payout = 15.0
                        user.balance += payout
                        vault.vault_balance -= payout
                        log = FinancialLog(action_type='جائزة عجلة الأرقام', admin_name='system', target_user=username, amount=payout, log_time=time.strftime('%Y-%m-%d %H:%M'))
                        db.session.add(log)
                        msg = f"🎉 مبروك! استقرت العجلة على الرقم الفائز ({winning_num}) وهو ضمن أرقامك المختارة! فزت بـ ${payout}!"
                    else:
                        is_win = False
                        msg = f"💥 حظ أوفر، استقرت العجلة على الرقم ({winning_num}) ولم يكن ضمن أرقامك."

                    db.session.commit()
                else:
                    msg = "رصيدك غير كافٍ لتغطية قيمة الرهانات المختارة!"
        except Exception as e:
            msg = f"حدث خطأ أثناء معالجة الرهان: {str(e)}"

    return render_template_string(GAME_NUMBER_WHEEL_PAGE, username=username, balance=user.balance, password=user.password, msg=msg, winning_num=winning_num, is_win=is_win, payout=payout)

@app.route('/game_reveal_and_win', methods=['GET', 'POST'])
def game_reveal_and_win():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    user = User.query.filter_by(username=username).first()
    vault = SystemVault.query.get(1)
    r_state = RevealAndWinState.query.get(1)
    
    msg = None
    result_data = None
    cost = 1.0

    if request.method == 'POST':
        box_indices = request.form.getlist('box_indices')
        if len(box_indices) != 3:
            msg = "يجب اختيار 3 صناديق بالضبط!"
        else:
            if user.balance >= cost:
                user.balance -= cost
                vault.vault_balance += cost

                log_sale = FinancialLog(action_type='مبيع رهان لعبة', admin_name='system', target_user=username, amount=cost, log_time=time.strftime('%Y-%m-%d %H:%M'))
                db.session.add(log_sale)

                pool = json.loads(r_state.pool_json)
                if r_state.global_attempts >= 46:
                    pool = ['WIN_3'] * 1 + ['WIN_2'] * 20 + ['LOSE'] * 25
                    random.shuffle(pool)
                    r_state.global_attempts = 0

                outcome = pool[r_state.global_attempts]
                r_state.global_attempts += 1
                db.session.commit()

                items = ['1', '3', '5', '7', '🦁']
                revealed_items = []
                prize = 0.0

                if outcome == 'WIN_3':
                    winning_item = random.choice(items)
                    revealed_items = [winning_item, winning_item, winning_item]
                    prize = 20.0
                    msg = f"🎉 مبروك يا {username}! ربحت الجائزة الكبرى 20$! 💰"
                elif outcome == 'WIN_2':
                    match_item = random.choice(items)
                    other_items = [item for item in items if item != match_item]
                    different_item = random.choice(other_items)
                    revealed_items = [match_item, match_item, different_item]
                    random.shuffle(revealed_items)
                    prize = 0.5
                    msg = f"✨ تنبيه بالربح! يا {username} لقد طابقت شكلين وربحت {prize}$"
                else:
                    revealed_items = random.sample(items, 3)
                    prize = 0.0
                    msg = f"💔 حظ أوفر يا {username}!"

                if prize > 0:
                    user.balance += prize
                    vault.vault_balance -= prize
                    log_prize = FinancialLog(action_type='جائزة اكشف واربح', admin_name='system', target_user=username, amount=prize, log_time=time.strftime('%Y-%m-%d %H:%M'))
                    db.session.add(log_prize)

                db.session.commit()
                
                selected_idxs = [int(idx) for idx in box_indices]
                boxes_map = {}
                for i, idx in enumerate(selected_idxs):
                    boxes_map[idx] = revealed_items[i]
                
                result_data = {
                    'boxes': selected_idxs,
                    'revealed': boxes_map,
                    'prize': prize
                }
            else:
                msg = "رصيدك غير كافٍ للبدء (تكلفة المحاولة 1$)!"

    return render_template_string(GAME_REVEAL_AND_WIN_PAGE, username=username, balance=user.balance, password=user.password, msg=msg, result_data=result_data)

@app.route('/game_golden_boxes_new', methods=['GET', 'POST'])
def game_golden_boxes_new():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    user = User.query.filter_by(username=username).first()
    vault = SystemVault.query.get(1)
    l_state = LuxuryGoldenState.query.get(1)
    msg = None

    if request.method == 'POST':
        if 'book_box' in request.form:
            if l_state.status == 'idle':
                box_num = int(request.form.get('box_number'))
                cost = 50.0
                if user.balance >= cost:
                    existing = LuxuryGoldenBooking.query.filter_by(box_number=box_num).first()
                    if not existing:
                        user.balance -= cost
                        vault.vault_balance += cost
                        log_sale = FinancialLog(action_type='مبيع رهان لعبة', admin_name='system', target_user=username, amount=cost, log_time=time.strftime('%Y-%m-%d %H:%M'))
                        db.session.add(log_sale)

                        new_b = LuxuryGoldenBooking(username=username, box_number=box_num, booking_date=time.strftime('%Y-%m-%d'))
                        db.session.add(new_b)
                        db.session.commit()
                        msg = f"تم حجز الصندوق رقم {box_num} بنجاح مقابل 50$!"
                    else:
                        msg = f"عذراً، الصندوق رقم {box_num} محجوز مسبقاً!"
                else:
                    msg = "رصيدك غير كافٍ (التكلفة 50$)!"
            else:
                msg = "عذراً، جاري السحب حالياً!"

        elif 'cancel_box' in request.form:
            if l_state.status == 'idle':
                box_num = int(request.form.get('box_number'))
                booking = LuxuryGoldenBooking.query.filter_by(box_number=box_num).first()
                if booking and booking.username == username:
                    db.session.delete(booking)
                    user.balance += 50.0
                    vault.vault_balance -= 50.0
                    db.session.commit()
                    msg = f"تم التراجع عن حجز الصندوق {box_num} واسترداد 50$!"
                else:
                    msg = "عذراً، لا يمكنك التراجع إلا عن الصناديق التي حجزتها بنفسك!"
            else:
                msg = "لا يمكن التراجع أثناء عملية السحب!"

        elif 'admin_execute_luxury_draw' in request.form and username == 'admin1':
            bookings_list = LuxuryGoldenBooking.query.all()
            booked_boxes = [b.box_number for b in bookings_list]
            if booked_boxes:
                forced = l_state.forced_winning_number
                winning_box = forced if (forced in booked_boxes) else random.choice(booked_boxes)
                
                winner_booking = LuxuryGoldenBooking.query.filter_by(box_number=winning_box).first()
                winner_user = User.query.filter_by(username=winner_booking.username).first()
                
                winner_user.balance += 200.0
                vault.vault_balance -= 200.0
                log = FinancialLog(action_type='جائزة الرقم الحنون الفاخر', admin_name='admin1', target_user=winner_user.username, amount=200.0, log_time=time.strftime('%Y-%m-%d %H:%M'))
                db.session.add(log)
                
                l_state.winning_number = winning_box
                l_state.status = 'finished'
                l_state.draw_end_time = time.time() + 15.0
                db.session.commit()
                msg = f"تم السحب بنجاح! الصندوق الفائز هو رقم {winning_box} للفائز {winner_user.username}"
            else:
                msg = "لا توجد صناديق محجوزة لإجراء السحب عليها حالياً!"

    bookings_records = LuxuryGoldenBooking.query.all()
    bookings = {b.box_number: b.username for b in bookings_records}
    my_bookings = LuxuryGoldenBooking.query.filter_by(username=username).all()
    my_booked_boxes = [b.box_number for b in my_bookings]
    my_total_spent = len(my_booked_boxes) * 50.0

    return render_template_string(GAME_GOLDEN_BOXES_NEW_PAGE, username=username, role=user.role, balance=user.balance, password=user.password,
                                  bookings=bookings, winning_number=l_state.winning_number, draw_status=l_state.status,
                                  my_booked_boxes=my_booked_boxes, my_total_spent=my_total_spent, msg=msg)

@app.route('/admin_customers', methods=['GET', 'POST'])
def admin_customers():
    if 'username' not in session or session.get('username') != 'admin1':
        return redirect(url_for('dashboard'))
    
    vault = SystemVault.query.get(1)
    msg = None

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'create_user':
            new_u = request.form.get('new_username', '').strip()
            new_p = request.form.get('new_password', '').strip()
            new_owner = request.form.get('new_owner', '').strip()
            existing = User.query.filter_by(username=new_u).first()
            if not existing:
                new_user = User(username=new_u, password=new_p, balance=0.0, role='player', created_by='admin1', owner_name=new_owner)
                db.session.add(new_user)
                db.session.commit()
                msg = f"تم إنشاء الحساب '{new_u}' بنجاح!"
            else:
                msg = "اسم المستخدم موجود مسبقاً!"

        elif action == 'sell_currency':
            target = request.form.get('target_user')
            amount = float(request.form.get('amount', 0))
            if vault.vault_balance >= amount and amount > 0:
                vault.vault_balance -= amount
                target_user = User.query.filter_by(username=target).first()
                if target_user:
                    target_user.balance += amount
                    log = FinancialLog(action_type='بيع عملات للزبون', admin_name='admin1', target_user=target, amount=amount, log_time=time.strftime('%Y-%m-%d %H:%M'))
                    db.session.add(log)
                    db.session.commit()
                    msg = f"تم بيع رصيد بقيمة ${amount} للحساب {target} بنجاح!"
            else:
                msg = "رصيد الخزنة غير كافٍ أو المبلغ غير صالح!"

        elif action == 'buy_back_currency':
            target = request.form.get('target_user')
            amount = float(request.form.get('amount', 0))
            target_user = User.query.filter_by(username=target).first()
            if target_user and target_user.balance >= amount and amount > 0:
                target_user.balance -= amount
                vault.vault_balance += amount
                log = FinancialLog(action_type='شراء وإعادة للخزنة', admin_name='admin1', target_user=target, amount=amount, log_time=time.strftime('%Y-%m-%d %H:%M'))
                db.session.add(log)
                db.session.commit()
                msg = f"تم استرجاع رصيد بقيمة ${amount} من الحساب {target} إلى الخزنة بنجاح!"
            else:
                msg = "رصيد الزبون غير كافٍ أو المبلغ غير صالح!"

    users_list = User.query.all()
    users_data = [(u.username, u.password, u.balance, u.role, u.created_by, u.owner_name) for u in users_list]

    return render_template_string(ADMIN_CUSTOMERS_PAGE, vault_balance=vault.vault_balance, users_list=users_data, msg=msg)

@app.route('/admin_games', methods=['GET', 'POST'])
def admin_games():
    if 'username' not in session or session.get('username') != 'admin1':
        return redirect(url_for('dashboard'))
    
    draw_state = GameDrawState.query.get(1)
    l_state = LuxuryGoldenState.query.get(1)
    msg = None

    if request.method == 'POST':
        if 'forced_winning_number' in request.form:
            forced_num = request.form.get('forced_winning_number', '').strip()
            f_val = int(forced_num) if forced_num.isdigit() else 0
            draw_state.forced_winning_number = f_val
            db.session.commit()
            msg = f"تم تحديث الرقم المسبق للرقم الحنون إلى: {f_val if f_val > 0 else 'عشوائي'}"
        elif 'forced_luxury_number' in request.form:
            forced_lux = request.form.get('forced_luxury_number', '').strip()
            l_val = int(forced_lux) if forced_lux.isdigit() else 0
            l_state.forced_winning_number = l_val
            db.session.commit()
            msg = f"تم تحديث الصندوق المسبق للرقم الحنون الفاخر إلى: {l_val if l_val > 0 else 'عشوائي'}"

    return render_template_string(ADMIN_GAMES_PAGE, forced_val=draw_state.forced_winning_number, forced_lux=l_state.forced_winning_number, msg=msg)

@app.route('/admin_accounting')
def admin_accounting():
    if 'username' not in session or session.get('username') != 'admin1':
        return redirect(url_for('dashboard'))
    
    vault = SystemVault.query.get(1)
    logs_records = FinancialLog.query.order_by(FinancialLog.id.desc()).all()
    logs = [(l.action_type, l.admin_name, l.target_user, l.amount, l.log_time) for l in logs_records]
    
    total_sales = db.session.query(db.func.sum(FinancialLog.amount)).filter(FinancialLog.action_type.in_(['بيع عملات للزبون', 'مبيع رهان لعبة'])).scalar() or 0.0
    
    payout_res1 = db.session.query(db.func.sum(FinancialLog.amount)).filter_by(action_type='جائزة الرقم الحنون').scalar() or 0.0
    payout_res3 = db.session.query(db.func.sum(FinancialLog.amount)).filter_by(action_type='جائزة روليت الحظ').scalar() or 0.0
    payout_res4 = db.session.query(db.func.sum(FinancialLog.amount)).filter_by(action_type='جائزة تحدي البالون').scalar() or 0.0
    payout_res5 = db.session.query(db.func.sum(FinancialLog.amount)).filter_by(action_type='جائزة عجلة الأرقام').scalar() or 0.0
    payout_res6 = db.session.query(db.func.sum(FinancialLog.amount)).filter_by(action_type='جائزة الرقم الحنون الفاخر').scalar() or 0.0
    payout_res7 = db.session.query(db.func.sum(FinancialLog.amount)).filter_by(action_type='جائزة اكشف واربح').scalar() or 0.0

    total_payouts = payout_res1 + payout_res3 + payout_res4 + payout_res5 + payout_res6 + payout_res7
    net_profits = total_sales - total_payouts

    return render_template_string(ADMIN_ACCOUNTING_PAGE, vault_balance=vault.vault_balance, logs=logs, total_sales=total_sales, total_payouts=total_payouts, net_profits=net_profits)


# --- قوالب HTML ---

LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تسجيل الدخول - امبراطورية الأرقام</title><link rel="manifest" href="/manifest.json">
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-box { background: linear-gradient(145deg, #1f1f1f, #121212); padding: 45px; border-radius: 20px; width: 360px; text-align: center; border: 3px solid #ffd700; box-shadow: 0 0 35px rgba(255,215,0,0.3); }
        .logo-title { font-size: 34px; font-weight: bold; color: #ffd700; text-shadow: 0 0 15px rgba(255,215,0,0.6); margin-bottom: 5px; }
        .logo-sub { font-size: 14px; color: #94a3b8; margin-bottom: 25px; }
        input { width: 100%; padding: 14px; margin: 10px 0; border-radius: 8px; border: 1px solid #444; background: #252525; color: white; box-sizing: border-box; font-size: 16px; }
        button { width: 100%; padding: 14px; background: linear-gradient(135deg, #ffd700, #b8860b); color: black; font-weight: bold; border: none; border-radius: 8px; cursor: pointer; margin-top: 15px; font-size: 18px; box-shadow: 0 4px 15px rgba(255,215,0,0.4); }
        .error { color: #ef4444; margin-bottom: 12px; font-weight: bold; }
        .no-account-btn { display: inline-block; margin-top: 15px; color: #38bdf8; text-decoration: none; font-weight: bold; font-size: 14px; }
        .no-account-btn:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="login-box">
        <div class="logo-title">👑 امبراطورية الأرقام</div><div class="logo-sub">منصة الألعاب التفاعلية الكبرى</div>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="اسم المستخدم" required>
            <input type="password" name="password" placeholder="كلمة المرور" required>
            <button type="submit">دخول للبرنامج</button>
        </form>
        <!-- زر ليس لدي حساب -> واتساب -->
        <a class="no-account-btn" href="https://wa.me/96176030208?text=اريد%20ان%20انشا%20حساب%20في%20لعبة%20امبراطورية%20الارقام" target="_blank">ليس لدي حساب؟ انقر هنا للتسجيل</a>
    </div>
</body>
</html>
"""

DASHBOARD_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>امبراطورية الأرقام - لوحة التحكم الرئيسية</title><link rel="manifest" href="/manifest.json">
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Cairo', Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 14px; box-shadow: 0 4px 15px rgba(0,0,0,0.6); flex-wrap: wrap; gap: 12px; border-bottom: 3px solid #ffd700; }
        .logo-area { display: flex; align-items: center; gap: 15px; flex-wrap: wrap; }
        .logo-badge { background: linear-gradient(135deg, #ffd700, #b8860b); color: #000; width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 26px; font-weight: bold; }
        .logo-area h1 { margin: 0; color: #ffd700; font-size: 26px; font-weight: 900; }
        .user-creds { background: #1f1f1f; padding: 8px 14px; border-radius: 8px; font-size: 14px; color: #cbd5e1; border: 1px dashed #ffd700; }
        .balance-badge { background: #065f46; color: #34d399; padding: 8px 15px; border-radius: 8px; font-weight: bold; font-size: 18px; border: 1px solid #10b981; }
        .nav-buttons { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
        .download-btn { background: #3b82f6; color: white; padding: 8px 14px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 14px; border: 1px solid #60a5fa; cursor: pointer; }
        .whatsapp-btn { background: #25d366; color: white; padding: 8px 15px; text-decoration: none; border-radius: 8px; font-weight: bold; }
        .withdraw-btn { background: #f59e0b; color: black; padding: 8px 15px; text-decoration: none; border-radius: 8px; font-weight: bold; }
        .logout-btn { background: #ef4444; color: white; padding: 8px 15px; text-decoration: none; border-radius: 8px; font-weight: bold; border: none; }
        .admin-link { background: #ffd700; color: black; padding: 8px 12px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 13px; }

        @keyframes glowAndColor {
            0% { color: #ffd700; text-shadow: 0 0 15px #ffd700, 0 0 30px #ff8c00; border-color: #ffd700; box-shadow: 0 0 20px rgba(255,215,0,0.5); }
            33% { color: #ff4500; text-shadow: 0 0 15px #ff4500, 0 0 30px #ff0000; border-color: #ff4500; box-shadow: 0 0 20px rgba(255,69,0,0.5); }
            66% { color: #00ffcc; text-shadow: 0 0 15px #00ffcc, 0 0 30px #00bfff; border-color: #00ffcc; box-shadow: 0 0 20px rgba(0,255,204,0.5); }
            100% { color: #ffd700; text-shadow: 0 0 15px #ffd700, 0 0 30px #ff8c00; border-color: #ffd700; box-shadow: 0 0 20px rgba(255,215,0,0.5); }
        }
        .promo-banner {
            background: linear-gradient(145deg, #1a1505, #0a0802);
            border: 4px solid #ffd700;
            padding: 20px 40px;
            border-radius: 25px;
            font-size: 32px;
            font-weight: 900;
            margin: 30px auto 10px auto;
            max-width: 750px;
            animation: glowAndColor 3s infinite;
            text-align: center;
            letter-spacing: 1px;
        }

        .icons-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 25px; margin-top: 30px; max-width: 900px; margin-left: auto; margin-right: auto; }
        @media (max-width: 900px) { .icons-grid { grid-template-columns: repeat(2, 1fr); } }
        @media (max-width: 500px) { .icons-grid { grid-template-columns: 1fr; } }
        
        .icon-card { 
            background: linear-gradient(145deg, #1f1f1f, #111111); 
            border: 3px solid #b8860b; 
            border-radius: 22px; 
            padding: 30px; 
            text-align: center; 
            cursor: pointer; 
            transition: all 0.4s ease; 
            box-shadow: 0 12px 30px rgba(0,0,0,0.8), inset 0 2px 6px rgba(255,255,255,0.1); 
            display: flex; 
            flex-direction: column; 
            align-items: center; 
            justify-content: center; 
            text-decoration: none; 
            aspect-ratio: 1; 
            transform: perspective(1000px) rotateX(4deg);
        }
        .icon-card:hover { 
            border-color: #ffd700; 
            transform: perspective(1000px) rotateX(0deg) translateY(-8px) scale(1.03); 
            box-shadow: 0 20px 40px rgba(255,215,0,0.4), inset 0 2px 10px rgba(255,255,255,0.2); 
        }
        .icon-logo { 
            font-size: 70px; 
            margin-bottom: 15px; 
            filter: drop-shadow(0 6px 12px rgba(0,0,0,0.7));
            transition: transform 0.3s ease;
        }
        .icon-card:hover .icon-logo {
            transform: scale(1.12) translateZ(20px);
        }
        .icon-title { 
            color: #ffd700; 
            font-size: 21px; 
            font-weight: 900; 
            text-shadow: 0 2px 5px rgba(0,0,0,0.9);
            letter-spacing: 0.5px;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo-area">
            <div class="logo-badge">👑</div><h1>امبراطورية الأرقام</h1>
            <div class="user-creds">👤 <b>{{ username }}</b></div>
            <div class="balance-badge">الرصيد: <span id="liveBalance">${{ balance }}</span></div>
        </div>
        <div class="nav-buttons">
            <button id="installAppBtn" class="download-btn" onclick="installApp()">📥 تثبيت التطبيق</button>
            <!-- زر شحن رصيد يرسل تلقائياً الحساب والباسورد إلى واتساب -->
            <a class="whatsapp-btn" href="https://wa.me/96176030208?text=اريد%20تعبئة%20رصيد%20لعبة%20امبراطورية%20الارقام%20وهذا%20هو%20حسابي%20لديكم%20-%20الحساب:%20{{ username }}%20-%20الباسورد:%20{{ password }}" target="_blank">💬 شحن رصيد</a>
            <!-- زر سحب رصيد يرسل تلقائياً الحساب والباسورد إلى واتساب -->
            <a class="withdraw-btn" href="https://wa.me/96176030208?text=اريد%20سحب%20رصيد%20لعبة%20امبراطورية%20الارقام%20وهذا%20هو%20حسابي%20لديكم%20-%20الحساب:%20{{ username }}%20-%20الباسورد:%20{{ password }}" target="_blank">💸 سحب رصيد</a>
            {% if username == 'admin1' %}
                <a href="/admin_customers" class="admin-link">👥 إدارة الزبائن والخزنة</a>
                <a href="/admin_games" class="admin-link">🎮 لوحة الألعاب</a>
                <a href="/admin_accounting" class="admin-link">📊 المحاسبة</a>
            {% endif %}
            <a href="/logout" class="logout-btn">🚪 خروج</a>
        </div>
    </div>

    <div class="promo-banner">
        ✨ العب واربح جوائز بقيمة 500,000$ ✨
    </div>

    <div class="icons-grid">
        <a href="/game_golden_number" class="icon-card"><div class="icon-logo">🏆</div><div class="icon-title">الرقم الحنون</div></a>
        <a href="/game_roulette" class="icon-card"><div class="icon-logo">🎰</div><div class="icon-title">روليت الحظ</div></a>
        <a href="/game_balloon_pop" class="icon-card"><div class="icon-logo">🎈</div><div class="icon-title">التحدي السريع (البالون)</div></a>
        <a href="/game_number_wheel" class="icon-card"><div class="icon-logo">🎡</div><div class="icon-title">عجلة الأرقام</div></a>
        <a href="/game_reveal_and_win" class="icon-card"><div class="icon-logo">🎟️</div><div class="icon-title">اكشف واربح</div></a>
        <a href="/game_golden_boxes_new" class="icon-card"><div class="icon-logo">🎁</div><div class="icon-title">الرقم الحنون الفاخر</div></a>
    </div>

    <script>
        // التحديث الصامت في الخلفية برمشة لكل الحسابات حتى لا يلاحظه اللاعب
        setInterval(() => {
            fetch('/api/sync_balance')
                .then(res => res.json())
                .then(data => {
                    let badge = document.getElementById('liveBalance');
                    if(badge && badge.innerText !== "$" + data.balance) {
                        badge.innerText = "$" + data.balance;
                    }
                })
                .catch(err => {});
        }, 2000);

        let deferredPrompt;
        window.addEventListener('beforeinstallprompt', (e) => { e.preventDefault(); deferredPrompt = e; });
        function installApp() {
            if (deferredPrompt) {
                deferredPrompt.prompt();
                deferredPrompt.userChoice.then((choiceResult) => { deferredPrompt = null; });
            } else {
                window.location.href = '/download';
            }
        }
    </script>
</body>
</html>
"""

GAME_BALLOON_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>التحدي السريع (البالون) - امبراطورية الأرقام</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; margin: 0; padding: 20px; text-align: center; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 12px; border-bottom: 2px solid #ffd700; flex-wrap: wrap; gap: 10px; }
        .download-btn { background: #3b82f6; color: white; padding: 6px 12px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 13px; cursor: pointer; border: none; }
        .game-box { background: linear-gradient(135deg, #1f1a0f, #0d0d0d); border: 4px solid #ffd700; padding: 30px; border-radius: 20px; max-width: 450px; margin: 30px auto; box-shadow: 0 0 35px rgba(255,215,0,0.3); }
        .balloon { width: 120px; height: 150px; background: radial-gradient(circle at 30% 30%, #ff5252, #c62828); border-radius: 50% 50% 50% 50% / 40% 40% 60% 60%; margin: 20px auto; position: relative; transition: 0.3s; }
        .balloon.popped { background: transparent !important; box-shadow: none !important; transform: scale(1.6); }
        .balloon.winning { background: radial-gradient(circle at 30% 30%, #ffd700, #ff8c00) !important; box-shadow: 0 0 30px rgba(255,215,0,0.9); transform: scale(1.1); }
        .pump-btn { background: linear-gradient(135deg, #ffd700, #b8860b); color: #000; font-size: 20px; font-weight: bold; padding: 15px 35px; border: none; border-radius: 12px; cursor: pointer; margin-top: 15px; width: 100%; }
        .back-btn { background: #3b82f6; color: white; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h2 style="color: #ffd700; margin: 0;">🎈 التحدي السريع (البالون)</h2>
        <div style="display: flex; gap: 15px; align-items: center;">
            <button id="installAppBtn" class="download-btn" onclick="installApp()">📥 تثبيت التطبيق</button>
            <div style="color: #34d399; font-weight: bold; font-size: 18px;">الرصيد: <span id="liveBalance">${{ balance }}</span></div>
            <a href="/dashboard" class="back-btn">⬅️ لوحة التحكم</a>
        </div>
    </div>
    {% if msg %}<div style="background: #7f1d1d; color: #fca5a5; padding: 10px; border-radius: 6px; margin-top: 15px;">{{ msg }}</div>{% endif %}
    <div class="game-box">
        <h3 style="color: #ffd700; margin-top: 0;">اضغط لضخ الهواء في البالون (التكلفة: 1$)</h3>
        <div class="balloon {% if is_popped %}popped{% elif is_win %}winning{% endif %}" id="myBalloon">
            {% if is_popped %}<div style="font-size: 45px; position: absolute; top: 40px; left: 35px;">💥</div>{% endif %}
        </div>
        <form method="POST">
            <input type="hidden" name="action" value="play_balloon">
            <button type="submit" class="pump-btn">💨 اضغط لضخ الهواء</button>
        </form>
        {% if win_result %}
        <div style="margin-top: 20px; font-size: 18px; font-weight: bold; padding: 12px; border-radius: 8px; background: {% if is_win %}#065f46{% else %}#7f1d1d{% endif %}; color: white;">
            {{ win_result }}
        </div>
        {% endif %}
    </div>
    <script>
        setInterval(() => {
            fetch('/api/sync_balance').then(res => res.json()).then(data => {
                let badge = document.getElementById('liveBalance');
                if(badge && badge.innerText !== "$" + data.balance) badge.innerText = "$" + data.balance;
            }).catch(err => {});
        }, 2000);
        function installApp() { window.location.href = '/download'; }
    </script>
</body>
</html>
"""

GAME_ROULETTE_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>روليت الحظ - امبراطورية الأرقام</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; margin: 0; padding: 15px; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 12px 20px; border-radius: 12px; border-bottom: 2px solid #ffd700; flex-wrap: wrap; gap: 10px; }
        .download-btn { background: #3b82f6; color: white; padding: 6px 12px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 13px; cursor: pointer; border: none; }
        .game-layout { display: flex; flex-direction: column; gap: 20px; margin-top: 20px; align-items: center; }
        .wheel-screen { background: #18181b; border: 4px solid #ffd700; padding: 20px; border-radius: 18px; text-align: center; width: 100%; max-width: 450px; }
        .roulette-ball-box { font-size: 50px; font-weight: bold; background: radial-gradient(circle, #2d2300 0%, #000 100%); border: 3px solid #ffd700; border-radius: 50%; width: 110px; height: 110px; display: flex; align-items: center; justify-content: center; margin: 10px auto; color: #ffd700; }
        .table-container { background: #064e3b; border: 5px solid #b8860b; padding: 15px; border-radius: 16px; overflow-x: auto; width: 100%; max-width: 650px; }
        .grid-board { display: grid; grid-template-columns: repeat(13, 1fr); gap: 4px; text-align: center; }
        .r-cell { background: #1e293b; border: 1px solid #475569; border-radius: 4px; height: 45px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 14px; font-weight: bold; cursor: pointer; }
        .r-cell.red { background: #dc2626; color: white; }
        .r-cell.black { background: #0f172a; color: white; }
        .r-cell.green { background: #16a34a; color: white; }
        .fixed-bet-notice { background: #1f2937; border: 1px dashed #ffd700; color: #ffd700; padding: 8px 15px; border-radius: 8px; font-size: 14px; margin-bottom: 12px; font-weight: bold; text-align: center; }
        .quick-bets-bar { display: flex; gap: 10px; justify-content: center; margin: 10px 0; flex-wrap: wrap; }
        .quick-btn { padding: 10px 15px; border-radius: 8px; font-weight: bold; border: none; cursor: pointer; font-size: 14px; color: white; }
        .spin-btn { background: linear-gradient(135deg, #ffd700, #b8860b); color: #000; font-size: 18px; font-weight: bold; padding: 12px 30px; border: none; border-radius: 10px; cursor: pointer; }
        .clear-btn { background: #ef4444; color: white; font-weight: bold; padding: 12px 20px; border: none; border-radius: 10px; cursor: pointer; }
        .repeat-btn { background: #3b82f6; color: white; font-weight: bold; padding: 12px 20px; border: none; border-radius: 10px; cursor: pointer; }
        .back-btn { background: #3b82f6; color: white; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h2 style="color: #ffd700; margin: 0;">🎰 روليت الحظ</h2>
        <div style="display: flex; gap: 15px; align-items: center;">
            <button id="installAppBtn" class="download-btn" onclick="installApp()">📥 تثبيت التطبيق</button>
            <div style="color: #34d399; font-weight: bold; font-size: 16px;">الرصيد: <span id="liveBalance">${{ balance }}</span></div>
            <a href="/dashboard" class="back-btn">⬅️ لوحة التحكم</a>
        </div>
    </div>
    {% if msg %}<div style="background: {% if last_win_data and last_win_data.total_payout > 0 %}#065f46{% else %}#7f1d1d{% endif %}; color: white; padding: 12px; border-radius: 8px; margin-top: 15px; text-align: center; font-weight: bold;">{{ msg }}</div>{% endif %}
    <div class="game-layout">
        <div class="wheel-screen">
            <h3 style="color: #ffd700; margin: 0 0 10px 0;">🎯 نتيجة السحب</h3>
            <div class="roulette-ball-box" id="winningDisplay">{% if last_win_data %}{{ last_win_data.winning_number }}{% else %}?{% endif %}</div>
            <p style="color: #cbd5e1; margin: 5px 0 0 0; font-size: 14px;">
                {% if last_win_data %}اللون: <b style="color: {% if last_win_data.winning_color == 'red' %}#ef4444{% elif last_win_data.winning_color == 'green' %}#22c55e{% else %}#94a3b8{% endif %};">{{ last_win_data.winning_color }}</b> | إجمالي الرهان: ${{ last_win_data.total_bet }}{% else %}اختر رهاناتك من الطاولة أدناه ثم اضغط تدوير{% endif %}
            </p>
        </div>
        <div style="text-align: center; width: 100%; max-width: 450px;">
            <div class="fixed-bet-notice">📌 الرهان ثابت حصرياً بقيمة <b>1$</b> لكل نقرة / رقم</div>
            <div class="quick-bets-bar">
                <button type="button" class="quick-btn" style="background: #dc2626;" onclick="betAllColor('red')">🔴 رهان على كل الأحمر (Red)</button>
                <button type="button" class="quick-btn" style="background: #0f172a; border: 1px solid #475569;" onclick="betAllColor('black')">⚫ رهان على كل الأسود (Black)</button>
            </div>
        </div>
        <div class="table-container">
            <div style="text-align: center; color: #ffd700; font-weight: bold; margin-bottom: 8px;">طاولة الرهانات الرقمية (كل نقرة بـ 1$)</div>
            <div class="grid-board" id="bettingBoard">
                <div class="r-cell green" style="grid-row: span 3;" onclick="placeBet('straight', 0, this)">0<span class="bet-tag" style="font-size:10px; color:#ffd700;"></span></div>
                <script>
                    let redsList = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36];
                    for(let i=1; i<=36; i++) {
                        let colorClass = redsList.includes(i) ? 'red' : 'black';
                        document.write(`<div class="r-cell ${colorClass}" data-num="${i}" data-color="${colorClass}" onclick="placeBet('straight', ${i}, this)">${i}<span class="bet-tag" style="font-size:10px; color:#ffd700;"></span></div>`);
                    }
                </script>
            </div>
        </div>
        <form method="POST" id="rouletteForm">
            <input type="hidden" name="bets_data" id="betsDataInput">
            <input type="hidden" name="total_bet_amount" id="totalBetInput" value="0">
            <div style="text-align: center; color: #cbd5e1; font-size: 15px; margin-bottom: 10px;">
                إجمالي الرهان الحالي: <b style="color: #ffd700;" id="totalBetText">$0</b>
            </div>
            <div style="display: flex; gap: 10px; justify-content: center; flex-wrap: wrap;">
                <button type="button" class="clear-btn" onclick="clearBets()">🗑️ مسح الرهانات</button>
                <button type="button" class="repeat-btn" onclick="repeatLastBet()">🔄 تكرار آخر رهان</button>
                <button type="submit" class="spin-btn" onclick="prepareSubmit()">🎡 تدوير العجلة (Spin)</button>
            </div>
        </form>
    </div>
    <script>
        setInterval(() => {
            fetch('/api/sync_balance').then(res => res.json()).then(data => {
                let badge = document.getElementById('liveBalance');
                if(badge && badge.innerText !== "$" + data.balance) badge.innerText = "$" + data.balance;
            }).catch(err => {});
        }, 2000);

        let fixedChipValue = 1;
        let activeBets = {};
        let lastUserBetsJson = '{{ last_bets_json | safe }}';

        function placeBet(type, value, element) {
            let key = type + "_" + value;
            if (!activeBets[key]) { activeBets[key] = { type: type, value: value, amount: 0 }; }
            activeBets[key].amount += fixedChipValue;
            let tag = element.querySelector('.bet-tag');
            if(tag) { tag.innerText = "$" + activeBets[key].amount; } 
            else { element.innerHTML += `<span class="bet-tag" style="font-size:10px; color:#ffd700;">$${activeBets[key].amount}</span>`; }
            updateTotalSummary();
        }

        function betAllColor(colorName) {
            let cells = document.querySelectorAll('.r-cell');
            cells.forEach(cell => {
                let cellColor = cell.getAttribute('data-color');
                let numStr = cell.getAttribute('data-num');
                if (cellColor === colorName && numStr) {
                    let num = parseInt(numStr);
                    placeBet('straight', num, cell);
                }
            });
        }

        function repeatLastBet() {
            if (!lastUserBetsJson || lastUserBetsJson === '[]') {
                alert('لا يوجد رهان سابق محفوظ لتكراره!');
                return;
            }
            clearBets();
            try {
                let parsedBets = JSON.parse(lastUserBetsJson);
                parsedBets.forEach(bet => {
                    let key = bet.type + "_" + bet.value;
                    activeBets[key] = { type: bet.type, value: bet.value, amount: bet.amount };
                    
                    if (bet.type === 'straight') {
                        let cell = document.querySelector(`.r-cell[data-num="${bet.value}"]`);
                        if (cell) {
                            let tag = cell.querySelector('.bet-tag');
                            if(tag) { tag.innerText = "$" + bet.amount; }
                            else { cell.innerHTML += `<span class="bet-tag" style="font-size:10px; color:#ffd700;">$${bet.amount}</span>`; }
                        }
                    }
                });
                updateTotalSummary();
            } catch(e) {
                console.error(e);
            }
        }

        function updateTotalSummary() {
            let total = 0;
            for (let k in activeBets) { total += activeBets[k].amount; }
            document.getElementById('totalBetText').innerText = "$" + total;
            document.getElementById('totalBetInput').value = total;
        }

        function clearBets() {
            activeBets = {};
            document.querySelectorAll('.bet-tag').forEach(t => t.innerText = "");
            updateTotalSummary();
        }

        function prepareSubmit() {
            let betsArray = [];
            for (let k in activeBets) { betsArray.push(activeBets[k]); }
            document.getElementById('betsDataInput').value = JSON.stringify(betsArray);
        }

        function installApp() { window.location.href = '/download'; }
    </script>
</body>
</html>
"""

GAME_NUMBER_WHEEL_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>عجلة الأرقام - امبراطورية الأرقام</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; margin: 0; padding: 20px; text-align: center; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 12px; border-bottom: 2px solid #ffd700; flex-wrap: wrap; gap: 10px; }
        .download-btn { background: #3b82f6; color: white; padding: 6px 12px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 13px; cursor: pointer; border: none; }
        .game-box { background: linear-gradient(135deg, #1f1a0f, #0d0d0d); border: 4px solid #ffd700; padding: 30px; border-radius: 24px; max-width: 600px; margin: 20px auto; box-shadow: 0 0 40px rgba(255,215,0,0.3); }
        .wheel-circle { width: 150px; height: 150px; background: radial-gradient(circle, #3d2c00 0%, #1a1200 100%); border: 6px solid #ffd700; border-radius: 50%; margin: 15px auto; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 42px; font-weight: bold; color: #ffd700; box-shadow: 0 0 25px rgba(255,215,0,0.5); transition: transform 2s cubic-bezier(0.15, 0.85, 0.35, 1.2); }
        .wheel-circle.lose { background: #dc2626 !important; border-color: #991b1b !important; color: #000000 !important; }
        .wheel-circle.win { background: radial-gradient(circle, #ffd700 0%, #b8860b 100%) !important; border-color: #fff !important; color: #000 !important; }
        .win-label { font-size: 14px; color: #ffffff !important; font-weight: bold; margin-top: -2px; }
        .numbers-board { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin: 20px 0; }
        .num-cell { background: #252525; border: 2px solid #555; border-radius: 10px; height: 45px; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: bold; color: #fff; cursor: pointer; transition: 0.2s; }
        .num-cell.selected { background: #22c55e; border-color: #ffd700; color: #000; transform: scale(1.05); }
        .spin-action-btn { background: linear-gradient(135deg, #ffd700, #b8860b); color: #000; font-size: 18px; font-weight: bold; padding: 12px 30px; border: none; border-radius: 12px; cursor: pointer; margin-top: 15px; width: 100%; box-shadow: 0 4px 20px rgba(255,215,0,0.4); }
        .spin-action-btn:disabled { background: #444; color: #888; cursor: not-allowed; }
        .back-btn { background: #3b82f6; color: white; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h2 style="color: #ffd700; margin: 0;">🎡 عجلة الأرقام الكبرى</h2>
        <div style="display: flex; gap: 15px; align-items: center;">
            <button id="installAppBtn" class="download-btn" onclick="installApp()">📥 تثبيت التطبيق</button>
            <div style="color: #34d399; font-weight: bold; font-size: 18px;">الرصيد: <span id="liveBalance">${{ balance }}</span></div>
            <a href="/dashboard" class="back-btn">⬅️ لوحة التحكم</a>
        </div>
    </div>
    {% if msg %}<div style="background: {% if is_win %}#065f46{% else %}#7f1d1d{% endif %}; color: white; padding: 12px; border-radius: 8px; margin-top: 15px; text-align: center; font-weight: bold; max-width: 600px; margin-left: auto; margin-right: auto;">{{ msg }}</div>{% endif %}
    <div class="game-box">
        <h3 style="color: #ffd700; margin-top: 0;">اختر أرقامك (بحد أقصى 15 رقماً | 1$ لكل رقم) ثم أدر العجلة!</h3>
        <div class="wheel-circle {% if winning_num is not none %}{% if is_win %}win{% else %}lose{% endif %}{% endif %}" id="wheelDisplay">
            {% if winning_num is not none %}
                <span>{{ winning_num }}</span>
                {% if is_win %}<span class="win-label">مبروك</span>{% endif %}
            {% else %}
                🎡
            {% endif %}
        </div>
        <p style="color: #38bdf8; font-size: 14px; margin: 5px 0;">الأرقام المختارة: <b id="selectedCountText">0</b> / 15</p>
        
        <div class="numbers-board">
            {% for i in range(1, 21) %}
                <div class="num-cell" onclick="toggleNumber({{ i }}, this)">{{ i }}</div>
            {% endfor %}
        </div>

        <form method="POST" id="wheelForm" onsubmit="spinWheelAndSubmit(event)">
            <input type="hidden" name="selected_numbers" id="selectedNumbersInput" value="[]">
            <div style="color: #ffd700; font-size: 16px; margin-bottom: 10px;">إجمالي الرهان: <b id="totalBetText">$0</b></div>
            <button type="submit" class="spin-action-btn" id="spinBtn" disabled>🎯 أدر العجلة الآن</button>
        </form>
    </div>
    <script>
        setInterval(() => {
            fetch('/api/sync_balance').then(res => res.json()).then(data => {
                let badge = document.getElementById('liveBalance');
                if(badge && badge.innerText !== "$" + data.balance) badge.innerText = "$" + data.balance;
            }).catch(err => {});
        }, 2000);

        let selectedNumbers = [];
        function toggleNumber(num, element) {
            let wheel = document.getElementById('wheelDisplay');
            if (wheel.innerText.trim() !== '🎡') {
                wheel.className = "wheel-circle";
                wheel.innerText = '🎡';
            }
            if (selectedNumbers.includes(num)) {
                selectedNumbers = selectedNumbers.filter(n => n !== num);
                element.classList.remove('selected');
            } else {
                if (selectedNumbers.length < 15) {
                    selectedNumbers.push(num);
                    element.classList.add('selected');
                } else {
                    alert('عذراً، الحد الأقصى للرهان هو 15 رقماً فقط!');
                }
            }
            document.getElementById('selectedCountText').innerText = selectedNumbers.length;
            document.getElementById('totalBetText').innerText = "$" + selectedNumbers.length;
            document.getElementById('selectedNumbersInput').value = JSON.stringify(selectedNumbers);
            document.getElementById('spinBtn').disabled = (selectedNumbers.length === 0);
        }

        function spinWheelAndSubmit(e) {
            e.preventDefault(); 
            let wheel = document.getElementById('wheelDisplay');
            let btn = document.getElementById('spinBtn');
            btn.disabled = true;
            btn.innerText = "⏳ جاري تدوير العجلة...";
            wheel.className = "wheel-circle";
            wheel.innerText = "🎡";
            wheel.style.transform = "rotate(1800deg)";
            setTimeout(function() {
                document.getElementById('wheelForm').submit();
            }, 2000); 
        }

        function installApp() { window.location.href = '/download'; }
    </script>
</body>
</html>
"""

GAME_REVEAL_AND_WIN_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>اكشف واربح - امبراطورية الأرقام</title>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&display=swap" rel="stylesheet">
    <style>
        body { background-color: #0b0f19; color: #fff; font-family: 'Cairo', sans-serif; margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 12px; border: 2px solid #ffd700; width: 100%; max-width: 800px; box-sizing: border-box; margin-bottom: 20px; }
        .back-btn { background: #3b82f6; color: white; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold; }
        h1 { background: linear-gradient(to left, #ffd700, #ff8c00); -webkit-background-clip: text; color: transparent; font-size: 2.2rem; margin: 10px 0; text-align: center; }
        .game-box { background: linear-gradient(135deg, #1f1a0f, #0d0d0d); border: 4px solid #ffd700; padding: 30px; border-radius: 24px; max-width: 700px; width: 100%; box-sizing: border-box; text-align: center; box-shadow: 0 0 40px rgba(255,215,0,0.3); }
        .boxes-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin: 20px 0; }
        .box-card { background: linear-gradient(145deg, #b8860b, #daa520); border: 3px solid #fff; border-radius: 12px; height: 85px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 26px; font-weight: bold; color: #000; cursor: pointer; transition: 0.2s; }
        .box-card.selected { background: linear-gradient(145deg, #22c55e, #15803d) !important; color: #fff !important; transform: scale(1.05); }
        .play-action-btn { background: linear-gradient(135deg, #ffd700, #b8860b); color: #000; font-size: 18px; font-weight: bold; padding: 14px 30px; border: none; border-radius: 12px; cursor: pointer; margin-top: 15px; width: 100%; box-shadow: 0 4px 20px rgba(255,215,0,0.4); }
        .play-action-btn:disabled { background: #444; color: #888; cursor: not-allowed; }
        .reset-btn { background: #3b82f6; color: white; font-size: 16px; font-weight: bold; padding: 10px 20px; border: none; border-radius: 10px; cursor: pointer; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="header">
        <h2 style="color: #ffd700; margin: 0;">🎟️ اكشف واربح</h2>
        <div style="color: #34d399; font-weight: bold; font-size: 18px;">الرصيد: <span id="liveBalance">${{ balance }}</span></div>
        <a href="/dashboard" class="back-btn">⬅️ لوحة التحكم</a>
    </div>

    <h1>أمامك 15 صندوقاً، اختر 3 صناديق وطابق الأشكال لتربح! (التكلفة: 1$)</h1>
    {% if msg %}<div style="background: {% if 'مبروك' in msg or 'تنبيه' in msg %}#065f46{% else %}#7f1d1d{% endif %}; color: white; padding: 12px; border-radius: 8px; margin-bottom: 20px; font-weight: bold; text-align: center; width: 100%; max-width: 700px;">{{ msg }}</div>{% endif %}

    <div class="game-box">
        <p style="color: #38bdf8; font-size: 15px; margin: 5px 0 15px 0;">الصناديق المختارة: <b id="selectionCount">0</b> / 3</p>
        
        <form method="POST" id="scratchForm">
            <div id="hiddenInputsContainer"></div>
            <div class="boxes-grid">
                {% for i in range(15) %}
                    <div class="box-card" id="box-{{ i }}" onclick="toggleBox({{ i }})">
                        <span id="box-icon-{{ i }}">📦</span>
                        <span id="box-text-{{ i }}" style="font-size: 11px; margin-top: 2px;">صندوق {{ i+1 }}</span>
                        <span id="box-val-{{ i }}" style="display:none; font-size: 32px;">
                            {% if result_data and i in result_data.revealed %}{{ result_data.revealed[i] }}{% endif %}
                        </span>
                    </div>
                {% endfor %}
            </div>
            <button type="submit" class="play-action-btn" id="playBtn" disabled>🎟️ اكشف الصناديق المختارة (1$)</button>
        </form>

        {% if result_data %}
        <button type="button" class="reset-btn" onclick="resetGameBoxes()">🔄 محاولة جديدة (إعادة إغلاق الصناديق)</button>
        {% endif %}
    </div>

    <script>
        setInterval(() => {
            fetch('/api/sync_balance').then(res => res.json()).then(data => {
                let badge = document.getElementById('liveBalance');
                if(badge && badge.innerText !== "$" + data.balance) badge.innerText = "$" + data.balance;
            }).catch(err => {});
        }, 2000);

        let selectedBoxes = [];
        let resultJson = '{{ result_data | tojson | safe }}';

        window.onload = function() {
            if (resultJson && resultJson !== 'None' && resultJson !== 'null') {
                try {
                    let res = JSON.parse(resultJson);
                    let map = res.revealed;
                    for (let idx in map) {
                        let card = document.getElementById('box-' + idx);
                        document.getElementById('box-icon-' + idx).innerText = "🔓";
                        document.getElementById('box-text-' + idx).style.display = "none";
                        let valSpan = document.getElementById('box-val-' + idx);
                        valSpan.innerText = map[idx];
                        valSpan.style.display = "block";
                        card.style.background = "linear-gradient(145deg, #1e3a8a, #1d4ed8)";
                        card.style.color = "#fff";
                    }
                } catch(e) { console.error(e); }
            }
        };

        function toggleBox(index) {
            if (resultJson && resultJson !== 'None' && resultJson !== 'null') return;

            let card = document.getElementById('box-' + index);
            if (selectedBoxes.includes(index)) {
                selectedBoxes = selectedBoxes.filter(i => i !== index);
                card.classList.remove('selected');
            } else {
                if (selectedBoxes.length < 3) {
                    selectedBoxes.push(index);
                    card.classList.add('selected');
                } else {
                    alert('يمكنك اختيار 3 صناديق كحد أقصى في كل محاولة!');
                }
            }
            document.getElementById('selectionCount').innerText = selectedBoxes.length;
            let container = document.getElementById('hiddenInputsContainer');
            container.innerHTML = "";
            selectedBoxes.forEach(boxIdx => {
                let input = document.createElement('input');
                input.type = 'hidden'; input.name = 'box_indices'; input.value = boxIdx;
                container.appendChild(input);
            });
            document.getElementById('playBtn').disabled = (selectedBoxes.length !== 3);
        }

        function resetGameBoxes() {
            window.location.href = '/game_reveal_and_win';
        }
    </script>
</body>
</html>
"""

GAME_GOLDEN_BOXES_NEW_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>الرقم الحنون الفاخر</title>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@700;900&display=swap" rel="stylesheet">
    <style>
        body { background-color: #0d0d0d; color: #fff; font-family: 'Cairo', sans-serif; margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 12px 25px; border-radius: 12px; border: 2px solid #d4af37; width: 100%; max-width: 900px; box-sizing: border-box; margin-bottom: 20px; }
        .back-btn { background: #3b82f6; color: white; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold; }
        h1 { background: linear-gradient(to left, #bf953f, #fcf6ba, #b38728, #fbf5b7, #aa771c); -webkit-background-clip: text; color: transparent; font-size: 2.2rem; margin: 10px 0; text-align: center; }
        .schedule-notice { color: #ffd700; background: #1f1f1f; border: 1px dashed #d4af37; padding: 10px 20px; border-radius: 8px; font-size: 15px; margin-bottom: 20px; text-align: center; }
        .user-stats-box { background: #18181b; border: 2px dashed #b8860b; padding: 15px; border-radius: 14px; margin-bottom: 20px; display: flex; justify-content: space-around; align-items: center; width: 100%; max-width: 700px; flex-wrap: wrap; gap: 15px; }
        .board-container { background: linear-gradient(135deg, #110d06, #000000); border: 5px solid #b8860b; padding: 25px; border-radius: 18px; margin-bottom: 25px; text-align: center; width: 100%; max-width: 700px; box-sizing: border-box; }
        .board-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 15px; margin-top: 15px; }
        .number-box { background: #3d2314; border: 2px solid #8b5a2b; border-radius: 12px; height: 90px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 22px; font-weight: bold; color: #ffffff; cursor: pointer; transition: 0.2s; }
        .number-box:hover { transform: translateY(-3px); border-color: #ffd700; }
        .number-box.booked { background: #7f1d1d !important; border-color: #ef4444 !important; color: #fca5a5 !important; cursor: not-allowed; }
        .number-box.my-booked { background: #1e3a8a !important; border-color: #3b82f6 !important; color: #93c5fd !important; }
        .number-box.winning { background: linear-gradient(135deg, #ffd700, #ff8c00) !important; color: #000 !important; }
        .draw-panel { background: #18181b; border: 3px solid #ffd700; padding: 25px; border-radius: 16px; margin-top: 20px; text-align: center; width: 100%; max-width: 700px; box-sizing: border-box; }
        .big-slot-screen { background: radial-gradient(circle, #3d2c00 0%, #000000 100%); border: 4px solid #ffd700; color: #ffd700; font-size: 60px; font-weight: bold; padding: 10px; width: 180px; margin: 15px auto; border-radius: 16px; }
        .win-badge { background: linear-gradient(135deg, #ffd700, #b8860b); color: #000; border: 3px solid #fff; padding: 15px; border-radius: 12px; margin: 15px auto; width: 90%; max-width: 450px; text-align: center; font-size: 20px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h2 style="color: #ffd700; margin: 0;">🎁 الرقم الحنون الفاخر</h2>
        <div style="color: #34d399; font-weight: bold; font-size: 18px;">الرصيد: <span id="liveBalance">${{ balance }}</span></div>
        <a href="/dashboard" class="back-btn">⬅️ لوحة التحكم</a>
    </div>

    <h1>اختر صندوقاً للحجز (التكلفة: 50$ | الجائزة: 200$)</h1>
    <div class="schedule-notice">⏰ مواعيد السحب: مرتين يومياً (عند الساعة 12:00 ظهراً وعند الساعة 22:00 مساءً)</div>
    
    {% if msg %}<div style="background: #065f46; color: #34d399; padding: 12px; border-radius: 8px; margin-bottom: 20px; font-weight: bold; text-align: center; width: 100%; max-width: 700px;">{{ msg }}</div>{% endif %}

    <div class="user-stats-box">
        <div><b style="color: #ffd700;">👤 حسابك:</b> <span style="color: #cbd5e1;">{{ username }}</span></div>
        <div><b style="color: #38bdf8;">صناديقك المحجوزة:</b> <span style="color: #fff; font-family: monospace; background: #000; padding: 4px 8px; border-radius: 4px;">{% if my_booked_boxes %}{{ my_booked_boxes | join(', ') }}{% else %}لا توجد{% endif %}</span></div>
        <div><b style="color: #34d399;">المصروف:</b> <span style="color: #34d399; font-weight: bold;">${{ my_total_spent }}</span></div>
    </div>

    <div class="board-container">
        <h3 style="color: #ffd700; margin-top: 0;">📦 صناديق الحجز الجماعي</h3>
        <div class="board-grid">
            {% for i in range(1, 6) %}
                {% if i in bookings %}
                    {% if bookings[i] == username %}
                        <form method="POST" style="margin: 0;">
                            <input type="hidden" name="box_number" value="{{ i }}">
                            <button type="submit" name="cancel_box" class="number-box my-booked" style="width: 100%;" title="إلغاء الحجز واسترداد 50$">
                                صندوق {{ i }}<br><span style="font-size: 11px;">(أنت) ❌</span>
                            </button>
                        </form>
                    {% else %}
                        <div class="number-box booked" title="محجوز بواسطة {{ bookings[i] }}">
                            صندوق {{ i }}<br><span style="font-size: 11px; color: #fca5a5;">({{ bookings[i] }})</span>
                        </div>
                    {% endif %}
                {% else %}
                    <form method="POST" style="margin: 0;">
                        <input type="hidden" name="box_number" value="{{ i }}">
                        <button type="submit" name="book_box" class="number-box" style="width: 100%;">صندوق {{ i }}<br><span style="font-size: 11px; color: #ffd700;">حجز 50$</span></button>
                    </form>
                {% endif %}
            {% endfor %}
        </div>
    </div>

    {% if username == 'admin1' %}
    <div class="draw-panel">
        <h3 style="color: #ffd700; margin-top: 0;">👑 لوحة التحكم والتحكم بالسحب (خاص بالآدمن)</h3>
        <p id="statusText" style="color: #cbd5e1; font-size: 15px;">{% if draw_status == 'finished' %}🎉 تم إعلان الصندوق الفائز!{% else %}في انتظار تنفيذ السحب في مواعيده المحددة{% endif %}</p>
        <div class="big-slot-screen" id="slotDisplay">{% if draw_status == 'finished' and winning_number %}{{ winning_number }}{% else %}?{% endif %}</div>
        <div id="winNotificationContainer">
            {% if draw_status == 'finished' and winning_number %}
            <div class="win-badge">الفائز بالصندوق رقم {{ winning_number }} حصل على 200$!</div>
            {% endif %}
        </div>
        <form method="POST" style="margin-top: 15px; border-top: 1px dashed #555; padding-top: 15px;">
            <button type="submit" name="admin_execute_luxury_draw" style="background: linear-gradient(135deg, #22c55e, #15803d); color: white; font-weight: bold; padding: 12px 30px; border: none; border-radius: 8px; cursor: pointer; font-size: 16px;">⚡ تنفيذ السحب الآن (للآدمن فقط)</button>
        </form>
    </div>
    {% endif %}

    <script>
        setInterval(() => {
            fetch('/api/sync_balance').then(res => res.json()).then(data => {
                let badge = document.getElementById('liveBalance');
                if(badge && badge.innerText !== "$" + data.balance) badge.innerText = "$" + data.balance;
            }).catch(err => {});
        }, 2000);

        let lastStatus = "{{ draw_status }}";
        let isRefreshing = false;
        function checkGameRealtime() {
            if (isRefreshing) return;
            fetch('/api/luxury_golden_status')
                .then(res => res.json())
                .then(data => {
                    if (data.status !== lastStatus && !isRefreshing) {
                        isRefreshing = true;
                        setTimeout(() => { location.reload(); }, 200);
                        return;
                    }
                    let slotEl = document.getElementById('slotDisplay');
                    let statusText = document.getElementById('statusText');
                    if (slotEl && data.status === 'finished') {
                        slotEl.innerText = data.winning_number;
                        if (statusText) statusText.innerText = "🎉 تم إعلان الصندوق الفائز!";
                    }
                });
        }
        setInterval(checkGameRealtime, 1000);
        function installApp() { window.location.href = '/download'; }
    </script>
</body>
</html>
"""

GAME_GOLDEN_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>الرقم الحنون - امبراطورية الأرقام</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 12px; border-bottom: 2px solid #ffd700; flex-wrap: wrap; gap: 10px; }
        .download-btn { background: #3b82f6; color: white; padding: 6px 12px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 13px; cursor: pointer; border: none; }
        .user-stats-box { background: #18181b; border: 2px dashed #b8860b; padding: 15px; border-radius: 14px; margin-top: 20px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px; }
        .board-container { background: linear-gradient(135deg, #110d06, #000000); border: 5px solid #b8860b; padding: 25px; border-radius: 18px; margin-top: 20px; text-align: center; }
        .board-grid { display: grid; grid-template-columns: repeat(10, 1fr); gap: 12px; margin-top: 20px; }
        @media(max-width: 768px) { .board-grid { grid-template-columns: repeat(5, 1fr); } }
        .number-box { background: #3d2314; border: 2px solid #8b5a2b; border-radius: 10px; height: 60px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 20px; font-weight: bold; color: #ffffff; cursor: pointer; }
        .number-box.booked { background: #7f1d1d !important; border-color: #ef4444 !important; color: #fca5a5 !important; cursor: not-allowed; }
        .number-box.my-booked { background: #1e3a8a !important; border-color: #3b82f6 !important; color: #93c5fd !important; }
        .number-box.winning { background: linear-gradient(135deg, #ffd700, #ff8c00) !important; color: #000 !important; }
        .draw-panel { background: #18181b; border: 3px solid #ffd700; padding: 25px; border-radius: 16px; margin-top: 25px; text-align: center; }
        .big-slot-screen { background: radial-gradient(circle, #3d2c00 0%, #000000 100%); border: 4px solid #ffd700; color: #ffd700; font-size: 70px; font-weight: bold; padding: 15px; width: 240px; margin: 15px auto; border-radius: 20px; }
        .win-badge { background: linear-gradient(135deg, #ffd700, #b8860b); color: #000; border: 3px solid #fff; padding: 20px; border-radius: 15px; margin: 20px auto; width: 90%; max-width: 500px; text-align: center; font-size: 24px; font-weight: bold; }
        .back-btn { background: #3b82f6; color: white; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h2 style="color: #ffd700; margin: 0;">🏆 الرقم الحنون</h2>
        <div style="display: flex; gap: 15px; align-items: center;">
            <button id="installAppBtn" class="download-btn" onclick="installApp()">📥 تثبيت التطبيق</button>
            <div style="color: #34d399; font-weight: bold; font-size: 18px;">الرصيد: <span id="liveBalance">${{ balance }}</span></div>
            <a href="/dashboard" class="back-btn">⬅️ لوحة التحكم</a>
        </div>
    </div>
    {% if msg %}<div style="background: #065f46; color: #34d399; padding: 12px; border-radius: 8px; margin-top: 15px; text-align: center; font-weight: bold;">{{ msg }}</div>{% endif %}
    <div class="user-stats-box">
        <div><b style="color: #ffd700;">👤 حسابك:</b> <span style="color: #cbd5e1;">{{ username }}</span></div>
        <div><b style="color: #38bdf8;">أرقامك:</b> <span style="color: #fff; font-family: monospace; background: #000; padding: 4px 8px; border-radius: 4px;">{% if my_booked_nums %}{{ my_booked_nums | join(', ') }}{% else %}لا توجد{% endif %}</span></div>
        <div><b style="color: #34d399;">المصروف:</b> <span style="color: #34d399; font-weight: bold;">${{ my_total_spent }}</span></div>
    </div>
    <div class="board-container">
        <h3 style="color: #ffd700; margin-top: 0;">🎯 اختر أرقامك (تكلفة الحجز: 2$ | الجائزة: 75$)</h3>
        <div class="board-grid">
            {% for i in range(1, 51) %}
                {% if i in bookings %}
                    {% if bookings[i] == username %}
                        <form method="POST" style="margin: 0;">
                            <input type="hidden" name="number" value="{{ i }}">
                            <button type="submit" name="cancel_number" id="box-{{ i }}" class="number-box my-booked" style="width: 100%; height: 60px;" title="تراجع واسترداد 2$">
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
                        <button type="submit" name="book_number" id="box-{{ i }}" class="number-box" style="width: 100%; height: 60px;">{{ i }}</button>
                    </form>
                {% endif %}
            {% endfor %}
        </div>
    </div>
    <div class="draw-panel">
        <h3 style="color: #ffd700; margin-top: 0;">🎰 شاشة السحب الفوري</h3>
        <p id="statusText" style="color: #cbd5e1; font-size: 16px;">{% if draw_status == 'finished' %}🎉 تم إعلان الفائز!{% else %}في انتظار ضغط زر السحب من المؤسس{% endif %}</p>
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
        setInterval(() => {
            fetch('/api/sync_balance').then(res => res.json()).then(data => {
                let badge = document.getElementById('liveBalance');
                if(badge && badge.innerText !== "$" + data.balance) badge.innerText = "$" + data.balance;
            }).catch(err => {});
        }, 2000);

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
        function installApp() { window.location.href = '/download'; }
    </script>
</body>
</html>
"""

ADMIN_CUSTOMERS_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>إدارة الزبائن والخزنة - امبراطورية الأرقام</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; padding: 20px; }
        .admin-header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 12px; border: 2px solid #ffd700; margin-bottom: 25px; }
        .download-btn { background: #3b82f6; color: white; padding: 6px 12px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 13px; cursor: pointer; border: none; }
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
        <h2 style="color: #ffd700; margin: 0;">👑 لوحة تحكم المؤسس - امبراطورية الأرقام</h2>
        <div style="display: flex; gap: 15px; align-items: center;">
            <button id="installAppBtn" class="download-btn" onclick="installApp()">📥 تثبيت التطبيق</button>
            <a href="/dashboard" class="back-btn">⬅️ العودة للرئيسية</a>
        </div>
    </div>
    {% if msg %}<div style="background: #065f46; color: #34d399; padding: 12px; border-radius: 8px; margin-bottom: 20px; text-align: center; font-weight: bold;">{{ msg }}</div>{% endif %}
    <div class="vault-box">
        <h3 style="margin: 0; color: #a7f3d0; font-size: 18px;">🏦 خزنة الشركة الأساسية (حصري لـ admin1)</h3>
        <div style="font-size: 45px; font-weight: bold; color: #fff; margin: 10px 0;">${{ vault_balance }}</div>
    </div>
    <div class="panel-grid">
        <div class="panel-box">
            <h3 style="color: #3b82f6; margin-top: 0;">👤 خلق حساب جديد</h3>
            <form method="POST">
                <input type="hidden" name="action" value="create_user">
                <label>اسم المستخدم:</label><input type="text" name="new_username" placeholder="اسم المستخدم" required>
                <label>الرقم السري:</label><input type="password" name="new_password" placeholder="كلمة المرور" required>
                <label>صاحب الحساب:</label><input type="text" name="new_owner" placeholder="اسم صاحب الحساب الحقيقي" required>
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
                    {% for u in users_list %}<option value="{{ u[0] }}">{{ u[0] }} (صاحبه: {{ u[5] }} | رصيده: ${{ u[2] }})</option>{% endfor %}
                </select>
                <label>المبلغ ($):</label><input type="number" name="amount" placeholder="المبلغ" min="1" required>
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
                    {% for u in users_list %}<option value="{{ u[0] }}">{{ u[0] }} (صاحبه: {{ u[5] }} | رصيده: ${{ u[2] }})</option>{% endfor %}
                </select>
                <label>المبلغ ($):</label><input type="number" name="amount" placeholder="المبلغ" min="1" required>
                <button type="submit" class="btn-buy">استرجاع للخزنة</button>
            </form>
        </div>
    </div>
    <div class="panel-box" style="margin-top: 25px;">
        <h3 style="color: #ffd700; margin-top: 0;">📋 سجل كافة الحسابات الثابتة والمسجلة</h3>
        <table>
            <tr><th>اسم المستخدم</th><th>كلمة المرور</th><th>صاحب الحساب</th><th>نوع الحساب</th><th>الرصيد الحالي</th><th>المُنشئ</th></tr>
            {% for u in users_list %}
            <tr>
                <td><b>{{ u[0] }}</b></td><td style="color: #38bdf8; font-family: monospace;">{{ u[1] }}</td>
                <td style="color: #ffd700; font-weight: bold;">{{ u[5] }}</td>
                <td>{{ u[3] }}</td><td style="color: #34d399; font-weight: bold;">${{ u[2] }}</td><td>{{ u[4] }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
    <script>
        function installApp() { window.location.href = '/download'; }
    </script>
</body>
</html>
"""

ADMIN_GAMES_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة تحكم الألعاب - امبراطورية الأرقام</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; padding: 20px; }
        .admin-header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 12px; border: 2px solid #ffd700; margin-bottom: 25px; }
        .download-btn { background: #3b82f6; color: white; padding: 6px 12px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 13px; cursor: pointer; border: none; }
        .back-btn { background: #3b82f6; color: white; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold; }
        .games-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-top: 30px; }
        @media(max-width:900px){ .games-grid { grid-template-columns: repeat(2, 1fr); } }
        .game-ctrl-card { background: #1f1f1f; border: 2px solid #ffd700; padding: 25px; border-radius: 14px; text-align: center; }
        .game-title { color: #ffd700; font-size: 16px; font-weight: bold; margin-bottom: 15px; }
        .ctrl-btn { background: #22c55e; color: white; padding: 10px 20px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; width: 100%; text-decoration: none; display: inline-block; box-sizing: border-box; }
        input[type="number"] { width: 100%; padding: 10px; margin: 10px 0; border-radius: 6px; background: #252525; color: white; border: 1px solid #ffd700; text-align: center; font-size: 16px; box-sizing: border-box; }
    </style>
</head>
<body>
    <div class="admin-header">
        <h2 style="color: #ffd700; margin: 0;">👑 لوحة تحكم الألعاب</h2>
        <div style="display: flex; gap: 15px; align-items: center;">
            <button id="installAppBtn" class="download-btn" onclick="installApp()">📥 تثبيت التطبيق</button>
            <a href="/dashboard" class="back-btn">⬅️ الرئيسية</a>
        </div>
    </div>
    {% if msg %}<div style="background: #065f46; color: #34d399; padding: 12px; border-radius: 8px; margin-bottom: 20px; text-align: center; font-weight: bold;">{{ msg }}</div>{% endif %}
    <div class="games-grid">
        <div class="game-ctrl-card" style="border: 3px solid #34d399;">
            <div class="game-title">1. الرقم الحنون 🏆</div>
            <form method="POST">
                <input type="number" name="forced_winning_number" value="{% if forced_val > 0 %}{{ forced_val }}{% endif %}" placeholder="رقم من 1 إلى 50" min="1" max="50">
                <button type="submit" class="ctrl-btn" style="background: #34d399; color: black; margin-top: 5px;">حفظ الرقم الفائز</button>
            </form>
            <a href="/game_golden_number" class="ctrl-btn" style="background: #3b82f6; margin-top: 10px;">فتح نافذة السحب</a>
        </div>
        <div class="game-ctrl-card" style="border: 3px solid #ffd700;">
            <div class="game-title">6. الرقم الحنون الفاخر 🎁</div>
            <form method="POST">
                <input type="number" name="forced_luxury_number" value="{% if forced_lux > 0 %}{{ forced_lux }}{% endif %}" placeholder="صندوق من 1 إلى 5" min="1" max="5">
                <button type="submit" class="ctrl-btn" style="background: #ffd700; color: black; margin-top: 5px;">حفظ الصندوق الفائز</button>
            </form>
            <a href="/game_golden_boxes_new" class="ctrl-btn" style="background: #3b82f6; margin-top: 10px;">فتح نافذة السحب</a>
        </div>
    </div>
    <script>
        function installApp() { window.location.href = '/download'; }
    </script>
</body>
</html>
"""

ADMIN_ACCOUNTING_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>برنامج المحاسبة - امبراطورية الأرقام</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; padding: 20px; }
        .admin-header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 12px; border: 2px solid #ffd700; margin-bottom: 25px; }
        .download-btn { background: #3b82f6; color: white; padding: 6px 12px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 13px; cursor: pointer; border: none; }
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
        <h2 style="color: #ffd700; margin: 0;">📊 برنامج المحاسبة والشؤون المالية</h2>
        <div style="display: flex; gap: 15px; align-items: center;">
            <button id="installAppBtn" class="download-btn" onclick="installApp()">📥 تثبيت التطبيق</button>
            <a href="/dashboard" class="back-btn">⬅️ الرئيسية</a>
        </div>
    </div>
    <div class="stats-grid">
        <div class="stat-card">
            <div style="color: #94a3b8;">إجمالي المبيعات (الواردات + كافة رهانات الألعاب)</div>
            <div class="stat-val" style="color: #22c55e;">${{ total_sales }}</div>
        </div>
        <div class="stat-card">
            <div style="color: #94a3b8;">إجمالي الجوائز (الصادرات)</div>
            <div class="stat-val" style="color: #ef4444;">${{ total_payouts }}</div>
        </div>
        <div class="stat-card">
            <div style="color: #94a3b8;">رصيد الخزنة الأساسية</div>
            <div class="stat-val" style="color: #38bdf8;">${{ vault_balance }}</div>
        </div>
        <div class="stat-card" style="border: 2px solid #ffd700; background: linear-gradient(135deg, #252010, #161616);">
            <div style="color: #ffd700; font-weight: bold;">صافي الأرباح</div>
            <div class="stat-val" style="color: #ffd700;">${{ net_profits }}</div>
        </div>
    </div>
    <div class="panel-box">
        <h3 style="color: #ffd700; margin-top: 0;">📋 سجل العمليات المالية والواردات والصادرات</h3>
        <table>
            <tr><th>نوع العملية</th><th>المسؤول</th><th>الهدف</th><th>المبلغ ($)</th><th>التوقيت</th></tr>
            {% for log in logs %}
            <tr>
                <td><b>{{ log[0] }}</b></td><td style="color: #ffd700;">{{ log[1] }}</td><td>{{ log[2] }}</td>
                <td style="color: #34d399; font-weight: bold;">${{ log[3] }}</td><td>{{ log[4] }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
    <script>
        function installApp() { window.location.href = '/download'; }
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
