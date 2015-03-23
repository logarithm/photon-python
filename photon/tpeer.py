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

import threading
import traceback
from photon.basepeer import BasePeer
from photon.enums import ConnectionState, DebugLevel, StatusCode
from photon.operations import OperationRequest
from photon.protocol import serialize_op_request
from photon.support import SupportClass
from photon.tconnect import TConnect
from photon.utils import now_in_millis, print_array


class TPeer(BasePeer):
    def __init__(self, peer_listener=None):
        super().__init__(peer_listener)

        self._rt = None
        self.incoming_list = []
        self.incoming_list_lock = threading.Lock()
        self.outgoing_op_list = []

        self.last_ping_result = 0
        self.ping_request = bytearray([256 - 16, 0, 0, 0, 0])
        self.tcp_head = bytearray([256 - 5, 0, 0, 0, 0, 0, 0, 256 - 13, 2])
        self.message_head = self.tcp_head[:]

        super().init_once()

    def connect(self, host, port, app_id=None):
        if self._state != ConnectionState.Disconnected and self.debug_level >= DebugLevel.Warning:
            self.peer_listener.debug_return(DebugLevel.Warning,
                                            "Connect() can't be called if peer is not Disconnected. Not connecting.")

        if self.debug_level >= DebugLevel.All:
            self.peer_listener.debug_return(DebugLevel.All, "Connect()")

        self.init_peer()

        if app_id is None:
            app_id = "Lite"

        app_id_bytes = bytearray(app_id, 'utf-8')
        for i in range(32):
            self._INIT_BYTES[(i + 9)] = app_id_bytes[i] if i < len(app_id_bytes) else 0

        self._state = ConnectionState.Connecting

        self._rt = TConnect(self, host, port)
        if self._rt.start_connection() is not True:
            self._state = ConnectionState.Disconnected
            return False

        self.m_connectionTime = now_in_millis()

        self.enqueue_init()

        return True

    def disconnect(self):
        if self._state == ConnectionState.Disconnected or self._state == ConnectionState.Disconnecting:
            return

        if self.debug_level >= DebugLevel.All:
            self.peer_listener.debug_return(DebugLevel.All, "Disconnect()")

        self._state = ConnectionState.Disconnecting
        self.outgoing_op_list[:] = []

        self._rt.stop_connection()

    def stop_connection(self):
        self._rt.stop_connection()

    def init_peer(self):
        BasePeer.init_peer(self)

        self.incoming_list = []
        self.outgoing_op_list = []

    def enqueue_init(self):
        tcp_header = bytearray([256 - 5, 0, 0, 0, 0, 0, 1])

        SupportClass.int_to_byte_array(tcp_header, 1, len(self._INIT_BYTES) + len(tcp_header))

        message = bytearray(tcp_header + self._INIT_BYTES)

        self.enqueue_message_as_payload(True, message, 0)

    def enqueue_message_as_payload(self, reliable, op_message, channel_id):
        if op_message is None:
            return False

        op_message[5] = channel_id
        op_message[6] = 1 if reliable else 0

        self.outgoing_op_list.append(op_message)

        return True

    def enqueue_operation(self, op_code, params, reliable, channel_id, encrypt, message_type=2):
        if self._state != ConnectionState.Connected:
            if self.debug_level >= DebugLevel.Error:
                self.peer_listener.debug_return(DebugLevel.Error,
                                                "Cannot send op: {}. Not connected. PeerState: {}".format(
                                                    0xFF & op_code, self._state.name))
            self.peer_listener.on_status_changed(StatusCode.SendError)
            return False

        if channel_id > self.m_channelCount:
            if self.debug_level >= DebugLevel.Error:
                self.peer_listener.debug_return(DebugLevel.Error,
                                                "Cannot send op: Selected channel ({})>= channelCount ({})".format(
                                                    channel_id, self.m_channelCount))
            self.peer_listener.on_status_changed(StatusCode.SendError)
            return False

        op_bytes = self.serialize_operation_to_message(op_code, params, encrypt, message_type)
        return self.enqueue_message_as_payload(reliable, op_bytes, channel_id)

    def send_outgoing_commands(self):
        if self._state == ConnectionState.Disconnected:
            return False

        if not self._rt.is_running():
            return False

        if (self._state == ConnectionState.Connected) and (
                        self.get_local_ms_timestamp() - self.last_ping_result > self.m_time_ping_interval):
            self.send_ping()

        if len(self.outgoing_op_list) > 0:
            to_send = list(self.outgoing_op_list)
            self.outgoing_op_list[:] = []

            for data in to_send:
                self.send_data(data)

        return True

    def send_ping(self):
        time = self.get_local_ms_timestamp()
        SupportClass.int_to_byte_array(self.ping_request, 1, time)
        self.last_ping_result = self.get_local_ms_timestamp()

        self.send_data(self.ping_request)

    def send_data(self, data):
        try:
            self._rt.send_tcp(data)
        except Exception as e:
            if self.debug_level >= DebugLevel.Error:
                self.peer_listener.debug_return(DebugLevel.Error, e)

            traceback.print_exc()

    def dispatch_incoming_commands(self):
        with self._action_queue_lock:
            while len(self._action_queue) > 0:
                self._action_queue.pop(0)()

        with self.incoming_list_lock:
            if len(self.incoming_list) <= 0:
                return False

            payload = self.incoming_list.pop(0)

        return self.deserialize_message_and_callback(payload)

    def receive_incoming_commands(self, data):
        if data is None:
            if self.debug_level >= DebugLevel.Error:
                self.peer_listener.debug_return(DebugLevel.Error, "receive_incoming_commands() - data is None")

            return

        if data[0] == 256 - 13 or data[0] == 256 - 12:
            with self.incoming_list_lock:
                self.incoming_list.append(data)
                if len(self.incoming_list) % self.m_warningSize == 0:
                    self.enqueue_status_callback(StatusCode.QueueIncomingReliableWarning)
        elif data[0] == 256 - 16:
            self.read_ping_result(data)
        elif self.debug_level >= DebugLevel.Error:
            self.enqueue_debug_return(DebugLevel.Error,
                                      "receiveIncomingCommands() MagicNumber should be 0xF0, 0xF3 or 0xF4. Is: {:02x}"
                                      .format(data[0]))

    def read_ping_result(self, payload):
        server_sent_time = int.from_bytes(payload[1:5], "big")
        client_sent_time = int.from_bytes(payload[5:9], "big")

        self.m_lastRoundTripTime = (self.get_local_ms_timestamp() - client_sent_time)
        self.update_round_trip_time_and_variance(self.m_lastRoundTripTime)

    def serialize_operation_to_message(self, op_code, params, encrypt, message_type):
        op_request = OperationRequest(op_code, params)
        op_bytes = serialize_op_request(op_request)
        full_message = None

        if op_bytes is not None and len(op_bytes) > 0:
            if encrypt:
                pass
                # here encrypt data

            full_message = bytearray()
            full_message.extend(self.message_head)
            full_message.extend(op_bytes)

            SupportClass.int_to_byte_array(full_message, 1, len(full_message))
        else:
            if self.debug_level >= DebugLevel.Error:
                self.peer_listener.debug_return(DebugLevel.Error, "Error serializing operation! {}".format(op_request))

        return full_message
