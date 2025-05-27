import socket
import struct
UDP_IP = "0.0.0.0"
UDP_PORT = 1234
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
while True:
    data, addr = sock.recvfrom(4096)
    to_print = "\n".join(str(i) for (i,) in struct.iter_unpack("<I", data))
    to_print += "\n======================================\n"

    print(len(data))
