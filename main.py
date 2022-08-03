import telebot
from telebot import types
import pandas as pd
import os
import random

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

#_______________initializing the bot and DBs___________________

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///psychometry.db'
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    def _repr_(self):
        return 'User ' + str(self.id)


'''NEW PART - END'''

API_KEY = '***********'
bot = telebot.TeleBot(API_KEY)

INITIAL_MESSAGE = "Hello! \n Welcome to the Psychometric Bot!"

xls = pd.ExcelFile(os.getcwd() + '/DB.xlsx')
engQuestions = pd.read_excel(xls, 'engBuiltQuestions')
engVoc = pd.read_excel(xls, 'wordVoc')


@bot.poll_answer_handler(func=lambda pollAnswer: True)
def get_poll_answer(poll_answer):
    # print(poll_answer.poll_id)
    return poll_answer


@bot.message_handler(commands=['start'])
def start(message):
    '''Welcome message'''
    bot.send_message(message.chat.id, INITIAL_MESSAGE)
    main_menu(message.chat.id)

#__________________English questions functions_______________________


def eng_built(chat_id, num_samples=1, qtype="eng_com"):
    """
    Sending English sentences completion / rephrase questions.

    :param chat_id: the user's chat id to send the message to.
    :param num_samples: the number of questions to send.
    """
    question, options, correct_option_id = get_rand_sample_info_eng_built(num_samples=num_samples, qtype=qtype)
    for i in range(num_samples):
        bot.send_message(chat_id, "Question:\n" + question[i] + "\n Answers:"
                                  "\n A: " + options[i][0] +
                                  "\n B: " + options[i][1] +
                                  "\n C: " + options[i][2] +
                                  "\n D: " + options[i][3])
        bot.send_poll(int(chat_id),
                      type='quiz',
                      question="Choose the correct answer",
                      options=["A", "B", "C", "D"],
                      correct_option_id=correct_option_id[i],
                      is_anonymous=False)


def get_rand_sample_info_eng_built(num_samples=1, qtype="eng_com"):
    """
    Generating English English sentences completion / rephrase questions.

    :param num_samples: the number of questions to send.
    :return: the question in quiz poll format.
    """
    data = engQuestions.copy()
    data = data[data['type'] == qtype]


    samples = data.sample(n=num_samples)
    question, options, correct_option_id = [], [], []
    for i in range(num_samples):
        question.append(samples['question'].iloc[i])
        options.append([
            samples['answer1'].iloc[i], samples['answer2'].iloc[i],
            samples['answer3'].iloc[i], samples['answer4'].iloc[i]
        ])
        correct_option_id.append(samples['correct_answer'].iloc[i] - 1)
    return question, options, correct_option_id


def eng_voc(chat_id, unit, num_samples=1, qtype=0):
    """
    Sending English vocabulary translation questions by unit.

    :param chat_id: the user's chat id to send the message to.
    :param unit: the unit which the vocabulary comes from: 0 => all units | other integer => specific unit number.
    :param num_samples: the number of questions to send.
    :param qtype: the direction of translation: 0 => English to Hebrew | 1 => hebrew to english
    """
    question, options, correct_option_id = get_rand_sample_info_eng_voc(qtype=qtype,
                                                                        unit=unit, num_samples=num_samples)
    for i in range(num_samples):
        bot.send_poll(int(chat_id),
                      type='quiz',
                      question=question[i],
                      options=[options[i][0], options[i][1], options[i][2], options[i][3]],
                      correct_option_id=correct_option_id[i],
                      is_anonymous=False)


def get_rand_sample_info_eng_voc(unit, num_samples=1, qtype=0):
    """
    Generating English vocabulary translation questions by unit.

    :param unit: the unit which the vocabulary comes from: 0 => all units | other integer => specific unit number.
    :param num_samples: the number of questions to send.
    :param qtype: the direction of translation: 0 => English to Hebrew | 1 => hebrew to english.
    :return: the question in quiz poll format.
    """
    data = engVoc.copy()
    col_names = ('english', 'hebrew')

    if qtype == 0:
        main, secondary = col_names
    else:
        main, secondary = col_names[::-1]

    if unit != 0:
        data = data[data['unit'] == unit]

    valid_sample = False
    for i in range(3):
        samples = data.sample(n=4*num_samples)
        if samples['english'].nunique() == 4*num_samples:
            valid_sample = True
            break

    if not valid_sample:
        samples = data.groupby(
            col_names[0]).apply(lambda df: df.sample(1)).sample(n=4*num_samples)
    options = samples[secondary].to_list()
    options = [options[i:i+4] for i in range(0, len(options), 4)]
    correct_option_id = [random.randint(0, 3) for i in range(num_samples)]
    question = ["Choose the correct translation of the word:\n" + str(samples[main].iloc[index * 4 + i]) for index,
                i in enumerate(correct_option_id)]
    return question, options, correct_option_id


def mix_voc(chat_id, unit, num_samples=1):
    """
    Generating a random translation direction (Hebrew->English or English->Hebrew).

    :param chat_id: the user's chat id to send the message to.
    :param unit: the unit which the vocabulary comes from: 0 => all units | other integer => specific unit number.
    :param num_samples: the number of questions to send.
    """
    random_list = [random.randint(0, 1) for i in range(num_samples)]
    x, y = random_list.count(0), random_list.count(1)

    if x != 0:
        eng_voc(chat_id, unit, x, 0)
    if y != 0:
        eng_voc(chat_id, unit, y, 1)


def full_mix(chat_id, num_samples=1):
    """
    Sending random English questions: translation, sentence completion / rephrase.

    :param chat_id: the user's chat id to send the message to.
    :param num_samples: the number of questions to send.
    """
    random_list = [random.randint(0, 3) for i in range(num_samples)]
    x, y, z, t = random_list.count(0), random_list.count(1), random_list.count(2), random_list.count(3)

    if x != 0:
        eng_built(chat_id, x, "eng_com")
    if y != 0:
        eng_voc(chat_id, 0, y, 0)
    if z != 0:
        eng_voc(chat_id, 0, z, 1)
    if t != 0:
        eng_built(chat_id, t, "eng_rephrase")

# _______________________________menus_________________________________


# menus dictionary in order to number them
menus_num = {
    'Main': '1',
    'Repeat': '2',
    'English': '3',
    'Hebrew': '4',
    'Math': '5',
    'Combine': '6',
    'EnglishVoc': '7',
    'Unit': '8',
    'Amount': '9'
}


def format_menu_callback(menu_num, pick):
    """
    Generating current selection in "menu_number|selection&" format in order to easily concat the
    "user's route of selections" through the menu.
    The user's route of selection format: "menu1|selection1&menu2|selection2&...&last_menu|last_selection".

    :param menu_num: the number of the menu where the selection was made in the menus_num dictionary.
    :param pick: the option number that was selected.
    :return: ready to concatenation string in "menu_num|pick&" format.
    """
    return menu_num + '|' + str(pick) + '&'


def main_menu(chat_id):
    """
    The main menu(1): here the user can select which subject to practice.

    :param chat_id: user's chat id
    """
    btn_1 = types.InlineKeyboardButton('אנגלית',
                                       callback_data=format_menu_callback(
                                           menus_num['Main'], 1))
    btn_2 = types.InlineKeyboardButton('עברית',
                                       callback_data=format_menu_callback(
                                           menus_num['Main'], 2))
    btn_3 = types.InlineKeyboardButton('חשבון',
                                       callback_data=format_menu_callback(
                                           menus_num['Main'], 3))
    btn_4 = types.InlineKeyboardButton('הכל',
                                       callback_data=format_menu_callback(
                                           menus_num['Main'], 4))
    a = [[btn_1], [btn_2, btn_3], [btn_4]]
    buttons = types.InlineKeyboardMarkup(a)
    bot.send_message(chat_id,
                     "Which subject do you want to learn?",
                     reply_markup=buttons)


def english_main_menu(chat_id, selection_status):
    """
    English main menu(3): here the user can select which type of English questions he wants.

    :param chat_id: the user's chat id.
    :param selection_status: current route of selection as described above (see: format_menu_callback).
    """
    btn_1 = types.InlineKeyboardButton(
        'תרגום אוצר מילים',
        callback_data=selection_status + format_menu_callback(menus_num["English"], 1))

    btn_2 = types.InlineKeyboardButton(
        'השלמת משפטים',
        callback_data=selection_status + format_menu_callback(menus_num["English"], 2))

    btn_3 = types.InlineKeyboardButton(
        'ערבוב תרגילים',
        callback_data=selection_status + format_menu_callback(menus_num["English"], 3))

    btn_4 = types.InlineKeyboardButton(
        'unseen',
        callback_data=selection_status + format_menu_callback(menus_num["English"], 4))

    btn_5 = types.InlineKeyboardButton(
        'ניסוח משפט מחדש',
        callback_data=selection_status + format_menu_callback(menus_num["English"], 5))

    a = [[btn_1], [btn_2, btn_5], [btn_4, btn_3]]
    buttons = types.InlineKeyboardMarkup(a)
    bot.send_message(chat_id, "What do you want to do?", reply_markup=buttons)


def english_voc_menu(chat_id, selection_status):
    """
      English vocabulary menu(7): here the user can select the language direction of translation.

      :param chat_id: the user's chat id.
      :param selection_status: current route of selection as described above (see: format_menu_callback).
      """
    btn_1 = types.InlineKeyboardButton(
        'תרגום אגנלית לעברית',
        callback_data=selection_status + format_menu_callback(menus_num["EnglishVoc"], 1))
    btn_2 = types.InlineKeyboardButton(
        'תרגום עברית לאנגלית',
        callback_data=selection_status + format_menu_callback(menus_num["EnglishVoc"], 2))
    btn_3 = types.InlineKeyboardButton(
        'תרגום אנגלית <-> עברית',
        callback_data=selection_status + format_menu_callback(menus_num["EnglishVoc"], 3))
    a = [[btn_1, btn_2], [btn_3]]
    buttons = types.InlineKeyboardMarkup(a)
    bot.send_message(chat_id,
                     "Choose translate direction",
                     reply_markup=buttons)


def unit_num_menu(chat_id, selection_status):
    #TODO: when Math and Hebrew will be added, transform the num of units from constant to adapting through the DB.
    """
    Unit number menu(8): here the user can select from which unit in the DB the questions will be generated.

    :param chat_id: the user's chat id.
    :param selection_status: current route of selection as described above (see: format_menu_callback).
    """

    a = []
    num_of_units = 10
    all_units_btn = types.InlineKeyboardButton(
        "הכל",
        callback_data=selection_status +
                      format_menu_callback(menus_num["Unit"], 0))
    for i in range(num_of_units // 3):  # known that there are more than 3
        btn_1 = types.InlineKeyboardButton(3 * i + 1,
                                           callback_data=selection_status + format_menu_callback(menus_num["Unit"],
                                                                                                 3 * i + 1))
        btn_2 = types.InlineKeyboardButton(3 * i + 2,
                                           callback_data=selection_status + format_menu_callback(menus_num["Unit"],
                                                                                                 3 * i + 2))
        btn_3 = types.InlineKeyboardButton(3 * i + 3,
                                           callback_data=selection_status + format_menu_callback(menus_num["Unit"],
                                                                                                 3 * i + 3))
        a.append([btn_1, btn_2, btn_3])

    if (num_of_units % 3) == 0:
        a.append([all_units_btn])

    if (num_of_units % 3) == 2:
        btn_1 = types.InlineKeyboardButton(
            num_of_units - 1,
            callback_data=selection_status + format_menu_callback(menus_num["Unit"], num_of_units - 1))

        btn_2 = types.InlineKeyboardButton(
            num_of_units,
            callback_data=selection_status + format_menu_callback(menus_num["Unit"], num_of_units))
        a.append([btn_1, btn_2, all_units_btn])

    if (num_of_units % 3) == 1:
        btn_1 = types.InlineKeyboardButton(
            num_of_units,
            callback_data=selection_status + format_menu_callback(menus_num["Unit"], num_of_units))

        a.append([btn_1, all_units_btn])

    buttons = types.InlineKeyboardMarkup(a)
    bot.send_message(chat_id,
                     "Please choose unit number:",
                     reply_markup=buttons)


def amount_menu(chat_id, selection_status):
    """
    amount menu(9): here the user can select how many questions will be generated.

    :param chat_id: the user's chat id.
    :param selection_status: current route of selection as described above (see: format_menu_callback).
    """
    btn_1 = types.InlineKeyboardButton(text='1',
                                       callback_data=selection_status + format_menu_callback(menus_num["Amount"], 1))
    btn_2 = types.InlineKeyboardButton(text='5',
                                       callback_data=selection_status + format_menu_callback(menus_num["Amount"], 5))
    btn_3 = types.InlineKeyboardButton(text='10',
                                       callback_data=selection_status + format_menu_callback(menus_num["Amount"], 10))
    empty_button = types.InlineKeyboardButton('בהצלחה \uE404',
                                              callback_data="null")
    a = [[btn_1, btn_2, btn_3], [empty_button]]
    buttons = types.InlineKeyboardMarkup(a)
    bot.send_message(chat_id,
                     "How many questions do you want?",
                     reply_markup=buttons)


def repeat_menu(chat_id, selection_status):
    """
    repeat menu(2): here the user can select either to go back the to main menu or run his last selection again.

    :param chat_id: the user's chat id.
    :param selection_status: current route of selection as described above (see: format_menu_callback).
    """
    btn_1 = types.InlineKeyboardButton(text='תפריט', callback_data=selection_status + format_menu_callback(menus_num['Repeat'], 1))
    btn_2 = types.InlineKeyboardButton(text='שוב פעם', callback_data=selection_status)
    a = [[btn_1], [btn_2]]
    buttons = types.InlineKeyboardMarkup(a)
    bot.send_message(chat_id, "Again or Menu?", reply_markup=buttons)


#_______________________handling user's selections (callbacks)_________________________

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    """
    Catching user's action and calling the next function / menu accordingly.

    :param call: the user's last action
    """

    chat_id = call.message.chat.id

    #creating a list of all the user's selections, and keeping his last menu and selection in another
    split_list = call.data.split("&")[:-1]
    last_menu = split_list[-1].split("|")[0]
    last_selection = split_list[-1].split("|")[1]

    # _____navigation through menus________
    if last_menu == menus_num['Main'] and last_selection == '1':
        english_main_menu(chat_id, call.data)
    # if last_menu == menus_num['Main'] and last_selection == '2':
    #     math_main_menu(chat_id,call.data)
    # if last_menu == menus_num['Main'] and last_selection == '3':
    #     hebrew_main_menu(chat_id,call.data)
    # if last_menu == menus_num['Main'] and last_selection == '4':
    #     all_main_menu(chat_id,call.data)

    #repeat_menu -> main_menu
    elif last_menu == menus_num['Repeat'] and last_selection == '1':
        main_menu(chat_id)

    #english_main_menu -> english_voc_menu
    elif last_menu == menus_num['English'] and last_selection == '1':
        english_voc_menu(chat_id, call.data)

    #english_main_menu -> amount_menu (english sentence completion selected)
    elif last_menu == menus_num['English'] and last_selection == '2':
        amount_menu(chat_id, call.data)

    #english_main_menu -> amount_menu (english mix selected)
    elif last_menu == menus_num['English'] and last_selection == '3':
        amount_menu(chat_id, call.data)

    # elif last_menu == menus_num['English'] and last_selection == '4': //unseen - maybe auto 1
    #    amount_menu(chat_id,call.data)

    # english_main_menu -> amount_menu (english rephrase selected)
    elif last_menu == menus_num['English'] and last_selection == '5':
       amount_menu(chat_id,call.data)

    #english_voc_menu -> unit_menu
    elif last_menu == menus_num['EnglishVoc'] and last_selection in ('1', '2', '3'):
        unit_num_menu(chat_id, call.data)

    #unit_menu -> amount menu
    elif last_menu == menus_num["Unit"]:
        amount_menu(chat_id, call.data)





    # ________calling questions functions_____________
    else:
        n = get_menu_info(split_list, 'Amount') #the number of questions to generate
        if menus_num["English"] + "|2" in split_list:
            eng_built(chat_id, n, "eng_com")

        elif menus_num["English"] + "|3" in split_list:
            full_mix(chat_id, n)

        elif menus_num["English"] + "|5" in split_list:
            eng_built(chat_id, n, "eng_rephrase")

        # unseen

        unit = get_menu_info(split_list, 'Unit')
        if menus_num["EnglishVoc"] + "|1" in split_list:
            eng_voc(chat_id, unit, n, 0)

        if menus_num["EnglishVoc"] + "|2" in split_list:
            eng_voc(chat_id, unit, n, 1)

        if menus_num["EnglishVoc"] + "|3" in split_list:
            mix_voc(chat_id, unit, n)

        repeat_menu(chat_id, call.data)


def get_menu_info(split_list, name_menu):
    '''
    returns the selection of the user in asked menu

    :param split_list: the list of the users selections in menus.
    :param name_menu: the asked menu.
    :return: the selection in the asked menu.
    '''
    for word in split_list:
        x, y = word.split('|')
        if x == menus_num[name_menu]:
            return int(y)
    return None


@bot.message_handler()
def recieve(message):
    """brings up the main menu if the user sends a text message"""

    main_menu(message.chat.id)


bot.polling()