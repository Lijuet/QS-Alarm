import requests
from datetime import date, timedelta
import re
import time
from bs4 import BeautifulSoup as bs

import telegram
from telegram.ext import Updater
from telegram.ext import CommandHandler

import secrets

target = {
    'gpu':{
        'name':'3060ti',
        'maximum_cost': 840000,
    },
    'gpu2':{
        'name':'3060 ti',
        'maximum_cost': 840000,
    },
    'ram':{
        'name':'ddr4 16',
        'maximum_cost': 180000,
    },
    'ram2':{
        'name':'ddr4 32',
        'maximum_cost': 180000,
    },
    'paladin':{
        'name':'paladin',
        'maximum_cost': 30000,
    },
    'rc410':{
        'name':'rc410',
        'maximum_cost': 34000,
    },
    'rc400':{
        'name':'rc400',
        'maximum_cost': 30000,
    },
}

repeat = True
send_cash = {}

def reformat_date(item):
    release_date = item.select_one('span.date').text
    release_date = re.search('\d\d-\d\d', release_date)
    
    if release_date is None:
        month = int(date.today().month)
        day = int(date.today().day)
    else:    
        release_date = release_date.group().split('-')
        month = int(release_date[0])
        day = int(release_date[1])

    if(month > date.today().month):
        release_date = date(2021, month, day)
    else:
        release_date = date(2022, month, day)

    return release_date
        
    

def search_target(type):
    formatted_target = target[type]['name'].replace(" ", "+")
    target_maximum_cost = target[type]['maximum_cost']
    search_saleinfo = "https://quasarzone.com/bbs/qb_saleinfo?_method=post&type=&page=1&_token=Q7kaCjkdlWWa9Q6lPxPZopa4URVoxDkq4VKwgCFM&category=&popularity=&kind=subject&keyword="+formatted_target+"&sort=num%2C+reply&direction=DESC"
    serach_qb_tsy = "https://quasarzone.com/bbs/qb_tsy?_method=post&type=&page=1&_token=WY2ufemJWAx3zqmjJfzJZwiNAUrTwgm4Ab50Fdva&popularity=&kind=subject%7C%7Ccontent&keyword="+formatted_target+"&sort=num%2C+reply&direction=DESC"
    if 'gpu' in type: serach_urls = [search_saleinfo, serach_qb_tsy]
    else: serach_urls = [search_saleinfo]
    
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
                'referer': 'referer: https://quasarzone.com/bbs/qb_saleinfo?_method=post&type=&page=1&_token=Q7kaCjkdlWWa9Q6lPxPZopa4URVoxDkq4VKwgCFM&category=&popularity=&kind=subject&keyword=3060+ti&sort=num%2C+reply&direction=DESC'}

    items_info = []
    try:
        for url in serach_urls:
            page = requests.get(url, headers=headers)
            html = bs(page.text, "html.parser")
            items = html.select('div.market-info-list-cont')
            
            for item in items:
                name = item.select_one('span.ellipsis-with-reply-cnt').text
                status = item.select_one('p.tit > span').text
                link = item.select_one('p.tit > a')['href']
                release_date = reformat_date(item)
                _cost = list(filter(str.isdigit, item.select_one('span.text-orange').text))

                if not _cost: _cost = ['0']
                cost = int(''.join(_cost))

                if status != '종료' \
                    and '품절' not in name \
                    and release_date > (date.today() - timedelta(days=1)) \
                    and cost < target_maximum_cost:

                    item_info = {
                            'date':release_date,
                            'name':name,
                            'status':status,
                            'cost':cost,
                            'link':"https://quasarzone.com"+link,
                        }
                    items_info.append(item_info)

    except Exception as e:
        print("Error while searching : ", e)

    return items_info


def repeat_searching(update, context):
    try:
        send_message("Program Start")
        while repeat:
            time.sleep(1)
            print("We will search {}".format(list(target.keys())))
            for type in target.keys():
                print("Search [{}] {}".format(type, target[type]['name']), end=" ")
                result = search_target(type)
                if result: send_result(result)
    except Exception as e:
        send_message("Error while sending : "+str(e))


def telegram_init():
    def add_handler(cmd, func):
        updater.dispatcher.add_handler(CommandHandler(cmd, func))

    token = secrets.token
    id = secrets.id

    bot = telegram.Bot(token=token)
    updater = Updater(token = token)

    add_handler('search', repeat_searching)
    return bot, updater, id

def send_result(result):    
    for item in result:
        if item['name'] not in send_cash: 
            bot.sendMessage(id, f"{item['date']}\n{item['name']}\t:\t{item['cost']} 원 \n\t-> {item['link']}")
            send_cash[item['name']] = item

def send_message(msg):
    bot.sendMessage(id, msg)




# ===================================== run ===================================== #
if __name__ == '__main__':
    bot, updater, id = telegram_init()
    updater.start_polling()
    updater.idle()