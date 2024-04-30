import requests, time, os, shutil, subprocess
from zipfile import ZipFile

from persist import PersistentData

MAIN_EXE_NAME = 'Steam Save Manager.exe'
UPDATE_EXE_NAME = 'updater.exe'
APP_FILES = {
    'files': ['Steam Save Manager.exe'],
    'folders': ['_internal'],
}
GITHUB_URL = 'https://api.github.com/repos/KaBooMa/steam-save-manager/releases'

def get_latest_pre_release():
    res = requests.get(GITHUB_URL)
    releases = res.json()

    pre_release = None
    for release in releases:
        pre_release_status = release.get('prerelease')
        if pre_release_status == True:
            pre_release = release
            break

    return pre_release
    

def get_latest_release_info():
    res = requests.get(GITHUB_URL)
    releases = res.json()

    latest_release = None
    for release in releases:
        draft = release.get('draft')
        prerelease = release.get('prerelease')

        if draft == False and prerelease == False:
            latest_release = release
            break

    id = latest_release.get('id')
    update_content = latest_release.get('body')
    asset = latest_release.get('assets')[0]
    download_url = asset.get('browser_download_url')
    download_size = asset.get('size')

    return {
        'id': id,
        'update_content': update_content,
        'download_url': download_url,
        'download_size': download_size,
        'download_size_formatted': format_bytes(download_size)
    }


def download_update(download_url):
    res = requests.get(download_url, stream=True)
    download_size = int(res.headers.get('Content-Length'))

    start_time = time.time()
    total_downloaded = 0
    with open('update.zip', 'wb') as file:
        for data in res.iter_content(1024):
            chunk_size = len(data)
            total_downloaded += chunk_size

            elapsed = time.time() - start_time
            download_speed = total_downloaded / elapsed if elapsed else 0
            download_percentage = round(total_downloaded / download_size * 100, 2)
            remaining_to_download = download_size - total_downloaded
            remaining_time = round(remaining_to_download / download_speed if download_speed else 0, 2)

            file.write(data)

            yield {
                'total_downloaded': format_bytes(total_downloaded),
                'download_speed': format_bytes(download_speed),
                'remaining_time': remaining_time,
                'download_percentage': download_percentage
            }


def install_update(release_id):
    # Verify there is an update folder to install
    if not os.path.exists('update.zip'):
        return False
    
    for file in APP_FILES.get('files'):
        os.remove(file)

    for folder in APP_FILES.get('folders'):
        shutil.rmtree(folder)

    os.mkdir('update')

    # Unzip the update into new update folder
    with ZipFile('update.zip', 'r') as zip:
        zip.extractall('update/')

    for file in os.listdir('update'):
        # Disregarding update file, as this will be updated from main later
        # Also disregarding persist.json so we don't wipe their data
        if file == UPDATE_EXE_NAME or file == 'persist.json':
            continue

        shutil.move(f'update/{file}', file)

    os.remove('update.zip')

    # Update our persistent data with new release
    persist = PersistentData()
    persist.release_id = release_id
    persist.save()

    # Launch the main app
    subprocess.Popen(MAIN_EXE_NAME)
    return True


def format_bytes(bytes):
    iterated = 0
    while bytes > 1024:
        bytes = bytes / 1024
        iterated += 1

    bytes = round(bytes, 2)
    match iterated:
        case 0:
            return f'{bytes} Bytes'
        case 1:
            return f'{bytes} Kilobytes'
        case 2:
            return f'{bytes} Megabytes'
        case 3:
            return f'{bytes} Gigabytes'
        case 4:
            return f'{bytes} Terabytes'
        case _:
            return f'{bytes} Unknown'