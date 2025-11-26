import os
import pandas as pd
from handlers.trackers import handle_score_trackers

SCORE_HANDLERS = {
    "trackers.csv": handle_score_trackers,
}
DATA_PATH = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")), "data")

def score_single_app(car_app_path):
    score = 0
    for csv, score_handler in SCORE_HANDLERS.items():
        path = os.path.join(car_app_path, csv)
        dataframe = pd.read_csv(path)
        score += score_handler(dataframe)
    return score

# car_app_path = os.path.join(DATA_PATH, 'Honda')
# print(score_single_app(car_app_path))