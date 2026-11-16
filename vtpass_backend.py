"""
Naija Prepaid Meter Tracker - Real VTpass Backend
Secure backend that calls VTpass Verify Meter.
NEVER put your Secret Key in the frontend app or in chat.
Put it only in environment variables on your server.
"""
import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def get_base_url():
    env = os.getenv("VTPASS_ENV", "sandbox").lower()
    if env == "live":
        return "https://vtpass.com/api"
    return "https://sandbox.vtpass.com/api"

@app.route("/health", methods=["GET"])
def health():
    env = os.getenv("VTPASS_ENV", "sandbox")
    has_key = bool(os.getenv("VTPASS_API_KEY"))
    has_secret = bool(os.getenv("VTPASS_SECRET_KEY"))
    return jsonify({
        "status": "ok",
        "env": env,
        "base_url": get_base_url(),
        "has_api_key": has_key,
        "has_secret_key": has_secret,
        "message": "Backend is running. Set VTPASS_ENV=sandbox for testing, live for real."
    })

@app.route("/api/verify-meter", methods=["POST"])
def verify_meter():
    data = request.get_json(silent=True) or {}
    service_id = data.get("serviceID") or data.get("serviceId")
    billers_code = data.get("billersCode") or data.get("meterNumber")
    meter_type = data.get("type") or "prepaid"

    if not service_id or not billers_code:
        return jsonify({
            "code": "400",
            "response_description": "Missing serviceID or billersCode",
            "content": None
        }), 400

    api_key = os.getenv("VTPASS_API_KEY")
    secret_key = os.getenv("VTPASS_SECRET_KEY")
    if not api_key or not secret_key:
        return jsonify({
            "code": "500",
            "response_description": "Backend missing VTPASS_API_KEY or VTPASS_SECRET_KEY env vars. Set them on your server, not in the frontend.",
            "content": None
        }), 500

    url = f"{get_base_url()}/merchant-verify"
    headers = {
        "api-key": api_key,
        "secret-key": secret_key,
        "Content-Type": "application/json"
    }
    payload = {
        "serviceID": service_id,
        "billersCode": str(billers_code),
        "type": meter_type
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        try:
            vtpass_json = resp.json()
        except Exception:
            vtpass_json = {"raw": resp.text}
        return jsonify(vtpass_json), resp.status_code
    except Exception as e:
        return jsonify({
            "code": "500",
            "response_description": f"Backend could not reach VTpass: {str(e)}",
            "content": None
        }), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
