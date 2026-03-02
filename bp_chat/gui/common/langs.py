
CURRENT_LANG = "ru"
EMPTY_D = {}
W_OBJECTS = set()
CALLBACKS = set()

def change_lang():
    global CURRENT_LANG
    if CURRENT_LANG == 'en':
        CURRENT_LANG = 'ru'
    else:
        CURRENT_LANG = 'en'

    for w, placeHolder in W_OBJECTS:
        tr_w(w, placeHolder)

    for c in CALLBACKS:
        c()

def add_callback(callback):
    CALLBACKS.add(callback)

def tr(text, **kwargs):
    d = LANGS_DICT.get(text, EMPTY_D)
    t = d.get(CURRENT_LANG, None)
    if not t:
        t = text
    return t

def tr_w(w, placeHolder=False):
    W_OBJECTS.add((w, placeHolder))

    if placeHolder:
        if hasattr(w, '_main_text_placeHolder'):
            last_text = w._main_text_placeHolder
        else:
            last_text = w.placeholderText()
    else:
        if hasattr(w, '_main_text'):
            last_text = w._main_text
        else:
            last_text = w.text()

    new_text = tr(last_text)
    if placeHolder:
        if not hasattr(w, '_main_text_placeHolder'):
            w._main_text_placeHolder = last_text
        w.setPlaceholderText(new_text)
    else:
        if not hasattr(w, '_main_text'):
            w._main_text = last_text
        w.setText(new_text)

    return w


LANGS_DICT = {
    'Loading': {'ru': 'Загрузка'},
    'Please sign in': {'ru': 'Пожалуйста авторизуйтесь'},
    'Connecting': {'ru': 'Соединение'},
    'Update': {'ru': 'Обновить'},
    'You can be updated. Do you want to restart application now?': {
        'ru': 'Для обновления необходимо перезагрузить приложение. Продолжить?'},
    'Choose file': {'ru': 'Выберите файл'},
    'Exiting from {}': {'ru': 'Выход из {}'},
    'Are you sure you want to close the application?\n\nYou can simply minimize it, if not.': {
        'ru': 'Вы уверены, что хотите закрыть приложение?\n\nЕсли нет, можете просто свернуть его.'},
    'New message': {'ru': 'Новое сообщение'},
    'Add to Autostart': {'ru': 'Добавить в Автозагрузку'},
    'Remove from Autostart': {'ru': 'Убрать из Автозагрузки'},
    'Answer': {'ru': 'Ответить'},
    'Resend': {'ru': 'Переслать'},
    'Copy': {'ru': 'Копировать'},
    'From favorites': {'ru': 'Из избранного'},
    'To favorites': {'ru': 'В избранное'},
    'Show all': {'ru': 'Показать все'},
    'Show only files': {'ru': 'Только файлы'},
    'Show only favorites': {'ru': 'Только избранное'},
    'Create group': {'ru': 'Создать группу'},
    'Create new Group': {'ru': 'Создать группу'},
    'Edit user': {'ru': 'Редактировать пользователя'},
    'Show profile': {'ru': 'Профиль пользователя'},
    'Disconnect user': {'ru': 'Отсоединить пользователя'},
    'Edit group': {'ru': 'Редактировать группу'},
    'Remove group': {'ru': 'Выйти из группы'},
    'Edit guest': {'ru': 'Редактировать гостя'},
    'Refresh chats': {'ru': 'Обновить'},
    'Mute': {'ru': 'Выключить уведомления'},
    'Unmute': {'ru': 'Включить уведомления'},
    'Mark all read': {'ru': 'Отметить все прочитано'},
    'Unmark all read': {'ru': 'Вернуть прочитанность'},
    'Remove from pinned': {'ru': 'Открепить'},
    'Add to pinned': {'ru': 'Закрепить'},
    'Disconnect': {'ru': 'Отсоединиться от сервера'},
    'Logout': {'ru': 'Выйти'},
    'ALL': {'ru': 'ВСЕ'},
    'GROUPS': {'ru': 'ГРУППЫ'},
    'CONTACTS': {'ru': 'КОНТАКТЫ'},
    'Settings': {'ru': 'Меню'}, # FIXME
    'UPDATE': {'ru': 'ОБНОВИТЬ'},
    'Sign In': {'ru': 'Вход'},
    'Login': {'ru': 'Войти'},
    'Set server': {'ru': 'Выбрать сервер'},
    'Name:': {'ru': 'Имя:'},
    'Password:': {'ru': 'Пароль:'},
    'Confirm password:': {'ru': 'Подтвердить пароль:'},
    'Register': {'ru': 'Зарегистрироваться'},
    'Do you have BP Chat Server?': {'ru': 'У Вас есть "BP Chat Server"?'},
    'Ask your administrator. Or download it from <a href="https://bp.compas.ru/app/bp-chat/server/">here</a>': {
        'ru': 'Спросите системного администратора. Или скачайте <a href="https://bp.compas.ru/app/bp-chat/server/">отсюда</a>'},
    'Save': {'ru': 'Сохранить'},
    'Group name field is empty': {'ru': 'Не выбрано имя группы'},
    'Group members are not selected': {'ru': 'Не выбраны участники группы'},
    'Input chat name': {'ru': 'Введите имя группы'},
    'Input members': {'ru': 'Найти пользователей'},
    'Show all users': {'ru': 'Показать всех'},
    'OK': {'ru': 'Сохранить'},
    'CANCEL': {'ru': 'Отменить'},
    'show only online': {'ru': 'показать только онлайн'},
    'Load more messages': {'ru': 'Загрузить еще сообщений'},
    'Select chat': {'ru': 'Выберите чат'},
    'OPEN FILE': {'ru': 'ОТКРЫТЬ ФАЙЛ'},
    'OPEN IN FOLDER': {'ru': 'ОТКРЫТЬ В ПАПКЕ'},
    'RELOAD': {'ru': 'ЗАГРУЗИТЬ ЗАНОВО'},
    'CLOSE': {'ru': 'ЗАКРЫТЬ'},
    'File downloaded:': {'ru': 'Файл загружен'},
    'Choose photo': {'ru': 'Выберите фото'},
    'Change login': {'ru': 'Изменить логин'},
    'Please input new login here:': {'ru': 'Пожалуйста введите новый логин:'},
    'Change user type': {'ru': 'Изменить тип пользователя'},
    'Select one of types list': {'ru': 'Выберите из списка'},
    'Phones': {'ru': 'Телефоны'},
    'Mails': {'ru': 'Адреса почты'},
    'Profile': {'ru': 'Профиль'},
    'TAKE CHAT from': {'ru': 'ЗАБРАТЬ ЧАТ у'},
    'TAKE CHAT': {'ru': 'ВЗЯТЬ ЧАТ'},
    'Find in chat': {'ru': 'Искать в чате'},
    'Clear find in chat': {'ru': 'Очистить поиск в чате'},
'': {'ru': ''},
}

