#!/usr/bin/env diploma
import socket
import pickle
import struct
import threading
import cv2
import imutils
import numpy as np


class ObjectDetection(threading.Thread):
    def __init__(self, hostname, port):
        threading.Thread.__init__(self)
        self.connected = False
        self.hostname = hostname
        self.port = port
        self.running = False
        self.streaming = False
        self.jpeg = None
        # Loading model
        self.net = cv2.dnn.readNet('models/MobileNetSSD_deploy.prototxt.txt',
                                   'models/MobileNetSSD_deploy.caffemodel')
        self.classes = []
        with open("models/coco.names", "r") as f:
            self.classes = [line.strip() for line in f.readlines()]
        self.colors = np.random.uniform(0, 255, size=(len(self.classes), 3))
        # Leave that lines for investigation
        # net.setPreferableBackend(cv2.dnn.DNN_BACKEND_HALIDE)
        # net.setPreferableTarget(cv2.dnn.DNN_TARGET_OPENCL)
        # print(cv2.getBuildInformation())

    def run(self):
        # Establish connect using socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((self.hostname, self.port))
        payload_size = struct.calcsize("Q")

        self.running = True
        while self.running:
            data = b""
            while True:
                while len(data) < payload_size:
                    # Receive package
                    packet = client_socket.recv(4 * 1024)
                    if not packet:
                        break
                    self.connected = True
                    data += packet

                packed_msg_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack("Q", packed_msg_size)[0]

                while len(data) < msg_size:
                    data += client_socket.recv(4 * 1024)

                frame_data = data[:msg_size]
                data = data[msg_size:]
                frame = pickle.loads(frame_data)

                if frame is not None:
                    a = frame.find(b'\xff\xd8')
                    b = frame.find(b'\xff\xd9')
                    if a != -1 and b != -1:
                        jpg = frame[a:b + 2]
                        i = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                        i = imutils.resize(i, width=1620)

                        # Grab the frame dimensions and convert it to a blob
                        (h, w) = i.shape[:2]
                        blob = cv2.dnn.blobFromImage(cv2.resize(i, (1620, 1080)),
                                                     0.007843, (300, 300), 127.5)

                        # Pass the blob through the network and obtain the detections and predictions
                        self.net.setInput(blob)
                        detections = self.net.forward()
                        # loop over the detections
                        for j in np.arange(0, detections.shape[2]):
                            # extract the confidence (i.e., probability) associated with
                            # the prediction
                            confidence = detections[0, 0, j, 2]

                            # filter out weak detections by ensuring the `confidence` is
                            # greater than the minimum confidence
                            if confidence > 0.3:
                                # extract the index of the class label from the
                                # `detections`, then compute the (x, y)-coordinates of
                                # the bounding box for the object
                                idx = int(detections[0, 0, j, 1])
                                box = detections[0, 0, j, 3:7] * np.array([w, h, w, h])
                                (startX, startY, endX, endY) = box.astype("int")

                                # draw the prediction on the frame
                                label = "{}: {:.2f}%".format(self.classes[idx],
                                                             confidence * 100)
                                cv2.rectangle(i, (startX, startY), (endX, endY),
                                              self.colors[idx], 2)
                                y = startY - 15 if startY - 15 > 15 else startY + 15

                                cv2.putText(i, label, (startX, y),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colors[idx], 2)
                        # show the output frame
                        # update image with new frame
                        ret, jpeg = cv2.imencode('.jpg', i)
                        self.jpeg = jpeg
                        self.streaming = True

    def stop(self):
        self.running = False

    def get_jpeg(self):
        if self.jpeg is not None:
            return self.jpeg.tobytes()

    def is_connected(self):
        return self.connected
