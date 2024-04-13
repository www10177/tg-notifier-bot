import logging
import asyncio
import os 
from telethon import TelegramClient,events
import tg_notifier.share  as s

class TGClient:
    AVAIBLE_USER = ['@www10177']
    def __init__(self):
        self.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.event_loop)
        self.client = TelegramClient(f'TG_{os.getenv("API_ID")}', os.getenv('API_ID'), os.getenv("API_HASH"))
        self.owner = f"@{os.getenv('OWNER')}"
        logging.info("Started TG Client")
        
   
    
    def set_msg_callback(self) :
        @self.client.on(events.NewMessage(from_users=[self.owner]))
        async def handler(event):
            logging.info(f"<<[{self.owner}] : {event}")
            await event.reply("Health")
    async def main_loop(self):
        logging.info("main loop started")
        await self.client.send_message(self.owner, "tg-notifier started up")
        while True :
            if not s.MSG_QUEUE.empty():
                msg = s.MSG_QUEUE.get()
                logging.info(f"<<[from socket]{msg}")
                await self.client.send_message(self.owner, msg)
                logging.info(f">>{msg}")
    def start(self):
        self.client.start()
        self.set_msg_callback()
        self.client.loop.run_until_complete(self.main_loop())
   