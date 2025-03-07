import pygame
import sys
import time
import socket
import threading

pygame.init()

WIDTH, HEIGHT = 816, 876
ROWS, COLS = 17, 17
TILE_SIZE = WIDTH // ROWS
FPS = 20
OFFSET = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (150, 150, 150)
RED = (255, 0, 0)
BLUE = (0,0,255)
GREEN = (0,255,0)
YELLOW = (255, 255, 0)
ORANGE = (255,165,0)

IP = "127.0.0.1"
PORT = 40000


clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = (IP, PORT)

class Player:
    def __init__(self, row, col, id, points, color):
        self.row = row
        self.col = col
        self.start_row = row
        self.start_col = col
        self.id = id
        self.points = points
        self.color = color 
        self.killed_time = 0

    def move(self, direction):
        new_row, new_col = self.row, self.col
        if direction == "up" and self.row > 0:
            new_row -= 1
        elif direction == "down" and self.row < ROWS - 1:
            new_row += 1
        elif direction == "left" and self.col > 0:
            new_col -= 1
        elif direction == "right" and self.col < COLS - 1:
            new_col += 1

        # Check if the new position is not a wall
        if board.grid[new_row][new_col].tile_type != "wall" and board.grid[new_row][new_col].tile_type != "chest":
            self.row, self.col = new_row, new_col

class Bomb:
    def __init__(self, row, col, color, time):
        self.row=row
        self.col=col
        self.color=color
        self.plant_time = time
        self.positions_around_bomb = []
        self.exploding_time = None
        self.isExploded = False


    def isExploding(self):
        current_time = time.time()
        time_elapsed = current_time-self.plant_time
        return time_elapsed >= 2

    def isEndExploding(self):
        current_time = time.time()
        return current_time - self.exploding_time >= 2


class Tile:
    def __init__(self, row, col, tile_type=None):
        self.row = row
        self.col = col
        self.tile_type = tile_type

    def draw(self, surface):
        if self.tile_type == "explosionBombPlayer":
            color = RED
        elif self.tile_type == "explosionBombPlayer2":
            color = GREEN
        elif self.tile_type == "explosionBombPlayer3":
            color = BLUE
        elif self.tile_type == "explosionBombPlayer4":
            color = YELLOW
        elif self.tile_type == "bomb":
            color = BLACK
        elif self.tile_type == "chest":
            color = ORANGE
        elif self.tile_type == "wall":
            color = GRAY
        elif self.tile_type == "otherPlayer":
            color = BLACK #PLACEHOLDER
        elif self.tile_type == "explosion":
            color = RED
        else:
            color = WHITE  # Domyślny kolor dla nieznanego typu

        pygame.draw.rect(surface, color, (self.col * TILE_SIZE, self.row * TILE_SIZE + OFFSET, TILE_SIZE, TILE_SIZE))
        pygame.draw.rect(surface, BLACK, (self.col * TILE_SIZE, self.row * TILE_SIZE + OFFSET, TILE_SIZE, TILE_SIZE), 1)


class Board:
    def __init__(self, player_id, numberPlayers):
        self.grid = [[Tile(row, col) for col in range(COLS)] for row in range(ROWS)]
        # Set outer tiles to 'wall' type
        for row in range(ROWS):
            for col in range(COLS):
                if row == 0 or row == ROWS - 1 or col == 0 or col == COLS - 1:
                    self.grid[row][col].tile_type = "wall"
        
        for i in range(3,14,2):
            for j in range(3,14,2):
                self.grid[i][j].tile_type = "wall"
                if j > 3:
                    self.grid[i][j-1].tile_type = "chest"

        for i in range(4,14,2):
            for j in range(3,14):
                self.grid[i][j].tile_type = "chest"

        self.keys_pressed = {'up': False, 'down': False, 'left': False, 'right': False}
        self.bombs = []
        self.last_bomb_time = 0
        
        self.running = True
        self.game_over = threading.Event()

        self.start_time = None 
        self.round = 0

        if numberPlayers == 4:
            if player_id == "1":
                self.player = Player(1,1,1,0,RED)
                self.player2 = Player(15,15,2,0,GREEN)
                self.player3 = Player(1,15,3,0,BLUE)
                self.player4 = Player(15,1,4,0, YELLOW)
                self.players = [self.player, self.player2, self.player3, self.player4]
            elif player_id == "2":
                self.player2 = Player(1,1,1,0,RED)
                self.player = Player(15,15,2,0,GREEN)
                self.player3 = Player(1,15,3,0,BLUE)
                self.player4 = Player(15,1,4,0, YELLOW)
                self.players = [self.player2, self.player, self.player3, self.player4]
            elif player_id == "3":
                self.player2 = Player(1,1,1,0,RED)
                self.player3 = Player(15,15,2,0,GREEN)
                self.player = Player(1,15,3,0,BLUE)
                self.player4 = Player(15,1,4,0, YELLOW)
                self.players = [self.player2, self.player3, self.player, self.player4]
            elif player_id == "4":
                self.player2 = Player(1,1,1,0,RED)
                self.player4 = Player(15,15,2,0,GREEN)
                self.player3 = Player(1,15,3,0,BLUE)
                self.player = Player(15,1,4,0, YELLOW)
                self.players = [self.player2, self.player4, self.player3, self.player]
        elif numberPlayers == 2:
            if player_id == "1":
                self.player = Player(1,1,1,0,RED)
                self.player2 = Player(15,15,2,0,GREEN)
                self.player3 = None
                self.player4 = None
                self.players = [self.player, self.player2]
            elif player_id == "2":
                self.player2 = Player(1,1,1,0,RED)
                self.player = Player(15,15,2,0,GREEN)
                self.player3 = None
                self.player4 = None
                self.players = [self.player2, self.player]    


    def draw(self, surface):
        surface.fill(WHITE)  

        # Draw grid lines
        for row in range(ROWS):
            for col in range(COLS):
                self.grid[row][col].draw(surface)

        # Draw player
        if self.player is not None and time.time() - self.player.killed_time > 3:
            player_rect = pygame.Rect(self.player.col * TILE_SIZE, self.player.row * TILE_SIZE + OFFSET, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(surface, self.player.color, player_rect)
        
        if self.player2 is not None and time.time() - self.player2.killed_time > 3:
            player_rect2 = pygame.Rect(self.player2.col * TILE_SIZE, self.player2.row * TILE_SIZE + OFFSET, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(surface, self.player2.color, player_rect2)
        
        if self.player3 is not None and time.time() - self.player3.killed_time > 3:
            player_rect3 = pygame.Rect(self.player3.col * TILE_SIZE, self.player3.row * TILE_SIZE + OFFSET, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(surface, self.player3.color, player_rect3)
        
        if self.player4 is not None and time.time() - self.player4.killed_time > 3:
            player_rect4 = pygame.Rect(self.player4.col * TILE_SIZE, self.player4.row * TILE_SIZE + OFFSET, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(surface, self.player4.color, player_rect4)

        # Draw bombs
        for bomb in self.bombs:
            bomb_rect = pygame.Rect(bomb.col * TILE_SIZE, bomb.row * TILE_SIZE + OFFSET, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(surface, bomb.color, bomb_rect)
            font = pygame.font.Font(None, 72)
            text_surface = font.render("*", True, BLACK)
            surface.blit(text_surface, (bomb.col * TILE_SIZE + TILE_SIZE // 3, bomb.row * TILE_SIZE + OFFSET + TILE_SIZE //4))

        self.draw_scoreboard(surface)


    def draw_scoreboard(self, surface):
        font = pygame.font.Font(None, 36)
        texts = []
        
        i = 1
        for player in self.players:
            if player is not None:
                texts.append((f'Player {i}: ' + str(player.points), player.color))
            i += 1 

        x = 20
        y = 0

        for text, color in texts:
            text_surface = font.render(text, True, color)
            surface.blit(text_surface, (x, y + 35))
            x += text_surface.get_width() + 20

        x = 20
        y = 10
        text_surface = font.render("BOMBERMAN", True, BLACK)
        surface.blit(text_surface, (x, y))
        text_surface = font.render(f'ROUND {self.round}', True, BLACK)
        surface.blit(text_surface, (x+200, y))
        elapsed_time = time.time() - self.start_time
        remaining_time = 180 - elapsed_time
        if remaining_time < 0:
            remaining_time = 0
        minutes = int(remaining_time // 60)
        seconds = int(remaining_time % 60)
        timer_text = f"Time: {minutes:02}:{seconds:02}"
        timer_surface = font.render(timer_text, True, BLACK)
        timer_x = (WIDTH - timer_surface.get_width()) // 2
        surface.blit(timer_surface, (x+350, y))

        if time.time() - self.start_time >= 180:
            font = pygame.font.Font(None, 150)
            text_surface = font.render("TIME OVER", True, BLACK)
            surface.blit(text_surface, (100, HEIGHT//2))
        elif remaining_time > 180:
            font = pygame.font.Font(None, 150)
            text_surface = font.render("NEW ROUND", True, BLACK)
            surface.blit(text_surface, (100, HEIGHT//2))


    def move_left(self, row, col, player):
        if self.grid[row][col].tile_type != "wall" and self.grid[row][col].tile_type != "chest":
            player.row = row
            player.col = col

    def move_right(self, row, col, player):
        if self.grid[row][col].tile_type != "wall" and self.grid[row][col].tile_type != "chest":
            player.row = row
            player.col = col

    def move_up(self, row, col, player):
        if self.grid[row][col].tile_type != "wall" and self.grid[row][col].tile_type != "chest":
            player.row = row
            player.col = col

    def move_down(self, row, col, player):
        if self.grid[row][col].tile_type != "wall" and self.grid[row][col].tile_type != "chest":
            player.row = row
            player.col = col


    def choose_move(self, player, row, col, action, time):
        if action == "rt":
            self.move_right(row, col, player)
        elif action == "lt":
            self.move_left(row, col, player)
        elif action == "up":
            self.move_up(row, col, player)
        elif action == "dn":
            self.move_down(row, col, player)
        elif action == "bm":
            self.place_bomb(row, col, player.color, float(time))
        elif action == "dc":
            if player.id == self.player.id:
                self.player = None
            elif player.id == self.player2.id:
                self.player2 = None
            elif player.id == self.player3.id:
                self.player3 = None
            elif player.id == self.player4.id:
                self.player4 = None


    def do_action(self, received_player_id, row, col, action, time):
        if self.player is not None and received_player_id == str(self.player.id):
            self.choose_move(self.player, int(row), int(col), action, time)
        elif self.player2 is not None and received_player_id == str(self.player2.id):
            self.choose_move(self.player2, int(row), int(col), action, time)
        elif self.player3 is not None and received_player_id == str(self.player3.id):
            self.choose_move(self.player3, int(row), int(col), action, time)
        elif self.player4 is not None and received_player_id == str(self.player4.id):
            self.choose_move(self.player4, int(row), int(col), action, time)


    def new_round(self, message):
        self.round = int(message[8])
        self.start_time = float(message[9:])

        self.bombs = []
        
        self.grid = [[Tile(row, col) for col in range(COLS)] for row in range(ROWS)]
        for row in range(ROWS):
            for col in range(COLS):
                if row == 0 or row == ROWS - 1 or col == 0 or col == COLS - 1:
                    self.grid[row][col].tile_type = "wall"
        
        for i in range(3,14,2):
            for j in range(3,14,2):
                self.grid[i][j].tile_type = "wall"
                if j > 3:
                    self.grid[i][j-1].tile_type = "chest"

        for i in range(4,14,2):
            for j in range(3,14):
                self.grid[i][j].tile_type = "chest"

        for player in self.players:
            if player.id == 1:
                player.col = 1
                player.row = 1
                player.killed_time = 0
                player.points = 0
            elif player.id == 2:
                player.col = 15
                player.row = 15
                player.killed_time = 0
                player.points = 0
            elif player.id == 3:
                player.row = 1
                player.col = 15
                player.killed_time = 0
                player.points = 0
            elif player.id == 4:
                player.row = 15
                player.col = 1
                player.killed_time = 0
                player.points = 0


    def receive_data(self):
        while not self.game_over.is_set():
            try:
                clientSocket.settimeout(3.0)
                message, _ = clientSocket.recvfrom(1024)
                message = message.decode()
                if message[0:8] == "NewRound":
                    self.new_round(message)
                elif message[0:7] == "EndGame":
                    self.running = False
                else:
                    self.do_action(message[0], message[1:3], message[3:5], message[5:7], message[7:])
            except socket.timeout:
                continue
        print("koncze sie")
    

    def send_data(self, action):
        row = str(self.player.row)
        col = str(self.player.col)
        if len(row) < 2:
            row = "0"+row
        if len(col) < 2:
            col = "0"+col
        message = str(self.player.id)+row+col+action
        if time.time() - self.start_time > 0 and time.time() - self.start_time < 180:
            clientSocket.sendto(message.encode(), server_address)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                row = str(self.player.row)
                col = str(self.player.col)
                if len(row) < 2:
                    row = "0"+row
                if len(col) < 2:
                    col = "0"+col
                message = str(self.player.id) + row + col + "dc"
                clientSocket.sendto(message.encode(), server_address)
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    if time.time() - self.player.killed_time > 3:
                        action = "up"
                        self.send_data(action)
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    if time.time() - self.player.killed_time > 3: 
                        action = "dn"
                        self.send_data(action)
                elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    if time.time() - self.player.killed_time > 3:
                        action = "lt"
                        self.send_data(action)
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    if time.time() - self.player.killed_time > 3:
                        action = "rt"
                        self.send_data(action)
                elif event.key == pygame.K_SPACE:
                    if time.time() - self.player.killed_time > 3:    
                        current_time = time.time()
                        if current_time - self.last_bomb_time >= 2:
                            action = "bm"
                            self.send_data(action)
                            self.last_bomb_time = current_time
        return True
    
    def place_bomb(self, row, col, color, time):
        # Create bomb object at player's position
        bomb = Bomb(row, col, color, time)
        # Add bomb to the list of bombs
        self.bombs.append(bomb)
        #self.explode_bomb(bomb)

    def explode_bomb(self, bomb):
        # Get positions around the bomb
        for i in range(1, 4):
            if bomb.row - i >= 0:
                if self.grid[bomb.row - i][bomb.col].tile_type == "wall":
                    break
                else:
                    bomb.positions_around_bomb.append((bomb.row - i, bomb.col))

        for i in range(1, 4):
            if bomb.row + i <= ROWS:
                if self.grid[bomb.row + i][bomb.col].tile_type == "wall":
                    break
                else:
                    bomb.positions_around_bomb.append((bomb.row + i, bomb.col))

        for i in range(1, 4):
            if bomb.col - i >= 0:
                if self.grid[bomb.row][bomb.col - i].tile_type == "wall":
                    break
                else:
                    bomb.positions_around_bomb.append((bomb.row, bomb.col - i))

        for i in range(1, 4):
            if bomb.col - i <= COLS:
                if self.grid[bomb.row][bomb.col + i].tile_type == "wall":
                    break
                else:
                    bomb.positions_around_bomb.append((bomb.row, bomb.col + i))
        
        bomb.positions_around_bomb.append((bomb.row,bomb.col))

        if bomb.color == RED:
            type_tile = "explosionBombPlayer"
        elif bomb.color == GREEN:
            type_tile = "explosionBombPlayer2"
        elif bomb.color == BLUE:
            type_tile = "explosionBombPlayer3"
        elif bomb.color == YELLOW:
            type_tile = "explosionBombPlayer4"


        # Change color of tiles around the bomb
        for row, col in bomb.positions_around_bomb:
            if row > 0 and col > 0 and row < ROWS and col < COLS:
                if self.grid[row][col].tile_type != "wall":
                    if self.grid[row][col].tile_type == "chest":
                        if self.player is not None and bomb.color == self.player.color:
                            self.player.points += 1
                        elif self.player2 is not None and bomb.color == self.player2.color:
                            self.player2.points += 1
                        elif self.player3 is not None and bomb.color == self.player3.color:
                            self.player3.points += 1
                        elif self.player4 is not None and bomb.color == self.player4.color:
                            self.player4.points += 1
                    self.grid[row][col].tile_type = type_tile  # Change color to 'chest' type

        bomb.exploding_time = time.time()
        bomb.isExploded = True

    def end_explode_bomb(self, bomb):
        for row, col in bomb.positions_around_bomb:
            if row > 0 and col > 0 and row < ROWS and col < COLS:
                if self.grid[row][col].tile_type != "wall":
                    self.grid[row][col].tile_type = WHITE

        self.bombs.remove(bomb)
    

    
    def kill_points(self, player, bomb):
        if player is not None and bomb.color == player.color:
            player.points -= 5
        elif self.player is not None and bomb.color == self.player.color:
            self.player.points += 3
        elif self.player2 is not None and bomb.color == self.player2.color:
            self.player2.points += 3
        elif self.player3 is not None and bomb.color == self.player3.color:
            self.player3.points += 3
        elif self.player4 is not None and bomb.color == self.player4.color:
            self.player4.points += 3



    def check_if_player_killed(self, bomb, player):
        if bomb.row == player.row and bomb.col == player.col and time.time() - player.killed_time > 3:
            player.row = player.start_row
            player.col = player.start_col
            player.killed_time = time.time()
            self.kill_points(player, bomb)
        for row, col in bomb.positions_around_bomb:
            if row > 0 and col > 0 and row < ROWS and col < COLS:
                if row == player.row and col == player.col and time.time() - player.killed_time > 3:
                    player.row = player.start_row
                    player.col = player.start_col
                    player.killed_time = time.time()
                    self.kill_points(player, bomb)
                    


    def check_if_players_killed(self, bomb):
        if self.player is not None:
            self.check_if_player_killed(bomb, self.player)
        if self.player2 is not None:
            self.check_if_player_killed(bomb, self.player2)
        if self.player3 is not None:
            self.check_if_player_killed(bomb, self.player3)
        if self.player4 is not None:
            self.check_if_player_killed(bomb, self.player4)

    def run_game(self):
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        clock = pygame.time.Clock()
        

        clientSocket.settimeout(20.0)
        message, _ = clientSocket.recvfrom(1024)
        message = message.decode()
        self.new_round(message)

        thread = threading.Thread(target=self.receive_data)
        thread.start()
        while self.running:
            self.running = self.handle_events()

            for bomb in self.bombs:
                if bomb.isExploding() and bomb.isExploded is False:
                    self.explode_bomb(bomb)
                if bomb.isExploded is True:
                    self.check_if_players_killed(bomb)
                    if bomb.isEndExploding():
                        self.end_explode_bomb(bomb)

            self.draw(screen)
            pygame.display.flip()
            clock.tick(FPS)


        print("KONIEC")
        self.game_over.set()
        print("WĄTEK DOŁĄCZA")
        thread.join()
        clientSocket.close()
        time.sleep(5)
        print("WYCHODZIMY")
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    # TODO create pygame UI
    # connect with server
    isReady = False
    isInQueue = False
    while(isReady is not True):
        message = "I'd like to join the queue!"
        clientSocket.sendto(message.encode(), server_address)
        respsoneMessage, _ = clientSocket.recvfrom(1024)
        if respsoneMessage.decode() == "You have joined the queue! Please, wait for other players!":
            isInQueue = True
            print("You have joined the queue! Please, wait for other players!")
            while(isInQueue):
                respsoneMessage, _ = clientSocket.recvfrom(1024)
                if respsoneMessage.decode() == "All players joined the queue! Are you ready?":
                    answer = input("Are you ready? [y/n]")
                    if answer == "y":
                        answer = "yes"
                        clientSocket.sendto(answer.encode(), server_address)
                        respsoneMessage, _ = clientSocket.recvfrom(1024)
                        if respsoneMessage.decode() == "Start":
                            isReady = True
                            isInQueue = False
                    else:
                        answer = "no"
                        clientSocket.sendto(answer.encode(), server_address)
                        isInQueue = False
                

    respsoneMessage, _ = clientSocket.recvfrom(1024)
    print(respsoneMessage.decode())
    response = respsoneMessage.decode()
    player_id = response[0]
    numberPlayers = int(response[1])
    clientSocket.sendto(response.encode(),server_address)


    # game
    board = Board(player_id, numberPlayers)
    board.run_game()
