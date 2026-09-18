import logging
import random
import asyncio
from datetime import datetime, time as dtime, timedelta
from zoneinfo import ZoneInfo
from telegram import Bot
from telegram.ext import Application

# ================== НАСТРОЙКИ ==================
TOKEN = "8941613345:AAHpkoBvptRPVLt1QCaGW2dKhPD_wPIDYjA"
CHAT_ID = -1004428877189

MESSAGE_TEMPLATE = """Время: {time}

Сумма: {number}$ | Статус: ACCEPTED

Доля воркера: {percent}$

ID: ******** | Воркер: Аноним"""

MIN_NUMBER = 92
MAX_NUMBER = 1349

# Случайный интервал между отправками (в секундах)
MIN_INTERVAL = 900    # 15 минут
MAX_INTERVAL = 2700   # 45 минут

# Окно СТАРТА (МСК) — утро
START_WINDOW_START = dtime(9, 0)
START_WINDOW_END   = dtime(9, 5)

# Окно ЗАВЕРШЕНИЯ (МСК) — вечер
END_WINDOW_START = dtime(20, 55)
END_WINDOW_END   = dtime(21, 0)

MSK = ZoneInfo("Europe/Moscow")
# ===============================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def random_datetime_in_window(start_t: dtime, end_t: dtime, base_date) -> datetime:
    start_dt = datetime.combine(base_date, start_t, tzinfo=MSK)
    end_dt   = datetime.combine(base_date, end_t,   tzinfo=MSK)
    total_seconds = int((end_dt - start_dt).total_seconds())
    offset = random.randint(0, total_seconds)
    return start_dt + timedelta(seconds=offset)

def seconds_until_random_start() -> int:
    """Определяет задержку до первой отправки с учётом окна 9:00–9:05."""
    now = datetime.now(MSK)
    today = now.date()

    start_dt = datetime.combine(today, START_WINDOW_START, tzinfo=MSK)
    end_dt   = datetime.combine(today, START_WINDOW_END,   tzinfo=MSK)

    # 1. Ещё рано (до 9:00) — ждём случайную точку в окне старта
    if now < start_dt:
        target = random_datetime_in_window(START_WINDOW_START, START_WINDOW_END, today)
        return max(int((target - now).total_seconds()), 0)

    # 2. Внутри окна старта (9:00–9:05) — стартуем почти сразу
    if start_dt <= now <= end_dt:
        return random.randint(1, 60)

    # 3. Окно старта уже прошло — стартуем сразу
    return 5

def get_end_deadline() -> datetime:
    """
    Случайный дедлайн окончания (20:55–21:00 МСК).
    Если сейчас до 21:00 — дедлайн сегодня.
    Если после 21:00 — дедлайн на завтра.
    """
    now = datetime.now(MSK)

    if now.hour < 21:
        base_date = now.date()
    else:
        base_date = now.date() + timedelta(days=1)

    return random_datetime_in_window(END_WINDOW_START, END_WINDOW_END, base_date)

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
        number = random.randint(MIN_NUMBER, MAX_NUMBER)
        percent = int(number * 0.7)
        now_msk = datetime.now(MSK).strftime("%H:%M:%S")
        text = MESSAGE_TEMPLATE.format(number=number, percent=percent, time=now_msk)
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=text
        )
        logging.info(f"Отправлено число: {number} (70% = {percent}) в {now_msk}")
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
    logging.info(f"Дедлайн окончания: {deadline.strftime('%d.%m %H:%M:%S')} МСК")

    delay = seconds_until_random_start()
    logging.info(f"Старт запланирован через {delay // 60} мин {delay % 60} сек.")

    application.job_queue.run_once(send_random_message, when=delay)

    logging.info("Бот запущен.")
    logging.info(f"Случайный интервал: {MIN_INTERVAL // 60}–{MAX_INTERVAL // 60} мин.")

    application.run_polling()

if __name__ == '__main__':
    main()
