from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import sqlite3
import random
import time
import datetime
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
app.secret_key = 'empire_lira_clean_2026'

DB_NAME = 'empire_stable.db'

def get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
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
            cursor.execute("INSERT INTO users (username, password, balance, role, created_by) VALUES (?,?, 100000.0, 'admin', 'system')",
                           (adm, 'admin123'))
            cursor.execute("UPDATE system_vault SET vault_balance = vault_balance - 100000.0 WHERE id=1")

    conn.commit()
    conn.close()

init_db()

# دالة السحب التلقائي الساعة 9 مساء
def auto_draw():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM game_draws WHERE game_name='golden_number'")
    st = cursor.fetchone()[0]
    if st == 'idle':
        winning_num = random.randint(1, 50)
        end_timestamp = time.time() + 15
        cursor.execute("UPDATE game_draws SET winning_number=?, status='drawing', draw_end_timestamp=? WHERE game_name='golden_number'",
                       (winning_num, end_timestamp))
        conn.commit()
        print(f"[AUTO DRAW] تم السحب التلقائي على الرقم: {winning_num}")
    conn.close()

scheduler = BackgroundScheduler(timezone="Asia/Beirut")
scheduler.add_job(func=auto_draw, trigger="cron", hour=21, minute=0)
scheduler.start()

@app.route('/manifest.json')
def manifest():
    manifest_data = '{"name
