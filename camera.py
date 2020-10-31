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
            thread3.start()
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
                receiver_address = ['sphnixdass@gmail.com', 'carolin.s@kotak.com', 'selvgnb@rbos.co.uk', 'carolins82@gmail.com']
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
        
        startflag = False

        while self.isrunning:
            #print("ssss")
            v,im = self.camera.read()
            im = cv2.rotate(im, cv2.cv2.ROTATE_180)
            orgimg = im
            if startflag == False:
                orgimg2 = im
                startflag = True
                
            s = im.shape
            font = cv2.FONT_HERSHEY_SIMPLEX
            bottomLeftCornerOfText = (10,s[0]-10)
            fontScale = 1
            fontColor = (20,200,20)
            lineType = 2

            cv2.putText(im,datetime.datetime.now().isoformat().split(".")[0],bottomLeftCornerOfText,font,fontScale,fontColor, lineType)

            fwflag = fwflag + 1
            grayA = cv2.cvtColor(orgimg, cv2.COLOR_BGR2GRAY)
            grayB = cv2.cvtColor(orgimg2, cv2.COLOR_BGR2GRAY)
            thresh = 127
            im_bw = cv2.threshold(grayA, thresh, 255, cv2.THRESH_BINARY)[1]
            im_bw2 = cv2.threshold(grayB, thresh, 255, cv2.THRESH_BINARY)[1]
            out_arr = np.logical_xor(im_bw, im_bw2)
            print("Logical calculation : ", np.count_nonzero(out_arr==True))



            # 5. Compute the Structural Similarity Index (SSIM) between the two
            #    images, ensuring that the difference image is returned
            (score, diff) = compare_ssim(grayA, grayB, full=True)
            diff = (diff * 255).astype("uint8")

            # 6. You can print only the score if you want
            #print("Matching Score: {}".format(score))
            if (score < 0.96):
                fwflag = 0
                framecount = framecount + 1
                if framecount > 100:
                    framecount = 1
                f = open("/home/pi/Desktop/flask-video-stream-master/static/alert.txt", "w")
                f.write(str(framecount))
                f.close()
            
                #date_string = datetime.datetime.now().strftime("%d%m%Y-%H%M%s")
                #print("intruder ", date_string)
                cv2.imwrite("/home/pi/Desktop/flask-video-stream-master/static/" + str(framecount) + ".jpg", im)
                thGmail = framecount
                thBuzzer = True

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
        