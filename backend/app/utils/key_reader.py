import json
import os

def get_alpaca_credentials(file: str):
    code_file_path = os.path.dirname(__file__)
    # json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), f'../../{file}')
    json_path = f'{code_file_path}/../../{file}'
    print('json_pathjson_pathjson_path1111:', json_path, 'code_file_path=', code_file_path)
    with open(json_path, 'r') as file:
        return json.load(file)