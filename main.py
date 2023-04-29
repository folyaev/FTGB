import logging
from telegram.ext import Updater
from config import config
from message_handlers import setup_dispatcher

def main() -> None:
    logging.basicConfig(level=logging.INFO)
    updater = Updater(config["bot_token"])
    bot_user_id = updater.bot.get_me().id
    dispatcher = updater.dispatcher
    setup_dispatcher(dispatcher, bot_user_id)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()