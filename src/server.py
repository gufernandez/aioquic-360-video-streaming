import argparse
import asyncio
import struct
from asyncio import Queue
from collections import deque

from aioquic.asyncio import serve
from aioquic.quic.configuration import QuicConfiguration
from src.structures.queues import StrictPriorityQueue, WeightedFairQueue
from src.structures.data_types import VideoRequestMessage, VideoPacket
from src.utils import message_to_QUICPacket, get_server_file_name
from src.constants.video_constants import CLOSE_REQUEST, TILE_REQUEST, PUSH_REQUEST, WFQ_QUEUE, SP_QUEUE, \
    N_SEGMENTS, PUSH_CANCEL, HIGHEST_PRIORITY, PUSH_RECEIVED


def handle_stream(reader, writer):
    asyncio.ensure_future(handle_echo(reader, writer))

async def handle_echo(reader, writer):
    closed = False

    if Queue_Type == WFQ_QUEUE:
        queue = WeightedFairQueue()
    elif Queue_Type == SP_QUEUE:
        queue = StrictPriorityQueue()
    else:
        queue = Queue()

    name = await reader.read(1024)

    print("Connection with "+str(name.decode()))

    asyncio.ensure_future(receive(reader, queue))
    while not closed:
        video_request = await queue.get()
        if video_request.message_type == CLOSE_REQUEST:
            closed = True
        else:
            await send(video_request, writer)

async def receive(reader, queue):
    last_segment = 1
    tiles_priority = deque()
    segment = 1
    closed = False
    is_push_allowed = False

    while not closed:
        try:
            read_data = await asyncio.wait_for(reader.readexactly(4), timeout=0.01)
            size, = struct.unpack('<L', read_data)

            message_data = await reader.readexactly(size)

            message = message_to_QUICPacket(eval(message_data.decode()))

            if message.end_stream:
                message_type = CLOSE_REQUEST

                priority = HIGHEST_PRIORITY
                segment = 0
                tile = 0
                bitrate = 0

                closed = True
            elif message.push_status == PUSH_CANCEL:
                message_type = PUSH_CANCEL

                priority = HIGHEST_PRIORITY
                tile = 0
                bitrate = 0

                is_push_allowed = False
            else:
                if message.push_status == PUSH_RECEIVED:
                    message_type = PUSH_RECEIVED
                else:
                    message_type = TILE_REQUEST

                segment = message.video_packet.segment
                priority = message.video_packet.priority
                tile = message.video_packet.tile
                bitrate = message.video_packet.bitrate

                if segment != last_segment:
                    tiles_priority = deque()
                    last_segment = segment
                    if message_type == TILE_REQUEST:
                        print("STARTED SENDING SEGMENT: ", segment)

                tiles_priority.appendleft((priority, tile, bitrate))
                is_push_allowed = True

        except asyncio.TimeoutError:
            if is_push_allowed:
                message_type = PUSH_REQUEST
                if segment == last_segment:
                    segment += 1
                    print("PUSHING SEGMENT: ", segment)

                if tiles_priority:
                    priority, tile, bitrate = tiles_priority.pop()
                else:
                    continue

        if segment <= N_SEGMENTS and message_type != PUSH_RECEIVED:
            data = VideoRequestMessage(message_type, segment, tile, bitrate)
            if Queue_Type == WFQ_QUEUE:
                queue.put_nowait((priority, size, data))
            elif Queue_Type == SP_QUEUE:
                queue.put_nowait((priority, data))
            else:
                queue.put_nowait(data)

async def send(message: VideoRequestMessage, writer):
    segment = message.segment
    tile = message.tile
    bitrate = message.bitrate

    video_info = VideoPacket(segment=segment, tile=tile, bitrate=bitrate)
    data = video_info.serialize()

    writer.write(struct.pack('<L', len(data)))
    writer.write(data)

    file_name = get_server_file_name(segment=segment, tile=tile, bitrate=bitrate)

    with open(file_name, "rb") as video_file:
        not_finished = True
        chunk_n = 1
        while not_finished:
            chunk = video_file.read(1024)
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

    print("Starting Server")
    asyncio.ensure_future(
        serve(args.host,
              args.port,
              configuration=configuration,
              stream_handler=handle_stream
        )
    )

    loop = asyncio.get_event_loop()
    loop.run_forever()