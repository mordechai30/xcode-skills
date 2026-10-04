"""Small local request channel using relative Unix socket paths."""
import json
import os
import socket


def connect(folder, name, request, timeout=180):
    """Send one request from the folder containing a short socket name.
    Call only from a single-threaded CLI or serialized retained runtime.
    """
    old = os.getcwd()
    try:
        os.chdir(folder)
        with socket.socket(socket.AF_UNIX) as channel:
            channel.settimeout(timeout)
            channel.connect(name)
            channel.sendall((json.dumps(request) + '\n').encode())
            with channel.makefile('r') as stream:
                line = stream.readline()
            if not line:
                raise RuntimeError('The retained connection closed without a result.')
            return json.loads(line)
    finally:
        os.chdir(old)
