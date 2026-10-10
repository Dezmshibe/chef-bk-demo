from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.get("/")
def home():
    return render_template("index.html")

@app.post("/request-quote")
def request_quote():
    data = request.get_json(silent=True) or request.form
    # Demo only: replace with email/CRM/WhatsApp integration.
    return jsonify({
        "success": True,
        "message": f"Thanks {data.get('name', 'there')}! Your enquiry has been received. Chef BK can follow up with you."
    })

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
