#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-10-17

import time
import commands


def log(*args):
    prefix = time.strftime("%m-%d %H:%M:%S")
    msg = [str(arg) for arg in args]
    print '%s | %s' % (prefix, ' '.join(msg))


def exec_cmd(cmd, func=None):
    log('start exec cmd:', cmd)
    sts, text = commands.getstatusoutput(cmd)
    if sts:
        log('failed exec cmd:', cmd, 'with', text)
        return False

    if func and not func(text):
        return False

    return True


def check_running():
    cmd = 'ps -ef | grep dht_worker | grep -v grep | wc -l'
    if exec_cmd(cmd, lambda text: int(text) == 0):
        exec_cmd('sh start.sh')


def main():
    fmt = time.strftime('%Y%m%d%H%M%S')
    # crontab是2, 直接运行是1
    if not exec_cmd('ps -ef | grep backup.py | grep -v grep | wc -l', lambda text: int(text) == 2):
        return False

    cmds = (
        ('ls -l metadata | wc -l', lambda text: int(text) >= 200000),
        ('sh stop.sh',),
        (r'find ./dht -name "*.pyc" -exec rm "{}" \;',),
        ('tar -jcf metadata.%s.tar.bz2 metadata' % fmt,),
        ('sh dropbox_uploader.sh upload metadata.%s.tar.bz2 metadata.%s.tar.bz2' % (fmt, fmt),),
        ('rm -rf dht.log metadata metadata.%s.tar.bz2' % fmt,),
        ('sh start.sh',),
    )
    for cmd in cmds:
        if not exec_cmd(*cmd):
            check_running()
            return False
    return True


if __name__ == '__main__':
    import sys

    success = main()
    if success:
        sys.exit(1)
