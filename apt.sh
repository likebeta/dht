#!/usr/bin/env bash
# -*- coding=utf-8 -*-

# Author: 易思龙 <ixxoo.me@gmail.com>
# Create: 2015-05-29

apt-get install libxml2-dev libxslt1-dev python-dev mysql-server sphinxsearch gcc libssl-dev -y
wget https://bootstrap.pypa.io/get-pip.py
pypy get-pip.py
pypy -m pip install -r requirements.txt
