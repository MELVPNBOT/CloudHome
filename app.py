import asyncio
import json
import random
import string
import threading
import aiohttp
from flask import Flask
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

API_TOKEN = '8635677711:AAF1VuX3AqiAUUXp5ZHcZXNSn6THDpOC0eY'
ADMIN_ID = 7768798243
GITHUB_TOKEN = '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'
REPO = 'MELVPNBOT/lolvpnsite'
FILE_PATH = 'code.json'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
app = Flask(__name__)

@app.route('/')
def home(): return "I'm alive", 200

def run_v(): app.run(host='0.0.0.0', port=10000) # Render использует порт 10000

async def update_github(code):
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    async with aiohttp.ClientSession() as s:
        async with s.get(url, headers=headers) as r:
            if r.status != 200: return False
            d = await r.json()
            c = json.loads(aiohttp.helpers.b64decode(d['content']).decode())
        c.append({"code": code, "activations": 1})
        upd = aiohttp.helpers.b64encode(json.dumps(c, indent=2).encode()).decode()
        payload = {"message": "new key", "content": upd, "sha": d['sha']}
        async with s.put(url, headers=headers, json=payload) as r:
            return r.status == 200

@dp.message(Command("start"))
async def s(m: types.Message):
    kb = [
        [KeyboardButton(text="Купить ВПН"), KeyboardButton(text="Подключить впн")],
        [KeyboardButton(text="Тестовый впн")]
    ]
    if m.from_user.id == ADMIN_ID: kb.append([KeyboardButton(text="Выдать ключ")])
    await m.answer("MEL VPN работает!", reply_markup=ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True))

@dp.message(F.text == "Купить ВПН")
async def b(m: types.Message): await m.answer("Купить у @sanek37r")

@dp.message(F.text == "Тестовый впн")
async def t(m: types.Message): await m.answer("отключен")

@dp.message(F.text == "Выдать ключ")
async def g(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    key = "GIFT-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    if await update_github(key): await m.answer(f"Ключ: `{key}`", parse_mode="Markdown")
    else: await m.answer("Ошибка")

async def main():
    threading.Thread(target=run_v, daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
