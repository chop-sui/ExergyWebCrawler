import json
from pprint import pprint

import requests
from bs4 import BeautifulSoup as bs
from jsbn import RSAKey

header = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,es;q=0.6',
    'Content-Length': '1230',
    'Host': 'pp.kepco.co.kr',
    'Origin': 'https://pp.kepco.co.kr',
    'Referer': 'https://pp.kepco.co.kr/intro.do',
    'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
    'sec-ch-ua-mobile': '?0',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded'
}

def scraping():
    with requests.Session() as s:
        base_url = 'https://pp.kepco.co.kr/'
        login_url = 'https://pp.kepco.co.kr/login'

        LOGIN_INFO = {'USER_ID': "0236915825", 'USER_PWD': "humphreys1!"}
        first_page = s.get(base_url)
        cookie_jar = s.cookies
        cookie_rsa = cookie_jar.values()[1]
        cookie_ssid = cookie_jar.values()[2]
        jsession_id = cookie_jar.values()[0]
        header['Cookie'] = 'cookieSsId=' + cookie_ssid + '; ' + 'cookieRsa=' + cookie_rsa + '; ' + 'JSESSIONID=' + jsession_id

        html = first_page.text
        soup = bs(html, 'html.parser')
        rsa_exponent = soup.find('input', {'id': 'RSAExponent'})['value'] # == 10001
        rsa = RSAKey()
        rsa.setPublic(cookie_rsa, rsa_exponent)

        id = jsession_id + '_' + rsa.encrypt(LOGIN_INFO['USER_ID'])
        pw = jsession_id + '_' + rsa.encrypt(LOGIN_INFO['USER_PWD'])

        LOGIN_INFO = {'USER_ID': id, 'USER_PW': pw}
        print(cookie_ssid)
        print(cookie_rsa)
        print(jsession_id)
        pprint(header)

        res_login = s.post(login_url, headers=header, data=LOGIN_INFO)
        print(res_login.status_code)
        print(res_login.text)

        data_15 = {
            'SELECT_ID': "20210601",
            'SEL_METER_ID': "",
            'TIME_TYPE': "15"
        }

        data_30 = {
            'SELECT_ID': "20210601",
            'SEL_METER_ID': "",
            'TIME_TYPE': "30"
        }


        # 1 hour data crawl

        # res = s.post('https://pp.kepco.co.kr/rs/rs0101N_hour.do', json=data_30, cookies=res_login.cookies, headers=header_post)
        # print(res.text)


        # 30 min data crawl

        # table1_30 = soup.find_all('div', {'class': 'hori_table1'})[1]
        # table2_30 = soup.find_all('div', {'class': 'hori_table2'})[1]
        #
        # powerdata1_30 = table1_30.find_all('tr')
        # powerdata2_30 = table2_30.find_all('tr')
        #
        # powerdata_30 = powerdata1_30 + powerdata2_30

        # 15 min data crawl

    #     usage_page = s.post('https://pccs.kepco.co.kr/iSmart/pccs/usage/getGlobalUsageStats.do',
    #                        data=data_15)
    #
    #     soup = bs(usage_page.text, 'html.parser')
    #
    #     table1_15 = soup.find_all('div', {'class': 'hori_table1'})[1]
    #     table2_15 = soup.find_all('div', {'class': 'hori_table2'})[1]
    #
    #     powerdata1_15 = table1_15.find_all('tr')
    #     powerdata2_15 = table2_15.find_all('tr')
    #
    #     powerdata_15 = powerdata1_15 + powerdata2_15
    #
    #     powerdatas = {'60': powerdata_60, '30': powerdata_30, '15': powerdata_15}
    #
    #     result = []
    #
    #     for datas in list(powerdatas.values()):
    #         period = (list(powerdatas.keys())[list(powerdatas.values()).index(datas)])
    #         for data in datas:
    #             data_row = data.find_all('td')
    #             data_row = [x.text.strip() for x in data_row]
    #             if data_row:
    #                 item_obj = {
    #                     'date': str(start_year) + "-" + str(start_month) + "-" + str(start_day),
    #                     'time': data_row[0],
    #                     'usage': data_row[1],
    #                     'max_supply': data_row[2],
    #                     'period': period,
    #                 }
    #                 result.append(item_obj)
    #
    #     for item in result:
    #         print(item['date'])
    #         PowerData(crawl_num=crawl_num,
    #                   date=item['date'],
    #                   time=item['time'],
    #                   usage=item['usage'],
    #                   max_supply=item['max_supply'],
    #                   period=item['period']).save()
    #
    #     cur_day += 1
    #     progress_recorder.set_progress(cur_day, total_day)
    #     start_day += 1
    #
    # cur_logininfo.status = "DONE"
    # cur_logininfo.save()

    return 'work is complete'


print(scraping())

