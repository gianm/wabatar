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
import logging
import re
import time

# Sensor and setpoint indexes.
IDX_TEMPERATURE = 0
IDX_CO2 = 2
IDX_O2 = 3
IDX_PRESSURE = 4
IDX_RH = 5
SETPOINT_LEN = 6

class AvatarProtocol(asyncio.Protocol):
  def __init__(self, name, callbacks):
    self.log = logging.getLogger(__name__).getChild(name)
    self.name = name
    self.callbacks = callbacks

    # Buffer for text coming off the serial port.
    self.buffer = ''

    # Current sensor values.
    self.sensors = {}

    # Current setpoint values.
    self.setpoints = {'time' : time.time()}

    # Pending commands (see queue_command).
    # Useful since the Avatar gets confused if you issue too many commands at once.
    self.pending_commands = []

  # asyncio protocol function
  def connection_made(self, transport):
    self.transport = transport
    self.log.info('Serial port connected: %s', repr(transport))
    transport.serial.rts = False

    # Turn on data logging and poll setpoints.
    self.queue_command('DE=7')
    self.poll_setpoints()

  # asyncio protocol function
  def data_received(self, data):
    try:
      self.buffer += data.decode('utf-8', 'replace')
      nl_index = self.buffer.find("\r\n")
      while nl_index > -1:
        avatar_text = self.buffer[0:nl_index].strip()
        self.log.debug("Received text: %s", avatar_text)
        self.buffer = self.buffer[(nl_index + 2):]
        nl_index = self.buffer.find("\r\n")

        # Try to interpret the avatar_text somehow.

        # Data log line.
        m = re.fullmatch(r'([\d\.]+)\S?\s+(00)\s+([\d\.]+)\S?\s+([\d\.]+)\S?\s+([\d\.]+)\S?\s+([\d\.]+)\S?', avatar_text)
        if m:
          # I don't know what 2 and 6 are.
          self.sensors = {
            'time' : time.time(),
            'values' : [float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4)), float(m.group(5)), float(m.group(6))]
          }

          for f in self.callbacks:
            try:
              f(self.status())
            except Exception as e:
              self.log.exception('Error executing sensor callback.')

          return

        # Setpoint values being reported.
        m = re.fullmatch(r'SP([0234])=([\d\.]+)\S?', avatar_text)
        if m:
          setpoint_id = int(m.group(1))
          setpoint_value = float(m.group(2))

          new_setpoints = self.merge_setpoints(self.setpoints, { 'time' : time.time(), setpoint_id : setpoint_value })

          if self.setpoints != new_setpoints:
            self.log.info("New setpoints: %s", new_setpoints)
            self.setpoints = new_setpoints

          # Setpoint values are written by the Avatar in response to our request for them, so we should
          # issue the next command.
          self.received_command_response(avatar_text)

          return

        # Some command we issued, echoed back.
        m = re.fullmatch(r'(DE0\=7-|SP[0234])', avatar_text)
        if m:
          self.received_command_response(avatar_text)
          return

        self.log.warn('Could not recognize data from serial port, ignoring: %s', avatar_text)
    except Exception as e:
      self.log.exception('Error reading from serial port.')
      self.transport.close()

  # asyncio protocol function
  def connection_lost(self, exc):
    self.log.info('Serial port disconnected.')
    self.transport.loop.stop()

  def queue_command(self, command):
    command_bytes = command.encode() + b'\r\n'
    if self.pending_commands:
      self.log.debug("Queued command: " + command)
      self.pending_commands.append(command_bytes)
    else:
      self.log.debug("Writing command immediately: " + command)
      self.pending_commands.append(command_bytes)
      self.transport.write(command_bytes)

  def received_command_response(self, avatar_text):
    if self.pending_commands:
      del self.pending_commands[0]

      if self.pending_commands:
        next_command = self.pending_commands[0]
        self.log.debug("Writing queued command: %s (%s left)", next_command.decode().strip(), str(len(self.pending_commands)))
        self.transport.write(next_command)
    else:
      self.log.warn("Got response to command I didn't issue, ignoring: %s", avatar_text)

  # Issue commands to poll setpoints.
  def poll_setpoints(self):
    self.queue_command('SP0')
    self.queue_command('SP2')
    self.queue_command('SP3')
    self.queue_command('SP4')

  # Write a new setpoint.
  def write_setpoint(self, index, value):
    self.queue_command('SP' + str(int(index)) + '=' + str(float(value)))

  # Merge two setpoint data structures: a is the old one and b is the new one.
  def merge_setpoints(self, a, b):
    m = a.copy()
    m.update(b)
    m['time'] = a['time']
    if m != a:
      m['time'] = b['time']
    return m

  def status(self):
    # Make setpoints look like sensors, for consistency.
    return {
      'name' : self.name,
      'sensors' : self.sensors,
      'setpoints' : { 'time' : self.setpoints['time'], 'values' : [self.setpoints.get(i, 0) for i in range(0, SETPOINT_LEN)] }
    }
