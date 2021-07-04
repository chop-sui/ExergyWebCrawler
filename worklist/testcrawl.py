import json
from pprint import pprint

import requests
from bs4 import BeautifulSoup as bs
from jsbn import RSAKey

header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36',
    'Content-Type': 'application/x-www-form-urlencoded'
}

def concat_cookies(cookie_jar):
    cookie_rsa = cookie_jar.values()[1]
    cookie_ssid = cookie_jar.values()[2]
    jsession_id = cookie_jar.values()[0]
    cookie_str = 'cookieSsId=' + cookie_ssid + '; ' + 'cookieRsa=' + cookie_rsa + '; ' + 'JSESSIONID=' + jsession_id
    return cookie_str

def scraping():
    with requests.Session() as s:
        base_url = 'https://pp.kepco.co.kr/'
        login_url = 'https://pp.kepco.co.kr/login'

        LOGIN_INFO = {'USER_ID': "0236915825", 'USER_PWD': "humphreys1!"}
        first_page = s.get(base_url)
        cookie_rsa = s.cookies.values()[1]
        cookie_ssid = s.cookies.values()[2]
        jsession_id = s.cookies.values()[0]
        cookie_str = concat_cookies(s.cookies)
        header['Cookie'] = cookie_str

        html = first_page.text
        soup = bs(html, 'html.parser')
        rsa_exponent = soup.find('input', {'id': 'RSAExponent'})['value'] # == 10001
        rsa = RSAKey()
        rsa.setPublic(cookie_rsa, rsa_exponent)

        id = jsession_id + '_' + rsa.encrypt(LOGIN_INFO['USER_ID'])
        pw = jsession_id + '_' + rsa.encrypt(LOGIN_INFO['USER_PWD'])

        payload = {'RSAExponent': rsa_exponent, 'USER_ID': id, 'USER_PWD': pw, 'viewType': 'web'}

        s.post(login_url, headers=header, data=payload)

        data_15 = {
            'SELECT_DT': "20210601",
            'SEL_METER_ID': "",
            'TIME_TYPE': "15"
        }

        data_30 = {
            'SELECT_DT': "20210601",
            'SEL_METER_ID': "",
            'TIME_TYPE': "30"
        }


        # 1 hour data crawl
        header['Content-Type'] = 'application/json'
        header['Accept'] = 'application/json, text/javascript, */*; q=0.01'
        header['X-Requested-With'] = 'XMLHttpRequest'
        cookie_str = concat_cookies(s.cookies)
        header['Cookie'] = cookie_str
        res = s.post('https://pp.kepco.co.kr/rs/rs0101N_hour.do', json=data_30, headers=header)

        # F_LARAP_QT: 무효전력(지상)
        # F_LERAP_QT: 무효전력(진상)
        # MR_HHMI2: 시
        # F_AP_QT: 사용량
        # MAX_PWR: 최대수요
        # F_LARAP_PF: 역률(지상)
        # F_LERAP_PF: 역률(진상)

        hour_data_list = res.json()

        for data in hour_data_list:
            # get the needed data and save them into the database



    return 'work is complete'


print(scraping())

