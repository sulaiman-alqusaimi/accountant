

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




class TextSettingsDialog(wx.Dialog):
	def __init__(self, parent, title, content, account, field, multiline=False):
		super().__init__(parent, title=title, size=(400, 250))

		main_sizer = wx.BoxSizer(wx.VERTICAL)

		lbl = wx.StaticText(self, label=f"{content}:")
		main_sizer.Add(lbl, 0, wx.ALL, 10)

		# ===== TextCtrl =====
		style = wx.TE_PROCESS_ENTER
		if multiline:
			style |= wx.TE_MULTILINE

		self.txt_value = wx.TextCtrl(
			self,
			value=getattr(account, field),
			style=style
		)

		main_sizer.Add(self.txt_value, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

		btn_sizer = wx.BoxSizer(wx.HORIZONTAL)

		btn_save = wx.Button(self, wx.ID_OK, label="حفظ")
		btn_cancel = wx.Button(self, wx.ID_CANCEL, label="إلغاء")

		btn_save.SetDefault()

		btn_sizer.AddStretchSpacer()
		btn_sizer.Add(btn_save, 0, wx.RIGHT, 5)
		btn_sizer.Add(btn_cancel, 0)

		main_sizer.Add(btn_sizer, 0, wx.ALL | wx.EXPAND, 10)
		btn_save.Bind(wx.EVT_BUTTON, self.on_save)
		self.SetSizer(main_sizer)
		self.Layout()
		self.Centre()
	def on_save(self, event):
		if self.txt_value:
			
			self.res = self.txt_value.Value
			self.EndModal(wx.ID_SAVE)
		else:
			self.EndModal(wx.ID_CANCEL)
			


class AccountMaximumSettingsDialog(wx.Dialog):
	def __init__(self, parent, account):
		self.account = account
		super().__init__(parent, title="تعيين سقف الحساب")
		self.CenterOnParent()
		p = wx.Panel(self)
		stateLabel = wx.StaticText(p, -1, "سقف الحساب: ")
		self.maximumState = wx.Choice(p, -1, choices=["بلا سقف", "تعيين سقف"])
		self.maximumState.Selection = 1 if self.account.maximum else 0
		self.amountLabel = wx.StaticText(p, -1, "قيمة السقف: ")
		self.maximumAmount = wx.TextCtrl(p, -1)
		self.togleAmount()

		saveButton = wx.Button(p, -1, "حفظ")
		saveButton.SetDefault()
		cancelButton = wx.Button(p, wx.ID_CANCEL, "إلغاء")
		sizer = wx.BoxSizer(wx.VERTICAL)
		grid = wx.GridSizer(3, 2, 5)
		grid.AddMany([
			(stateLabel, 1),
			(self.maximumState, 1, wx.EXPAND),
			(self.amountLabel, 1),
			(self.maximumAmount, 1, wx.EXPAND),
			(saveButton, 1),
			(cancelButton, 1)
])
		sizer.Add(grid)
		p.SetSizer(sizer)
		self.maximumState.Bind(wx.EVT_CHOICE, self.onChoice)
		saveButton.Bind(wx.EVT_BUTTON, self.onSave)

	def togleAmount(self):
		if self.account.maximum is not None:
			self.maximumAmount.Value = str(self.account.maximum)
		else:
			self.maximumAmount.Value = "100000"
			self.amountLabel.Hide()
			self.maximumAmount.Hide()
	def onChoice(self, event):
		selection = self.maximumState.Selection

		if selection == 1:
			self.amountLabel.Show()
			self.maximumAmount.Show()
			self.maximumAmount.SetFocus()
		else:
			self.amountLabel.Hide()
			self.maximumAmount.Hide()

	def onSave(self, event):
		if self.maximumState.Selection == 0:
			self.maximum = None
		else:
			value = float(self.maximumAmount.Value)
			self.maximum = value if value - int(value) != 0.0 else int(value)
		self.EndModal(wx.ID_SAVE)