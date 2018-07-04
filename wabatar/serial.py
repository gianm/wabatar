import asyncio
import logging
import re
import time

class AvatarProtocol(asyncio.Protocol):
  def __init__(self, sensor_cb, setpoint_cb):
    self.log = logging.getLogger(__name__)

    # Buffer for text coming off the serial port.
    self.buffer = ''

    # Callbacks.
    self.sensor_callbacks = sensor_cb
    self.setpoint_callbacks = setpoint_cb

    # Current sensor values.
    self.sensors = {}

    # Current setpoint values.
    self.setpoints = {'time' : time.time()}

  # asyncio protocol function
  def connection_made(self, transport):
    self.transport = transport
    self.log.info('Serial port connected: %s', repr(transport))
    transport.serial.rts = False

    # Turn on data logging and poll setpoints.
    transport.write(b'DE=7\r\n')
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
            'temperature' : float(m.group(1)),
            'co2' : float(m.group(3)),
            'o2' : float(m.group(4)),
            'pressure' : float(m.group(5)),
          }

          for f in self.sensor_callbacks:
            try:
              f(self.sensors)
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
            self.setpoints = new_setpoints
            for f in self.setpoint_callbacks:
              try:
                f(new_setpoints)
              except Exception as e:
                self.log.exception('Error executing setpoint callback.')

          return

        # Some command we issued, echoed back.
        m = re.fullmatch(r'(DE0\=7-|SP[0234])', avatar_text)
        if m:
          return

        self.log.warn('Could not recognize data from serial port, ignoring: %s', avatar_text)
    except Exception as e:
      self.log.exception('Error reading from serial port.')
      self.transport.close()

  # asyncio protocol function
  def connection_lost(self, exc):
    self.log.info('Serial port disconnected.')
    self.transport.loop.stop()

  # Issue commands to poll setpoints.
  def poll_setpoints(self):
    self.transport.write(b'SP0\r\n')
    self.transport.write(b'SP2\r\n')
    self.transport.write(b'SP3\r\n')
    self.transport.write(b'SP4\r\n')

  # Merge two setpoint data structures: a is the old one and b is the new one.
  def merge_setpoints(self, a, b):
    m = a.copy()
    m.update(b.copy())
    m['time'] = a['time']
    if m is not a:
      m['time'] = b['time']
    return m
