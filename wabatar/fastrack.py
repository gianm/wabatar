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

import aiohttp
import asyncio
import logging
import urllib

from . import avatar

class FastrackEmitter:
  def __init__(self):
    self.log = logging.getLogger(__name__)
    self.ctr = 0

  async def start(self):
    self.session = aiohttp.ClientSession()

  async def stop(self):
    await self.session.close()

  def emit_done_cb(self, future):
    try:
      r = future.result()
      self.log.debug('Sent message to fastrack (%s outstanding): %s', self.ctr, repr(r))
    except Exception as e:
      self.log.exception('Failed to send message to fastrack.')
    finally:
      self.ctr = self.ctr - 1

  def emit(self, sensors, setpoints):
    if self.ctr > 100:
      self.log.warn('Skipping send to fastrack, too many queued.')
    else:
      def do_send(kind, values):
        url = 'https://cc-int.imply.io/g/imply/ft.gif?' + urllib.parse.urlencode({
          'A' : 'FT-WABATAR',
          'D01' : kind,
          'M01' : values[avatar.IDX_TEMPERATURE] if len(values) > avatar.IDX_TEMPERATURE else 0,
          'M02' : values[avatar.IDX_CO2] if len(values) > avatar.IDX_CO2 else 0,
          'M03' : values[avatar.IDX_O2] if len(values) > avatar.IDX_O2 else 0,
          'M04' : values[avatar.IDX_PRESSURE] if len(values) > avatar.IDX_PRESSURE else 0,
          'M05' : values[avatar.IDX_RH] if len(values) > avatar.IDX_RH else 0,
        })
        self.log.debug('Sending message to fastrack: ' + url)
        task = asyncio.ensure_future(self.session.get(url))
        self.ctr = self.ctr + 1
        task.add_done_callback(self.emit_done_cb)

      do_send('sensor', sensors['values'])
      do_send('setpoint', setpoints)
