import argparse
import asyncio
import binascii
import csv
import struct
import datetime
import timeit

from aioquic.asyncio import QuicConnectionProtocol
from aioquic.asyncio.client import connect
from aioquic.quic.configuration import QuicConfiguration
from src.dash import Dash

from src.structures.data_types import VideoPacket, QUICPacket
from src.utils import message_to_video_packet, get_client_file_name, get_user_id, create_user_dir, host_parser
from src.constants.video_constants import HIGH_PRIORITY, FRAME_TIME_MS, LOW_PRIORITY, VIDEO_FPS, CLIENT_BITRATES, \
    N_SEGMENTS, MAX_TILE, INITIAL_BUFFER_SIZE

last_segment = 1
Client_Log = False
received_files = [[False for x in range(N_SEGMENTS)] for y in range(MAX_TILE)]
waiting_for_buffer = True
downloaded_time = 0
# 1: Sequencial, 2: Alternado
REQUEST_MODE = 2


async def aioquic_client(ca_cert: str, connection_host: str, connection_port: int, dash_algorithm: Dash):
    print("Connecting to Host", connection_host, connection_port)
    configuration = QuicConfiguration(is_client=True)
    configuration.load_verify_locations(ca_cert)
    async with connect(connection_host, connection_port, configuration=configuration) as client:
        connection_protocol = QuicConnectionProtocol
        high_priority_reader, high_priority_writer = await connection_protocol.create_stream(client)
        low_priority_reader, low_priority_writer = await connection_protocol.create_stream(client)
        await handle_stream(high_priority_reader, high_priority_writer, low_priority_reader, low_priority_writer,
                            dash_algorithm)


async def send_data(writer, stream_id, end_stream, packet=None, push_status=None):
    data = QUICPacket(stream_id, end_stream, packet, push_status).serialize()

    writer.write(struct.pack('<L', len(data)))
    writer.write(data)

    await asyncio.sleep(0.0001)


async def handle_stream(hp_reader, hp_writer, lp_reader, lp_writer, dash):
    global waiting_for_buffer

    client_id = get_user_id()
    print("Starting Client: ", client_id)
    create_user_dir(client_id)

    # User input
    asyncio.ensure_future(receive(hp_reader, client_id, dash))
    asyncio.ensure_future(receive(lp_reader, client_id, dash))

    # Server data received
    hp_writer.write(client_id.encode())
    await asyncio.sleep(0.0001)

    # List all tiles
    tiles_list = list(range(1, MAX_TILE))

    # Total frames
    total_frames = 0
    total_frames_fov = 0

    # Missed frames
    missed_frames = 0
    missed_frames_fov = 0

    # Missing ratio
    missed_frames_seg = {}
    total_frames_seg = {}
    missing_ratio = {}
    missed_frames_seg_fov = {}
    total_frames_seg_fov = {}
    missing_ratio_fov = {}

    # Initial buffer
    print("Initial Buffer...")
    for buffer_segment in range(1, INITIAL_BUFFER_SIZE+1):
        if Client_Log:
            print("Request segment ", buffer_segment)

        current_bitrate = dash.get_max_bitrate()
        for tile in range(1, MAX_TILE):
            message = VideoPacket(buffer_segment, tile, HIGH_PRIORITY, current_bitrate)

            await send_data(hp_writer, stream_id=client_id, end_stream=False, packet=message)

        for tile in range(1, MAX_TILE):
            tile_exists = False
            while not tile_exists:
                tile_exists = received_files[tile-1][buffer_segment-1]
                await asyncio.sleep(0.01)

    print("Initial buffer complete.")
    waiting_for_buffer = False

    asyncio.ensure_future(play(dash, hp_writer, client_id))

    # User input obtained from CSV file
    with open(User_Input_File) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        frame = 0
        video_segment = 0
        frame_request = 1

        for row in csv_reader:
            del row[0]
            frame_time = datetime.datetime.now()

            # Frame to make request
            if frame == frame_request and video_segment < N_SEGMENTS:
                fov = []
                for i in row:
                    fov.append(int(i))

                video_segment += 1

                missed_frames_seg[video_segment] = 0
                total_frames_seg[video_segment] = 0
                missed_frames_seg_fov[video_segment] = 0
                total_frames_seg_fov[video_segment] = 0

                current_bitrate = dash.get_next_bitrate(video_segment)

                while waiting_for_buffer:
                    await asyncio.sleep(0.5)
                    print("Waiting for the buffer to fill...")

                print("Client requesting segment: ", video_segment)

                all_tiles = list(range(1, MAX_TILE))

                if REQUEST_MODE == 1:
                    # Request Ordenado
                    for tile in all_tiles:
                        if not received_files[tile-1][video_segment-1]:
                            if tile in fov:
                                priority = HIGH_PRIORITY
                                writer_to_send = hp_writer
                            else:
                                priority = LOW_PRIORITY
                                writer_to_send = lp_writer

                            message = VideoPacket(video_segment, tile, priority, current_bitrate)
                            await send_data(writer_to_send, stream_id=client_id, end_stream=False, packet=message)
                else:
                    # Request alternado
                    out_fov = list(set(all_tiles) - set(fov))
                    running = True
                    get_state = 0
                    while running:
                        if get_state < 2:
                            tile = out_fov[0]
                            del out_fov[0]

                        if not received_files[tile-1][video_segment-1]:
                            if get_state == 2: # FOV
                                priority = HIGH_PRIORITY
                                writer_to_send = hp_writer
                            else: # OUT FOV
                                priority = LOW_PRIORITY
                                writer_to_send = lp_writer

                            message = VideoPacket(video_segment, tile, priority, current_bitrate)
                            await send_data(writer_to_send, stream_id=client_id, end_stream=False, packet=message)

                        get_state += 1
                        if len(out_fov) == 0 & len(fov) == 0:
                            running = False
                        elif len(fov) == 0 & get_state == 2:
                            get_state = 0
                        elif len(out_fov) == 0 & get_state < 2:
                            get_state = 2
                        else:
                            get_state += 1

                frame_request += VIDEO_FPS

                await asyncio.sleep(0.005)

            # CHECK FOR MISSING RATIO
            if frame != 0:
                # Wait for the actual time of the frame
                waiting_for_time = True
                while waiting_for_time:
                    time_now = datetime.datetime.now()
                    delta = time_now - frame_time

                    if delta.microseconds > FRAME_TIME_MS:
                        waiting_for_time = False

                    await asyncio.sleep(0.0001)

                # Check for missing segments
                index = 0
                missed_tiles = 0
                missed_tiles_fov = 0
                total_tiles = 0
                total_tiles_fov = 0

                tiles_in_fov = []
                for t in row:
                    tile = int(t)
                    if index != 0:
                        tiles_in_fov.append(tile)
                    index += 1

                for tile in tiles_list:
                    total_tiles += 1
                    in_row = False

                    if tile in tiles_in_fov:
                        total_tiles_fov += 1
                        in_row = True

                    if not received_files[tile-1][video_segment-1]:
                        missed_tiles += 1
                        if in_row:
                            missed_tiles_fov += 1

                missed_frames += missed_tiles
                total_frames += total_tiles
                missed_frames_seg[video_segment] = missed_frames_seg[video_segment] + missed_tiles
                total_frames_seg[video_segment] = total_frames_seg[video_segment] + total_tiles

                missed_frames_fov += missed_tiles_fov
                total_frames_fov += total_tiles_fov
                missed_frames_seg_fov[video_segment] = missed_frames_seg_fov[video_segment] + missed_tiles_fov
                total_frames_seg_fov[video_segment] = total_frames_seg_fov[video_segment] + total_tiles_fov

                # On last segment, print the results and end connection
                if frame == (N_SEGMENTS*VIDEO_FPS)+1:
                    i = 1
                    sum_bitrate = 0
                    download_time_seg = {}
                    while i <= N_SEGMENTS:
                        missing_ratio[i] = str(round((missed_frames_seg[i]/total_frames_seg[i])*100, 2))+"%"
                        missing_ratio_fov[i] = str(round((missed_frames_seg_fov[i]/total_frames_seg_fov[i])*100, 2))+'%'

                        sum_bitrate += dash.bitrates_seg[i]
                        try:
                            download_time_seg[i] = str(round(dash.previous_segment_times_seg[i], 2))+'s'
                        except:
                            download_time_seg[i] = 'NOT_FINISHED'

                        i += 1

                    missing_ratio_total = round((missed_frames/total_frames)*100, 2)
                    missing_ratio_total_fov = round((missed_frames_fov/total_frames_fov)*100, 2)

                    print("Missing ratio total: "+str(missing_ratio_total)+"%")
                    print("Missing ratio total (campo visão): "+str(missing_ratio_total_fov)+"%")
                    print("Missing ratio por segmento: "+str(missing_ratio))
                    print("Missing ratio por segmento (campo visão): "+str(missing_ratio_fov))
                    print("Tempo total de download: "+str(round(sum(dash.previous_segment_times), 2))+"s")
                    print("Tempo total de download por segmento: "+str(download_time_seg))
                    print("Bitrate médio: "+str(round(sum_bitrate / N_SEGMENTS, 2)))
                    print("Bitrate por segmento: "+str(dash.bitrates_seg))
                    await send_data(hp_writer, stream_id=client_id, end_stream=True)
                    await send_data(lp_writer, stream_id=client_id, end_stream=True)
                    return

            frame += 1


async def receive(reader, client_id, client_dash):
    global last_segment
    global Client_Log
    global received_files
    global downloaded_time

    current_segment = 0

    while True:
        start_time = timeit.default_timer()

        size, = struct.unpack('<L', await reader.readexactly(4))

        client_dash.append_download_size(size)

        file_name_data = await reader.readexactly(size)
        file_info = message_to_video_packet(eval(file_name_data.decode()))

        file_name = get_client_file_name(segment=file_info.segment, tile=file_info.tile, bitrate=file_info.bitrate,
                                         client_id=client_id)

        with open(file_name, "wb") as newFile:
            not_finished = True
            while not_finished:
                file_size, = struct.unpack('<L', await reader.readexactly(4))
                if file_size == 0:
                    not_finished = False
                else:
                    chunk = await reader.readexactly(file_size)
                    newFile.write(binascii.hexlify(chunk))

        last_segment = file_info.segment

        received_files[file_info.tile-1][file_info.segment-1] = True

        downloaded_time += 1/200

        if Client_Log and current_segment != last_segment:
            print("Receiving segment:", current_segment)
        elif Client_Log:
            print("Receiving file:", file_name)

        client_dash.update_download_time(timeit.default_timer() - start_time, int(file_info.segment))


async def play(play_dash, hp_writer, client_id):
    global downloaded_time
    global waiting_for_buffer

    start_time = datetime.datetime.now()
    stopped_time = start_time - start_time
    while downloaded_time < N_SEGMENTS:
        delta = datetime.datetime.now()
        played_time = delta - start_time - stopped_time
        print("Buffer: "+'{0:.2f}'.format(played_time.seconds)+"s/"+'{0:.2f}'.format(downloaded_time)+"s")
        if played_time.seconds > downloaded_time:
            waiting_for_buffer = True
            await fill_buffer(round(downloaded_time), play_dash, hp_writer, client_id)
            waiting_for_buffer = False
            stopped_time += datetime.datetime.now()-delta

        await asyncio.sleep(0.5)


async def fill_buffer(current_segment, buffer_dash, hp_writer, client_id):

    start_segment = current_segment
    end_segment = min(N_SEGMENTS, current_segment+INITIAL_BUFFER_SIZE)

    print("Filling buffer from segment "+str(start_segment)+" to segment "+str(end_segment))

    for buffer_segment in range(start_segment, end_segment):
        if Client_Log:
            print("Request segment ", buffer_segment)

        current_bitrate = buffer_dash.get_max_bitrate()
        for tile in range(1, MAX_TILE):
            message = VideoPacket(buffer_segment, tile, HIGH_PRIORITY, current_bitrate)

            await send_data(hp_writer, stream_id=client_id, end_stream=False, packet=message)

        for tile in range(1, MAX_TILE):
            tile_exists = False
            while not tile_exists:
                tile_exists = received_files[tile-1][buffer_segment-1]
                await asyncio.sleep(0.01)
    return


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
    parser.add_argument(
        "-da",
        "--dash-algorithm",
        required=False,
        default="basic",
        type=str,
        help="dash algorithm (options: basic, basic2) - (defaults to basic)",
    )

    args = parser.parse_args()

    Client_Log = args.verbose

    User_Input_File = args.user_input

    host, port = host_parser(args.url)
    print(host)

    if port is None:
        port = 4433

    user_dash = Dash(CLIENT_BITRATES, args.dash_algorithm)

    asyncio.get_event_loop().run_until_complete(aioquic_client(ca_cert=args.ca_certs, connection_host=host,
                                                               connection_port=port, dash_algorithm=user_dash))
