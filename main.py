from dotenv import load_dotenv
import os 
from typing import Callable
import threading 
import asyncio
import logging
from functools import partial

from tg_notifier import SocketServer, TGUserBot, TGClient

        


def start_socket():
    server=  SocketServer(os.environ['SOCKET_PATH'])
    server.setup()
    server.listen()

def start_TGClient():
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
        threading.Thread(target=start_TGClient)
        
    ]
    [t.start() for t in threads]
    [t.join() for t in threads]



if __name__ == "__main__":
    main()