import json
import os

def get_alpaca_credentials(file: str):
    json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), file)
    with open(json_path, 'r') as file:
        return json.load(file)