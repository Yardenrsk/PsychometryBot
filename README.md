
# PsychometryBot

A TelegramBot made in order to help people train to their psychometric
examination free of charge.

With the bot, one can practice different type of subject (English, math and Hebrew)
and different types of questions, such as translating words or even 
rephrasing English sentences. You can also control the amount of questions to get, or
 choose to practice specific study units that you
 hard and want to practice more.









## How Does It Work?
Connected to TelegramApi using [TeleBot](https://pypi.org/project/pyTelegramBotAPI/) 
and reading questions MS Excel DB using Pandas.

We created a session class so that each user's current state in the menu is saved.
The navigation through the menus is done by inline buttons and JSON callbacks sent
to a callback handler and there calling actions by the user's current state.



## Use It By Yourself

Download [the Telegram app](https://telegram.org/) to your machine and use 
 [t.me/ThePsychometryBot](https://t.me/ThePsychometryBot) for a quick start!


## Screenshots
![alt-text-1](https://github.com/Yardenrsk/PsychometryBot/blob/main/DATA/example0.png?raw=true) ![alt-text-2](https://github.com/Yardenrsk/PsychometryBot/blob/main/DATA/example1.png?raw=true)
## Acknowledgements
The questions were taken from the sites:
 - [HighQ](https://www.high-q.co.il/)
 - [CampusIL](https://campus.gov.il/)
 - [unseenimi](https://unseenimi.co.il)

All credit saved them.
If one of the websites above is yours and you want us to delete the data, tell us.