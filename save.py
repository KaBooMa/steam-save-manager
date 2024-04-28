from datetime import datetime
import os

from persist import PersistentData

SAVE_FOLDER_NAME = 'Saves'

def get_saves(persist: PersistentData):
    save_folder = f'{SAVE_FOLDER_NAME}/{persist.selected_app_id}'
    if not os.path.exists(save_folder):
        return []
    
    saves = []
    for save in os.listdir(save_folder):
        last_updated = datetime.fromtimestamp(os.path.getmtime(f'{save_folder}/{save}')).strftime('%Y-%m-%d %I:%M:%S %p')
        notes = persist.save_metadata.get(persist.selected_app_id, {}).get(save, {}).get('notes', None)
        saves.append({
            'name': save,
            'notes': notes,
            last_updated: last_updated,
        })

    return saves