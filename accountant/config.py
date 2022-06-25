import paths
import os
import configparser



defaults = {
	
}

def initialize():
	try:
		os.makedirs(paths.data_path)

	except FileExistsError:
		pass
	if not os.path.exists(paths.settings_path):
		config = configparser.ConfigParser()
		config.add_section("settings")
		for key, value in defaults.items():
			config["settings"][key] = str(value)
		with open(paths.settings_path, "w") as file:
			config.write(file)

def string_to_bool(string):
	if string == "True":
		return True
	elif string == "False":
		return False
	else:
		return string


def config_get(string):
	config = configparser.ConfigParser()
	config.read(os.path.join(settings_path, "settings.ini"))
	try:
		value = config["settings"][string]
		return string_to_bool(value)
	except KeyError:
		config_set(string, defaults[string])
		return defaults[string]


def config_set(key, value):
	config = configparser.ConfigParser()
	config.read(os.path.join(settings_path, "settings.ini"))
	config["settings"][key] = str(value)
	with open(os.path.join(settings_path, "settings.ini"), "w") as file:
		config.write(file)

