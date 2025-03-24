def read_test_res_bytes(file_path) -> bytes:
    with open(file_path, 'rb') as f:
        return f.read()


def read_test_res_text(file_path) -> str:
    return read_test_res_bytes(file_path).decode('utf-8')
