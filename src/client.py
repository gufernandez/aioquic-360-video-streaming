import asyncio
import binascii
import csv
import struct
import time
import datetime
import os.path

from aioquic.asyncio import QuicConnectionProtocol
from aioquic.asyncio.client import connect
from aioquic.quic.configuration import QuicConfiguration

CLIENT_ID = '1'
FILE_BASE_NAME = '../data/client_files/video_tiled_dash_track'
FILE_FORMAT = '.m4s'
DASH = '10000'
MAX_TILE = 201
FPS = 30
FRAME_TIME_MS = 33333

async def aioquic_client():
    configuration = QuicConfiguration(is_client=True)
    configuration.load_verify_locations('../cert/pycacert.pem')
    async with connect('127.0.0.1', 8888, configuration=configuration) as client:
        connection_protocol = QuicConnectionProtocol
        reader, writer = await connection_protocol.create_stream(client)
        await handle_stream(reader, writer)

async def handle_stream(reader, writer):
    # User input
    asyncio.ensure_future(receive(reader))
    # Server data received
    writer.write(CLIENT_ID.encode())
    await asyncio.sleep(0.0001)

    # List all tiles
    tiles_list = list(range(1,201))
    # Missed frames
    missed_frames = 0
    # Total frames
    total_frames = 0

    # USER INPUT (currently simulated by CSV)
    with open('../data/example.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        frame = 0
        video_segment = 0
        frame_request = 1

        for row in csv_reader:
            frame_time = datetime.datetime.now()
            index = 0
            not_in_fov = tiles_list.copy()
            # Frame to make request
            if frame == frame_request:
                video_segment += 1

                # SEND REQUEST FOR TILES IN FOV WITH HIGHER PRIORITY
                for tile in row:
                    tile = int(tile)
                    if index != 0:
                        # Smaller the number, bigger the priority
                        message = [video_segment, 1, tile]
                        message_data = str(message).encode()

                        writer.write(struct.pack('<L', len(message_data)))
                        writer.write(message_data)

                        await asyncio.sleep(0.0001)

                        not_in_fov.remove(tile)
                    index += 1

                # REQUESTS FOR THE TILES THAT ARE NOT IN FOV WITH LOWER PRIORITY
                for tile in not_in_fov:
                    message = [video_segment, 2, tile]
                    message_data = str(message).encode()

                    writer.write(struct.pack('<L', len(message_data)))
                    writer.write(message_data)

                    await asyncio.sleep(0.0001)
                frame_request += FPS

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
                    if index != 0:
                        total_frames += 1
                        if is_segment_missed(tile, video_segment):
                            missed_frames += 1
                    index += 1

                # On last segment, print the results
                if video_segment == 10:
                    percentage = round((missed_frames/total_frames)*100, 2)
                    print("Total tiles: "+str(total_frames))
                    print("Missed tiles: "+str(missed_frames))
                    print("Missing ratio: "+str(percentage)+"%")
                    return

            frame += 1

def is_segment_missed(tile, segment):
    return not os.path.isfile(FILE_BASE_NAME + str(tile).strip() + '_' + str(segment).strip() + FILE_FORMAT)

async def receive(reader):
    while True:
        size, = struct.unpack('<L', await reader.readexactly(4))
        file_name_data = await reader.readexactly(size)
        file_info = file_name_data.decode()

        #print("Received "+file_info)

        file_name = FILE_BASE_NAME+file_info+FILE_FORMAT
        with open(file_name, "wb") as newFile:
            not_finished = True
            while not_finished:
                file_size, = struct.unpack('<L', await reader.readexactly(4))
                if file_size == 0:
                    not_finished = False
                else:
                    chunk = await reader.readexactly(file_size)
                    newFile.write(binascii.hexlify(chunk))


async def main():
    await aioquic_client()


asyncio.get_event_loop().run_until_complete(main())