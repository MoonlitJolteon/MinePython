import random
import socket
from time import sleep
from timeit import default_timer as timer

from DataTypes import *
import packet_handling
import json
import threading
from faker import Faker
import uuid
import io
import sys


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
        self.script = ""
        self.debug = False
        self.ticks = 0
        self.conn = conn
        self.addr = addr
        self.state = 0
        self.last_state = 0
        self.loaded_in = False
        self.disconnected = False
        self.heartbeat_started = False
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
                3: "Chat",
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

            if self.disconnected:
                print(f'[CONNECTION CLOSED] {addr} disconnected.')
                conn.close()
                break

            response = self._read_packet()
            if self.state != self.last_state:
                print(f'[NEW STATE] {self.addr} State: {self._get_state_type()}, ID: {self.state}')

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
                disconnected = self._handle_play()
                if disconnected:
                    sleep(5)
                    self.conn.close()
                    break

            self.last_state = self.state

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
        if not self.heartbeat_started:
            self.heartbeat_started = True
            # print(f'[HEARTBEAT] Sending Keep Alive to {self.addr}')
            msg = b"\x21" + Long(1).pack()
            msg = VarInt(len(msg)).pack() + msg
            self.conn.send(msg)
        else:
            if self.packet_type == "Keep Alive":
                heartbeatID = (Long().unpack(bytearray(self.data)) + 1) % 1000000000000
                # print(f"HeartbeatID: {heartbeatID}")
                msg = b"\x21" + Long(heartbeatID).pack()
                msg = VarInt(len(msg)).pack() + msg
                # print(f'[HEARTBEAT] Sending Keep Alive to {self.addr}')
                self.conn.send(msg)
    
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
                    "name": "MinePython 1.15.2",
                    "protocol": 578
                },
                "players": {
                    "max": 20,
                    "online": 1,
                    "sample": [
                        {
                            "name": "Test Player",
                            "id": "21a3feda-3387-440d-85b7-fc08038aa307"
                        }
                    ]
                },
                "description": {
                    "text": "\u00A75Hello world!"
                }
            }

            msg = b'\x00' + Json(demoJSON).pack()
            msg = VarInt(len(msg)).pack() + msg
            self.conn.send(msg)

        elif self.packet_type == 'Status Ping':
            # print(f'[PING] {data}')
            self.conn.send(self.packet)
        else:
            print(f'[UNKNOWN/UNHANDLED PACKET] State: {self._get_state_type()}, Packet ID: {self.packet_id}, Packet '
                  f'Type: {self.packet_type}, Packet Data: {self.data}')

    def _handle_logon(self):

        ##############################
        # Login Processing (offline) #
        ##############################

        if self.packet_type == 'Login Start':
            username = String().unpack(bytearray(self.data))
            print(f'[LOGIN START] {username}')

            Faker.seed(username)
            uuidString = fake.uuid4()

            msg = b'\x02' + String(uuidString).pack() + String(username).pack()

            msg = VarInt(len(msg)).pack() + msg

            print(f'[LOGIN SUCCESSFUL] {username} - {uuidString}')
            self.conn.send(msg)
            self.state = 3
            
            msg = b'\x26' + Int(1).pack() + UnsignedByte(3).pack() + Int(0).pack() + Long(12345678).pack()
            msg += UnsignedByte(20).pack() + String("flat").pack() + VarInt(16).pack()
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
            print(f'[UNKNOWN/UNHANDLED PACKET] State: {self._get_state_type()}, Packet ID: {self.packet_id}, Packet Type: {self.packet_type}, Packet Data: {self.data}')

    def _send_chat_message_(self, message):
        # give the result
        chatMessage = {
            "text": message
        }
        msg = b'\x0F' + Json(chatMessage).pack() + Byte(0).pack()
        msg = VarInt(len(msg)).pack() + msg
        self.conn.send(msg)
    
    def _handle_play(self):
        start = timer()
        Faker.seed("Time until kick")
        uuidString = fake.uuid4()
        if not self.joined and not self.disconnected and self.loaded_in:
            self.joined = True
            self._send_chat_message_(f"Hello, Welcome to the WIP \u00A75MinePython\u00A7r server, currently only functions in 1.15.2")
            
            # Create a boss bar to count down to server kick
            title = {
                "text": f"\u00A75\u00A7lTime Left on MinePython",
                "bold": "true"
            }
            msg = b'\x0D' + uuid.UUID(uuidString).bytes + VarInt(0).pack() + Json(title).pack() + Float(1).pack() + VarInt(5).pack() +  VarInt(4).pack() + UnsignedByte(0).pack()
            msg = VarInt(len(msg)).pack() + msg
            self.conn.send(msg)
        else:
            self._handle_keep_alive()

            if self.packet_type == "Chat":
                script = self.data[1:]
                if script.startswith(b"/addline"):
                    if len(self.script) > 0:
                        self.script += f"\n{script[9:].decode()}"
                    else:
                        self.script = f"{script[9:].decode()}"
                    self._send_chat_message_('Current program:\n'+self.script)
                if script.startswith(b"/execute"):
                    sys.stdout = io.StringIO()
                    sys.stderr = io.StringIO()
                    errored = False
                    try:
                        exec(self.script)
                    except:
                        errored = True
                    self._send_chat_message_('Errored: \u00A7c'+sys.stderr.getvalue().strip() if errored else f"Result:\n{sys.stdout.getvalue().strip()}")
                    sys.stdout = sys.__stdout__
                    sys.stderr = sys.__stderr__
                if script.startswith(b"/clearprog"):
                    self.script = ""
                    self._send_chat_message_("Cleared the program!")
            elif self.packet_type == "Keep Alive":
                pass
            else:
                print(f'[UNKNOWN/UNHANDLED PACKET] State: {self._get_state_type()}, Packet ID: {self.packet_id}, Packet Type: {self.packet_type}, Packet Data: {self.data}')



            if self.loaded_in:
                if self.ticks % 100 == 0:
                    chatMessage = {
                        "text": f"Hello, it has been {self.ticks} ticks since you joined, you will be kicked at 1000 ticks"
                    }
                    msg = b'\x0F' + Json(chatMessage).pack() + Byte(2).pack()
                    msg = VarInt(len(msg)).pack() + msg
                    self.conn.send(msg)

                if self.ticks == 1000:
                    chatMessage = {
                        "text": "\u00A75\u00A7lThank you for connecting to MinePython 1.15.2"
                    }
                    msg = b'\x1B' + Json(chatMessage).pack()
                    msg = VarInt(len(msg)).pack() + msg
                    # self.conn.send(msg)
                    # return True
                
                # Update boss bar countdown
                left = 1 - (self.ticks / 1000)
                if left > 0:
                    msg = b'\x0D' + uuid.UUID(uuidString).bytes + VarInt(2).pack() + Float(left).pack()
                    msg = VarInt(len(msg)).pack() + msg
                    self.conn.send(msg)
                elif left == 0:
                    msg = b'\x0D' + uuid.UUID(uuidString).bytes + VarInt(1).pack()

                self.ticks += 1
            else:
                sleep(0.25)
                print('[UPDATE PLAYER POSITION PACKET]')
                msg = b'\x36' + Double(0).pack() + Double(0).pack() + Double(0).pack() + Float(0).pack() + Float(0).pack() + Byte(0).pack() + VarInt(0).pack()
                msg = VarInt(len(msg)).pack() + msg
                self.conn.send(msg)
                self.loaded_in = True
        end = timer()
        actual_time = (end - start) * 1000
        delay = 0.02 - (actual_time/1000)
        if (delay) > 0:
            sleep(delay)
        return False


while True:
    conn, addr = s.accept()
    print(f'[INCOMING CONNECTION] {addr}')

    thread = threadedClient(conn, addr)
    thread.start()