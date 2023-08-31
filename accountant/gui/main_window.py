from .components import BaseFrame
import wx
import application
from .dialogs import NewAccountDialog, EditAccountDialog, ResultsDialog, SearchDialog
from database import get_accounts, delete_account, get_account_by_id as Account
from .account import AccountViewer
from utiles import check_for_updates, play
from config import config_get, config_set
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
			self.Parent.sort()
			for n in range(self.Count):
				if self.GetClientData(n) == account_id:
					self.Selection = n
					break


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
		wx.StaticText(self, -1, "فرز حسب: ")
		self.sortBy = wx.Choice(self, -1, choices=["تاريخ الإضافة", "الاسم", "المجموع"])
		self.sortBy.Selection = int(config_get("sort_by"))
		sizer.Add(self.sortBy)
		self.directionBox = wx.RadioBox(self, -1, "الاتجاه", choices=["تصاعدي", "تنازلي"])
		self.directionBox.Selection = int(config_get("direction"))
		sizer.Add(self.directionBox)
		self.setData()
		addButton = wx.Button(self, wx.ID_ADD, "إضافة عميل...")
		addButton.Bind(wx.EVT_BUTTON, self.onAdd)
		searchButton = wx.Button(self, -1, "بحث...")
		searchButton.Bind(wx.EVT_BUTTON, self.onSearch)
		self.sortBy.Bind(wx.EVT_CHOICE, self.onSort)
		self.directionBox.Bind(wx.EVT_RADIOBOX, self.onDirection)
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
	def onDirection(self, event):
		print("triggred")
		config_set("direction", self.directionBox.Selection)
		self.sort()
	def sort(self):
		self.accounts.Clear()
		self.setData()

	def onAdd(self, event):
		with NewAccountDialog(self.Parent) as dlg:
			account_id = dlg.ShowModal()
			name = dlg.accountName.Value
		if hasattr(dlg, "saved"):
			self.sort()
			for n in range(self.accounts.Count):
				if self.accounts.GetClientData(n) == account_id:
					self.accounts.Selection = n
					break

		self.accounts.SetFocus()if not self.FindFocus() == self.accounts else None
	def onSort(self, event):
		config_set("sort_by", self.sortBy.Selection)
		self.sort()
	def setData(self):
		accounts = get_accounts()
		sort = self.sortBy.Selection
		if sort == 1:
			accounts = sorted(accounts, key=lambda e: e.name)
		elif sort == 2:
			accounts = sorted(accounts, key=lambda e: e.total)

		direction=int(config_get("direction"))
		if direction == 1:
			accounts.reverse()
		for account in accounts:
			total = account.total
			total = round(total, 3) if total - int(total) != 0.0 else int(total)
			self.accounts.Append(f"{account.name}, المجموع {total} ريال", account.id)
		try:
			self.accounts.Selection = 0
		except:
			pass

	def onSearch(self, event):
		dlg = SearchDialog(self)
		if dlg.result:
			results = []
			for account in get_accounts():
				if dlg.result in account.name:
					results.append(account)
			if not results:
				wx.MessageBox("لم يتم العثور على العميل المطلوب", "خطأ", wx.ICON_ERROR, self.Parent)
			else:
				viewer = ResultsDialog(self.Parent, results)
				if viewer.account:
					account = viewer.account
					for position in range(self.accounts.Count):
						if self.accounts.GetClientData(position) == account.id:
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

