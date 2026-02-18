import asyncio
import time

TCP_MAIN = 9000       # main TCP client (heartbeat)
TCP_FORWARD = 9001
BUFFER_SIZE = 4096
HEARTBEAT_TIMEOUT = 2.0  # send heartbeat if idle > 2s

tcp_main_clients = set()
tcp_forward_clients = set()
tcp_main_last = {}  # last received time for heartbeat


async def handle_tcp_main(reader, writer):
    addr = writer.get_extra_info("peername")
    tcp_main_clients.add(writer)
    tcp_main_last[writer] = time.time()
    print(f"TCP 9000 connected: {addr}")

    async def heartbeat_check():
        while writer in tcp_main_clients:
            elapsed = time.time() - tcp_main_last[writer]
            if elapsed > HEARTBEAT_TIMEOUT:
                try:
                    writer.write(b"\x00")
                    await asyncio.wait_for(writer.drain(), timeout=0.01)
                    tcp_main_last[writer] = time.time()
                except Exception:
                    break
            await asyncio.sleep(0.1)

    asyncio.create_task(heartbeat_check())

    try:
        while True:
            data = await reader.read(BUFFER_SIZE)
            if data:
                tcp_main_last[writer] = time.time()
                if data == b"\x00":
                    continue
                # forward to all TCP_FORWARD clients
                for f_client in list(tcp_forward_clients):
                    try:
                        f_client.write(data)
                        await asyncio.wait_for(f_client.drain(), timeout=0.01)
                    except Exception:
                        tcp_forward_clients.discard(f_client)
            else:
                await asyncio.sleep(0.01)
    except Exception as e:
        print(f"TCP 9000 error: {e}")
    finally:
        print(f"TCP 9000 disconnected: {addr}")
        tcp_main_clients.discard(writer)
        tcp_main_last.pop(writer, None)
        try:
            writer.close()
        except:
            pass


async def handle_tcp_forward(reader, writer):
    addr = writer.get_extra_info("peername")
    tcp_forward_clients.add(writer)
    print(f"TCP 19999 connected: {addr}")

    try:
        while True:
            data = await reader.read(BUFFER_SIZE)
            if data:
                # forward to all TCP_MAIN clients
                for main_client in list(tcp_main_clients):
                    try:
                        main_client.write(data)
                        await asyncio.wait_for(main_client.drain(), timeout=0.01)
                    except Exception:
                        tcp_main_clients.discard(main_client)

                # forward to other TCP_FORWARD clients
                for f_client in list(tcp_forward_clients):
                    if f_client != writer:
                        try:
                            f_client.write(data)
                            await asyncio.wait_for(f_client.drain(), timeout=0.01)
                        except Exception:
                            tcp_forward_clients.discard(f_client)
            else:
                await asyncio.sleep(0.01)
    except Exception as e:
        print(f"TCP 19999 error: {e}")
    finally:
        print(f"TCP 19999 disconnected: {addr}")
        tcp_forward_clients.discard(writer)
        try:
            writer.close()
        except:
            pass


async def main():
    # Start both servers concurrently
    server_main = await asyncio.start_server(handle_tcp_main, "0.0.0.0", TCP_MAIN)
    server_forward = await asyncio.start_server(handle_tcp_forward, "0.0.0.0", TCP_FORWARD)

    print(f"TCP listening on {TCP_MAIN} (main with heartbeat)")
    print(f"TCP listening on {TCP_FORWARD} (forward clients)")

    async with server_main, server_forward:
        await asyncio.gather(
            server_main.serve_forever(),
            server_forward.serve_forever()
        )


if __name__ == "__main__":
    asyncio.run(main())

