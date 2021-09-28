import argparse
import asyncio
import struct
from asyncio import Queue

from aioquic.asyncio import serve
from aioquic.quic.configuration import QuicConfiguration
from queues import StrictPriorityQueue, WeightedFairQueue

FILE_BASE_NAME = '../data/segments/video_tiled_dash_track'
FILE_FORMAT = '.m4s'
DASH = '10000'
MAX_TILE = 201
FPS = 30
FRAME_TIME_MS = 33.33
SEGMENTS = 10

def handle_stream(reader, writer):
    asyncio.ensure_future(handle_echo(reader, writer))

async def handle_echo(reader, writer):
    if Queue_Type == "WFQ":
        queue = WeightedFairQueue()
    elif Queue_Type == "SP":
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
    last_segment = 1
    tiles_priority = Queue()
    segment = 1

    while True:
        try:
            read_data = await asyncio.wait_for(reader.readexactly(4), timeout=0.01)
            size, = struct.unpack('<L', read_data)

            message_data = await reader.readexactly(size)

            message = eval(message_data.decode())
            message_type = 'tile_request'

            segment = message[0]
            priority = int(message[1])
            tile = message[2]

            if segment != last_segment:
                tiles_priority = Queue()
                last_segment = segment

            tiles_priority.put_nowait((priority, tile))

        except asyncio.TimeoutError:
            if segment == last_segment:
                segment += 1

            priority, tile = await tiles_priority.get()
            message_type = 'push'

        if Queue_Type == "WFQ":
            queue.put_nowait((priority, size, (message_type, segment, tile)))
        elif Queue_Type == "SP":
            queue.put_nowait((priority, (message_type, segment, tile)))
        else:
            queue.put_nowait((message_type, segment, tile))

async def send(message, writer):
    info = eval(message[1:-1])
    message_type = str(info[0])
    segment = str(info[1])
    tile = str(info[2])

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