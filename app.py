from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify, json, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import random
import time
import os

app = Flask(__name__)
app.secret_key = 'lira_empire_secure_2026_key'

# إعداد قاعدة البيانات عبر SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///lira_enterprise.db')
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

# نموذج حالة لعبة "اكشف واربح" المشتركة بين جميع الحسابات
class ScratchGameState(db.Model):
    __tablename__ = 'scratch_game_state'
    id = db.Column(db.Integer, primary_key=True)
    current_index = db.Column(db.Integer, default=0)
    pool_json = db.Column(db.Text, nullable=False)


# إنشاء الجداول وإدخال حساب الآدمن الافتراضي عند التشغيل الأول
with app.app_context():
    db.create_all()
    
    if not SystemVault.query.get(1):
        vault = SystemVault(id=1, vault_balance=1000000.0)
        db.session.add(vault)
    
    if not GameDrawState.query.get(1):
        draw_state = GameDrawState(id=1, winning_number=0, status='idle', draw_end_time=0, forced_winning_number=0)
        db.session.add(draw_state)
        
    if not BalloonState.query.get(1):
        balloon_state = BalloonState(id=1, attempts_since_last_win=0, sequence_index=0)
        db.session.add(balloon_state)

    # تهيئة حوض لعبة اكشف واربح (46 محاولة: 1 فائز بـ 20$, 20 فائزين بـ 0.5$, 25 خاسر)
    if not ScratchGameState.query.get(1):
        initial_pool = [3] + [2]*20 + [0]*25
        random.shuffle(initial_pool)
        scratch_state = ScratchGameState(id=1, current_index=0, pool_json=json.dumps(initial_pool))
        db.session.add(scratch_state)
        
    admin = User.query.filter_by(username='admin1').first()
    if not admin:
        admin = User(username='admin1', password='admin123', balance=50000.0, role='admin', created_by='system')
        vault_record = SystemVault.query.get(1)
        if vault_record:
            vault_record.vault_balance -= 50000.0
        db.session.add(admin)
        
    db.session.commit()


# --- المسارات (Routes) والمنطق البرمجي ---

@app.route('/manifest.json')
def manifest():
    manifest_data = {
        "name": "ليرة - المنصة التفاعلية الكبرى",
        "short_name": "ليرة",
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
        return send_from_directory('static', 'lira.apk', as_attachment=True)
    except Exception:
        return redirect("https://wa.me/96176030208?text=اريد%20تحميل%20تطبيق%20ليرة%20الرسمي")

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
    return render_template_string(DASHBOARD_PAGE, username=user.username, role=user.role, balance=user.balance)

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

@app.route('/game_golden_number', methods=['GET', 'POST'])
def game_golden_number():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    user = User.query.filter_by(username=username).first()
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
                log = FinancialLog(action_type='جائزة الرقم الذهبي', admin_name='admin1', target_user=winner_user.username, amount=75.0, log_time=time.strftime('%Y-%m-%d %H:%M'))
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

    return render_template_string(GAME_GOLDEN_PAGE, username=username, role=user.role, balance=user.balance, 
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

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'play_balloon':
            cost = 1.0
            if user.balance >= cost:
                user.balance -= cost
                vault.vault_balance += cost
                
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

    return render_template_string(GAME_BALLOON_PAGE, username=username, balance=user.balance, msg=msg, win_result=win_result, is_popped=is_popped)

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

    return render_template_string(GAME_ROULETTE_PAGE, username=username, balance=user.balance, msg=msg, last_win_data=last_win_data, last_bets_json=last_bets_json)

# --- لعبة عجلة الأرقام (الأيقونة الرابعة) ---
@app.route('/game_number_wheel', methods=['GET', 'POST'])
def game_number_wheel():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    user = User.query.filter_by(username=username).first()
    vault = SystemVault.query.get(1)
    
    msg = None
    result_data = None
    cost = 1.0

    if request.method == 'POST':
        if user.balance >= cost:
            user.balance -= cost
            vault.vault_balance += cost

            outcomes = [
                {'name': 'خسارة', 'multiplier': '0x', 'payout': 0.0, 'weight': 51, 'color': '#ef4444'},
                {'name': 'استرجاع نصفي', 'multiplier': '0.5x', 'payout': 0.5, 'weight': 18, 'color': '#f97316'},
                {'name': 'استرجاع كامل', 'multiplier': '1x', 'payout': 1.0, 'weight': 14, 'color': '#3b82f6'},
                {'name': 'مضاعف صغير', 'multiplier': '2x', 'payout': 2.0, 'weight': 11, 'color': '#a855f7'},
                {'name': 'مضاعف مميز', 'multiplier': '4x', 'payout': 4.0, 'weight': 5, 'color': '#22c55e'},
                {'name': 'الجائزة الكبرى', 'multiplier': '10x', 'payout': 10.0, 'weight': 1, 'color': '#ffd700'}
            ]

            weights = [o['weight'] for o in outcomes]
            chosen_outcome = random.choices(outcomes, weights=weights, k=1)[0]
            
            payout = chosen_outcome['payout']
            if payout > 0:
                user.balance += payout
                vault.vault_balance -= payout
                log = FinancialLog(action_type='جائزة عجلة الأرقام', admin_name='system', target_user=username, amount=payout, log_time=time.strftime('%Y-%m-%d %H:%M'))
                db.session.add(log)

            db.session.commit()
            result_data = chosen_outcome
            if payout > 0:
                msg = f"🎉 مبروك! استقرت العجلة على ({chosen_outcome['name']} - مضاعف {chosen_outcome['multiplier']}) وتمت إضافة الأرباح بقيمة ${payout} إلى رصيدك!"
            else:
                msg = "💥 حظ أوفر في المرة القادمة، استقرت العجلة على منطقة الخسارة."
        else:
            msg = "رصيدك غير كافٍ للبدء (تكلفة التجربة 1$)!"

    return render_template_string(GAME_NUMBER_WHEEL_PAGE, username=username, balance=user.balance, msg=msg, result_data=result_data)

# --- لعبة اكشف واربح الجديدة (نظام الحوض المشترك المغلق لكل الحسابات - 46 محاولة) ---
@app.route('/game_scratch', methods=['GET', 'POST'])
def game_scratch():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    user = User.query.filter_by(username=username).first()
    vault = SystemVault.query.get(1)
    scratch_state = ScratchGameState.query.get(1)
    
    msg = None
    revealed_numbers = None
    cost = 1.0  # تكلفة المحاولة 1 دولار

    if request.method == 'POST':
        if user.balance >= cost:
            user.balance -= cost
            vault.vault_balance += cost

            # سحب النتيجة من الحوض المشترك المغلق (46 محاولة)
            pool = json.loads(scratch_state.pool_json)
            if scratch_state.current_index >= len(pool):
                pool = [3] + [2]*20 + [0]*25
                random.shuffle(pool)
                scratch_state.current_index = 0

            match_type = pool[scratch_state.current_index]
            scratch_state.current_index += 1
            db.session.commit()

            # توليد الأرقام التي تظهر للمتسابقة بناءً على حالة المطابقة في الحوض
            if match_type == 3:
                # مطابقة 3 أرقام -> جائزة 20$
                num = random.randint(1, 9)
                revealed_numbers = [num, num, num]
                payout = 20.0
                msg = "🏆 مبروك! طابقت الأرقام الثلاثة وفزت بالجائزة الكبرى (20$) وتمت إضافتها إلى رصيدك!"
            elif match_type == 2:
                # مطابقة رقمين -> نصف قيمة الرهان (0.5$)
                num = random.randint(1, 9)
                other_num = random.choice([x for x in range(1, 10) if x != num])
                revealed_numbers = [num, num, other_num]
                random.shuffle(revealed_numbers)
                payout = 0.5
                msg = "✨ ممتاز! طابقت رقمين وفزت بنصف قيمة الرهان (0.5$) وتمت إضافتها إلى رصيدك!"
            else:
                # خسارة (أرقام غير متطابقة)
                revealed_numbers = random.sample(range(1, 10), 3)
                payout = 0.0
                msg = "💥 حظ أوفر في المرة القادمة، لم تتطابق الأرقام."

            if payout > 0:
                user.balance += payout
                vault.vault_balance -= payout
                log = FinancialLog(action_type='جائزة اكشف واربح', admin_name='system', target_user=username, amount=payout, log_time=time.strftime('%Y-%m-%d %H:%M'))
                db.session.add(log)

            db.session.commit()
        else:
            msg = "رصيدك غير كافٍ للبدء (تكلفة المحاولة 1$)!"

    return render_template_string(GAME_SCRATCH_PAGE, username=username, balance=user.balance, msg=msg, revealed_numbers=revealed_numbers)

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
            existing = User.query.filter_by(username=new_u).first()
            if not existing:
                new_user = User(username=new_u, password=new_p, balance=0.0, role='player', created_by='admin1')
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
    users_data = [(u.username, u.password, u.balance, u.role, u.created_by) for u in users_list]

    return render_template_string(ADMIN_CUSTOMERS_PAGE, vault_balance=vault.vault_balance, users_list=users_data, msg=msg)

@app.route('/admin_games', methods=['GET', 'POST'])
def admin_games():
    if 'username' not in session or session.get('username') != 'admin1':
        return redirect(url_for('dashboard'))
    
    draw_state = GameDrawState.query.get(1)
    msg = None

    if request.method == 'POST':
        forced_num = request.form.get('forced_winning_number', '').strip()
        f_val = int(forced_num) if forced_num.isdigit() else 0
        draw_state.forced_winning_number = f_val
        db.session.commit()
        msg = f"تم تحديث الرقم المسبق للسحب إلى: {f_val if f_val > 0 else 'عشوائي'}"

    return render_template_string(ADMIN_GAMES_PAGE, forced_val=draw_state.forced_winning_number, msg=msg)

@app.route('/admin_accounting')
def admin_accounting():
    if 'username' not in session or session.get('username') != 'admin1':
        return redirect(url_for('dashboard'))
    
    vault = SystemVault.query.get(1)
    logs_records = FinancialLog.query.order_by(FinancialLog.id.desc()).all()
    logs = [(l.action_type, l.admin_name, l.target_user, l.amount, l.log_time) for l in logs_records]
    
    sales_res = db.session.query(db.func.sum(FinancialLog.amount)).filter_by(action_type='بيع عملات للزبون').scalar() or 0.0
    payout_res1 = db.session.query(db.func.sum(FinancialLog.amount)).filter_by(action_type='جائزة الرقم الذهبي').scalar() or 0.0
    payout_res3 = db.session.query(db.func.sum(FinancialLog.amount)).filter_by(action_type='جائزة روليت الحظ').scalar() or 0.0
    payout_res4 = db.session.query(db.func.sum(FinancialLog.amount)).filter_by(action_type='جائزة تحدي البالون').scalar() or 0.0
    payout_res5 = db.session.query(db.func.sum(FinancialLog.amount)).filter_by(action_type='جائزة عجلة الأرقام').scalar() or 0.0
    payout_res6 = db.session.query(db.func.sum(FinancialLog.amount)).filter_by(action_type='جائزة اكشف واربح').scalar() or 0.0

    total_sales = sales_res
    total_payouts = payout_res1 + payout_res3 + payout_res4 + payout_res5 + payout_res6
    net_profits = total_sales - total_payouts

    return render_template_string(ADMIN_ACCOUNTING_PAGE, vault_balance=vault.vault_balance, logs=logs, total_sales=total_sales, total_payouts=total_payouts, net_profits=net_profits)


# --- قوالب HTML ---

LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تسجيل الدخول - ليرة Lira</title><link rel="manifest" href="/manifest.json">
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
        <div class="logo-title">👑 ليرة</div><div class="logo-sub">منصة ليرة الألعاب التفاعلية</div>
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
    <title>ليرة - لوحة التحكم الرئيسية</title><link rel="manifest" href="/manifest.json">
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; margin: 0; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 14px; box-shadow: 0 4px 15px rgba(0,0,0,0.6); flex-wrap: wrap; gap: 12px; border-bottom: 3px solid #ffd700; }
        .logo-area { display: flex; align-items: center; gap: 15px; flex-wrap: wrap; }
        .logo-badge { background: linear-gradient(135deg, #ffd700, #b8860b); color: #000; width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 26px; font-weight: bold; }
        .logo-area h1 { margin: 0; color: #ffd700; font-size: 26px; font-weight: bold; }
        .user-creds { background: #1f1f1f; padding: 8px 14px; border-radius: 8px; font-size: 14px; color: #cbd5e1; border: 1px dashed #ffd700; }
        .balance-badge { background: #065f46; color: #34d399; padding: 8px 15px; border-radius: 8px; font-weight: bold; font-size: 18px; border: 1px solid #10b981; }
        .nav-buttons { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
        .download-btn { background: #3b82f6; color: white; padding: 8px 14px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 14px; border: 1px solid #60a5fa; cursor: pointer; }
        .whatsapp-btn { background: #25d366; color: white; padding: 8px 15px; text-decoration: none; border-radius: 8px; font-weight: bold; }
        .logout-btn { background: #ef4444; color: white; padding: 8px 15px; text-decoration: none; border-radius: 8px; font-weight: bold; border: none; }
        .admin-link { background: #ffd700; color: black; padding: 8px 12px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 13px; }
        .icons-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 35px; }
        @media (max-width: 900px) { .icons-grid { grid-template-columns: repeat(2, 1fr); } }
        @media (max-width: 500px) { .icons-grid { grid-template-columns: 1fr; } }
        .icon-card { background: linear-gradient(145deg, #1f1f1f, #121212); border: 2px solid #b8860b; border-radius: 16px; padding: 30px; text-align: center; cursor: pointer; transition: all 0.3s ease; box-shadow: 0 4px 20px rgba(0,0,0,0.6); display: flex; flex-direction: column; align-items: center; justify-content: center; text-decoration: none; aspect-ratio: 1; }
        .icon-card:hover { border-color: #ffd700; transform: translateY(-5px); box-shadow: 0 8px 30px rgba(255,215,0,0.4); }
        .icon-logo { font-size: 60px; margin-bottom: 15px; }
        .icon-title { color: #ffd700; font-size: 18px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo-area">
            <div class="logo-badge">👑</div><h1>ليرة | Lira</h1>
            <div class="user-creds">👤 <b>{{ username }}</b></div>
            <div class="balance-badge">الرصيد: <span>${{ balance }}</span></div>
        </div>
        <div class="nav-buttons">
            <button id="installAppBtn" class="download-btn" onclick="installApp()">📥 تثبيت التطبيق</button>
            <a class="whatsapp-btn" href="https://wa.me/96176030208?text=اريد%20شحن%20رصيد" target="_blank">💬 شحن رصيد</a>
            {% if username == 'admin1' %}
                <a href="/admin_customers" class="admin-link">👥 إدارة الزبائن والخزنة</a>
                <a href="/admin_games" class="admin-link">🎮 لوحة الألعاب</a>
                <a href="/admin_accounting" class="admin-link">📊 المحاسبة</a>
            {% endif %}
            <a href="/logout" class="logout-btn">🚪 خروج</a>
        </div>
    </div>
    <div class="icons-grid">
        <a href="/game_golden_number" class="icon-card"><div class="icon-logo">🏆</div><div class="icon-title">الرقم الذهبي</div></a>
        <a href="/game_roulette" class="icon-card"><div class="icon-logo">🎰</div><div class="icon-title">روليت الحظ</div></a>
        <a href="/game_balloon_pop" class="icon-card"><div class="icon-logo">🎈</div><div class="icon-title">التحدي السريع (البالون)</div></a>
        <a href="/game_number_wheel" class="icon-card"><div class="icon-logo">🎡</div><div class="icon-title">عجلة الأرقام</div></a>
        <!-- الأيقونة الخامسة: لعبة اكشف واربح -->
        <a href="/game_scratch" class="icon-card"><div class="icon-logo">🎟️</div><div class="icon-title">اكشف واربح</div></a>
        <div class="icon-card" onclick="alert('قريباً في التعديل القادم')"><div class="icon-logo">🎁</div><div class="icon-title">الصناديق الذهبية</div></div>
        <div class="icon-card" onclick="alert('اللعبة السابعة قيد التفعيل')"><div class="icon-logo">🔢</div><div class="icon-title">تحدي الأرقام</div></div>
        <div class="icon-card" onclick="alert('اللعبة الثامنة قيد التفعيل')"><div class="icon-logo">🃏</div><div class="icon-title">البوكر الملكي</div></div>
        <div class="icon-card" onclick="alert('اللعبة التاسعة قيد التفعيل')"><div class="icon-logo">💎</div><div class="icon-title">المجوهرات الكبرى</div></div>
    </div>
    <script>
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
    <title>التحدي السريع (البالون) - ليرة</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; margin: 0; padding: 20px; text-align: center; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 12px; border-bottom: 2px solid #ffd700; flex-wrap: wrap; gap: 10px; }
        .download-btn { background: #3b82f6; color: white; padding: 6px 12px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 13px; cursor: pointer; border: none; }
        .game-box { background: linear-gradient(135deg, #1f1a0f, #0d0d0d); border: 4px solid #ffd700; padding: 30px; border-radius: 20px; max-width: 450px; margin: 30px auto; box-shadow: 0 0 35px rgba(255,215,0,0.3); }
        .balloon { width: 120px; height: 150px; background: radial-gradient(circle at 30% 30%, #ff5252, #c62828); border-radius: 50% 50% 50% 50% / 40% 40% 60% 60%; margin: 20px auto; position: relative; transition: 0.3s; }
        .balloon.popped { background: transparent !important; box-shadow: none !important; transform: scale(1.6); }
        .pump-btn { background: linear-gradient(135deg, #ffd700, #b8860b); color: #000; font-size: 20px; font-weight: bold; padding: 15px 35px; border: none; border-radius: 12px; cursor: pointer; margin-top: 15px; width: 100%; }
        .back-btn { background: #3b82f6; color: white; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h2 style="color: #ffd700; margin: 0;">🎈 التحدي السريع (البالون)</h2>
        <div style="display: flex; gap: 15px; align-items: center;">
            <button id="installAppBtn" class="download-btn" onclick="installApp()">📥 تثبيت التطبيق</button>
            <div style="color: #34d399; font-weight: bold; font-size: 18px;">الرصيد: ${{ balance }}</div>
            <a href="/dashboard" class="back-btn">⬅️ لوحة التحكم</a>
        </div>
    </div>
    {% if msg %}<div style="background: #7f1d1d; color: #fca5a5; padding: 10px; border-radius: 6px; margin-top: 15px;">{{ msg }}</div>{% endif %}
    <div class="game-box">
        <h3 style="color: #ffd700; margin-top: 0;">اضغط لضخ الهواء في البالون (التكلفة: 1$)</h3>
        <div class="balloon {% if is_popped %}popped{% endif %}" id="myBalloon">
            {% if is_popped %}<div style="font-size: 45px; position: absolute; top: 40px; left: 35px;">💥</div>{% endif %}
        </div>
        <form method="POST">
            <input type="hidden" name="action" value="play_balloon">
            <button type="submit" class="pump-btn">💨 اضغط لضخ الهواء</button>
        </form>
        {% if win_result %}
        <div style="margin-top: 20px; font-size: 18px; font-weight: bold; padding: 12px; border-radius: 8px; background: {% if 'فزت' in win_result %}#065f46{% else %}#7f1d1d{% endif %}; color: white;">
            {{ win_result }}
        </div>
        {% endif %}
    </div>
    <script>
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
    <title>روليت الحظ - ليرة</title>
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
        <h2 style="color: #ffd700; margin: 0;">🎰 روليت الحظ (ليرة)</h2>
        <div style="display: flex; gap: 15px; align-items: center;">
            <button id="installAppBtn" class="download-btn" onclick="installApp()">📥 تثبيت التطبيق</button>
            <div style="color: #34d399; font-weight: bold; font-size: 16px;">الرصيد: ${{ balance }}</div>
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
    <title>عجلة الأرقام - ليرة</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; margin: 0; padding: 20px; text-align: center; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 12px; border-bottom: 2px solid #ffd700; flex-wrap: wrap; gap: 10px; }
        .download-btn { background: #3b82f6; color: white; padding: 6px 12px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 13px; cursor: pointer; border: none; }
        .game-box { background: linear-gradient(135deg, #1f1a0f, #0d0d0d); border: 4px solid #ffd700; padding: 35px; border-radius: 24px; max-width: 500px; margin: 30px auto; box-shadow: 0 0 40px rgba(255,215,0,0.3); }
        .wheel-circle { width: 180px; height: 180px; background: radial-gradient(circle, #3d2c00 0%, #1a1200 100%); border: 6px solid #ffd700; border-radius: 50%; margin: 25px auto; display: flex; align-items: center; justify-content: center; font-size: 45px; font-weight: bold; color: #ffd700; box-shadow: 0 0 25px rgba(255,215,0,0.5); transition: transform 1.5s ease-in-out; }
        .spin-action-btn { background: linear-gradient(135deg, #ffd700, #b8860b); color: #000; font-size: 20px; font-weight: bold; padding: 15px 40px; border: none; border-radius: 14px; cursor: pointer; margin-top: 15px; width: 100%; box-shadow: 0 4px 20px rgba(255,215,0,0.4); }
        .spin-action-btn:hover { transform: scale(1.02); }
        .back-btn { background: #3b82f6; color: white; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h2 style="color: #ffd700; margin: 0;">🎡 عجلة الأرقام الكبرى</h2>
        <div style="display: flex; gap: 15px; align-items: center;">
            <button id="installAppBtn" class="download-btn" onclick="installApp()">📥 تثبيت التطبيق</button>
            <div style="color: #34d399; font-weight: bold; font-size: 18px;">الرصيد: ${{ balance }}</div>
            <a href="/dashboard" class="back-btn">⬅️ لوحة التحكم</a>
        </div>
    </div>
    {% if msg %}<div style="background: {% if result_data and result_data.payout > 0 %}#065f46{% else %}#7f1d1d{% endif %}; color: white; padding: 12px; border-radius: 8px; margin-top: 15px; text-align: center; font-weight: bold; max-width: 500px; margin-left: auto; margin-right: auto;">{{ msg }}</div>{% endif %}
    <div class="game-box">
        <h3 style="color: #ffd700; margin-top: 0;">أدر العجلة واربح مضاعفات كبرى! (تكلفة اللعبة: 1$)</h3>
        <div class="wheel-circle" id="wheelDisplay">
            {% if result_data %}{{ result_data.multiplier }}{% else %}🎡{% endif %}
        </div>
        <p style="color: #cbd5e1; font-size: 14px; margin-bottom: 20px;">
            {% if result_data %}النتيجة: <b style="color: {{ result_data.color }};">{{ result_data.name }}</b>{% else %}اضغط زر الدوران أدناه لاختبار حظك بقيمة 1${% endif %}
        </p>
        <form method="POST" onsubmit="spinWheelAnimation(event)">
            <button type="submit" class="spin-action-btn" id="spinBtn">🎯 أدر العجلة الآن (1$)</button>
        </form>
    </div>
    <script>
        function spinWheelAnimation(e) {
            let wheel = document.getElementById('wheelDisplay');
            let btn = document.getElementById('spinBtn');
            btn.disabled = true;
            btn.innerText = "⏳ جاري تدوير العجلة...";
            wheel.style.transform = "rotate(720deg) scale(1.1)";
        }
        function installApp() { window.location.href = '/download'; }
    </script>
</body>
</html>
"""

# قالب واجهة لعبة "اكشف واربح" الجديدة
GAME_SCRATCH_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>اكشف واربح - ليرة</title>
    <style>
        body { font-family: Tahoma, sans-serif; background-color: #0b0f19; color: #f8fafc; margin: 0; padding: 20px; text-align: center; }
        .header { display: flex; justify-content: space-between; align-items: center; background: #121212; padding: 15px 25px; border-radius: 12px; border-bottom: 2px solid #ffd700; flex-wrap: wrap; gap: 10px; }
        .download-btn { background: #3b82f6; color: white; padding: 6px 12px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 13px; cursor: pointer; border: none; }
        .game-box { background: linear-gradient(135deg, #1f1a0f, #0d0d0d); border: 4px solid #ffd700; padding: 35px; border-radius: 24px; max-width: 500px; margin: 30px auto; box-shadow: 0 0 40px rgba(255,215,0,0.3); }
        .scratch-grid { display: flex; justify-content: center; gap: 15px; margin: 25px 0; }
        .scratch-cell { width: 85px; height: 95px; background: linear-gradient(145deg, #b8860b, #ffd700); border: 3px solid #fff; border-radius: 14px; display: flex; align-items: center; justify-content: center; font-size: 38px; font-weight: bold; color: #000; box-shadow: 0 5px 15px rgba(0,0,0,0.5); }
        .play-action-btn { background: linear-gradient(135deg, #22c55e, #15803d); color: white; font-size: 20px; font-weight: bold; padding: 15px 40px; border: none; border-radius: 14px; cursor: pointer; margin-top: 15px; width: 100%; box-shadow: 0 4px 20px rgba(34,197,94,0.4); }
        .play-action-btn:hover { transform: scale(1.02); }
        .back-btn { background: #3b82f6; color: white; text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h2 style="color: #ffd700; margin: 0;">🎟️ اكشف واربح (مطابقة الأرقام)</h2>
        <div style="display: flex; gap: 15px; align-items: center;">
            <button id="installAppBtn" class="download-btn" onclick="installApp()">📥 تثبيت التطبيق</button>
            <div style="color: #34d399; font-weight: bold; font-size: 18px;">الرصيد: ${{ balance }}</div>
            <a href="/dashboard" class="back-btn">⬅️ لوحة التحكم</a>
        </div>
    </div>
    {% if msg %}<div style="background: {% if 'مبروك' in msg or 'ممتاز' in msg %}#065f46{% else %}#7f1d1d{% endif %}; color: white; padding: 12px; border-radius: 8px; margin-top: 15px; text-align: center; font-weight: bold; max-width: 500px; margin-left: auto; margin-right: auto;">{{ msg }}</div>{% endif %}
    <div class="game-box">
        <h3 style="color: #ffd700; margin-top: 0;">اكشف الأرقام الثلاثة وطابقها لتربح! (تكلفة المحاولة: 1$)</h3>
        <p style="color: #94a3b8; font-size: 13px; margin-bottom: 20px;">طابق رقمين واربح نصف الرهان (0.5$) | طابق 3 أرقام واربح الكبرى (20$)</p>
        <div class="scratch-grid">
            <div class="scratch-cell">{% if revealed_numbers %}{{ revealed_numbers[0] }}{% else %}?{% endif %}</div>
            <div class="scratch-cell">{% if revealed_numbers %}{{ revealed_numbers[1] }}{% else %}?{% endif %}</div>
            <div class="scratch-cell">{% if revealed_numbers %}{{ revealed_numbers[2] }}{% else %}?{% endif %}</div>
        </div>
        <form method="POST">
            <button type="submit" class="play-action-btn" id="playBtn">🎟️ اكشف الآن (1$)</button>
        </form>
    </div>
    <script>
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
    <title>الرقم الذهبي - ليرة</title>
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
        <h2 style="color: #ffd700; margin: 0;">🏆 الرقم الذهبي (ليرة)</h2>
        <div style="display: flex; gap: 15px; align-items: center;">
            <button id="installAppBtn" class="download-btn" onclick="installApp()">📥 تثبيت التطبيق</button>
            <div style="color: #34d399; font-weight: bold; font-size: 18px;">الرصيد: ${{ balance }}</div>
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
    <title>إدارة الزبائن والخزنة - ليرة</title>
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
        <h2 style="color: #ffd700; margin: 0;">👑 لوحة تحكم المؤسس - ليرة</h2>
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
                    {% for u in users_list %}<option value="{{ u[0] }}">{{ u[0] }} (رصيده: ${{ u[2] }})</option>{% endfor %}
                </select>
                <label>المبلغ ($):</label><input type="number" name="amount" placeholder="المبلغ" min="1" required>
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
                <td><b>{{ u[0] }}</b></td><td style="color: #38bdf8; font-family: monospace;">{{ u[1] }}</td>
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
    <title>لوحة تحكم الألعاب - ليرة</title>
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
            <div class="game-title">1. الرقم الذهبي 🏆</div>
            <form method="POST">
                <input type="number" name="forced_winning_number" value="{% if forced_val > 0 %}{{ forced_val }}{% endif %}" placeholder="رقم من 1 إلى 50" min="1" max="50"><button type="submit" class="ctrl-btn" style="background: #34d399; color: black; margin-top: 5px;">حفظ الرقم الفائز</button>
            </form>
            <a href="/game_golden_number" class="ctrl-btn" style="background: #3b82f6; margin-top: 10px;">فتح نافذة السحب</a>
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
    <title>برنامج المحاسبة - ليرة</title>
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
        <h2 style="color: #ffd700; margin: 0;">📊 برنامج المحاسبة والشؤون المالية (ليرة)</h2>
        <div style="display: flex; gap: 15px; align-items: center;">
            <button id="installAppBtn" class="download-btn" onclick="installApp()">📥 تثبيت التطبيق</button>
            <a href="/dashboard" class="back-btn">⬅️ الرئيسية</a>
        </div>
    </div>
    <div class="stats-grid">
        <div class="stat-card">
            <div style="color: #94a3b8;">إجمالي المبيعات (الواردات)</div>
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
