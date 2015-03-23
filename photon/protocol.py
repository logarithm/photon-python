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

import traceback
import struct
import array
from photon.operations import OperationRequest, OperationResponse, EventData
from photon.typeddict import typed_dict


def serialize_op_request(op_request):
    out = bytearray()

    _serialize_op_request(out, op_request, False)

    return out


def deserialize_event_data(buf):
    result = EventData()
    result.code = _deserialize_byte(buf)
    result.params = _deserialize_parameters(buf)

    return result


def deserialize_op_request(buf):
    result = OperationRequest()
    result.op_code = _deserialize_byte(buf)
    result.params = _deserialize_parameters(buf)

    return result


def deserialize_op_response(buf):
    result = OperationResponse()
    result.op_code = _deserialize_byte(buf)
    result.return_code = _deserialize_short(buf)
    result.debug_message = _deserialize(buf)
    result.params = _deserialize_parameters(buf)

    return result


# private methods


def _serialize(out, value, set_type):
    if value is None:
        out.append(42)
        return

    v_type = type(value)

    if str == v_type:
        _serialize_string(out, value, set_type)
    elif bool == v_type:
        _serialize_boolean(out, value, set_type)
    elif int == v_type:
        byte_cnt = (value.bit_length() + 7) // 8

        if byte_cnt == 1:
            _serialize_byte(out, value, set_type)
        elif byte_cnt == 2:
            _serialize_short(out, value, set_type)
        elif byte_cnt <= 4:
            _serialize_integer(out, value, set_type)
        elif byte_cnt <= 8:
            _serialize_long(out, value, set_type)
    elif float == v_type:
        _serialize_double(out, value, set_type)
    elif bytearray == v_type:
        _serialize_bytearray(out, value, set_type)
    elif array.array == v_type:
        _serialize_array(out, value, set_type)
    elif dict == v_type:
        _serialize_dict(out, value, set_type)
    elif typed_dict == v_type:
        _serialize_typed_dict(out, value, set_type)
    elif list == v_type:
        _serialize_list(out, value, set_type)
    elif OperationRequest == v_type:
        _serialize_op_request(out, value, set_type)
    elif OperationResponse == v_type:
        _serialize_op_response(out, value, set_type)
    elif EventData == v_type:
        _serialize_event_data(out, value, set_type)
    else:
        raise Exception("Cannot serialize value of type {}".format(v_type))


def _serialize_parameters(out, params):
    try:
        if params is None:
            params = {}

        _serialize_short(out, len(params), False)

        for key in params:
            _serialize_byte(out, key, False)
            _serialize(out, params[key], True)
    except:
        traceback.print_exc()


def _serialize_string(out, value, set_type):
    if set_type:
        out.extend(bytearray([115]))

    str_bytes = bytearray(value, "utf-8")
    _serialize_short(out, len(str_bytes), False)
    out.extend(str_bytes)


def _serialize_boolean(out, value, set_type):
    if set_type:
        out.extend(bytearray([111]))

    _serialize_byte(out, 1 if value is True else 0, False)


def _serialize_byte(out, value, set_type):
    if set_type:
        out.extend(bytearray([98]))

    value = ((value + ((1 << 7) - 1)) % (1 << 8)) - ((1 << 7) - 1)
    out.extend(struct.pack('>b', value))


def _serialize_short(out, value, set_type):
    if set_type:
        out.extend(bytearray([107]))

    value = ((value + ((1 << 15) - 1)) % (1 << 16)) - ((1 << 15) - 1)
    out.extend(struct.pack('>h', value))


def _serialize_integer(out, value, set_type):
    if set_type:
        out.extend(bytearray([105]))

    value = ((value + ((1 << 31) - 1)) % (1 << 32)) - ((1 << 31) - 1)
    out.extend(struct.pack('>i', value))


def _serialize_long(out, value, set_type):
    if set_type:
        out.extend(bytearray([108]))

    value = ((value + ((1 << 63) - 1)) % (1 << 64)) - ((1 << 63) - 1)
    out.extend(struct.pack('>q', value))


def _serialize_float(out, value, set_type):
    if set_type:
        out.extend(bytearray([102]))

    out.extend(struct.pack('>f', value))


def _serialize_double(out, value, set_type):
    if set_type:
        out.extend(bytearray([100]))

    out.extend(struct.pack('>d', value))


def _serialize_bytearray(out, value, set_type):
    if set_type:
        out.extend(bytearray([120]))

    _serialize_integer(out, len(value), False)
    out.extend(value)


def _serialize_array(out, value, set_type):
    if set_type:
        out.extend(bytearray([121]))

    _serialize_short(out, len(value), False)
    code = _get_code_for_array_typecode(value.typecode)
    func = _get_serialize_func_for_code(code)

    _serialize_byte(out, code, False)
    for val in value:
        func(out, val, False)


def _serialize_list(out, value, set_type):
    """
    Now we can serialize only not empty list of strings.
    For empty list please use None and for list of other type user array()
    """
    if len(value) == 0:
        raise ValueError("List must be not empty")

    if set_type:
        out.extend(bytearray([121]))

    _serialize_short(out, len(value), False)
    _serialize_byte(out, 115, False)

    for val in value:
        _serialize_string(out, val, False)


def _serialize_dict(out, value, set_type):
    if set_type:
        out.extend(bytearray([104]))

    _serialize_short(out, len(value), False)

    for key in value:
        if key is None:
            raise ValueError("None keys are now allowed for dict!")

        _serialize(out, key, True)
        _serialize(out, value[key], True)


def _serialize_typed_dict(out, value, set_type):
    if set_type:
        out.extend(bytearray([68]))

    if object == value.key_type:
        _serialize_byte(out, 0, False)
    else:
        _serialize_byte(out, _get_code_for_type(value.key_type), False)

    if object == value.value_type:
        _serialize_byte(out, 0, False)
    else:
        _serialize_byte(out, _get_code_for_type(value.value_type), False)

    _serialize_short(out, len(value), False)

    for key in value:
        if key is None:
            raise ValueError("None keys are now allowed for dict!")

        _serialize(out, key, object == value.key_type)

        if int is value.value_type:
            _serialize_integer(out, value[key], False)
        else:
            _serialize(out, value[key], object == value.value_type)


def _serialize_event_data(out, value, set_type):
    if set_type:
        out.extend(bytearray([101]))

    out.extend(bytearray([value.code]))
    _serialize_parameters(out, value.params)


def _serialize_op_request(out, value, set_type):
    if set_type:
        out.extend(bytearray([113]))

    out.extend(bytearray([value.op_code]))
    _serialize_parameters(out, value.params)


def _serialize_op_response(out, value, set_type):
    if set_type:
        out.extend(bytearray([112]))

    _serialize_byte(out, value.op_code, False)
    _serialize_short(out, value.return_code, False)

    if value.debug_message is None or len(value.debug_message) == 0:
        _serialize_byte(out, 42, False)
    else:
        _serialize_byte(out, 115, False)
        _serialize_string(out, value.debug_message, False)

    _serialize_parameters(out, value.params)


def _deserialize(buf, v_type=None):
    if v_type is None:
        v_type = _deserialize_byte(buf)

    if v_type == 0 or v_type == 42:
        return None
    elif v_type == 115:
        return _deserialize_string(buf)
    elif v_type == 111:
        return _deserialize_boolean(buf)
    elif v_type == 98:
        return _deserialize_byte(buf)
    elif v_type == 107:
        return _deserialize_short(buf)
    elif v_type == 105:
        return _deserialize_integer(buf)
    elif v_type == 108:
        return _deserialize_long(buf)
    elif v_type == 102:
        return _deserialize_float(buf)
    elif v_type == 100:
        return _deserialize_double(buf)
    elif v_type == 120:
        return _deserialize_bytearray(buf)
    elif v_type == 121:
        return _deserialize_array(buf)
    elif v_type == 104:
        return _deserialize_dict(buf)
    elif v_type == 68:
        return _deserialize_typed_dict(buf)
    elif v_type == 113:
        return deserialize_op_request(buf)
    elif v_type == 112:
        return deserialize_op_response(buf)
    elif v_type == 101:
        return deserialize_event_data(buf)
    else:
        raise Exception("Cannot serialize value of type {}".format(v_type))


def _deserialize_parameters(buf):
    params = {}

    length = _deserialize_short(buf)
    for i in range(length):
        key = _deserialize_byte(buf)
        value = _deserialize(buf)
        params[key] = value

    return params


def _deserialize_string(buf):
    length = _deserialize_short(buf)
    return _fetch_bytes(buf, length).decode("utf-8")


def _deserialize_boolean(buf):
    return _deserialize_byte(buf) == 1


def _deserialize_byte(buf):
    return struct.unpack('>b', _fetch_bytes(buf, 1))[0]


def _deserialize_short(buf):
    return struct.unpack('>h', _fetch_bytes(buf, 2))[0]


def _deserialize_integer(buf):
    return struct.unpack('>i', _fetch_bytes(buf, 4))[0]


def _deserialize_long(buf):
    return struct.unpack('>q', _fetch_bytes(buf, 8))[0]


def _deserialize_float(buf):
    return struct.unpack('>f', _fetch_bytes(buf, 4))[0]


def _deserialize_double(buf):
    return struct.unpack('>d', _fetch_bytes(buf, 8))[0]


def _deserialize_bytearray(buf):
    length = _deserialize_integer(buf)
    return _fetch_bytes(buf, length)


def _deserialize_array(buf):
    length = _deserialize_short(buf)
    code = _deserialize_byte(buf)

    if code == 115:
        result = []

        for i in range(length):
            result.append(_deserialize_string(buf))

        return result
    else:
        typecode = _get_array_typecode_for_code(code)
        func = _get_deserialize_func_for_code(code)

        result = array.array(typecode)
        for i in range(length):
            result.append(func(buf))

        return result


def _deserialize_dict(buf):
    length = _deserialize_short(buf)

    result = {}
    for i in range(length):
        result[_deserialize(buf)] = _deserialize(buf)

    return result


def _deserialize_typed_dict(buf):

    key_type_code = _deserialize_byte(buf)
    value_type_code = _deserialize_byte(buf)

    result = typed_dict(_get_type_for_code(key_type_code), _get_type_for_code(value_type_code))

    read_key_type = key_type_code == 0 or key_type_code == 42
    read_value_type = value_type_code == 0 or value_type_code == 42

    length = _deserialize_short(buf)
    for i in range(length):
        key = _deserialize(buf, None if read_key_type else key_type_code)
        value = _deserialize(buf, None if read_value_type else value_type_code)
        result[key] = value

    return result


def _get_serialize_func_for_code(code):
    if code is 115:
        return _serialize_string
    if code is 111:
        return _serialize_boolean
    if code is 98:
        return _serialize_byte
    if code is 107:
        return _serialize_short
    if code is 105:
        return _serialize_integer
    if code is 108:
        return _serialize_long
    if code is 102:
        return _serialize_float
    if code is 100:
        return _serialize_double
    if code is 120:
        return _serialize_bytearray
    if code is 121:
        return _serialize_array
    if code is 104:
        return _serialize_dict
    if code is 101:
        return _serialize_event_data
    if code is 113:
        return _serialize_op_request
    if code is 112:
        return _serialize_op_response
    else:
        raise Exception("Unknown code: {}".format(code))


def _get_deserialize_func_for_code(code):
    if code is 115:
        return _deserialize_string
    if code is 111:
        return _deserialize_boolean
    if code is 98:
        return _deserialize_byte
    if code is 107:
        return _deserialize_short
    if code is 105:
        return _deserialize_integer
    if code is 108:
        return _deserialize_long
    if code is 102:
        return _deserialize_float
    if code is 100:
        return _deserialize_double
    if code is 120:
        return _deserialize_bytearray
    if code is 121:
        return _deserialize_array
    if code is 104:
        return _deserialize_dict
    if code is 101:
        return deserialize_event_data
    if code is 113:
        return deserialize_op_request
    if code is 112:
        return deserialize_op_response
    else:
        raise Exception("Unknown code: {}".format(code))


def _get_code_for_array_typecode(typecode):
    if typecode is 'b' or typecode is 'B':
        return 98
    if typecode is 'h' or typecode is 'H':
        return 107
    if typecode is 'i' or typecode is 'I':
        return 105
    if typecode is 'l' or typecode is 'L':
        return 108
    if typecode is 'q' or typecode is 'Q':
        return 108
    if typecode is 'f':
        return 102
    if typecode is 'd':
        return 100
    else:
        raise Exception("Unknown typecode: {}".format(typecode))


def _get_array_typecode_for_code(code):
    if code is 98:
        return 'b'
    if code is 107:
        return 'h'
    if code is 105:
        return 'i'
    if code is 108:
        return 'q'
    if code is 102:
        return 'f'
    if code is 100:
        return 'd'
    else:
        raise Exception("Unknown code: {}".format(code))


def _get_code_for_type(v_type, value=None):
    if v_type is None:
        return 42
    elif str == v_type:
        return 115
    elif bool == v_type:
        return 111
    elif int == v_type:
        if value is None:
            return 105

        byte_cnt = (value.bit_length() + 7) // 8

        if byte_cnt == 1:
            return 98
        elif byte_cnt == 2:
            return 107
        elif byte_cnt <= 4:
            return 105
        elif byte_cnt <= 8:
            return 108
    elif float == v_type:
        return 100
    elif bytearray == v_type:
        return 120
    elif array.array == v_type:
        return 121
    elif dict == v_type:
        return 104
    elif typed_dict == v_type:
        return 68
    elif list == v_type:
        return 121
    elif OperationRequest == v_type:
        return 113
    elif OperationResponse == v_type:
        return 112
    elif EventData == v_type:
        return 101
    else:
        raise Exception("Cannot serialize value of type {}".format(v_type))


def _get_type_for_code(code):
    if code == 42 or code == 0:
        return object
    elif code == 115:
        return str
    elif code == 111:
        return bool
    elif code == 98 or code == 107 or code == 105 or code == 108:
        return int
    elif code == 102 or code == 100:
        return float
    elif code == 120:
        return bytearray
    elif code == 121:
        return array.array
    elif code == 104:
        return dict
    elif code == 68:
        return typed_dict
    elif code == 113:
        return OperationRequest
    elif code == 112:
        return OperationResponse
    elif code == 101:
        return EventData
    else:
        raise Exception("Cannot serialize value of type {}".format(v_type))


def _fetch_bytes(buf, count):
    res = buf[0:count]
    for i in range(0, count):
        buf.pop(0)

    return res