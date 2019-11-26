#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-10-05

import json
import jinja2
from util.tool import Util
from util.log import Logger
from util.db_mysql import DbMySql
from twisted.internet import defer
from util.exceptions import NotFoundException
from util.response import http_response_handle


class Router(object):
    def __init__(self):
        self.env = jinja2.Environment(loader=jinja2.FileSystemLoader('assets/template'))
        self.json_path = {
            '/': self.index,
            '/q': self.search,
            '/d': self.detail
        }

    def onMessage(self, request):
        if request.path in self.json_path:
            args = request.get_args()
            Logger.debug(args)
            return self.json_path[request.path](args, request)

        raise NotFoundException('Not Found')

    @http_response_handle(response='html')
    def rander_page(self, result, tpl_name):
        tpl = self.env.get_template(tpl_name, globals={'Util': Util})
        return tpl.render(info=result).encode('utf-8')

    @http_response_handle(response='html')
    def index(self, args, request):
        tpl = self.env.get_template('index_new.html', globals={'Util': Util})
        return tpl.render().encode('utf-8')

    @defer.inlineCallbacks
    def search(self, args, request):
        keyword = args.get('s')
        page = int(args.get('p', 1))
        if page <= 0:
            page = 1
        elif page > 100:
            page = 100

        if keyword:
            result = yield DbMySql.interaction('search', self.do_search, keyword, page, 10)
            # Logger.debug(result)
            result = yield DbMySql.interaction('dht', self.do_search_detail, result)
            html = self.rander_page(result, 'search.html')
            defer.returnValue(html)

    @defer.inlineCallbacks
    def detail(self, args, request):
        keyword = args.get('s')
        tid = int(args.get('i', 0))
        if tid <= 0:
            tid = 1
        if keyword:
            result = yield DbMySql.interaction('dht', self.do_detail, keyword, tid)
            html = self.rander_page(result, 'detail.html')
            defer.returnValue(html)

    def do_search(self, tst, keyword, page, count):
        offset = (page - 1) * count
        sql = "SELECT id, info_hash, name, length, hit, create_time, access_ts FROM search WHERE MATCH(%s) "
        sql += "LIMIT %s, %s;"
        tst.execute(sql, (keyword, offset, count))
        result = [list(one) for one in tst.fetchall()]
        fields = ('id', 'info_hash', 'name', 'length', 'hit', 'create_time', 'access_ts')
        for i, one in enumerate(result):
            detail = dict(zip(fields, one))
            result[i] = detail

        tst.execute('SHOW META')
        tmp = dict(tst.fetchall())

        try:
            keyword = keyword.decode('utf-8')
        except:
            pass

        info = {
            'list': result,
            'total': int(tmp['total_found']),
            'keyword': keyword,
        }
        total_pages = info['total'] / count
        if info['total'] % count != 0:
            total_pages += 1
        if total_pages > 100:
            total_pages = 100
        prev_btn, rc_show, next_btn = self.calc_pages(total_pages, page)
        pages = {
            'total': total_pages,
            'page': page,
            'prev_btn': prev_btn,
            'next_btn': next_btn,
            'pages': rc_show
        }
        info['pages'] = pages
        return info

    def do_search_detail(self, tst, result):
        ids = []
        id_detail_map = dict()
        for one in result['list']:
            id_detail_map[one['id']] = one
            ids.append(str(one['id']))

        sql = "SELECT id, files FROM bt WHERE id IN (%s) LIMIT %s;"
        tst.execute(sql, (','.join(ids), len(ids)))
        files_detail = [list(one) for one in tst.fetchall()]
        for line in files_detail:
            if line[1] is not None:
                id_detail_map[line[0]]['files'] = json.loads(line[1])
        return result

    def do_detail(self, tst, keyword, tid):
        sql = "SELECT info_hash, name, length, hit, UNIX_TIMESTAMP(create_time) AS create_time, UNIX_TIMESTAMP(access_ts) AS access_ts, files FROM bt WHERE id=%s LIMIT 1;"
        tst.execute(sql, (tid,))
        result = tst.fetchall()
        if not result:
            raise NotFoundException('Not Found')

        values = list(result[0])
        fields = ('info_hash', 'name', 'length', 'hit', 'create_time', 'access_ts', 'files')
        detail = dict(zip(fields, values))
        if not detail['files']:
            del detail['files']
        else:
            detail['files'] = json.loads(detail['files'])

        try:
            keyword = keyword.decode('utf-8')
        except:
            pass
        return dict(keyword=keyword, **detail)

    def calc_pages(self, total, c_p):
        if total == 0 or c_p < 1 or c_p > total:
            return False, [], False

        prev_btn, next_btn = False, False
        left_dot, right_dot = False, False
        max_show, max_right, min_left = 10, c_p, c_p
        # left
        if c_p - 1 >= 6:
            left_dot = True
            rc_show = [c_p - 2, c_p - 1]
            max_show -= 5
            min_left -= 5
        else:
            rc_show = range(2, c_p)
            max_show -= len(rc_show)
            min_left = 2
        rc_show.append(c_p)
        # right
        if total - c_p >= 6:
            right_dot = True
            rc_show.extend([c_p + 1, c_p + 2])
            max_show -= 5
            max_right += 5
        else:
            tmp = range(c_p + 1, total)
            rc_show.extend(tmp)
            max_show -= len(tmp)
            max_right = total - 1

        while max_show > 0:
            tmp = max_show
            if min_left > 2:
                rc_show.insert(0, min_left)
                min_left -= 1
                max_show -= 1
            if max_show > 0:
                if max_right < total - 1:
                    rc_show.append(max_right)
                    max_right += 1
                    max_show -= 1
            if tmp == max_show:
                break

        if left_dot:
            rc_show.insert(0, '...')

        if right_dot:
            rc_show.append('...')

        if c_p != 1:
            rc_show.insert(0, 1)
        if c_p != total:
            rc_show.append(total)

        if c_p > 1:
            prev_btn = True

        if c_p < total:
            next_btn = True

        return prev_btn, rc_show, next_btn


Router = Router()
