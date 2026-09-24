import os
from flask import Flask, render_template, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

app = Flask(__name__)

# Récupère l'URL Neon depuis la variable d'environnement ou utilise la clé par défaut
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS brisage (
            id SERIAL PRIMARY KEY,
            pseudo TEXT,
            item_name TEXT,
            category TEXT,
            break_type TEXT,
            craft_cost INTEGER,
            coeff REAL,
            kama_profit INTEGER,
            entry_date TEXT
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

# Initialisation de la BDD au chargement de l'application (nécessaire pour Render)
try:
    init_db()
except Exception as e:
    print(f"Erreur d'initialisation BDD: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bilan')
def bilan():
    return render_template('bilan.html')

@app.route('/items')
def items():
    return render_template('items.html')

@app.route('/api/brisage', methods=['GET'])
def get_data():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute('''
        SELECT id, pseudo, item_name, category, craft_cost, coeff, kama_profit, entry_date, break_type 
        FROM brisage 
        ORDER BY id DESC
    ''')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify(rows)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute('''
        SELECT pseudo, COUNT(*) as total_count, COALESCE(SUM(kama_profit), 0) as total_profit
        FROM brisage
        GROUP BY pseudo
        ORDER BY total_profit DESC
    ''')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(rows)

@app.route('/api/brisage', methods=['POST'])
def add_data():
    req = request.json or {}
    entry_date = req.get('entry_date') or datetime.now().strftime('%Y-%m-%d')
    
    # Conversion sécurisée des types pour PostgreSQL
    try:
        craft_cost = int(req.get('craft_cost')) if req.get('craft_cost') is not None and req.get('craft_cost') != '' else 0
        coeff = float(req.get('coeff')) if req.get('coeff') is not None and req.get('coeff') != '' else 0.0
        kama_profit = int(req.get('kama_profit')) if req.get('kama_profit') is not None and req.get('kama_profit') != '' else 0
    except (ValueError, TypeError) as e:
        return jsonify({"status": "error", "message": f"Données numériques invalides: {e}"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO brisage (pseudo, item_name, category, break_type, craft_cost, coeff, kama_profit, entry_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ''', (
        req.get('pseudo', ''), 
        req.get('item_name', ''), 
        req.get('category', ''), 
        req.get('break_type', ''), 
        craft_cost, 
        coeff, 
        kama_profit, 
        entry_date
    ))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"status": "success"}), 201

@app.route('/api/brisage/<int:item_id>', methods=['PUT'])
def update_data(item_id):
    req = request.json or {}
    
    try:
        craft_cost = int(req.get('craft_cost')) if req.get('craft_cost') is not None and req.get('craft_cost') != '' else 0
        coeff = float(req.get('coeff')) if req.get('coeff') is not None and req.get('coeff') != '' else 0.0
        kama_profit = int(req.get('kama_profit')) if req.get('kama_profit') is not None and req.get('kama_profit') != '' else 0
    except (ValueError, TypeError) as e:
        return jsonify({"status": "error", "message": f"Données numériques invalides: {e}"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE brisage 
        SET pseudo = %s, item_name = %s, category = %s, break_type = %s, craft_cost = %s, coeff = %s, kama_profit = %s, entry_date = %s
        WHERE id = %s
    ''', (
        req.get('pseudo', ''),
        req.get('item_name', ''),
        req.get('category', ''),
        req.get('break_type', ''),
        craft_cost,
        coeff,
        kama_profit,
        req.get('entry_date'),
        item_id
    ))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"status": "updated"}), 200

@app.route('/api/brisage/<int:item_id>', methods=['DELETE'])
def delete_data(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM brisage WHERE id = %s', (item_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"status": "deleted"}), 200

if __name__ == '__main__':
    print("Serveur lancé sur http://127.0.0.1:5000")
    app.run(debug=True, port=5000)