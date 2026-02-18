# p2p-to-client-server
This is a python code with server and client to convert p2p connection to client server architecture

# Usage
Run python server using python3 server-tcp.py and open port 9000 (for host code to connect to) and 9001 (for client to connect to) then run the host-tcp.py on host device by python3 host-tcp.py

# For Warcraft 3 TFT and ROC on PVPGN
For now it works with one client and one host only as it doesn't support more that 2 players
1-The server runs first
2-Host must change game port to 9001
3-The host creates a game on PVPGN server
4-address_translation.conf file must add "PUBLIC_IP_OF_HOST:9001  IP_OF_SERVER:9001  NONE  ANY"
5-client connects to game on lobby

# Concept
In PVPGN server there is no nat traversal for hosted games from players,this solves this problem by making client connects to server then server forwards the connection to host by tcp tunnel initiated from host to server using the host code then it is forwarded to local 9001 port on host

