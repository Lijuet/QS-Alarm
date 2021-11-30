import requests
from datetime import date, timedelta
import re
import time
from bs4 import BeautifulSoup as bs
import telegram

import secrets


key = secrets.key
bot = telegram.Bot(token=key)

target = {
    'cpu':{
        'name':'5600x',
        'maximum_cost': 290000,
    },
    'gpu':{
        'name':'3060 ti',
        'maximum_cost': 7000000,
    },
}

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
        release_date = date(2020, month, day)
    else:
        release_date = date(2021, month, day)

    return release_date
        
    

def search_target(type):
    formatted_target = target[type]['name'].replace(" ", "+")
    target_maximum_cost = target[type]['maximum_cost']
    search_url = "https://quasarzone.com/bbs/qb_saleinfo?_method=post&type=&page=1&_token=Q7kaCjkdlWWa9Q6lPxPZopa4URVoxDkq4VKwgCFM&category=&popularity=&kind=subject&keyword="+formatted_target+"&sort=num%2C+reply&direction=DESC"
    headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
                'referer': 'referer: https://quasarzone.com/bbs/qb_saleinfo?_method=post&type=&page=1&_token=Q7kaCjkdlWWa9Q6lPxPZopa4URVoxDkq4VKwgCFM&category=&popularity=&kind=subject&keyword=3060+ti&sort=num%2C+reply&direction=DESC'}

    items_info = []
    try:
        page = requests.get(search_url, headers=headers)
        html = bs(page.text, "html.parser")
        items = html.select('div.market-info-list-cont')
        
        for item in items:
            name = item.select_one('span.ellipsis-with-reply-cnt').text
            status = item.select_one('p.tit > span').text
            link = item.select_one('p.tit > a')['href']
            release_date = reformat_date(item)
            cost = int(''.join(filter(str.isdigit, item.select_one('span.text-orange').text)))

            if status != '종료' \
                and '품절' not in name \
                and release_date > date.today() - timedelta(days=7) \
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
        print("Error : ", e)

    return items_info


def repeat_searching():
    repeat = True
    while repeat:
        time.sleep(1)
        print("We will search {}".format(list(target.keys())))
        for type in target.keys():
            print("Search [{}] {}".format(type, target[type]['name']), end=" ")
            result = search_target(type)
            if result: 
                try:
                    send_message(result)
                except Exception as e:
                    print("Error : ", e)
                finally:
                    repeat = False

            else:
                print("FAIL....")


def send_message(result):
    id = bot.getUpdates()[0].message.chat.id
    for item in result:
        bot.sendMessage(id, f"{item['name']}\t:\t{item['cost']} 원 \n\t-> {item['link']}")


# ===================================== run ===================================== #
if __name__ == '__main__':
    print("Program Start")
    repeat_searching()