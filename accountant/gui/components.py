import wx


class BaseFrame(wx.Frame):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.Centre()
		self.Bind(wx.EVT_CLOSE, lambda e: wx.Exit())
