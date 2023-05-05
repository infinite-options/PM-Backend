
from datetime import date, timedelta, datetime
import calendar
from calendar import monthrange
from dateutil.relativedelta import relativedelta
from pandas.tseries.holiday import USFederalHolidayCalendar


def diff_month(d1, d2):
    return (d1.year - d2.year) * 12 + d1.month - d2.month


def days_in_month(dt): return monthrange(
    dt.year, dt.month)[1]


def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    return d + timedelta(days_ahead)


def next_weekday_biweekly(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 14
    return d + timedelta(days_ahead)


def usholiday(dt):
    # dt = datetime.strptime('2023-07-04', '%Y-%m-%d')
    dTime = datetime.strptime(dt, '%Y-%m-%d')
    cal = USFederalHolidayCalendar()
    holidays = cal.rules
    holidays = cal.holidays(
        start='2023-01-01', end='2023-12-31').to_pydatetime()
    if dTime in holidays or dTime > 5:
        return 'true'


def date_for_weekday(day: int, start_date):
    #  today = date.today()
    # weekday returns the offsets 0-6
    # If you need 1-7, use isoweekday
    weekday = start_date.weekday()
    return start_date + timedelta(days=day - weekday)
