import socket
import select
import time
import sys

REMOTE_IP = "mytv2.duckdns.org"
REMOTE_PORT = 9000

LOCAL_TCP_IP = "127.0.0.1"
LOCAL_TCP_PORT = 9001

BUF_SIZE = 4096

def log(msg):
    print(msg)
    sys.stdout.flush()  # force output to appear immediately

def connect_local():
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((LOCAL_TCP_IP, LOCAL_TCP_PORT))
            s.setblocking(False)
            log(f"[OK] Local connected {LOCAL_TCP_IP}:{LOCAL_TCP_PORT}")
            return s
        except Exception as e:
            log(f"[WAIT] Local not ready: {e}")
            time.sleep(1)

def connect_remote():
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((REMOTE_IP, REMOTE_PORT))
            s.setblocking(False)
            log(f"[OK] Remote connected {REMOTE_IP}:{REMOTE_PORT}")
            return s
        except Exception as e:
            log(f"[WAIT] Remote failed: {e}")
            time.sleep(1)

def main():
    tcp_remote = connect_remote()
    tcp_local = connect_local()
    log("Relay running...")

    while True:
        rlist = [tcp_remote, tcp_local]
        readable, _, _ = select.select(rlist, [], [], 1)

        for s in readable:
            try:
                data = s.recv(BUF_SIZE)
            except Exception as e:
                log(f"Recv error: {e}")
                data = b""

            if not data:
                log(f"[CLOSED] {'REMOTE' if s is tcp_remote else 'LOCAL'} connection")
                # Close and reconnect automatically
                s.close()
                if s is tcp_remote:
                    tcp_remote = connect_remote()
                else:
                    tcp_local = connect_local()
                continue

            # Detect heartbeat (single 0x00 byte) from remote
            if s is tcp_remote and data == b"\x00":
                log("[HEARTBEAT] from remote, not forwarding to local")
                # Optional: respond to server heartbeat if required
                try:
                    tcp_remote.sendall(data)
                except:
                    pass
                continue  # skip forwarding to local

            # Forward remote → local
            if s is tcp_remote:
                try:
                    tcp_local.sendall(data)
                    log(f"REMOTE → LOCAL {len(data)} bytes")
                except Exception as e:
                    log(f"Forward error LOCAL: {e}")
                    tcp_local.close()
                    tcp_local = connect_local()

            # Forward local → remote
            elif s is tcp_local:
                try:
                    tcp_remote.sendall(data)
                    log(f"LOCAL → REMOTE {len(data)} bytes")
                except Exception as e:
                    log(f"Forward error REMOTE: {e}")
                    tcp_remote.close()
                    tcp_remote = connect_remote()

if __name__ == "__main__":
    main()

