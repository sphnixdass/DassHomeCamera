#!/usr/bin/python3

from flask import Flask, render_template, send_from_directory, Response
from flask_socketio import SocketIO
from pathlib import Path
from capture import capture_and_save
from camera import Camera
import argparse, logging, logging.config, conf
from time import sleep

logging.config.dictConfig(conf.dictConfig)
logger = logging.getLogger(__name__)

camera = Camera()
camera.run()

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app, ping_timeout=10, ping_interval=5)


@socketio.on('my event')
def handle_my_custom_event(data):
    print('received json: ' + str(data))
    tempvar = 0
    
    while True:
        if tempvar != camera.currentImage:
            sleep(1)
            socketio.emit('ImageUpdate', str(camera.currentImage))
            tempvar = camera.currentImage

@socketio.on('captureimage')
def handle_captureimage(data):
    print('captureimage'  + str(data))
    camera.CaptureImage = True

            

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering or Chrome Frame,
    and also to cache the rendered page for 10 minutes
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers["Cache-Control"] = "public, max-age=0"
    return r

@app.route("/")
def entrypoint():
    logger.debug("Requested /")
    return render_template("index.html")

@app.route("/r")
def capture():
    logger.debug("Requested capture")
    im = camera.get_frame(_bytes=False)
    capture_and_save(im)
    return render_template("send_to_init.html")

@app.route("/images/last")
def last_image():
    logger.debug("Requested last image")
    p = Path("images/last.png")
    if p.exists():
        r = "last.png"
    else:
        logger.debug("No last image")
        r = "not_found.jpeg"
    return send_from_directory("images",r)


def gen(camera):
    logger.debug("Starting stream")
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/png\r\n\r\n' + frame + b'\r\n')

@app.route("/stream")
def stream_page():
    logger.debug("Requested stream page")
    return render_template("stream.html")

@app.route("/video_feed")
def video_feed():
    return Response(gen(camera),
        mimetype="multipart/x-mixed-replace; boundary=frame")

if __name__=="__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-p','--port',type=int,default=5010, help="Running port")
    parser.add_argument("-H","--host",type=str,default='0.0.0.0', help="Address to broadcast")
    args = parser.parse_args()
    logger.debug("Dass Server Started")
    #app.run(host=args.host,port=args.port)
    socketio.run(app,host=args.host,port=args.port)
    
