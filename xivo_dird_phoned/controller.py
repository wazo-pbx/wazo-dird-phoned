# -*- coding: utf-8 -*-
#
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

import logging

from xivo_dird_phoned.auth import AuthClient
from xivo_dird_phoned.rest_api import RestApi
from xivo_dird_phoned.http import DirectoriesConfiguration

logger = logging.getLogger(__name__)


class Controller(object):
    def __init__(self, config):
        self.config = config
        self.rest_api = RestApi(self.config['rest_api'])
        self.rest_api.app.config['authorized_subnets'] = self.config['rest_api']['authorized_subnets']
        DirectoriesConfiguration(config['dird'])
        self.auth_client = AuthClient(config['auth'], self.rest_api.app.config)

    def run(self):
        logger.debug('xivo-dird-phoned running...')
        self.auth_client.renew_token()
        try:
            self.rest_api.run()
        finally:
            logger.info('xivo-dird-phoned stopping...')
            self.auth_client.stop()
