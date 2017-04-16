# -*- coding: utf-8 -*-

import telebot
import config as cfg
import cherrypy
import requests
import os
from ml import Model
from threading import Timer

bot = telebot.TeleBot(cfg.token)
model = Model()

users = {}

env_var = {
    'last_theme': None,
    'get_response': None,
    'expected': 'query',
    'timer': None,
    'timer_desc': '',
    'try_count': 0,
    'context': None
}

'''
class WebhookServer(object):
    @cherrypy.expose
    def index(self):
        if 'content-length' in cherrypy.request.headers and \
                        'content-type' in cherrypy.request.headers and \
                        cherrypy.request.headers['content-type'] == 'application/json':
            length = int(cherrypy.request.headers['content-length'])
            json_string = cherrypy.request.body.read(length).decode("utf-8")
            update = telebot.types.Update.de_json(json_string)
            # Эта функция обеспечивает проверку входящего сообщения (скорее всего это так)
            bot.process_new_updates([update])
            return ''
        else:
            raise cherrypy.HTTPError(403)
'''


def check_currency(text, lt):
    if lt == 'Курс доллара':
        text = "Текущий курс доллара: 65 рублей. " + text
    elif lt == 'Курс евро':
        text = "Текущий курс евро: 70 рублей. " + text
    return text


def classify_answer(mtext):
    yes_mes = ['да', 'конечно', 'угадал', 'точно', 'верно', 'ага']
    no_mes = ['нет', 'неа', 'ошибка', 'ошибаешься', 'не']
    if mtext in yes_mes:
        return 1
    elif mtext in no_mes:
        return 2
    return 0


def check_confirmation(conf_res, expected, user_id):
    if conf_res == 1:
        if expected in ['confirmation', 'retry']:
            text = "В ближайшее время на ваш вопрос ответит оператор"
        elif expected == 'query':
            return 'Я жду вопроса ^_^'
        else:
            text = "Error"
        text = check_currency(text, users[user_id]['last_theme'])
        users[user_id]['expected'] = 'query'
        users[user_id]['timer'].cancel()
        print(users[user_id]['timer_desc'] + "  отменён")
    else:
        if expected == 'confirmation':
            text = "Не смогли определить тему вашего вопроса. Попробуйте перефразировать вопрос"
            users[user_id]['expected'] = 'retry'
            print("Awaiting retry")
            users[user_id]['timer'].cancel()
            print(users[user_id]['timer_desc'] + "  отменён")
            users[user_id]['timer'] = Timer(30.0, remind,
                                    [user_id, "Я все еще хочу вам помочь. Попробуйте перефразировать вопрос."])
            users[user_id]['timer'].start()
            users[user_id]['timer_desc'] = "Ожидание перефразирования в первый раз"
            users[user_id]['try_count'] = 1
        elif expected == 'retry':
            if users[user_id]['try_count'] < 2:
                text = "Не смогли определить тему вашего вопроса. Попробуйте ещё раз"
                users[user_id]['try_count'] += 1
                users[user_id]['timer'].cancel()
                print(users[user_id]['timer_desc'] + "  отменён")
                users[user_id]['timer'] = Timer(30.0, remind,
                                         [user_id, "Я все еще хочу вам помочь. Попробуйте перефразировать вопрос ещё раз.", True])
                users[user_id]['timer'].start()
                users[user_id]['timer_desc'] = "Ожидание перефразирования в %d раз" % users[user_id]['try_count']
                print("Try no. %d" % users[user_id]['try_count'])
            else:
                text = "Ок, я запутался, давайте начнём заново :)"
                users[user_id]['expected'] = 'query'
                users[user_id]['try_count'] = 0
                users[user_id]['timer'].cancel()
                print(users[user_id]['timer_desc'] + "  отменён")
        else:
            text = "Problemes"
    return text


def remind(user_id, text, fail=False):  # TODO написать
    bot.send_message(user_id, text)
    users[user_id]['timer'] = Timer(180.0, forget, [user_id, fail])  # TODO поставить 180
    users[user_id]['timer'].start()
    users[user_id]['timer_desc'] = "Ждём чтобы забыть"


def forget(user_id, fail=False):
    users[user_id]['timer'].cancel()
    if fail:
        bot.send_message(user_id, "Ок, похоже, мы оба запутались. Давайте начнём заново :)")
    print(users[user_id]['timer_desc'] + " отменён")
    users[user_id]['expected'] = 'query'


@bot.message_handler(commands=['start'])
def greeting(message):
    greet_text = "Доброе утро, день, вечер или ночь! Я - бот-консультант по финансовым вопросам. Напишите, что вас интересует."
    bot.send_message(message.chat.id, greet_text)


@bot.message_handler(content_types=['text'])
def respond(message):
    global env_var, users
    user_id = message.chat.id
    if user_id not in users.keys():
        users[user_id] = {
            'last_theme': None,
            'get_response': None,
            'expected': 'query',
            'timer': None,
            'timer_desc': '',
            'try_count': 0,
            'context': None
        }

    markup = None
    text = "Problemes"
    ans_type = classify_answer(message.text.lower())
    if ans_type:
        text = check_confirmation(ans_type, users[user_id]['expected'], user_id)
    elif users[user_id]['expected'] == 'choice':
        if message.text.lower().split(".")[1] == "никакая из предложенных":
            text = "Не смогли определить тему вашего вопроса. Попробуйте ещё раз"
            users[user_id]['expected'] = 'query'
        else:
            num = int(message.text.lower().split('.')[0])
            if 0 < num < 5:
                text = "В ближайшее время на ваш запрос ответит оператор"
                users[user_id]['expected'] = 'query'
            else:
                text = "Номер темы указан неправильно. Уточните, какая тема вас интересует."
        users[user_id]['timer'].cancel()
        print(users[user_id]['timer_desc'] + ' отменён')
    else:
        if users[user_id]['expected'] == 'retry':
            users[user_id]['context'] = users[user_id]['context'] + ". " + message.text
        elif users[user_id]['expected'] == 'query' or users[user_id]['expected'] == 'choice':
            users[user_id]['context'] = message.text
        else:
            print("Expectations failed. Abort now!")
        print(users[user_id]['context'])
        response = model.get_response(users[user_id]['context'])
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        if len(response) == 1:
            text = "Вас интересует тема \"%s\". Да?" % response[0][1]
            users[user_id]['last_theme'] = response[0][1]
            if users[user_id]['expected'] == 'query':
                users[user_id]['expected'] = 'confirmation'
            if users[user_id]['timer']:
                users[user_id]['timer'].cancel()
                print(users[user_id]['timer_desc'] + " отменён")
            users[user_id]['timer'] = Timer(30.0, remind, [user_id, "Мне нужен ваш ответ. Напишите \"Да\" или \"Нет\"."])
            users[user_id]['timer'].start()
            users[user_id]['timer_desc'] = "Напомнить про конфёрм"
            markup.add('Да', 'Нет')
        elif len(response) < 5:
            text = "Пожалуйста, уточните, какая из тем вас интересует:"
            i = 0
            for theme in response:
                i += 1
                markup.add("%d. %s" % (i, theme[1]))
            i += 1
            markup.add("%d.Никакая из предложенных" % i)
            users[user_id]['expected'] = 'choice'
            # TODO ДОЛЛАРЫ
            if users[user_id]['timer']:
                users[user_id]['timer'].cancel()
                print(users[user_id]['timer_desc'] + " отменён")
            users[user_id]['timer'] = Timer(30.0, remind, [user_id, "Мне нужен ваш ответ. Выберите одну из предложенных тем."])
            users[user_id]['timer'].start()
            users[user_id]['desc'] = "Напомнить выбор"
        else:
            text = "Произошла ошибка определения, обратитесь к Рыбкину."

    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(content_types=['document'])
def eval_csv(message):
    print(message)
    file_info = bot.get_file(message['document']['file_id'])
    file_name = message['document']['file_name']
    f = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(cfg.token, file_info.file_path))
    model.eval_csv(f, file_name)
    out_csv = open(file_name, 'rb')
    bot.send_document(message['chat']['id'], out_csv)
    os.remove(file_name)

'''
bot.remove_webhook()

bot.set_webhook(url=cfg.WEBHOOK_URL_BASE + cfg.WEBHOOK_URL_PATH, certificate=open(cfg.WEBHOOK_SSL_CERT, 'r'))

cherrypy.config.update({
    'server.socket_host': cfg.WEBHOOK_LISTEN,
    'server.socket_port': cfg.WEBHOOK_PORT,
    'server.ssl_module': 'builtin',
    'server.ssl_certificate': cfg.WEBHOOK_SSL_CERT,
    'server.ssl_private_key': cfg.WEBHOOK_SSL_PRIV
})

cherrypy.quickstart(WebhookServer(), cfg.WEBHOOK_URL_PATH, {'/': {}})
'''

if __name__ == '__main__':
    bot.polling(none_stop=True)
