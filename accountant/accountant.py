import os
os.chdir(os.path.dirname(__file__))
import config
config.initialize()
from gui.main_window import MainWindow
import wx

import sys



def isOtherInstance():
	process = os.path.basename(sys.executable)
	isOther = False
	for p in psutil.process_iter():
		try:
			if p.name() == process and p.pid != os.getpid():
				isOther = True
				break
		except:
			pass
	return isOther



app = wx.App()




MainWindow()
app.MainLoop()