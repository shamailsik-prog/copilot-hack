"""Train the flight delay model and export the artifacts the API needs.

Reads data/flights.csv (2013 US domestic flights), trains a classifier that
estimates the probability a flight arrives more than 15 minutes late given the
day of the week and the arrival (destination) airport, then writes:

  app/server/model.pkl      - the fitted scikit-learn pipeline
  app/server/airports.csv   - the destination airports the model knows about
  app/server/metadata.json  - how the model scored, and the overall late rate

Run from the repository root:

    python app/model/train.py
"""

import argparse
import json
import pickle
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA = REPO_ROOT / "data" / "flights.csv"
DEFAULT_OUTPUT = REPO_ROOT / "app" / "server"

# The two things a traveller knows ahead of time.
FEATURES = ["DayOfWeek", "DestAirportID"]
TARGET = "ArrDel15"

RANDOM_STATE = 42


def load_flights(path: Path) -> pd.DataFrame:
    """Load the raw flight data and clean up the columns the model relies on."""
    flights = pd.read_csv(path)

    # DepDel15 is missing for a handful of rows; those flights left on time.
    flights["DepDel15"] = flights["DepDel15"].fillna(0)

    # Cancelled flights never arrived, so they cannot be labelled late or not.
    flights = flights[flights["Cancelled"] == 0]

    # Drop anything still missing a feature or the label.
    flights = flights.dropna(subset=FEATURES + [TARGET])

    flights["DayOfWeek"] = flights["DayOfWeek"].astype(int)
    flights["DestAirportID"] = flights["DestAirportID"].astype(int)
    flights[TARGET] = flights[TARGET].astype(int)

    return flights


def build_model() -> Pipeline:
    """A logistic regression over one-hot encoded day and airport.

    Both features are categorical - airport IDs are labels, not quantities - so
    they are one-hot encoded rather than fed to the model as raw numbers.

    The classes are left unweighted on purpose. The app reports a probability
    rather than a yes/no answer, so the probabilities need to stay calibrated
    against the real base rate of roughly one late arrival in five.
    """
    encoder = ColumnTransformer(
        [("categorical", OneHotEncoder(handle_unknown="ignore"), FEATURES)]
    )
    classifier = LogisticRegression(max_iter=1000)
    return Pipeline([("encode", encoder), ("classify", classifier)])


def export_airports(flights: pd.DataFrame, destination: Path) -> pd.DataFrame:
    """Write the destination airports, sorted by name, for the API to serve."""
    airports = (
        flights[["DestAirportID", "DestAirportName"]]
        .drop_duplicates()
        .rename(columns={"DestAirportID": "id", "DestAirportName": "name"})
        .sort_values("name")
    )
    airports.to_csv(destination, index=False)
    return airports


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)

    print(f"Loading {args.data}")
    flights = load_flights(args.data)
    print(f"{len(flights):,} usable flights, {flights[TARGET].mean():.1%} arrived late")

    X_train, X_test, y_train, y_test = train_test_split(
        flights[FEATURES],
        flights[TARGET],
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=flights[TARGET],
    )

    model = build_model()
    model.fit(X_train, y_train)

    probabilities = model.predict_proba(X_test)[:, 1]
    print(f"\nAccuracy:    {model.score(X_test, y_test):.3f}")
    print(f"ROC AUC:     {roc_auc_score(y_test, probabilities):.3f}")
    print(f"Brier score: {brier_score_loss(y_test, probabilities):.3f} (lower is better)")
    print(
        f"Predicted risk ranges from {probabilities.min():.1%} to "
        f"{probabilities.max():.1%}; {y_test.mean():.1%} of held-out flights were late"
    )

    # Day and airport alone only nudge the odds around the base rate, so the
    # model almost never crosses a 0.5 threshold. Compare the predicted risk
    # against what actually happened instead of scoring hard yes/no calls.
    print("\nPredicted vs. actual late arrivals by risk band:")
    bands = pd.DataFrame({"risk": probabilities, "late": y_test.to_numpy()})
    for label, group in bands.groupby(pd.qcut(bands["risk"], 5, duplicates="drop")):
        print(
            f"  {str(label):>16}  predicted {group['risk'].mean():5.1%}"
            f"  actual {group['late'].mean():5.1%}  ({len(group):,} flights)"
        )

    model_path = args.output / "model.pkl"
    with open(model_path, "wb") as model_file:
        pickle.dump(model, model_file)
    print(f"Wrote {model_path}")

    airports_path = args.output / "airports.csv"
    airports = export_airports(flights, airports_path)
    print(f"Wrote {airports_path} ({len(airports)} airports)")

    metadata_path = args.output / "metadata.json"
    metadata = {
        "trained_on": len(flights),
        "airports": len(airports),
        # The share of all flights that arrived late, so the app can show how a
        # given day and airport compares with an average flight.
        "base_rate": float(flights[TARGET].mean()),
        "accuracy": float(model.score(X_test, y_test)),
        "roc_auc": float(roc_auc_score(y_test, probabilities)),
        "brier_score": float(brier_score_loss(y_test, probabilities)),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"Wrote {metadata_path}")


if __name__ == "__main__":
    main()
