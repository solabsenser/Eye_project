from flask import Flask, render_template, jsonify
import random

app = Flask(__name__)

# Тестовые gaze данные
gaze_data = {
    "x": 500,
    "y": 300
}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/gaze")
def gaze():
    return jsonify(gaze_data)

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
