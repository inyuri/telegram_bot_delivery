import logging

from telegram import InputMediaPhoto
from telegram.ext import Application, MessageHandler, CommandHandler, CallbackQueryHandler,\
    ConversationHandler, filters

from config import BOT_TOKEN, YANDEX_GEOCODE_API_KEY, ADMIN_PASSWORD
from buttons import main_menu_buttons, back_button, menu_restaurant_buttons, menu_order, accept_menu_buttons, \
    scroll_menu_buttons, admin_panel_buttons, delete_pos_buttons, back_admin_panel_button
from data import db_session
from data.users import User
from data.foods import Food

import requests
import os


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)

RESTAURANT_ADDRESS = 'улица Энтузиастов, 1, Балашов, Саратовская область'


async def start(update, context):
    context.user_data['order'] = {}
    context.user_data['number_phone'] = ''
    context.user_data['address'] = ''

    await update.message.reply_text(f'Привет {update.effective_user.first_name}!\n'
                                    f'<b>Мы рады вас приветствовать в нашем боте</b>!',
                                    parse_mode='HTML')
    await update.message.reply_text('Выберите интересующий вас раздел:', reply_markup=main_menu_buttons)


async def menu(update, context):
    db_sess = db_session.create_session()
    all_food = [(food.food_title, food.description, food.price, food.path_img)
                for food in db_sess.query(Food).all()]

    order_user = context.user_data['order']

    for food in all_food:
        order_user[food[0]] = 0

    list_of_food = []
    for title, desc, price, path_img in all_food:
        list_of_food.append(f'<b>{title}</b> - {desc} <b>Цена</b>: {price}')
    await update.callback_query.edit_message_text('<b>📖 Меню</b>:\n\n' + '\n\n'.join(list_of_food),
                                                  parse_mode='HTML',
                                                  reply_markup=menu_restaurant_buttons)


async def order(update, context):
    query = update.callback_query
    data = query.data
    db_sess = db_session.create_session()
    all_food = [(food.food_title, food.description, food.price, food.path_img)
                for food in db_sess.query(Food).all()]

    # Добавление в чек
    order_user = context.user_data['order']
    for food in order_user.keys():
        if food == data:
            order_user[food] += 1

    list_of_food = []
    for title, desc, price, path_img in all_food:
        list_of_food.append(f'<b>{title}</b> - {desc} <b>Цена</b>: {price}')

    check_data = ''
    for food in order_user.keys():
        if order_user[food] != 0:
            check_data += food + ' x' + str(order_user[food]) + '\n'

    total = 0
    for food in order_user.keys():
        for food_massive in all_food:
            if order_user[food] != 0:
                if food == food_massive[0]:
                    total += order_user[food] * food_massive[2]

    await update.callback_query.edit_message_text('---\nВаш чек:\n'
                                                  + check_data +
                                                  '---\n<b>Итого: </b>' + str(total) + '\n\n'
                                                  + '<b>📖 Меню</b>:\n\n'
                                                  + '\n\n'.join(list_of_food),
                                                  parse_mode='HTML',
                                                  reply_markup=menu_order)


async def make_order(update, context):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.telegramId == update.effective_user.id).first()

    order_user = context.user_data['order']
    check_data = ''
    all_food = [(food.food_title, food.description, food.price, food.path_img)
                for food in db_sess.query(Food).all()]

    total = 0
    for food in order_user.keys():
        for food_massive in all_food:
            if order_user[food] != 0:
                if food == food_massive[0]:
                    total += order_user[food] * food_massive[2]

    if total > user.money:
        await update.callback_query.edit_message_text('<b>У вас недостаточно средств!</b> Попробуйте заново.',
                                                      reply_markup=back_button,
                                                      parse_mode='HTML')
    else:
        for food in order_user.keys():
            if order_user[food] != 0:
                check_data += food + ' x' + str(order_user[food]) + '\n'

        await update.callback_query.edit_message_text('Проверьте введенные данные, всё верно?\n\n' +
                                                      '---\nВаш чек:\n'
                                                      + check_data + '---\n<b>Итого: </b>' + str(total),
                                                      parse_mode='HTML',
                                                      reply_markup=accept_menu_buttons)


async def ask_address(update, context):
    await update.callback_query.edit_message_text('Введите адрес на который нужно оформить доставку')
    return 1


async def ask_number_phone(update, context):
    context.user_data['address'] = update.message.text
    await update.message.reply_text('Введите номер телефона по которому мы сможем связаться с вами.\n'
                                    '(Номер телефона нужно вводить в таком виде: "+79991234567")')
    return 2


async def success_order(update, context):
    try:
        context.user_data['number_phone'] = update.message.text
        if not (context.user_data['number_phone'][1:].isdigit() and len(context.user_data['number_phone']) == 12 and
                context.user_data['number_phone'].startswith('+7')):
            raise Exception
        db_sess = db_session.create_session()

        locations = [RESTAURANT_ADDRESS, context.user_data['address']]
        coordinates = []

        all_food = [(food.food_title, food.description, food.price, food.path_img)
                    for food in db_sess.query(Food).all()]

        order_user = context.user_data['order']
        total = 0
        for food in order_user.keys():
            for food_massive in all_food:
                if order_user[food] != 0:
                    if food == food_massive[0]:
                        total += order_user[food] * food_massive[2]

        for location in locations:
            url = f'https://geocode-maps.yandex.ru/1.x/?apikey={YANDEX_GEOCODE_API_KEY}&format=json&geocode={location}'
            response = requests.get(url).json()
            coordinates.append(response['response']['GeoObjectCollection']['featureMember']
                               [0]['GeoObject']['Point']['pos'])

        request = f'https://static-maps.yandex.ru/1.x/?ll={",".join(coordinates[1].split())}&spn=0.09,' \
                  f'0.09&l=map&pt={",".join(coordinates[0].split())},pm2wtm~{",".join(coordinates[1].split())},pm2wtm'
        response = requests.get(request)

        map_file = "map.png"
        with open(map_file, "wb") as file:
            file.write(response.content)

        order_user = context.user_data['order']
        check_data = ''
        for food in order_user.keys():
            if order_user[food] != 0:
                check_data += food + ' x' + str(order_user[food]) + '\n'

        await context.bot.send_photo(update.effective_user.id, photo=open('map.png', 'rb'),
                                     caption=f'<b>🍽️ Адрес ресторана:</b> {RESTAURANT_ADDRESS}\n'
                                             f'<b>🏠 Ваш адрес:</b> {context.user_data["address"]}\n'
                                             f'<b>☎️ Ваш номер телефона:</b> {context.user_data["number_phone"]}\n\n'
                                             f'---\n<b>Ваш чек:</b>\n' + check_data + '---\n<b>Итого: </b>'
                                             + str(total) + '\n\n' +
                                             f'<b>Заказ успешно принят!</b> Ждите доставки.\n'
                                             f'<b>Если доставка длится больше 2 часов,'
                                             f' заказ будет оплачен за счёт заведения!</b>', parse_mode='HTML')

        os.remove('map.png')

        user = db_sess.query(User).filter(User.telegramId == update.effective_user.id).first()
        user.amountOrders += 1
        user.money -= total
        db_sess.commit()
    except Exception:
        await update.message.reply_text('<b>Возможно вы ввели неправильный адрес/телефон</b>.'
                                        ' Попробуйте сделать заказ заново.',
                                        reply_markup=back_button, parse_mode='HTML')

    return ConversationHandler.END


async def profile(update, context):
    db_sess = db_session.create_session()
    print(db_sess.query(User).all())

    if update.effective_user.id not in [user.telegramId for user in db_sess.query(User).all()]:
        user = User()
        user.telegramId = update.effective_user.id
        db_sess.add(user)
    db_sess.commit()

    user = db_sess.query(User).filter(User.telegramId == update.effective_user.id).first()

    await update.callback_query.edit_message_text(f'*👀 Имя*: {update.effective_user.first_name}\n\n'
                                                  f'*🆔 id*: {update.effective_user.id}\n\n'
                                                  f'*💸 Баланс*: {user.money}\n\n'
                                                  f'*📦 Количество заказов*: {user.amountOrders}\n',
                                                  parse_mode='MarkdownV2',
                                                  reply_markup=back_button)


async def information(update, context):
    await update.callback_query.edit_message_text('<b>📱 Телефон</b>: +7(800)555-35-35\n\n'
                                                  '<b>👥 Вконтакте</b>: vk.com/DeliveryBot\n\n'
                                                  '<b>🌐 Вебсайт</b>: https://DeliveryBot.ru\n\n'
                                                  '<b>📧 Почта</b>: DeliveryBot@yandex.ru\n\n\n'
                                                  f'<b>🏠 Адрес</b>: {RESTAURANT_ADDRESS}', parse_mode='HTML',
                                                  reply_markup=back_button)


# Перелистывание фотографий "просмотр меню"
async def look_menu(update, context):
    db_sess = db_session.create_session()

    info_food = [(food.path_img, food.food_title, food.description) for food in db_sess.query(Food).all()]
    context.user_data['current_index'] = 0
    current_index = context.user_data['current_index']
    message = await context.bot.send_photo(chat_id=update.effective_user.id,
                                           photo=open(info_food[current_index][0], mode='rb'),
                                           caption=f'<b>{info_food[context.user_data["current_index"] % len(info_food)][1]}</b>'
                                                   f' ({context.user_data["current_index"] % len(info_food) + 1}/{len(info_food)})\n'
                                                   f'{info_food[context.user_data["current_index"] % len(info_food)][2]}',
                                           reply_markup=scroll_menu_buttons, parse_mode='HTML')
    context.user_data['id_media_edit'] = message.message_id


async def scroll_image(update, context):
    db_sess = db_session.create_session()

    info_food = [(food.path_img, food.food_title, food.description) for food in db_sess.query(Food).all()]
    if update.callback_query.data == 'prev':
        context.user_data['current_index'] -= 1
    elif update.callback_query.data == 'next':
        context.user_data['current_index'] += 1
    info_index_food = info_food[context.user_data['current_index'] % len(info_food)]
    print(context.user_data['current_index'], context.user_data['current_index'] % len(info_food), len(info_food))
    await context.bot.edit_message_media(chat_id=update.effective_user.id,
                                         message_id=context.user_data['id_media_edit'],
                                         media=InputMediaPhoto(open(info_index_food[0], 'rb')),
                                         reply_markup=scroll_menu_buttons)
    await context.bot.edit_message_caption(chat_id=update.effective_user.id,
                                           message_id=context.user_data['id_media_edit'],
                                           caption=f'<b>{info_index_food[1]}</b>'
                                                   f' ({context.user_data["current_index"] % len(info_food) + 1}'
                                                   f'/{len(info_food)})\n'
                                                   f'{info_index_food[2]}',
                                           reply_markup=scroll_menu_buttons, parse_mode='HTML')


async def ask_password(update, context):
    await update.message.reply_text('Здравствуйте! Добро пожаловать в систему управления меню. '
                                    'Чтобы начать взаимодействие введите пароль:')
    return 1


async def admin_panel(update, context):
    if ADMIN_PASSWORD == update.message.text:
        await update.message.reply_text('<b>Добро пожаловать в админ-панель!</b>\n'
                                        'Выберите интересующий вас раздел:',
                                        reply_markup=admin_panel_buttons, parse_mode='HTML')
    else:
        await update.message.reply_text('<b>Вы ввели неверный пароль!</b> Попробуйте заново.', parse_mode='HTML')
    return ConversationHandler.END


async def delete_pos_menu(update, context):
    await update.callback_query.edit_message_text('<b>Выберите какое блюдо вы хотите удалить из меню:</b>',
                                                  reply_markup=delete_pos_buttons, parse_mode='HTML')


async def delete_pos(update, context):
    db_sess = db_session.create_session()
    all_food_titles = [food.food_title for food in db_sess.query(Food).all()]
    for food_title in all_food_titles:
        if food_title + '_delete' == update.callback_query.data:
            food_delete = db_sess.query(Food).filter(Food.food_title == food_title).first()
            food_delete_title = db_sess.query(Food).filter(Food.food_title == food_title).first().food_title
            print(food_delete_title)
            db_sess.delete(food_delete)
            db_sess.commit()
            await update.callback_query.edit_message_text(f'<b>Блюдо {food_delete_title} успешно удалено!</b>',
                                                          reply_markup=back_admin_panel_button, parse_mode='HTML')


async def add_pos_menu(update, context):
    await update.callback_query.edit_message_text('<b>Эта функция пока что не реализована.</b>', parse_mode='HTML',
                                                  reply_markup=back_admin_panel_button)


async def back(update, context):
    await update.callback_query.edit_message_text('Выберите интересующий вас раздел:', reply_markup=main_menu_buttons)


async def back_admin_panel(update, context):
    await update.callback_query.edit_message_text('<b>Добро пожаловать в админ-панель!</b>\n'
                                                  'Выберите интересующий вас раздел:',
                                                  reply_markup=admin_panel_buttons, parse_mode='HTML')
    return ConversationHandler.END


async def unknown_command(update, context):
    await update.message.reply_text('Бот не знает такой команды. Для начала диалога'
                                    ' с ботом используйте команду /start.')


async def fallback(update, context):
    await update.message.reply_text('Извините, я не понимаю вашего сообщения. Для начала диалога'
                                    ' с ботом используйте команду /start.')


async def delete_scroll(update, context):
    await context.bot.delete_message(chat_id=update.effective_user.id, message_id=context.user_data['id_media_edit'])


def main():
    db_session.global_init("db/users.db")
    db_sess = db_session.create_session()
    application = Application.builder().token(BOT_TOKEN).build()
    all_food = [(food.food_title, food.description, food.price, food.path_img) for food in db_sess.query(Food).all()]

    application.add_handler(CommandHandler("start", start))

    # Создание админ-панели
    admin_panel_conv = ConversationHandler(
        entry_points=[CommandHandler("admin_panel", ask_password)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_panel)]
        },
        fallbacks=[],
        allow_reentry=True
    )
    application.add_handler(admin_panel_conv)
    application.add_handler(CallbackQueryHandler(back_admin_panel, pattern='back_admin_panel'))

    # Удалени позиции из меню
    application.add_handler(CallbackQueryHandler(delete_pos_menu, pattern='delete_pos_menu'))
    for food in all_food:
        application.add_handler(CallbackQueryHandler(delete_pos, pattern=food[0] + '_delete'))

    # Добавление позиции в меню
    application.add_handler(CallbackQueryHandler(add_pos_menu, pattern='add_pos_menu'))

    application.add_handler(CallbackQueryHandler(menu, pattern='menu'))

    for food in all_food:
        application.add_handler(CallbackQueryHandler(order, pattern=food[0]))
    application.add_handler(CallbackQueryHandler(menu, pattern='no'))

    user_info_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_address, pattern='yes')],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_number_phone)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, success_order)]
        },
        fallbacks=[],
        allow_reentry=True
    )

    application.add_handler(user_info_conv)

    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    application.add_handler(MessageHandler(filters.ALL, fallback))

    application.add_handler(CallbackQueryHandler(make_order, pattern='make_order'))
    application.add_handler(CallbackQueryHandler(profile, pattern='profile'))
    application.add_handler(CallbackQueryHandler(information, pattern='information'))
    application.add_handler(CallbackQueryHandler(look_menu, pattern='look_menu'))
    application.add_handler(CallbackQueryHandler(scroll_image, pattern='prev'))
    application.add_handler(CallbackQueryHandler(scroll_image, pattern='next'))
    application.add_handler(CallbackQueryHandler(delete_scroll, pattern='delete_scroll'))
    application.add_handler(CallbackQueryHandler(back, pattern='back'))

    application.run_polling()


if __name__ == '__main__':
    main()
