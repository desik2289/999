import logging
import random
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo
from telegram import Bot
from telegram.ext import Application

# ================== НАСТРОЙКИ ==================
TOKEN = "8941613345:AAHpkoBvptRPVLt1QCaGW2dKhPD_wPIDYjA"
CHAT_ID = -1004428877189

# Обновленный шаблон (доля рассчитывается автоматически)
MESSAGE_TEMPLATE = """Время: {time}

Сумма: {number}$ | Статус: ACCEPTED

Доля воркера: {share}$

ID: {id} | Воркер: {worker}"""

MIN_NUMBER = 92
MAX_NUMBER = 730

# Случайный интервал между отправками (в секундах)
MIN_INTERVAL = 340    # 15 минут
MAX_INTERVAL = 2200   # 45 минут

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
    percent = 40 / 100
    chars_to_replace = max(1, int(name_len * percent))
    
    # Отрезаем часть, которую оставляем, и добавляем звездочки
    visible_part = chosen_name[:-chars_to_replace]
    stars = "*" * chars_to_replace
    
    return f"@{visible_part}{stars}"

# ----------------------------------------------------

def schedule_next(context):
    """Планирует следующую отправку через случайный интервал."""
    delay = random.randint(MIN_INTERVAL, MAX_INTERVAL)
    
    context.job_queue.run_once(send_random_message, when=delay)
    minutes = delay // 60
    seconds = delay % 60
    logging.info(f"Следующая отправка через {minutes} мин {seconds} сек.")

async def send_random_message(context):
    try:
        # Генерируем данные для сообщения
        number = random.randint(MIN_NUMBER, MAX_NUMBER)
        now_msk = datetime.now(MSK).strftime("%H:%M:%S")
        random_id = generate_random_id()
        worker_name = generate_worker_name()
        
        # Считаем 70% от суммы и округляем до целого числа
        worker_share = round(number * 0.7)

        # Подставляем всё в шаблон
        text = MESSAGE_TEMPLATE.format(
            number=number, 
            time=now_msk,
            share=worker_share,
            id=random_id,
            worker=worker_name
        )
        
        # Отправляем сообщение
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=text
        )
        logging.info(f"Отправлено: {number}$ | Доля: {worker_share}$ | ID: {random_id} | Воркер: {worker_name}")
    except Exception as e:
        logging.error(f"Ошибка при отправке: {e}")

    # Планируем следующую отправку
    schedule_next(context)

async def delete_webhook():
    bot = Bot(token=TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Webhook удалён.")

def main():
    asyncio.run(delete_webhook())

    # Если у вас ошибка сети (Timeout), раскомментируйте строку ниже и вставьте URL от Cloudflare Worker:
    # application = Application.builder().token(TOKEN).base_url("https://ваш-воркер.имя.workers.dev/bot").build()
    
    application = Application.builder().token(TOKEN).build()

    # Запускаем первую отправку через 5 секунд после старта
    delay = 5
    logging.info(f"Старт запланирован через {delay} секунд.")
    
    application.job_queue.run_once(send_random_message, when=delay)

    logging.info("Бот запущен и работает круглосуточно.")
    logging.info(f"Случайный интервал: {MIN_INTERVAL // 60}–{MAX_INTERVAL // 60} мин.")

    application.run_polling()

if __name__ == '__main__':
    main()
