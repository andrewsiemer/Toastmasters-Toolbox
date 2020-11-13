import sys
import random
from PyQt5 import QtWidgets,uic
from PyQt5.QtCore import QThread
import requests

# Add a click value and tell host
def Handle_Click_Add():
    r = requests.post('http://10.211.55.10:5000/add_SDF', json={})

# User Quit function
def Quit():
    thread.terminate()
    thread.wait()
    App.quit()

# Start UI application
App = QtWidgets.QApplication([])
UI=uic.loadUi("SDF_app.ui")

# Handle UI interaction
UI.btn_add.clicked.connect(Handle_Click_Add)
UI.actionQuit.triggered.connect(Quit)

# Start UI application
UI.show()

sys.exit(App.exec_())