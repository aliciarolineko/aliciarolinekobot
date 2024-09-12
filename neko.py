from telethon import TelegramClient, events
import requests
from bs4 import BeautifulSoup
import re
import os
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

client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

print("El bot se ha iniciado, para detenerlo pulse CTRL+C")


# Obtener la lista de usuarios permitidos desde la variable de entorno
allowed_users = os.getenv('USERS').split(',')

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    sender = await event.get_sender()
    username = sender.username

    if username not in allowed_users:
        return
    await event.respond('Funcionando🙃')

compress_in_progress = False

user_comp = {}

@client.on(events.NewMessage(pattern='/setsize (.+)'))
async def set_comp(event):
    sender = await event.get_sender()
    username = sender.username
    valor = event.pattern_match.group(1)
    
    user_comp[username] = int(valor)
    await event.reply(f"Tamaño de archivos {valor} MB registrado para el usuario @{username}")

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

import os
import shutil

# Define la carpeta que deseas limpiar
download_folder = 'descargas'

def clear_folder(folder):
    if os.path.exists(folder):
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(e)

@client.on(events.NewMessage(pattern='/compress'))
async def compress(event):
    global compress_in_progress
    sender = await event.get_sender()
    username = sender.username

    if username not in allowed_users:
        return

    if compress_in_progress:
        await event.respond("El comando está en uso actualmente, espere un poco🙃")
        return

    if event.is_reply:
        reply_message = await event.get_reply_message()
        if reply_message.media:
            try:
                compress_in_progress = True
                await event.respond("Descargando el archivo para comprimirlo...")

                # Crear carpeta temporal
                #temp_dir = "tempcompress"
                #os.makedirs(temp_dir, exist_ok=True)

                # Descargar archivo
                file_path = await client.download_media(reply_message.media, file="server")
                #compressed_file = os.path.join(temp_dir, os.path.basename(file_path) + '.7z')

                await event.respond("Comprimiendo el archivo...")

                try:
                    sizd = user_comp[username]
                except:
                    sizd = 10
                
                # Comprimir archivo
                #with py7zr.SevenZipFile(compressed_file, 'w') as archive:
                #    archive.write(file_path, os.path.basename(file_path))

                # Dividir archivo comprimido
                #parts = split_file(compressed_file, sizd * 1024 * 1024)
                parts = compressfile(file_path, sizd)
                await event.respond(f"Se ha comprimido el archivo en {len(parts)} partes, ahora se enviarán")

                # Enviar partes
                for part in parts:
                    await client.send_file(event.chat_id, part)

                await event.respond("Esas son todas las partes")
                clear_folder("server")
            
                # Limpiar archivos temporales
                #shutil.rmtree(temp_dir)
            except Exception as e:
                await event.respond(f'Error: {str(e)}')
            finally:
                compress_in_progress = False
        else:
            await event.respond('Ejecute el comando respondiendo a un archivo')
    else:
        await event.respond('Ejecute el comando respondiendo a un archivo')

def split_file(file_path, part_size):
    parts = []
    with open(file_path, 'rb') as f:
        part_num = 1
        while True:
            part_data = f.read(part_size)
            if not part_data:
                break
            part_file = f"{file_path}.part{part_num}"
            with open(part_file, 'wb') as part:
                part.write(part_data)
            parts.append(part_file)
            part_num += 1
    return parts
    

command_in_use2 = False

@client.on(events.NewMessage(pattern='/rename (.+)'))
async def rename(event):
    global command_in_use2

    sender = await event.get_sender()
    username = sender.username

    if username not in allowed_users:
        return

    if command_in_use2:
        await event.respond("El comando está en uso actualmente, espere un poco🙃")
        return

    command_in_use2 = True

    if event.is_reply:
        reply_message = await event.get_reply_message()
        if reply_message.media:
            try:
                await event.respond("Descargando el archivo para renombrarlo...")
                new_name = event.pattern_match.group(1)
                file_path = await client.download_media(reply_message.media)
                new_file_path = os.path.join(os.path.diname(file_path), new_name)
                os.rename(file_path, new_file_path)
                await event.respond("Subiendo el archivo con nuevo nombre...")
                await client.send_file(event.chat_id, new_file_path, force_document=True)
                os.remove(new_file_path)
            except Exception as e:
                await event.respond(f'Error: {str(e)}')
        else:
            await event.respond('Ejecute el comando respondiendo a un archivo')
    else:
        await event.respond('Ejecute el comando respondiendo a un archivo')

    command_in_use = False

@client.on(events.NewMessage(pattern='/up'))
async def upmoodle(event):

    sender = await event.get_sender()
    username = sender.username
    if username not in allowed_users:
        return
    if event.is_reply:
        reply_message = await event.get_reply_message()
        if reply_message.media:
            try:
                await event.respond("Descargando el archivo para subir a moodle...")
                filename = await client.download_media(reply_message.media)
                await event.respond("Subiendo el archivo...")
                link = upload_token(filename, os.getenv("NUBETOKEN"), "https://cursad.jovenclub.cu")
                await event.respond("Enlace:\n\n"+link)
            except Exception as ex:
                await event.respond(ex)

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

    
h3_in_use = False

def clean_string(input_string):
    return ''.join(char for char in input_string if char.isalnum() or char in '[]')



@client.on(events.NewMessage(pattern='/h3dl ?(.*)'))
async def download_images(event):
    global h3_in_use
    if h3_in_use:
        await event.reply("El comando está en uso actualmente, espere un poco🙃")
        return

    h3_in_use = True
    sender = await event.get_sender()
    username = sender.username
    codes = event.pattern_match.group(1).split(',')

    if not codes:
        await event.reply("No puedes enviar el comando vacío")
        h3_in_use = False
        return

    total_codes = len(codes)
    for index, code in enumerate(codes, start=1):
        code = clean_string(code.strip())
        url = f"https://es.3hentai.net/d/{code}"

        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            await event.reply(f"Error al acceder a la página: {str(e)}")
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
                await event.reply(f"Error al descargar el archivo {link}: {str(e)}")
                h3_in_use = False
                return

        await event.reply(f"Descargando {code} (Progreso {index}/{total_codes})")

        zip_filename = f"{folder_name}.cbz"
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for root, _, files in os.walk(folder_name):
                for file in files:
                    zipf.write(os.path.join(root, file), arcname=file)

        await client.send_file(event.chat_id, zip_filename)
        await event.reply(f"Archivo {code} descargado, enviando...")

    await event.reply("Todos los archivos CBZ han sido enviados correctamente")
    h3_in_use = False
    






# Variables de entorno para las credenciales de Disroot
DISMAIL = os.getenv('DISMAIL')
DISPASS = os.getenv('DISPASS')

# Diccionario para almacenar los correos electrónicos de los usuarios
user_emails = {}

@client.on(events.NewMessage(pattern='/setmail (.+)'))
async def set_mail(event):
    sender = await event.get_sender()
    username = sender.username
    email = event.pattern_match.group(1)
    
    # Registrar el correo electrónico del usuario
    user_emails[username] = email
    await event.reply(f"Correo electrónico {email} registrado para el usuario @{username}")

sendmail_in_use = False

@client.on(events.NewMessage(pattern='/send'))
async def send_mail(event):
    global sendmail_in_use
    sender = await event.get_sender()
    username = sender.username

    if username not in allowed_users:
        return

    if username not in user_emails:
        await event.reply("Use /setmail para registrar su correo")
        return

    if sendmail_in_use:
        await event.reply("Se está enviando un correo actualmente, espere un poco🙃")
        return

    recipient_email = user_emails[username]

    if event.is_reply:
        # Obtener el mensaje o archivo al que se responde
        reply_message = await event.get_reply_message()
        if not reply_message:
            await event.reply("Debe responder a un mensaje")
            return

        sendmail_in_use = True

        # Conectar al servidor SMTP de Disroot
        try:
            server = smtplib.SMTP('disroot.org', 587)
            server.starttls()
            server.login(DISMAIL, DISPASS)

            # Crear el correo
            msg = MIMEMultipart()
            msg['From'] = "Neko bot <" + DISMAIL + ">"
            msg['To'] = recipient_email
            msg['Subject'] = "Mensaje desde Telegram"

            if reply_message.media:
                # Si el mensaje tiene un archivo adjunto
                await event.reply("Descargando adjunto...")
                file = await reply_message.download_media()
                if os.path.getsize(file) > 11 * 1024 * 1024:  # 11MB en bytes
                    await event.reply("El archivo no debe superar los 11MB, use /compress para reducir el volumen")
                    sendmail_in_use = False
                    return

                attachment = open(file, 'rb')

                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f"attachment; filename= {file}")

                msg.attach(part)
            else:
                await event.reply("Solo se pueden enviar archivos, videos, audios y fotos, no texto.")
                sendmail_in_use = False
                return

            # Enviar el correo
            server.sendmail(DISMAIL, recipient_email, msg.as_string())
            server.quit()

            await event.reply("Correo electrónico enviado correctamente")
        except Exception as e:
            await event.reply(f"Error al enviar el mensaje: {str(e)}")
        finally:
            sendmail_in_use = False
    else:
        await event.reply("Debe responder a un mensaje")

                  
    
client.start()
client.run_until_disconnected()

    
