import os
import struct

from tests.utils.res_utils import read_test_res_bytes

my_dir = os.path.dirname(os.path.abspath(__file__))
res_dir = f'{my_dir}/res'


def test_box_feature_binary_decode():
    content = read_test_res_bytes(f'{res_dir}/provenancedata.tech_HELIOS_6668ae9af5bdec6693b017bc_02.b00')

    box_features = []
    index = 0
    while index < len(content):
        box, features, index = assemble_box_features(content, index)
        box_features.append({
            'box': box,
            'features': features
        })

    assert len(box_features) == 5


def assemble_box_features(b: bytes, index: int) -> tuple[list[int], list[float], int]:
    box = [
        two_bytes_to_int(b, index),
        two_bytes_to_int(b, index + 2),
        two_bytes_to_int(b, index + 4),
        two_bytes_to_int(b, index + 6)
    ]
    index += 8

    features = [four_bytes_to_float(b, i) for i in range(index, index + 1536 * 4, 4)]
    index += 1536 * 4

    return box, features, index


def two_bytes_to_int(b: bytes, index: int) -> int:
    b0 = b[index]
    b1 = b[index + 1]
    return b0 + b1 * 256


def four_bytes_to_float(b: bytes, index: int) -> float:
    b = b[index:index + 4]
    return struct.unpack('f', b)[0]
