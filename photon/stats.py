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

class TrafficStats:
    def __init__(self):
        self.packageHeaderSize = 0
        self.reliableCommandCount = 0
        self.unreliableCommandCount = 0
        self.fragmentCommandCount = 0
        self.controlCommandCount = 0
        self.totalPacketCount = 0
        self.totalCommandsInPackets = 0
        self.reliableCommandBytes = 0
        self.unreliableCommandBytes = 0
        self.fragmentCommandBytes = 0
        self.controlCommandBytes = 0

    def total_command_count(self):
        return self.reliableCommandCount + self.unreliableCommandCount + \
               self.fragmentCommandCount + self.controlCommandCount

    def total_command_bytes(self):
        return self.reliableCommandBytes + self.unreliableCommandBytes + \
               self.fragmentCommandBytes + self.controlCommandBytes

    def total_packet_bytes(self):
        return self.total_command_bytes() + self.totalPacketCount * self.packageHeaderSize

    def count_control_command(self, size):
        self.controlCommandBytes += size
        self.controlCommandCount += 1

    def count_reliable_op_command(self, size):
        self.reliableCommandBytes += size
        self.reliableCommandCount += 1

    def count_unreliable_op_command(self, size):
        self.unreliableCommandBytes += size
        self.unreliableCommandCount += 1

    def count_fragment_op_command(self, size):
        self.fragmentCommandBytes += size
        self.fragmentCommandCount += 1

    def __str__(self, *args, **kwargs):
        return "TotalPacketBytes: {}\nTotalCommandBytes: {}\nTotalPacketCount: {}\nTotalCommandsInPackets: {}" \
            .format(self.total_packet_bytes(), self.total_command_bytes(),
                    self.totalPacketCount, self.totalCommandsInPackets)