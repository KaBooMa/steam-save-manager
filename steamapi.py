import requests, json

STEAM_APPLIST_URL = 'https://api.steampowered.com/ISteamApps/GetAppList/v2/'

def get_app_list():
    res = requests.get(STEAM_APPLIST_URL)
    apps = res.json().get('applist').get('apps')
    apps_dict = {app.get('appid'):app.get('name') for app in apps}
    # organized_apps = {appid:name for appid, name in sorted(apps_dict.items(), key=lambda item: item[1])}
    return apps_dict