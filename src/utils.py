import os
import time

from src.structures.data_types import QUICPacket, VideoPacket
from src.constants.video_constants import SERVER_FILE_LOCATION, FILE_BASE_NAME, FILE_END_NAME, FILE_FORMAT, CLIENT_FILE_LOCATION

def message_to_QUICPacket(data):
    packet = QUICPacket(stream_id=data[0], end_stream=data[1])
    if len(data) > 2:
        packet.video_packet = VideoPacket(segment=data[2], tile=data[3], priority=data[4], bitrate=data[5])

    return packet

def message_to_VideoPacket(data):
    return VideoPacket(segment=data[0], tile=data[1], priority=data[2], bitrate=data[3])

def get_server_file_name(segment, tile, bitrate):
    return SERVER_FILE_LOCATION + FILE_BASE_NAME + str(bitrate).strip() + FILE_END_NAME + str(tile).strip() + '_' + str(segment).strip() + FILE_FORMAT

def get_client_file_name(segment, tile, bitrate, client_id):
    return get_client_folder(client_id) + FILE_BASE_NAME + str(bitrate).strip() + FILE_END_NAME + str(tile).strip() + '_' + str(segment).strip() + FILE_FORMAT

def segment_exists(segment, tile, bitrate, client_id):
    return os.path.isfile(get_client_file_name(segment, tile, bitrate, client_id))

def get_user_id():
    return str(int(time.time()))

def create_user_dir(client_id):
    print(get_client_folder(client_id))
    os.makedirs(get_client_folder(client_id))

def get_client_folder(client_id):
    return CLIENT_FILE_LOCATION + client_id + '/'