import cv2
import threading
import time
import logging
import datetime, time
from skimage.measure import compare_ssim
import imutils
from gpiozero import Buzzer
from time import sleep
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import numpy as np


logger = logging.getLogger(__name__)

thread = None
thread2 = None
thread3 = None
thBuzzer = False
buzzer = Buzzer(17)
thGmail = 0

class Camera:
    def __init__(self,fps=20,video_source=0):
        logger.info(f"Initializing camera class with {fps} fps and video_source={video_source}")
        self.fps = fps
        self.video_source = video_source
        self.camera = cv2.VideoCapture(self.video_source)
        # We want a max of 5s history to be stored, thats 5s*fps
        self.max_frames = 5*self.fps
        self.frames = []
        self.isrunning = False
        self.currentImage = 1
        self.CaptureImage = False
    def run(self):
        logging.debug("Perparing thread")
        global thread
        global thread2
        if thread is None:
            logging.debug("Creating thread")
            thread = threading.Thread(target=self._capture_loop,daemon=True)
            thread2 = threading.Thread(target=self._buzzer_loop,daemon=True)
            thread3 = threading.Thread(target=self._gmail_loop,daemon=True)
            logger.debug("Starting thread")
            self.isrunning = True
            thread.start()
            thread2.start()
            #thread3.start()
            logger.info("Thread started")

    def _buzzer_loop(self):
        global thBuzzer
        global buzzer
        while self.isrunning:
            if thBuzzer == True:
                #buzzer = Buzzer(17)
                #print(str(thBuzzer))
                thBuzzer = False
                buzzer.on()
                sleep(2)
                buzzer.off()
                thBuzzer = False
                #print(str(thBuzzer))
    def _gmail_loop(self):
        global thGmail

        while self.isrunning:
            if thGmail != 0:
                html = """\
                <html>
                  <body>
                    <p>Hi,<br>
                       Intruder has been dected on Dass's Home!!!!<br>
                       
                    </p>
                    <h2>Dass's Home AI security systeam</h2>
                    <p> <a href="http://183.82.36.26:5010">Click here for live stream!</a> </p>
                    <img id="img" src="http://183.82.36.26:5010/static/dass.jpg" style="border: 3px solid black">
                    
                  </body>
                </html>
                """

                html = html.replace("dass.jpg", str(thGmail) + ".jpg")
                #The mail addresses and password
                sender_address = 'sphnixdass@gmail.com'
                sender_pass = 'tailoymewuzueuri'
                receiver_address = ['sphnixdass@gmail.com', 'carolin.s@kotak.com', 'carolins82@gmail.com']
                #Setup the MIME
                message = MIMEMultipart()
                message['From'] = sender_address
                message['To'] = ", ".join(receiver_address)
                message['Subject'] = 'Intruder alert!!!.'   #The subject line
                #The body and the attachments for the mail
                message.attach(MIMEText(html, 'html'))
                #Create SMTP session for sending the mail
                session = smtplib.SMTP('smtp.gmail.com', 587) #use gmail with port
                session.starttls() #enable security
                session.login(sender_address, sender_pass) #login with mail_id and password
                text = message.as_string()
                session.sendmail(sender_address, receiver_address, text)
                session.quit()
                print('Mail Sent')
                thGmail = 0
                #print(str(thBuzzer))

    def _capture_loop(self):
        global thBuzzer
        global thGmail
        dt = 1/self.fps
        logger.debug("Observation started")
        fwflag = 0
        framecount = 0
        f = open("/home/pi/Desktop/flask-video-stream-master/static/alert.txt", "r")
        framecount = int(f.readline())
        self.currentImage = framecount
        
        startflag = False

        while self.isrunning:
            #print("ssss")
            v,im = self.camera.read()
            im = cv2.rotate(im, cv2.cv2.ROTATE_180)
            orgimg = im.copy()
            if startflag == False:
                orgimg2 = im.copy()
                startflag = True
                
            s = im.shape
            font = cv2.FONT_HERSHEY_SIMPLEX
            bottomLeftCornerOfText = (10,s[0]-10)
            fontScale = 1
            fontColor = (20,200,20)
            lineType = 2

            cv2.putText(im,datetime.datetime.now().isoformat().split(".")[0],bottomLeftCornerOfText,font,fontScale,fontColor, lineType)

            fwflag = fwflag + 1
            grayA = cv2.cvtColor(orgimg.copy(), cv2.COLOR_BGR2GRAY)
            grayB = cv2.cvtColor(orgimg2.copy(), cv2.COLOR_BGR2GRAY)
            grayA[0:120] = 1
            grayA[:,:250] = 1
            #grayA[:50] = 1
            grayB[0:120] = 1
            grayB[:,:250] = 1





            # 5. Compute the Structural Similarity Index (SSIM) between the two
            #    images, ensuring that the difference image is returned
            (score, diff) = compare_ssim(grayA, grayB, full=True)
            diff = (diff * 255).astype("uint8")

            thresh = cv2.threshold(diff, 0, 255,
                cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
            cnts, hie = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE)
            #cnts = cnts[0] if imutils.is_cv2() else cnts[1]
            #im = thresh
            savedflag = False
            for c in cnts:
                (x, y, w, h) = cv2.boundingRect(c)
                if (y < 410 and w > 10 and h > 20 and w < 300 and h < 300 and len(cnts) < 15 and savedflag == False) or self.CaptureImage == True:
                #if y < 410 and w > 10 and h > 20 and len(cnts) < 20:
                    print(len(cnts), x, y, w, h)
                    self.CaptureImage = False
                
                    cv2.rectangle(im, (x, y), (x + w, y + h), (50, 50, 255), 3)
                    fwflag = 0
                    framecount = framecount + 1
                    if framecount > 100:
                        framecount = 1
                    self.currentImage = framecount
                    f = open("/home/pi/Desktop/flask-video-stream-master/static/alert.txt", "w")
                    f.write(str(framecount))
                    f.close()
            
                    cv2.imwrite("/home/pi/Desktop/flask-video-stream-master/static/" + str(framecount) + ".jpg", im)
                    thGmail = framecount
                    thBuzzer = True
                    savedflag = True


  #  cv2.rectangle(imageB, (x, y), (x + w, y + h), (0, 0, 255), 2)
    

            # 6. You can print only the score if you want
            #print("Matching Score: {}".format(score))
            #if (score < 0.96):

            orgimg2 = orgimg
            
            if v:
                if len(self.frames)==self.max_frames:
                    self.frames = self.frames[1:]
                self.frames.append(im)
            time.sleep(dt)
        logger.info("Thread stopped successfully")

    def stop(self):
        logger.debug("Stopping thread")
        self.isrunning = False
    def get_frame(self, _bytes=True):
        if len(self.frames)>0:
            if _bytes:
                img = cv2.imencode('.jpg',self.frames[-1])[1].tobytes()
            else:
                img = self.frames[-1]
        else:
            f = open("/home/pi/Desktop/flask-video-stream-master/static/alert.txt", "r")
            framecount = int(f.readline())
            with open("static/" + str(framecount) + ".jpg","rb") as f:
                img = f.read()
        return img
        