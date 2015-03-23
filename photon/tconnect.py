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

from _socket import timeout
import socket
import threading
import traceback
from photon.enums import DebugLevel, StatusCode
from photon.utils import print_array


class TConnect:
    def __init__(self, pp, host, port):
        self.pp = pp
        self.host = host
        self.port = port

        self.connection = None
        self.is_connected = False
        self.connection_thread = None

        self.obsolete = False

    def is_running(self):
        return (self.connection_thread is not None) and self.is_connected

    def start_connection(self):

        try:
            self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except Exception as e:
            if self.pp.debug_level >= DebugLevel.Error:
                self.pp.peer_listener.debug_return(DebugLevel.ERROR, e)
            self.pp.peer_listener.on_status_changed(StatusCode.ExceptionOnConnect)
            self.pp.peer_listener.on_status_changed(StatusCode.Disconnect)

            self.stop_connection()
            return False

        self.obsolete = False
        self.is_connected = False
        self.connection_thread = threading.Thread(target=self.connection_thread_run)
        self.connection_thread.start()

        return True

    def send_tcp(self, data):
        if self.obsolete:
            if self.pp.debug_level >= DebugLevel.Info:
                self.pp.peer_listener.debug_return(DebugLevel.Info,
                                                   "Sending was skipped because connection is obsolete.")

            return

        try:
            self.connection.send(data)
        except Exception as e:
            if not self.obsolete:
                self.obsolete = True

            if self.pp.debug_level >= DebugLevel.Error:
                self.pp.enqueue_debug_return(DebugLevel.Error,
                                             "TCP send failed. Exception: " + e)

            traceback.print_exc()

    def stop_connection(self):
        if self.connection_thread is not None:
            self.obsolete = True
            self.connection.close()
            self.connection_thread.join()

    def connection_thread_run(self):
        self.connection.connect((self.host, self.port))

        self.is_connected = True

        while self.obsolete is False:
            try:
                bytes_read = 0
                to_read = 9
                in_buff = bytearray([0] * 9)
                buff_pointer = memoryview(in_buff)

                while to_read:
                    nbytes = self.connection.recv_into(buff_pointer, to_read)
                    buff_pointer = buff_pointer[nbytes:]
                    to_read -= nbytes
                    bytes_read += nbytes

                if bytes_read >= 9:
                    op_collection = bytearray()

                    if in_buff[0] == 256 - 16:
                        self.pp.receive_incoming_commands(in_buff)
                    else:
                        length1 = 0xFF & in_buff[1]
                        length2 = 0xFF & in_buff[2]
                        length3 = 0xFF & in_buff[3]
                        length4 = 0xFF & in_buff[4]

                        length = length1 << 24 | length2 << 16 | length3 << 8 | length4

                        if self.pp.debug_level >= DebugLevel.All:
                            self.pp.enqueue_debug_return(DebugLevel.All, "message length: {}".format(length))

                        op_collection.extend(in_buff[7:])

                        bytes_read = 0
                        length -= 9
                        to_read = length
                        in_buff = bytearray([0] * length)
                        buff_pointer = memoryview(in_buff)

                        while to_read:
                            nbytes = self.connection.recv_into(buff_pointer, to_read)
                            buff_pointer = buff_pointer[nbytes:]
                            to_read -= nbytes
                            bytes_read += nbytes

                        op_collection.extend(in_buff[0:bytes_read])

                        if len(op_collection):
                            self.pp.receive_incoming_commands(op_collection)
            except timeout:
                if (not self.obsolete) and (self.pp.debug_level >= DebugLevel.All):
                    self.pp.enqueue_debug_return(DebugLevel.ALL, "TCP Receive timeout. All ok, just wait again.")
            except OSError as e:
                if not self.obsolete:
                    self.obsolete = True

                    if self.pp.debug_level >= DebugLevel.Error:
                        self.pp.enqueue_debug_return(DebugLevel.Error,
                                                     "Receiving failed. SocketException: {}".format(e))

        self.is_connected = False
        self.connection.close()