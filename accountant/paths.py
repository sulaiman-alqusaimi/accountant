import os
import application

if os.path.exists(os.path.join(os.getcwd(), "unins000.exe")):
	base_dir = os.path.join(os.getenv("appdata"), application.english_name)
else:
		base_dir = os.path.join(os.getcwd(), "applicationData")

update_path = os.path.join(base_dir, "updates")

data_path = os.path.join(base_dir, "data")
settings_path = os.path.join(base_dir, "settings.ini")
