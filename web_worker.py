#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-10-05

import setting
from twisted.internet import defer
from twisted.internet import reactor
from twisted.python.failure import Failure
from util.log import Logger
from util.response import JsonResult
from util.response import XmlResult
from util.response import HtmlResult
from util.exceptions import SystemException
from util.exceptions import NotFoundException
from util.exceptions import ForbiddenException
from web.route import Router
from web.protocol import BasicRequest
from web.protocol import BasicResource
from web.protocol import BasicHttpFactory
from web.protocol import BasicHttpProtocol
from util.db_mysql import DbMySql


class ServerHttpProtocol(BasicHttpProtocol):
    def __defer_callback(self, result, request):
        if request._disconnected:
            Logger.info('<====', request.path, 'connection lost')
        elif isinstance(result, Failure):
            Logger.exception()
            body = '{"error":500,"desc":"System Error"}'
            request.setResponseCode(500)
            request.setHeader('Content-Type', 'application/json; charset=utf-8')
            request.setHeader('Content-Length', str(len(body)))
            request.write(body)
            request.finish()
            Logger.debug('<====', request.path, 'json', body)
        else:
            body = str(result)
            request.setHeader('Content-Type', 'application/json; charset=utf-8')
            request.setHeader('Content-Length', str(len(body)))
            request.write(body)
            request.finish()
            Logger.debug('<====', request.path, 'json', body)

    def makeTask(self, request):
        Logger.debug('====>', request.path)
        try:
            mo = Router.onMessage(request)
            if isinstance(mo, defer.Deferred):
                mo.addBoth(self.__defer_callback, request)
            elif request._disconnected:
                Logger.info('<====', request.path, 'connection lost')
            else:
                if isinstance(mo, JsonResult):
                    body, content_type = str(mo), 'application/json; charset=utf-8'
                elif isinstance(mo, XmlResult):
                    body, content_type = str(mo), 'text/xml; charset=utf-8'
                elif isinstance(mo, HtmlResult):
                    body, content_type = str(mo), 'text/html; charset=utf-8'
                else:
                    body, content_type = str(mo), 'text/plain; charset=utf-8'
                request.setHeader('Access-Control-Allow-Origin', request.get_origin())
                request.setHeader('Access-Control-Allow-Credentials', 'true')
                request.setHeader('Content-Type', content_type)
                request.setHeader('Content-Length', str(len(body)))
                request.write(body)
                request.finish()
                Logger.debug('<====', request.path, repr(mo))
        except SystemException, e:
            body = '{"error":500,"desc":"System Error"}'
            request.setResponseCode(500)
            request.setHeader('Content-Type', 'application/json; charset=utf-8')
            request.setHeader('Content-Length', str(len(body)))
            request.write(body)
            request.finish()
            Logger.debug('<====', request.path, 'json', body)
        except NotFoundException, e:
            body = '{"error":404,"desc":"Not Found"}'
            request.setResponseCode(404)
            request.setHeader('Content-Type', 'application/json; charset=utf-8')
            request.setHeader('Content-Length', str(len(body)))
            request.write(body)
            request.finish()
            Logger.debug('<====', request.path, 'json', body)
        except ForbiddenException, e:
            body = '{"error":403,"desc":"Forbidden Access"}'
            request.setResponseCode(403)
            request.setHeader('Content-Type', 'application/json; charset=utf-8')
            request.setHeader('Content-Length', str(len(body)))
            request.write(body)
            request.finish()
            Logger.debug('<====', request.path, 'json', body)
        except Exception, e:
            Logger.exception()
            body = '{"error":500,"desc":"System Error"}'
            request.setHeader('Access-Control-Allow-Origin', request.get_origin())
            request.setHeader('Access-Control-Allow-Credentials', 'true')
            request.setHeader('Content-Type', 'application/json; charset=utf-8')
            request.setHeader('Content-Length', str(len(body)))
            request.write(body)
            request.finish()
            Logger.debug('<====', request.path, 'json', body)


class ServerHttpFactory(BasicHttpFactory):
    protocol = ServerHttpProtocol
    requestFactory = BasicRequest

    def __init__(self, logPath=None, webroot=None):
        BasicHttpFactory.__init__(self, logPath, BasicResource(webroot))


if __name__ == "__main__":
    Logger.show_task_id(False)
    Logger.open_std_log()
    DbMySql.connect('search', setting.search_db_info)
    # reactor.listenTCP(8888, ServerHttpFactory(), interface='127.0.0.1')
    reactor.listenTCP(8888, ServerHttpFactory(setting.log_path, setting.webroot))
    reactor.run()
