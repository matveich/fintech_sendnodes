# -*- coding: utf-8 -*-

import telebot
import config as cfg
import cherrypy
from ml import Model

bot = telebot.TeleBot(cfg.token)

awaiting_confirm = False

get_response = None


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


@bot.message_handler(commands=['start'])
def greeting(message):
    greet_text = "Доброе утро, день, вечер или ночь! Я - бот-консультант по финансовым вопросам. Напишите, что вас интересует."
    bot.send_message(message.chat.id, greet_text)


@bot.message_handler(content_types=['text'])
def respond(message):
    global get_response
    text = "Critical Error"
    markup = None
    if message.text.lower() == 'да':
        text = "В ближайшее время на ваш вопрос ответит оператор"
    elif message.text.lower() == 'нет':
        text = "Не смогли определить тему вашего вопроса. Попробуйте перефразировать вопрос"
    else:
        response = get_response(message.text)
        if response['type'] == "get_confirmation":
            text = "Вас интересует тема \"%s\". Да?" % response['pos_themes'][0]
            markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add('Да', 'Нет')
        elif response['type'] == "choose_theme":
            markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            text = "Пожалуйста, уточните, какая из тем вас интересует:"
            for theme in response['pos_themes']:
                markup.add(theme)
            markup.add("Никакая из предложенных")

    bot.send_message(message.chat.id, text, reply_markup=markup)


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


if __name__ == '__main__':
    model = Model()
    get_response = model.get_response
    # bot.polling(none_stop=True)
