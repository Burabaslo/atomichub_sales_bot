import logging
from aiogram import Bot, Dispatcher, executor, types
from typing import List, NamedTuple, Optional
from config import tg_bot_token, tg_my_chat_id
import json
import datetime
import time
import requests

# Объект бота
bot = Bot(token=tg_bot_token)
# Диспетчер для бота
dp = Dispatcher(bot)
# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)


# Kласс для хранения настроек из сообщения пользователя
class parsed_msg():
    state: int
    symbol: str
    collection_name: str
    template_id: int
    sort: str
    limit_of_sales: int
    refresh_seconds: int
    seconds_to_send_sales: int


# Парсим настройки из сообщения в объект класса
def parse_settings(json_data):
    q = parsed_msg()
    q.sort = json_data["settings"]["sort"]
    q.collection_name = json_data["settings"]["collection_name"]
    q.limit_of_sales = json_data["settings"]["limit_of_sales"]
    q.refresh_seconds = json_data["settings"]["refresh_seconds"]
    q.seconds_to_send_sales = json_data["settings"]["seconds_to_send_sales"]
    q.state = json_data["settings"]["state"]
    q.symbol = json_data["settings"]["symbol"]
    q.template_id = json_data["settings"]["template_id"]
    return q


# Основная функция для отправки запроса к торговой площадке и получения данных о последних продажах
# А так же вывод полученных данных в телеграмм
async def sales_printer(settings):
    t_end = time.time() + settings.seconds_to_send_sales
    while time.time() < t_end:
        now = datetime.datetime.now()
        await bot.send_message(tg_my_chat_id, f"============{now}============\n")
        response = requests.get(
            f"https://wax.api.atomicassets.io/atomicmarket/v1/sales?state={settings.state}&collection_name={settings.collection_name}&template_id={settings.template_id}&page=1&limit={settings.limit_of_sales}&order=desc&sort={settings.sort}")
        response_json = response.json()
        # print(response_json)
        try:
            for asset in response_json["data"]:
                if asset["listing_symbol"] == "WAX":
                    id = asset["sale_id"]
                    price = int(asset["listing_price"]) * 0.00000001
                    await bot.send_message(tg_my_chat_id, f'{id} > {price}\n')
                    # print(asset["sale_id"], ">", int(asset["listing_price"]) * 0.00000001)
            time.sleep(settings.refresh_seconds)
        except IndexError:
            await bot.send_message(tg_my_chat_id, f"IndexError\n")
            time.sleep(1)


# Хэндлер на команду /start
@dp.message_handler(commands=["start"])
async def cmd_test1(message: types.Message):
    await message.answer(
        "Привет, я умею выводить цену продажи и id предметов на Atomichub, закидывай json с парметрами")
    await message.answer(
        "Пример:\n""""{
	"settings":{
		"state":3,
		"symbol":"WAX",
		"collection_name":"crypto5tache",
		"template_id":172880,
		"sort":"created",
		"limit_of_sales":20,
		"refresh_seconds":5,
		"seconds_to_send_sales":20
	}
}""")

# Хэндлер на отправленный json
@dp.message_handler()
async def get_json_msg(message: types.Message):
    data = message.text
    try:
        json_data = json.loads(data)
        # print(json_data)
        settings = parse_settings(json_data)
        await sales_printer(settings)
    except:
        await message.answer("Проверьте json")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
