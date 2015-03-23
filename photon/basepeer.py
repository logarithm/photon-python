"""
Copyright 2015 Logvinenko Maksim

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import abc
import threading
from photon.enums import ConnectionState, DebugLevel, StatusCode
from photon.protocol import deserialize_op_response, deserialize_event_data
from photon.utils import now_in_millis


class BasePeer:
    def __init__(self, peer_listener):
        self.peer_listener = peer_listener

        self.debug_level = DebugLevel.Error
        self.traffic_stats_enabled = False

        self._state = ConnectionState.Disconnected

        self._INIT_BYTES = bytearray([0] * 41)

        self._action_queue = []
        self._action_queue_lock = threading.Lock()

        self.m_applicationIsInitialized = False

        self.m_connectionTime = 0

        self.m_roundTripTime = 0
        self.m_lastRoundTripTime = 0
        self.m_roundTripTimeVariance = 0
        self.m_lowestRoundTripTime = 0
        self.m_highestRoundTripTimeVariance = 0

        self.m_warningSize = 100
        self.m_time_ping_interval = 1000
        self.m_channelCount = 2

    def get_local_ms_timestamp(self):
        return now_in_millis() - self.m_connectionTime

    def enqueue_action_for_dispatch(self, action):
        with self._action_queue_lock:
            self._action_queue.append(action)

    def enqueue_debug_return(self, debug_level, message):
        with self._action_queue_lock:
            self._action_queue.append(
                lambda:
                self.peer_listener.debug_return(debug_level, message)
            )

    def enqueue_status_callback(self, status):
        with self._action_queue_lock:
            self._action_queue.append(
                lambda:
                self.peer_listener.on_status_changed(status)
            )

    @abc.abstractmethod
    def enqueue_operation(self, params, op_code, reliable, channel_id, encrypt, message_type=2):
        pass

    def init_once(self):
        self._INIT_BYTES[0] = 256 - 13
        self._INIT_BYTES[1] = 0
        self._INIT_BYTES[2] = 1
        self._INIT_BYTES[3] = 6
        self._INIT_BYTES[4] = 1
        self._INIT_BYTES[5] = 3
        self._INIT_BYTES[6] = 0
        self._INIT_BYTES[7] = 2
        self._INIT_BYTES[8] = 7

    def init_peer(self):
        self.m_connectionTime = 0
        self._state = ConnectionState.Disconnected

        self.m_applicationIsInitialized = False

    def init_callback(self):
        if self._state == ConnectionState.Connecting:
            self._state = ConnectionState.Connected

        self.m_applicationIsInitialized = True
        self.peer_listener.on_status_changed(StatusCode.Connect)

    def deserialize_message_and_callback(self, payload):
        if len(payload) < 2:
            if self.debug_level >= DebugLevel.Error:
                self.peer_listener.debug_return(DebugLevel.Error, "Incoming data too short! {}".format(len(payload)))
            return False

        if payload[0] != 256 - 13 and payload[1] != 256 - 3:
            if self.debug_level >= DebugLevel.Error:
                self.peer_listener.debug_return(DebugLevel.Error, "No regular operation message: {}".format(payload[0]))
            return False

        msg_type = payload[1] & 0x7F
        is_encrypted = (payload[1] & 0x80) > 0

        if msg_type != 1:
            try:
                if is_encrypted:
                    raise Exception("We don't supper encrypted connect yet")
                else:
                    payload = payload[2:]
            except Exception as e:
                if self.debug_level >= DebugLevel.Error:
                    self.peer_listener.debug_return(DebugLevel.Error, e)

                return False

        if msg_type == 3:
            self.peer_listener.on_operation_response(deserialize_op_response(payload))
        elif msg_type == 4:
            self.peer_listener.on_event(deserialize_event_data(payload))
        elif msg_type == 1:
            self.init_callback()
        elif msg_type == 7:
            print("Receive shared key")
        else:
            if self.debug_level >= DebugLevel.Error:
                self.enqueue_debug_return(DebugLevel.Error, "unexpected msgType {}".format(msg_type))

    @abc.abstractmethod
    def connect(self, host, port, app_id=None):
        pass

    @abc.abstractmethod
    def disconnect(self):
        pass

    @abc.abstractmethod
    def stop_connection(self):
        pass

    @abc.abstractmethod
    def send_outgoing_commands(self):
        pass

    @abc.abstractmethod
    def dispatch_incoming_commands(self):
        pass

    def update_round_trip_time_and_variance(self, last_round_trip_time):
        if last_round_trip_time < 0:
            return

        self.m_roundTripTimeVariance -= self.m_roundTripTimeVariance / 4
        if last_round_trip_time >= self.m_roundTripTime:
            self.m_roundTripTime += (last_round_trip_time - self.m_roundTripTime) / 8
            self.m_roundTripTimeVariance += (last_round_trip_time - self.m_roundTripTime) / 4
        else:
            self.m_roundTripTime += (last_round_trip_time - self.m_roundTripTime) / 8
            self.m_roundTripTimeVariance -= (last_round_trip_time - self.m_roundTripTime) / 4

        if self.m_roundTripTime < self.m_lowestRoundTripTime:
            self.m_lowestRoundTripTime = self.m_roundTripTime

        if self.m_roundTripTimeVariance > self.m_highestRoundTripTimeVariance:
            self.m_highestRoundTripTimeVariance = self.m_roundTripTimeVariance