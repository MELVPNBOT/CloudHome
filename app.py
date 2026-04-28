import asyncio
import json
import random
import string
import threading
import aiohttp
import os
from flask import Flask
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.bot import DefaultBotProperties

# --- КОНФИГУРАЦИЯ ---
API_TOKEN = '8635677711:AAF1VuX3AqiAUUXp5ZHcZXNSn6THDpOC0eY'
ADMIN_ID = 7768798243
GITHUB_TOKEN = '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'
REPO = 'MELVPNBOT/lolvpnsite'
FILE_PATH = 'code.json'

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode='Markdown'))
dp = Dispatcher()
app = Flask(__name__)

@app.route('/')
def home(): 
    return "🌐 VPN Bot is Running", 200

def run_web():
    # Render требует порт 10000
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- УЛУЧШЕННАЯ ЛОГИКА GITHUB ---
async def update_github_json(new_code):
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    async with aiohttp.ClientSession() as session:
        try:
            # 1. Получаем текущий файл
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    print(f"Ошибка получения файла: {resp.status}")
                    return False
                data = await resp.json()
                sha = data['sha']
                # Декодируем содержимое
                content_raw = aiohttp.helpers.b64decode(data['content']).decode('utf-8')
                content = json.loads(content_raw)

            # 2. Добавляем новый ключ
            content.append({"code": new_code, "activations": 1})
            new_json_str = json.dumps(content, indent=2)
            new_content_b64 = aiohttp.helpers.b64encode(new_json_str.encode('utf-8')).decode('utf-8')

            # 3. Отправляем обновление обратно
            payload = {
                "message": f"🤖 Авто-создание ключа: {new_code}",
                "content": new_content_b64,
                "sha": sha
            }
            async with session.put(url, headers=headers, json=payload) as resp:
                if resp.status in [200, 201]:
                    return True
                else:
                    print(f"Ошибка сохранения на GitHub: {resp.status}")
                    return False
        except Exception as e:
            print(f"Критическая ошибка GitHub: {e}")
            return False

# --- КЛАВИАТУРЫ ---
def get_main_kb(user_id):
    buttons = [
        [KeyboardButton(text="💎 Купить ВПН"), KeyboardButton(text="🚀 Подключить впн")],
        [KeyboardButton(text="🎁 Тестовый впн")]
    ]
    if user_id == ADMIN_ID:
        buttons.append([KeyboardButton(text="🔑 Выдать ключ")])
    
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# --- ОБРАБОТЧИКИ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 *Добро пожаловать в MEL VPN!*\n\nВыбирай нужный раздел в меню ниже:",
        reply_markup=get_main_kb(message.from_user.id)
    )

@dp.message(F.text == "💎 Купить ВПН")
async def cmd_buy(message: types.Message):
    await message.answer("💳 Для покупки ВПН напишите нашему менеджеру: @sanek37r")

@dp.message(F.text == "🎁 Тестовый впн")
async def cmd_test(message: types.Message):
    await message.answer("⚠️ Тестовый период временно *отключен*.")

@dp.message(F.text == "🚀 Подключить впн")
async def cmd_connect(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Перейти на сайт", url="https://lolvpnsub.vercel.app/code.html")]
    ])
    await message.answer(
        "🛠 *Инструкция:*\n\n1. Перейдите на сайт по кнопке ниже.\n2. Введите ваш ключ, полученный при покупке.\n3. Следуйте шагам на странице.",
        reply_markup=kb
    )

@dp.message(F.text == "🔑 Выдать ключ")
async def cmd_admin_key(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    # Генерация красивого ключа
    new_key = "MEL-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    status_msg = await message.answer("🔄 *Связываюсь с сервером GitHub...*")
    
    success = await update_github_json(new_key)
    
    if success:
        await status_msg.edit_text(
            f"✅ *Ключ успешно создан!*\n\n🔑 Ключ: `{new_key}`\n🌐 Он уже доступен для активации на сайте."
        )
    else:
        await status_msg.edit_text("❌ *Ошибка!*\nНе удалось обновить файл на GitHub. Проверьте логи сервера.")

# --- ЗАПУСК ---
async def main():
    # Запускаем Flask в отдельном потоке
    threading.Thread(target=run_web, daemon=True).start()
    
    print("🤖 Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен")
