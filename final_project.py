import sys
import cv2
import numpy
import cv2
from PyQt5 import QtWidgets, QtGui, uic
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
from PyQt5.QtWidgets import QFileDialog
import time
from fer import FER
from stopwatch import Stopwatch
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 

# Global Variables
camera_flip = False
track_face = False

class VideoThread(QThread):
    new_frame_signal = pyqtSignal(numpy.ndarray)
    global timer, first_warning, second_warning, third_warning

    def run(self):
        # Capture from Webcam
        width = 320
        height = 240
        video_capture_device = cv2.VideoCapture(0)
        video_capture_device.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        video_capture_device.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        # Create facial expression recognition object
        detector = FER()

        # FPS Variables
        fps = 0
        sampled_frames = 0
        start_time = time.time()
        while True:
            if self.isInterruptionRequested():
                video_capture_device.release()
                return
            else:
                # Set Timer Label
                UI.timer_lbl.setText('%02d:%02d' % (timer.duration // 60, timer.duration % 60))
                if timer.duration >= third_warning * 60:
                    BG_Color = "rgb(250,200,200);" 
                elif timer.duration >= second_warning * 60:
                    BG_Color = "rgb(250,250,200);" 
                elif timer.duration >= first_warning * 60:
                    BG_Color = "rgb(200,250,200);" 
                else:
                    BG_Color = "rgb(240,240,240);" 
                UI.timer_lbl.setStyleSheet("QLabel {background-color :" + BG_Color + "color : rgb(0,0,0);}")

                # Calculate FPS
                current_time = time.time()
                if current_time >= start_time + 1:
                    fps = sampled_frames
                    sampled_frames = 0
                    start_time = time.time()
                else:
                    sampled_frames += 1
                UI.menuFPS.setTitle("FPS: " + str(round(fps)))

                # Capture current frame
                ret, frame = video_capture_device.read()
                
                # Get result of FER
                result = detector.detect_emotions(frame)

                """ # IF face found in frame
                if result:
                    bounding_box = result[0]["box"]
                    emotions = result[0]["emotions"]

                    # Display face bounding box
                    cv2.rectangle(
                        frame,
                        (bounding_box[0], bounding_box[1]),
                        (bounding_box[0] + bounding_box[2], bounding_box[1] + bounding_box[3]),
                        (0, 155, 255),
                        2,
                    )
                    
                    # Display emotion scores on image
                    for idx, (emotion, score) in enumerate(emotions.items()):
                        color = (211, 211, 211) if score < 0.1 else (0, 255, 0)
                        emotion_score = "{}: {}".format(
                            emotion, "{:.2f}".format(score) if score > 0.01 else ""
                        )
                        cv2.putText(
                            frame,
                            emotion_score,
                            (bounding_box[0], bounding_box[1] + bounding_box[3] + 30 + idx * 15),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            color,
                            1,
                            cv2.LINE_AA,
                        ) """

                if ret:
                    self.new_frame_signal.emit(frame)

def Update_Image(frame):
    height, width, channel = frame.shape
    bytesPerLine = 3 * width
    h = UI.lblOutput.height()
    w = UI.lblOutput.width()
    qImg = QtGui.QImage(frame.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
    qImg = qImg.rgbSwapped()
    # Scale image to widget size maintaining aspect ratio
    UI.lblOutput.setPixmap(QtGui.QPixmap(qImg).scaled(w,h,Qt.KeepAspectRatio,Qt.FastTransformation))

def Start_Timer():
    global timer, state

    if state == 'Ready' or state == 'Paused':
        UI.parameters_action.setEnabled(False)
        UI.import_file_action.setEnabled(False)

        UI.start_btn.hide()
        UI.pause_btn.show()
        UI.stop_btn.show()

        print('Starting Timer...')
        timer.start()
        state = 'Running'
        print('Currint State: ' + state)

def Stop_Timer():
    global timer, state

    if state == 'Running' or state == 'Paused':
        UI.pause_btn.hide()
        UI.resume_btn.hide()
        UI.stop_btn.hide()

        print('Stopping Timer...')
        timer.stop()
        state = 'End'
        print('Currint State: ' + state)

def Pause_Timer():
    global timer, state

    if state == 'Running':
        UI.pause_btn.hide()
        UI.resume_btn.show()

        print('Pausing Timer...')
        timer.stop()
        state = 'Paused'
        print('Currint State: ' + state)

def Resume_Timer():
    global timer, state

    if state == 'Paused':
        UI.resume_btn.hide()
        UI.pause_btn.show()

        print('Starting Timer...')
        timer.start()
        state = 'Running'
        print('Currint State: ' + state)

def Restart_Timer():
    global timer, state

    if state != 'Ready':
        UI.start_btn.show()
        UI.stop_btn.hide()
        UI.pause_btn.hide()
        UI.resume_btn.hide()

        print('Restarting Timer...')
        timer.reset()
        state = 'Ready'
        print('Currint State: ' + state)

def Show_Parameters():
    global first_warning,second_warning, third_warning
    UI.parameters_action.setEnabled(False)
    UI.start_btn.hide()
    UI.timer_lbl.hide()

    print('Show Parameters...')
    UI.first_lbl.show()
    UI.first_warning.show()
    UI.second_lbl.show()
    UI.second_warning.show()
    UI.third_lbl.show()
    UI.third_warning.show()
    UI.save_btn.show()

    UI.first_warning.setValue(first_warning)
    UI.second_warning.setValue(second_warning)
    UI.third_warning.setValue(third_warning)

def Hide_Parameters():
    global first_warning,second_warning, third_warning
    UI.parameters_action.setEnabled(True)
    UI.start_btn.show()
    UI.timer_lbl.show()

    first_warning = UI.first_warning.value()
    second_warning = UI.second_warning.value()
    third_warning = UI.third_warning.value()

    print('Hiding Parameters...')
    UI.first_lbl.hide()
    UI.first_warning.hide()
    UI.second_lbl.hide()
    UI.second_warning.hide()
    UI.third_lbl.hide()
    UI.third_warning.hide()
    UI.save_btn.hide()

def Import_File():
    filename = QFileDialog.getOpenFileName()
    path = filename[0]
    print(path)

    UI.teleprompter.setText('')
    with open(path, "r") as f: 
        for line in f:
            UI.teleprompter.append(line)

def Restart():
    Restart_Timer()

    UI.parameters_action.setEnabled(True)
    UI.import_file_action.setEnabled(True)

def Quit():
    thread.requestInterruption()
    thread.wait()
    App.quit()

App = QtWidgets.QApplication([])
UI=uic.loadUi("final_project.ui")

UI.stop_btn.hide()
UI.pause_btn.hide()
UI.resume_btn.hide()
state = 'Ready'

first_warning = 3.0
second_warning = 4.0
third_warning = 5.0
UI.first_lbl.hide()
UI.first_warning.hide()
UI.second_lbl.hide()
UI.second_warning.hide()
UI.third_lbl.hide()
UI.third_warning.hide()
UI.save_btn.hide()
UI.save_btn.clicked.connect(Hide_Parameters)

timer = Stopwatch()
timer.reset()
UI.start_btn.clicked.connect(Start_Timer)
UI.stop_btn.clicked.connect(Stop_Timer)
UI.pause_btn.clicked.connect(Pause_Timer)
UI.resume_btn.clicked.connect(Resume_Timer)

UI.parameters_action.triggered.connect(Show_Parameters)
UI.import_file_action.triggered.connect(Import_File)
UI.restart_action.triggered.connect(Restart)
UI.quit_action.triggered.connect(Quit)

UI.show()

thread = VideoThread()
thread.new_frame_signal.connect(Update_Image)
thread.start()

sys.exit(App.exec_())