#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2015-10-09

import os
import time
from twisted.web import http
from twisted.web import server
from twisted.web import static
from twisted.web import resource
from twisted.python import logfile
from util.tool import Time
from util.log import Logger
from util.response import json_response_500


class BasicResource(static.File):
    pass


class BasicDailyLogFile(logfile.DailyLogFile):
    def suffix(self, tupledate):
        try:
            t = map(str, tupledate)
        except:
            t = map(str, self.toDate(tupledate))
        return '%04d-%02d-%02d' % (int(t[0]), int(t[1]), int(t[2]))


class BasicRequest(server.Request):
    cookieString = 'x_session'
    secureCookieString = 'x_session'

    def __init__(self, *args, **kw):
        server.Request.__init__(self, *args, **kw)
        self.started = time.time()

    def render(self, resrc):
        if isinstance(resrc, (resource.NoResource, static.DirectoryLister)):
            self.channel.receive_done(self)
        else:
            self.setHeader('Access-Control-Allow-Origin', self.get_origin())
            self.setHeader('Access-Control-Allow-Credentials', 'true')
            server.Request.render(self, resrc)

    def getClientIP(self):
        try:
            X_Forwarded_For = self.requestHeaders.getRawHeaders('X-Forwarded-For')
            if X_Forwarded_For:
                return X_Forwarded_For[0].split(',')[0].strip()
        except Exception, e:
            pass
        return self.getHeader('X-Real-IP') or server.Request.getClientIP(self)

    def getSession(self, sessionInterface=None, forceNotSecure=False):
        # Make sure we aren't creating a secure session on a non-secure page
        secure = self.isSecure() and not forceNotSecure

        if not secure:
            cookieString = self.cookieString or b"TWISTED_SESSION"
            sessionAttribute = "_insecureSession"
        else:
            cookieString = self.secureCookieString or b"TWISTED_SECURE_SESSION"
            sessionAttribute = "_secureSession"

        session = getattr(self, sessionAttribute)

        # Session management
        if not session:
            cookiename = b"_".join([cookieString] + self.sitepath)
            sessionCookie = self.getCookie(cookiename)
            if sessionCookie:
                try:
                    session = self.site.getSession(sessionCookie)
                except KeyError:
                    pass
            # if it still hasn't been set, fix it up.
            if not session:
                session = self.site.makeSession()
                self.addCookie(cookiename, session.uid, path=b"/",
                               secure=secure)

        session.touch()
        setattr(self, sessionAttribute, session)

        if sessionInterface:
            return session.getComponent(sessionInterface)

        return session

    def get_args(self):
        args = {}
        for k, v in self.args.iteritems():
            if len(v) > 1:
                args[k] = v
            else:
                args[k] = v[0]
        return args

    def raw_data(self):
        return self.content.read()

    def get_origin(self):
        return self.getHeader('origin') or '*'


class BasicHttpProtocol(http.HTTPChannel):
    def make_task(self, request):
        raise NotImplementedError

    def receive_done(self, request):
        try:
            self.make_task(request)
        except Exception, e:
            Logger.exception()
            body, content_type = json_response_500(request)
            Logger.debug('<====', request.path, content_type, repr(body))


class BasicHttpFactory(server.Site):
    def __init__(self, logPath, resource, **kwargs):
        logPath += '.access'
        if 'logFormatter' not in kwargs:
            kwargs['logFormatter'] = self.time_log_formatter
        server.Site.__init__(self, resource, logPath=logPath, **kwargs)

    def _openLogFile(self, path):
        return BasicDailyLogFile(os.path.basename(path), os.path.dirname(path))

    @classmethod
    def time_log_formatter(cls, timestamp, request):
        referrer = http._escape(request.getHeader("referer") or "-")
        agent = http._escape(request.getHeader("user-agent") or "-")
        tc = round(time.time() - request.started, 4)
        line = u'%(fmt)s | "%(ip)s" %(tc)ss %(code)d %(length)s "%(method)s %(uri)s %(proto)s" "%(agent)s" "%(ref)s"' % {
            'fmt': Time.current_time('%m-%d %H:%M:%S.%f'),
            'ip': http._escape(request.getClientIP() or "-"),
            'tc': tc,
            'method': http._escape(request.method),
            'uri': http._escape(request.uri),
            'proto': http._escape(request.clientproto),
            'code': request.code,
            'length': request.sentLength or "-",
            'agent': agent,
            'ref': referrer,
        }
        return line
