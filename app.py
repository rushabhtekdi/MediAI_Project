from flask import Flask, request, jsonify, render_template
from helpers import generate_ai_response, generate_mock_response
from config import USE_MOCK_RESPONSE

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/check-symptoms", methods=["POST"])
def check_symptoms():
    symptoms = request.form.get("symptoms")
    
    # Use the appropriate response generator based on config
    if USE_MOCK_RESPONSE:
        response = generate_mock_response(symptoms)
    else:
        response = generate_ai_response(symptoms)
    
    return jsonify({"result": response})

if __name__ == "__main__":
    app.run(debug=True)