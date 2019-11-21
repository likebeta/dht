#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2014-11-07

import os
import re
import time
import datetime
import calendar


class Time(object):
    @classmethod
    def asctime(cls, p_tuple=None):
        return time.asctime(p_tuple)

    @classmethod
    def current_ts(cls, dt=None):
        if dt is None:
            return int(time.time())
        else:
            t = dt.timetuple()
            return int(time.mktime(t))

    @classmethod
    def current_ms(cls, dt=None):
        if dt is None:
            return int(time.time() * 1000)
        else:
            t = dt.timetuple()
            return int(time.mktime(t) * 1000)

    @classmethod
    def is_today(cls, s):
        tm = time.strptime(s, '%Y-%m-%d %X')
        tm_now = time.localtime()
        return tm.tm_mday == tm_now.tm_mday and tm.tm_year == tm_now.tm_year and tm.tm_mon == tm_now.tm_mon

    @classmethod
    def is_yesterday(cls, s):
        tm = time.strptime(s, '%Y-%m-%d %X')
        tm_yes = time.localtime(int(time.time()) - 3600 * 24)
        return tm.tm_mday == tm_yes.tm_mday and tm.tm_year == tm_yes.tm_year and tm.tm_mon == tm_yes.tm_mon

    @classmethod
    def current_time(cls, fmt='%Y-%m-%d %X'):
        return datetime.datetime.now().strftime(fmt)

    @classmethod
    def datetime_now(cls, fmt='%Y-%m-%d %X.%f'):
        return cls.current_time(fmt)

    @classmethod
    def datetime(cls):
        return datetime.datetime.now()

    @classmethod
    def current_localtime(cls, t=None):
        if not t:
            t = cls.current_ts()
        return time.localtime(t)

    @classmethod
    def next_days(cls, dt=None, days=1):
        if dt is None:
            dt = datetime.datetime.now()
        return dt + datetime.timedelta(days=days)

    @classmethod
    def next_days_ts(cls, ts=None, days=1):
        if ts is None:
            ts = int(time.time())
        return ts + 86400 * days

    @classmethod
    def timestamp_to_str(cls, ts, fmt=None):
        t = time.localtime(ts)
        if fmt is None:
            fmt = '%Y-%m-%d %X'
        return time.strftime(fmt, t)

    @classmethod
    def datetime_to_str(cls, dt, fmt=None):
        if fmt is None:
            fmt = '%Y-%m-%d %X'
        return dt.strftime(fmt)

    @classmethod
    def str_to_timestamp(cls, s, fmt=None):
        if fmt is None:
            fmt = '%Y-%m-%d %X'
        t = datetime.datetime.strptime(s, fmt).timetuple()
        return int(time.mktime(t))

    @classmethod
    def str_to_datetime(cls, s, fmt=None):
        if fmt is None:
            fmt = '%Y-%m-%d %X'
        return datetime.datetime.strptime(s, fmt)

    @classmethod
    def timestamp_to_datetime(cls, ts):
        return datetime.datetime.fromtimestamp(ts)

    @classmethod
    def tomorrow_start_ts(cls, ts=None):
        if ts is None:
            ts = int(time.time())
        now_tm = time.localtime(ts)
        return ts + 86400 - now_tm.tm_hour * 3600 - now_tm.tm_min * 60 - now_tm.tm_sec

    @classmethod
    def today_start_ts(cls, ts=None):
        if ts is None:
            ts = int(time.time())
        now_tm = time.localtime(ts)
        return ts - now_tm.tm_hour * 3600 - now_tm.tm_min * 60 - now_tm.tm_sec

    @classmethod
    def current_week_start_ts(cls, ts=None):
        """ 获取本周开始的时间戳
        """
        if ts is None:
            ts = int(time.time())
        tm = time.localtime(ts)
        return ts - tm.tm_wday * 86400 - tm.tm_hour * 3600 - tm.tm_min * 60 - tm.tm_sec

    @classmethod
    def current_week_left_time(cls, ts=None):
        tm = time.localtime(ts)
        return (7 - tm.tm_wday) * 86400 - tm.tm_hour * 3600 - tm.tm_min * 60 - tm.tm_sec

    @classmethod
    def pre_week_start_ts(cls, ts=None):
        ts = cls.current_week_start_ts(ts)
        return ts - 86400 * 7

    @classmethod
    def next_week_start_ts(cls, ts=None):
        ts = cls.current_week_start_ts(ts)
        return ts + 86400 * 7

    @classmethod
    def current_month_start_ts(cls, ts=None):
        if ts is None:
            ts = int(time.time())
        tm = time.localtime(ts)
        return ts - (tm.tm_mday - 1) * 86400 - tm.tm_hour * 3600 - tm.tm_min * 60 - tm.tm_sec

    @classmethod
    def current_month_left_time(cls, ts=None):
        tm = time.localtime(ts)
        _, days = calendar.monthrange(tm.tm_year, tm.tm_mon)
        return (days - tm.tm_mday + 1) * 86400 - tm.tm_hour * 3600 - tm.tm_min * 60 - tm.tm_sec

    @classmethod
    def pre_month_start_ts(cls, ts=None):
        tm = time.localtime(ts)
        if tm.tm_mon > 1:
            dt = datetime.datetime(tm.tm_year, tm.tm_mon - 1, 1)
        else:
            dt = datetime.datetime(tm.tm_year - 1, 12, 1)
        return int(time.mktime(dt.timetuple()))

    @classmethod
    def next_month_start_ts(cls, ts=None):
        if ts is None:
            ts = int(time.time())
        tm = time.localtime(ts)
        _, days = calendar.monthrange(tm.tm_year, tm.tm_mon)
        return ts - tm.tm_hour * 3600 - tm.tm_min * 60 - tm.tm_sec + (days - tm.tm_mday + 1) * 86400

    @classmethod
    def up_days(cls, dt=None):
        if dt is None:
            dt = datetime.date.today()
        return (dt - datetime.date(2016, 1, 1)).days

    @classmethod
    def weekday(cls, today=True, year=None, month=None, day=None):
        if today:
            d = datetime.datetime.now()
        else:
            d = datetime.datetime(year, month, day)
        return d.weekday()

    @classmethod
    def timestamp_from_hms(cls, hms, now_dt=None):
        if now_dt is None:
            now_dt = datetime.datetime.now()
        prefix = cls.datetime_to_str(now_dt, '%Y-%m-%d')
        return cls.str_to_timestamp('%s %s' % (prefix, hms))

    @classmethod
    def at_this_time(cls, start, end, now_dt=None):
        if now_dt is None:
            now_dt = datetime.datetime.now()
        prefix = cls.datetime_to_str(now_dt, '%Y-%m-%d')
        now_ts = cls.current_ts(now_dt)
        start_ts = cls.str_to_timestamp('%s %s' % (prefix, start))
        end_ts = Time.str_to_timestamp('%s %s' % (prefix, end))
        if start_ts <= now_ts <= end_ts:
            return True
        return False

    @classmethod
    def month_days(cls, year, month):
        _, days = calendar.monthrange(year, month)
        return days


class Util(object):
    @classmethod
    def sizeof_fmt(cls, num, suffix='B'):
        for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
            if abs(num) < 1024.0:
                return "%3.2f %s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.2f %s%s" % (num, 'Y', suffix)

    @classmethod
    def format_size(cls, sz):
        return format(sz, ',')

    @classmethod
    def calc_days(cls, ts, now_ts=None):
        if now_ts is None:
            now_ts = int(time.time())
        return (now_ts - ts) / 86400 + 1

    @classmethod
    def highlight_words(cls, s, *words):
        try:
            for word in words:
                s = re.sub(word, '<strong>%s</strong>' % word, s)
        except:
            pass
        return s

    @classmethod
    def format_ts(cls, ts, fmt='%Y-%m-%d %X'):
        return Time.timestamp_to_str(ts, fmt)

    @classmethod
    def abs_path(cls, p):
        path_ = os.path.abspath(os.path.expanduser(p))
        return path_

    @classmethod
    def make_dirs(cls, path_):
        if not os.path.exists(path_):
            os.makedirs(path_)
