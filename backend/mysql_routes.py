from flask import jsonify
from database import get_db_connection
from datetime import datetime
import random

IN_MEMORY_EQUIPMENT = [
    {"id":1, "name":"Haul Truck HT-001", "type":"Haul Truck", "status":"operational",
     "runtime_hours":12450, "fuel_efficiency":8.5, "last_maintenance":"2024-09-15",
     "next_maintenance":"2025-01-15", "location":"Pit A"},
]

def register_mysql_routes(app):

    @app.route('/api/mysql/status')
    def mysql_status():
        conn = get_db_connection()
        if conn:
            conn.close()
            return jsonify({"status": "connected", "database": True})
        return jsonify({"status": "disconnected", "database": False})

    @app.route('/api/equipment')
    def get_equipment():
        conn = get_db_connection()
        if not conn:
            return jsonify(IN_MEMORY_EQUIPMENT)
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM equipment")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(rows or IN_MEMORY_EQUIPMENT)

    @app.route('/api/production')
    def get_production():
        conn = get_db_connection()
        if not conn:
            return jsonify([
                {"name": e["name"], "production_date": datetime.now().date().isoformat(),
                 "production_value": random.uniform(800,1500), "efficiency": random.uniform(75,95)}
                for e in IN_MEMORY_EQUIPMENT
            ])
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT e.name, p.production_date, p.production_value, p.efficiency
            FROM production_data p
            JOIN equipment e ON p.equipment_id = e.id
            ORDER BY p.production_date DESC
            LIMIT 50
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(rows)

    @app.route('/api/maintenance-alerts')
    def get_maintenance_alerts():
        conn = get_db_connection()
        if not conn:
            alerts = []
            now = datetime.now().date()
            for e in IN_MEMORY_EQUIPMENT:
                try:
                    next_m = datetime.fromisoformat(e.get('next_maintenance')).date()
                    if (next_m - now).days <= 30:
                        alerts.append({
                            "name": e["name"],
                            "type": e["type"],
                            "next_maintenance": e.get('next_maintenance'),
                            "status": "pending"
                        })
                except Exception:
                    continue
            return jsonify(alerts)

        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT e.name, e.type, m.next_maintenance, m.status, m.maintenance_type
            FROM maintenance_schedule m
            JOIN equipment e ON m.equipment_id = e.id
            WHERE m.status IN ('urgent', 'pending')
            ORDER BY m.next_maintenance ASC
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(rows)


def gather_context():
    conn = get_db_connection()
    if not conn:
        return {"equipment": IN_MEMORY_EQUIPMENT, "production": [], "alerts": []}

    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM equipment")
    equipment = cur.fetchall()

    cur.execute("""
        SELECT production_date as date, production_value as ore_extracted_tons, efficiency
        FROM production_data
        ORDER BY production_date DESC
        LIMIT 7
    """)
    production = cur.fetchall()

    cur.execute("""
        SELECT e.id as equipment_id, e.name as equipment_name, m.next_maintenance
        FROM maintenance_schedule m
        JOIN equipment e ON m.equipment_id = e.id
        WHERE m.status IN ('urgent', 'pending')
    """)
    alerts = cur.fetchall()

    cur.close()
    conn.close()

    return {
        "equipment": equipment or IN_MEMORY_EQUIPMENT,
        "production": production,
        "alerts": alerts or []
    }
