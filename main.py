import telebot
from telebot import types
from morph import *
from data import db_session
from docx import Document
from datetime import datetime, timedelta

bot = telebot.TeleBot('')  # сюда кидать ключ API
db_session.global_init("db/log.db")
delay = {}


@bot.message_handler(commands=['start'])
def welcome(message):
    sticker = open('stickers/hello.webp', 'rb')
    bot.send_sticker(message.chat.id, sticker)
    start_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    b1 = types.KeyboardButton("Морфологический разбор")
    b2 = types.KeyboardButton("Анализ текста")
    start_markup.add(b1, b2)
    bot.send_message(message.chat.id,
                     "Приветствую, {0.first_name}!\nЯ <b>{1.first_name}</b>, могу помочь с морфологическим разбором слов или анализом текста на части речи.".format(
                         message.from_user, bot.get_me()),
                     parse_mode='html', reply_markup=start_markup)


@bot.message_handler(content_types=['text'])
def replying(message):
    if message.chat.type == 'private':
        if message.text == "Морфологический разбор":
            bt1_clicked = bot.reply_to(message, "Введите слово для анализа")
            bot.register_next_step_handler(bt1_clicked, morpying_message)
        elif message.text == "Анализ текста":
            if delay.get(message.from_user.id) is None or \
                    (datetime.now() - delay.get(message.from_user.id)) > timedelta(minutes=2):  # задержка на 2 минуты в использовании анализа текста
                bt2_clicked = bot.reply_to(message, "Отправьте текст сообщением или в форматах .docx/.txt")
                bot.register_next_step_handler(bt2_clicked, analysis)
            else:
                bot.send_message(message.chat.id, "Вы можете анализировать текст раз в 2 минуты")


def morpying_message(message):
    make_note(message)
    if is_russian(message.text):
        for i in range(len(morphying(message))):
            bot.send_message(message.chat.id, morphying(message)[i])
    else:
        bot.send_message(message.chat.id, 'Не слово')


def analysis(message):
    global delay
    try:
        if message.content_type == 'document':
            file_format = message.document.file_name.split('.')[-1]
            if file_format in ['txt', 'docx'] and message.document.file_size < 2000001:
                file = bot.get_file(message.document.file_id)
                downloaded_file = bot.download_file(file.file_path)
                path = 'files/' + message.document.file_name
                with open(path, 'wb') as new:
                    new.write(downloaded_file)
                if file_format == 'txt':
                    f = open(f'files/{message.document.file_name}', encoding='utf-8').readlines()
                    bot.reply_to(message, analyzying(f))
                    delay[message.from_user.id] = datetime.now()
                elif file_format == 'docx':
                    document = Document(f'files/{message.document.file_name}')
                    text = []
                    for par in document.paragraphs:
                        text.append(par.text)
                    delay[message.from_user.id] = datetime.now()
                    bot.reply_to(message, analyzying(text))
            else:
                bot.reply_to(message, 'Файл неподдерживаемого формата')
        else:
            f = message.text.split('\n')
            bot.reply_to(message, analyzying(f))
    except Exception as error:
        print(error)


while True:
    try:
        bot.polling(none_stop=True)

    except Exception as e:
        print(e)
