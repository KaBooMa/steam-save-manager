### This fix is applied to allow pyinstaller!! ###
import sys, os, io
if not os.path.exists('README.md'):
    logfile = io.StringIO()
    sys.stdout = logfile
    sys.stderr = logfile
    DEBUG = False
else:
    DEBUG = True
##################################################

from tkinter import messagebox
import eel, shutil, threading, subprocess, time, uuid

import update, migration
from userdata import get_savedata_path
from steamapi import get_app_list
from save import get_saves
from persist import PersistentData

# Clean up any update leftovers
if os.path.exists('update'):
    shutil.copy(f'update/{update.UPDATE_EXE_NAME}', './')
    shutil.rmtree('update')

# Application vars
persist = PersistentData()

# Statics
SAVE_FOLDER_NAME = 'Saves'


# Sadly didn't have migrations available in initial release... 
# So we're patching in a migration here to prevent current userbase data loss
# This code can go away at some point in the future when nobody is using the old version (?)
if type(persist.app_active_saves.get(persist.selected_app_id)) != dict and persist.release_id == '153940052':
    migration.run('153391761')
    persist = PersistentData() # Reload persist

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

latest_release = update.get_latest_release_info()
latest_pre_release = update.get_latest_pre_release()

### Eel exposed functions below ###
@eel.expose
def get_app_data():
    return {
        'selected_app_id': persist.selected_app_id,
        'active_save': persist.app_active_saves.get(persist.selected_app_id),
        'savedata_path': persist.savedata_path,
        'current_version': persist.release_id,
        'games': games,
        'saves': get_saves(persist),
        'latest_release': latest_release,
        'latest_pre_release': latest_pre_release,
        'debug': DEBUG,
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
    steam_save_path = f'{savedata_path}/{persist.selected_app_id}'

    # Create Saves/ if not exist
    if not os.path.exists(SAVE_FOLDER_NAME):
        os.mkdir(SAVE_FOLDER_NAME)

    # Create Saves/app_id if not exist
    app_id_path = f'{SAVE_FOLDER_NAME}/{persist.selected_app_id}'
    if not os.path.exists(app_id_path):
        os.mkdir(app_id_path)

    # Create new save version
    active_save = persist.app_active_saves.get(persist.selected_app_id)
    new_version = str(uuid.uuid4())
    if not active_save:
        active_save = persist.app_active_saves[persist.selected_app_id] = {
            'name': 'MainSave',
            'version': new_version
        }
    else:
        active_save['version'] = new_version

    # Create Saves/app_id/active_save if not exist
    active_save_path = f'{app_id_path}/{active_save.get("name")}'
    if not os.path.exists(active_save_path):
        os.mkdir(active_save_path)

    if not os.path.exists(steam_save_path):
        os.mkdir(steam_save_path)

    # Start the save process
    current_save_path = f'{active_save_path}/{new_version}'
    shutil.copytree(steam_save_path, current_save_path, dirs_exist_ok=True)
    current_time = time.time()
    os.utime(current_save_path, (current_time, current_time))
        
    persist.save()

    return True


@eel.expose
def edit_game(original_name, new_name, notes):
    original_save_path = f'{SAVE_FOLDER_NAME}/{persist.selected_app_id}/{original_name}'
    new_save_path = f'{SAVE_FOLDER_NAME}/{persist.selected_app_id}/{new_name}'

    # Stop accidental name overlaps
    if original_name != new_name and os.path.exists(new_save_path):
        return False
    
    # Update active save if editing active
    save = persist.app_active_saves[persist.selected_app_id]
    if save.get('name') == original_name:
        save['name'] = new_name

    del persist.save_metadata[persist.selected_app_id][original_name]
        
    persist.save_metadata[persist.selected_app_id][new_name] = {
        'name': new_name,
        'notes': notes
    }
    
    shutil.move(original_save_path, new_save_path)

    return True


@eel.expose
def new_game(name, notes):
    save_game() # Save player's current game before we go overwriting
        
    # Create new save
    save = persist.app_active_saves[persist.selected_app_id] = {
        'name': name,
        'version': str(uuid.uuid4())
    }
    
    active_save_path = f'{SAVE_FOLDER_NAME}/{persist.selected_app_id}/{name}'
    local_save_path = f'{active_save_path}/{save.get("version")}'
    steam_save_path = f'{savedata_path}/{persist.selected_app_id}'
    
    # Create Saves/app_id/active_save if not exist
    if not os.path.exists(active_save_path):
        os.mkdir(active_save_path)

    os.mkdir(local_save_path)
    shutil.rmtree(steam_save_path)
    os.mkdir(steam_save_path)
    
    # Make metadata for app if not exist
    if not persist.save_metadata.get(persist.selected_app_id):
        persist.save_metadata[persist.selected_app_id] = {}

    # Make save dict for app if not exist
    if not persist.save_metadata[persist.selected_app_id].get(name):
        persist.save_metadata[persist.selected_app_id][name] = {}

    persist.save_metadata[persist.selected_app_id][name]['notes'] = notes
        
    persist.save()

    return True


@eel.expose
def load_version(name, version):
    save_game() # Save player's current game before we go overwriting
    local_save_path = f'{SAVE_FOLDER_NAME}/{persist.selected_app_id}/{name}/{version}'
    steam_save_path = f'{savedata_path}/{persist.selected_app_id}'

    shutil.rmtree(steam_save_path)
    shutil.copytree(local_save_path, steam_save_path)

    # Update active save data
    persist.app_active_saves[persist.selected_app_id] = {
        'name': name,
        'version': version
    }
        
    persist.save()

    return True


@eel.expose
def delete_game(name):
    local_save_path = f'{SAVE_FOLDER_NAME}/{persist.selected_app_id}/{name}'

    if not os.path.exists(local_save_path):
        return False
    
    shutil.rmtree(local_save_path)

    # del persist.app_active_saves[persist.selected_app_id]
    del persist.save_metadata[persist.selected_app_id][name]
        
    persist.save()

    return True


@eel.expose
def delete_version(name, save_version):
    local_save_path = f'{SAVE_FOLDER_NAME}/{persist.selected_app_id}/{name}'
    local_version_path = f'{local_save_path}/{save_version}'

    if len(os.listdir(local_save_path)) <= 1:
        return False
    
    shutil.rmtree(local_version_path)

    if save_version == persist.app_active_saves.get('version'):
        persist.app_active_saves['version'] = None
        
    persist.save()

    return True
    

update_progress = None
@eel.expose
def start_update():
    thread = threading.Thread(target=download_update)
    thread.start()
    return True


def download_update():
    global update_progress

    for status in update.download_update(latest_release.get('download_url')):
        update_progress = status

    eel.close_window()
    time.sleep(1) # Might be a better way to handle this. Delaying to allow time for eel to close.
    subprocess.Popen([update.UPDATE_EXE_NAME, str(latest_release.get('id'))])


@eel.expose
def get_update_progress():
    global update_progress
    return update_progress

eel.start('index.html', size=(1200, 800))