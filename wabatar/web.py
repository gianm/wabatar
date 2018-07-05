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
    self.app.router.add_route('GET', '/', self.get_root)
    self.app.router.add_route('GET', '/v1/status', self.get_status)
    self.app.router.add_route('POST', '/v1/setpoint', self.post_setpoint)

    self.log = logging.getLogger(__name__)
    self.avatars = avatars

  def new_handler(self):
    return self.app.make_handler()

  async def get_root(self, request):
    html = r'<html><head><title>WABATAR</title></head><body><div style="text-align: center"><h1>WABATAR</h1><table border="1" width="100%">'
    html += r'<tr><th>Avatar</th><th>Temperature (deg C)</th><th>O<sub>2</sub> (%)</th><th>CO<sub>2</sub> (%)</th><th>Pressure (psi above ambient)</th><th>Relative humidity (%)</th><th>Last update</th></tr>'

    for name, avatar in self.avatars.items():
      status = avatar.status()

      html += '<tr>'
      html += '<td>' + name + '</td>'

      for i in [0, 2, 3, 4, 5]:
        html += '<td>'
        html += str(status['sensors']['values'][i])
        html += '</td>'

      html += '<td>' + str(time.time() - status['sensors']['time']) + 's ago (sensors), ' + str(time.time() - status['setpoints']['time']) + 's ago (setpoints)</td>'
      html += '</tr>'

    html += r'</table></body></html>'

    return web.Response(body=html.encode(), headers={'Content-Type': 'text/html'})

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
