import logging
import asyncio
import os 

import socket
import tg_notifier.share as s 
from tg_notifier.common import *
from http import HTTPStatus
from telegram import Bot, Update, ReplyKeyboardMarkup,ReplyKeyboardRemove
from telegram.constants import ChatType
from telegram.ext import Application,CommandHandler
import uvicorn
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route
import duckdb
import json


"""Socket Format, in Json
check TGUserBot.send_msg for details
{
    "to" : Telegram username, 
    "msg" : Message that sent to user,
    "silent" : bool, disable notification sound or not 
}


"""


class WebhookUpdate:
    """Simple dataclass to wrap a custom update type"""
    user_id: int
    payload: str

WEB_PAYLOAD_API_KEY="OuOv!@#vOuO"
ADMIN_USERNAME = "www10177"
ADMIN_USERS= [
    476980473,  #www10177
]
class TGUserBot:
    def __init__(self):
        self.env= os.environ
        logging.info("Started TG Bot")
        
        self.app = Application.builder().token(self.env['USER_BOT_TOKEN']).build()
        self.event_loop = asyncio.new_event_loop()
        self.db= duckdb.connect(os.environ.get("DUCKDB_PATH"))
        asyncio.set_event_loop(self.event_loop)
        logging.info("Stuck at ayncio")
        
    async def cmd_start(self,update:Update,context):
        logging.info(f"<<[TG_Start] ", {update})
        userid=update.message.from_user.id
        username=update.message.from_user.username
        isAdmin= "true" if userid in ADMIN_USERS else "false"
        print(type(userid))
        logging.info(f"Add to DB: {userid},{username},{isAdmin}")
        self.db.execute("INSERT OR REPLACE INTO TGUser(TGUserName, TGUserID, IsAdmin) VALUES (?,?,?)",(username,userid,isAdmin))
        await update.message.reply_text(f"Hi {update.message.from_user.full_name}🥰🥰🥰(@{username}, {userid})")
        
    
    async def setup_tg(self):
        self.app.add_handler(CommandHandler("start",self.cmd_start))
        await self.app.bot.set_webhook(url=self.env['URL'], allowed_updates=Update.ALL_TYPES)
        logging.info("Setuped webhook")

    async def web_request(self,request: Request) -> Response:
        """Handle incoming Telegram updates by putting them into the `update_queue`"""
        await self.app.update_queue.put(
            Update.de_json(data=await request.json(), bot=self.app.bot)
        )
        return Response()

    async def web_payload(self,request: Request) -> PlainTextResponse:
        """
        Handle incoming webhook updates by also putting them into the `update_queue` if
        the required parameters were passed correctly.
        """
        try:
            user_id = int(request.query_params["user_id"])
            payload = request.query_params["payload"]
            apikey= request.query_params.get("apikey",'')
            if apikey !=WEB_PAYLOAD_API_KEY:
                return PlainTextResponse(
                    status_code=HTTPStatus.BAD_REQUEST,
                    content="Wrong API KEY",
                )
        except KeyError:
            return PlainTextResponse(
                status_code=HTTPStatus.BAD_REQUEST,
                content="Please pass both `user_id` and `payload` as query parameters.",
            )
        except ValueError:
            return PlainTextResponse(
                status_code=HTTPStatus.BAD_REQUEST,
                content="The `user_id` must be a string!",
            )

        await self.app.update_queue.put(WebhookUpdate(user_id=user_id, payload=payload))
        return PlainTextResponse("Thank you for the submission! It's being forwarded.")

    async def web_health(self, req: Request) -> PlainTextResponse:
        """For the health endpoint, reply with a simple plain text message."""
        host = req.headers.get('x-forwarded-for','NULL')
        await self.send_msg(to=ADMIN_USERNAME, msg=f"Health Check from {host}")
        return PlainTextResponse(content="The bot is still running fine :)")
    
    async def web_sockethealth(self, req: Request) -> PlainTextResponse:
        host = req.headers.get('x-forwarded-for','NULL')
        msg= json.dumps({
            "to":ADMIN_USERNAME, 
            "msg":f"Socket Health Check from {host}"})
        socket_path = os.environ.get("SOCKET_PATH","MISSING_PATH")
        try : 
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.connect(socket_path)
            s.send(str(msg).encode('ascii'))
            content=f"Socket Should be run correctly, {socket_path}.\n PAYLOAD : {msg}"
        except Exception as e :
            content=f"OOPS, PATH={os.environ['SOCKET_PATH']}, ERR: {e}"
        return PlainTextResponse(content=content)

    async def checking_queue(self) :
        await self.send_msg(to=ADMIN_USERNAME, msg="Service is up")
        try :
            while True :
                if not s.MSG_QUEUE.empty():
                    msg = s.MSG_QUEUE.get()
                    logging.info(f"<<[from socket]{msg}")
                    try: 
                        await self.send_msg(**json.loads(msg))
                    except json.JSONDecodeError as e :
                        msg = dict(
                            to=ADMIN_USERNAME,
                            msg="JSON_DECODE_ERROR\nMessage: " + msg
                                )
                        await self.send_msg(msg)
                        logging.fatal(f"JSON {type(e)}: {e}")
                    except Exception as e :
                        await self.send_msg(to=ADMIN_USERNAME,msg=f"Exception:\n{msg}")
                        logging.fatal(f"EXCEPTION {type(e)}: {e}")
                    finally:
                        s.MSG_QUEUE.task_done()
                await asyncio.sleep(3)
        except Exception as e :
            logging.fatal(f"OUTER EXCEPTION {type(e)}: {e}")

    async def send_msg(self,to:str=ADMIN_USERNAME, msg:str="MSG_NOT_FOUND",silent:bool=True,**kwargs):
        """Send tg Message to user 

        Args:
            to (str, optional): tg username . Defaults to ADMIN_USERNAME.
            msg (str, optional): text to sent. Defaults to "MSG_NOT_FOUND".
            silent (bool, optional): diable notification sound or not. Defaults to False.
        """
        rows  = self.db.execute("SELECT TGUserId, IsAdmin from TGUser where TGUserName == ?",[to] ).fetchall()
        for k, v in kwargs:
            msg += f'\n({k}): {v}'
        for userid, isAdmin in rows:
            await self.app.bot.send_message(chat_id=userid, text=msg,disable_notification=silent)
            logging.info(f">>[{userid}]{msg}")
        

    async def _start(self):
        logging.info("__start")
        await self.setup_tg()
        route = '/'
        starlette_app = Starlette( routes=[
                Route(f'{route}', self.web_request, methods=["POST"]),
                Route(f"{route}", self.web_health, methods=["GET"]),
                Route(f"{route}/healthcheck", self.web_health, methods=["GET"]),
                Route(f"{route}/sockethealth", self.web_sockethealth, methods=["GET"]),
                Route(f"{route}/custom", self.web_payload, methods=["POST", "GET"]),
            ]
        )
        webserver = uvicorn.Server(
            config=uvicorn.Config(
                app=starlette_app,
                port=int(self.env['PORT']),
                use_colors=False,
                host=self.env['IP'],
            )
        )

        async with self.app:
            logging.debug("WEBSERVER Started")
            await self.app.start()
            checking_queue = asyncio.create_task(self.checking_queue())
            webserver = asyncio.create_task(webserver.serve())
            await webserver
            await checking_queue
            await self.app.stop()

    def start(self):
        logging.debug("START")
        self.event_loop.run_until_complete(self._start())
