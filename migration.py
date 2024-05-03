import os, uuid, shutil

from persist import PersistentData

def run(override_id):
    persist = PersistentData()
    if override_id:
        persist.release_id = override_id

    if persist.release_id == '153391761':
        for game in os.listdir('Saves'):
            game_path = f'Saves/{game}'
            for save in os.listdir(game_path):
                save_path = f'{game_path}/{save}'
                version = str(uuid.uuid4())
                version_path = f'{save_path}/{version}'
                shutil.move(save_path, 'temp')
                os.mkdir(save_path)
                os.mkdir(version_path)
                shutil.move('temp', version_path)
                persist.app_active_saves[game] = {
                    'name': save,
                    'version': version
                }
        
        persist.release_id == '153940052'
    
    persist.save()

