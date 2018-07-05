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

from aiohttp import web

class WabatarServer:
  def __init__(self, avatars):
    self.app = web.Application()
    self.app.router.add_route('GET', '/', self.get_root)
    self.app.router.add_route('GET', '/v1/status', self.get_status)
    self.app.router.add_route('POST', '/v1/setpoint', self.post_setpoint)

    self.log = logging.getLogger(__name__)
    self.avatars = avatars

  def new_handler(self):
    return self.app.make_handler()

  async def get_root(self, request):
    return web.Response(body=r'<html><head><title>WABATAR</title></head><body><div style="text-align: center"><img src="https://user-images.githubusercontent.com/1214075/42293069-2117eb7c-7f8c-11e8-9264-277f6dab0492.jpg" style="width:80%" /></div></body></html>'.encode(), headers={'Content-Type': 'text/html'})

  async def get_status(self, request):
    statuses = {}
    for name, avatar in self.avatars.items():
      statuses[name] = avatar.status()
    return web.Response(body=json.dumps(statuses).encode(), headers={'Content-Type': 'application/json'})

  async def post_setpoint(self, request):
    request_obj = await request.json()
    self.avatars[request_obj['name']].write_setpoint(int(request_obj['index']), float(request_obj['value']))
    self.avatars[request_obj['name']].poll_setpoints()
    return web.Response(body=json.dumps({'ok' : True}).encode(), headers={'Content-Type': 'application/json'})
