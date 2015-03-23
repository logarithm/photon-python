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


class PeerListener:
    def __init__(self):
        pass

    @abc.abstractmethod
    def debug_return(self, debug_level, message):
        pass

    @abc.abstractmethod
    def on_status_changed(self, status_code):
        pass

    @abc.abstractmethod
    def on_operation_response(self, operation_response):
        pass

    @abc.abstractmethod
    def on_event(self, event_data):
        pass