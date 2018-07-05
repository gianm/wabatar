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
import logging
import serial_asyncio
import urllib

from . import avatar
from . import fastrack
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
  fastrack_emitter = fastrack.FastrackEmitter()

  # Set up Avatar callbacks.
  callbacks = []
  callbacks.append(lambda x, y: log.info("Sensors: %s (setpoints = %s)", repr(x), repr(y)))
  callbacks.append(fastrack_emitter.emit)

  # Set up asyncio.
  loop = asyncio.get_event_loop()

  loop.run_until_complete(fastrack_emitter.start())

  avatar_obj = avatar.AvatarProtocol(callbacks)
  avatar_coro = serial_asyncio.create_serial_connection(loop, lambda: avatar_obj, '/dev/ttyUSB0', baudrate=9600)
  avatar_task = loop.run_until_complete(avatar_coro)

  web_handler = web.WabatarServer(avatar_obj).new_handler()
  web_task = loop.run_until_complete(loop.create_server(web_handler, '0.0.0.0', 8080))

  try:
    loop.run_forever()
  finally:
    web_task.close()
    loop.run_until_complete(fastrack_emitter.stop())
    loop.run_until_complete(web_task.wait_closed())
    loop.close()
