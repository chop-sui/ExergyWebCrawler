from celery import shared_task
from jsbn import RSAKey

from celery_progress.backend import ProgressRecorder
import requests
from bs4 import BeautifulSoup as bs
from .models import LoginInfo, PowerData
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ExergyPowerManager.settings")

django.setup()

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

def totalDays(start_date, end_date):
    return (end_date-start_date).days

# celery -A ExergyPowerManager worker -l info (Command call for celery server)
@shared_task(bind=True)
def scraping(self, crawl_num, start_year, end_year, start_month, end_month, start_day, end_day):
    with requests.Session() as s:
        base_url = 'https://pp.kepco.co.kr/'
        login_url = 'https://pp.kepco.co.kr/login'

        cur_logininfo = LoginInfo.objects.get(pk=crawl_num)
        progress_recorder = ProgressRecorder(self)
        total_day = totalDays(cur_logininfo.startDate, cur_logininfo.endDate)
        cur_day = 0

        LOGIN_INFO = {'USER_ID': cur_logininfo.userId, 'USER_PWD': cur_logininfo.userPw}

        while start_year != end_year or start_month != end_month or start_day != end_day + 1:  # iterate usage_page
            print(start_year, start_month, start_day)
            if start_month in [1, 3, 5, 7, 8, 10]:
                if start_day > 31:
                    start_month += 1
                    start_day = 1

            elif start_month in [4, 6, 9, 11]:
                if start_day > 30:
                    start_month += 1
                    start_day = 1

            elif start_month == 2:
                if (start_year % 4 == 0 and start_year % 100 != 0) or start_year % 400 == 0:
                    if start_day > 29:
                        start_month += 1
                        start_day = 1
                else:
                    if start_day > 28:
                        start_month += 1
                        start_day = 1

            elif start_month == 12:
                if start_day > 31:
                    start_year += 1
                    start_month = 1
                    start_day = 1

            start_year_str = str(start_year)
            if start_month < 10:
                start_month_str = "0" + str(start_month)
            if start_day < 10:
                start_day_str = "0" + str(start_day)

            data_15 = {
                'SELECT_DT': start_year_str + start_month_str + start_day_str,
                'SEL_METER_ID': "",
                'TIME_TYPE': "15"
            }

            data_30 = {
                'SELECT_DT': start_year_str + start_month_str + start_day_str,
                'SEL_METER_ID': "",
                'TIME_TYPE': "30"
            }

            # login
            first_page = s.get(base_url)
            cookie_rsa = s.cookies.values()[1]
            cookie_ssid = s.cookies.values()[2]
            jsession_id = s.cookies.values()[0]
            cookie_str = concat_cookies(s.cookies)
            header['Cookie'] = cookie_str

            html = first_page.text
            soup = bs(html, 'html.parser')
            rsa_exponent = soup.find('input', {'id': 'RSAExponent'})['value']  # == 10001
            rsa = RSAKey()
            rsa.setPublic(cookie_rsa, rsa_exponent)

            id = jsession_id + '_' + rsa.encrypt(LOGIN_INFO['USER_ID'])
            pw = jsession_id + '_' + rsa.encrypt(LOGIN_INFO['USER_PWD'])

            payload = {'RSAExponent': rsa_exponent, 'USER_ID': id, 'USER_PWD': pw, 'viewType': 'web'}

            s.post(login_url, headers=header, data=payload)

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
                PowerData(crawl_num=crawl_num,
                          date=start_year_str + start_month_str + start_day_str,
                          time=data['MR_HHMI2'],
                          usage=data['F_AP_QT'],
                          max_supply=data['MAX_PWR'],
                          period="60").save()

            # 30 min data crawl
            res = s.post('https://pp.kepco.co.kr/rs/rs0101N_chart.do', json=data_30, headers=header)
            thirtymin_data_list = res.json()['list1']

            for data in thirtymin_data_list:
                PowerData(crawl_num=crawl_num,
                          date=start_year_str + start_month_str + start_day_str,
                          time=data['MR_HHMI2'],
                          usage=data['F_AP_QT'],
                          max_supply=data['MAX_PWR'],
                          period="30").save()

            # 15 min data crawl
            res = s.post('https://pp.kepco.co.kr/rs/rs0101N_chart.do', json=data_15, headers=header)
            fifteenmin_data_list = res.json()['list1']

            for data in fifteenmin_data_list:
                PowerData(crawl_num=crawl_num,
                          date=start_year_str + start_month_str + start_day_str,
                          time=data['MR_HHMI2'],
                          usage=data['F_AP_QT'],
                          max_supply=data['MAX_PWR'],
                          period="15").save()

            cur_day += 1
            progress_recorder.set_progress(cur_day, total_day)
            start_day += 1

        cur_logininfo.status = "DONE"
        cur_logininfo.save()

        return 'work is complete'

