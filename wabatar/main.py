import aiohttp
import argparse
import asyncio
import functools
import logging
import serial_asyncio
import urllib

from . import serial

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

  # This generates an error: ERROR:asyncio:Creating a client session outside of coroutine, but seems to work anyway.
  # Should figure out how to do this better, then.
  fastrack_session = aiohttp.ClientSession()

  def fastrack_done_cb(ctr, future):
    try:
      r = future.result()
      log.info('Sent message to fastrack (%s outstanding): %s', ctr[0], repr(r))
    except Exception as e:
      log.exception('Failed to send message to fastrack.')
    finally:
      ctr[0] = ctr[0] - 1

  def fastrack_send(ctr, sensors):
    if ctr[0] > 20:
      log.warn('Skipping send to fastrack, too many queued.')
    else:
      url = 'https://cc-int.imply.io/g/imply/ft.gif?' + urllib.parse.urlencode({
        'A' : 'FT-WABATAR',
        'M01' : sensors['temperature'],
        'M02' : sensors['co2'],
        'M03' : sensors['o2'],
        'M04' : sensors['pressure']
      })
      log.info('Sending message to fastrack: ' + url)
      task = asyncio.ensure_future(fastrack_session.get(url))
      ctr[0] = ctr[0] + 1
      task.add_done_callback(functools.partial(fastrack_done_cb, ctr))

  # Set up sensor and setpoint callbacks.
  sensor_callbacks = []
  setpoint_callbacks = []

  sensor_callbacks.append(lambda x: print("Sensors: " + repr(x)))
  sensor_callbacks.append(functools.partial(fastrack_send, fastrack_ctr))

  setpoint_callbacks.append(lambda x: print("Setpoints: " + repr(x)))

  # Set up asyncio.
  loop = asyncio.get_event_loop()
  coro = serial_asyncio.create_serial_connection(loop, lambda: serial.AvatarProtocol(sensor_callbacks, setpoint_callbacks), '/dev/ttyUSB0', baudrate=9600)
  loop.run_until_complete(coro)
  loop.run_forever()
  loop.close()
