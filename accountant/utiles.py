import json
import application
from threading import Thread
import requests
import wx
from winsound import PlaySound
import os
from database import Product, Payment
from config import config_get
import pdfkit


def format_number(n):
	return round(n, 1) if n-int(n) != 0.0 else int(n)

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

def play(sound):
		path = os.path.join("sounds", f"{sound}.wav")
		PlaySound(path, 1)


def prepare_receet(obj):
	if isinstance(obj, Payment):
		template = \
		f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>إيصال دفع</title>
	<style>
		body {{
			font-family: Arial, sans-serif;
			background-color: #f4f4f4;
			margin: 0;
			padding: 0;
			display: flex;
			justify-content: center;
			align-items: center;
			min-height: 100vh;
		}}
		.receipt-container {{
			max-width: 400px;
			background-color: #fff;
			padding: 20px;
			border-radius: 8px;
			box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
		}}
		.header, .footer {{
			text-align: center;
			margin-bottom: 20px;
			color: #555;
		}}
		.header h2, .footer p {{
			margin: 0;
			font-weight: normal;
		}}
		.details {{
			margin-bottom: 15px;
		}}
		.details div {{
			display: block;
			justify-content: space-between;
			margin-bottom: 8px;
			font-size: 16px;
		}}
		.details div span {{
			color: #333;
		}}
		.highlight {{
			font-weight: bold;
			color: #007bff;
		}}
		.total {{
			display: flex;
			justify-content: space-between;
			font-size: 18px;
			font-weight: bold;
			margin-top: 15px;
		}}	
		</style>
</head>
<body>

<div class="receipt-container">
	<!-- Header Section -->
	<div class="header">
		<h2>إيصال دفع</h2>
		<p>اسم العميل: {obj.account.name}</p>
		<p>رقم الهاتف: {obj.phone}</p>
	</div>

	<!-- Payment Details -->
	<div class="details">
		<div>
			<span>التاريخ والوقت: </span>
			<span class="highlight">{obj.date.strftime("%d/%m/%Y %I:%M %p") } </span>
		</div>
		<div>
			<span>المبلغ المضاف: </span>
			<span class="highlight">{format_number(obj.amount)} ريال</span>
		</div>
		<div>
			<span>الحساب السابق: </span
			<span>{format_number(obj.account.total + obj.amount)} ريال</span>
		</div>
		<div class="total">
			<span>إجمالي الحساب: </span>
			<span class="highlight">{format_number(obj.account.total)} ريال</span>
		</div>
	</div>

	<!-- Footer Section -->
	<div class="footer">
		<p>شكراً لاستخدامكم خدماتنا</p>
	</div>
</div>

</body>
</html>
"""
	elif isinstance(obj, Product):
			template = \
		f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>إيصال المنتج</title>
	<style>
		body {{
			font-family: Arial, sans-serif;
			background-color: #f4f4f4;
			margin: 0;
			padding: 0;
			display: flex;
			justify-content: center;
			align-items: center;
			min-height: 100vh;
		}}
		.receipt-container {{
			max-width: 400px;
			background-color: #fff;
			padding: 20px;
			border-radius: 8px;
			box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
		}}
		.header, .footer {{
			text-align: center;
			margin-bottom: 20px;
			color: #555;
		}}
		.header h2, .footer p {{
			margin: 0;
			font-weight: normal;
		}}
		.details {{
			margin-bottom: 15px;
		}}
		.details div {{
			display: block;
			justify-content: space-between;
			margin-bottom: 8px;
			font-size: 16px;
		}}
		.details div span {{
			color: #333;
		}}
		.highlight {{
			font-weight: bold;
			color: #007bff;
		}}
		.total {{
			display: flex;
			justify-content: space-between;
			font-size: 18px;
			font-weight: bold;
			margin-top: 15px;
		}}	
		</style>
</head>
<body>

<div class="receipt-container">
	<!-- Header Section -->
	<div class="header">
		<h2>إيصال المنتج</h2>
		<p>اسم العميل: {obj.account.name}</p>
		<p>رقم الهاتف: {obj.phone}</p>
	</div>

	<!-- Payment Details -->
	<div class="details">
			<div>
			<span>اسم المنتج: </span
			<span>{obj.name}</span>
		</div>
		<div>
			<span>القيمة: </span>
			<span class="highlight">{format_number(obj.price)} ريال</span>
		</div>

		<div>
			<span>التاريخ والوقت: </span>
			<span class="highlight">{obj.date.strftime("%d/%m/%Y %I:%M %p") }</span>
		</div>
		<div class="total">
			<span>إجمالي الحساب الحالي: </span>
			<span class="highlight">{format_number(obj.account.total)} ريال</span>
		</div>
	</div>

	<!-- Footer Section -->
	<div class="footer">
		<p>شكراً لاستخدامكم خدماتنا</p>
	</div>
</div>

</body>
</html>
"""
	return template

def save_html_receet(data):
	if isinstance(data, Product):
		title = f"إيصال المنتج_رقم {data.id}_{data.account.name}.html"
		path = os.path.join(config_get("default_path"), data.account.name, "المنتجات")
	elif isinstance(data, Payment):
		title = f"إيصال الدفع_رقم {data.id}_{data.account.name}.html"
		path = os.path.join(config_get("default_path"), data.account.name, "المدفوعات")


	receet = prepare_receet(data)

	try:
		os.makedirs(path, exist_ok=True)
	except FileExistsError:
		pass
	path = os.path.join(path, title)
	with open(path, "w", encoding="utf-8") as file:
		file.write(receet)
	return path


def save_pdf_receet(data):
	if isinstance(data, Product):
		title = f"إيصال المنتج_رقم {data.id}_{data.account.name}.pdf"
		path = os.path.join(config_get("default_path"), data.account.name, "المنتجات")
	elif isinstance(data, Payment):
		title = f"إيصال الدفع_رقم {data.id}_{data.account.name}.pdf"
		path = os.path.join(config_get("default_path"), data.account.name, "المدفوعات")


	receet = prepare_receet(data)

	try:
		os.makedirs(path, exist_ok=True)
	except FileExistsError:
		pass
	path = os.path.join(path, title)
	exe = os.path.join(os.getcwd(), "wkhtmltopdf", "bin", "wkhtmltopdf.exe")
	config = pdfkit.configuration(wkhtmltopdf=exe)
	pdfkit.from_string(receet, path, configuration=config)
	return path