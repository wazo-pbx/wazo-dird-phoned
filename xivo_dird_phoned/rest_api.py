# -*- coding: utf-8 -*-

# Copyright (C) 2015 Avencall
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

from datetime import timedelta

import logging
import os

import cherrypy
from cherrypy.process.servers import ServerAdapter
from cherrypy.wsgiserver import CherryPyWSGIServer
from cherrypy.wsgiserver import WSGIPathInfoDispatcher
from cherrypy.wsgiserver.ssl_builtin import BuiltinSSLAdapter
from flask import Flask
from flask_restful import Api
from flask_cors import CORS
from werkzeug.contrib.fixers import ProxyFix
from xivo import http_helpers


VERSION = 0.1

logger = logging.getLogger(__name__)
api = Api(prefix='/{}'.format(VERSION))


class RestApi(object):

    def __init__(self, config):
        self.config = config
        self.app = Flask('xivo_dird_phoned')
        http_helpers.add_logger(self.app, logger)
        self.app.after_request(http_helpers.log_request)
        self.app.wsgi_app = ProxyFix(self.app.wsgi_app)
        self.app.secret_key = os.urandom(24)
        self.app.permanent_session_lifetime = timedelta(minutes=5)
        self.load_cors()
        self.api = api

    def load_cors(self):
        cors_config = dict(self.config.get('cors', {}))
        enabled = cors_config.pop('enabled', False)
        if enabled:
            CORS(self.app, **cors_config)

    def run(self):
        self.api.init_app(self.app)
        http_config = self.config['http']
        https_config = self.config['https']

        wsgi_app = WSGIPathInfoDispatcher({'/': self.app})
        cherrypy.server.unsubscribe()
        cherrypy.config.update({'environment': 'production'})

        if https_config['enabled']:
            try:
                _check_file_readable(https_config['certificate'])
                _check_file_readable(https_config['private_key'])

                bind_addr_https = (https_config['host'], https_config['port'])
                ssl_adapter = BuiltinSSLAdapter(https_config['certificate'],
                                                https_config['private_key'])
                server_https = CherryPyWSGIServer(bind_addr=bind_addr_https,
                                                  wsgi_app=wsgi_app)
                server_https.ssl_adapter = ssl_adapter
                ServerAdapter(cherrypy.engine, server_https).subscribe()
                logger.debug('WSGIServer starting... uid: %s, listen: %s:%s',
                             os.getuid(), bind_addr_https[0], bind_addr_https[1])
            except IOError as e:
                logger.warning("HTTPS server won't start: %s", e)
        else:
            logger.debug('HTTPS server is disabled')

        if http_config['enabled']:
            bind_addr_http = (http_config['host'], http_config['port'])
            server_http = CherryPyWSGIServer(bind_addr=bind_addr_http,
                                             wsgi_app=wsgi_app)
            ServerAdapter(cherrypy.engine, server_http).subscribe()
            logger.debug('WSGIServer starting... uid: %s, listen: %s:%s',
                         os.getuid(), bind_addr_http[0], bind_addr_http[1])
        else:
            logger.debug('HTTP server is disabled')

        if not http_config['enabled'] and not https_config['enabled']:
            logger.critical('No HTTP/HTTPS server enabled')
            exit()

        list_routes(self.app)

        try:
            cherrypy.engine.start()
            cherrypy.engine.block()
        except KeyboardInterrupt:
            cherrypy.engine.stop()


def _check_file_readable(file_path):
    with open(file_path, 'r'):
        pass


def list_routes(app):
    output = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        line = "{:50s} {:20s} {}".format(rule.endpoint, methods, rule)
        output.append(line)

    for line in sorted(output):
        logger.debug(line)
