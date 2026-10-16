import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
metrics = [
    "user.logins:1|c",
    "user.logins:2|c",
    "cpu.usage:85.5|g",
    "cpu.usage:+5|g|#host:server1",
    "request.latency:120|ms|#endpoint:/api",
    "request.latency:150|ms|#endpoint:/api",
    "request.latency:180|ms|#endpoint:/api",
]
for m in metrics:
    sock.sendto(m.encode('utf-8'), ("127.0.0.1", 8125))
