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
        notes = persist.save_metadata.get(persist.selected_app_id, {}).get(save, {}).get('notes', None)
        versions = []
        for version in os.listdir(f'{save_folder}/{save}'):
            versions.append({
                'name': version,
                'last_updated_raw': os.path.getmtime(f'{save_folder}/{save}/{version}'),
                'last_updated': datetime.fromtimestamp(os.path.getmtime(f'{save_folder}/{save}/{version}')).strftime('%Y-%m-%d %I:%M:%S %p')
            })

        versions = sorted(versions, key=lambda item: item['last_updated_raw'], reverse=True)

        saves.append({
            'name': save,
            'notes': notes,
            'versions': versions
        })

    return saves