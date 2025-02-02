import os
from aiogram import types
from os.path import join, dirname
from dotenv import load_dotenv
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
import httplib2
import logging
import requests

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("telegram_bot_utils")

# Загрузка переменных окружения
def get_from_env(key):
    dotenv_path = join(dirname(__file__), "../token.env")  # Путь к token.env
    load_dotenv(dotenv_path)
    return os.environ.get(key)

# Google Sheets настройки
def get_service_sacc():
    creds_json = os.path.dirname(__file__) + "/../creds/sacc1.json"
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds_service = ServiceAccountCredentials.from_json_keyfile_name(creds_json, scopes).authorize(httplib2.Http())
    return build('sheets', 'v4', http=creds_service)

# Чтение данных из таблицы
def read_users_from_sheet():
    try:
        service = get_service_sacc()
        sheet_id = get_from_env("SHEET_ID")
        sheet = service.spreadsheets()
        resp = sheet.values().batchGet(spreadsheetId=sheet_id, ranges=["L_Users"]).execute()
        data = resp.get('valueRanges', [])[0].get('values', [])
        if data:
            headers = data[0]
            users_dict = {}
            for row in data[1:]:
                if len(row) > 0:
                    user_id = row[0]
                    users_dict[user_id] = {headers[i]: row[i] for i in range(1, min(len(row), len(headers)))}
            return users_dict
        return {}
    except Exception as e:
        logger.error(f"Ошибка при чтении данных из таблицы: {e}")
        return {}

# Запись данных в таблицу
def save_registration_to_sheet(user_id, username, full_name):
    try:
        service = get_service_sacc()
        sheet_id = get_from_env("SHEET_ID")
        values = [[user_id, username, full_name]]
        body = {"values": values}
        sheet = service.spreadsheets()
        sheet.values().append(
            spreadsheetId=sheet_id,
            range="L_Users!A:D",
            valueInputOption="RAW",
            body=body
        ).execute()
        logger.info(f"Данные пользователя {user_id} успешно сохранены.")
    except Exception as e:
        logger.error(f"Ошибка при записи данных в таблицу: {e}")

# Функция для получения прогноза погоды
def get_weather_forecast(lat, lon, api_key):
    url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=ru"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Ошибка при получении данных о погоде: {response.status_code}")
        return None

# Установка команд в интерфейсе бота
async def set_commands(bot):
    commands = [
        types.BotCommand(command="/start", description="Начать общение"),
        types.BotCommand(command="/help", description="Список команд"),
        types.BotCommand(command="/register", description="Регистрация"),
        types.BotCommand(command="/check", description="Проверить регистрацию"),
        types.BotCommand(command="/weather", description="Узнать погоду")
    ]
    try:
        await bot.set_my_commands(commands)
        logger.info("Команды бота успешно установлены.")
    except Exception as e:
        logger.error(f"Ошибка при установке команд: {e}")