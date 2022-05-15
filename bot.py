#add exceptions for no search results
#add exceptions for incorrect ozon code

import numpy as np

import logging, requests
import time

from selenium import webdriver
from bs4 import BeautifulSoup
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext


PARSER = 'lxml'
SLEEP_TIME_FOR_LOAD = 0.5
PAGES_TO_FIND = 10
FIND_CLASS = None


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
        fr'Добрый день {user.mention_markdown_v2()}\!' + 
        '\nДля получения позиции товара'
        '\nВведите команду /site, код продукта и поисковый запрос'
        '\nНапример: "/site 123456789 шоколад Ritter Sport"'
    )


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('\nДля получения позиции товара'
                              '\nВведите команду /site, код продукта и поисковый запрос'
                              '\nНапример: "/site 123456789 шоколад Ritter Sport"')


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


    global PARSER
    global SLEEP_TIME_FOR_LOAD
    global PAGES_TO_FIND
    global FIND_CLASS


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

    #start = time.time()
    #!!!input this line to main and quit webdriver with bot only
    driver = webdriver.Chrome(options=options)
    print("\nStarting")
    print(FIND_CLASS)
    #print(time.time() - start)
    start = time.time()

    f = open("Items.txt", "w")

    for page in range(1,PAGES_TO_FIND+1):

        print(f"page #{page} is loading")

        
        driver.get(url + f'&page={page}')

        time.sleep(SLEEP_TIME_FOR_LOAD) # wait for html to be fully loaded

        soup = BeautifulSoup(driver.page_source, PARSER)

        print(f"page #{page} search")

        pageItems = soup.find_all("div", {"class": FIND_CLASS})
        itemsNum = len(pageItems)
        if(itemsNum == 0):
            update.message.reply_text(f'Товар не найден\nТоваров просмотрено:{36*(PAGES_TO_FIND-1-page)} ')
            print("\nFinishing")
            print("Time in process: " + '{:07.3f}'.format(time.time() - start))
            driver.quit()
            return

        elif itemsNum<36:
            print("<36 !!!")
        #print("Items on Page: " + str(itemsNum))



        for item in pageItems:
            if item == None:
                if page == 1:
                    update.message.reply_text(f'По запросу не найдено товаров')
                    driver.quit()
                    return
                else: 
                    update.message.reply_text(f'Товар не найден\nТоваров просмотрено:{36*(PAGES_TO_FIND-1)} ')
                    driver.quit()
                    return
            link = item.a.get('href')
            #print(ozon_code)
            f.write(link.split('/')[2] + '\n')
            #print(link)

            if ozon_code in link:
                is_found = 1
                break
            counter += 1

        if is_found == 1:
            update.message.reply_text(f"Позиция в поиске: {counter}\nНомер страницы с товаром: {page}")
            break

    if is_found != 1:
        update.message.reply_text(f'Товар не найден\nТоваров просмотрено:{36*PAGES_TO_FIND} ')

    print("\nFinishing")
    print("Time in process: " + '{:07.3f}'.format(time.time() - start))

    driver.quit()


def search_ini():

    global SLEEP_TIME_FOR_LOAD
    global PARSER
    global FIND_CLASS

    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    driver = webdriver.Chrome(options=options)

    driver.get("https://www.ozon.ru/search/?text=%D1%88%D0%BA%D0%BE%D0%BB%D0%B0&from_global=true")
    time.sleep(SLEEP_TIME_FOR_LOAD)
    soup = BeautifulSoup(driver.page_source, PARSER)

    class_massive = soup.body.div.div.div.div.next_sibling.next_sibling.next_sibling.div.next_sibling.div.next_sibling.div.next_sibling.div.div.div.div.get('class')
    FIND_CLASS = ' '.join(class_massive)
    print(FIND_CLASS)
    driver.quit()



def unknown(update: Update, context: CallbackContext) -> None:
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.

    with open('token.txt') as token_file:
        token = token_file.read()

    updater = Updater(token=token, use_context = True)


    search_ini()


    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    # new commands

    dispatcher.add_handler(CommandHandler('site', site))

    dispatcher.add_handler(MessageHandler(Filters.command, unknown))

    # start the Bot
    updater.start_polling()

    # run the bot until you press Ctrl-C
    updater.idle()


if __name__ == '__main__':
    main()
