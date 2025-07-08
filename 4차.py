import pygame
import random
import sys
import os

# 초기화
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
pygame.display.set_caption("Gravity Ship - Dense Galaxy")

# 색상
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
PLANET_COLOR = (100, 100, 255)
SHIP_COLOR = (255, 255, 100)
EXPLOSION_COLOR = (255, 100, 100)
WARNING_COLOR = (255, 0, 0)
MINIMAP_COLOR = (50, 50, 50)

# 상수
G = 700
SHIP_RADIUS = 8
PLANET_RADIUS = 30
SHIP_THRUST = 150
FUEL_MAX = 300
FUEL_CONSUMPTION = 10
WARNING_DISTANCE = 120
MINIMAP_SCALE = 0.05
FUEL_POD_RECHARGE = 200
FUEL_POD_COUNT = 20

# 기록 파일
HIGHSCORE_FILE = "highscore.txt"


class Spaceship:
    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.acc = pygame.Vector2(0, 0)
        self.time_alive = 0
        self.fuel = FUEL_MAX
        self.alive = True

    def apply_gravity(self, planets):
        total_force = pygame.Vector2(0, 0)
        for planet in planets:
            dir_vector = planet.pos - self.pos
            distance_sq = max(dir_vector.length_squared(), 100)
            force_magnitude = G * planet.mass / distance_sq
            force = dir_vector.normalize() * force_magnitude
            total_force += force
        self.acc = total_force

    def apply_input(self, keys, dt):
        thrust = pygame.Vector2(0, 0)
        if self.fuel > 0:
            if keys[pygame.K_LEFT]:
                thrust.x -= SHIP_THRUST
            if keys[pygame.K_RIGHT]:
                thrust.x += SHIP_THRUST
            if keys[pygame.K_UP]:
                thrust.y -= SHIP_THRUST
            if keys[pygame.K_DOWN]:
                thrust.y += SHIP_THRUST
            if thrust.length_squared() > 0:
                self.fuel -= FUEL_CONSUMPTION * dt
                self.fuel = max(self.fuel, 0)
        self.acc += thrust

    def update(self, planets, dt, keys):
        if not self.alive:
            return
        self.apply_gravity(planets)
        self.apply_input(keys, dt)
        self.vel += self.acc * dt
        self.pos += self.vel * dt
        self.time_alive += dt

    def draw(self, surface, camera_offset):
        draw_pos = self.pos - camera_offset + pygame.Vector2(WIDTH // 2, HEIGHT // 2)
        if self.alive:
            pygame.draw.circle(surface, SHIP_COLOR, draw_pos, SHIP_RADIUS)
        else:
            pygame.draw.circle(surface, EXPLOSION_COLOR, draw_pos, SHIP_RADIUS * 2)

    def check_collision(self, planets):
        for planet in planets:
            if (self.pos - planet.pos).length() < (PLANET_RADIUS + SHIP_RADIUS):
                self.alive = False
                return True
        return False


class Planet:
    def __init__(self, x, y, mass):
        self.pos = pygame.Vector2(x, y)
        self.mass = mass
        self.vel = pygame.Vector2(random.uniform(-20, 20), random.uniform(-20, 20))

    def update(self, dt):
        self.pos += self.vel * dt

    def draw(self, surface, camera_offset):
        draw_pos = self.pos - camera_offset + pygame.Vector2(WIDTH // 2, HEIGHT // 2)
        pygame.draw.circle(surface, PLANET_COLOR, draw_pos, PLANET_RADIUS)


class FuelPod:
    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.collected = False

    def draw(self, surface, camera_offset):
        if not self.collected:
            draw_pos = self.pos - camera_offset + pygame.Vector2(WIDTH // 2, HEIGHT // 2)
            pygame.draw.circle(surface, (100, 255, 100), draw_pos, 6)

    def check_collect(self, ship):
        if not self.collected and (ship.pos - self.pos).length() < 20:
            self.collected = True
            ship.fuel = min(FUEL_MAX, ship.fuel + FUEL_POD_RECHARGE)


def generate_planets(num_planets, min_dist=80):
    planets = []
    tries = 0
    while len(planets) < num_planets and tries < num_planets * 20:
        tries += 1
        x = random.randint(-2000, 2000)
        y = random.randint(-2000, 2000)
        mass = random.randint(1000, 5000)
        pos = pygame.Vector2(x, y)

        too_close = any((p.pos - pos).length() < (PLANET_RADIUS * 2 + min_dist) for p in planets)
        if not too_close:
            planets.append(Planet(x, y, mass))
    return planets


def generate_fuelpods(num_pods):
    pods = []
    for _ in range(num_pods):
        x = random.randint(-2000, 2000)
        y = random.randint(-2000, 2000)
        pods.append(FuelPod(x, y))
    return pods


def draw_warning(surface, ship, planets, camera_offset):
    for planet in planets:
        distance = (ship.pos - planet.pos).length()
        if distance < WARNING_DISTANCE + PLANET_RADIUS:
            draw_pos = planet.pos - camera_offset + pygame.Vector2(WIDTH // 2, HEIGHT // 2)
            pygame.draw.circle(surface, WARNING_COLOR, draw_pos, PLANET_RADIUS + 10, 2)


def draw_minimap(surface, ship, planets, fuelpods):
    minimap_width = int(WIDTH * 0.25)
    minimap_height = int(HEIGHT * 0.25)
    minimap = pygame.Surface((minimap_width, minimap_height))
    minimap.fill(MINIMAP_COLOR)

    center = pygame.Vector2(minimap_width // 2, minimap_height // 2)

    for planet in planets:
        offset = (planet.pos - ship.pos) * MINIMAP_SCALE
        pos = center + offset
        if 0 <= pos.x < minimap_width and 0 <= pos.y < minimap_height:
            pygame.draw.circle(minimap, PLANET_COLOR, pos, 3)

    for pod in fuelpods:
        if not pod.collected:
            offset = (pod.pos - ship.pos) * MINIMAP_SCALE
            pos = center + offset
            if 0 <= pos.x < minimap_width and 0 <= pos.y < minimap_height:
                pygame.draw.circle(minimap, (100, 255, 100), pos, 2)

    pygame.draw.circle(minimap, SHIP_COLOR, center, 4)
    surface.blit(minimap, (WIDTH - minimap_width - 10, HEIGHT - minimap_height - 10))


def load_highscore():
    if os.path.exists(HIGHSCORE_FILE):
        with open(HIGHSCORE_FILE, "r") as f:
            return float(f.read())
    return 0


def save_highscore(score):
    with open(HIGHSCORE_FILE, "w") as f:
        f.write(str(score))


# 게임 초기화
ship = Spaceship(0, 0)
planets = generate_planets(80)
fuelpods = generate_fuelpods(FUEL_POD_COUNT)

font = pygame.font.SysFont(None, 30)
running = True
game_over = False
explosion_timer = 0
highscore = load_highscore()

# 게임 루프
while running:
    dt = clock.tick(60) / 1000
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT or keys[pygame.K_ESCAPE]:
            running = False

    if not game_over:
        ship.update(planets, dt, keys)
        for planet in planets:
            planet.update(dt)
        for pod in fuelpods:
            pod.check_collect(ship)
        if ship.check_collision(planets):
            game_over = True
            explosion_timer = 1.5
            if ship.time_alive > highscore:
                highscore = ship.time_alive
                save_highscore(highscore)
    else:
        explosion_timer -= dt
        if explosion_timer <= 0:
            running = False

    camera_offset = ship.pos

    screen.fill(BLACK)
    for planet in planets:
        planet.draw(screen, camera_offset)
    for pod in fuelpods:
        pod.draw(screen, camera_offset)

    draw_warning(screen, ship, planets, camera_offset)
    ship.draw(screen, camera_offset)
    draw_minimap(screen, ship, planets, fuelpods)

    label = "Score" if game_over else "Time"
    time_text = font.render(f"{label}: {ship.time_alive:.2f} s", True, WHITE)
    fuel_text = font.render(f"Fuel: {ship.fuel:.1f}", True, WHITE)
    highscore_text = font.render(f"Best: {highscore:.2f} s", True, WHITE)

    screen.blit(time_text, (10, 10))
    screen.blit(fuel_text, (10, 40))
    screen.blit(highscore_text, (10, 70))

    pygame.display.flip()

# 종료
print(f"\n게임 종료! 생존 시간: {ship.time_alive:.2f}초")
pygame.quit()
sys.exit()
