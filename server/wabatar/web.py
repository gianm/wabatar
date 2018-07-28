# Copyright 2018 Gian Merlino
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import aiohttp
import json
import logging
import time

from aiohttp import web

class WabatarServer:
  def __init__(self, avatars):
    self.app = web.Application()
    self.app.router.add_route('GET', '/v1/status', self.get_status)
    self.app.router.add_route('POST', '/v1/setpoint', self.post_setpoint)
    self.app.router.add_static('/', '../app/build')

    self.log = logging.getLogger(__name__)
    self.avatars = avatars

  def new_handler(self):
    return self.app.make_handler()

  async def get_status(self, request):
    statuses = []
    for name in sorted(self.avatars.keys()):
      statuses.append(self.avatars[name].status())

    return web.Response(body=json.dumps(statuses).encode(), headers={'Content-Type': 'application/json'})

  async def post_setpoint(self, request):
    request_obj = await request.json()
    self.avatars[request_obj['name']].write_setpoint(int(request_obj['index']), float(request_obj['value']))
    self.avatars[request_obj['name']].poll_setpoints()
    return web.Response(body=json.dumps({'ok' : True}).encode(), headers={'Content-Type': 'application/json'})
