from celery import shared_task
from celery_progress.backend import ProgressRecorder
import requests
from bs4 import BeautifulSoup as bs
from .models import LoginInfo, PowerData
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ExergyPowerManager.settings")

django.setup()

header = {
    'Referer': 'https://pccs.kepco.co.kr/iSmart/jsp/cm/login/main.jsp',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36'
}

# class CallbackTask(celery.Task):
#     def on_success(self, retval, task_id, args, kwargs):


def totalDays(start_date, end_date):
    return (end_date-start_date).days



# celery -A ExergyPowerManager worker -l info (Command call for celery server)
@shared_task(bind=True)
def scraping(self, crawl_num, start_year, end_year, start_month, end_month, start_day, end_day):
    with requests.Session() as s:
        base_URL = 'https://pccs.kepco.co.kr'
        res = s.get(base_URL)
        soup = bs(res.content, 'html.parser')
        target_URL = soup.find('frame').get('src')
        target_URL = base_URL + target_URL

        cur_logininfo = LoginInfo.objects.get(pk=crawl_num)
        progress_recorder = ProgressRecorder(self)
        total_day = totalDays(cur_logininfo.startDate, cur_logininfo.endDate)
        cur_day = 0

        LOGIN_INFO = {'userId': cur_logininfo.userId, 'password': cur_logininfo.userPw}

        login_req = s.post(base_URL + '/iSmart/cm/login.do', headers=header, data=LOGIN_INFO)
        # print(login_req.headers)

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

            data_15 = {
                'diodval': 30,
                'reviseFlag': 30,
                'year': start_year,
                'month': start_month,
                'day': start_day,
                'diodGubun': 0,
                'searchType_min': 15,
            }

            data_30 = {
                'diodval': 30,
                'reviseFlag': 30,
                'year': start_year,
                'month': start_month,
                'day': start_day,
                'diodGubun': 0,
                'searchType_min': 30,
            }

            # 1 hour data crawl

            usage_page = s.post('https://pccs.kepco.co.kr/iSmart/pccs/usage/getGlobalUsageStats.do',
                                data=data_30)

            soup = bs(usage_page.text, 'html.parser')

            table_check = soup.find('table', {'class': 'basic_table'})

            if table_check is None:
                cur_logininfo.status = "FAILED"
                cur_logininfo.save()
                return "OK"

            table1_60 = soup.find_all('div', {'class': 'hori_table1'})[0]
            table2_60 = soup.find_all('div', {'class': 'hori_table2'})[0]

            powerdata1_60 = table1_60.find_all('tr')
            powerdata2_60 = table2_60.find_all('tr')

            powerdata_60 = powerdata1_60 + powerdata2_60

            # 30 min data crawl

            table1_30 = soup.find_all('div', {'class': 'hori_table1'})[1]
            table2_30 = soup.find_all('div', {'class': 'hori_table2'})[1]

            powerdata1_30 = table1_30.find_all('tr')
            powerdata2_30 = table2_30.find_all('tr')

            powerdata_30 = powerdata1_30 + powerdata2_30

            # 15 min data crawl

            usage_page = s.post('https://pccs.kepco.co.kr/iSmart/pccs/usage/getGlobalUsageStats.do',
                                data=data_15)

            soup = bs(usage_page.text, 'html.parser')

            table1_15 = soup.find_all('div', {'class': 'hori_table1'})[1]
            table2_15 = soup.find_all('div', {'class': 'hori_table2'})[1]

            powerdata1_15 = table1_15.find_all('tr')
            powerdata2_15 = table2_15.find_all('tr')

            powerdata_15 = powerdata1_15 + powerdata2_15

            powerdatas = {'60': powerdata_60, '30': powerdata_30, '15': powerdata_15}

            result = []

            for datas in list(powerdatas.values()):
                period = (list(powerdatas.keys())[list(powerdatas.values()).index(datas)])
                for data in datas:
                    data_row = data.find_all('td')
                    data_row = [x.text.strip() for x in data_row]
                    if data_row:
                        item_obj = {
                            'date': str(start_year) + "-" + str(start_month) + "-" + str(start_day),
                            'time': data_row[0],
                            'usage': data_row[1],
                            'max_supply': data_row[2],
                            'period': period,
                        }
                        result.append(item_obj)

            for item in result:
                print(item['date'])
                PowerData(crawl_num=crawl_num,
                          date=item['date'],
                          time=item['time'],
                          usage=item['usage'],
                          max_supply=item['max_supply'],
                          period=item['period']).save()

            cur_day += 1
            progress_recorder.set_progress(cur_day, total_day)
            start_day += 1

        cur_logininfo.status = "DONE"
        cur_logininfo.save()

        return 'work is complete'

