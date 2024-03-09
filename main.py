from dotenv import load_dotenv
from telethon import TelegramClient, events, sync
import os 


class TGClient:
    def __init__(self):
        print( os.getenv('API_ID'))
        self.client = TelegramClient(f'TG_{os.getenv("API_ID")}', os.getenv('API_ID'), os.getenv("API_HASH"))
        self.owner = f"@{os.getenv('OWNER')}"
    
    
    def start(self):
        self.client.start()
        
        # Ugly way
        @self.client.on(events.NewMessage(pattern='(?i).*Hello'))
        async def handler(event):
            print("RECEIVED")
            print(event)
            await event.reply("Hi")
        
        self.client.run_until_disconnected()
    
        



if __name__ == "__main__":
    load_dotenv()
    client = TGClient()
    client.start()