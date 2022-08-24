class Session:
    '''
    A unique data structure for each user in order to keep their state in the menu
    '''
    def __init__(self):
        self.subject = None
        self.question_amount = None
        self.question_unit = None
        self.question_type = None


