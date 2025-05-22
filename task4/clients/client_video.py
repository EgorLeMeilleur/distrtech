import time
import threading
import requests
import cv2
from common import register_service, discover_service, health_app
import video_control_pb2_grpc, video_control_pb2

def run_video_client():
    register_service('video_client', 'video_client_1', 5003)
    threading.Thread(target=health_app, args=(5003,), daemon=True).start()

    stream_url = 'https://stream.mu-u.ru:8443/amka/cam7/playlist.m3u8'
    cap = cv2.VideoCapture(stream_url)
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        _, img_encoded = cv2.imencode('.jpg', frame)
        addrs = discover_service('video_server')
        if addrs:
            addr, port = addrs[0]
            url = f"http://{addr}:{port}/analyze"
            try:
                requests.post(url, files={'frame': img_encoded.tobytes()})
            except:
                pass
        time.sleep(1)

if __name__ == '__main__':
    run_video_client()