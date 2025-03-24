from enum import Enum


class RedisPollError(Exception):
    class Code(Enum):
        GET = 'RedisPollGet'
        DECODE = 'RedisPollDecode'
        TIMEOUT = 'RedisPollTimeout'

    def __init__(self, code: Code):
        self.code = code
