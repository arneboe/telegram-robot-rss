# /bin/bash/python/
import logging
import re

from telegram.error import (TelegramError, Unauthorized)
from telegram import ParseMode
from multiprocessing.dummy import Pool as ThreadPool
from threading import Thread as RunningThread
from util.datehandler import DateHandler
from util.feedhandler import FeedHandler
import datetime
import threading
import traceback
from time import sleep


class BatchProcess(threading.Thread):

    def __init__(self, database, update_interval, bot):
        RunningThread.__init__(self)
        self.db = database
        self.update_interval = float(update_interval)
        self.bot = bot
        self.running = True

    def run(self):
        """
        Starts the BatchThreadPool
        """

        while self.running:
            # Init workload queue, add queue to ThreadPool
            url_queue = self.db.get_all_urls()
            self.parse_parallel(queue=url_queue, threads=4)

            # Sleep for interval
            sleep(self.update_interval)

    def parse_parallel(self, queue, threads):
        time_started = datetime.datetime.now()

        pool = ThreadPool(threads)
        pool.map(self.update_feed, queue)
        pool.close()
        pool.join()

        time_ended = datetime.datetime.now()
        duration = time_ended - time_started
        logging.info("Finished updating! Parsed " + str(len(queue)) +
              " rss feeds in " + str(duration) + " !")

    def update_feed(self, url):
        telegram_users = self.db.get_users()
        posts = FeedHandler.parse_feed(url[0])

        for user in telegram_users:
            filters = self.db.get_filters_for_user_and_url(user, url[0])

            for post in posts:
                if self.match_filters(post, filters):
                    try:
                        self.send_newest_messages(url=url, post=post, user=user)
                    except Exception as e:
                        logging.exception("Error in update feed",exec_info=e)
                        message = "Something went wrong when I tried to parse the URL: \n\n " + \
                         url[0] + "\n\nCould you please check that for me? Remove the url from your subscriptions using the /remove command, it seems like it does not work anymore!"

        self.db.update_feed_date(url=url[0], new_date=str(DateHandler.get_datetime_now()))

    def send_newest_messages(self, url, post, user):
        post_update_date = DateHandler.parse_datetime(datetime=post.updated)
        url_update_date = DateHandler.parse_datetime(datetime=url[1])
        if post_update_date > url_update_date:
            logging.info("New data in %s for user %d" % (url[0], user))
            message = "<a href='" + post.link + "'>" + post.title + "</a>"
            try:
                self.bot.send_message(
                    chat_id=user, text=message, parse_mode=ParseMode.HTML)
            except Unauthorized as e:
                logging.exception("unathorized", exec_info=e)
            except TelegramError as e:
                logging.exception("Telegram error", exec_info=e)

    def set_running(self, running):
        self.running = running

    def match_filters(self, post, filters):
        for filter in filters:
            result = self.match_filter(post, filter)
            if result:
                return True
        return False

    def match_filter(self, post, filter_text):
        '''
        :return: True if filter matches, False otherwise
        '''
        if re.search(filter_text, post.title, re.IGNORECASE) or re.search(filter_text, post.summary, re.IGNORECASE):
            return True
        else:
            return False
