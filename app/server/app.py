"""Flight delay prediction API.

Serves the list of arrival airports the model was trained on and, for a given
day of the week and arrival airport, the probability a flight arrives more
than 15 minutes late.

Both `model.pkl` and `airports.csv` are produced by `app/model/train.py`.

Run from this directory:

    python app.py
"""

import csv
import json
import pickle
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

SERVER_DIR = Path(__file__).resolve().parent
MODEL_PATH = SERVER_DIR / "model.pkl"
AIRPORTS_PATH = SERVER_DIR / "airports.csv"
METADATA_PATH = SERVER_DIR / "metadata.json"

# Column names the trained pipeline expects, and the ISO day numbering the
# dataset uses: 1 is Monday through 7 for Sunday.
FEATURE_COLUMNS = ["DayOfWeek", "DestAirportID"]
MIN_DAY_OF_WEEK = 1
MAX_DAY_OF_WEEK = 7


def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"{MODEL_PATH} is missing. Run `python app/model/train.py` first."
        )
    with open(MODEL_PATH, "rb") as model_file:
        return pickle.load(model_file)


def load_airports() -> list[dict]:
    """Read the airport lookup, sorted by name for display."""
    if not AIRPORTS_PATH.exists():
        raise FileNotFoundError(
            f"{AIRPORTS_PATH} is missing. Run `python app/model/train.py` first."
        )
    with open(AIRPORTS_PATH, newline="") as airports_file:
        airports = [
            {"id": int(row["id"]), "name": row["name"]}
            for row in csv.DictReader(airports_file)
        ]
    return sorted(airports, key=lambda airport: airport["name"])


def load_metadata() -> dict:
    """Training summary, including the overall rate of late arrivals."""
    if not METADATA_PATH.exists():
        raise FileNotFoundError(
            f"{METADATA_PATH} is missing. Run `python app/model/train.py` first."
        )
    return json.loads(METADATA_PATH.read_text())


app = Flask(__name__)
CORS(app)

model = load_model()
airports = load_airports()
metadata = load_metadata()
airports_by_id = {airport["id"]: airport["name"] for airport in airports}


def read_int_param(name: str) -> int:
    """Read a required integer query parameter, or raise a 400-worthy error."""
    raw = request.args.get(name)
    if raw is None or raw == "":
        raise ValueError(f"'{name}' is required")
    try:
        return int(raw)
    except ValueError:
        raise ValueError(f"'{name}' must be a whole number, got '{raw}'") from None


@app.get("/health")
def health():
    """Basic liveness check, useful for confirming the artifacts loaded."""
    return jsonify({"status": "ok", "airports": len(airports)})


@app.get("/airports")
def list_airports():
    """The arrival airports the model can make a prediction for."""
    return jsonify(airports)


@app.get("/model")
def describe_model():
    """How the model was trained and how well it scored."""
    return jsonify(metadata)


@app.get("/predict")
def predict():
    """Probability of an arrival delay over 15 minutes.

    Query parameters:
        day_of_week: 1 (Monday) through 7 (Sunday)
        airport_id:  an id from /airports
    """
    try:
        day_of_week = read_int_param("day_of_week")
        airport_id = read_int_param("airport_id")
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    if not MIN_DAY_OF_WEEK <= day_of_week <= MAX_DAY_OF_WEEK:
        return (
            jsonify(
                {
                    "error": "'day_of_week' must be between 1 (Monday) and 7 (Sunday), "
                    f"got {day_of_week}"
                }
            ),
            400,
        )

    if airport_id not in airports_by_id:
        return jsonify({"error": f"Unknown airport id {airport_id}"}), 404

    features = pd.DataFrame([[day_of_week, airport_id]], columns=FEATURE_COLUMNS)
    probability = float(model.predict_proba(features)[0][1])

    return jsonify(
        {
            "day_of_week": day_of_week,
            "airport_id": airport_id,
            "airport_name": airports_by_id[airport_id],
            "probability": probability,
            "percent": round(probability * 100, 1),
            # The share of all flights in the training data that arrived late,
            # so the answer can be read against a typical flight.
            "baseline": metadata["base_rate"],
        }
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
