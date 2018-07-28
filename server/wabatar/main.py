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
import csv
import functools
import json
import logging
import serial_asyncio
import urllib

from . import avatar
from . import fastrack
from . import web

def status_to_list(name, status):
  return [name, status['sensors']['time']] + status['sensors']['values'] + [status['setpoints']['time']] + status['setpoints']['values']

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='An all new world awaits.')
  parser.add_argument('--debug', dest='debug', action='store_true')
  parser.add_argument('--config', '-c', dest='config', action='store', required=True)
  parser.add_argument('--log', dest='log', action='store')
  args = parser.parse_args()

  # Set up Python logging.
  log_level = 'DEBUG' if args.debug else 'INFO'
  logging.basicConfig(level=log_level)
  log = logging.getLogger(__name__)

  # Set up logging to a file, maybe.
  datafile = None
  if args.log:
    log.info("Logging to %s", args.log)
    datafile = open(args.log, 'a', 1)
    datawriter = csv.writer(datafile)

  # Load configuration file.
  log.debug('Loading configuration from[%s].', args.config)
  with open(args.config, 'r') as f:
    conf = json.loads(f.read())

  # Create asyncio loop, fastrack emitter, and Avatar handlers.
  loop = asyncio.get_event_loop()
  fastrack_emitter = fastrack.FastrackEmitter()
  loop.run_until_complete(fastrack_emitter.start())

  avatars = {}

  for avatar_conf in conf['avatars']:
    name = avatar_conf['name']

    if name in avatars:
      raise Error('Cannot have two Avatars with the same name: ' + str(avatar_conf['name']))

    callbacks = []
    callbacks.append(lambda x: log.debug("Status from[%s]: %s", name, repr(x)))
    callbacks.append(lambda x: datawriter.writerow(status_to_list(name, x)))
    callbacks.append(functools.partial(fastrack_emitter.emit, name))

    avatar_obj = avatar.AvatarProtocol(name, callbacks)
    avatar_coro = serial_asyncio.create_serial_connection(loop, lambda: avatar_obj, '/dev/ttyUSB0', baudrate=9600)
    avatar_task = loop.run_until_complete(avatar_coro)

    avatars[name] = avatar_obj

  # Create web server.
  web_handler = web.WabatarServer(avatars).new_handler()
  web_task = loop.run_until_complete(loop.create_server(web_handler, '0.0.0.0', 8080))

  try:
    loop.run_forever()
  finally:
    web_task.close()
    loop.run_until_complete(fastrack_emitter.stop())
    loop.run_until_complete(web_task.wait_closed())
    loop.close()

    if datafile:
      datafile.close()
