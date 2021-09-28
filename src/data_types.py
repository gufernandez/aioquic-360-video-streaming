class VideoPacket:
    def _init(self, segment, tile, priority, bitrate=1):
        self.segment = segment
        self.tile = tile
        self.priority = priority
        self.bitrate = bitrate

