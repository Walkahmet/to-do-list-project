import json
import os
import datetime

DATA_FILE = "todos.json"
DEFAULT_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

TR_TO_EN = {
    "Pazartesi": "Monday",
    "Salı": "Tuesday",
    "Çarşamba": "Wednesday",
    "Perşembe": "Thursday",
    "Cuma": "Friday",
    "Cumartesi": "Saturday",
    "Pazar": "Sunday"
}

def load_tasks():
    default_data = {day: [] for day in DEFAULT_DAYS}
    if not os.path.exists(DATA_FILE):
        return default_data
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Migration from old list format to dict format
            if isinstance(data, list):
                today_idx = datetime.datetime.today().weekday()
                today_name = DEFAULT_DAYS[today_idx]
                default_data[today_name] = data
                save_tasks(default_data)
                return default_data
            
            # Migration from Turkish to English day keys
            migrated_data = {}
            for key, tasks in data.items():
                if key in TR_TO_EN:
                    en_key = TR_TO_EN[key]
                    migrated_data[en_key] = tasks
                else:
                    migrated_data[key] = tasks
            data = migrated_data
            
            # Merge with default structure to ensure all days exist
            for day in DEFAULT_DAYS:
                if day not in data:
                    data[day] = []
            
            # Filter out any non-default days
            final_data = {day: data[day] for day in DEFAULT_DAYS}
            return final_data
    except Exception as e:
        print(f"Error loading tasks: {e}")
        return default_data

def save_tasks(tasks):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving tasks: {e}")
