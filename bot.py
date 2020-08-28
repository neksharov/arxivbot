import config
import telebot
import arxiv
import sqlite3
from sqlite3 import Error
from time import sleep, ctime


bot = telebot.TeleBot(config.token)

max_results = 0
theme = ''
titles = []
id = []
last = []

def post_sql_query(sql_query):
    with sqlite3.connect('arxiv.db') as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(sql_query)
        except Error:
            pass
        result = cursor.fetchall()
        return result


def create_tables():
    users_query = '''CREATE TABLE IF NOT EXISTS USERS 
                        (user_id INTEGER PRIMARY KEY NOT NULL,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        reg_date TEXT);'''
    post_sql_query(users_query)


def register_user(user, username, first_name, last_name):
    user_check_query = f'SELECT * FROM USERS WHERE user_id = {user};'
    user_check_data = post_sql_query(user_check_query)
    if not user_check_data:
        insert_to_db_query = f'INSERT INTO USERS (user_id,' \
                             f' username, first_name,' \
                             f'  last_name, reg_date)' \
                             f' VALUES ({user}, "{username}",' \
                             f' "{first_name}", "{last_name}",' \
                             f' "{ctime()}");'
        post_sql_query(insert_to_db_query)


create_tables()


@bot.message_handler(commands=['start'])
def start(message):
    register_user(message.from_user.id, message.from_user.username,
                  message.from_user.first_name, message.from_user.last_name)
    bot.send_message(message.from_user.id, f'Welcome  {message.from_user.first_name}' )


def get_papers(text):
    block = arxiv.query(query=text, max_results=max_results, sort_by = 'submittedDate')
    for i in range(len(block)):
        titles.append(block[i]['title'])
        id.append(block[i]['id'])
        last.append(block[i]['arxiv_primary_category']['term'])


@bot.message_handler(commands=["start"])
def default_test(message):
    bot.send_message(message.chat.id, "Привет! Введи название интересующей тебя области.")


@bot.message_handler(content_types=["text"])
def answer(message):
    global theme
    block = arxiv.query(query=message.text, max_results=1)
    if bool(block) == False:
        bot.send_message(message.chat.id, "К сожалению, подобной темы не найдено. Попробуйте ещё раз.")
    else:
        theme = message.text
        bot.send_message(message.chat.id, 'Введите число результатов в выдаче')
        bot.register_next_step_handler(message, number)


def number(message):
    global max_results
    global theme
    if not message.text.isdigit():
        bot.send_message(message.chat.id, "Введите число.")
        bot.register_next_step_handler(message, number)
        return
    elif int(message.text) == 0:
        bot.send_message(message.chat.id, "Я не могу выдать нулевое число запросов. Попробуйте ещё раз")
        bot.register_next_step_handler(message, number)
        return
    elif int(message.text) > 25:
        bot.send_message(message.chat.id, "Я не могу выдать больше 25 запросов. Попробуйте ещё раз.")
        bot.register_next_step_handler(message, number)
        return
    else:
        max_results = int(message.text)
        get_papers(theme)
        bot.send_message(message.chat.id, "Последние статьи по твоей теме:")
        for i in range(0, max_results):
            bot.send_message(message.chat.id, titles[i])
            bot.send_message(message.chat.id, id[i])
        titles.clear()
        id.clear()
        max_results = 0
        theme = ''


if __name__ == '__main__':
    bot.infinity_polling()