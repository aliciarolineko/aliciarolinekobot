from telethon import TelegramClient, events
import requests
from bs4 import BeautifulSoup
import re
import os
import zipfile
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


# Configura tu API ID y Hash aquí
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('TOKEN')

client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

print("El bot se ha iniciado, para detenerlo pulse CTRL+C")

@client.on(events.NewMessage)
async def handler(event):
    sender = await event.get_sender()
    username = sender.username

    if username not in allowed_users:
        await event.reply('No tienes permitido usar este Bot')
        return

# Obtener la lista de usuarios permitidos desde la variable de entorno
allowed_users = os.getenv('USERS').split(',')

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    sender = await event.get_sender()
    username = sender.username

    if username not in allowed_users:
        await event.reply('No tienes permitido usar este Bot')
        return
    await event.respond('Funcionando🙃')

@client.on(events.NewMessage(pattern='/compress'))
async def compress(event):
    sender = await event.get_sender()
    username = sender.username

    if username not in allowed_users:
        await event.reply('No tienes permitido usar este Bot')
        return
    if event.is_reply:
        reply_message = await event.get_reply_message()
        if reply_message.media:
            try:
                file_path = await client.download_media(reply_message.media)
                compressed_file = file_path + '.rar'
                with zipfile.ZipFile(compressed_file, 'w') as archive:
                    archive.write(file_path, os.path.basename(file_path))
                parts = split_file(compressed_file, 10 * 1024 * 1024)
                for part in parts:
                    await client.send_file(event.chat_id, part)
                os.remove(file_path)
                os.remove(compressed_file)
            except Exception as e:
                await event.respond(f'Error: {str(e)}')
        else:
            await event.respond('Ejecute el comando respondiendo a un archivo')
    else:
        await event.respond('Ejecute el comando respondiendo a un archivo')

@client.on(events.NewMessage(pattern='/rename (.+)'))
async def rename(event):
    sender = await event.get_sender()
    username = sender.username

    if username not in allowed_users:
        await event.reply('No tienes permitido usar este Bot')
        return
    if event.is_reply:
        reply_message = await event.get_reply_message()
        if reply_message.media:
            try:
                new_name = event.pattern_match.group(1)
                file_path = await client.download_media(reply_message.media)
                new_file_path = os.path.join(os.path.dirname(file_path), new_name)
                os.rename(file_path, new_file_path)
                await client.send_file(event.chat_id, new_file_path, force_document=True)
                os.remove(new_file_path)
            except Exception as e:
                await event.respond(f'Error: {str(e)}')
        else:
            await event.respond('Ejecute el comando respondiendo a un archivo')
    else:
        await event.respond('Ejecute el comando respondiendo a un archivo')

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

@client.on(events.NewMessage(pattern='/h3dl ?(.*)'))
async def download_images(event):
    sender = await event.get_sender()
    username = sender.username
    code = event.pattern_match.group(1)

    if not code:
        await event.reply("No puedes enviar el comando vacío")
        return

    url = f"https://es.3hentai.net/d/{code}"

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        await event.reply(f"Error al acceder a la página: {str(e)}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')
    page_title = soup.title.string if soup.title else "sin_titulo"
    folder_name = re.sub(r'[\\/*?:"<>|]', "", page_title)

    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    image_links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.endswith('t.jpg'):
            image_links.append(href.replace('t.jpg', '.jpg'))

    for link in image_links:
        try:
            img_data = requests.get(link).content
            img_name = os.path.join(folder_name, os.path.basename(link))
            with open(img_name, 'wb') as handler:
                handler.write(img_data)
        except Exception as e:
            await event.reply(f"Error al descargar el archivo {link}: {str(e)}")
            return

    zip_filename = f"{folder_name}.cbz"
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for root, _, files in os.walk(folder_name):
            for file in files:
                zipf.write(os.path.join(root, file), arcname=file)

    await client.send_file(event.chat_id, zip_filename)
    await event.reply("Archivo CBZ enviado correctamente")


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

@client.on(events.NewMessage(pattern='/send'))
async def send_mail(event):
    sender = await event.get_sender()
    username = sender.username

    if username not in allowed_users:
        await event.reply('No tienes permitido usar este Bot')
        return

    if username not in user_emails:
        await event.reply("Use /setmail para registrar su correo")
        return

    recipient_email = user_emails[username]

    if event.is_reply:
        # Obtener el mensaje o archivo al que se responde
        reply_message = await event.get_reply_message()
        if not reply_message:
            await event.reply("Debe responder a un mensaje")
            return

        # Conectar al servidor SMTP de Disroot
        try:
            server = smtplib.SMTP('disroot.org', 587)
            server.starttls()
            server.login(DISMAIL, DISPASS)

            # Crear el correo
            msg = MIMEMultipart()
            msg['From'] = DISMAIL
            msg['To'] = recipient_email
            msg['Subject'] = "Mensaje desde Telegram"

            if reply_message.media:
                # Si el mensaje tiene un archivo adjunto
                file = await reply_message.download_media()
                if os.path.getsize(file) > 11 * 1024 * 1024:  # 11MB en bytes
                    await event.reply("No puedes enviar este archivo, debe ser menor a 11MB")
                    return

                attachment = open(file, 'rb')

                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f"attachment; filename= {file}")

                msg.attach(part)
            else:
                await event.reply("Solo se pueden enviar archivos, videos, audios y fotos, no texto.")
                return

            # Enviar el correo
            server.sendmail(DISMAIL, recipient_email, msg.as_string())
            server.quit()

            await event.reply("Mensaje enviado correctamente")
        except Exception as e:
            await event.reply(f"Error al enviar el mensaje: {str(e)}")
    else:
        await event.reply("Debe responder a un mensaje")
                  
    
client.start()
client.run_until_disconnected()
