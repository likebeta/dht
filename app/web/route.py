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
        self.env = jinja2.Environment(loader=jinja2.FileSystemLoader('template'))
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
        tpl = self.env.get_template('index.html', globals={'Util': Util})
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

        # 最多显示10个页码
        left_page = c_p - 1
        right_page = c_p + 1
        pages = [c_p]
        while len(pages) < 10:
            if left_page >= 1:
                pages.insert(0, left_page)
                left_page -= 1
            if len(pages) < 10 and right_page <= total:
                pages.append(right_page)
                right_page += 1
            if left_page < 1 and right_page > total:
                break
        return c_p > 1, pages, c_p < total


Router = Router()
