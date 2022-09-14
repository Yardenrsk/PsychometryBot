import json
import telebot
from telebot import types
import pandas as pd
import os
import random
import session
from menu import MenuType, QuestionType, AmountQuestion, Unit, MenuAnswer, MenuAnswerEncoder

# _______________initializing the bot and DBs___________________

#Connecting to the API using environment variable (also set on the Heroku cloud)
API_TOKEN = os.environ['API_TOKEN']
bot = telebot.TeleBot(API_TOKEN)

INITIAL_MESSAGE = "Hello! \n Welcome to the Psychometric Bot!"

xls = pd.ExcelFile(os.getcwd() + '/DATA/DB.xlsx')
engQuestions = pd.read_excel(xls, 'engBuiltQuestions')
engVoc = pd.read_excel(xls, 'wordVoc')
mathQuestions = pd.read_excel(xls, 'mathBuiltQuestions')
users_sessions = {}


@bot.poll_answer_handler(func=lambda pollAnswer: True)
def get_poll_answer(poll_answer):
    # print(poll_answer.poll_id)
    return poll_answer


@bot.message_handler(commands=['start'])
def start(message):
    '''Welcome message'''
    bot.send_message(message.chat.id, INITIAL_MESSAGE)
    main_menu(message.chat.id)


# __________________English questions functions_______________________


def eng_built(chat_id, num_samples=1, qtype="eng_com"):
    """
    Sending English sentences completion / rephrase questions.
    :param chat_id: the user's chat id to send the message to.
    :param num_samples: the number of questions to send.
    """
    question, options, correct_option_id = get_rand_sample_info_eng_built(num_samples=num_samples, qtype=qtype)
    for i in range(num_samples):
        bot.send_message(chat_id, "Question:\n" + question[i] + "\n\nAnswers:" +
                         "\n\n 1: " + options[i][0] +
                         "\n\n 2: " + options[i][1] +
                         "\n\n 3: " + options[i][2] +
                         "\n\n 4: " + options[i][3])
        bot.send_poll(int(chat_id),
                      type='quiz',
                      question="Choose the correct answer",
                      options=["1", "2", "3", "4"],
                      correct_option_id=correct_option_id[i],
                      is_anonymous=False)



def get_rand_sample_info_eng_built(num_samples=1, qtype="eng_com"):
    """
    Generating English sentences completion / rephrase questions.
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
        samples = data.sample(n=4 * num_samples)
        if samples['english'].nunique() == 4 * num_samples:
            valid_sample = True
            break

    if not valid_sample:
        samples = data.groupby(
            col_names[0]).apply(lambda df: df.sample(1)).sample(n=4 * num_samples)
    options = samples[secondary].to_list()
    options = [options[i:i + 4] for i in range(0, len(options), 4)]
    correct_option_id = [random.randint(0, 3) for i in range(num_samples)]
    question = ["Choose the correct translation of the word:\n" + str(samples[main].iloc[index * 4 + i]) for index,
                                                                                                             i in
                enumerate(correct_option_id)]
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


def eng_full_mix(chat_id, num_samples=1):
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

def math_built(chat_id, num_samples=1, qtype="math_alg"):
    """
    Sending math questions as photos.
    :param chat_id: the user's chat id to send the message to.
    :param num_samples: the number of questions to send.
    """
    question, correct_option_id = get_rand_sample_info_math_built(num_samples=num_samples, qtype=qtype)
    for i in range(num_samples):
        photo = open(question[i], 'rb')
        bot.send_photo(chat_id, photo)
        bot.send_poll(int(chat_id),
                      type='quiz',
                      question="Choose the correct answer",
                      options=["1", "2", "3", "4"],
                      correct_option_id=correct_option_id[i],
                      is_anonymous=False)


def get_rand_sample_info_math_built(num_samples=1, qtype="math_alg"):
    """
    Generating math problems/algebra/geomtery questions.
    :param num_samples: the number of questions to send.
    :return: the question in quiz poll format.
    """
    data = mathQuestions.copy()
    data = data[data['type'] == qtype]

    samples = data.sample(n=num_samples)
    question, correct_option_id = [], []
    for i in range(num_samples):
        question.append(samples['question_dir'].iloc[i])
        correct_option_id.append(samples['correct_answer'].iloc[i] - 1)
    return question, correct_option_id

def math_full_mix(chat_id, num_samples=1):
    """
    Sending random math questions: algebra, geometry and problems.
    :param chat_id: the user's chat id to send the message to.
    :param num_samples: the number of questions to send.
    """
    random_list = [random.randint(0, 3) for i in range(num_samples)]
    x, y, z = random_list.count(0), random_list.count(1), random_list.count(2)

    if x != 0:
        math_built(chat_id, x, "math_alg")
    if y != 0:
        math_built(chat_id, x, "math_geo")
    if z != 0:
        math_built(chat_id, x, "math_prob")

def all_full_mix(chat_id):
    """
    Sending random questions of all subjects (currently without hebrew).
    :param chat_id: the user's chat id to send the message to.
    """
    eng_full_mix(chat_id,num_samples=10)
    math_full_mix(chat_id, num_samples=10)

# _______________________________menus_________________________________
def main_menu(chat_id):
    """
    The main menu(1): here the user can select which subject to practice.
    :param chat_id: user's chat id
    """
    # print(json.dumps(MenuAnswer(MenuType.MAIN, MenuType.ENGLISH),indent=1, cls=MenuAnswerEncoder))
    btn_1 = types.InlineKeyboardButton('אנגלית',
                                       callback_data=json.dumps(MenuAnswer(MenuType.MAIN, MenuType.ENGLISH), indent=1,
                                                                cls=MenuAnswerEncoder))
    btn_2 = types.InlineKeyboardButton('עברית',
                                       callback_data=json.dumps(MenuAnswer(MenuType.MAIN, MenuType.HEBREW), indent=1,
                                                                cls=MenuAnswerEncoder))
    btn_3 = types.InlineKeyboardButton('חשבון',
                                       callback_data=json.dumps(MenuAnswer(MenuType.MAIN, MenuType.MATH), indent=1,
                                                                cls=MenuAnswerEncoder))
    btn_4 = types.InlineKeyboardButton('הכל', callback_data=json.dumps(MenuAnswer(MenuType.MAIN, MenuType.COMBINATION),
                                                                       indent=1, cls=MenuAnswerEncoder))
    a = [[btn_1], [btn_2, btn_3], [btn_4]]
    buttons = types.InlineKeyboardMarkup(a)
    bot.send_message(chat_id,
                     "Which subject do you want to learn?",
                     reply_markup=buttons)


def english_main_menu(chat_id):
    """
    English main menu(3): here the user can select which type of English questions he wants.
    :param chat_id: the user's chat id.
    :param selection_status: current route of selection as described above (see: format_menu_callback).
    """
    btn_1 = types.InlineKeyboardButton('תרגום אוצר מילים',
                                       callback_data=json.dumps(MenuAnswer(MenuType.ENGLISH, MenuType.ENG_VOC),
                                                                indent=1, cls=MenuAnswerEncoder))

    btn_2 = types.InlineKeyboardButton('השלמת משפטים',
                                       callback_data=json.dumps(MenuAnswer(MenuType.ENGLISH, QuestionType.ENG_COM),
                                                                indent=1, cls=MenuAnswerEncoder))

    btn_3 = types.InlineKeyboardButton('ערבוב תרגילים',
                                       callback_data=json.dumps(MenuAnswer(MenuType.ENGLISH, QuestionType.ENG_MIX),
                                                                indent=1, cls=MenuAnswerEncoder))

    btn_4 = types.InlineKeyboardButton('ניסוח משפט מחדש',
                                       callback_data=json.dumps(
                                           MenuAnswer(MenuType.ENGLISH, QuestionType.ENG_REPHRASE), indent=1,
                                           cls=MenuAnswerEncoder))

    a = [[btn_1, btn_2], [btn_3, btn_4]]
    buttons = types.InlineKeyboardMarkup(a)
    bot.send_message(chat_id, "What do you want to do?", reply_markup=buttons)


def english_voc_menu(chat_id):
    """
      English vocabulary menu(7): here the user can select the language direction of translation.
      :param chat_id: the user's chat id.
      :param selection_status: current route of selection as described above (see: format_menu_callback).
      """
    btn_1 = types.InlineKeyboardButton(
        'תרגום אגנלית לעברית',
        callback_data=json.dumps(MenuAnswer(MenuType.ENG_VOC, QuestionType.ENG_VOC_ENG), indent=1,
                                 cls=MenuAnswerEncoder))
    btn_2 = types.InlineKeyboardButton(
        'תרגום עברית לאנגלית',
        callback_data=json.dumps(MenuAnswer(MenuType.ENG_VOC, QuestionType.ENG_VOC_HEB), indent=1,
                                 cls=MenuAnswerEncoder))
    btn_3 = types.InlineKeyboardButton(
        'תרגום אנגלית <-> עברית',
        callback_data=json.dumps(MenuAnswer(MenuType.ENG_VOC, QuestionType.ENG_VOC_MIX), indent=1,
                                 cls=MenuAnswerEncoder))
    a = [[btn_1, btn_2], [btn_3]]
    buttons = types.InlineKeyboardMarkup(a)
    bot.send_message(chat_id,
                     "Choose translate direction",
                     reply_markup=buttons)

def math_main_menu(chat_id):
    """
    Math main menu(3): here the user can select which type of math questions he wants.
    :param chat_id: the user's chat id.
    :param selection_status: current route of selection as described above (see: format_menu_callback).
    """
    btn_1 = types.InlineKeyboardButton('אלגברה',
                                       callback_data=json.dumps(MenuAnswer(MenuType.MATH, QuestionType.MATH_ALGEBRA),
                                                                indent=1, cls=MenuAnswerEncoder))

    btn_2 = types.InlineKeyboardButton('גאומטריה',
                                       callback_data=json.dumps(MenuAnswer(MenuType.MATH, QuestionType.MATH_GEOMETRY),
                                                                indent=1, cls=MenuAnswerEncoder))

    btn_3 = types.InlineKeyboardButton('בעיות מילוליות',
                                       callback_data=json.dumps(MenuAnswer(MenuType.MATH, QuestionType.MATH_PROBLEM),
                                                                indent=1, cls=MenuAnswerEncoder))

    btn_4 = types.InlineKeyboardButton('ערבוב תרגילים',
                                       callback_data=json.dumps(
                                           MenuAnswer(MenuType.MATH, QuestionType.MATH_MIX), indent=1,
                                           cls=MenuAnswerEncoder))

    a = [[btn_1, btn_2], [btn_3, btn_4]]
    buttons = types.InlineKeyboardMarkup(a)
    bot.send_message(chat_id, "What do you want to do?", reply_markup=buttons)


def unit_num_menu(chat_id):
    """
    Unit number menu(8): here the user can select from which unit in the DB the questions will be generated.
    :param chat_id: the user's chat id.
    :param selection_status: current route of selection as described above (see: format_menu_callback).
    """

    a = []
    num_of_units = 10
    all_units_btn = types.InlineKeyboardButton(
        "הכל",
        callback_data=json.dumps(MenuAnswer(MenuType.UNIT, Unit.COMBINATION), indent=1, cls=MenuAnswerEncoder))
    for i in range(num_of_units // 3):  # known that there are more than 3
        btn_1 = types.InlineKeyboardButton(3 * i + 1,
                                           callback_data=json.dumps(MenuAnswer(MenuType.UNIT, Unit(str(3 * i + 1))),
                                                                    indent=1, cls=MenuAnswerEncoder))
        btn_2 = types.InlineKeyboardButton(3 * i + 2,
                                           callback_data=json.dumps(MenuAnswer(MenuType.UNIT, Unit(str(3 * i + 2))),
                                                                    indent=1, cls=MenuAnswerEncoder))
        btn_3 = types.InlineKeyboardButton(3 * i + 3,
                                           callback_data=json.dumps(MenuAnswer(MenuType.UNIT, Unit(str(3 * i + 3))),
                                                                    indent=1, cls=MenuAnswerEncoder))
        a.append([btn_1, btn_2, btn_3])

    if (num_of_units % 3) == 0:
        a.append([all_units_btn])

    if (num_of_units % 3) == 2:
        btn_1 = types.InlineKeyboardButton(
            num_of_units - 1,
            callback_data=json.dumps(MenuAnswer(MenuType.UNIT, Unit(str(num_of_units - 1))), indent=1,
                                     cls=MenuAnswerEncoder))

        btn_2 = types.InlineKeyboardButton(
            num_of_units,
            callback_data=json.dumps(MenuAnswer(MenuType.UNIT, Unit(str(num_of_units))), indent=1,
                                     cls=MenuAnswerEncoder))
        a.append([btn_1, btn_2, all_units_btn])

    if (num_of_units % 3) == 1:
        btn_1 = types.InlineKeyboardButton(
            num_of_units,
            callback_data=json.dumps(MenuAnswer(MenuType.UNIT, Unit(str(num_of_units))), indent=1,
                                     cls=MenuAnswerEncoder))

        a.append([btn_1, all_units_btn])

    buttons = types.InlineKeyboardMarkup(a)
    bot.send_message(chat_id,
                     "Please choose unit number:",
                     reply_markup=buttons)


def amount_menu(chat_id):
    """
    amount menu(9): here the user can select how many questions will be generated.
    :param chat_id: the user's chat id.
    :param selection_status: current route of selection as described above (see: format_menu_callback).
    """
    btn_1 = types.InlineKeyboardButton(text='1',
                                       callback_data=json.dumps(MenuAnswer(MenuType.AMOUNT, AmountQuestion.ONE),
                                                                indent=1, cls=MenuAnswerEncoder))
    btn_2 = types.InlineKeyboardButton(text='5',
                                       callback_data=json.dumps(MenuAnswer(MenuType.AMOUNT, AmountQuestion.FIVE),
                                                                indent=1, cls=MenuAnswerEncoder))
    btn_3 = types.InlineKeyboardButton(text='10',
                                       callback_data=json.dumps(MenuAnswer(MenuType.AMOUNT, AmountQuestion.TEN),
                                                                indent=1, cls=MenuAnswerEncoder))
    empty_button = types.InlineKeyboardButton('בהצלחה \uE404',
                                              callback_data="null")
    a = [[btn_1, btn_2, btn_3], [empty_button]]
    buttons = types.InlineKeyboardMarkup(a)
    bot.send_message(chat_id,
                     "How many questions do you want?",
                     reply_markup=buttons)

def repeat_menu(chat_id):
    """
    repeat menu(2): here the user can select either to go back the to main menu or run his last selection again.
    :param chat_id: the user's chat id.
    :param selection_status: current route of selection as described above (see: format_menu_callback).
    """
    btn_1 = types.InlineKeyboardButton(text='תפריט',
                                       callback_data=json.dumps(MenuAnswer(MenuType.REPEAT, MenuType.MAIN), indent=1,
                                                                cls=MenuAnswerEncoder))
    btn_2 = types.InlineKeyboardButton(text='שוב פעם',
                                       callback_data=json.dumps(MenuAnswer(MenuType.REPEAT, QuestionType.REPEAT),
                                                                indent=1, cls=MenuAnswerEncoder))
    a = [[btn_1], [btn_2]]
    buttons = types.InlineKeyboardMarkup(a)
    bot.send_message(chat_id, "Again or Menu?", reply_markup=buttons)


# _______________________handling user's selections (callbacks)_________________________

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    """
    Catching user's action and calling the next function / menu accordingly.
    :param call: the user's last action
    """
    chat_id = call.message.chat.id
    curr_session = users_sessions.get(chat_id)
    if not curr_session:  # In case its an new user, adding another user to user_sessions
        users_sessions[chat_id] = session.Session()
        curr_session = users_sessions[chat_id]

    call_data = json.loads(call.data)
    menu_answer = MenuAnswer.create_from_call_back(call_data)
    make_action(menu_answer, chat_id)


def make_action(menu_answer, chat_id):
    """
    Change the current session of specific user according to his menu answer
    :param menu_answer: MenuAnswer object which represents the last answer of user
    :param chat_id: User id
    """

    # _____navigation through menus________

    user_session = users_sessions.get(chat_id)
    if menu_answer.option == MenuType.ENGLISH:
        user_session.subject = MenuType.ENGLISH
        english_main_menu(chat_id)

    elif menu_answer.option == MenuType.HEBREW:
        user_session.subject = MenuType.HEBREW
        bot.send_message(chat_id,"Sorry, this options is currently unavailable. Try another option")
        main_menu(chat_id)

    elif menu_answer.option == MenuType.MATH:
        user_session.subject = MenuType.MATH
        math_main_menu(chat_id)

    elif menu_answer.option == MenuType.COMBINATION:
        user_session.subject = MenuType.COMBINATION
        user_session.question_type = QuestionType.FULL_MIX
        call_questions(chat_id)


    # english_main_menu -> english_voc_menu
    elif menu_answer.option == MenuType.ENG_VOC:
        english_voc_menu(chat_id)

    # english_main_menu -> amount_menu (english sentence completion selected)
    elif menu_answer.option == QuestionType.ENG_COM:
        user_session.question_type = menu_answer.option
        amount_menu(chat_id)

    # english_main_menu -> amount_menu (english mix selected)
    elif menu_answer.option == QuestionType.ENG_MIX:
        user_session.question_type = menu_answer.option
        amount_menu(chat_id)

    # english_main_menu -> amount_menu (english rephrase selected)
    elif menu_answer.option == QuestionType.ENG_REPHRASE:
        user_session.question_type = menu_answer.option
        amount_menu(chat_id)

    # english_voc_menu -> unit_menu
    elif menu_answer.option in (QuestionType.ENG_VOC_HEB,QuestionType.ENG_VOC_ENG,QuestionType.ENG_VOC_MIX):
        user_session.question_type = menu_answer.option
        unit_num_menu(chat_id)

    # math_menu -> amount_menu
    elif menu_answer.menu_type == MenuType.MATH:
        user_session.question_type = menu_answer.option
        amount_menu(chat_id)

    # unit_menu -> amount menu
    elif menu_answer.menu_type == MenuType.UNIT:
        user_session.question_unit = menu_answer.option
        amount_menu(chat_id)

    elif menu_answer.menu_type == MenuType.AMOUNT:
        user_session.question_amount = menu_answer.option
        call_questions(chat_id)

    elif menu_answer.option == QuestionType.REPEAT:
        call_questions(chat_id)

    else:
        user_session.subjet = None
        user_session.question_type = None
        user_session.question_unit = None
        user_session.question_amount = None
        main_menu(chat_id)

# ________calling questions functions_____________
def call_questions(chat_id):
    user_session = users_sessions.get(chat_id)
    if user_session.subject == None or user_session.question_type == None:
        bot.send_message(chat_id, "You didn't select a needed option,"
                                          +" start again and be aware for not skipping any of the menus")

    if user_session.subject == MenuType.ENGLISH:

        if user_session.question_type == QuestionType.ENG_COM:
            eng_built(chat_id, int(user_session.question_amount), "eng_com")

        elif user_session.question_type == QuestionType.ENG_MIX:
            eng_full_mix(chat_id, int(user_session.question_amount))

        elif user_session.question_type == QuestionType.ENG_REPHRASE:
            eng_built(chat_id, int(user_session.question_amount), "eng_rephrase")

        elif user_session.question_type == QuestionType.ENG_VOC_ENG:
            eng_voc(chat_id,
                    int(user_session.question_unit) if user_session.question_unit.isnumeric() else 0,
                    int(user_session.question_amount), 0)

        elif user_session.question_type == QuestionType.ENG_VOC_HEB:
            eng_voc(chat_id,
                    int(user_session.question_unit) if user_session.question_unit.isnumeric() else 0,
                    int(user_session.question_amount), 1)

        elif user_session.question_type == QuestionType.ENG_VOC_MIX:
            mix_voc(chat_id,
                    int(user_session.question_unit) if user_session.question_unit.isnumeric() else 0,
                    int(user_session.question_amount))

    elif user_session.subject == MenuType.MATH:

        if user_session.question_type == QuestionType.MATH_ALGEBRA:
            math_built(chat_id, int(user_session.question_amount), "math_alg")

        elif user_session.question_type == QuestionType.MATH_GEOMETRY:
            math_built(chat_id, int(user_session.question_amount), "math_geo")

        elif user_session.question_type == QuestionType.MATH_PROBLEM:
            math_built(chat_id, int(user_session.question_amount), "math_prob")

    elif user_session.subject == MenuType.COMBINATION:
        all_full_mix(chat_id)

    repeat_menu(chat_id)


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
def receive(message):
    """brings up the main menu if the user sends a text message"""
    main_menu(message.chat.id)



bot.polling()

