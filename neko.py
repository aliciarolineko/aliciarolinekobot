from pyrogram import Client
import requests
from bs4 import BeautifulSoup
import re
import os
import shutil
import zipfile
import py7zr
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase 
from email import encoders
from moodleclient import upload_token

# Configura tu API ID y Hash aquí
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('TOKEN')

bot = Client('bot', api_id=api_id, api_hash=api_hash, bot_token=bot_token)

print("El bot se ha iniciado, para detenerlo pulse CTRL+C")


# Obtener la lista de usuarios permitidos desde la variable de entorno
allowed_users = os.getenv('USERS').split(',')

DISMAIL = os.getenv('DISMAIL')
DISPASS = os.getenv('DISPASS')

sendmail_in_use = False
command_rename = False
compress_in_progress = False
h3_in_use = False

user_comp = {}
user_emails = {}

def compressfile(filename, sizd):
    maxsize = 1024 * 1024 * sizd
    mult_file =  zipfile.MultiFile(filename+'.7z', maxsize)
    zip = zipfile.ZipFile(mult_file,  mode='w', compression=zipfile.ZIP_DEFLATED)
    zip.write(filename)
    zip.close()
    mult_file.close()
    files = []
    for part in zipfile.files:
        files.append(part)
    return files

@bot.on_message()
async def commands(client, message):
	text = message.text
	username = message.from_user.username
	if not username in allowed_users:
		return
	if text.startswith("/start"):
		await message.reply("Funcionando🙃")
	elif text.startswith("/rename"):
		global command_rename
		if command_rename:
		    	await message.reply("El comando está en uso actualmente, espere un poco🙃")
		    	return
		command_rename = True
		replied_message = message.reply_to_message
		if replied_message:
		    	await message.reply("Descargando el archivo para renombrarlo...")
		    	new_name = text.split(" ")[1]
		    	file_path = await client.download_media(replied_message.document.file_id)
		    	new_file_path = os.path.join(os.path.dirname(file_path), new_name)
		    	os.rename(file_path, new_file_path)
		    	await message.reply("Subiendo el archivo con nuevo nombre...")
		    	await client.send_document(chat_id=message.chat.id, document=new_file_path)
		    	os.remove(new_file_path)
		    	command_rename = False
	elif text.startswith("/setsize"):
		valor = text.split(" ")[1]
		user_comp[username] = int(valor)
		await message.reply(f"Tamaño de archivos {valor} MB registrado para el usuario @{username}")
	elif text.startswith("/compress"):
		global compress_in_progress
		if compress_in_progress:
			await message.reply("El comando está en uso actualmente, espere un poco🙃")
			return
		replied_message = message.reply_to_message
		if replied_message:
			compress_in_progress = True
			os.system("rm -rf ./server/*")
			await message.reply("Descargando el archivo para comprimirlo...", "server")
			file_path = await client.download_media(replied_message.document.file_id)
			await message.reply("Comprimiendo archivo...")
			try: sizd = user_comp[username]
			except: sizd = 10
			parts = compressfile(file_path, sizd)
			await message.reply("Enviando archivos...")
			for part in parts:
				try:
					client.send_document(chat_id=message.chat.id, document=part)
				except:pass
			await message.reply("Completado")
			compress_in_progress = False
	elif text.startswith("/up"):
		replied_message = message.reply_to_message
		if replied_message:
			await message.reply("Descargando...")
			file_path = await client.download_media(replied_message.document.file_id)
			await message.reply("Subiendo a la nube...")
			link = upload_token(filename, os.getenv("NUBETOKEN"), "https://cursad.jovenclub.cu")
			await message.reply("Enlace:\n"+link)
	elif text.startswith("/setmail"):
		user_emails[username] = text.split(" ")[1]
		await message.reply(f"Correo electrónico registrado para el usuario @{username}")

	elif text.startswith("/h3dl"):
		global h3_in_use
                hcode = text.split(" ")
                if hdl_in_progress:
                    await message.reply("El comando está en uso actualmente, espere un poco🙃")
                    return
                elif not hcode:
                    await message.reply("No puedes enviar el comando vacío")
                    h3_in_use = False
                    return
                await message.reply(f"Buscando imagenes de {hcode}")
                h3_in_use = True
                url = f"https://es.3hentai.net/d/{hcode}"
                try:
                                        response = requests.get(url)
                                        response.raise_for_status()
                except requests.exceptions.RequestException as e:
                                        await message.reply(f"Error al acceder a la página: {str(e)}")
                                        h3_in_use = False
                                        return
                                        soup = BeautifulSoup(response.content, 'html.parser')
                                        page_title = soup.title.string if soup.title else "sin_titulo"
                                        folder_name = clean_string(re.sub(r'[\\/*?:"<>|]', "", page_title))
                                        if not os.path.exists(folder_name):
                                        	os.makedirs(folder_name)
                                        	image_links = []
                                        	for img in soup.find_all('img'):
                                        		src = img.get('src')
                                        		if src and src.endswith('t.jpg'):
                                        			image_links.append(src.replace('t.jpg', '.jpg'))
                                        			for link in image_links:
                                        			 	try:
                                        			 		img_data = requests.get(link).content
                                        			 		img_name = os.path.join(folder_name, os.path.basename(link))
                                        			 		with open(img_name, 'wb') as handler:
                                        			 			handler.write(img_data)
                                        			 	except Exception as e:
                                        			 	   await message.reply(f"Error al descargar el archivo {link}: {str(e)}")
                                        			 	   h3_in_use = False
                                        			 	   return
                                        			 	message.reply(f"Creando un CBZ")
                                        			 	zip_filename = f"{folder_name}.cbz"
                                        			 	with zipfile.ZipFile(zip_filename, 'w') as zipf:
                                        			 	             for root, _, files in os.walk(folder_name):
                                        			 	             	for file in files:
                                        			 	             		zipf.write(os.path.join(root, file), arcname=file)
                                        			 	             		await message.send_document(chat_id=message.chat.id, document=zip_filename)
                                        			 	             		await message.reply(f"Archivo {hcode} descargado, enviando...")
                                        			 	             		await message.reply(f"Las imagenesn de {hcode} fueron enviadas en un CBZ correctamente")
                                        			 	             h3_in_use = False
	elif text.startswith("/send"):
	       global sendmail_in_use
	       if sendmail_in_use:
	           await message.reply("Se está enviando un correo actualmente, espere un poco🙃")
	           return
	       recipient_email = user_emails[username]
	       server = smtplib.SMTP('disroot.org', 587)
	       server.starttls()
	       server.login(DISMAIL, DISPASS)
	       msg = MIMEMultipart()
	       msg['From'] = "Neko bot <" + DISMAIL + ">"
	       msg['To'] = recipient_email
	       msg['Subject'] = "Mensaje desde Telegram"
	       replied_message = message.reply_to_message
	       if replied_message:
	          sendmail_in_use = True
	          await message.reply("Descargando...")
	          file = client.download_media(replied_message.document.file_id)
	          if os.path.getsize(file) > 11 * 1024 * 1024:
	              await message.reply("El archivo no puede superar los 11 MB, use /compress para reducirlo")
	              sendmail_in_use = False
	              return
	          attachment = open(file, 'rb')
	          part = MIMEBase('application', 'octet-stream')
	          part.set_payload(attachment.read())
	          encoders.encode_base64(part)
	          part.add_header('Content-Disposition', f"attachment; filename= {file}")
	          msg.attach(part)
	          server.sendmail(DISMAIL, recipient_email, msg.as_string())
	          server.quit()
	          await message.reply("Correo enviado con éxito")
                                                  
def split_file(file_path, part_size):
    parts = []
    with open(file_path, 'rb') as f:
        part_num = 0
        while True:
            part_data = f.read(part_size)
            if not part_data:
                break
            part_file = f"{file_path}.part{part_num}"
            with open(part_file, 'wb') as part_f:
                part_f.write(part_data)
            parts.append(part_file)
            part_num += 1
    return parts


def clean_string(input_string):
    return ''.join(char for char in input_string if char.isalnum() or char in '[]')
    
bot.run()
