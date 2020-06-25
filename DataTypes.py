import struct
import bitarray

class DataType:
    pattern = ""
    def __init__(self,value):
        self.value = value
    def setValue(self,value):
        self.value = value
    def pack(self):
        return struct.pack(f">{self.pattern}", self.value)
    def unpack(self, value):
        self.value = struct.unpack(f">{self.pattern}", value)
        return self.value

class Boolean(DataType):
    def pack(self):
        return b"\x01" if self.value else b"\x00"
    def unpack(self, value):
        self.value = b"\x01" == value
        return self.value
class Byte(DataType):
    pattern = "b"
class UnsingedByte(DataType):
    pattern = "B"
class Short(DataType):
    pattern = "h"
class UnsingedShort(DataType):
    pattern = "H"
class Int(DataType):
    pattern = "i"
class UnsingedInt(DataType):
    pattern = "I"
class Long(DataType):
    pattern = "l"
class UnsingedLong(DataType):
    pattern = "L"
class Float(DataType):
    pattern = "f"
class Double(DataType):
    pattern = "d"
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
        if len(oridinal) > 5:
            raise ValueError(f"{self.value} is out of the range of a VarInt")
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
        if len(oridinal) > 7:
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
        return VarInt(len(byte)).pack + byte
class Chat(String):
    pass
class Identifier(String):
    pass

              
