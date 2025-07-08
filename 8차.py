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
G = 1600
SHIP_RADIUS = 8
PLANET_RADIUS = 30
SHIP_THRUST = 150
FUEL_MAX = 150
FUEL_CONSUMPTION = 10
WARNING_DISTANCE = 120
MINIMAP_SCALE = 0.05
FUEL_POD_RECHARGE = 100
FUEL_POD_COUNT = 20

MAP_SIZE = 5000
MAP_HALF = MAP_SIZE // 2
PLANET_SAFE_DISTANCE = 500

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
        self.distance_traveled = 0
        self.prev_pos = pygame.Vector2(x, y)

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
        self.distance_traveled += (self.pos - self.prev_pos).length()
        self.prev_pos = self.pos.copy()

        # 맵 경계 제한 및 충돌 시 속도 0으로
        if self.pos.x < -MAP_HALF:
            self.pos.x = -MAP_HALF
            self.vel.x = 0
        elif self.pos.x > MAP_HALF:
            self.pos.x = MAP_HALF
            self.vel.x = 0

        if self.pos.y < -MAP_HALF:
            self.pos.y = -MAP_HALF
            self.vel.y = 0
        elif self.pos.y > MAP_HALF:
            self.pos.y = MAP_HALF
            self.vel.y = 0

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

        # 맵 경계에서 반사
        if self.pos.x < -MAP_HALF or self.pos.x > MAP_HALF:
            self.vel.x *= -1
            self.pos.x = max(min(self.pos.x, MAP_HALF), -MAP_HALF)
        if self.pos.y < -MAP_HALF or self.pos.y > MAP_HALF:
            self.vel.y *= -1
            self.pos.y = max(min(self.pos.y, MAP_HALF), -MAP_HALF)

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


def generate_planets(num_planets, min_dist=80, safe_radius=PLANET_SAFE_DISTANCE):
    planets = []
    tries = 0
    while len(planets) < num_planets and tries < num_planets * 50:
        tries += 1
        x = random.randint(-MAP_HALF, MAP_HALF)
        y = random.randint(-MAP_HALF, MAP_HALF)
        pos = pygame.Vector2(x, y)

        if pos.length() < safe_radius:
            continue

        too_close = any((p.pos - pos).length() < (PLANET_RADIUS * 2 + min_dist) for p in planets)
        if not too_close:
            mass = random.randint(1000, 5000)
            planets.append(Planet(x, y, mass))
    return planets


def generate_fuelpods(num_pods):
    pods = []
    for _ in range(num_pods):
        x = random.randint(-MAP_HALF, MAP_HALF)
        y = random.randint(-MAP_HALF, MAP_HALF)
        pods.append(FuelPod(x, y))
    return pods


def maintain_fuelpods(fuelpods, max_count=FUEL_POD_COUNT):
    active_pods = [pod for pod in fuelpods if not pod.collected]
    while len(active_pods) < max_count:
        x = random.randint(-MAP_HALF, MAP_HALF)
        y = random.randint(-MAP_HALF, MAP_HALF)
        new_pod = FuelPod(x, y)
        fuelpods.append(new_pod)
        active_pods.append(new_pod)


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


def draw_map_boundary_warning(surface, camera_offset):
    top_left = pygame.Vector2(-MAP_HALF, -MAP_HALF) - camera_offset + pygame.Vector2(WIDTH // 2, HEIGHT // 2)
    rect = pygame.Rect(top_left.x, top_left.y, MAP_SIZE, MAP_SIZE)
    pygame.draw.rect(surface, WARNING_COLOR, rect, 3)


def load_highscore():
    if os.path.exists(HIGHSCORE_FILE):
        with open(HIGHSCORE_FILE, "r") as f:
            try:
                return float(f.read())
            except:
                return 0
    return 0


def save_highscore(score):
    with open(HIGHSCORE_FILE, "w") as f:
        f.write(str(score))


def reset_game():
    global ship, planets, fuelpods, game_over, explosion_timer
    ship = Spaceship(0, 0)
    planets = generate_planets(80)
    fuelpods = generate_fuelpods(FUEL_POD_COUNT)
    game_over = False
    explosion_timer = 0


def draw_game_over_screen(surface, font):
    # 반투명 검정 배경
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))
    surface.blit(overlay, (0, 0))

    # "Game Over" 텍스트
    game_over_text = font.render("GAME OVER", True, WHITE)
    text_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
    surface.blit(game_over_text, text_rect)

    # 버튼 그리기
    button_rect = pygame.Rect(0, 0, 200, 50)
    button_rect.center = (WIDTH // 2, HEIGHT // 2 + 30)
    pygame.draw.rect(surface, (100, 100, 255), button_rect)
    pygame.draw.rect(surface, WHITE, button_rect, 2)

    button_text = font.render("Restart", True, WHITE)
    button_text_rect = button_text.get_rect(center=button_rect.center)
    surface.blit(button_text, button_text_rect)

    return button_rect


# 게임 초기화
ship = Spaceship(0, 0)
planets = generate_planets(80)
fuelpods = generate_fuelpods(FUEL_POD_COUNT)

font = pygame.font.SysFont(None, 30)
running = True
game_over = False
explosion_timer = 0
highscore = load_highscore()

button_rect = None

# 게임 루프
while running:
    dt = clock.tick(60) / 1000
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT or keys[pygame.K_ESCAPE]:
            running = False

        if game_over and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if button_rect and button_rect.collidepoint(event.pos):
                reset_game()

    if not game_over:
        ship.update(planets, dt, keys)
        for planet in planets:
            planet.update(dt)
        for pod in fuelpods:
            pod.check_collect(ship)

        # 연료캡슐 개수 유지
        active_pods = [pod for pod in fuelpods if not pod.collected]
        while len(active_pods) < FUEL_POD_COUNT:
            x = random.randint(-MAP_HALF, MAP_HALF)
            y = random.randint(-MAP_HALF, MAP_HALF)
            new_pod = FuelPod(x, y)
            fuelpods.append(new_pod)
            active_pods.append(new_pod)

        if ship.check_collision(planets):
            game_over = True
            explosion_timer = 1.5
            score = ship.distance_traveled / 10
            if score > highscore:
                highscore = score
                save_highscore(highscore)
    else:
        explosion_timer -= dt
        if explosion_timer <= 0:
            # 폭발 애니메이션 끝나면 버튼 활성화
            pass

    camera_offset = ship.pos

    screen.fill(BLACK)
    draw_map_boundary_warning(screen, camera_offset)
    for planet in planets:
        planet.draw(screen, camera_offset)
    for pod in fuelpods:
        pod.draw(screen, camera_offset)

    draw_warning(screen, ship, planets, camera_offset)
    ship.draw(screen, camera_offset)
    draw_minimap(screen, ship, planets, fuelpods)

    score = ship.distance_traveled / 10
    score_text = font.render(f"Score: {score:.0f}", True, WHITE)
    fuel_text = font.render(f"Fuel: {ship.fuel:.1f}", True, WHITE)
    highscore_text = font.render(f"Best: {highscore:.0f}", True, WHITE)

    screen.blit(score_text, (10, 10))
    screen.blit(fuel_text, (10, 40))
    screen.blit(highscore_text, (10, 70))

    if game_over:
        button_rect = draw_game_over_screen(screen, font)
    else:
        button_rect = None

    pygame.display.flip()

# 종료
print(f"\n게임 종료! 점수(이동 거리): {ship.distance_traveled:.2f}px")
pygame.quit()
sys.exit()
