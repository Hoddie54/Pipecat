from fastapi import FastAPI
import subprocess
from pipecat.transports.services.helpers.daily_rest import DailyRESTHelper, DailyRoomParams
import os
import aiohttp
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()
daily_helper = DailyRESTHelper(daily_api_key=os.getenv("DAILY_API_KEY"), aiohttp_session=aiohttp.ClientSession())

@app.post("/bot")
async def start_bot(character_name: str, personality: str, room_url: str):

    bot_token = await daily_helper.get_token(room_url)
    user_token = await daily_helper.get_token(room_url)

    # Launch bot
    subprocess.Popen([
        "python", "./pipecat_project/bot.py",
        "--room_url", room_url,
        "--token", bot_token,
        "--character_name", character_name,
        "--personality", personality
    ])

    return {"room_url": room_url, "user_token": user_token}

@app.post("/room")
async def create_room(name: str):
    params = DailyRoomParams(name=name)
    room = await daily_helper.create_room(params=params)
    print(room.url)
    return {"room_url": room.url}

@app.delete("/room")
async def delete_room(room_url: str):
    return daily_helper.delete_room_from_url(room_url)
   