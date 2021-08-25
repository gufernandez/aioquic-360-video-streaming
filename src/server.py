import asyncio
import struct
import time
from aioquic.asyncio import serve
from aioquic.quic.configuration import QuicConfiguration
from priority_queue import StrictPriorityQueue

CLIENT_ID = '1'
FILE_BASE_NAME = '../data/segments/video_tiled_dash_track'
FILE_FORMAT = '.m4s'
DASH = '10000'
MAX_TILE = 201
FPS = 30
FRAME_TIME_MS = 33.33

async def handle_echo(reader, writer):
    queue = StrictPriorityQueue()
    name = await reader.read(1024)
    name.decode()

    asyncio.ensure_future(receive(reader, queue))
    while True:
        tile = await queue.get()
        send(str(tile), writer)

async def receive(reader, queue):
    while True:
        size, = struct.unpack('<L', await reader.readexactly(4))
        message_data = await reader.readexactly(size)

        message = eval(message_data.decode())
        queue.put_nowait((int(message[1]), (message[0], message[2])))

def send(message, writer):
    info = eval(message[1:-1])
    segment = str(info[0])
    tile = str(info[1])

    file_info = tile+'_'+segment
    data = file_info.encode()

    writer.write(struct.pack('<L', len(data)))
    writer.write(data)

    file_name = FILE_BASE_NAME+file_info+FILE_FORMAT
    print("Sending file for tile " + tile + " and segment " + segment)

    with open(file_name, "rb") as binaryfile:
        not_finished = True
        while not_finished:
            chunk = binaryfile.read(4096)
            if not chunk:
                writer.write(struct.pack('<L', 0))
                not_finished = False
            else:
                writer.write(struct.pack('<L', 4096))
                writer.write(chunk)

    # If first time send mp4
    # If not, just the m4s

def handle_stream(reader, writer):
    asyncio.ensure_future(handle_echo(reader, writer))

async def main():
    configuration = QuicConfiguration(
        is_client=False,
        max_datagram_frame_size=65536
    )

    configuration.load_cert_chain('../cert/ssl_cert.pem', '../cert/ssl_key.pem')

    await serve('127.0.0.1',
                8888,
                configuration=configuration,
                stream_handler=handle_stream,)


asyncio.ensure_future(main())
loop = asyncio.get_event_loop()
loop.run_forever()