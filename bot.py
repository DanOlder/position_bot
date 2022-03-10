#add exceptions for no search results
#add exceptions for incorrect ozon code

#token = "1655217772:AAEEg8VIjNrU_t2678URbPODYzA132YTEI4"

import numpy as np

import logging, requests
import time

from selenium import webdriver
from bs4 import BeautifulSoup
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

#Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context.
def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!',
        reply_markup=ForceReply(selective=True),
    )


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def echo(update: Update, context: CallbackContext) -> None:
    """Echo the user message."""
    update.message.reply_text(update.message.text)


#for scraping ozon (otherwise Incapsule lock)
def get_random_ua():
    random_ua = ''
    ua_file = 'ua_file.txt'
    try:
        with open(ua_file) as f:
            lines = f.readlines()
        if len(lines) > 0:
            prng = np.random.RandomState()
            index = prng.permutation(len(lines) - 1)
            idx = np.asarray(index, dtype=np.integer)[0]
            random_proxy = lines[int(idx)]
    except Exception as ex:
        print('Exception in random_ua')
        print(str(ex))
    finally:
        return random_ua    

def site(update: Update, context: CallbackContext) -> None:

    arg_num = len(context.args)
    if arg_num<2:
        update.message.reply_text('Not enough args')
        return



    FIND_CLASS = 'hy5 y5h'
    # parser lutshe pomenyat' !!!
    PARSER = 'lxml'
    SLEEP_TIME_FOR_LOAD = 0.5
    PAGES_TO_FIND = 10



    # make with requests for changing pages
    url = 'https://www.ozon.ru/search/?text='

    for i in range(1, arg_num):
        url += context.args[i] + ' '


    # user simulation
    user_agent = get_random_ua()
    headers = {
            'user-agent': user_agent,
        }


    ozon_code = context.args[0]
    counter = 1
    is_found = 0



    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    for page in range(1,PAGES_TO_FIND+1):
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        time.sleep(SLEEP_TIME_FOR_LOAD) # wait for html to be fully loaded
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()


        for item in soup.find_all("div", {"class": FIND_CLASS}):
            link = item.a.get('href')
            if ozon_code in link:
                is_found = 1
                break
            counter += 1

        if is_found:
            update.message.reply_text(f"Позиция в поиске: {counter}\n Номер страницы с товаром: {page}")
            break



    





'''
    print("###############################################################")
    #иногда классы меняются к хуям(не надежный способ поиска адреса)
    item = soup.find("div", {"class": FIND_CLASS})
    link = item.a.get('href')
    print(link)
    print("###############################################################")
'''
'''

    ozon_code = context.args[0]
    global_counter = 1
    on_page_counter = 1
    pageNum = 1


    while  global_counter != 10001:

        if ozon_code in link:
            break

        if on_page_counter == 36:
            print("###############################################################")
            print('check page counter')
            pageNum += 1
            newPageUrl = ulr + f"&from_global=true&page={pageNum}"


            r = requests.get(newPageUrl, headers=headers)
            soup = BeautifulSoup(r.text, PARSER)


            item = soup.findNext("div", {"class": FIND_CLASS})
            link = item.a.get('href')
            print(link)
            print("###############################################################")
            on_page_counter = 1
        else:
            print("###############################################################")
            print('check regular counter')
            item = item.findNext("div", {"class": FIND_CLASS})
            link = item.a.get('href')
            print(link)
            print("###############################################################")
            on_page_counter += 1

        global_counter += 1


    if global_counter == 10001:
        update.message.reply_text('Not in fisrt 10000')
    else:
        update.message.reply_text(f"Позиция в поиске: {global_counter}")
'''
'''
    while (ozon_code not in link) and (global_counter != 37):


        print("###############################################################")
        item = item.findNext("div", {"class": FIND_CLASS})
        link = item.a.get('href')
        print(link)
        print("###############################################################")


        global_counter += 1
        continue




    if global_counter == 37:
        update.message.reply_text('Not in fisrt 36')
    else:
        update.message.reply_text(f"Позиция в поиске: {global_counter}")
 '''





def unknown(update: Update, context: CallbackContext) -> None:
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(token='1655217772:AAEEg8VIjNrU_t2678URbPODYzA132YTEI4', use_context = True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - echo the message on Telegram
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # new commands

    dispatcher.add_handler(CommandHandler('site', site))




    dispatcher.add_handler(MessageHandler(Filters.command, unknown))

    # start the Bot
    updater.start_polling()

    # run the bot until you press Ctrl-C
    updater.idle()


if __name__ == '__main__':
    main()