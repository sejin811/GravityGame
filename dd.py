import pygame
import random
import math
import sys

# 초기화
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
pygame.display.set_caption("Gravity Ship")

# 색상
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
PLANET_COLOR = (100, 100, 255)
SHIP_COLOR = (255, 255, 100)
EXPLOSION_COLOR = (255, 100, 100)

# 상수
G = 300  # 중력 상수
SHIP_RADIUS = 8
PLANET_RADIUS = 30
SHIP_THRUST = 150  # 방향키 가속도

# 우주선 클래스
class Spaceship:
    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.acc = pygame.Vector2(0, 0)
        self.time_alive = 0
        self.alive = True

    def apply_gravity(self, planets):
        total_force = pygame.Vector2(0, 0)
        for planet in planets:
            dir_vector = planet.pos - self.pos
            distance_sq = max(dir_vector.length_squared(), 100)  # 너무 가까우면 힘 과다
            force_magnitude = G * planet.mass / distance_sq
            force = dir_vector.normalize() * force_magnitude
            total_force += force
        self.acc = total_force

    def apply_input(self, keys):
        thrust = pygame.Vector2(0, 0)
        if keys[pygame.K_LEFT]:
            thrust.x -= SHIP_THRUST
        if keys[pygame.K_RIGHT]:
            thrust.x += SHIP_THRUST
        if keys[pygame.K_UP]:
            thrust.y -= SHIP_THRUST
        if keys[pygame.K_DOWN]:
            thrust.y += SHIP_THRUST
        self.acc += thrust

    def update(self, planets, dt, keys):
        if not self.alive:
            return
        self.apply_gravity(planets)
        self.apply_input(keys)
        self.vel += self.acc * dt
        self.pos += self.vel * dt
        self.time_alive += dt

    def draw(self, surface):
        if self.alive:
            pygame.draw.circle(surface, SHIP_COLOR, (int(self.pos.x), int(self.pos.y)), SHIP_RADIUS)
        else:
            pygame.draw.circle(surface, EXPLOSION_COLOR, (int(self.pos.x), int(self.pos.y)), SHIP_RADIUS * 2)

    def check_collision(self, planets):
        for planet in planets:
            if (self.pos - planet.pos).length() < (PLANET_RADIUS + SHIP_RADIUS):
                self.alive = False
                return True
        return False

# 행성 클래스
class Planet:
    def __init__(self, x, y, mass):
        self.pos = pygame.Vector2(x, y)
        self.mass = mass

    def draw(self, surface):
        pygame.draw.circle(surface, PLANET_COLOR, (int(self.pos.x), int(self.pos.y)), PLANET_RADIUS)

# 게임 객체 초기화
ship = Spaceship(WIDTH // 2, HEIGHT - 50)
planets = [
    Planet(random.randint(100, WIDTH - 100), random.randint(100, HEIGHT - 200), random.randint(1000, 5000))
    for _ in range(4)
]

# 게임 루프
running = True
font = pygame.font.SysFont(None, 30)
game_over = False
explosion_timer = 0

while running:
    dt = clock.tick(60) / 1_000  # 초 단위 시간
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT or keys[pygame.K_ESCAPE]:
            running = False

    if not game_over:
        ship.update(planets, dt, keys)
        if ship.check_collision(planets):
            game_over = True
            explosion_timer = 1.5  # 폭발 지속 시간 (초)

    else:
        explosion_timer -= dt
        if explosion_timer <= 0:
            running = False

    # 그리기
    screen.fill(BLACK)
    for planet in planets:
        planet.draw(screen)
    ship.draw(screen)

    # 시간 표시
    label = "Score" if game_over else "Time"
    time_text = font.render(f"{label}: {ship.time_alive:.2f} s", True, WHITE)
    screen.blit(time_text, (10, 10))

    pygame.display.flip()

# 결과 출력
print(f"\n게임 종료! 생존 시간: {ship.time_alive:.2f}초")
pygame.quit()
sys.exit()