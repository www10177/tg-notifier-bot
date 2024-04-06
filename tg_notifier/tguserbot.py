import logging
import asyncio
import os 

import  tg_notifier.share as s 
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

class WebhookUpdate:
    """Simple dataclass to wrap a custom update type"""
    user_id: int
    payload: str

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
            if apikey !='OuOvwwwvOuO':
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

    async def web_health(self, _: Request) -> PlainTextResponse:
        """For the health endpoint, reply with a simple plain text message."""
        return PlainTextResponse(content="The bot is still running fine :)")

    async def checking_queue(self) :
        while True :
            if not s.MSG_QUEUE.empty():
                try: 
                    msg = s.MSG_QUEUE.get()
                    logging.info(f"<<[from socket]{msg}")
                    result = await self.handle_with_socket_msg(json.loads(msg))
                    logging.info(f"DONE")
                except Exception as e :
                    logging.fatal(f"EXCEPTION: {e}")
                
            await asyncio.sleep(0.5)

    async def handle_with_socket_msg(self,msg:dict):
        user = msg.get("user","")
        msg= msg.get("msg","")
        rows  = self.db.execute("SELECT TGUserId, IsAdmin from TGUser where TGUserName == ?",[user] ).fetchall()
        for userid, isadmin in rows:
            await self.app.bot.send_message(chat_id=userid, text=msg)
            logging.info(f">>[{userid}]{msg}")
        

    async def _start(self):
        logging.info("__start")
        await self.setup_tg()
        route = ''
        starlette_app = Starlette( routes=[
                Route(f'{route}/', self.web_request, methods=["POST"]),
                Route(f'{route}/', self.web_health, methods=["GET"]),
                Route(f"{route}/healthcheck", self.web_health, methods=["GET"]),
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
            await self.app.stop()

    def start(self):
        logging.debug("START")
        self.event_loop.run_until_complete(self._start())