#add exceptions for no search results
#add exceptions for incorrect ozon code

import numpy as np

import logging, requests
import time
from threading import Thread

from selenium import webdriver
from bs4 import BeautifulSoup
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

#Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


#      CONSTANTS
FIND_CLASS = str()
PARSER = 'lxml'
SLEEP_TIME_FOR_LOAD = 0.5
PAGES_TO_FIND = 10
#######################

# Define a few command handlers. These usually take the two arguments update and
# context.
def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!' + 
        '\nEnter the Command /site, Product code, and the Search query'
        '\nFor example: "/site 123456789 chocolate Ritter Sport"',
        #reply_markup=ForceReply(selective=True),
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

def scan_page(update, driver, page, url, ozon_code):

    ##################INI#######################
    print(f"page #{page} is loading")

    driver.get(url + f'&page={page}')
    time.sleep(SLEEP_TIME_FOR_LOAD)  # wait for html to be fully loaded

    soup = BeautifulSoup(driver.page_source, PARSER)

    print(f"page #{page} search")
    ############################################

    counter = 1
    is_found = 0

    for item in soup.find_all("div", {"class": FIND_CLASS}):
        if item is None:
            update.message.reply_text(f'Товар не найден\nТоваров просмотрено:{36 * (page - 1)} ')
            driver.quit()
            return True

        #print(item.a.get('href'))
        link = item.a.get('href')

        if ozon_code in link:
            is_found = 1
            break
        counter += 1

    if is_found == 1:
        update.message.reply_text(f"Позиция в поиске: {(page-1)*36+counter}\nНомер страницы с товаром: {page}")
        return True
    return False

def site(update: Update, context: CallbackContext) -> None:

    arg_num = len(context.args)
    if arg_num<2:
        update.message.reply_text('Not enough args')
        return


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




    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    start = time.time()
    #!!!input this line to main and quit webdriver with bot only
    driver = webdriver.Chrome(options=options)
    print("1")
    print(time.time() - start)
    start = time.time()









    page = 1


    print(f"page #{page} is loading")
    start = time.time()

    driver.get(url + f'&page={page}')
    print("2")
    print(time.time() - start)
    start = time.time()

    time.sleep(SLEEP_TIME_FOR_LOAD)  # wait for html to be fully loaded
    print("3")
    print(time.time() - start)
    start = time.time()

    soup = BeautifulSoup(driver.page_source, PARSER)
    print("4")
    print(time.time() - start)
    start = time.time()

    print(f"page #{page} search")
    print(time.time() - start)

    #################check the html file##################
    # f = open("ozon html.txt", "w", encoding="utf-8")
    # f.write(soup.prettify())
    # f.close()
    ######################################################

    ###################find class name####################
    class_massive = soup.body.div.div.div.div.next_sibling.next_sibling.next_sibling.div.next_sibling.div.next_sibling.div.next_sibling.div.div.div.div.get('class')
    global FIND_CLASS
    FIND_CLASS = ' '.join(class_massive)
    # print(FIND_CLASS)
    ######################################################

    counter = 1
    is_found = 0

    for item in soup.find_all("div", {"class": FIND_CLASS}):
        if item == None:
            update.message.reply_text(f'По запросу не найдено товаров')
            driver.quit()
            return
        link = item.a.get('href')
        # print(ozon_code)
        # print(link)
        if ozon_code in link:
            is_found = 1
            break
        counter += 1

    if is_found == 1:
        update.message.reply_text(f"Позиция в поиске: {counter}\nНомер страницы с товаром: {page}")

    else:
        threads = []
        for page in range(2, PAGES_TO_FIND+1):
            threads.append(Thread(target = scan_page, args = (update, driver, page, url, ozon_code)))
            threads[-1].start()
        for thread in threads:
            thread.join()


    #update.message.reply_text(f'Товар не найден\nТоваров просмотрено:{36*PAGES_TO_FIND} ')

    driver.quit()



def unknown(update: Update, context: CallbackContext) -> None:
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.

    token_string = str()

    with open('token.txt') as token_file:
        token_string = token_file.read()

    updater = Updater(token = token_string, use_context = True)


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
