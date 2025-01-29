import json

def save_mcam(config_data, filepath):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=4)

def load_mcam(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)
