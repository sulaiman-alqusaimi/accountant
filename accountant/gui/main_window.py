from .components import BaseFrame
import wx
import application
from .dialogs import NewAccountDialog, EditAccountDialog, ResultsDialog, SearchDialog
from database import get_accounts, delete_account, Account
from .account import AccountViewer
from utiles import check_for_updates, play
from threading import Thread





class ListBox(wx.ListBox):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.contextSetup()
		self.Bind(wx.EVT_CONTEXT_MENU, lambda e: self.PopupMenu(self.context) if self.Selection != -1 else None)
		hotkeys = wx.AcceleratorTable([
			(wx.ACCEL_CTRL, ord("E"), wx.ID_EDIT),
			(0, wx.WXK_NUMPAD_DELETE, wx.ID_DELETE),
			(0, wx.WXK_DELETE, wx.ID_DELETE),
			(0, wx.WXK_RETURN, wx.ID_OPEN),
		])
		self.SetAcceleratorTable(hotkeys)
	def delete(self, event):
		if self.Selection == -1:
			return
		message = wx.MessageBox("هل أنت متأكد من رغبتك في حذف هذا العميل؟", "حذف", style=wx.YES_NO, parent=wx.GetTopLevelParent(self))
		if not message == wx.YES:
			return
		account_id = self.GetClientData(self.Selection)
		delete_account(account_id)
		self.Delete(self.Selection)

	def contextSetup(self):
		self.context = wx.Menu()
		self.context.Append(wx.ID_EDIT, "تعديل معلومات العميل")
		self.context.Append(wx.ID_OPEN, "فتح الحساب")
		self.context.Append(wx.ID_DELETE, "حذف العميل")
		self.Bind(wx.EVT_MENU, self.onOpen, id=wx.ID_OPEN)
		self.Bind(wx.EVT_MENU, self.edit, id=wx.ID_EDIT)
		self.Bind(wx.EVT_MENU, self.delete, id=wx.ID_DELETE)
	def edit(self, event):
		account_id = self.GetClientData(self.Selection)
		account = Account(account_id)
		with EditAccountDialog(wx.GetTopLevelParent(self), account.name, account.phone, account_id) as dlg:
			res = dlg.ShowModal()
		if not res == account_id:
			return
		if hasattr(dlg, "new_name"):
			self.SetString(self.Selection, dlg.new_name)
	def onOpen(self, event):
		ac_id = self.GetClientData(self.Selection)
		account = Account(ac_id)
		self.Parent.Hide()
		viewer = AccountViewer(wx.GetApp().GetTopWindow(), account)
		play("open")



class MainPanel(wx.Panel):
	def __init__(self, parent):
		super().__init__(parent)
		wx.StaticText(self, -1, "قائمة العملاء:")
		sizer = wx.BoxSizer(wx.VERTICAL)
		self.accounts = ListBox(self, -1)
		sizer.Add(self.accounts)

		self.setData()
		try:
			self.accounts.Selection = 0
		except:
			pass
		addButton = wx.Button(self, wx.ID_ADD, "إضافة عميل...")
		addButton.Bind(wx.EVT_BUTTON, self.onAdd)
		searchButton = wx.Button(self, -1, "بحث...")
		searchButton.Bind(wx.EVT_BUTTON, self.onSearch)
		sizer.Add(addButton)
		sizer.Add(searchButton)
		hotkeys = wx.AcceleratorTable([
			(wx.ACCEL_CTRL, ord("N"), wx.ID_ADD),
			(wx.ACCEL_CTRL, ord("F"), searchButton.GetId())
		])
		self.SetAcceleratorTable(hotkeys)
		self.SetSizer(sizer)
		self.Parent.Sizer.Add(self)
		self.Layout()
		self.Parent.Sizer.Fit(self)
	def onAdd(self, event):
		with NewAccountDialog(self.Parent) as dlg:
			account_id = dlg.ShowModal()
			name = dlg.accountName.Value
		if hasattr(dlg, "saved"):
			self.accounts.Append(name, account_id)
			self.accounts.Selection = len(self.accounts.Strings)-1
		self.accounts.SetFocus()if not self.FindFocus() == self.accounts else None
	def setData(self):
		for account_id, name in get_accounts():
			total = Account(account_id).total
			total = round(total, 3) if total - int(total) != 0.0 else int(total)
			self.accounts.Append(f"{name}, المجموع {total} ريال", account_id)
	def onSearch(self, event):
		dlg = SearchDialog(self)
		if dlg.result:
			results = []
			for account in get_accounts():
				if dlg.result in account[1]:
					results.append(account)
			if not results:
				wx.MessageBox("لم يتم العثور على العميل المطلوب", "خطأ", wx.ICON_ERROR, self.Parent)
			else:
				viewer = ResultsDialog(self.Parent, results)
				if viewer.account:
					account = viewer.account
					for position in range(self.accounts.Count):
						if self.accounts.GetClientData(position) == account[0]:
							break

					self.accounts.Selection = position
					self.accounts.onOpen(None)


class MainWindow(BaseFrame):
	def __init__(self):
		super().__init__(None, title=application.name)
		self.SetSize(wx.GetDisplaySize())
		self.Maximize(True)
		sizer = wx.BoxSizer(wx.VERTICAL)
		self.SetSizer(sizer)
		self.panels = {0: MainPanel(self)}
		menubar = wx.MenuBar()
		mainMenu = wx.Menu()
		exitItem = mainMenu.Append(-1, "خروج")
		menubar.Append(mainMenu, "القائمة الرئيسية")
		self.SetMenuBar(menubar)
		self.Bind(wx.EVT_MENU, lambda e: wx.Exit(), exitItem)
		self.Show()
		t = Thread(target=check_for_updates, args=[True])
		t.daemon = True
		t.start()

