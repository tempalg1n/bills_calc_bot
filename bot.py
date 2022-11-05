import math
import time

from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext

from settings import bot_config
from database import orm

bot = Bot(token=bot_config.TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class ChoiceAddress(StatesGroup):
    address = State()


class MakeReport(StatesGroup):
    cold = State()
    hot = State()
    electricity = State()


@dp.message_handler(commands=['start'])
async def start_message(message: types.Message):
    orm.add_user(message.from_user.id)
    markup = types.reply_keyboard.ReplyKeyboardMarkup(resize_keyboard=True)
    city = orm.get_user_address(message.from_user.id)
    b1 = types.KeyboardButton('новая запись')
    b2 = types.KeyboardButton('мои записи')
    b3 = types.KeyboardButton('текущий тариф')
    b4 = types.KeyboardButton('изменить тариф')
    b5 = types.KeyboardButton('изменить адресс')
    if city is None:
        b6 = types.KeyboardButton('установить свой адресс')
        markup.add(b1, b2, b3, b4, b5, b6)
    else:
        markup.add(b1, b2, b3, b4, b5)
    hello = f'Привет, {message.from_user.first_name}! Я рассчитываю сумму оплаты ЖКХ по тарифу и веду записи.'
    await message.answer(hello)
    time.sleep(2)
    await message.answer('На клавиатуре список команд, которыми можно пользоваться', reply_markup=markup)


@dp.message_handler(regexp='Меню')
async def start_message(message: types.Message):
    markup = types.reply_keyboard.ReplyKeyboardMarkup(resize_keyboard=True)
    city = orm.get_user_address(message.from_user.id)
    b1 = types.KeyboardButton('новая запись')
    b2 = types.KeyboardButton('мои записи')
    b3 = types.KeyboardButton('текущий тариф')
    b4 = types.KeyboardButton('изменить тариф')
    b5 = types.KeyboardButton('изменить адресс')
    if city is None:
        b6 = types.KeyboardButton('установить свой адресс')
        markup.add(b1, b2, b3, b4, b5, b6)
    else:
        markup.add(b1, b2, b3, b4, b5)
    text = 'Держи меню, друг.'
    await message.answer(text, reply_markup=markup)


@dp.message_handler(regexp='текущий тариф')
async def start_message(message: types.Message):
    markup = types.reply_keyboard.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('Меню')
    markup.add(btn1)
    tariff = orm.Tariff()
    text = 'Текущий тариф:\nГВС: {}\nХВС: {}\nВодоотведение: {}\nЭлектричество: {}'.format(*tariff.tariff)
    await message.answer(text, reply_markup=markup)


@dp.message_handler(regexp='установить свой адресс')
async def set_user_address(message: types.Message):
    markup = types.reply_keyboard.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Меню')
    markup.add(btn1)
    text = 'Напиши свой адрес.'
    await message.answer(text, reply_markup=markup)
    await ChoiceAddress.address.set()


@dp.message_handler(state=ChoiceAddress.address)
async def user_city_chosen(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    user_data = await state.get_data()
    orm.set_user_address(message.from_user.id, user_data.get('address'))
    markup = types.reply_keyboard.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Меню')
    markup.add(btn1)
    text = f'Запомнил, {user_data.get("address")} ваш адресс.'
    await message.answer(text, reply_markup=markup)
    await state.finish()


@dp.message_handler(regexp='новая запись')
async def start_message(message: types.Message):
    markup = types.reply_keyboard.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('Меню')
    markup.add(btn1)
    city = orm.get_user_address(message.from_user.id)
    if city is None:
        text = 'Пожалуйста установите адресс!'
        await message.answer(text, reply_markup=markup)
        return
    text = 'Давайте сделаем запись. Напиши показания счетчика *холодной* воды'
    await message.answer(text, parse_mode="Markdown")
    await MakeReport.cold.set()


@dp.message_handler(state=MakeReport.cold)
async def cold(message: types.Message, state: FSMContext):
    await state.update_data(cold=message.text)
    markup = types.reply_keyboard.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Меню')
    markup.add(btn1)
    text = 'Теперь показания *горячей* воды'
    await message.answer(text, parse_mode="Markdown")
    await MakeReport.hot.set()


@dp.message_handler(state=MakeReport.hot)
async def hot(message: types.Message, state: FSMContext):
    await state.update_data(hot=message.text)
    markup = types.reply_keyboard.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Меню')
    markup.add(btn1)
    text = 'Теперь показания *электрического счетчика*'
    await message.answer(text, parse_mode="Markdown")
    await MakeReport.electricity.set()


@dp.message_handler(state=MakeReport.electricity)
async def electricity(message: types.Message, state: FSMContext):
    await state.update_data(electricity=message.text)
    markup = types.reply_keyboard.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Меню')
    markup.add(btn1)
    text = 'Запомнил!'
    await message.answer(text, reply_markup=markup, parse_mode="Markdown")
    text2 = 'Давай я заодно тебе посчитаю сумму для оплаты по кватанции...'
    time.sleep(2)
    await message.answer(text2)
    user_data = await state.get_data()
    bills = orm.do_report(message.from_user.id, cold=int(user_data.get('cold')), hot=int(user_data.get('hot')),
                          electricity=int(user_data.get('electricity')))
    time.sleep(2)
    text3 = f"Так, получается...\n\nЗа холодную воду надо *{bills['cold']} р.*\nЗа горячую *{bills['hot']} р.*\nЗа " \
            f"водоотведение *{bills['drainage']} р.*\nЗа электричество *{bills['electricity']} р.*\n\nИтого, получ" \
            f"ается: `{round(bills['total'], 2)}` р. "
    await message.answer(text3, parse_mode="Markdown")
    await state.finish()


@dp.message_handler(regexp='изменить тариф')
async def start_message(message: types.Message):
    markup = types.reply_keyboard.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('Меню')
    markup.add(btn1)
    text = 'А надо ли его менять?..🤷‍♂️'
    await message.answer(text, reply_markup=markup)


@dp.message_handler(regexp='изменить адресс')
async def start_message(message: types.Message):
    markup = types.reply_keyboard.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('Меню')
    markup.add(btn1)
    text = 'Напиши свой адрес.'
    await message.answer(text, reply_markup=markup)
    await ChoiceAddress.address.set()


@dp.message_handler(regexp='мои записи')
async def get_reports(message: types.Message):
    orm.do_reports_for_me(message.from_user.id)
    current_page = 1
    reports = orm.get_reports(message.from_user.id)
    total_pages = math.ceil(len(reports) / 4)
    text = 'История запросов:'
    inline_markup = types.InlineKeyboardMarkup()
    for report in reports[:current_page * 4]:
        inline_markup.add(types.InlineKeyboardButton(
            text=f'{report.address} {report.date.day}.{report.date.month}.{report.date.year}',
            callback_data=f'report_{report.id}'
        ))
    current_page += 1
    inline_markup.row(
        types.InlineKeyboardButton(text=f'{current_page - 1}/{total_pages}', callback_data='None'),
        types.InlineKeyboardButton(text='Вперёд', callback_data=f'next_{current_page}')
    )
    await message.answer(text, reply_markup=inline_markup)


@dp.callback_query_handler(lambda call: True)
async def callback_query(call, state: FSMContext):
    query_type = call.data.split('_')[0]
    if query_type == 'delete' and call.data.split('_')[1] == 'report':
        report_id = int(call.data.split('_')[2])
        current_page = 1
        orm.delete_user_report(report_id)
        reports = orm.get_reports(call.from_user.id)
        total_pages = math.ceil(len(reports) / 4)
        inline_markup = types.InlineKeyboardMarkup()
        for report in reports[:current_page * 4]:
            inline_markup.add(types.InlineKeyboardButton(
                text=f'{report.address} {report.date.day}.{report.date.month}.{report.date.year}',
                callback_data=f'report_{report.id}'
            ))
        current_page += 1
        inline_markup.row(
            types.InlineKeyboardButton(text=f'{current_page - 1}/{total_pages}', callback_data='None'),
            types.InlineKeyboardButton(text='Вперёд', callback_data=f'next_{current_page}')
        )
        await call.message.edit_text(text='История запросов:', reply_markup=inline_markup)
        return
    async with state.proxy() as data:
        data['current_page'] = int(call.data.split('_')[1])
        await state.update_data(current_page=data['current_page'])
        if query_type == 'next':
            reports = orm.get_reports(call.from_user.id)
            total_pages = math.ceil(len(reports) / 4)
            inline_markup = types.InlineKeyboardMarkup()
            if data['current_page'] * 4 >= len(reports):
                for report in reports[data['current_page'] * 4 - 4:len(reports) + 1]:
                    inline_markup.add(types.InlineKeyboardButton(
                        text=f'{report.address} {report.date.day}.{report.date.month}.{report.date.year}',
                        callback_data=f'report_{report.id}'
                    ))
                data['current_page'] -= 1
                inline_markup.row(
                    types.InlineKeyboardButton(text='Назад', callback_data=f'prev_{data["current_page"]}'),
                    types.InlineKeyboardButton(text=f'{data["current_page"] + 1}/{total_pages}', callback_data='None')
                )
                await call.message.edit_text(text="История запросов:", reply_markup=inline_markup)
                return
            for report in reports[data['current_page'] * 4 - 4:data['current_page'] * 4]:
                inline_markup.add(types.InlineKeyboardButton(
                    text=f'{report.address} {report.date.day}.{report.date.month}.{report.date.year}',
                    callback_data=f'report_{report.id}'
                ))
            data['current_page'] += 1
            inline_markup.row(
                types.InlineKeyboardButton(text='Назад', callback_data=f'prev_{data["current_page"] - 2}'),
                types.InlineKeyboardButton(text=f'{data["current_page"] - 1}/{total_pages}', callback_data='None'),
                types.InlineKeyboardButton(text='Вперёд', callback_data=f'next_{data["current_page"]}')
            )
            await call.message.edit_text(text="История запросов:", reply_markup=inline_markup)
        if query_type == 'prev':
            reports = orm.get_reports(call.from_user.id)
            total_pages = math.ceil(len(reports) / 4)
            inline_markup = types.InlineKeyboardMarkup()
            if data['current_page'] == 1:
                for report in reports[0:data['current_page'] * 4]:
                    inline_markup.add(types.InlineKeyboardButton(
                        text=f'{report.address} {report.date.day}.{report.date.month}.{report.date.year}',
                        callback_data=f'report_{report.id}'
                    ))
                data['current_page'] += 1
                inline_markup.row(
                    types.InlineKeyboardButton(text=f'{data["current_page"] - 1}/{total_pages}', callback_data='None'),
                    types.InlineKeyboardButton(text='Вперёд', callback_data=f'next_{data["current_page"]}')
                )
                await call.message.edit_text(text="История запросов:", reply_markup=inline_markup)
                return
            for report in reports[data['current_page'] * 4 - 4:data['current_page'] * 4]:
                inline_markup.add(types.InlineKeyboardButton(
                    text=f'{report.address} {report.date.day}.{report.date.month}.{report.date.year}',
                    callback_data=f'report_{report.id}'
                ))
            data['current_page'] -= 1
            inline_markup.row(
                types.InlineKeyboardButton(text='Назад', callback_data=f'prev_{data["current_page"]}'),
                types.InlineKeyboardButton(text=f'{data["current_page"] + 1}/{total_pages}', callback_data='None'),
                types.InlineKeyboardButton(text='Вперёд', callback_data=f'next_{data["current_page"]}'),
            )
            await call.message.edit_text(text="История запросов:", reply_markup=inline_markup)
        if query_type == 'report':
            reports = orm.get_reports(call.from_user.id)
            report_id = call.data.split('_')[1]
            inline_markup = types.InlineKeyboardMarkup()
            for report in reports:
                if report.id == int(report_id):
                    inline_markup.add(
                        types.InlineKeyboardButton(text='Назад', callback_data=f'reports_{data["current_page"]}'),
                        types.InlineKeyboardButton(text='Удалить зарос', callback_data=f'delete_report_{report_id}')
                    )
                    await call.message.edit_text(
                        text=f'Данные по запросу:\n\n'
                             f'Дата: {report.date.day}.{report.date.month}.{report.date.year}\n'
                             f'Адресс:{report.address}\n'
                             f'ХВС:{report.cold}\n'
                             f'ГВС:{report.hot}\n'
                             f'Свет:{report.electricity}\n',
                        reply_markup=inline_markup
                    )
                    break
        if query_type == 'reports':
            reports = orm.get_reports(call.from_user.id)
            total_pages = math.ceil(len(reports) / 4)
            inline_markup = types.InlineKeyboardMarkup()
            data['current_page'] = 1
            for report in reports[:data['current_page'] * 4]:
                inline_markup.add(types.InlineKeyboardButton(
                    text=f'{report.address} {report.date.day}.{report.date.month}.{report.date.year}',
                    callback_data=f'report_{report.id}'
                ))
            data['current_page'] += 1
            inline_markup.row(
                types.InlineKeyboardButton(text=f'{data["current_page"] - 1}/{total_pages}', callback_data='None'),
                types.InlineKeyboardButton(text='Вперёд', callback_data=f'next_{data["current_page"]}')
            )
            await call.message.edit_text(text='История запросов:', reply_markup=inline_markup)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
