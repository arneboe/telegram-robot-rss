# /bin/bash/python
# encoding: utf-8
from telegram.error import Unauthorized, TelegramError
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode
from util.filehandler import FileHandler
from util.database import DatabaseHandler
from util.processing import BatchProcess
from util.feedhandler import FeedHandler
import logging


class RobotRss(object):

    def __init__(self, telegram_token, update_interval):

        # Initialize bot internals
        self.db = DatabaseHandler("resources/db.db")
        self.fh = FileHandler("..")

        # Register webhook to telegram bot
        self.updater = Updater(telegram_token)
        self.dispatcher = self.updater.dispatcher

        # Add Commands to bot
        self._addCommand(CommandHandler("start", self.start))
        self._addCommand(CommandHandler("stop", self.stop))
        self._addCommand(CommandHandler("help", self.help))
        self._addCommand(CommandHandler("list", self.list))
        self._addCommand(CommandHandler("add", self.add, pass_args=True))
        self._addCommand(CommandHandler("remove", self.remove, pass_args=True))

        # Start the Bot
        self.processing = BatchProcess(
            database=self.db, update_interval=update_interval, bot=self.dispatcher.bot)

        self.processing.start()
        self.updater.start_polling()
        self.updater.idle()

    def _addCommand(self, command):
        """
        Registers a new command to the bot
        """

        self.updater.dispatcher.add_handler(command)

    def start(self, bot, update):
        """
        Send a message when the command /start is issued.
        """
        telegram_user = update.message.from_user

        if telegram_user.is_bot:
            message = "Sorry, I don't talk to bots!"
            update.message.reply_text(message)
            return

        # Add new User if not exists
        if not self.db.user_exists(telegram_id=telegram_user.id):
            self.db.add_user(telegram_id=telegram_user.id)
            message = "Hi %s! I am the Conartism GVT Bot" % (telegram_user.first_name)
            update.message.reply_text(message)

        self.help(bot, update)

    def remove(self, bot, update, args):

        if len(args) != 1:
            message = "/remove <filter id>.\n You can find the filter id using /list"
            update.message.reply_text(message)
            return

        telegram_id = update.message.from_user.id
        filter_id = args[0]

        if not str.isdigit(filter_id):
            update.message.reply_text("Illegal filter id '%s'" % (filter_id))
            return


        if(self.db.filter_exists(filter_id)):
            self.db.remove_filter(filter_id)
            update.message.reply_text("Filter '%s' removed" % (filter_id))
        else:
            update.message.reply_text("Unknown filter id '%s'" % (filter_id))


    def list(self, bot, update):
        telegram_id = update.message.from_user.id

        filters = self.db.get_filters_for_user(telegram_id)

        message = "Active filters:\n"
        for filter in filters:
            message += "%d: %s\n" % (filter[0], filter[1])
        update.message.reply_text(message)



    def help(self, bot, update):
        message = ("Commands:\n\n"
                   "/start\nsubscribe to the bot\n\n"
                   "/stop\nunsubscribe from the bot\n\n"
                   "/add <search term>\n Add a new search term\n\n"
                   "/remove <id>\n Remove search term. Use /list to get the id \n\n"
                   "/list\nShow current search terms")

        update.message.reply_text(message)

    def stop(self, bot, update):
        """
        Stops the bot from working
        """
        self.db.remove_user(update.message.from_user.id)
        message = "Bye!"
        update.message.reply_text(message)

    def add(self, bot, update, args):
        '''
        add a filter to all urls for a given user
        '''

        telegram_user = update.message.from_user

        if len(args) < 1:
            message = "/add <search term>."
            update.message.reply_text(message)
            return

        filter_regexp = args[0]
        # check if the regexp is multi-word
        if len(args) > 1:
            for i in range(1, len(args)):
                filter_regexp = filter_regexp + " " + args[i]

        #add filter to all urls
        urls = self.db.get_all_url_names()
        for url in urls:
            self.db.add_filter(telegram_user.id, filter_regexp, url)

        update.message.reply_text("Added Filter '%s'" % (filter_regexp))

if __name__ == '__main__':
    logging.basicConfig(filename='log.log', level=logging.INFO)
    logging.info("Starting RobotRss")
    # Load Credentials
    fh = FileHandler("..")
    credentials = fh.load_json("resources/credentials.json")

    # Pass Credentials to bot
    token = credentials["telegram_token"]
    update = credentials["update_interval"]
    RobotRss(telegram_token=token, update_interval=update)
