# -*- coding: utf-8 -*-

import telebot
import config as cfg
import cherrypy
from ml import Model
from threading import Timer

bot = telebot.TeleBot(cfg.token)
model = Model()

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


def check_confirmation(conf_res, expected, message):
    if conf_res == 1:
        if expected == 'confirmation':
            text = "В ближайшее время на ваш вопрос ответит оператор"
        elif expected == 'query':
            return 'Я жду вопроса ^_^'
        else:
            text = "Error"
        text = check_currency(text, env_var['last_theme'])
        env_var['expected'] = 'query'
        env_var['timer'].cancel()
        print(env_var['timer_desc'] + "  отменён")
    else:
        if expected == 'confirmation':
            text = "Не смогли определить тему вашего вопроса. Попробуйте перефразировать вопрос"
            env_var['expected'] = 'retry'
            print("Awaiting retry")
            env_var['timer'].cancel()
            print(env_var['timer_desc'] + "  отменён")
            env_var['timer'] = Timer(30.0, remind,
                                     [message, "Я все еще хочу вам помочь. Попробуйте перефразировать вопрос."])
            env_var['timer'].start()
            env_var['timer_desc'] = "Ожидание перефразирования в первый раз"
            env_var['try_count'] = 1
        elif expected == 'retry':
            if env_var['try_count'] < 2:
                text = "Не смогли определить тему вашего вопроса. Попробуйте ещё раз"
                env_var['try_count'] += 1
                env_var['timer'].cancel()
                print(env_var['timer_desc'] + "  отменён")
                env_var['timer'] = Timer(30.0, remind,
                                         [message, "Я все еще хочу вам помочь. Попробуйте перефразировать вопрос ещё раз."])
                env_var['timer'].start()
                env_var['timer_desc'] = "Ожидание перефразирования в %d раз" % env_var['try_count']
                print("Try no. %d" % env_var['try_count'])
            else:
                text = "Ок, я запутался, давайте начнём заново :)"
                env_var['expected'] = 'query'
                env_var['try_count'] = 0
                env_var['timer'].cancel()
                print(env_var['timer_desc'] + "  отменён")
        else:
            text = "Problemes"
    return text


def remind(message, text):  # TODO написать
    bot.send_message(message.chat.id, text)
    env_var['timer'] = Timer(180.0, forget)  # TODO поставить 180
    env_var['timer'].start()
    env_var['timer_desc'] = "Ждём чтобы забыть"


def forget():
    env_var['timer'].cancel()
    print(env_var['timer_desc'] + " отменён")
    env_var['expected'] = 'query'


@bot.message_handler(commands=['start'])
def greeting(message):
    greet_text = "Доброе утро, день, вечер или ночь! Я - бот-консультант по финансовым вопросам. Напишите, что вас интересует."
    bot.send_message(message.chat.id, greet_text)


@bot.message_handler(content_types=['text'])
def respond(message):
    global env_var
    markup = None
    text = "Problemes"
    ans_type = classify_answer(message.text.lower())
    if ans_type:
        text = check_confirmation(ans_type, env_var['expected'], message)
    elif env_var['expected'] == 'choice':
        if message.text.lower().split(".")[1] == "никакая из предложенных":
            text = "Не смогли определить тему вашего вопроса. Попробуйте ещё раз"
            env_var['expected'] = 'query'
        else:
            num = int(message.text.lower().split('.')[0])
            if 0 < num < 5:
                text = "В ближайшее время на ваш запрос ответит оператор"
                env_var['expected'] = 'query'
            else:
                text = "Номер темы указан неправильно. Уточните, какая тема вас интересует."
        env_var['timer'].cancel()
        print(env_var['timer_desc'] + ' отменён')
    else:
        if env_var['expected'] == 'retry':
            env_var['context'] = env_var['context'] + ". " + message.text
        elif env_var['expected'] == 'query' or env_var['expected'] == 'choice':
            env_var['context'] = message.text
        else:
            print("Expectations failed. Abort now!")
        print(env_var['context'])
        response = model.get_response(env_var['context'])
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        if len(response) == 1:
            text = "Вас интересует тема \"%s\". Да?" % response[0][1]
            env_var['last_theme'] = response[0][1]
            if env_var['expected'] == 'query':
                env_var['expected'] = 'confirmation'
            if env_var['timer']:
                env_var['timer'].cancel()
                print(env_var['timer_desc'] + " отменён")
            env_var['timer'] = Timer(30.0, remind, [message, "Мне нужен ваш ответ. Напишите \"Да\" или \"Нет\"."])
            env_var['timer'].start()
            env_var['timer_desc'] = "Напомнить про конфёрм"
            markup.add('Да', 'Нет')
        elif len(response) < 5:
            text = "Пожалуйста, уточните, какая из тем вас интересует:"
            i = 0
            for theme in response:
                i += 1
                markup.add("%d. %s" % (i, theme[1]))
            i += 1
            markup.add("%d.Никакая из предложенных" % i)
            env_var['expected'] = 'choice'
            # TODO ДОЛЛАРЫ
            if env_var['timer']:
                env_var['timer'].cancel()
                print(env_var['timer_desc'] + " отменён")
            env_var['timer'] = Timer(30.0, remind, [message, "Мне нужен ваш ответ. Выберите одну из предложенных тем."])
            env_var['timer'].start()
            env_var['desc'] = "Напомнить выбор"
        else:
            text = "Произошла ошибка определения, обратитесь к Рыбкину."

    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.message_handler(content_types=['document'])
def eval_csv(message):
    print(message)
    

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
