import struct
import json


class DataType:
    pattern = ""
    length = 0

    def __init__(self, value=None):
        self.value = value

    def setValue(self, value):
        self.value = value

    def getValue(self):
        return self.value

    def pack(self):
        return struct.pack(f">{self.pattern}", self.value)

    def unpack(self, value):
        data = b""
        for i in range(self.length):
            data += bytes([value.pop(0)])
        self.value,  = struct.unpack(f">{self.pattern}", data)
        return self.value


class Boolean(DataType):
    def pack(self):
        return b"\x01" if self.value else b"\x00"

    def unpack(self, input):
        self.value = bytearray(b"\x01")[0] == input.pop(0)
        return self.value, input


class Byte(DataType):
    pattern = "b"
    length = 1


class UnsignedByte(DataType):
    pattern = "B"
    length = 1


class Short(DataType):
    pattern = "h"
    length = 2


class UnsignedShort(DataType):
    pattern = "H"
    length = 2


class Int(DataType):
    pattern = "i"
    length = 4


class UnsignedInt(DataType):
    pattern = "I"
    length = 4


class Long(DataType):
    pattern = "q"
    length = 8


class UnsignedLong(DataType):
    pattern = "Q"
    length = 8


class Float(DataType):
    pattern = "f"
    length = 4


class Double(DataType):
    pattern = "d"
    length = 8


class VarInt(DataType):
    def pack(self):
        data = self.value
        """ Pack the var int """
        ordinal = b''

        while True:
            byte = data & 0x7F
            data >>= 7
            ordinal += struct.pack('B', byte | (0x80 if data > 0 else 0))

            if data == 0:
                break
        if len(ordinal) > 5:
            raise ValueError(f"{self.value} is out of the range of a VarInt")
        return ordinal

    def unpack(self, input):
        """ Unpack the varint """
        CONTINUE_BIT = bytearray(b'\x80')
        SEGMENT_BITS = bytearray(b'\x7F')
        data = 0
        position = 0
        while True:
            ordinal = input.pop(0)
            byte = ordinal
            if (byte & CONTINUE_BIT[0]) == 0:
                break

            data |= (byte & SEGMENT_BITS[0]) << position
            position += 7

            if (position >= 32):
                raise Exception("VarInt too long!")

        self.value = data
        return data, input


class VarLong(DataType):
    def pack(self):
        data = self.value
        """ Pack the var int """
        ordinal = b''

        while True:
            byte = data & 0x7F
            data >>= 7
            ordinal += struct.pack('B', byte | (0x80 if data > 0 else 0))

            if data == 0:
                break
        if len(ordinal) > 7:
            raise ValueError(f"{self.value} is out of the range of a VarLong")
        return ordinal

    def unpack(self, value):
        """ Unpack the varint """
        data = 0
        for i in range(5):
            ordinal = value.pop(0)

            if len(ordinal) == 0:
                break

            byte = ord(ordinal)
            data |= (byte & 0x7F) << 7 * i

            if not byte & 0x80:
                break
        self.value = data
        return data


class String(DataType):
    def pack(self):
        byte = self.value.encode("utf-8")
        return VarInt(len(byte)).pack() + byte

    def unpack(self, value):
        leng, bytearray = VarInt().unpack(value)
        nex = b""
        for i in range(leng):
            nex += bytes([value.pop()])
        self.value = nex.decode("utf-8")[::-1]
        return self.value


class Json(DataType):
    def pack(self):
        string = json.dumps(self.value)
        return String(string).pack()

    def unpack(self):
        string = String().unpack(self.value)
        return json.loads(string)


class Chat(String):
    pass


class Identifier(String):
    pass
