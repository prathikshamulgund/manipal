from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os

# blueprints / modules
from mysql_routes import register_mysql_routes, gather_context
from vector_db import semantic_search  # make sure this exists
from ml_agent import process_ai_query  # LLM logic in ml_agent.py
from auth import register_auth_routes  # NEW: Import auth

app = Flask(__name__)
CORS(app)

# Register MySQL routes
register_mysql_routes(app)

# Register Authentication routes (ADD THIS LINE HERE)
register_auth_routes(app)

@app.route('/api/query', methods=['POST'])
def handle_query():
    data = request.get_json() or {}
    query = data.get('query', '').strip()
    if not query:
        return jsonify({"error": "Query is required"}), 400

    context_data = gather_context()
    response = process_ai_query(query, context_data)

    return jsonify({
        "query": query,
        "response": response.get("answer"),
        "query_type": response.get("query_type"),
        "data": response.get("data"),
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "AI Mining Operations Co-Pilot",
        "timestamp": datetime.now().isoformat()
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)