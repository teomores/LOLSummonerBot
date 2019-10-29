import telegram
from telegram.ext import Updater
import logging
from telegram.ext import CommandHandler
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import requests
import json

# import multiprocessing for parallel scraping
import multiprocessing as mp

# neo4j
from neo4j import GraphDatabase

# utils functions
from utils import *

# riotwatcher
import riotwatcher as rw

POLL_SECONDS = 60

class LOLSummonerBot:
    def __init__(self):
        # read info.txt file
        info = {}
        with open("info.txt", "r") as f:
            for line in f:
                (key,value) = line.split()
                info[key] = value
        # setup bot
        updater = Updater(token=info['token'], use_context=True)
        self.dispatcher = updater.dispatcher
        updater.start_polling()
        # setup Neo4j driver
        self.neo4j_uri = "bolt://localhost:7687"
        self.neo4j_driver = GraphDatabase.driver(self.neo4j_uri, auth=("neo4j", "password"))
        # setup logging
        logging.basicConfig(format='%(asctime)s - %(message)s',
                             level=logging.INFO)
        self.logger = logging.getLogger()

        # create handlers
        help_handler = CommandHandler('help', self.help)
        subscribe_to_summoner_handler = CommandHandler('subscribe_to', self.subscribe_to_summoner)
        list_subscriptions_handler = CommandHandler('subscriptions', self.list_subscriptions)
        unsubscribe_from_handler = CommandHandler('unsubscribe_from', self.unsubscribe_from_summoner)
        clear_subs_handler = CommandHandler('clear_subs', self.clear_subs)

        # add handlers to dispatcher
        self.dispatcher.add_handler(subscribe_to_summoner_handler)
        self.dispatcher.add_handler(list_subscriptions_handler)
        self.dispatcher.add_handler(unsubscribe_from_handler)
        self.dispatcher.add_handler(clear_subs_handler)
        self.dispatcher.add_handler(help_handler)

        #setup all we need in order to scrape
        self.summoner_list = []
        self.dict_summ_last_status = {}
        # riotwatcher
        self.region = 'euw1'
        self.watcher = rw.RiotWatcher(info['riot_developer_key'])
        while True:
            with self.neo4j_driver.session() as sess:
                l  = sess.read_transaction(get_all_summoners)
                self.logger.info(f"Summoners: {l}")
            for s in l:
                self.check_summoner_activity(s)
            time.sleep(POLL_SECONDS)

    def check_summoner_activity(self, s):
        try:
            summoner = self.watcher.summoner.by_name(self.region, s)
        except rw.ApiError:
            self.logger.info(f'Invalid username {s}...')
        if 'summoner' in locals():
            try:
                l = self.watcher.spectator.by_summoner(self.region, summoner['id'])
                if s in self.dict_summ_last_status:
                    if self.dict_summ_last_status[s] == 'inactive': # <--- triggering case: previously inactive, now active = started playing
                        msg = f'{s.upper()} IS IN GAME!'
                        self.logger.info(msg)
                        with self.neo4j_driver.session() as sess:
                            subscribers = sess.read_transaction(get_subscribers, s.lower())
                            for subs in subscribers:
                                self.dispatcher.bot.send_message(chat_id=subs, text=msg)
                    elif self.dict_summ_last_status[s] == 'active':
                        self.logger.info(f"{s.upper()} is still in game.")
                    else:
                        self.logger.info(f"{s.upper()} ERROR WHILE PLAYING")
                else:
                    msg = f'{s.upper()} IS IN GAME!'
                    self.logger.info(msg)
                    with self.neo4j_driver.session() as sess:
                        subscribers = sess.read_transaction(get_subscribers, s.lower())
                        for subs in subscribers:
                            self.dispatcher.bot.send_message(chat_id=subs, text=msg)
                self.dict_summ_last_status[s] = 'active'
            except rw.ApiError:
                if s in self.dict_summ_last_status:
                    if self.dict_summ_last_status[s] == 'active': # <--- triggering case: previously active, now inactive = finished the game
                        msg = f"{s.upper()} just finished a game. Wanna join?"
                        self.logger.info(msg)
                        with self.neo4j_driver.session() as sess:
                            subscribers = sess.read_transaction(get_subscribers, s.lower())
                            for subs in subscribers:
                                self.dispatcher.bot.send_message(chat_id=subs, text=msg)
                    elif self.dict_summ_last_status[s] == 'inactive':
                        self.logger.info(f"{s.upper()} is not playing right now...")
                    else:
                        self.logger.info(f"{s.upper()} ERROR WHILE NOT PLAYING")
                else:
                    self.logger.info(f"{s.upper()} is not playing right now...")
                self.dict_summ_last_status[s] = 'inactive'


    def help(self, update, context):
        final_msg = """If you want more information, you'd like to report some bug or you just have a nice idea to improve the bot, please go [here](https://github.com/teomores)"""
        help_msg = " What you can do: \n"+"/help, but you already know what this command does :) \n"+"/subscribe_to <summoner_username> : start following the activity of a specific summoner \n"+"/unsubscribe_from <summoner_username> : stop following a specific summoner \n"+"/subscriptions : display all subscriptions \n"+"/clear_subs : remove all subscriptions"
        context.bot.send_chat_action(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
        time.sleep(0.5)
        context.bot.send_message(chat_id=update.message.chat_id,
            text= help_msg,
            #parse_mode=telegram.ParseMode.MARKDOWN
        )
        context.bot.send_message(chat_id=update.message.chat_id,
            text= final_msg,
            parse_mode=telegram.ParseMode.MARKDOWN
        )

    def subscribe_to_summoner(self, update, context):
        summoner_id = self.clean_summoner(" ".join(context.args))
        chat_id = update.message.chat_id
        if summoner_id not in self.summoner_list:
            try:
                summoner = self.watcher.summoner.by_name(self.region, summoner_id)
                self.summoner_list.append(summoner_id)
            except:
                self.logger.info(f"{summoner_id} is not valid username...")
                context.bot.send_message(chat_id=chat_id, text=f"{summoner_id} is not valid username...")
                return
        with self.neo4j_driver.session() as s:
            # 1) create user instance if it does not exist
            s.write_transaction(create_user_instance, chat_id)
            # 2) create summoner instance if it does not exist
            s.write_transaction(create_summoner_instance, summoner_id) # TODO: check existence of username
            # 3) subscribe user to summoner if not already subscribed
            s.write_transaction(connect_user_summoner, chat_id, summoner_id)
        context.bot.send_message(chat_id=chat_id, text=f"You are subscribed to {summoner_id}!")

    def list_subscriptions(self, update, context):
        chat_id = update.message.chat_id
        with self.neo4j_driver.session() as s:
            subs = s.read_transaction(get_subscriptions, chat_id)
        context.bot.send_message(chat_id=chat_id, text=f"Here are your subs: (total: {len(subs)})")
        for s in subs:
            context.bot.send_message(chat_id=chat_id, text=f"- {s}")

    def unsubscribe_from_summoner(self, update,context):
        summoner_id = self.clean_summoner(" ".join(context.args))
        chat_id = update.message.chat_id
        with self.neo4j_driver.session() as s:
            s.write_transaction(delete_sub_user_summoner, chat_id, summoner_id)
        context.bot.send_message(chat_id=chat_id, text=f"You are now unsubscribed from {summoner_id}.")
        # TODO:
        # after unsub check if the summoner has any followers, if no followers delete

    def clear_subs(self, update, context):
        chat_id = update.message.chat_id
        with self.neo4j_driver.session() as s:
            s.write_transaction(delete_all_subs, chat_id)
        context.bot.send_message(chat_id=chat_id, text="All your subs are now deleted.")

    def clean_summoner(self, s):
        return s.replace(" ","").lower()

if __name__ == '__main__':
    lsm = LOLSummonerBot()
