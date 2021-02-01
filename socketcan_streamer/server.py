import asyncio
import websockets
import can
import struct

from threading import Timer

class Watchdog(Exception):
    def __init__(self, timeout, userHandler=None):  # timeout in seconds
        self.timeout = timeout
        self.handler = userHandler if userHandler is not None else self.defaultHandler
        self.timer = Timer(self.timeout, self.handler)
        self.timer.start()

    def reset(self):
        self.timer.cancel()
        self.timer = Timer(self.timeout, self.handler)
        self.timer.start()

    def stop(self):
        self.timer.cancel()

    def defaultHandler(self):
        raise self



ws=None


def pack_can(address, data, bus):

    CAN_TRANSMIT = 1
    CAN_EXTENDED = 4

    if(len(data) > 8):
        #can't have more than 8 bytes of data in a can frame
        return
    if ( address >= 0x800):
        address = ((address << 3) | CAN_TRANSMIT | CAN_EXTENDED) >> 0
    else:
        address = ((address << 21) | CAN_TRANSMIT) >> 0
    buff = bytearray(struct.pack('<I', address))
    buff.extend(struct.pack('<I', (len(data) | (bus << 4)) >> 0))
    buff.extend(data)
    print(buff)
    return buff



msg_count=0
can_packet = bytearray()
MAX_MESSAGE_QUEUE = 100
watchdog = None

async def on_can_message(msg):
    global ws
    global can_packet
    global msg_count
    global MAX_MESSAGE_QUEUE
    global watchdog
    print(msg)
    watchdog.reset()
    can_frame = pack_can(msg.arbitration_id, msg.data, 0)
    if(len(can_frame) < 16):
        diff = 16-len(can_frame)
        can_frame.extend(bytearray(diff))
    can_packet.extend(can_frame)
    msg_count+=1
    if(ws is not None):
        if(msg_count >= MAX_MESSAGE_QUEUE):
            msg_count = 0
            await ws.send(can_packet)
            can_packet = bytearray()

def can_watchdog_expired():
    global ws
    global can_packet
    global msg_count
    if(ws is not None):
        print("sending last little bit of data")
        print(can_packet)
        if(msg_count>0):
            asyncio.run(ws.send(can_packet))
            can_packet = bytearray()
            msg_count = 0


async def on_new_ws_client(websocket, path):
    global ws
    ws = websocket
    print("New WS Client Connected")
    while True:
        try:
            name = await websocket.recv()
        except websockets.ConnectionClosed:
            print(f"Terminated")
            break
    # await websocket.send(greeting)
async def can_setup():
    global watchdog
    can_interface = 'can0'
    bus = can.interface.Bus(can_interface, bustype='socketcan')
    loop = asyncio.get_event_loop()
    notifier = can.Notifier(bus, [on_can_message], loop=loop)
    watchdog = Watchdog(0.5, can_watchdog_expired)

start_server = websockets.serve(on_new_ws_client, "localhost", 8080)


asyncio.get_event_loop().run_until_complete(can_setup())
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
