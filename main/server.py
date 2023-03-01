#!/usr/bin/env diploma
from flask import Flask, render_template, Response
from object_detection import ObjectDetection

app = Flask(__name__, template_folder="templates")


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/video_feed')
def video_feed():
    resp = Response(get_img(), mimetype='multipart/x-mixed-replace; boundary=frame')
    resp.headers['Age'] = 0
    resp.headers['Cache-Control'] = 'no-cache, private'
    resp.headers['Pragma'] = 'no-cache'
    return resp


def get_img():
    while True:
        if stream.streaming:
            yield b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + stream.get_jpeg() + b'\r\n\r\n'


if __name__ == '__main__':
    stream = ObjectDetection('192.168.0.115', 10050)
    # stream = ObjectDetection('10.42.0.1', 10050)
    # starting flask server
    stream.start()
    app.run(host='0.0.0.0', port=8080, threaded=True, debug=False)
