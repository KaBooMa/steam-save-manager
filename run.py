### This fix is applied to allow pyinstaller!! ###
import sys, os, io
if not os.path.exists('build.json'):
    logfile = io.StringIO()
    sys.stdout = logfile
    sys.stderr = logfile
##################################################

from tkinter import messagebox
import eel, shutil
from userdata import get_savedata_path
from steamapi import get_app_list
from save import get_saves
from persist import PersistentData

# Application vars
persist = PersistentData()

# Statics
SAVE_FOLDER_NAME = 'Saves'

eel.init('gui')

# Get the user's save data path
if not persist.savedata_path:
    persist.savedata_path = get_savedata_path()
    persist.save()

savedata_path = persist.savedata_path
game_save_folders = os.listdir(savedata_path)
app_list = get_app_list()

# Get the games the user has
games = {appid:name for appid, name in app_list.items() if str(appid) in game_save_folders}

### Eel exposed functions below ###
@eel.expose
def get_app_data():
    return {
        'selected_app_id': persist.selected_app_id,
        'active_save': persist.active_save,
        'games': games,
        'saves': get_saves(persist),
    }


@eel.expose
def select_game(app_id):
    persist.selected_app_id = app_id
    persist.active_save = persist.app_active_saves.get(app_id)

    # Not yet saved, so let's init
    if not persist.active_save:
        persist.active_save = 'MainSave'
        local_save_path = f'{SAVE_FOLDER_NAME}/{persist.selected_app_id}/{persist.active_save}'

        # Something went wrong. Abort without overwriting save!!
        if os.path.exists(local_save_path):
            messagebox.showerror('Malformed Data', 'Mismatch between persistent data and local saves found! Stopping save to prevent data loss.')
            return
        
        save_game()

    persist.save()



@eel.expose
def save_game():
    if not persist.active_save:
        persist.active_save = 'MainSave'

    if not os.path.exists(SAVE_FOLDER_NAME):
        os.mkdir(SAVE_FOLDER_NAME)

    ##### DOUBLE CHECK FOR SAVE SECURITY HERE #####
    save_path = f'{SAVE_FOLDER_NAME}/{persist.selected_app_id}/{persist.active_save}' ###### THIS NEEDS TO FACTOR IN SAVE NAME
    if os.path.exists(save_path):
        shutil.rmtree(save_path)

    # Start the save process
    shutil.copytree(f'{savedata_path}/{persist.selected_app_id}', save_path, dirs_exist_ok=True)
        
    persist.save()

    return True


@eel.expose
def new_game(name, notes):
    save_game() # Save player's current game before we go overwriting
    local_save_path = f'{SAVE_FOLDER_NAME}/{persist.selected_app_id}/{name}'
    steam_save_path = f'{savedata_path}/{persist.selected_app_id}'

    # Prevent erroneous duplication
    if os.path.exists(local_save_path):
        return False
    
    os.mkdir(local_save_path)
    shutil.rmtree(steam_save_path)
    os.mkdir(steam_save_path)

    # Update active save data for that app to new save
    persist.active_save = name
    persist.app_active_saves[persist.selected_app_id] = name
    
    # Make metadata for app if not exist
    if not persist.save_metadata.get(persist.selected_app_id):
        persist.save_metadata[persist.selected_app_id] = {}

    # Make save dict for app if not exist
    if not persist.save_metadata[persist.selected_app_id].get(name):
        persist.save_metadata[persist.selected_app_id][name] = {}

    persist.save_metadata[persist.selected_app_id][name]['notes'] = notes
        
    persist.save()

    # Load our new save
    load_game(name)

    return True


@eel.expose
def load_game(name):
    save_game() # Save player's current game before we go overwriting
    local_save_path = f'{SAVE_FOLDER_NAME}/{persist.selected_app_id}/{name}'
    steam_save_path = f'{savedata_path}/{persist.selected_app_id}'

    shutil.rmtree(steam_save_path)
    shutil.copytree(local_save_path, steam_save_path)

    # Update active save data
    persist.active_save = name
    persist.app_active_saves[persist.selected_app_id] = name
        
    persist.save()

    return True


@eel.expose
def delete_game(name):
    local_save_path = f'{SAVE_FOLDER_NAME}/{persist.selected_app_id}/{name}'

    if not os.path.exists(local_save_path):
        return False
    
    shutil.rmtree(local_save_path)

    del persist.app_active_saves[persist.selected_app_id]
    del persist.save_metadata[persist.selected_app_id][name]
    if persist.active_save == name:
        persist.active_save = None
        
    persist.save()

    return True
    

eel.start('index.html', size=(1200, 800))