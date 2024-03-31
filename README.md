# TG Notifier Bot
**Still in early development.**  
This program would create a socket and listen to it.  
If any message sent to the socket, it would sent telegram message to the OWNER in env.  

- install dependency using poetry
- set all environment variable in `.env.example` or save them  as file `.env` in the same folder
  - API_KEY and API_HASH are NOT in bot api, GET it from [here](https://docs.telethon.dev/en/stable/basic/signing-in.html#signing-in)
- you could also set as system daemon
- Connect to socker: `nc -U SOCKET_PATH `




