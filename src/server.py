import argparse
import asyncio
import struct
from asyncio import Queue

from aioquic.asyncio import serve
from aioquic.quic.configuration import QuicConfiguration
from queues import StrictPriorityQueue

FILE_BASE_NAME = '../data/segments/video_tiled_dash_track'
FILE_FORMAT = '.m4s'
DASH = '10000'
MAX_TILE = 201
FPS = 30
FRAME_TIME_MS = 33.33

def handle_stream(reader, writer):
    asyncio.ensure_future(handle_echo(reader, writer))

async def handle_echo(reader, writer):
    if Queue_Type == "SP":
        queue = StrictPriorityQueue()
    else:
        queue = Queue()

    name = await reader.read(1024)

    print("Connection with "+str(name.decode()))

    asyncio.ensure_future(receive(reader, queue))
    while True:
        tile = await queue.get()
        await send(str(tile), writer)

async def receive(reader, queue):
    while True:
        size, = struct.unpack('<L', await reader.readexactly(4))
        message_data = await reader.readexactly(size)

        message = eval(message_data.decode())
        if Queue_Type == "SP":
            queue.put_nowait((int(message[1]), (message[0], message[2])))
        else:
            queue.put_nowait((message[0], message[2]))

async def send(message, writer):
    info = eval(message[1:-1])
    segment = str(info[0])
    tile = str(info[1])

    file_info = tile+'_'+segment
    data = file_info.encode()

    writer.write(struct.pack('<L', len(data)))
    writer.write(data)

    file_name = FILE_BASE_NAME+file_info+FILE_FORMAT

    with open(file_name, "rb") as binaryfile:
        not_finished = True
        chunk_n = 1
        while not_finished:
            chunk = binaryfile.read(1024)
            if not chunk:
                writer.write(struct.pack('<L', 0))
                not_finished = False
            else:
                writer.write(struct.pack('<L', len(chunk)))
                writer.write(chunk)
                chunk_n+=1

    # If first time send mp4
    # If not, just the m4s


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="QUIC Video Server")

    parser.add_argument(
        "-c",
        "--certificate",
        type=str,
        required=True,
        help="load the TLS certificate from the specified file",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="::",
        help="listen on the specified address (defaults to ::)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=4433,
        help="listen on the specified port (defaults to 4433)",
    )
    parser.add_argument(
        "-k",
        "--private-key",
        type=str,
        required=True,
        help="load the TLS private key from the specified file",
    )
    parser.add_argument(
        "-q",
        "--queue",
        type=str,
        default="FIFO",
        help="the type of Queuing used by the server",
    )
    args = parser.parse_args()

    global Queue_Type
    Queue_Type = args.queue

    configuration = QuicConfiguration(
        is_client=False,
        max_datagram_frame_size=65536
    )

    configuration.load_cert_chain(args.certificate, args.private_key)

    asyncio.ensure_future(
        serve(args.host,
              args.port,
              configuration=configuration,
              stream_handler=handle_stream
        )
    )

    loop = asyncio.get_event_loop()
    loop.run_forever()