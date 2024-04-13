import logging
import socket
import os 
import tg_notifier.share as s 
class SocketServer:
    def __init__(self,file:str):
        self.file:str=file
        self.s:socket.socket = None
    

    def callback(self,msg:str)->bool:
        logging.info(f"<< {msg}")
        s.MSG_QUEUE.put(msg)
        logging.info(f"{msg} Putted ")
        
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
