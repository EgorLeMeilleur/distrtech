import os
import json

def send_pipe(pipe_path: str, message: dict):

    if not os.path.exists(pipe_path):
        os.mkfifo(pipe_path)
    with open(pipe_path, "w") as f:
        f.write(json.dumps(message))

def receive_pipe(pipe_path: str):
    if not os.path.exists(pipe_path):
        os.mkfifo(pipe_path)
    with open(pipe_path, "r") as f:
        msg = json.loads(f.read())
    return msg
    
