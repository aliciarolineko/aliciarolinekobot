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
    await event.respond('Funcionando🙃')

@client.on(events.NewMessage(pattern='/compress'))
async def compress(event):
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
async def handler(event):
    code = event.pattern_match.group(1).strip()
    
    if not code:
        await event.reply("Es necesario escribir un código")
        return
    
    url = f'https://es.3hentai.net/d/{code}'
    
    # Accede a la página web
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Captura y edita el nombre de la página
    page_title = soup.title.string
    edited_title = re.sub(r'[^a-zA-Z0-9\[\]]', '', page_title) + f'({code})'
    
    # Enlista las fotos de la página
    a_tags = soup.find_all('a')
    img_urls = [a['href'].replace('t.jpg', '.jpg') for a in a_tags if a.get('href') and a['href'].endswith('.jpg')]
    
    # Descarga las fotos
    img_dir = f'images_{code}'
    os.makedirs(img_dir, exist_ok=True)
    for i, img_url in enumerate(img_urls):
        img_data = requests.get(img_url).content
        with open(os.path.join(img_dir, f'image_{i}.jpg'), 'wb') as img_file:
            img_file.write(img_data)
    
    # Crea un archivo CBZ
    cbz_filename = f'{edited_title}.cbz'
    os.system(f'zip -r {cbz_filename} {img_dir}')
    
    # Envía el archivo CBZ
    await client.send_file(event.chat_id, cbz_filename)
    
    # Limpia los archivos temporales
    os.remove(cbz_filename)
    for img_file in os.listdir(img_dir):
        os.remove(os.path.join(img_dir, img_file))
    os.rmdir(img_dir)

# Variables de entorno para las credenciales de Disroot
DISMAIL = os.getenv('DISMAIL')
DISPASS = os.getenv('DISPASS')

@client.on(events.NewMessage(pattern='/send (.+)'))
async def handler(event):
    if event.is_reply:
        recipient_email = event.pattern_match.group(1)
        if not recipient_email:
            await event.reply("Debe proporcionar el destinatario")
            return
        
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
                # Si el mensaje es solo texto
                body = reply_message.message
                msg.attach(MIMEText(body, 'plain'))
            
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
