import sys, time, cv2, numpy, random, flask, pygame
from fer import FER
from stopwatch import Stopwatch
from PyQt5 import QtWidgets, QtGui, uic
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread

class FlaskServer(QThread):
    """ Flask Server Class for Speech Disfluency Feedback
    
    Communicates with SDF_app.py."""

    Flask_App = flask.Flask(__name__)
    Flask_App.config['DEBUG'] = False
    pygame.mixer.init()
    pygame.mixer.music.load("chime.wav")

    def run(self):
       self.Flask_App.run(host='0.0.0.0')

    # Handle add_SDF POST request
    @Flask_App.route('/add_SDF', methods=['POST'])
    def set_count():
        if UIThread.Get_State() == 'Running':
            UIThread.Add_SDF()
            pygame.mixer.music.play()
            

        return flask.jsonify(flask.request.json)

class AppThread(QThread):
    """ Qt Application Class & UI Thread

    Updates UI based on state of the system."""
    App = QtWidgets.QApplication([])
    UI=uic.loadUi('app.ui')
    UI.show()

    def __init__(self):
        super(AppThread, self).__init__()

        # UI Action Handler
        self.UI.start_btn.clicked.connect(self.Start_Timer)
        self.UI.stop_btn.clicked.connect(self.Stop_Timer)
        self.UI.pause_btn.clicked.connect(self.Pause_Timer)
        self.UI.resume_btn.clicked.connect(self.Resume_Timer)
        self.UI.stop_btn.clicked.connect(Generate_Report)
        self.UI.save_btn.clicked.connect(self.Hide_Parameters)
        self.UI.parameters_action.triggered.connect(self.Show_Parameters)
        self.UI.import_file_action.triggered.connect(self.Import_File)
        self.UI.restart_action.triggered.connect(self.Restart)
        self.UI.quit_action.triggered.connect(Quit) 

        # Initialize Timer
        self.timer = Stopwatch()
        self.timer.reset()

        # Timer Warnings
        self.first_warning = 3.0
        self.second_warning = 4.0
        self.third_warning = 5.0

        # Speech Disfluency Feedback count
        self.SDF = 0

        # Set Initial UI State
        self.UI.stop_btn.hide()
        self.UI.pause_btn.hide()
        self.UI.resume_btn.hide()
        self.UI.first_lbl.hide()
        self.UI.first_warning.hide()
        self.UI.second_lbl.hide()
        self.UI.second_warning.hide()
        self.UI.third_lbl.hide()
        self.UI.third_warning.hide()
        self.UI.save_btn.hide()

        # System State
        self.state = 'Ready'
    
    def Get_State(self):
        """Get_State -> state (string)"""
        return self.state
    
    def Get_SDF(self):
        """Get_SDF -> SDF (string)"""
        return self.SDF

    def Add_SDF(self):
        """Adds one SDF"""
        self.SDF += 1

    def Get_Speech_Time(self):
        """Get_Speech_Timer -> timer (Stopwatch)"""
        return self.timer

    def Get_Speech_Notes(self):
        """Get_Speech_Notes -> UI.speech_notes (string)"""
        return self.UI.speech_notes.toPlainText()

    def Update_Image(self, frame):
        """Update webcam feed on UI"""
        height, width, channel = frame.shape
        bytesPerLine = 3 * width
        h = self.UI.webcam_lbl.height()
        w = self.UI.webcam_lbl.width()
        qImg = QtGui.QImage(frame.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
        qImg = qImg.rgbSwapped()
        # Scale image to widget size maintaining aspect ratio
        self.UI.webcam_lbl.setPixmap(QtGui.QPixmap(qImg).scaled(w,h,Qt.KeepAspectRatio,Qt.FastTransformation))

    def Start_Timer(self):
        """Starts speech timer

        Must be in 'Ready' or 'Paused' state."""
        if self.state == 'Ready' or self.state == 'Paused':
            self.UI.parameters_action.setEnabled(False)
            self.UI.import_file_action.setEnabled(False)

            self.UI.start_btn.hide()
            self.UI.pause_btn.show()
            self.UI.stop_btn.show()

            print('Starting Timer...')
            self.timer.start()
            self.state = 'Running'
            print('Currint State: ' + self.state)

    def Stop_Timer(self):
        """Stops speech timer & ends speech
        
        Must be in 'Running' or 'Paused' state."""
        if self.state == 'Running' or self.state == 'Paused':
            self.UI.pause_btn.hide()
            self.UI.resume_btn.hide()
            self.UI.stop_btn.hide()

            print('Stopping Timer...')
            self.timer.stop()
            self.state = 'End'
            print('Currint State: ' + self.state)

    def Pause_Timer(self):
        """Pauses speech timer
        
        Must be in 'Running' state."""
        if self.state == 'Running':
            self.UI.pause_btn.hide()
            self.UI.resume_btn.show()

            print('Pausing Timer...')
            self.timer.stop()
            self.state = 'Paused'
            print('Currint State: ' + self.state)

    def Resume_Timer(self):
        """Resumes speech timer
        
        Must be in 'Paused' state."""
        if self.state == 'Paused':
            self.UI.resume_btn.hide()
            self.UI.pause_btn.show()

            print('Starting Timer...')
            self.timer.start()
            self.state = 'Running'
            print('Currint State: ' + self.state)

    def Restart_Timer(self):
        """Restarts speech timer"""
        if self.state != 'Ready':
            self.UI.start_btn.show()
            self.UI.stop_btn.hide()
            self.UI.pause_btn.hide()
            self.UI.resume_btn.hide()

            print('Restarting Timer...')
            self.timer.reset()
            self.state = 'Ready'
            print('Currint State: ' + self.state)
    
    def Show_Parameters(self):
        """Shows speech timer parameters"""
        self.UI.parameters_action.setEnabled(False)
        self.UI.start_btn.hide()
        self.UI.timer_lbl.hide()

        print('Showing Parameters...')
        self.UI.first_lbl.show()
        self.UI.first_warning.show()
        self.UI.second_lbl.show()
        self.UI.second_warning.show()
        self.UI.third_lbl.show()
        self.UI.third_warning.show()
        self.UI.save_btn.show()

        self.UI.first_warning.setValue(self.first_warning)
        self.UI.second_warning.setValue(self.second_warning)
        self.UI.third_warning.setValue(self.third_warning)

    def Hide_Parameters(self):
        """Hides & saves speech timer parameters"""
        self.UI.parameters_action.setEnabled(True)
        self.UI.start_btn.show()
        self.UI.timer_lbl.show()

        self.first_warning = self.UI.first_warning.value()
        self.second_warning = self.UI.second_warning.value()
        self.third_warning = self.UI.third_warning.value()

        print('Hiding Parameters...')
        self.UI.first_lbl.hide()
        self.UI.first_warning.hide()
        self.UI.second_lbl.hide()
        self.UI.second_warning.hide()
        self.UI.third_lbl.hide()
        self.UI.third_warning.hide()
        self.UI.save_btn.hide()

    def Import_File(self):
        """Imports .txt file from file browser"""
        filename = QFileDialog.getOpenFileName()
        path = filename[0]
        print(path)

        self.UI.speech_notes.setText('')
        with open(path, 'r') as f: 
            for line in f:
                self.UI.speech_notes.append(line)

    def Restart(self):
        """Resets all speech parameters to defaults"""
        self.Restart_Timer()
        FeedThread.Reset_FER()
        self.SDF = 0

        self.UI.parameters_action.setEnabled(True)
        self.UI.import_file_action.setEnabled(True)

    def run(self):
        """Updates UI elements while app is running"""
        while(1):
            # Set SDF Label
            self.UI.sdf_lbl.setText('Filler used ' + str(self.SDF) + ' times')

            # Set Timer Label
            self.UI.timer_lbl.setText('%02d:%02d' % (self.timer.duration // 60, self.timer.duration % 60))
            if self.timer.duration >= self.third_warning * 60:
                BG_Color = 'rgb(250,200,200);' 
            elif self.timer.duration >= self.second_warning * 60:
                BG_Color = 'rgb(250,250,200);' 
            elif self.timer.duration >= self.first_warning * 60:
                BG_Color = 'rgb(200,250,200);' 
            else:
                BG_Color = 'rgb(240,240,240);' 
            self.UI.timer_lbl.setStyleSheet('QLabel {background-color :' + BG_Color + 'color : rgb(0,0,0);}')

            self.UI.fer_lbl.setText('You look ' + FeedThread.Get_Curr_Emotion())

            self.UI.menuFPS.setTitle('FPS: ' + str(FeedThread.Get_FPS()))
            
            time.sleep(0.1)
            
class VideoThread(QThread):
    """Image Processing Class & Video Thread"""
    new_frame_signal = pyqtSignal(numpy.ndarray)

    def __init__(self):
        super(VideoThread, self).__init__()
        
        # FPS
        self.FPS = 0

        # FER
        self.curr_emotion = 'neutral'
        self.emotions = [0,0,0,0,0,0,0]
        self.analyzed_frames = 0

    def Get_Curr_Emotion(self):
        """Get_Curr_Emotion -> curr_emotion (string)"""
        return self.curr_emotion

    def Get_FPS(self):
        """Get_FPS -> FPS (int)"""
        return self.FPS
    
    def Get_Speech_Emotions(self):
        """Get_Speech_Emotions -> emotions (list), analyzed_frames (int)"""
        return self.emotions, self.analyzed_frames
    
    def Reset_FER(self):
        """Resets stored emotion data"""
        self.emotions = [0,0,0,0,0,0,0]
        self.analyzed_frames = 0

    def run(self):
        """Catures Webcam Frame & Processes Emotions"""
        # Capture from Webcam
        width = 320
        height = 240
        video_capture_device = cv2.VideoCapture(0)
        video_capture_device.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        video_capture_device.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        # Create facial expression recognition object
        detector = FER()

        # FPS Variables
        sampled_frames = 0
        start_time = time.time()

        while True:
            if self.isInterruptionRequested():
                video_capture_device.release()
                return
            else:
                # Calculate FPS
                current_time = time.time()
                if current_time >= start_time + 1:
                    self.FPS = sampled_frames
                    sampled_frames = 0
                    start_time = time.time()
                else:
                    sampled_frames += 1

                # Capture current frame
                ret, frame = video_capture_device.read()
                
                # Get result of FER
                result = detector.detect_emotions(frame)
                if result:
                    self.curr_emotion = 'neutral'
                    emotion_score = 0.5
                    for idx, (emotion, score) in enumerate(result[0]['emotions'].items()):
                        # Update Top Emotion in Current Frame
                        if score > emotion_score and score > 0.6:
                            self.curr_emotion = emotion
                            emotion_score = score
                        
                        # Store All Emotions from Current Frame
                        if UIThread.Get_State() == 'Running':
                            self.analyzed_frames += 1
                            self.emotions[idx] += score
                    if UIThread.Get_State() == 'Running':
                        self.analyzed_frames += 1 
                        
                if ret:
                    self.new_frame_signal.emit(frame)

def Generate_Report():
    """Generates a Report of Speech Data
    
    File is stored in Reports/ with timestamp."""
    filename = 'Reports/Speech-' + str(round(time.time())) + '.txt'
    print('Generating Report @ ' + filename + '...')
    f = open(filename, 'w')
    f.write('Toastmasters Toolbox Speech Report\n\n')

    # Get Time of Speech
    f.write('Speech Time\n')
    f.write(str(UIThread.Get_Speech_Time()) + '\n\n')

    # Get Captured Emotions from Speech
    emotions, analyzed_frames = FeedThread.Get_Speech_Emotions()
    f.write('Facial Expression Recognition\n')
    if analyzed_frames > 0:
        f.write('Angry: ' + str(round((emotions[0]/analyzed_frames)*100)) + '%\n')
        f.write('Disgust: ' + str(round((emotions[1]/analyzed_frames)*100)) + '%\n')
        f.write('Fear: ' + str(round((emotions[2]/analyzed_frames)*100)) + '%\n')
        f.write('Happy: ' + str(round((emotions[3]/analyzed_frames)*100)) + '%\n')
        f.write('Sad: ' + str(round((emotions[4]/analyzed_frames)*100)) + '%\n')
        f.write('Surprise: ' + str(round((emotions[5]/analyzed_frames)*100)) + '%\n')
        f.write('Neutral: ' + str(round((emotions[6]/analyzed_frames)*100)) + '%\n\n')
    else:
        f.write('Facial Expression Recognition not detected.\n')

    # Get SDF Count from Speech
    f.write('Speech Disfluency Feedback\n')
    f.write(str(UIThread.Get_SDF()) + ' filler words spoken\n\n')

    # Get Speech Notes from Speech
    f.write('Speech Notes\n')
    f.write(UIThread.Get_Speech_Notes())
    
    f.close()

def Quit():
    """Closes application safetly"""
    FeedThread.requestInterruption()
    FeedThread.wait()
    SDFThread.terminate()
    SDFThread.wait()
    UIThread.terminate()
    UIThread.wait()
    UIThread.App.quit()

if __name__ == '__main__': 

    # Start UI in new AppThread
    UIThread = AppThread()
    UIThread.start()

    # Start Video in new FeedThread
    FeedThread = VideoThread()
    FeedThread.new_frame_signal.connect(UIThread.Update_Image)
    FeedThread.start()

    # Start Flask in new SDFThread
    SDFThread = FlaskServer()
    SDFThread.start()

    sys.exit(UIThread.App.exec_())