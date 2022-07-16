
import wx

from utiles import play
from .components import BaseFrame
import application
from .dialogs import AddProduct, PayDialog, EventsHistory, AccountSettingsDialog
from .report_viewer import Report



class AccountViewer(wx.Panel):
	def __init__(self, parent, account):
		self.account = account
		parent.panels[0].Hide()
		super().__init__(parent)
		wx.StaticText(self, -1, "المعلومات الأساسية:")
		self.summary = wx.TextCtrl(self, -1, style=wx.TE_READONLY + wx.TE_MULTILINE + wx.HSCROLL)
		settingsButton = wx.Button(self, -1, "إعدادات الحساب...")
		settingsButton.Bind(wx.EVT_BUTTON, self.onSettings)
		self.addButton = wx.Button(self, -1, "إضافة منتج...")
		self.addButton.Enabled = self.account.active
		self.addButton.Bind(wx.EVT_BUTTON, self.onAdd)
		payButton = wx.Button(self, -1, "ادفع...")
		payButton.Bind(wx.EVT_BUTTON, self.onPay)
		eventsButton = wx.Button(self, -1, "تحرير عمليات الحساب")
		eventsButton.Bind(wx.EVT_BUTTON, self.onEvents)
		reportButton = wx.Button(self, -1, "عرض التقرير")
		reportButton.Bind(wx.EVT_BUTTON, self.onReport)
		clearButton = wx.Button(self, -1, "تصفير الحساب")
		clearButton.Bind(wx.EVT_BUTTON, self.onClear)
		backButton = wx.Button(self, -1, "رجوع")
		backButton.Bind(wx.EVT_BUTTON, self.onBack)
		hotkeys = wx.AcceleratorTable([
			(wx.ACCEL_ALT, ord("S"), settingsButton.GetId()),
			(wx.ACCEL_ALT, ord("A"), self.addButton.GetId()),
			(wx.ACCEL_ALT, ord("P"), payButton.GetId()),
			(wx.ACCEL_ALT, ord("E"), eventsButton.GetId()),
			(wx.ACCEL_ALT, ord("R"), reportButton.GetId()),
			(wx.ACCEL_ALT, ord("C"), clearButton.GetId())
])
		self.SetAcceleratorTable(hotkeys)
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(backButton, 1)
		sizer.Add(self.summary, 1, wx.EXPAND)
		sizer1 = wx.BoxSizer(wx.HORIZONTAL)
		sizer1.Add(settingsButton, 1)
		sizer1.Add(self.addButton, 1)
		sizer1.Add(payButton, 1)
		sizer1.Add(eventsButton, 1)
		sizer1.Add(reportButton, 1)
		sizer1.Add(clearButton, 1)
		sizer.Add(sizer1, 1, wx.EXPAND)
		self.SetSizer(sizer)
		self.Bind(wx.EVT_CHAR_HOOK, self.onHook)
		self.summary.Bind(wx.EVT_SET_FOCUS, self.onFocus)
		self.display_summary()
		self.Parent.panels[1] = self
		self.Parent.Sizer.Add(self)
		self.Layout()
		self.Parent.Sizer.Fit(self)
		self.summary.SetFocus()

	def onAdd(self, event):
		if not self.account.active:
			return
		AddProduct(self.Parent, self.account)
		self.display_summary()
	def onPay(self, event):
		PayDialog(self.Parent, self.account)
		self.display_summary()
	def display_summary(self):
		status = "نشط" if self.account.active else "غير نشط"
		maximum = f"{self.account.maximum if self.account.maximum - int(self.account.maximum) != 0.0 else int(self.account.maximum)} ريال" if self.account.maximum else "لم يتم تعيينه"
		self.summary.SetValue(
f"""اسم العميل: {self.account.name}
رقم الهاتف: {self.account.phone}
الحساب الإجمالي: {round(self.account.total, 3) if self.account.total - int(self.account.total) != 0.0 else int(self.account.total)} ريال
حالة الحساب: {status}
سقف الحساب: {maximum}
""")
	def onHook(self, event):
		if event.KeyCode == wx.WXK_ESCAPE:
			self.onBack(None)
		else:
			event.Skip()
	def onReport(self, event):
		Report(self.Parent, self.account)

	def onEvents(self, event):
		EventsHistory(self.Parent, self.account)


	def onFocus(self, event):
		event.Skip()
		self.display_summary()

	def onClear(self, event):
		if wx.MessageBox(f"أمتأكد من رغبتك في إفراغ بيانات العميل {self.account.name}?", "تصفير الحساب", wx.YES_NO, self.Parent) == wx.YES:
			self.account.products = []
			self.account.payments = []
	def onSettings(self, event):
		AccountSettingsDialog(self.Parent, self.account)
		self.display_summary()
		self.addButton.Enabled = self.account.active
	def onBack(self, event):
		self.Hide()
		del self.Parent.panels[1]
		self.Parent.panels[0].Show()
		self.Parent.panels[0].SetFocus()
		self.Destroy()
		play("close")