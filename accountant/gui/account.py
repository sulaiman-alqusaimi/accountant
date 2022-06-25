import wx
from .components import BaseFrame
import application
from .dialogs import AddProduct, PayDialog, EventsHistory
from .report_viewer import Report



class AccountViewer(wx.Panel):
	def __init__(self, parent, account):
		self.account = account
		parent.panels[0].Hide()
		super().__init__(parent)
		wx.StaticText(self, -1, "المعلومات الأساسية:")
		self.summary = wx.TextCtrl(self, -1, style=wx.TE_READONLY + wx.TE_MULTILINE + wx.HSCROLL)

		addButton = wx.Button(self, -1, "إضافة منتج...")
		addButton.Bind(wx.EVT_BUTTON, self.onAdd)
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
		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(backButton, 1)
		sizer.Add(self.summary, 1, wx.EXPAND)
		sizer1 = wx.BoxSizer(wx.HORIZONTAL)
		sizer1.Add(addButton, 1)
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
		AddProduct(self.Parent, self.account)
		self.display_summary()
	def onPay(self, event):
		PayDialog(self.Parent, self.account)
		self.display_summary()
	def display_summary(self):
		self.summary.SetValue(
f"""اسم العميل: {self.account.name}
رقم الهاتف: {self.account.phone}
الحساب الإجمالي: {round(self.account.total, 3)}
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
	def onBack(self, event):
		self.Hide()
		del self.Parent.panels[1]
		self.Parent.panels[0].Show()
		self.Parent.panels[0].SetFocus()
		self.Destroy()
