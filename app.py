from flask import Flask, render_template, request, jsonify, redirect, url_for, abort
import os, json, secrets
from datetime import datetime
from pathlib import Path

app = Flask(__name__)

# ---------------------------------------------------------------
# In-memory store for demo quotes. Resets when the server restarts.
# ---------------------------------------------------------------
QUOTES = {}

# ---------------------------------------------------------------
# Demo pricing (ZAR). Tune with Chef BK's real rates.
# ---------------------------------------------------------------
RATES = {
    "Private dinner":         {"per_guest": 550, "label": "Private dinner"},
    "Birthday / celebration": {"per_guest": 420, "label": "Celebration catering"},
    "Corporate event":        {"per_guest": 380, "label": "Corporate catering"},
    "Graduation":             {"per_guest": 400, "label": "Graduation catering"},
    "Meal prep":              {"per_guest": 180, "label": "Meal prep (per portion)"},
    "Other":                  {"per_guest": 450, "label": "Custom experience"},
}

def chef_fee(guests):
    if guests <= 10:  return 850
    if guests <= 30:  return 1500
    if guests <= 60:  return 2500
    return 3500


def build_quote(data):
    name       = (data.get("name") or "").strip()
    phone      = (data.get("phone") or "").strip()
    email      = (data.get("email") or "").strip()
    event_type = (data.get("event_type") or "Other").strip()
    date       = (data.get("date") or "").strip()
    message    = (data.get("message") or "").strip()

    try:
        guests = int(data.get("guests") or 0)
    except (TypeError, ValueError):
        guests = 0

    rate_info = RATES.get(event_type, RATES["Other"])
    per_guest = rate_info["per_guest"]
    label     = rate_info["label"]

    subtotal   = per_guest * max(guests, 0)
    fee        = chef_fee(guests) if guests > 0 else 0
    low_total  = subtotal + fee
    high_total = int(low_total * 1.15)

    quote_id = "BK-" + secrets.token_hex(3).upper()

    return {
        "id": quote_id,
        "created_at": datetime.utcnow().strftime("%d %b %Y"),
        "client": {"name": name, "phone": phone, "email": email},
        "event": {
            "type": event_type,
            "label": label,
            "date": date,
            "guests": guests,
            "notes": message,
        },
        "pricing": {
            "per_guest": per_guest,
            "subtotal": subtotal,
            "chef_fee": fee,
            "low_total": low_total,
            "high_total": high_total,
        },
    }


@app.get("/")
def home():
    return render_template("index.html")


@app.post("/request-quote")
def request_quote():
    data = request.get_json(silent=True) or request.form
    quote = build_quote(data)

    # store for the /quote/<id> page
    QUOTES[quote["id"]] = quote

    # also persist to disk so nothing is lost on restart
    log_path = Path(app.root_path) / "enquiries.jsonl"
    try:
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(quote) + "\n")
    except Exception as e:
        app.logger.warning("Could not write enquiry log: %s", e)

    return jsonify({
        "success": True,
        "quote_id": quote["id"],
        "redirect": url_for("quote_page", quote_id=quote["id"]),
    })


@app.get("/quote/<quote_id>")
def quote_page(quote_id):
    quote = QUOTES.get(quote_id)
    if not quote:
        abort(404)
    return render_template("quote.html", quote=quote)


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(debug=debug, host="127.0.0.1", port=5000)