from django.views.generic import TemplateView
from django.http import HttpResponse
from django.urls import reverse
from django.shortcuts import redirect
from django.http import Http404
from .models import LoginInfo, PowerData
from .tasks import scraping
from datetime import datetime
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
import xlwt


class WorkListView(LoginRequiredMixin, TemplateView):
    login_url = settings.LOGIN_URL
    template_name = 'worklist/index.html'
    queryset = LoginInfo.objects.all()
    task_id_items = {}


    def get(self, request, *args, **kwargs):
        author = self.request.user
        worklist = self.queryset.filter(author=author)

        for work in worklist:
            self.task_id_items[work.pk] = work.taskId
        print(self.task_id_items)
        ctx = {
            'task_id_items': self.task_id_items,
            'worklist': worklist
        }
        return self.render_to_response(ctx)


class WorklistCreateView(LoginRequiredMixin, TemplateView):
    login_url = settings.LOGIN_URL
    template_name = 'worklist/create_work.html'
    queryset = LoginInfo.objects.all()
    pk_url_kwargs = 'work_id'
    success_message = 'Crawling Successfully Started'

    def get_object(self, queryset=None):
        queryset = queryset or self.queryset
        pk = self.kwargs.get(self.pk_url_kwargs)
        work = queryset.filter(pk=pk).first()

        if pk and not work:
            raise Http404('invalid pk')
        return work

    def get(self, request, *args, **kwargs):
        work = self.get_object()

        ctx = {
            'work': work
        }
        return self.render_to_response(ctx)

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        post_data = {key: request.POST.get(key) for key in ('userId', 'userPw', 'startDate', 'endDate')}
        for key in post_data:
            if not post_data[key]:
                messages.error(self.request, 'There is no {}.'.format(key), extra_tags='danger')  # error 레벨로 메시지 저장

        post_data['author'] = self.request.user
        post_data['status'] = "waiting"

        if len(messages.get_messages(request)) == 0:  # 메시지가 있다면 아무것도 처리하지 않음
            if action == 'create':
                login_info = LoginInfo.objects.create(**post_data)
                startDate = post_data.get('startDate')
                endDate = post_data.get('endDate')

                login_info.startDate = datetime.strptime(startDate, '%Y-%m-%d')
                login_info.endDate = datetime.strptime(endDate, '%Y-%m-%d')

                crawl_num = login_info.id

                task = scraping.delay(crawl_num, login_info.get_start_year(), login_info.get_end_year(),
                                      login_info.get_start_month(), login_info.get_end_month(),
                                      login_info.get_start_day(), login_info.get_end_day())

                login_info.taskId = task.task_id
                login_info.save()

                if task == "OK":
                    messages.error(self.request, 'Wrong iSMART ID/PASSWORD', extra_tags='danger')
                else:
                    messages.success(self.request, self.success_message)  # success 레벨로 메시지 저장
            else:
                messages.error(self.request, 'Unknown Request', extra_tags='danger')  # error 레벨로 메시지 저장


            return redirect(reverse('worklist:index'))
            # return render(request, 'worklist/index.html', {'task_id_items': task_id_items, 'worklist': worklist})
        ctx = {
            'work': self.get_object() if action == 'update' else None
        }
        return self.render_to_response(ctx)


def export_usage_xls(request, usage_id):
    obj = LoginInfo.objects.get(id=usage_id)
    filename = "Usage from-" + str(obj.startDate) + "-to-" + str(obj.endDate)
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=' + filename + ".xls"

    wb = xlwt.Workbook(encoding='utf-8')

    # 1 hour sheet
    ws1 = wb.add_sheet('1 hour')

    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    ws1.write(0, 0, 'Date', font_style)

    # standard column & row setting
    for col_num in range(1, 25):
        ws1.write(row_num, col_num, col_num, font_style)

    font_style = xlwt.XFStyle()

    rows = PowerData.objects.filter(crawl_num=usage_id, period='60').values_list('date', flat=True)

    yearlist = list(dict.fromkeys(rows))

    for i in range(len(yearlist)):
        row_num += 1
        ws1.write(row_num, 0, yearlist[i], font_style)

    rows_usage = PowerData.objects.filter(crawl_num=usage_id, period='60').values_list('usage', flat=True)

    print(len(rows_usage))

    # 1 hour data input
    i = 0
    for j in range(int(len(rows_usage) / 24)):
        for col_num in range(0, 24):
            ws1.write(j + 1, col_num + 1, rows_usage[col_num + 24 * i], font_style)
        i += 1

    # 30 min sheet
    ws2 = wb.add_sheet('30 minutes')

    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    ws2.write(0, 0, 'Date', font_style)

    # standard column & row setting
    rows = PowerData.objects.filter(crawl_num=usage_id, period='30').values_list('time', flat=True)

    for col_num in range(48):
        ws2.write(row_num, col_num + 1, rows[col_num], font_style)

    font_style = xlwt.XFStyle()

    rows = PowerData.objects.filter(crawl_num=usage_id, period='30').values_list('date', flat=True)

    yearlist = list(dict.fromkeys(rows))

    for i in range(len(yearlist)):
        row_num += 1
        ws2.write(row_num, 0, yearlist[i], font_style)

    rows_usage = PowerData.objects.filter(crawl_num=usage_id, period='30').values_list('usage', flat=True)

    # 30 min data input
    i = 0
    for j in range(int(len(rows_usage) / 48)):
        for col_num in range(0, 48):
            ws2.write(j + 1, col_num + 1, rows_usage[col_num + 48 * i], font_style)
        i += 1

    # 15 min sheet
    ws3 = wb.add_sheet('15 minutes')

    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    ws3.write(0, 0, 'Date', font_style)

    # standard column & row setting
    rows = PowerData.objects.filter(crawl_num=usage_id, period='15').values_list('time', flat=True)

    for col_num in range(96):
        ws3.write(row_num, col_num + 1, rows[col_num], font_style)

    font_style = xlwt.XFStyle()

    rows = PowerData.objects.filter(crawl_num=usage_id, period='15').values_list('date', flat=True)

    yearlist = list(dict.fromkeys(rows))

    for i in range(len(yearlist)):
        row_num += 1
        ws3.write(row_num, 0, yearlist[i], font_style)

    rows_usage = PowerData.objects.filter(crawl_num=usage_id, period='15').values_list('usage', flat=True)

    # 15 min data input
    i = 0
    for j in range(int(len(rows_usage) / 96)):
         for col_num in range(0, 96):
              ws3.write(j + 1, col_num + 1, rows_usage[col_num + 96 * i], font_style)
         i += 1

    wb.save(response)

    return response

