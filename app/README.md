# Will my flight be late?

A working solution to the [workshop challenges](../hackathon.md): pick an
arrival airport and a day of the week, and see the chance a flight lands more
than 15 minutes behind schedule.

Three pieces, one per challenge:

| Directory | What it is |
| --- | --- |
| [`model/`](./model) | Trains the delay model from [`data/flights.csv`](../data/flights.csv) and exports it |
| [`server/`](./server) | A Flask API serving the airport list and predictions |
| [`client/`](./client) | A SvelteKit frontend |

## Running it

Three steps, from the repository root. The model artifacts are committed, so
you can skip step 1 unless you want to retrain.

### 1. Train the model (optional)

```bash
pip install -r app/server/requirements.txt
python app/model/train.py
```

This writes `model.pkl`, `airports.csv` and `metadata.json` into `app/server/`.

### 2. Start the API

```bash
cd app/server
pip install -r requirements.txt
python app.py
```

It listens on <http://127.0.0.1:5000>.

### 3. Start the frontend

In a second terminal:

```bash
cd app/client
npm install
npm run dev
```

Then open <http://localhost:5173>. If the API is running somewhere else, set
`API_BASE_URL` before starting the dev server.

## The API

| Endpoint | Returns |
| --- | --- |
| `GET /health` | Liveness check and the number of airports loaded |
| `GET /airports` | `[{ "id": 10140, "name": "Albuquerque International Sunport" }, ...]`, sorted by name |
| `GET /model` | Training summary: rows used, base rate, accuracy, ROC AUC, Brier score |
| `GET /predict?day_of_week=5&airport_id=13930` | The delay probability for that day and airport |

`day_of_week` runs from 1 (Monday) to 7 (Sunday), matching the dataset.
`airport_id` must be one of the ids from `/airports`; anything else is a 404,
and a missing or out-of-range parameter is a 400.

```json
{
  "day_of_week": 5,
  "airport_id": 13930,
  "airport_name": "Chicago O'Hare International",
  "probability": 0.2658,
  "percent": 26.6,
  "baseline": 0.2074
}
```

`baseline` is the share of all flights in the training data that arrived late,
so the frontend can say whether a given flight is better or worse than average.

## About the model

A logistic regression over one-hot encoded day of week and arrival airport.
Both are categorical - an airport id is a label, not a quantity - so encoding
them keeps the model from reading the ids as numbers on a scale.

The classes are deliberately left unweighted. Only about one flight in five
arrives late, so a model optimised for hard yes/no accuracy would simply answer
"on time" every time. The app reports a probability instead, which needs those
probabilities to stay calibrated against the real rate:

```
Predicted vs. actual late arrivals by risk band:
   (0.0972, 0.171]  predicted 15.2%  actual 15.1%  (10,904 flights)
    (0.171, 0.193]  predicted 18.2%  actual 18.3%  (10,639 flights)
    (0.193, 0.215]  predicted 20.3%  actual 20.5%  (10,767 flights)
    (0.215, 0.242]  predicted 22.8%  actual 22.9%  (10,796 flights)
    (0.242, 0.347]  predicted 27.3%  actual 27.1%  (10,699 flights)
```

Day and airport alone are weak predictors - ROC AUC is 0.57, barely better than
a coin flip at ranking flights - so predictions only range from about 10% to
35%. That is an honest limit of these two features rather than a bug, and the
frontend shows each answer against the 20.7% average so the comparison is the
point rather than the absolute number. Departure time, carrier and month are
all in the dataset if you want to push the model further.

## Data notes

Of the 271,940 flights in the dataset, 269,024 are used for training:

- Cancelled flights are dropped - they never arrived, so they cannot be
  labelled late or on time.
- `DepDel15` is missing on a few rows; those flights left on time, so it is
  filled with 0.
