import logging
import random
import asyncio
from datetime import datetime, time as dtime, timedelta
from zoneinfo import ZoneInfo
from telegram import Bot
from telegram.ext import Application

# ================== НАСТРОЙКИ ==================
TOKEN = "8941613345:AAHpkoBvptRPVLt1QCaGW2dKhPD_wPIDYjA"
CHAT_ID = -1004297426958
THREAD_ID = 3

# Обновленный шаблон
MESSAGE_TEMPLATE = """Время: {time}

Сумма: {number}$ | Статус: ACCEPTED

ID: {id} | Воркер: {worker}"""

MIN_NUMBER = 92
MAX_NUMBER = 1349

# Случайный интервал между отправками (в секундах)
MIN_INTERVAL = 900    # 15 минут
MAX_INTERVAL = 2700   # 45 минут

# Окно СТАРТА (МСК)
START_WINDOW_START = dtime(9, 19)
START_WINDOW_END   = dtime(9, 27)

# Окно ЗАВЕРШЕНИЯ (последняя отправка не позже этого момента, МСК)
END_WINDOW_START = dtime(20, 42)
END_WINDOW_END   = dtime(20, 56)

MSK = ZoneInfo("Europe/Moscow")

# Список ников (15 первых + 31 новых = 46 штук)
WORKER_NAMES = [
    # Ваши первые 15
    "foreverstro", "Killbil", "mindkast", "kkoppx", "jelosyhe", "hero_ew",
    "gerroinoll", "WorK1ng_ever", "loower1_00", "jastcallme", "secretpers",
    "geniusPe22", "forager_for", "WexOn", "11pxcvee",
    
    # Ваши новые 31
    "toller_2gol", "7evengGodd", "Holycell", "jffeuu", "kendric0", 
    "yedraggs", "kopovich_t2k", "vol0fHer", "ivoxxP", "vkkkey66", 
    "personalde", "aw1qaw_j", "hcr44_lolls", "dsNchik", "ursulcallme", 
    "genifer_us", "snex42", "napapijri812", "wellwornndd", "fF_fainwax", 
    "Romerio1422", "mxmxs0909", "alexsanderlitovsky", "chto_za_trus666", 
    "afganec771", "ARESTOBAN_ZA_SWAT_MAGAZINA", "ggf554", 
    "krovnaasphalte", "fruktodaaad", "aliemazoyka_tg", "HUGOBOSS112"
]
# ===============================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- Вспомогательные функции для генерации данных ---

def generate_random_id() -> str:
    """Генерирует случайное число от 5 до 7 знаков и добавляет ** в конец"""
    random_num = random.randint(10000, 9999999)
    return f"{random_num}**"

def generate_worker_name() -> str:
    """Выбирает случайный ник и заменяет последние 30-40% букв на звезды."""
    chosen_name = random.choice(WORKER_NAMES)
    name_len = len(chosen_name)
    
    # Вычисляем 30-40% от длины слова
    percent = random.randint(30, 40) / 100
    chars_to_replace = max(1, int(name_len * percent))
    
    # Отрезаем часть, которую оставляем, и добавляем звездочки
    visible_part = chosen_name[:-chars_to_replace]
    stars = "*" * chars_to_replace
    
    return f"@{visible_part}{stars}"

# ----------------------------------------------------

def random_datetime_in_window(start_t: dtime, end_t: dtime, base_date) -> datetime:
    start_dt = datetime.combine(base_date, start_t, tzinfo=MSK)
    end_dt   = datetime.combine(base_date, end_t,   tzinfo=MSK)
    total_seconds = int((end_dt - start_dt).total_seconds())
    offset = random.randint(0, total_seconds)
    return start_dt + timedelta(seconds=offset)

def seconds_until_random_start() -> int:
    """Определяет задержку до первой отправки."""
    now = datetime.now(MSK)
    today = now.date()

    start_dt = datetime.combine(today, START_WINDOW_START, tzinfo=MSK)
    end_dt   = datetime.combine(today, START_WINDOW_END,   tzinfo=MSK)

    # 1. Ещё рано — ждём случайную точку в окне 9:19–9:27
    if now < start_dt:
        total_seconds = int((end_dt - start_dt).total_seconds())
        offset = random.randint(0, total_seconds)
        target = start_dt + timedelta(seconds=offset)
        return max(int((target - now).total_seconds()), 0)

    # 2. Внутри окна 9:19–9:27 — стартуем почти сразу
    if start_dt <= now <= end_dt:
        return random.randint(1, 60)

    # 3. Окно уже прошло — стартуем сразу
    return 5

def get_end_deadline() -> datetime:
    """Случайный дедлайн окончания (20:42–20:56 МСК) для сегодняшнего дня."""
    now = datetime.now(MSK)
    return random_datetime_in_window(END_WINDOW_START, END_WINDOW_END, now.date())

def schedule_next(context, deadline: datetime):
    """Планирует следующую отправку через случайный интервал, но не позже deadline."""
    delay = random.randint(MIN_INTERVAL, MAX_INTERVAL)
    next_time = datetime.now(MSK) + timedelta(seconds=delay)

    if next_time >= deadline:
        logging.info("Дедлайн достигнут. Больше отправок сегодня не будет.")
        return

    context.job_queue.run_once(send_random_message, when=delay)
    minutes = delay // 60
    seconds = delay % 60
    logging.info(f"Следующая отправка через {minutes} мин {seconds} сек.")

async def send_random_message(context):
    deadline = context.bot_data.get("deadline")
    if deadline and datetime.now(MSK) >= deadline:
        logging.info("Дедлайн прошёл. Остановка отправок.")
        return

    try:
        # Генерируем данные для сообщения
        number = random.randint(MIN_NUMBER, MAX_NUMBER)
        now_msk = datetime.now(MSK).strftime("%H:%M:%S")
        random_id = generate_random_id()
        worker_name = generate_worker_name()

        # Подставляем всё в шаблон
        text = MESSAGE_TEMPLATE.format(
            number=number, 
            time=now_msk,
            id=random_id,
            worker=worker_name
        )
        
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=text,
            message_thread_id=THREAD_ID
        )
        logging.info(f"Отправлено число: {number} в {now_msk} | ID: {random_id} | Воркер: {worker_name}")
    except Exception as e:
        logging.error(f"Ошибка при отправке: {e}")

    schedule_next(context, deadline)

async def delete_webhook():
    bot = Bot(token=TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Webhook удалён.")

def main():
    asyncio.run(delete_webhook())

    application = Application.builder().token(TOKEN).build()

    deadline = get_end_deadline()
    application.bot_data["deadline"] = deadline
    logging.info(f"Дедлайн окончания: {deadline.strftime('%H:%M:%S')} МСК")

    delay = seconds_until_random_start()
    logging.info(f"Старт запланирован через {delay // 60} мин {delay % 60} сек.")

    application.job_queue.run_once(send_random_message, when=delay)

    logging.info("Бот запущен.")
    logging.info(f"Случайный интервал: {MIN_INTERVAL // 60}–{MAX_INTERVAL // 60} мин.")

    application.run_polling()

if __name__ == '__main__':
    main()


if __name__ == '__main__':
    main()
