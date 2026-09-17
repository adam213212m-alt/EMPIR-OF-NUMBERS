from flask import Flask, render_template_string, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = 'empire_secret_key_2026'

# تحديد مسار قاعدة البيانات بدقة (دعم قرص Render الدائم /data أو المحلي)
if os.path.exists('/data'):
    db_path = '/data/empire_numbers.db'
else:
    db_path = os.path.join(os.getcwd(), 'instance', 'empire_numbers.db')

os.makedirs(os.path.dirname(db_path), exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), default='لاعب ملكي')
    message = db.Column(db.String(500))

with app.app_context():
    db.create_all()

# قالب الصفحة الرئيسية المتجاوب والشامل لجميع الميزات
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>إمبراطورية الأرقام - Empire of Numbers</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Cairo', sans-serif; }
        body { background: #0f172a; color: #f8fafc; direction: rtl; overflow-x: hidden; padding: 10px; }
        .container { width: 100%; max-width: 1400px; margin: 0 auto; padding: 10px; }
        header { text-align: center; padding: 20px; background: rgba(30, 41, 59, 0.9); border-radius: 15px; margin-bottom: 20px; border: 1px solid #334155; }
        h1 { color: #fef08a; font-size: 1.8rem; margin-bottom: 10px; }
        
        /* زر تثبيت التطبيق */
        #install-btn {
            display: none;
            background: linear-gradient(135deg, #f59e0b, #d97706);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 25px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(245, 158, 11, 0.4);
            margin: 15px auto;
            font-size: 1rem;
            transition: 0.3s;
        }
        #install-btn:hover { transform: scale(1.05); }

        /* قسم الروليت والرهان */
        .game-section { background: rgba(30, 41, 59, 0.8); padding: 20px; border-radius: 15px; margin-bottom: 20px; border: 1px solid #334155; text-align: center; }
        .bet-display-box { background: rgba(255, 215, 0, 0.15); border: 2px solid gold; padding: 12px; border-radius: 12px; text-align: center; margin: 15px auto; max-width: 400px; }
        
        /* غرفة الدردشة المتجاوبة */
        .chat-section { background: rgba(30, 41, 59, 0.8); padding: 20px; border-radius: 15px; border: 1px solid #334155; }
        .chat-container { width: 100%; max-height: 250px; overflow-y: auto; background: rgba(15, 23, 42, 0.9); border-radius: 10px; padding: 15px; margin-bottom: 15px; text-align: right; }
        .chat-form { display: flex; gap: 10px; }
        .chat-form input { flex: 1; background: #1e293b; color: #fff; padding: 10px; border-radius: 8px; border: 1px solid #475569; font-size: 1rem; }
        .chat-form button { background: #3b82f6; color: #fff; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-weight: bold; }

        /* توافق الهواتف الذكية والشاشات الكبيرة */
        @media (max-width: 768px) {
            body { padding: 5px; }
            h1 { font-size: 1.4rem !important; }
            button, input { font-size: 0.9rem !important; padding: 8px !important; }
            .chat-form { flex-direction: column; }
            .chat-form button { width: 100%; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>👑 إمبراطورية الأرقام - النسخة الملكية المحدثة</h1>
            <p>منصة الألعاب والمسابقات المتكاملة</p>
            <!-- زر تثبيت البرنامج -->
            <button id="install-btn">📱 تثبيت تطبيق المنصة على هاتفك</button>
        </header>

        <!-- لعبة الروليت وخانة الرهان -->
        <div class="game-section">
            <h2>🎲 لعبة الروليت الملكية</h2>
            <div class="bet-display-box">
                <span style="font-size: 1.1rem; color: #fef08a;">🎯 قيمة الرهان الحالي: </span>
                <span id="current-bet-value" style="font-size: 1.3rem; color: #fbbf24; font-weight: bold;">0</span>
            </div>
            <button onclick="placeBet(100)" style="background: #10b981; color: white; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">رهان تجريبي (100)</button>
        </div>

        <!-- غرفة الدردشة -->
        <div class="chat-section">
            <h2>💬 غرفة الدردشة الحية</h2>
            <div class="chat-container" id="chat-box">
                {% for msg in chats %}
                    <div style="margin-bottom: 8px; border-bottom: 1px solid #334155; padding-bottom: 5px;"><strong>{{ msg.username }}:</strong> {{ msg.message }}</div>
                {% endfor %}
            </div>
            <form method="POST" class="chat-form">
                <input type="text" name="message" placeholder="اكتب رسالتك هنا..." required autocomplete="off">
                <button type="submit">إرسال</button>
            </form>
        </div>
    </div>

    <script>
        // دالة تحديث قيمة الرهان في الروليت
        function placeBet(amount) {
            document.getElementById('current-bet-value').innerText = amount;
        }

        // كود تفعيل زر تثبيت التطبيق تلقائياً
        let deferredPrompt;
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            const installBtn = document.getElementById('install-btn');
            if (installBtn) {
                installBtn.style.display = 'block';
                installBtn.addEventListener('click', () => {
                    deferredPrompt.prompt();
                    deferredPrompt.userChoice.then((choiceResult) => {
                        deferredPrompt = null;
                        installBtn.style.display = 'none';
                    });
                });
            }
        });
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        msg_text = request.form.get('message')
        if msg_text:
            new_chat = Chat(message=msg_text)
            db.session.add(new_chat)
            db.session.commit()
        return redirect(url_for('index'))
    
    chats = Chat.query.all()
    return render_template_string(HTML_TEMPLATE, chats=chats)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
