import random
import socket
import time

from DataTypes import *
import packet_handling
import json
import threading
from faker import Faker

fake = Faker()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server = ''
port = 25565

server_ip = socket.gethostbyname(server)

try:
    s.bind((server, port))
    print(f'[INIT] Server bound to port: {port}')
except socket.error as e:
    print(str(e))

s.listen(1)


class threadedClient(threading.Thread):
    def __init__(self, conn, addr):
        threading.Thread.__init__(self)
        self.debug = False

        self.conn = conn
        self.addr = addr
        self.state = 0
        self.last_time = 0
        self.data_len = None
        self.packet = None
        self.packet_id = None
        self.packet_type = None
        self.data = None
        self.packet_types = {
            0: {
                0: "Handshake",
                1: "Legacy"
            },
            1: {
                0: "Status Request",
                1: "Status Ping"
            },
            2: {
                0: "Login Start",
                1: "Encryption Response",
                2: "Login Plugin Response"
            },
            3: {
                4: "Client Status",
                15: "Keep Alive"
            }
        }
        self.state_types = {
            0: "Handshaking",
            1: "Status",
            2: "Login",
            3: "Play"
        }
        self.joined = False

    def run(self):
        while True:
            response = self._read_packet()

            if response == -1:
                print(f'[CONNECTION CLOSED] {addr} disconnected.')
                conn.close()
                break

            elif response == -2:
                print("[ERROR] Legacy Ping.. We made booboo")
                self.conn.close()
                print(f'[CONNECTION CLOSED] {addr} disconnected.')
                break

            if self.debug:
                print(f'[CURRENT STATE] {self._get_state_type()}')
                print(f'[DATA RAW] {self.addr}: {self.packet}')
                print(f'[DATA LENGTH] {self.data_len}')
                print(f'[PACKET TYPE] {self.packet_id}: {self.packet_type}')
                print(f'[DATA CONTENT] {self.data}')

            if self._get_state_type() == "Handshaking":
                result = self._handle_handshake()
                if result == -3:
                    self.conn.close()
                    print(f'[INVALID STATE] {addr} disconnected due to invalid state.')
                    break
            elif self._get_state_type() == "Status":
                self._handle_status()
            elif self._get_state_type() == "Login":
                self._handle_logon()
            elif self._get_state_type() == "Play":
                self._handle_play()

    def _get_packet_type(self):
        return self.packet_types.get(self.state).get(self.packet_id)

    def _get_state_type(self):
        return self.state_types.get(self.state)

    def _read_packet(self):

        self.data_len = packet_handling.unpack_varint(self.conn)
        self.packet_id = packet_handling.unpack_varint(self.conn)
        self.packet_type = self._get_packet_type()

        if self.data_len >= 2:
            self.data = self.conn.recv(self.data_len - 1)

        self.packet = self.data_len.to_bytes(1, 'little') + self.packet_id.to_bytes(1, 'little') + self.data
        if not self.data_len:
            return -1
        elif self.data_len == b'\xfe':  # and self.packet_id == b'\x01'
            return -2

    def _handle_keep_alive(self):
        if time.time() > self.last_time and self.state == 3:
            # pass
            self.last_time = time.time()
            print(f'[HEARTBEAT] Sending Keep Alive to {self.addr}')
            packet_handling.send_data(self.conn, b'\x21', random.randint(0, 100000).to_bytes(4, 'little'))

    def _handle_handshake(self):
        self.state = self.data[-1]
        print(f'[NEW STATE] {self.addr} State: {self._get_state_type()}, ID: {self.state}')
        if self.state not in [0, 1, 2, 3]:
            self.state = 0
            return -3

    def _handle_status(self):

        ##########################
        # Status Ping Processing #
        ##########################

        if self.packet_type == "Status Request":
            demoJSON = {
                "version": {
                    "name": "MinePython 1.12.2",
                    "protocol": 340
                },
                "players": {
                    "max": 20,
                    "online": 1,
                    "sample": [
                        {
                            "name": "MoonlitJolty",
                            "id": "21a3feda-3387-440d-85b7-fc08038aa307"
                        }
                    ]
                },
                "description": {
                    "text": "Hello world!"
                }
            }

            msg = b'\x00' + Json(demoJSON).pack()
            msg = VarInt(len(msg)).pack() + msg
            self.conn.send(msg)

        elif self.packet_type == 'Status Ping':
            # print(f'[PING] {data}')
            self.conn.send(self.packet)
        else:
            print(f'[UNKNOWN/UNHANDLED PACKET] State: {self._get_state_name()}, Packet ID: {self.packet_id}, Packet '
                  f'Type: {self.packet_type}, Packet Data: {self.data}')

    def _handle_logon(self):

        ##############################
        # Login Processing (offline) #
        ##############################

        if self.packet_type == 'Login Start':
            username = self.data.decode()
            print(f'[LOGIN START] {username}')

            Faker.seed(username)
            uuid = fake.uuid4()

            msg = b'\02' + String(uuid).pack() + String(username).pack()

            msg = VarInt(len(msg)).pack() + msg

            print(f'[LOGIN SUCCESSFUL] {username} - {uuid}')

            self.conn.send(msg)
            self.state = 3

            msg = b'\x26' + Int(1).pack() + UnsignedByte(1).pack() + Int(0).pack() + Long(12345678).pack()
            msg += UnsignedByte(0).pack() + String("default").pack() + VarInt(16).pack()
            msg += Boolean(False).pack() + Boolean(True).pack()

            msg = VarInt(len(msg)).pack() + msg
            print(f'[JOIN PACKET] {addr} {msg}')

            self.conn.send(msg)

        elif self.packet_type == 'Encryption Response':
            pass

        elif self.packet_type == 'Login Plugin Response':
            pass

        ################################
        # Unexpected Packet Processing #
        ################################

        else:
            print(
                f'[UNKNOWN/UNHANDLED PACKET] State: {self._get_state_name()}, Packet ID: {self.packet_id}, Packet Type: {self.packet_type}, Packet Data: {self.data}')

    def _handle_play(self):
        if not self.joined:
            self.conn.send(b'\x15\x23\x00\x00\x0a\x4d\x00\x00\x00\x00\x00\x01\x14\x07\x64\x65'
                           b'\x66\x61\x75\x6c\x74\x00')
            self.joined = True
        else:
            self._handle_keep_alive()


while True:
    conn, addr = s.accept()
    print(f'[INCOMING CONNECTION] {addr}')

    thread = threadedClient(conn, addr)
    thread.start()
