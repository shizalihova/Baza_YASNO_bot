# Импорты для handlers.py
from .handlers import dp  # Импорт диспетчера
from .handlers import (
    start_command,
    help_command,
    register_command,
    process_callback,
    check_user,
    weather_command,
    process_weather_date,
    unknown_command,
    handle_unknown_message,
)

# Импорты для utils.py
from .utils import (
    set_commands,
    get_from_env,
    read_users_from_sheet,
    save_registration_to_sheet,
    get_weather_forecast,
)