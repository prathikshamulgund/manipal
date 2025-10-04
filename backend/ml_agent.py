# backend/ml_agent.py
import os
import requests
from datetime import datetime
from database import get_db_connection
from vector_db import semantic_search

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")

SYSTEM_PROMPT = """
You are an AI Mining Operations Co-Pilot assistant...
"""

def get_mining_context_summary(context_data):
    # (Use your original summary function but accept DB context)
    equipment = context_data.get('equipment', [])
    production = context_data.get('production', [])
    alerts = context_data.get('alerts', [])
    # Build simple summary (same as your original logic)...
    eq_count = len(equipment)
    operational = sum(1 for e in equipment if e.get('status') == 'operational')
    eq_details = [f"{e.get('name')} ({e.get('type')})" for e in equipment[:3]]
    summary = f"Fleet: {eq_count}. Operational: {operational}. Examples: {', '.join(eq_details)}."
    if production:
        # compute average if numeric
        try:
            avg_eff = sum(float(p.get('efficiency',0)) for p in production)/len(production)
            total_ore = sum(float(p.get('ore_extracted_tons', p.get('production_value',0))) for p in production)
            summary += f" Production last {len(production)} days: avg eff {avg_eff:.1f}%, total ore {total_ore}."
        except Exception:
            pass
    summary += f" Alerts: {len(alerts)}."
    return summary

def call_groq_mistral(query, context):
    if not GROQ_API_KEY:
        return None, "Groq API key not configured"
    context_summary = get_mining_context_summary(context)
    payload = {
        "model": os.getenv("GROQ_MODEL", "mistral-7b"),  # set via env
        "messages": [
            {"role":"system", "content": SYSTEM_PROMPT},
            {"role":"user", "content": f"{context_summary}\n\nQuery: {query}"}
        ],
        "temperature": float(os.getenv("GROQ_TEMPERATURE", 0.2)),
        "max_tokens": int(os.getenv("GROQ_MAX_TOKENS", 300))
    }
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    try:
        resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        # adapt to provider response format
        choice = data.get("choices", [{}])[0].get("message", {}).get("content") or data.get("choices", [{}])[0].get("text")
        return choice, None
    except requests.exceptions.RequestException as e:
        return None, f"AI service error: {e}"
    except Exception as e:
        return None, f"Unexpected response: {e}"

def extract_relevant_data(query, context_data):
    # Reuse your function logic but fetch dynamic DB data if necessary
    # For brevity, return a small subset:
    data = {}
    q = query.lower()
    if "fuel" in q:
        data["fuel_summary"] = {"total": sum(float(e.get('fuel_efficiency',0))*int(e.get('runtime_hours',0))/100 for e in context_data.get('equipment', []))}
    if "maintenance" in q:
        data["alerts"] = context_data.get('alerts', [])
    if "production" in q:
        data["production"] = context_data.get('production', [])
    return data

def process_ai_query(query, context_data):
    answer, error = call_groq_mistral(query, context_data)
    if error:
        # fallback: do local semantic search for helpful documents
        docs = semantic_search(query, n_results=3)
        fallback_answer = f"AI service unavailable: {error}. I returned relevant docs instead."
        return {"query_type":"fallback", "answer": fallback_answer, "data":{"docs":docs}, "ai_powered": False}
    relevant_data = extract_relevant_data(query, context_data)
    return {"query_type":"ai_response", "answer": answer, "data": relevant_data, "ai_powered": True, "model": os.getenv("GROQ_MODEL","mistral-7b")}
