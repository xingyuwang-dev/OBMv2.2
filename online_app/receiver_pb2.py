# -*- coding: utf-8 -*-
"""Minimal protobuf-compatible messages for the OBM gRPC receiver service.

The original generated ``receiver_pb2.py`` was missing from the repository.
Both messages contain one string field with field number 1, so this module
implements the small subset of the generated API used by ``receiver_pb2_grpc``.
"""


def _encode_varint(value):
    data = bytearray()
    while value > 0x7F:
        data.append((value & 0x7F) | 0x80)
        value >>= 7
    data.append(value)
    return bytes(data)


def _decode_varint(data, index):
    shift = 0
    value = 0
    while True:
        if index >= len(data):
            raise ValueError("incomplete varint")
        byte = data[index]
        index += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, index
        shift += 7


class _StringMessage:
    FIELD_NAME = ""

    def __init__(self, **kwargs):
        setattr(self, self.FIELD_NAME, kwargs.get(self.FIELD_NAME, ""))

    def SerializeToString(self):
        value = getattr(self, self.FIELD_NAME).encode("utf-8")
        return b"\x0a" + _encode_varint(len(value)) + value

    @classmethod
    def FromString(cls, data):
        message = cls()
        index = 0
        while index < len(data):
            tag, index = _decode_varint(data, index)
            wire_type = tag & 0x07
            field_number = tag >> 3
            if wire_type != 2:
                raise ValueError("unsupported protobuf wire type")
            length, index = _decode_varint(data, index)
            value = data[index:index + length]
            index += length
            if field_number == 1:
                setattr(message, cls.FIELD_NAME, value.decode("utf-8"))
        return message


class send_parameters(_StringMessage):
    FIELD_NAME = "send_string"


class receive_parameter(_StringMessage):
    FIELD_NAME = "receive_string"
