import socket
import threading
import json
import pygame
import time

DISCOVERY_PORT = 50001
TCP_PORT = 50000

def discover_rooms(timeout=1.5):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(0.4)

    found = []
    start = time.time()

    while time.time() - start < timeout:
        sock.sendto(b"DISCOVER_ROOM", ("<broadcast>", DISCOVERY_PORT))
        try:
            data, addr = sock.recvfrom(1024)
            info = json.loads(data.decode())
            found.append(info)
        except:
            pass

    return found


class Client:
    def __init__(self):
        self.sock = None
        self.players = []
        self.running = True
        self.status = "Searching for rooms..."
        self.room_code = "" 
        

    def connect(self, host):
        self.status = "Connecting..."
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, TCP_PORT))
        self.status = "Connected!"
        threading.Thread(target=self.recv_loop, daemon=True).start()

    def recv_loop(self):
        buf = b""
        while self.running:
            try:
                data = self.sock.recv(4096)
                if not data:
                    break
                buf += data
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    msg = json.loads(line.decode())
                    if msg["type"] == "welcome":
                        self.id = msg["id"]
                        if "room_code" in msg:              # <<< ROOM CODE
                            self.room_code = msg["room_code"]
                    elif msg["type"] == "state":
                        self.players = msg["players"]
            except:
                break

    def send_input(self, dx, dy):
        msg = json.dumps({"dx": dx, "dy": dy}) + "\n"
        try:
            self.sock.sendall(msg.encode())
        except:
            pass


# ---------------------- PYGAME LOOP ----------------------
pygame.init()
screen = pygame.display.set_mode((1000, 700))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 32)
instruction_text = font.render("Use Arrow Keys to Move", True, (255, 255, 255))

client = Client()
print("Searching for rooms.../n")

rooms = discover_rooms()
if rooms:
    print("Found rooms:/n", rooms)
    if "room_code" in rooms[0]:                      
        client.room_code = rooms[0]["room_code"] 
    client.connect(rooms[0]["host"])
else:
    print("No rooms found.\n")
    client.status = "No rooms found."

running = True
while running:
    dx = dy = 0
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]: dx = -5
    if keys[pygame.K_RIGHT]: dx = 5
    if keys[pygame.K_UP]: dy = -5
    if keys[pygame.K_DOWN]: dy = 5

    client.send_input(dx, dy)

    screen.fill((30, 30, 30))
    for p in client.players:
        pygame.draw.rect(screen, (0,255,0), (p["x"], p["y"], 40, 40))

    status_surface = font.render(client.status, True, (255, 255, 0))
    screen.blit(status_surface, (15, 50))
    room_surface = font.render(f"Room: {client.room_code}", True, (0, 200, 255))  
    text_width = room_surface.get_width()                                         
    screen_width = screen.get_width()                                            
    screen.blit(room_surface, (screen_width - text_width - 15, 15)) 
    fps = clock.get_fps()  
    fps_text = font.render(f"FPS: {int(fps)}", True, (255, 255, 255))
    screen.blit(fps_text, (15, 80))

    screen.blit(instruction_text, (15, 120))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
client.running = False