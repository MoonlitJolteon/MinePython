import socket
import struct
import json
import time
from bitarray import bitarray

class DataType:
    pattern = ""
    def __init__(self,value):
        self.value = value
    def setValue(self,value):
        self.value = value
    def pack(self):
        return struct.pack(f">{self.pattern}", self.value)

class Boolean(DataType):
    def pack(self):
        return b"\x01" if self.value else b"\x00"
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
class String(DataType):
    def pack(self):
        byte = self.value.encode("utf-8")
        return VarInt(len(byte)).pack + byte
class Chat(String):
    pass
class Identifier(String):
    pass

def unpack_varint(sock):
    """ Unpack the varint """
    data = 0
    for i in range(5):
        ordinal = sock.recv(1)

        if len(ordinal) == 0:
            break

        byte = ord(ordinal)
        data |= (byte & 0x7F) << 7 * i

        if not byte & 0x80:
            break

    return data


def pack_varint(data):
    """ Pack the var int """
    ordinal = b''

    while True:
        byte = data & 0x7F
        data >>= 7
        ordinal += struct.pack('B', byte | (0x80 if data > 0 else 0))

        if data == 0:
            break

    return ordinal


def pack_data(data):
    """ Page the data """
    if type(data) is str:
        data = data.encode('utf8')
        return pack_varint(len(data)) + data
    elif type(data) is int:
        return struct.pack('H', data)
    elif type(data) is float:
        return struct.pack('L', int(data))
    else:
        return data


def send_data(connection, *args):
    """ Send the data on the connection """
    data = b''

    for arg in args:
        data += pack_data(arg)

    connection.send(pack_varint(len(data)) + data)

def read_fully(connection, extra_varint=False):
    """ Read the connection and return the bytes """
    packet_length = unpack_varint(connection)
    packet_id = unpack_varint(connection)
    byte = b''

    if extra_varint:
        # Packet contained netty header offset for this
        if packet_id > packet_length:
            unpack_varint(connection)

        extra_length = unpack_varint(connection)

        while len(byte) < extra_length:
            byte += connection.recv(extra_length)

    else:
        byte = connection.recv(packet_length)

    return byte

    # def get_status(self):
    #     """ Get the status response """
    #     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
    #         connection.settimeout(self._timeout)
    #         connection.connect((self._host, self._port))
    #
    #         # Send handshake + status request
    #         self._send_data(connection, b'\x00\x00', self._host, self._port, b'\x01')
    #         self._send_data(connection, b'\x00')
    #
    #         # Read response, offset for string length
    #         data = self._read_fully(connection, extra_varint=True)
    #
    #         # Send and read unix time
    #         self._send_data(connection, b'\x01', time.time() * 1000)
    #         unix = self._read_fully(connection)
    #
    #     # Load json and return
    #     response = json.loads(data.decode('utf8'))
    #     response['ping'] = int(time.time() * 1000) - struct.unpack('L', unix)[0]
    #
    #     return response
if __name__ == "__main__":
    a = 2147483647
    i = VarInt(a)
    print(i.pack())
    print(pack_varint(a))
