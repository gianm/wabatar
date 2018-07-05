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
import argparse
import asyncio
import functools
import logging
import serial_asyncio
import urllib

from . import avatar
from . import web

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='An all new world awaits.')
  parser.add_argument('--debug', dest='debug', action='store_true')
  args = parser.parse_args()

  # Set up logging.
  log_level = 'DEBUG' if args.debug else 'INFO'
  logging.basicConfig(level=log_level)
  log = logging.getLogger(__name__)

  # FasTrack reporting.
  fastrack_ctr = [0]

  # This generates an error: UserWarning: Creating a client session outside of coroutine is a very dangerous idea
  # Should figure out how to do this better, then.
  fastrack_session = aiohttp.ClientSession()

  def fastrack_done_cb(ctr, future):
    try:
      r = future.result()
      log.debug('Sent message to fastrack (%s outstanding): %s', ctr[0], repr(r))
    except Exception as e:
      log.exception('Failed to send message to fastrack.')
    finally:
      ctr[0] = ctr[0] - 1

  def fastrack_send(ctr, sensors, setpoints):
    if ctr[0] > 100:
      log.warn('Skipping send to fastrack, too many queued.')
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
        log.debug('Sending message to fastrack: ' + url)
        task = asyncio.ensure_future(fastrack_session.get(url))
        ctr[0] = ctr[0] + 1
        task.add_done_callback(functools.partial(fastrack_done_cb, ctr))

      do_send('sensor', sensors['values'])
      do_send('setpoint', setpoints)

  # Set up Avatar callbacks.
  callbacks = []
  callbacks.append(lambda x, y: log.info("Sensors: %s (setpoints = %s)", repr(x), repr(y)))
  callbacks.append(functools.partial(fastrack_send, fastrack_ctr))

  # Set up asyncio.
  loop = asyncio.get_event_loop()

  avatar_obj = avatar.AvatarProtocol(callbacks)
  avatar_coro = serial_asyncio.create_serial_connection(loop, lambda: avatar_obj, '/dev/ttyUSB0', baudrate=9600)
  avatar_task = loop.run_until_complete(avatar_coro)

  web_handler = web.WabatarServer(avatar_obj).new_handler()
  web_task = loop.run_until_complete(loop.create_server(web_handler, '0.0.0.0', 8080))

  try:
    loop.run_forever()
  finally:
    web_task.close()
    loop.run_until_complete(fastrack_session.close())
    loop.run_until_complete(web_task.wait_closed())
    loop.close()
