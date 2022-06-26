import json
import application
from threading import Thread
import requests
import wx



def get_events(account, reverse=False):
		events = list(account.products)
		events.extend(account.payments)
		return sorted(events, key=lambda e: e.date, reverse=reverse)


def check_for_updates(quiet=False):
	url = "https://raw.githubusercontent.com/sulaiman-alqusaimi/accountant/master/update_info.json"
	try:
		r = requests.get(url)
		if r.status_code != 200:
			wx.MessageBox(
				"حدث خطأ ما أثناء الاتصال بخدمة العثور على التحديثات. تأكد من وجود اتصال مستقر بالإنترنت ثم عاود المحاولة", 
				"خطأ", 
				parent=wx.GetApp().GetTopWindow(), style=wx.ICON_ERROR
			) if not quiet else None
			return
		info = r.json()
		if application.version != info["version"]:
			message = wx.MessageBox("هناك تحديث جديد متوفر. هل ترغب في تنزيله الآن؟", "تحديث جديد", parent=wx.GetApp().GetTopWindow(), style=wx.YES_NO)
			url = info["url"]
			if message == wx.YES:
				from gui.update_dialog import UpdateDialog
				wx.CallAfter(UpdateDialog, wx.GetApp().GetTopWindow(), url)
			return
		wx.MessageBox("أنت تعمل الآن على آخر تحديث متوفر من التطبيق", "لا يوجد تحديث", parent=wx.GetApp().GetTopWindow()) if not quiet else None
	except requests.ConnectionError:
		wx.MessageBox(
			"حدث خطأ ما أثناء الاتصال بخدمة العثور على التحديثات. تأكد من وجود اتصال مستقر بالإنترنت ثم عاود المحاولة", 
			"خطأ", 
			parent=wx.GetApp().GetTopWindow(), style=wx.ICON_ERROR
		) if not quiet else None
