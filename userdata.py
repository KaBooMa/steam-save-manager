import os
from tkinter import filedialog, messagebox

def get_userdata_path():
    DEFAULT_PATHS = ['C:/Program Files (x86)/Steam/userdata']
    userdata_path = None

    # Check if one of the defaults exist
    for path in DEFAULT_PATHS:
        if os.path.exists(path):
            return path

    # Allow user to manually select userdata folder
    messagebox.showinfo('Locate Userdata Folder', 'Unable to find userdata folder automatically. Please manually locate your userdata folder. This is typically located in your Steam folder.')
    userdata_path = filedialog.askdirectory()
    if os.path.exists(userdata_path) and os.path.dirname(userdata_path) == 'userdata':
        return userdata_path
    
    # Unable to locate. Throw an error
    raise Exception('Unable to locate userdata folder!')

    
def get_savedata_path():
    userdata_path = get_userdata_path()
    user_path = None

    # Automatically select the only folder if one exists (Single user setup)
    user_folders = os.listdir(userdata_path)
    if len(user_folders) == 1:
        user_path = f'{userdata_path}/{user_folders[0]}'
    else: # Unable to determine so ask the user
        messagebox.showinfo('Select User Folder', 'Unable to determine which user folder to use. Please select the desired folder.')
        user_path = filedialog.askdirectory()
    
    return user_path