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

from enum import IntEnum


class ConnectionProtocol(IntEnum):
    Udp = 0
    Tcp = 1


class ConnectionState(IntEnum):
    Disconnected = 0
    Connecting = 1
    Connected = 3
    Disconnecting = 4
    AcknowledgingDisconnect = 5
    Zombie = 6


class DebugLevel(IntEnum):
    Off = 0
    Error = 1
    Warning = 2
    Info = 3
    All = 5


class StatusCode(IntEnum):
    Connect = 1024
    Disconnect = 1025
    Exception = 1026
    ExceptionOnConnect = 1023
    QueueOutgoingReliableWarning = 1027
    QueueOutgoingReliableError = 1028
    QueueOutgoingUnreliableWarning = 1029
    SendError = 1030
    QueueOutgoingAcksWarning = 1031
    QueueIncomingReliableWarning = 1033
    QueueIncomingUnreliableWarning = 1035
    QueueSentWarning = 1037
    InternalReceiveException = 1039
    TimeoutDisconnect = 1040
    DisconnectByServer = 1041
    DisconnectByServerUserLimit = 1042
    DisconnectByServerLogic = 1043
    TcpRouterResponseOk = 1044
    TcpRouterResponseNodeIdUnknown = 1045
    TcpRouterResponseEndpointUnknown = 1046
    TcpRouterResponseNodeNotReady = 1047
    EncryptionEstablished = 1048
    EncryptionFailedToEstablish = 1049