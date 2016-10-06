#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-10-05

import json
from util.log import Logger
from util.db_mysql import DbMySql
from util.exceptions import NotFoundException
from util.response import http_response_handle


class Router(object):
    def __init__(self):
        self.json_path = {
            '/v1/search': self.search
        }

    def onMessage(self, request):
        # if request.method.lower() == 'post':
        if request.path in self.json_path:
            args = request.get_args()
            Logger.debug(args)
            return self.json_path[request.path](args, request)

        raise NotFoundException('Not Found')

    def search(self, args, request):
        keyword = args.get('s')
        offset = args.get('o', 0)
        if keyword:
            return DbMySql.interaction('search', self.query_info, keyword, offset, 10)

    @http_response_handle()
    def query_info(self, tst, keyword, start, count):
        sql = "SELECT id, info_hash, name, length, hit, create_time, access_ts, files FROM search WHERE MATCH(%s) "
        sql += "LIMIT %s, %s;"
        tst.execute(sql, (keyword, start, count))
        result = [list(one) for one in tst.fetchall()]
        for one in result:
            files = one[-1]
            del one[-1]
            if files:
                files = json.loads(files)
                detail_info = []
                for f in files[:3]:
                    detail_info.append([f['path'], f['length']])
                if detail_info:
                    one.append(detail_info)

        tst.execute('SHOW META')
        tmp = dict(tst.fetchall())
        return {'info': result, 'total': int(tmp['total'])}


Router = Router()
