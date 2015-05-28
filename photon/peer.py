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
from photon import tpeer
from photon.enums import ConnectionProtocol


class PhotonPeer:
    def __init__(self, protocol, peer_listener=None):
        self.send_lock = threading.Lock()
        self.dispatch_lock = threading.Lock()
        self.enqueue_lock = threading.Lock()

        if protocol == ConnectionProtocol.Tcp:
            self.basePeer = tpeer.TPeer(peer_listener)
        else:
            raise Exception("Support only TCP protocol")

    def connect(self, host, port, app_id=None):
        with self.dispatch_lock:
            with self.send_lock:
                return self.basePeer.connect(host, port, app_id)

    def disconnect(self):
        with self.dispatch_lock:
            with self.send_lock:
                self.basePeer.disconnect()

    def stop_thread(self):
        with self.dispatch_lock:
            with self.send_lock:
                self.basePeer.stop_connection()

    def set_listener(self, peer_listener):
        self.basePeer._peer_listener = peer_listener

    def set_debug_level(self, debug_level):
        self.basePeer.debug_level = debug_level

    def service(self):
        while self.dispatch_incoming_commands():
            pass

        self.send_outgoing_commands()

    def send_outgoing_commands(self):
        with self.send_lock:
            return self.basePeer.send_outgoing_commands()

    def dispatch_incoming_commands(self):
        with self.dispatch_lock:
            return self.basePeer.dispatch_incoming_commands()

    def op_custom(self, op_code, params, reliable, channel_id=0):
        with self.enqueue_lock:
            return self.basePeer.enqueue_operation(op_code, params, reliable, channel_id, False)
