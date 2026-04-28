import asyncio
import aiohttp
import os
import threading
import json
import random
import string
from flask import Flask
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.bot import DefaultBotProperties

# --- КОНФИГУРАЦИЯ ---
API_TOKEN = '8635677711:AAF1VuX3AqiAUUXp5ZHcZXNSn6THDpOC0eY'
# Ссылка на RAW JSON для проверки ключей
JSON_URL = "https://raw.githubusercontent.com/MELVPNBOT/lolvpnsite/refs/heads/main/code.json"

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode='Markdown'))
dp = Dispatcher()
app = Flask(__name__)

class Form(StatesGroup):
    waiting_for_key = State()

@app.route('/')
def home(): return "Бот работает", 200

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- ГЛАВНОЕ МЕНЮ ---
def main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="💎 Купить ВПН"), KeyboardButton(text="🚀 Подключить впн")]
    ], resize_keyboard=True)

# --- ОБРАБОТЧИКИ ---

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("👋 Привет! Я бот *MEL VPN*.\n\nНажми на кнопку ниже, чтобы начать.", reply_markup=main_kb())

@dp.message(F.text == "🚀 Подключить впн")
async def connect_step_1(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Перейти на сайт", url="https://lolvpnsub.vercel.app/code.html")],
        [InlineKeyboardButton(text="➡️ Продолжить в боте", callback_data="choice_os")]
    ])
    await message.answer("Выберите способ настройки:", reply_markup=kb)

@dp.callback_query(F.data == "choice_os")
async def choice_os(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Android", callback_data="os_android"), InlineKeyboardButton(text="🍎 iOS (iPhone/iPad)", callback_data="os_ios")],
        [InlineKeyboardButton(text="💻 Windows", callback_data="os_win")],
        [InlineKeyboardButton(text="🍏 Mac OS", callback_data="os_mac"), InlineKeyboardButton(text="🐧 Linux", callback_data="os_linux")]
    ])
    await callback.message.edit_text("📱 **Выберите ваше устройство:**", reply_markup=kb)

@dp.callback_query(F.data.startswith("os_"))
async def choice_app(callback: types.CallbackQuery):
    # Для всех систем предлагаем Happ
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Happ", callback_data="app_happ")]
    ])
    await callback.message.edit_text("✨ Выберите приложение для установки:", reply_markup=kb)

@dp.callback_query(F.data == "app_happ")
async def ask_key(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🔑 **Введите ваш ключ активации:**\n\nБот проверит его по базе данных.")
    await state.set_state(Form.waiting_for_key)

@dp.message(Form.waiting_for_key)
async def check_key(message: types.Message, state: FSMContext):
    user_key = message.text.strip()
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(JSON_URL) as resp:
                if resp.status != 200:
                    await message.answer("❌ Ошибка соединения с базой ключей.")
                    return
                
                data = await resp.json()
                # Проверка: есть ли введенный код в JSON файле
                is_valid = any(item.get('code') == user_key for item in data)

                if is_valid:
                    # Ссылки на скачивание
                    kb_list = [
                        [InlineKeyboardButton(text="➕ Добавить подписку", url="https://melvpnbot.github.io/CloudHome/")],
                        [InlineKeyboardButton(text="📥 Скачать для Android", url="https://play.google.com/store/apps/details?id=com.happproxy&hl=ru")],
                        [InlineKeyboardButton(text="📥 Скачать для iOS", url="https://apps.apple.com/ru/app/happ-proxy-utility-plus/id6746188973")],
                        [InlineKeyboardButton(text="📥 Скачать для Windows", url="https://github.com/Happ-proxy/happ-desktop/releases/download/2.9.1/setup-Happ.x64.exe")],
                        [InlineKeyboardButton(text="📥 Скачать для Mac OS", url="https://github.com/Happ-proxy/happ-desktop/releases/download/2.9.1/Happ.macOS.universal.dmg")],
                        [InlineKeyboardButton(text="📥 Скачать для Linux", url="https://github.com/Happ-proxy/happ-desktop/releases/download/2.9.1/Happ.linux.arm64.deb")]
                    ]

                    await message.answer(
                        f"✅ **Ключ `{user_key}` успешно активирован!**\n\nНиже представлены ссылки на приложение Happ для всех платформ и кнопка для добавления вашей подписки.",
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_list)
                    )
                    await state.clear()
                else:
                    await message.answer("❌ **Ключ недействителен.**\n\nПроверьте правильность ввода или купите новый ключ у @sanek37r.")
        except Exception as e:
            await message.answer(f"⚠️ Произошла ошибка: {e}")

async def main():
    threading.Thread(target=run_web, daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
