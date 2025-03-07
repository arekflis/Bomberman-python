import socket
import threading
import time

IP = "0.0.0.0"
PORT = 40000
ROWS, COLS = 17, 17

# Create socket 
UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

# Set adress and port value
server_adress = (IP, PORT)

# Socket start
UDPServerSocket.bind(server_adress)

# Set timeout for socket -> time for messages
UDPServerSocket.settimeout(10)

print("UDP Server up and waiting for players!")

numberPlayers = 0 # number of players in the queue
playerAddresses = [] # their adresses
player_ports = []
queue_time = time.time() # queue time

ROUNDS = 4

def give_player_ids(readyPlayers):
    playerId = 1
    for address in playerAddresses:
      message = str(playerId) + str(readyPlayers)
      UDPServerSocket.sendto(message.encode(), address)
      playerId+=1
     
def get_players_ready(readyPlayers):
        connected_players = []
        print(readyPlayers)
        while len(connected_players) < readyPlayers:
            try:
                message, address = UDPServerSocket.recvfrom(1024)
                print(f"Wiadomość {message.decode()} z adresu {address}")
                if message.decode() not in connected_players:
                    connected_players.append(message.decode())
            except:
                pass
        print(connected_players)
        game_over = False
        t = threading.Thread(target=receive_data, args=(game_over,))
        t.start()
        t.join()

def start_game(readyPlayers):
    t1 = threading.Thread(target=give_player_ids, args=(readyPlayers,))
    t1.start()
    t2 = threading.Thread(target=get_players_ready, args=(readyPlayers,))
    t2.start()
    t1.join()
    t2.join()

    
def receive_data(game_over):
    for address in playerAddresses:
        player_ports.append(address[1])


    start_round = time.time() + 7
    roundNumber = 1
    message = "NewRound" + str(roundNumber) + str(start_round)
    t = threading.Thread(target=broadcast_data, args=(message,))
    t.start()
    t.join()
    UDPServerSocket.settimeout(0.5)
    while roundNumber <= ROUNDS:
        if time.time() - start_round > 180:
            roundNumber += 1
            start_round = time.time() + 7
            text = "NewRound"
            if roundNumber == 5:
                text = "EndGame"
            message = text + str(roundNumber) + str(start_round)
            t = threading.Thread(target=broadcast_data, args=(message,))
            t.start()
            t.join()
        
        try:
            message, address = UDPServerSocket.recvfrom(1024)
            player_port = address[1]
            if player_port in player_ports:
                message = message.decode()
                print(f"Wiadomość: {message}")
                t = threading.Thread(target=game_logic, args=(message,address,player_port))
                t.start()
                t.join()
            else:
                print("dupa zbita")
                pass
            
        except socket.timeout:
            pass

                
def broadcast_data(new_message):
    for address in playerAddresses:
        UDPServerSocket.sendto(new_message.encode(), address)

    

def game_logic(message, address, player_port):
    player_id = message[0]
    row = message[1:3]
    col = message[3:5]
    action = message[5:]

    if action == "rt":
        col = int(col) + 1
        col = str(col)
        if len(col) < 2:
            col = "0" + col
    elif action == "lt":
        col = int(col) - 1
        col = str(col)
        if len(col) < 2:
            col = "0" + col
    elif action == "up":
        row = int(row) - 1
        row = str(row)
        if len(row) < 2:
            row = "0" + row
    elif action == "dn":
        row = int(row) + 1
        row = str(row)
        if len(row) < 2:
            row = "0" + row
    elif action == "bm":
        pass
    elif action == "dc":
        playerAddresses.remove(address)
        player_ports.remove(player_port)
    
    new_message = player_id+row+col+action+str(time.time())
    print(f"Wiadomość serwera: {new_message}")
    t = threading.Thread(target=broadcast_data,args=(new_message,))
    t.start()
    t.join()

    
    
    
def queue(numberPlayers,playerAddresses,queue_time): 
    while(True):
        # player join the queue
        try:
            message, address = UDPServerSocket.recvfrom(1024)
            numberPlayers += 1
            playerAddresses.append(address)

            print(f'Client {address} joined the queue')

            # server response
            message = "You have joined the queue! Please, wait for other players!"
            UDPServerSocket.sendto(message.encode(), address)
        except:
            print("Nobody joined the queue")
        
        print(numberPlayers)
        # game conditions
        if time.time() - queue_time > 10:
            if numberPlayers > 0 and numberPlayers % 2 == 0:
                # player has to confirm his participation 
                message = "All players joined the queue! Are you ready?"
                for playerAddress in playerAddresses:
                    UDPServerSocket.sendto(message.encode(), playerAddress)
                
                # check if all responses from players are OK
                readyPlayers = 0
                while(readyPlayers != len(playerAddresses)):
                    message, address = UDPServerSocket.recvfrom(1024)
                    if(message.decode() == "yes"):
                        readyPlayers += 1
                    else: # remove player from queue
                        playerAddresses.remove(address)
                        numberPlayers -= 1

                # check if can start the game
                if (readyPlayers > 0 and readyPlayers % 2  == 0):
                    # TODO start the game
                    message = "Start"
                    for playerAddress in playerAddresses:
                        UDPServerSocket.sendto(message.encode(), playerAddress)
                    print("Game is starting!")
                    return readyPlayers
                else: # we create new queue ; restart time
                    queue_time = time.time()
            
            else: # Number of players is too small
                queue_time = time.time()



readyPlayers = queue(numberPlayers,playerAddresses,queue_time)
start_game(readyPlayers)

UDPServerSocket.close()