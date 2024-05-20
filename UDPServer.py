import json
import socket
import threading
from time import sleep


class UDPServer:
    def __init__(self, port: int):
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ip = '127.0.0.1'
        self.port = port
        self.serverSocket.bind((self.ip, self.port))
        print('UDP Server Started and Listening...')
        self.connected_users = set()
        self.data = list()
        threading.Thread(target=self.run).start()

    def run(self):
        while True:
            data, addr = self.serverSocket.recvfrom(1024 * 80)
            try:
                data = bytes.decode(data)
                data = json.loads(data)
                print(data, addr)
                if data['type'] == 'connect':
                    self.connected_users.add(addr)
                    self.serverSocket.sendto(json.dumps({'type': 'connected'}).encode(), addr)
                    sleep(0.5)

                    self.serverSocket.sendto(json.dumps({'type': 'data', 'data': self.data}).encode(), addr)
                    sleep(0.5)
                elif data['type'] == 'disconnect':
                    self.connected_users.discard(addr)
                    self.serverSocket.sendto(json.dumps({'type': 'disconnected'}).encode(), addr)
                    sleep(0.5)
                elif data['type'] == 'message' and addr in self.connected_users:
                    self.data.append(data['message'])
                    for user in self.connected_users:
                        self.serverSocket.sendto(json.dumps({'type': 'data', 'data': self.data}).encode(), user)
                        sleep(0.5)
                        print(self.data, 'sent')
                else:
                    self.serverSocket.sendto('404'.encode(), addr)
                    sleep(0.5)
            except Exception as e:
                print(e)

if __name__ == '__main__':
    server = UDPServer(8080)