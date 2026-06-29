import json, os

PREDICTIONS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "predictions.json")

def load_predictions():
    try:
        with open(PREDICTIONS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_prediction(user_id, match_id, home_score, away_score):
    preds = load_predictions()
    if user_id not in preds:
        preds[user_id] = {}
    preds[user_id][str(match_id)] = {
        "home_score": home_score,
        "away_score": away_score,
        "timestamp": os.popen('date -u +"%Y-%m-%dT%H:%M:%SZ"').read().strip() if os.name != 'nt' else "" 
    }
    # Simple timestamp for Windows/Linux
    import datetime
    preds[user_id][str(match_id)]["timestamp"] = datetime.datetime.utcnow().isoformat()
    
    with open(PREDICTIONS_FILE, "w") as f:
        json.dump(preds, f, indent=2)
    return preds[user_id][str(match_id)]

def get_user_predictions(user_id):
    preds = load_predictions()
    return preds.get(user_id, {})
