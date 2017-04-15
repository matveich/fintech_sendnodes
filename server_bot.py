# -*- coding: utf-8 -*-

import telebot
import config as cfg
import cherrypy
from ml import Model
from threading import Timer

bot = telebot.TeleBot(cfg.token)

env_var = {
    'last_theme': None,
    'get_response': None,
    'expected': 'query',
    'timer': None
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


def check_confirmation(conf_res, expected):
    if conf_res == 1:
        if expected == 'confirmation':
            text = "В ближайшее время на ваш вопрос ответит оператор"
        elif expected == 'query':
            return 'Я жду вопроса ^_^'
        text = check_currency(text, env_var['last_theme'])
    else:
        text = "Не смогли определить тему вашего вопроса. Попробуйте перефразировать вопрос"
    env_var['expected'] = 'query'
    env_var['timer'].cancel()
    return text


def remind():
    pass

@bot.message_handler(commands=['start'])
def greeting(message):
    greet_text = "Доброе утро, день, вечер или ночь! Я - бот-консультант по финансовым вопросам. Напишите, что вас интересует."
    bot.send_message(message.chat.id, greet_text)


@bot.message_handler(content_types=['text'])
def respond(message):
    global env_var
    text = "Critical Error"
    markup = None
    ans_type = classify_answer(message.text.lower())
    if ans_type:
        text = check_confirmation(ans_type, env_var['expected'])
    # If user didn't check the answer
    else:
        response = env_var['get_response'](message.text)
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        if response['type'] == "get_confirmation":
            text = "Вас интересует тема \"%s\". Да?" % response['pos_themes'][0]
            env_var['last_theme'] = response['pos_themes'][0]
            env_var['expected'] = 'confirmation'
            env_var['timer'] = Timer(30.0, remind)
            markup.add('Да', 'Нет')
        elif response['type'] == "choose_theme":
            text = "Пожалуйста, уточните, какая из тем вас интересует:"
            for theme in response['pos_themes']:
                markup.add(theme)
            markup.add("Никакая из предложенных")

    bot.send_message(message.chat.id, text, reply_markup=markup)

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
    model = Model()
    env_var['get_response'] = model.get_response
    bot.polling(none_stop=True)
