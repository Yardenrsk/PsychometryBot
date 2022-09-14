import enum
from json import JSONEncoder

class MenuType(str, enum.Enum):
    """
    All possible different menus
    """
    ENGLISH = "ENGLISH_MENU"
    MATH = "MATH_MENU"
    HEBREW = "HEBREW_MENU"
    COMBINATION = "COMBINATION_MENU"
    ENG_VOC = "ENG_VOC_MENU"
    AMOUNT = "AMOUNT_MENU"
    MAIN = "MAIN_MENU"
    UNIT = "UNIT_MENU"
    REPEAT = "REPEAT_MENU"


class QuestionType(str, enum.Enum):
    """
    All possible question types on menus
    """
    ENG_COM = "ENG_COM"
    ENG_REPHRASE = "ENG_REPHRASE"
    ENG_VOC_HEB = "ENG_VOC_HEB"
    ENG_VOC_ENG = "ENG_VOC_ENG"
    ENG_VOC_MIX = "ENG_VOC_MIX"
    ENG_MIX = "ENG_MIX"
    MATH_ALGEBRA = "MATH_ALGEBRA"
    MATH_GEOMETRY = "MATH_GEOMETRY"
    MATH_PROBLEM = "MATH_PROBLEM"
    MATH_MIX = "MATH_MIX"
    FULL_MIX = "FULL_MIX"
    REPEAT = "REPEAT"


class AmountQuestion(str, enum.Enum):
    """
    All options for amount menu
    """
    ONE = "1"
    FIVE = "5"
    TEN = "10"


class Unit(str, enum.Enum):
    """
    All options for unit menu
    """
    (ONE,
     TWO,
     THREE,
     FOUR,
     FIVE,
     SIX,
     SEVEN,
     EIGHT,
     NINE,
     TEN) = [str(i) for i in range(1, 11)]
    COMBINATION = "COMBINATION"


class MenuAnswer:
    """
    Each call back is represented by MenuAnswer
    :var menu_type: The menu where the answer was made
    :var option:  The answer on this specific menu. option type in [MenuType, QuestionType, AmountQuestion, Unit]
    """

    def __init__(self, menu_type: MenuType, option):
        self.menu_type = menu_type  # MenuType
        self.option = option  # EveryPossibleChoice

    @staticmethod
    def create_from_call_back(callback):
        """
        Create instance of MenuAnswer from callback
        :param callback: call back returned after choosing of user in format {"menu_type":****, "option":****}
        :return new MenuAnswer which is represented by the callback
        """
        if callback['option'] in [e.value for e in MenuType]:
            option = MenuType(callback['option'])

        elif callback['option'] in [e.value for e in QuestionType]:
            option = QuestionType(callback['option'])

        elif callback['menu_type'] == MenuType.AMOUNT:
            option = AmountQuestion(callback['option'])

        else:
            option = Unit(callback['option'])
        menu_type = MenuType(callback['menu_type'])
        return MenuAnswer(menu_type, option)


class MenuAnswerEncoder(JSONEncoder):
    """
    Class for making MenuAnswer JSON Serializable
    """
    def default(self, o):
        return o.__dict__
