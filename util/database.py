import itertools
import logging
import sqlite3
from itertools import chain

from util.filehandler import FileHandler
from util.datehandler import DateHandler as dh


class DatabaseHandler(object):

    def __init__(self, database_path):

        self.database_path = database_path
        self.filehandler = FileHandler(relative_root_path="..")
        logging.info("Databasepath: %s" % (database_path))

        if not self.filehandler.file_exists(self.database_path):
            logging.info("Creating new database")
            sql_command = self.filehandler.load_file("resources/setup.sql")
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            cursor.executescript(sql_command)
            conn.commit()
            conn.close()
            #TODO put somewhere in config
            self.add_url("https://gebrauchte-veranstaltungstechnik.de/rss.php")

    def add_user(self, telegram_id):
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO user (telegram_id) VALUES (%d);" % (telegram_id))
        conn.commit()
        conn.close()
        logging.info("Added user '%d'" % (telegram_id))

    def remove_user(self, telegram_id):
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user WHERE telegram_id = " + str(telegram_id) + ";")
        cursor.execute("DELETE FROM filter WHERE telegram_id = " + str(telegram_id) + ";")
        conn.commit()
        conn.close()
        logging.info("Deleted user %d" % (telegram_id))

    def user_exists(self, telegram_id):
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        sql_command = "SELECT * FROM user WHERE telegram_id=%s" % (telegram_id)

        cursor.execute(sql_command)
        result = cursor.fetchone()

        conn.commit()
        conn.close()
        if result:
            return True
        else:
            return False


    def add_url(self, url):
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        cursor.execute("INSERT OR IGNORE INTO feed (url, last_updated) VALUES (?,?)",
                       (url, dh.get_datetime_now()))

        conn.commit()
        conn.close()

    def get_url(self, url):
        raise NotImplementedError()

    def get_all_urls(self):
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        sql_command = "SELECT * FROM feed;"

        cursor.execute(sql_command)
        result = cursor.fetchall()

        conn.commit()
        conn.close()

        return result

    def get_all_url_names(self):
        '''
        :return: A list of all url names
        '''
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        sql_command = "SELECT url FROM feed;"

        cursor.execute(sql_command)
        result = cursor.fetchall()

        conn.commit()
        conn.close()
        return list(itertools.chain(*result))

    def get_urls_for_user(self, telegram_id):
        raise NotImplementedError()

    def get_users_for_url(self, url):
        raise NotImplementedError()


    def add_filter(self, telegram_id, filter_regex, url):

        #TODO check if url exists
        #TODO maybe do duplicate check

        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO filter (regexp, telegram_id, url) VALUES(?, ?, ?);",
                       (filter_regex, telegram_id, url))
        conn.commit()
        conn.close()
        logging.info("Added Filter '%s' for user '%d'" % (filter_regex, telegram_id))


    def get_filters_for_user(self, telegram_id):
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()

        sql_command = "SELECT filter_id, regexp FROM filter WHERE telegram_id=%d;" % (telegram_id)

        cursor.execute(sql_command)
        result = cursor.fetchall()

        conn.commit()
        conn.close()
        return result

    def filter_exists(self, filter_id):
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT filter_id FROM filter WHERE filter_id = " + str(filter_id))
        result = cursor.fetchone()
        conn.commit()
        conn.close()

        if result:
            return True
        else:
            return False

    def remove_filter(self, filter_id):
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM filter WHERE filter_id = " + str(filter_id))
        conn.commit()
        conn.close()
        logging.info("Removed Filter %d" % (filter_id))


