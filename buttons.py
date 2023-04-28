from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from build_menu import build_menu
from data import db_session
from data.foods import Food

# Подключение к БД
db_session.global_init("db/users.db")
db_sess = db_session.create_session()

# Кнопки главного меню
button_list_main_menu = [
        InlineKeyboardButton("📋 Сделать заказ", callback_data='menu'),
        InlineKeyboardButton("🤗 Ваш профиль", callback_data='profile'),
        InlineKeyboardButton("📖 Просмотр меню", callback_data='look_menu'),
        InlineKeyboardButton("ℹ Информация", callback_data='information')
    ]
main_menu_buttons = InlineKeyboardMarkup(build_menu(button_list_main_menu, n_cols=1))

# Кнопка "Назад"
back_button = InlineKeyboardMarkup(build_menu([InlineKeyboardButton("◀ Назад", callback_data='back')], n_cols=1))

# Создание кнопок для меню ресторана
button_list_menu_restaurant = []

for food in db_sess.query(Food).all():
    button_list_menu_restaurant.append(InlineKeyboardButton(food.food_title, callback_data=food.food_title))
button_list_menu_restaurant.append(InlineKeyboardButton("◀ Назад", callback_data='back'))

menu_restaurant_buttons = InlineKeyboardMarkup(build_menu(button_list_menu_restaurant, n_cols=2))

# Создание кнопок для меню ресторана с кнопкой оформления заказа
button_list_menu_order = []

for food in db_sess.query(Food).all():
    button_list_menu_order.append(InlineKeyboardButton(food.food_title, callback_data=food.food_title))
button_list_menu_order.append(InlineKeyboardButton("◀ Назад", callback_data='back'))
button_list_menu_order.append(InlineKeyboardButton('✅ Оформить заказ', callback_data='make_order'))

menu_order = InlineKeyboardMarkup(build_menu(button_list_menu_order, n_cols=2))

# Создание кнопок подтверждения
all_food = [(food.food_title, food.description, food.price, food.path_img) for food in db_sess.query(Food).all()]

accept_list_menu = [
    InlineKeyboardButton("❌ Нет", callback_data='no'),
    InlineKeyboardButton("✅ Да", callback_data='yes'),
]
accept_menu_buttons = InlineKeyboardMarkup(build_menu(accept_list_menu, n_cols=2))

# Создание кнопок перелистывания
scroll_list_menu = [
    InlineKeyboardButton("◀", callback_data='prev'),
    InlineKeyboardButton("▶️", callback_data='next'),
    InlineKeyboardButton("◀ Назад", callback_data='delete_scroll')
]
scroll_menu_buttons = InlineKeyboardMarkup(build_menu(scroll_list_menu, n_cols=2))

# Создание кнопок админ-панели
admin_panel_menu = [
    InlineKeyboardButton("➕ Добавить новое блюдо", callback_data='add_pos_menu'),
    InlineKeyboardButton("➖ Удалить блюдо", callback_data='delete_pos_menu')
]
admin_panel_buttons = InlineKeyboardMarkup(build_menu(admin_panel_menu, n_cols=2))

# Создание кнопок для удаления
delete_pos_list = []
for food in db_sess.query(Food).all():
    delete_pos_list.append(InlineKeyboardButton(food.food_title, callback_data=food.food_title + '_delete'))
delete_pos_list.append(InlineKeyboardButton("◀ Назад", callback_data='back_admin_panel'))
delete_pos_buttons = InlineKeyboardMarkup(build_menu(delete_pos_list, n_cols=2))
back_admin_panel_button = InlineKeyboardMarkup(build_menu([InlineKeyboardButton("◀ Назад",
                                                          callback_data='back_admin_panel')],
                                                          n_cols=1))
