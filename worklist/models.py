from django.db import models
from django.contrib.auth.models import User

class PowerData(models.Model):
    crawl_num = models.IntegerField(null=True)
    date = models.CharField(null=True, max_length=100)
    time = models.CharField(max_length=50)
    usage = models.CharField(max_length=100)
    max_supply = models.CharField(max_length=100)
    period = models.CharField(null=True, max_length=50)

class LoginInfo(models.Model):
    author = models.ForeignKey('accounts.User', related_name='worklists', on_delete=models.CASCADE, null=True)
    userId = models.CharField(max_length=50, null=True)
    userPw = models.CharField(max_length=50)
    startDate = models.DateField(null=True)
    endDate = models.DateField(null=True)
    status = models.CharField(max_length=50)
    period = models.CharField(null=True, max_length=50)
    taskId = models.CharField(max_length=300, null=True)

    def __str__(self):
        return str(self.userId)

    def get_start_year(self):
        return self.startDate.year

    def get_end_year(self):
        return self.endDate.year

    def get_start_month(self):
        return self.startDate.month

    def get_end_month(self):
        return self.endDate.month

    def get_start_day(self):
        return self.startDate.day

    def get_end_day(self):
        return self.endDate.day
