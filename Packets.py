from DataTypes import *
from collections import OrderedDict

class Packet:
    form = OrderedDict()
    packetId = VarInt(0)
    def __init__(self):
        self.data = OrderedDict()
        for key, value in self.form.items():
            self.data[key] = value()
    def __getitem__(self, key):
        return self.data[key].value
    def __setitem__(self, key, value):
        self.data[key].value = value
    def __dir__(self):
        return list(self.form.keys())
    def pack(self):
        output = b""
        for item in data:
            output += item.pack()
        output = self.packetId.pack() + output
        leng = VarInt(len(output))
        output = leng.pack() + output
        return output
    def unpack(self, data):
        for item in self.data:
            item.unpack(data)
class HandShake:
    form = OrderedDict([("Protocol Version",VarInt), ("Server Address",String), ("Server Port", UnsingedShort), ("Next State",VarInt)])
    packetId = VarInt(0)
