import requests
import json
import urllib
from random import randint

def upload_token(filename, token, host):
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

#print(upload_token("requirements.txt", "3e7e0d514c6ea7c7040217a37dcfcc70", "https://eva.uo.edu.cu"))
