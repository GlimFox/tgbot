from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
import sqlite3
import logging
import os


# Логирование для отладки
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Состояния диалога
ASK_PHOTO, ASK_DESCRIPTION, ASK_NAME = range(3)

# Стартовая команда
async def start(update: Update, context):
    await update.message.reply_text("Привет! Пожалуйста, отправь мне свою фотографию.")
    return ASK_PHOTO

# Функция для скачивания фото
async def download_photo(context, file_id, user_id):
    # Создаём путь для сохранения фото
    file_path = f"photos/{user_id}/"
    if not os.path.exists(file_path):
        os.makedirs(file_path)

    # Получаем файл через Telegram API
    new_file = await context.bot.get_file(file_id)
    
    # Сохраняем фото на диск
    file_name = f"{file_path}photo.jpg"
    await new_file.download_to_drive(file_name)
    
    return file_name

# Обработка фотографии
async def handle_photo(update: Update, context):
    photo = update.message.photo[-1].file_id  # Получение последней (самой большой) фотографии
    user_id = update.message.from_user.id
    
    # Скачиваем фото и сохраняем на диск
    photo_path = await download_photo(context, photo, user_id)
    
    # Сохраняем путь к фото в контексте
    context.user_data['photo_path'] = photo_path

    await update.message.reply_text("Теперь напиши описание для этой фотографии.")
    return ASK_DESCRIPTION


# Обработка описания
async def handle_description(update: Update, context):
    description = update.message.text
    context.user_data['description'] = description

    await update.message.reply_text("Теперь укажи свое имя и фамилию.")
    return ASK_NAME

# Обработка имени и фамилии
async def handle_name(update: Update, context):
    user_data = update.message.from_user
    first_name = user_data.first_name
    last_name = user_data.last_name

    context.user_data['first_name'] = first_name
    context.user_data['last_name'] = last_name

    # Сохранение данных в базу данных
    save_data(update.message.from_user.id, context.user_data)

    await update.message.reply_text("Спасибо! Ваши данные сохранены.")
    return ConversationHandler.END

def save_data(user_id, user_data):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Получение данных
    first_name = user_data['first_name']
    last_name = user_data['last_name']
    description = user_data['description']
    photo_path = user_data['photo_path']  # Путь к сохранённому фото

    # Сохранение в базу данных
    cursor.execute('''
        INSERT INTO users (user_id, first_name, last_name, description, photo)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, first_name, last_name, description, photo_path))

    conn.commit()
    conn.close()


# Команда отмены
async def cancel(update: Update, context):
    await update.message.reply_text("Процесс отменен.")
    return ConversationHandler.END


def main():
    # Ваш токен
    TOKEN = "7534438139:AAEJeAofM0IPOgiW2SkEoQT2BEuAv_Uo64E"

    # Создание приложения
    application = Application.builder().token(TOKEN).build()

    # Обработка команд
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASK_PHOTO: [MessageHandler(filters.PHOTO, handle_photo)],
            ASK_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_description)],
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(conv_handler)

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()