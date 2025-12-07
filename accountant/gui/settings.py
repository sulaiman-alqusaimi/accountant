

import wx
from config import config_get, config_set


class SettingsDialog(wx.Dialog):
	def __init__(self, parent):
		super().__init__(parent)
		
		self.SetTitle("إعدادات البرنامج")
		self.InitUI()
		self.SetSize((400, 200))
		self.Center()

	def InitUI(self):
		main_sizer = wx.BoxSizer(wx.VERTICAL)
		
		path_sizer = wx.BoxSizer(wx.HORIZONTAL)
		path_sizer.Add(wx.StaticText(self, -1, "المسار الافتراضي:"))
		self.path_ctrl = wx.TextCtrl(self, style=wx.TE_READONLY|wx.TE_MULTILINE|wx.HSCROLL)
		self.path_ctrl.Value = config_get("default_path")
		change_button = wx.Button(self, label="تغيير...")
		path_sizer.Add(self.path_ctrl, proportion=1, flag=wx.ALL | wx.EXPAND, border=5)
		path_sizer.Add(change_button, flag=wx.ALL, border=5)
		
		
		main_sizer.Add(path_sizer, flag=wx.ALL | wx.EXPAND, border=10)
		button_sizer = self.CreateButtonSizer(wx.OK | wx.CANCEL)

		main_sizer.Add(button_sizer, flag=wx.ALL | wx.ALIGN_RIGHT, border=10)
		
		self.SetSizer(main_sizer)
		self.path_ctrl.SetFocus()
		change_button.Bind(wx.EVT_BUTTON, self.onChange)
	def onChange(self, event):
		path = wx.DirSelector("", self.path_ctrl.Value, parent=self)
		if path:
			self.path_ctrl.Value = path