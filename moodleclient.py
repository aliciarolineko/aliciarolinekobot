import requests
import json
import urllib
from random import randint
import urllib.parse
import os

def upload_token(filename, token, host):
    token = os.getenv("UPLOAD_TOKEN")
    if not token:
        raise ValueError("Token not found in environment variables")
    
    s = requests.session()
    data = {
        "token": token,
        "itemid": "0",
        "filearea": "draft"
    }
    files = {
        "file": (filename, open(filename, "rb"), "application/x-subrip"),
    }
    resp = s.post(f"{host}/webservice/upload.php", data=data, files=files)
    resp = json.loads(resp.text)[0]
    contextid, itemid, filename = resp["contextid"], resp["itemid"], resp["filename"]
    url = f"{host}/webservice/draftfile.php/{contextid}/user/draft/{itemid}/{urllib.parse.quote(filename)}?token={token}"
    return url

# Ejemplo de uso:
# print(upload_token("requirements.txt", "https://eva.uo.edu.cu"))

