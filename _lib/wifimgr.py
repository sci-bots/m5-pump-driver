import gc
import machine
import network
import socket
import ure
import time
import ubinascii

unique_id = ubinascii.hexlify(machine.unique_id())
DEFAULT_SSID = "scibots-" + unique_id.decode('utf-8')
DEFAULT_PASSWORD = "microfluidics"
DEFAULT_AUTHMODE = 3  # WPA2


def send_header(client, status_code=200, content_length=None ):
    client.sendall("HTTP/1.0 {} OK\r\n".format(status_code))
    client.sendall("Content-Type: text/html\r\n")
    if content_length is not None:
        client.sendall("Content-Length: {}\r\n".format(content_length))
    client.sendall("\r\n")


def send_response(client, payload, status_code=200):
    content_length = len(payload)
    send_header(client, status_code, content_length)
    if content_length > 0:
        client.sendall(payload)
    client.close()
    

def handle_not_found(client, url):
    send_response(client, "Path not found: {}".format(url), status_code=404)


class WiFiManager:
    def __init__(self, profiles='wifi.dat'):
        self.profiles_path = profiles
        self.wlan_ap = network.WLAN(network.AP_IF)
        self.wlan_sta = network.WLAN(network.STA_IF)
        self.server_socket = None

    def get_connection(self):
        """return a working WLAN(STA_IF) instance or None

        .. versionchanged:: 0.8.2
            Do not start wifi configuration webserver if connection cannot be
            established. Instead, leave it up to the calling code to execute
            ``start()`` explicitly as needed.
        """
        # First check if there already is any connection:
        if self.wlan_sta.isconnected():
            return self.wlan_sta

        connected = False
        try:
            # ESP connecting to WiFi takes time, wait a bit and try again:
            time.sleep(3)
            if self.wlan_sta.isconnected():
                return self.wlan_sta

            # Read known network profiles from file
            profiles = self.read_profiles()

            # Search WiFis in range
            self.wlan_sta.active(True)
            networks = self.wlan_sta.scan()

            AUTHMODE = {0: "open", 1: "WEP", 2: "WPA-PSK", 3: "WPA2-PSK",
                        4: "WPA/WPA2-PSK"}
            for network_i in sorted(networks, key=lambda x: x[3],
                                    reverse=True):
                ssid, bssid, channel, rssi, authmode, hidden = network_i
                ssid = ssid.decode('utf-8')
                encrypted = authmode > 0
                authmode_label = AUTHMODE.get(authmode, '?')
                print("ssid: %s chan: %d rssi: %d authmode: %s" %
                      (ssid, channel, rssi, authmode_label))
                if encrypted:
                    if ssid in profiles:
                        password = profiles[ssid]
                        connected = self.do_connect(ssid, password)
                    else:
                        print("skipping unknown encrypted network")
                else:  # open
                    connected = self.do_connect(ssid, None)
                if connected:
                    break

        except OSError as e:
            print("exception", str(e))

        return self.wlan_sta if connected else None

    def read_profiles(self):
        with open(self.profiles_path) as f:
            lines = f.readlines()
        profiles = {}
        for line in lines:
            ssid, password = line.strip("\n").split(";")
            profiles[ssid] = password
        return profiles
    
    def write_profiles(self, profiles):
        lines = []
        for ssid, password in profiles.items():
            lines.append("%s;%s\n" % (ssid, password))
        with open(self.profiles_path, "w") as f:
            f.write(''.join(lines))
    
    def do_connect(self, ssid, password):
        self.wlan_sta.active(True)
        if self.wlan_sta.isconnected():
            return None
        print('Trying to connect to %s...' % ssid)
        self.wlan_sta.connect(ssid, password)
        for retry in range(100):
            connected = self.wlan_sta.isconnected()
            if connected:
                break
            time.sleep(0.1)
            print('.', end='')
        if connected:
            print('\nConnected. Network config: ', self.wlan_sta.ifconfig())
        else:
            print('\nFailed. Not Connected to: ' + ssid)
        return connected
    
    def handle_root(self, client):
        self.wlan_sta.active(True)
        while True:
            try:
                scan_result = self.wlan_sta.scan()
                break
            except Exception as exception:
                print(exception)

        ssids = sorted(ssid.decode('utf-8') for ssid, *_ in scan_result)
        send_header(client)
        client.sendall("""\
            <html>
                <h1 style="color: #5e9ca0; text-align: center;">
                    <span style="color: #ff0000;">
                        Wi-Fi Client Setup
                    </span>
                </h1>
                <form action="configure" method="post">
                    <table style="margin-left: auto; margin-right: auto;">
                        <tbody>
        """)
        while len(ssids):
            ssid = ssids.pop(0)
            client.sendall("""\
                            <tr>
                                <td colspan="2">
                                    <input type="radio" name="ssid" value="{0}" />{0}
                                </td>
                            </tr>
            """.format(ssid))
        client.sendall("""\
                            <tr>
                                <td>Password:</td>
                                <td><input name="password" type="password" /></td>
                            </tr>
                        </tbody>
                    </table>
                    <p style="text-align: center;">
                        <input type="submit" value="Submit" />
                    </p>
                </form>
                <p>&nbsp;</p>
                <hr />
                <h5>
                    <span style="color: #ff0000;">
                        Your ssid and password information will be saved into the
                        "%(filename)s" file in your ESP module for future usage.
                        Be careful about security!
                    </span>
                </h5>
                <hr />
                <h2 style="color: #2e6c80;">
                    Some useful infos:
                </h2>
                <ul>
                    <li>
                        Original code from <a href="https://github.com/cpopp/MicroPythonSamples"
                            target="_blank" rel="noopener">cpopp/MicroPythonSamples</a>.
                    </li>
                    <li>
                        This code available at <a href="https://github.com/tayfunulu/WiFiManager"
                            target="_blank" rel="noopener">tayfunulu/WiFiManager</a>.
                    </li>
                </ul>
            </html>
        """ % dict(filename=self.profiles_path))
        client.close()
    
    def handle_configure(self, client, request):
        match = ure.search("ssid=([^&]*)&password=(.*)", request)
    
        if match is None:
            send_response(client, "Parameters not found", status_code=400)
            return False
        # version 1.9 compatibility
        try:
            ssid = match.group(1).decode("utf-8").replace("%3F", "?").replace("%21", "!")
            password = match.group(2).decode("utf-8").replace("%3F", "?").replace("%21", "!")
        except Exception:
            ssid = match.group(1).replace("%3F", "?").replace("%21", "!")
            password = match.group(2).replace("%3F", "?").replace("%21", "!")
    
        if len(ssid) == 0:
            send_response(client, "SSID must be provided", status_code=400)
            return False
    
        if self.do_connect(ssid, password):
            response = """\
                <html>
                    <center>
                        <br><br>
                        <h1 style="color: #5e9ca0; text-align: center;">
                            <span style="color: #ff0000;">
                                ESP successfully connected to WiFi network %(ssid)s.
                            </span>
                        </h1>
                        <br><br>
                    </center>
                </html>
            """ % dict(ssid=ssid)
            send_response(client, response)
            try:
                profiles = self.read_profiles()
            except OSError:
                profiles = {}
            profiles[ssid] = password
            self.write_profiles(profiles)
    
            time.sleep(5)
    
            return True
        else:
            response = """\
                <html>
                    <center>
                        <h1 style="color: #5e9ca0; text-align: center;">
                            <span style="color: #ff0000;">
                                ESP could not connect to WiFi network %(ssid)s.
                            </span>
                        </h1>
                        <br><br>
                        <form>
                            <input type="button" value="Go back!" onclick="history.back()"></input>
                        </form>
                    </center>
                </html>
            """ % dict(ssid=ssid)
            send_response(client, response)
            return False
    
    def stop(self):
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None
    
    def start(self, port=80, ap_ssid=DEFAULT_SSID,
              ap_password=DEFAULT_PASSWORD, ap_authmode=DEFAULT_AUTHMODE):
        self.stop()
    
        self.wlan_ap.config(essid=ap_ssid, password=ap_password,
                            authmode=ap_authmode)
    
        self.server_socket = socket.socket()
        addr = ('0.0.0.0', '80')
        self.server_socket.bind(addr)
        self.server_socket.listen(1)

        gc.collect()
    
        self.wlan_sta.active(True)
        gc.collect()
        self.wlan_ap.active(True)
        gc.collect()
    
        print('Connect to WiFi ssid ' + ap_ssid + ', default password: ' +
              ap_password)
        print('and access the ESP via your favorite web browser at '
              '192.168.4.1.')
        print('Listening on:', addr)
    
        while True:
            if self.wlan_sta.isconnected():
                return True
    
            client, addr = self.server_socket.accept()
            gc.collect()
            try:
                client.settimeout(5.0)
    
                request = b""
                try:
                    while "\r\n\r\n" not in request:
                        request += client.recv(512)
                except OSError:
                    pass
    
                print("Request is: {}".format(request))
                if "HTTP" not in request:  # skip invalid requests
                    continue
    
                # version 1.9 compatibility
                try:
                    url = ure.search("(?:GET|POST) /(.*?)(?:\\?.*?)? HTTP",
                                     request).group(1).decode("utf-8")\
                                         .rstrip("/")
                except Exception:
                    url = ure.search("(?:GET|POST) /(.*?)(?:\\?.*?)? HTTP",
                                     request).group(1).rstrip("/")
                print("URL is {}".format(url))
    
                if url == "":
                    self.handle_root(client)
                elif url == "configure":
                    self.handle_configure(client, request)
                else:
                    handle_not_found(client, url)
    
            finally:
                client.close()