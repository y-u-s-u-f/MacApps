import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

date_string = datetime.now().strftime("%Y-%m-%d")

def get_free_apps():
    url = f"https://appadvice.com/apps-gone-free/{date_string}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    free_apps = soup.find_all('div', class_='aa_app__icon aa_bg aa_bg-888--1')
    app_list = []

    for app in free_apps:
        app_name = app.find('img').get('alt')
        app_list.append(app_name)

    half_length = len(app_list) // 2
    app_list = app_list[:half_length]

    return app_list

def send_to_discord(app_list):
    webhook_url = "https://discord.com/api/webhooks/1193700195322560543/1dvD02JlbTVS9Xxu0zpE3Ez2GUN95n_BVMDTC3v8vzJ7xAc1ULtNYTBSZpVMEo3NgB2e"
    data = {}
    data["embeds"] = []
    embed = {}
    embed["title"] = "Todays Apps Gone Free"
    embed["description"] = "\n".join(app_list)
    embed["color"] = int("5384EC", 16)
    embed["footer"] = {"text": f"https://appadvice.com/apps-gone-free/{date_string}",
                        "icon_url": "https://media.licdn.com/dms/image/C560BAQGLpOtO6VB09Q/company-logo_200_200/0/1630663861224/appadvice_logo?e=2147483647&v=beta&t=wbZXD3hheDKs6TMWU3rINJCsFa0R5zufCLDlaN1tRwk"}
    embed["timestamp"] = datetime.utcnow().isoformat()
    data["embeds"].append(embed)
    result = requests.post(webhook_url, data=json.dumps(data), headers={"Content-Type": "application/json"})



app_list = get_free_apps()
send_to_discord(app_list)
