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

import struct


class SupportClass:
    def __init__(self):
        pass

    @staticmethod
    def short_to_byte_array(buf, index, number):
        number = ((number + (pow(2, 15) - 1)) % pow(2, 16)) - (pow(2, 15) - 1)
        for byte in struct.pack('>h', number):
            buf[index] = byte
            index += 1

    @staticmethod
    def int_to_byte_array(buf, index, number):
        number = ((number + (pow(2, 31) - 1)) % pow(2, 32)) - (pow(2, 31) - 1)
        for byte in struct.pack('>i', number):
            buf[index] = byte
            index += 1

    @staticmethod
    def long_to_byte_array(buf, index, number):
        number = ((number + (pow(2, 63) - 1)) % pow(2, 64)) - (pow(2, 63) - 1)
        for byte in struct.pack('>l', number):
            buf[index] = byte
            index += 1