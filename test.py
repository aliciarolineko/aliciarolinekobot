from telethon import TelegramClient, events
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

client.start()
client.run_until_disconnected()
