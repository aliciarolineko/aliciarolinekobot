from telethon import TelegramClient, events
import requests
from bs4 import BeautifulSoup
import re
import os
import zipfile

# Configura tu API ID y Hash aquí
api_id = '21441504'
api_hash = 'd4f0a90c121e84d3d812eaed96b58e2e'
bot_token = '7283759114:AAHzCm4o_Trsc0tq8NHSphlpW2cF6TsayVI'

client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

print("El bot se ha iniciado, para detenerlo pulse CTRL+C")

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
    img_tags = soup.find_all('img')
    img_urls = [img['src'].replace('t.jpg', '.jpg') for img in img_tags if 't.jpg' in img['src']]
    
    # Descarga las fotos
    img_dir = f'images_{code}'
    os.makedirs(img_dir, exist_ok=True)
    for i, img_url in enumerate(img_urls):
        img_data = requests.get(img_url).content
        with open(os.path.join(img_dir, f'image_{i}.jpg'), 'wb') as img_file:
            img_file.write(img_data)
    
    # Crea un archivo CBZ
    cbz_filename = f'{edited_title}.cbz'
    with zipfile.ZipFile(cbz_filename, 'w') as cbz_file:
        for img_file in os.listdir(img_dir):
            cbz_file.write(os.path.join(img_dir, img_file), img_file)
    
    # Envía el archivo CBZ
    await client.send_file(event.chat_id, cbz_filename)
    
    # Limpia los archivos temporales
    os.remove(cbz_filename)
    for img_file in os.listdir(img_dir):
        os.remove(os.path.join(img_dir, img_file))
    os.rmdir(img_dir)
    
client.start()
client.run_until_disconnected()
