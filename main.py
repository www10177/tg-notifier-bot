from dotenv import load_dotenv
from telethon import TelegramClient, events, sync
import os 
import socket
from typing import Callable
import threading 
import asyncio
import logging
from queue import Queue
from functools import partial

## Cross Thread Shared Var##
msg_queue = Queue()
#######################
class SocketServer:
    def __init__(self,file:str):
        self.file:str=file
        self.s:socket.socket = None
    

    def callback(self,msg:str)->bool:
        logging.info(f"<< {msg}")
        msg_queue.put(msg)
        
    def setup(self):
        if os.path.exists(self.file):
            os.remove(self.file)
        self.s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.s.bind(self.file)
        logging.info(f"Set Socket at {self.file}")

    def listen(self):
        self.s.listen()
        logging.info("Start Listening Socket")
        while True:
            conn, addr = self.s.accept()

            while True:
                msg = conn.recv(1024)
                if not msg:
                    break  # Client closed connection
                self.callback(msg.decode("utf8").strip())

            conn.close()
            logging.info("Connection closed")
    def close_server(self):
        if self.s:
            self.s.close()
            if os.path.exists(self.file):
                os.remove(self.file)
            logging.info("Socket Server shut down")
    def __del__(self):
        self.close_server()

class TGClient:
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
            if not msg_queue.empty():
                msg = msg_queue.get()
                logging.info(f"<<[from socket]{msg}")
                await self.client.send_message(self.owner, msg)
                logging.info(f">>{msg}")
    def start(self):
        self.client.start()
        self.set_msg_callback()
        self.client.loop.run_until_complete(self.main_loop())
    
        


def start_socket():
    server=  SocketServer('/var/run/tg-notifier/tg-notifier.sock')
    server.setup()
    server.listen()

def start_TG():
    client = TGClient()
    client.start()
    
def set_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(threadName)s]%(message)s"
    )

def main():
    load_dotenv()
    set_logger()
    threads =  [
        threading.Thread(target=start_socket),
        threading.Thread(target=start_TG)
        
    ]
    [t.start() for t in threads]
    [t.join() for t in threads]



if __name__ == "__main__":
    main()