import os
import json
import requests
from services.config import CONSUL_ADDR, CONSUL_PORT
import errno
BASE_URL = f"http://{CONSUL_ADDR}:{CONSUL_PORT}"

def get_aggregator_pipe(pipe_key):
    url = f"{BASE_URL}/v1/catalog/service/aggregator"
    try:
        resp = requests.get(url, timeout=2)
        resp.raise_for_status()
        entries = resp.json()
    except Exception as e:
        print(f"[AggregatorPipe] Consul catalog fetch failed: {e}")
        return None

    if not entries:
        print("[AggregatorPipe] No aggregator instances in catalog")
        return None
    
    paths = []
    for entry in entries:
        meta = entry.get("ServiceMeta", {})
        path = meta.get(pipe_key)
        if not path:
            print(f"[AggregatorPipe] Meta key '{pipe_key}' missing in ServiceMeta")
            return None
        paths.append(path)
    return paths

if os.name == 'nt':
    import win32pipe, win32file, pywintypes
    def create_pipe(path: str):
        full_name = r"\\\\.\\pipe\\" + path
        try:
            handle = win32pipe.CreateNamedPipe(
                full_name,
                win32pipe.PIPE_ACCESS_DUPLEX,
                win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_WAIT,
                1, 65536, 65536, 0, None
            )
            print(f"Created Windows pipe: {full_name}")
        except pywintypes.error as e:
            if e.winerror == 32:
                print(f"Pipe already exists: {full_name}")
            else:
                print(f"Failed to create Windows pipe {full_name}: {e}")
        return full_name

    def send_pipe(path: str, message: dict) -> bool:
        full_name = r"\\\\.\\pipe\\" + path
        try:
            handle = win32file.CreateFile(
                full_name,
                win32file.GENERIC_WRITE,
                0, None,
                win32file.OPEN_EXISTING,
                0, None
            )
            data = json.dumps(message).encode('utf-8')
            win32file.WriteFile(handle, data)
            win32file.CloseHandle(handle)
            return True
        except pywintypes.error as e:
            print(f"No reader or error on Windows pipe {full_name}: {e}")
            return False

    def open_pipe_reader(path: str):
        full_name = r"\\\\.\\pipe\\" + path
        handle = win32pipe.CreateNamedPipe(
            full_name,
            win32pipe.PIPE_ACCESS_DUPLEX,
            win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_WAIT,
            1, 65536, 65536, 0, None
        )
        win32pipe.ConnectNamedPipe(handle, None)
        return handle

    def read_pipe(handle) -> dict:
        try:
            _, data = win32file.ReadFile(handle, 65536)
            return json.loads(data.decode('utf-8'))
        except Exception as e:
            print(f"Error reading Windows pipe: {e}")
            return None

else:
    import errno

    def create_pipe(path: str):
        if not os.path.exists(path):
            os.mkfifo(path)
            print(f"Created FIFO: {path}")
        return path

    def send_pipe(path: str, message: dict) -> bool:
        payload = json.dumps(message).encode('utf-8')
        flags = os.O_WRONLY | os.O_NONBLOCK
        try:
            fd = os.open(path, flags)
        except OSError as e:
            if e.errno in (errno.ENXIO, errno.ENOENT):
                print(f"No reader or missing FIFO {path}")
                return False
            else:
                print(f"Error opening FIFO {path}: {e}")
                raise
        try:
            os.write(fd, payload)
        finally:
            os.close(fd)
        return True

    def open_pipe_reader(path: str):
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
        return fd

    def read_pipe(fd) -> dict:
        try:
            data = os.read(fd, 4096)
            if data:
                return json.loads(data.decode('utf-8'))
        except BlockingIOError:
            return None
        return None


    
