import argparse
import asyncio
import binascii
import csv
import struct
import datetime
from urllib.parse import urlparse

from aioquic.asyncio import QuicConnectionProtocol
from aioquic.asyncio.client import connect
from aioquic.quic.configuration import QuicConfiguration

from src.structures.data_types import VideoPacket, QUICPacket
from src.utils import message_to_video_packet, get_client_file_name, client_file_exists, get_user_id, create_user_dir
from src.constants.video_constants import HIGH_PRIORITY, FRAME_TIME_MS, LOW_PRIORITY, VIDEO_FPS, CLIENT_BITRATE, N_SEGMENTS, \
    PUSH_RECEIVED, MAX_TILE


async def aioquic_client(ca_cert: str, connection_host: str, connection_port: int):
    print("Connecting to Host", connection_host, connection_port)
    configuration = QuicConfiguration(is_client=True)
    configuration.load_verify_locations(ca_cert)
    async with connect(connection_host, connection_port, configuration=configuration) as client:
        connection_protocol = QuicConnectionProtocol
        high_priority_reader, high_priority_writer = await connection_protocol.create_stream(client)
        low_priority_reader, low_priority_writer = await connection_protocol.create_stream(client)
        await handle_stream(high_priority_reader, high_priority_writer, low_priority_reader, low_priority_writer)


async def send_data(writer, stream_id, end_stream, packet=None, push_status=None):
    data = QUICPacket(stream_id, end_stream, packet, push_status).serialize()

    writer.write(struct.pack('<L', len(data)))
    writer.write(data)

    await asyncio.sleep(0.0001)


async def handle_stream(hp_reader, hp_writer, lp_reader, lp_writer):
    client_id = get_user_id()
    print("Starting Client: ", client_id)
    create_user_dir(client_id)

    # User input
    asyncio.ensure_future(receive(hp_reader, client_id))
    asyncio.ensure_future(receive(lp_reader, client_id))

    # Server data received
    hp_writer.write(client_id.encode())
    await asyncio.sleep(0.0001)

    # Missed frames
    missed_tiles_fov = 0
    missed_tiles_fov_per_seg = {}
    # Total frames
    total_tiles_in_fov = 0
    total_tiles_in_fov_per_seg = {}

    missing_ratio = {}

    # USER INPUT (currently simulated by CSV)
    with open(User_Input_File) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        frame = 0
        video_segment = 0
        frame_request = 1

        for row in csv_reader:
            del row[0]
            frame_time = datetime.datetime.now()

            # Frame to make request
            if frame == frame_request:
                fov = []
                for i in row:
                    fov.append(int(i))

                video_segment += 1
                print("Client requesting segment: ", video_segment)

                missed_tiles_fov_per_seg[video_segment] = 0
                total_tiles_in_fov_per_seg[video_segment] = 0

                for tile in range(1, MAX_TILE):
                    if tile in fov:
                        priority = HIGH_PRIORITY
                        writer_to_send = hp_writer
                    else:
                        priority = LOW_PRIORITY
                        writer_to_send = lp_writer

                    message = VideoPacket(video_segment, tile, priority, CLIENT_BITRATE)
                    push_status = PUSH_RECEIVED

                    if not client_file_exists(video_segment, tile, CLIENT_BITRATE, client_id):
                        push_status = None

                    await send_data(writer_to_send, stream_id=client_id, end_stream=False, packet=message,
                                    push_status=push_status)
                frame_request += VIDEO_FPS

                await asyncio.sleep(0.1)

            # CHECK FOR MISSING RATIO
            if frame != 0:
                # Wait for the actual time of the frame
                waiting_for_time = True
                while waiting_for_time:
                    time_now = datetime.datetime.now()
                    delta = time_now - frame_time

                    if delta.microseconds > FRAME_TIME_MS:
                        waiting_for_time = False

                # Check for missing segments
                for tile in row:
                    total_tiles_in_fov += 1
                    if not client_file_exists(video_segment, tile, CLIENT_BITRATE, client_id):
                        missed_tiles_fov += 1

                total_tiles_in_fov_per_seg[video_segment] = total_tiles_in_fov
                missed_tiles_fov_per_seg[video_segment] = missed_tiles_fov

                # On last segment, print the results and end connection
                if video_segment == N_SEGMENTS:
                    percentage = round((missed_tiles_fov/total_tiles_in_fov)*100, 2)
                    for i in range(1, N_SEGMENTS):
                        missing_ratio[i] = str(round((missed_tiles_fov_per_seg[i] / total_tiles_in_fov_per_seg[i]) * 100, 2)) + "%"

                    print("Total tiles: "+str(total_tiles_in_fov))
                    print("Missed tiles: "+str(missed_tiles_fov))
                    print("Missing ratio: "+str(percentage)+"%")
                    print("Missing ratio per segment: "+str(missing_ratio))
                    await send_data(hp_writer, stream_id=client_id, end_stream=True)
                    await send_data(lp_writer, stream_id=client_id, end_stream=True)
                    return

            frame += 1


async def receive(reader, client_id):
    while True:
        size, = struct.unpack('<L', await reader.readexactly(4))
        file_name_data = await reader.readexactly(size)
        file_info = message_to_video_packet(eval(file_name_data.decode()))

        file_name = get_client_file_name(segment=file_info.segment, tile=file_info.tile, bitrate=file_info.bitrate,
                                         client_id=client_id)

        if Client_Log:
            print("Receiving file:", file_name)

        with open(file_name, "wb") as newFile:
            not_finished = True
            while not_finished:
                file_size, = struct.unpack('<L', await reader.readexactly(4))
                if file_size == 0:
                    not_finished = False
                else:
                    chunk = await reader.readexactly(file_size)
                    newFile.write(binascii.hexlify(chunk))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HTTP/3 client for video streaming")
    parser.add_argument(
        "url",
        type=str,
        help="the URL to query (must be HTTPS)"
    )
    parser.add_argument(
        "-c",
        "--ca-certs",
        type=str,
        help="load CA certificates from the specified file"
    )
    parser.add_argument(
        "-i",
        "--user-input",
        required=True,
        type=str,
        help="CSV file with user input simulation",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="increase output verbosity",
        action="store_true"
    )

    args = parser.parse_args()

    global Client_Log
    Client_Log = args.verbose

    global User_Input_File
    User_Input_File = args.user_input

    parsed = urlparse(args.url).path
    url = parsed.split(':')
    host = url[0]

    if len(url) > 1:
        port = url[1]
    else:
        port = 4433

    asyncio.get_event_loop().run_until_complete(aioquic_client(ca_cert=args.ca_certs, connection_host=host, connection_port=port))