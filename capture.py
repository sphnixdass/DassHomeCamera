import cv2
import datetime, time
from pathlib import Path

def capture_and_save(im):
    s = im.shape
    # Add a timestamp
    font = cv2.FONT_HERSHEY_SIMPLEX
    bottomLeftCornerOfText = (10,s[0]-10)
    fontScale = 1
    fontColor = (20,200,20)
    lineType = 2

    cv2.putText(im,datetime.datetime.now().isoformat().split(".")[0],bottomLeftCornerOfText,font,fontScale,fontColor, lineType)

    #m = 0
    #p = Path("static")
    #for imp in p.iterdir():
    #    if imp.suffix == ".png" and imp.stem != "last":
    #        num = imp.stem.split("_")[1]
    #        try:
    #            num = int(num)
    #            if num>m:
    #                m = num
    #        except:
    #            print("Error reading image number for",str(imp))
    #m +=1
    #lp = Path("static/last.png")
    #if lp.exists() and lp.is_file():
    #    np = Path("static/img_{}.jpg".format(m))
    #    np.write_bytes(lp.read_bytes())
    
    framecount = 0
    f = open("/home/pi/Desktop/flask-video-stream-master/static/alert.txt", "r")
    framecount = int(f.readline())
    framecount = framecount + 1
            
    cv2.imwrite("static/" + str(framecount) + ".jpg",im)
    f = open("/home/pi/Desktop/flask-video-stream-master/static/alert.txt", "w")
    f.write(str(framecount))
    f.close()
    

if __name__=="__main__":
    capture_and_save()
    print("done")