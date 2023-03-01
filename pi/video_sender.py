import io
import pickle
import socket
import struct
import zlib
from threading import Condition

import cv2
from libcamera import Transform
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput

normalSize = (1280, 720)
lowresSize = (800, 600)


class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

# Server socket
# create an INET, STREAMing socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_name = socket.gethostname()
host_ip = '192.168.0.115'
#host_ip= '10.42.0.1'
print('HOST IP:', host_ip)
port = 10050
socket_address = (host_ip, port)
print('Socket created')
# bind the socket to the host.
# The values passed to bind() depend on the address family of the socket
server_socket.bind(socket_address)
print('Socket bind complete')
# listen() enables a server to accept() connections
# listen() has a backlog parameter.
# It specifies the number of unaccepted connections that the system will allow before refusing new connections.
server_socket.listen(5)
print('Socket now listening')

print("Configure camera started")
picam2 = Picamera2()
config = picam2.create_video_configuration(main={"size": normalSize},
                                           lores={"size": lowresSize, "format": "YUV420"},
                                           transform=Transform(vflip=1))
picam2.configure(config)
output = StreamingOutput()
picam2.start_recording(JpegEncoder(), FileOutput(output))
print("Configure camera finished")
while True:
    client_socket, addr = server_socket.accept()
    print('Connection from:', addr)
    if client_socket:
        while True:
            frame = output.frame
            a = pickle.dumps(frame)
            message = struct.pack("Q", len(a)) + a
            try:
                client_socket.sendall(message)
            except:
                print("Connection refused")
                break

