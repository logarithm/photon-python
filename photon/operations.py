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

class OperationRequest:
    def __init__(self, op_code=None, params=None):
        self.op_code = op_code
        self.params = params

    def __str__(self):
        return "OperationRequest {}: {}".format(self.op_code, self.params)


class OperationResponse:
    def __init__(self, op_code=None, return_code=None, debug_message=None, params=None):
        self.op_code = op_code
        self.return_code = return_code
        self.debug_message = debug_message
        self.params = params

    def __str__(self):
        return "OperationResponse {}: ReturnCode: {} ({}). Parameters: {}" \
            .format(self.op_code, self.return_code, self.debug_message, self.params)


class EventData:
    def __init__(self, code=None, params=None):
        self.code = code
        self.params = params

    def __str__(self):
        return "Event {}: {}".format(self.code, self.params)