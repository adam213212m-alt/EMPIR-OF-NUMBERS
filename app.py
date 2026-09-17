from flask import Flask, render_template_string, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os
import random

app = Flask(__name__)
app.secret_key = 'empire_secret_key_2026'

# تحديد مسار قاعدة البيانات بدقة لضمان الحفاظ على حسابات وأرصدة اللاعبين
if os.path.exists('/data'):
    db_path = '/data/empire_numbers.db'
else:
    db_path = os.path.join(os.getcwd(), 'instance', 'empire_numbers.db')

os.makedirs(os.path.dirname(db_path), exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# جدول المستخدمين والأرصدة
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    balance = db.Column(db.Float, default=1000.0)

# جدول غرفة الدردشة
class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), default='لاعب ملكي')
    message = db.Column(db.String(500))

with app.app_context():
    db.create_all()

# قالب الواجهة الملكية المتكاملة
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>إمبراطورية الأرقام والجوائز الكبرى - Empire of Numbers</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Cairo', sans-serif; }
        body { background: #0f172a; color: #f8fafc; direction: rtl; padding: 10px; }
        .container { width: 100%; max-width: 1400px; margin: 0 auto; padding: 15px; }
        header { text-align: center; padding: 25px; background: rgba(30, 41, 59, 0.95); border-radius: 15px; margin-bottom: 20px; border: 1px solid #334155; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }
        h1 { color: #fef08a; font-size: 2rem; margin-bottom: 10px; text-shadow: 0 2px 4px rgba(0,0,0,0.3); }
        
        .card { background: rgba(30, 41, 59, 0.85); padding: 20px; border-radius: 15px; margin-bottom: 20px; border: 1px solid #334155; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
        h2 { color: #38bdf8; margin-bottom: 15px; font-size: 1.4rem; border-bottom: 2px solid #334155; padding-bottom: 8px; }
        
        .btn { background: linear-gradient(135deg, #3b82f6, #1d4ed8); color: white; border: none; padding: 12px 24px; border-radius: 10px; font-weight: bold; cursor: pointer; transition: 0.3s; font-size: 1rem; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4); }
        
        input, select { background: #1e293b; color: #fff; padding: 12px; border-radius: 10px; border: 1px solid #475569; font-size: 1rem; width: 100%; margin-bottom: 10px; }
        
        .chat-container { max-height: 250px; overflow-y: auto; background: rgba(15, 23, 42, 0.9); border-radius: 10px; padding: 15px; margin-bottom: 15px; }
        .chat-msg { margin-bottom: 10px; border-bottom: 1px solid #334155; padding-bottom: 6px; }
        
        @media (max-width: 768px) {
            h1 { font-size: 1.5rem; }
            .container { padding: 5px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>👑 إمبراطورية الأرقام والجوائز الكبرى</h1>
            <p>منصة الألعاب الملكية والمسابقات التفاعلية</p>
        </header>

        <!-- لوحة التحكم وحساب اللاعب -->
        <div class="card">
            <h2>👤 حساب اللاعب</h2>
            <form method="POST" action="/login" style="display: flex; gap: 10px; flex-wrap: wrap;">
                <input type="text" name="username" placeholder="أدخل اسم اللاعب أو المعرف..." required style="flex: 1;">
                <button type="submit" class="btn" style="background: #10b981;">تسجيل الدخول / إنشاء حساب</button>
            </form>
            {% if current_user %}
                <div style="margin-top: 15px; padding: 10px; background: rgba(16, 185, 129, 0.2); border: 1px solid #10b981; border-radius: 8px;">
                    أهلاً بك يا <strong>{{ current_user.username }}</strong> | رصيدك الحالي: <span style="color: #fbbf24; font-weight: bold; font-size: 1.2rem;">{{ current_user.balance }}</span> نقطة
                </div>
            {% endif %}
        </div>

        <!-- ألعاب المنصة -->
        <div class="card">
            <h2>🎲 ألعاب الإمبراطورية</h2>
            <p style="margin-bottom: 15px; color: #94a3b8;">اختر لعبتك المفضلة وابدأ التحدي الآن!</p>
            <div style="display: flex; gap: 15px; flex-wrap: wrap;">
                <button class="btn" onclick="alert('لعبة الروليت الملكية جاهزة للعب!')">لعبة الروليت</button>
                <button class="btn" onclick="alert('مسابقة الليرة الذهبية مفعلة!')">الليرة الذهبية</button>
            </div>
        </div>

        <!-- غرفة الدردشة -->
        <div class="card">
            <h2>💬 غرفة الدردشة الحية</h2>
            <div class="chat-container">
                {% for msg in chats %}
                    <div class="chat-msg"><strong>{{ msg.username }}:</strong> {{ msg.message }}</div>
                {% endfor %}
            </div>
            <form method="POST" action="/chat">
                <input type="text" name="message" placeholder="اكتب رسالتك في الدردشة..." required autocomplete="off">
                <button type="submit" class="btn">إرسال الرسالة</button>
            </form>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    username = session.get('username')
    current_user = User.query.filter_by(username=username).first() if username else None
    chats = Chat.query.all()
    return render_template_string(HTML_TEMPLATE, current_user=current_user, chats=chats)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    if username:
        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username, balance=1000.0)
            db.session.add(user)
            db.session.commit()
        session['username'] = user.username
    return redirect(url_for('index'))

@app.route('/chat', methods=['POST'])
def chat():
    username = session.get('username', 'زائر ملكي')
    message = request.form.get('message')
    if message:
        new_chat = Chat(username=username, message=message)
        db.session.add(new_chat)
        db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)