import os

from src.data_types import QUICPacket, VideoPacket
from src.video_constants import SERVER_FILE_LOCATION, FILE_BASE_NAME, FILE_END_NAME, FILE_FORMAT, CLIENT_FILE_LOCATION

def message_to_QUICPacket(data):
    packet = QUICPacket(stream_id=data[0], end_stream=data[1])
    if len(data) > 2:
        packet.video_packet = VideoPacket(segment=data[2], tile=data[3], priority=data[4], bitrate=data[5])

    return packet

def message_to_VideoPacket(data):
    return VideoPacket(segment=data[0], tile=data[1], priority=data[2], bitrate=data[3])

def get_server_file_name(segment, tile, bitrate):
    return SERVER_FILE_LOCATION + FILE_BASE_NAME + str(bitrate).strip() + FILE_END_NAME + str(tile).strip() + '_' + str(segment).strip() + FILE_FORMAT

def get_client_file_name(segment, tile, bitrate):
    return CLIENT_FILE_LOCATION + FILE_BASE_NAME + str(bitrate).strip() + FILE_END_NAME + str(tile).strip() + '_' + str(segment).strip() + FILE_FORMAT

def segment_exists(segment, tile, bitrate):
    return os.path.isfile(get_client_file_name(segment, tile, bitrate))