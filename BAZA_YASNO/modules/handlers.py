from aiogram import Dispatcher, types
from aiogram.filters import Command
from .utils import (
    save_registration_to_sheet,
    read_users_from_sheet,
    get_weather_forecast,
    get_from_env,
)
import datetime
import logging

logger = logging.getLogger("telegram_bot_handlers")
dp = Dispatcher()


# Обработчик команды /start
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("Добро пожаловать, я Telegram-бот базы отдыха ЯСНО!) Для просмотра моих команд выберите /help")

# Обработчик команды /help
@dp.message(Command("help"))
async def help_command(message: types.Message):
    await message.answer(
        "Вот список доступных команд:\n"
        "/start - начать общение\n"
        "/help - список команд\n"
        "/register - зарегистрироваться\n"
        "/check - проверить регистрацию\n"
        "/weather - узнать погоду\n"
    )

# Обработчик команды /register
@dp.message(Command("register"))
async def register_command(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="✅ Разрешаю", callback_data="register_yes"),
                types.InlineKeyboardButton(text="❌ Отказываюсь", callback_data="register_no"),
            ]
        ]
    )
    await message.answer(
        "Вы разрешаете передать ваш Telegram ID и имя пользователя для регистрации?",
        reply_markup=keyboard
    )

# Обработчик коллбэков
@dp.callback_query(lambda c: c.data and c.data.startswith('register'))
async def process_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or "unknown"
    full_name = f"{callback_query.from_user.first_name} {callback_query.from_user.last_name or ''}".strip()
    if callback_query.data == "register_yes":
        # Сохраняем данные в таблицу
        save_registration_to_sheet(user_id, username, full_name)
        await callback_query.message.answer("Регистрация прошла успешно!")
    elif callback_query.data == "register_no":
        await callback_query.message.answer("Регистрация отменена.")
    await callback_query.answer()

# Проверка наличия пользователя в таблице
@dp.message(Command("check"))
async def check_user(message: types.Message):
    user_id = str(message.from_user.id)
    users_dict = read_users_from_sheet()
    if user_id in users_dict:
        await message.answer(f"Пользователь {user_id} уже зарегистрирован.")
    else:
        await message.answer(f"Пользователь {user_id} не найден в базе.")

# Обработчик команды /weather
@dp.message(Command("weather"))
async def weather_command(message: types.Message):
    await message.answer("Введите дату в формате DD.MM.YYYY (не позднее чем через 5 дней)")

# Обработчик текстового сообщения после команды /weather
@dp.message(lambda message: len(message.text.split(".")) == 3)  # Проверка формата даты
async def process_weather_date(message: types.Message):
    try:
        # Разбиваем дату на компоненты
        date_parts = message.text.split(".")
        day, month, year = map(int, date_parts)
        # Создаем объект datetime для введенной даты
        user_date = datetime.date(year, month, day)
        # Получаем сегодняшнюю дату
        today = datetime.date.today()
        # Вычисляем разницу в днях
        delta = (user_date - today).days
        # Проверяем, что дата находится в допустимом диапазоне
        if delta < 0:
            await message.answer("Дата должна быть не раньше сегодняшнего дня.")
            return
        elif delta > 5:
            await message.answer("Дата должна быть не позже чем через 5 дней от сегодняшнего дня.")
            return
        # Получаем данные о погоде
        api_key = get_from_env("OPENWEATHER_API_KEY")
        lat = "44.605298"  # Координаты Севастополя
        lon = "33.527107"
        # Запрашиваем прогноз на 5 дней
        weather_data = get_weather_forecast(lat, lon, api_key)
        if not weather_data:
            await message.answer("Не удалось получить данные о погоде.")
            return
        forecast_list = weather_data.get("list", [])
        result = f"Прогноз погоды на {message.text}:\n\n"
        # Фильтруем записи, оставляя только те, которые соответствуют указанной дате
        filtered_forecast = [
            entry for entry in forecast_list
            if datetime.datetime.fromtimestamp(entry["dt"]).date() == user_date
        ]
        # Если прогноз для указанной даты недоступен
        if not filtered_forecast:
            await message.answer("Прогноз на указанную дату недоступен.")
            return
        # Выводим прогноз для каждого 3-часового интервала
        for entry in filtered_forecast:
            temp = entry['main']['temp']  # Температура в °C
            description = entry['weather'][0]['description'].capitalize()
            time = datetime.datetime.fromtimestamp(entry["dt"]).strftime("%H:%M")
            feels_like = entry['main']['feels_like']  # Ощущаемая температура
            humidity = entry['main']['humidity']  # Влажность
            wind_speed = entry['wind']['speed']  # Скорость ветра
            result += (
                f"⏰ {time}\n"
                f"🌡️ Температура: {temp:.1f}°C (ощущается как {feels_like:.1f}°C)\n"
                f"☁️ Описание: {description}\n"
                f"💧 Влажность: {humidity}%\n"
                f"💨 Скорость ветра: {wind_speed} м/с\n\n"
            )
        # Добавляем разделитель в конце
        result += "	"
        await message.answer(result)
    except ValueError:
        await message.answer("Некорректная дата. Пожалуйста, попробуйте снова.")
    except Exception as e:
        logger.error(f"Ошибка при обработке даты: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте снова.")

# Обработчик неизвестных команд
@dp.message(lambda message: message.text.startswith('/'))
async def unknown_command(message: types.Message):
    await message.answer("Извините, такой команды не существует. Используйте /help для просмотра доступных команд.")

# Обработчик для любых других сообщений
@dp.message()
async def handle_unknown_message(message: types.Message):
    await message.answer(
        "Выберите команду из списка. Для просмотра списка команд напишите /help"
    )