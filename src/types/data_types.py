class VideoPacket:
    def __init__(self, segment, tile, priority=2, bitrate=1):
        self.segment = segment
        self.tile = tile
        self.priority = priority
        self.bitrate = bitrate

    def get_list(self):
        return [self.segment, self.tile, self.priority, self.bitrate]

    def serialize(self):
        message = self.get_list()
        return str(message).encode()

class QUICPacket:
    def __init__(self, stream_id, end_stream, video_packet=None, push_status=None):
        self.stream_id = stream_id
        self.video_packet = video_packet
        self.end_stream = end_stream
        self.push_status = push_status

    def serialize(self):
        message = [self.stream_id, self.end_stream]

        if self.video_packet:
            message += self.video_packet.get_list()

        if self.push_status:
            message += self.push_status

        return str(message).encode()

class VideoRequestMessage:
    def __init__(self, message_type, segment, tile, bitrate):
        self.message_type = message_type
        self.segment = segment
        self.tile = tile
        self.bitrate = bitrate

