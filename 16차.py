import pygame
import random
import sys
import os

# 초기화
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
clock = pygame.time.Clock()
pygame.display.set_caption("Gravity Ship - Dense Galaxy")

# 색상
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
PLANET_RADIUS = 30
SHIP_RADIUS = 8

# 행성 색상
RED_COLOR = (255, 50, 50)
GREEN_COLOR = (100, 255, 100)
BLUE_COLOR = (100, 100, 255)

SHIP_COLOR = (255, 255, 100)
EXPLOSION_COLOR = (255, 100, 100)
WARNING_COLOR = (255, 0, 0)
MINIMAP_COLOR = (50, 50, 50)

# 상수
MAP_SIZE = 5000
MAP_HALF = MAP_SIZE // 2
PLANET_SAFE_DISTANCE = 500

FUEL_MAX = 300
FUEL_CONSUMPTION = 10
FUEL_POD_RECHARGE = 200
FUEL_POD_COUNT = 20

SHIP_THRUST = 150

WARNING_DISTANCE = 120
MINIMAP_SCALE = 0.05

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
            force_magnitude = planet.gravity_strength * planet.mass / distance_sq
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

        # 맵 경계 제한 및 속도 0 처리
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
    def __init__(self, x, y, planet_type):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(random.uniform(-20, 20), random.uniform(-20, 20))
        self.type = planet_type
        if planet_type == "red":
            self.mass = 5000
            self.color = RED_COLOR
            self.gravity_strength = 1500
        elif planet_type == "blue":
            self.mass = 3000
            self.color = BLUE_COLOR
            self.gravity_strength = 500
        elif planet_type == "green":
            self.mass = 4000
            self.color = GREEN_COLOR
            self.gravity_strength = 1000

    def update(self, dt):
        self.pos += self.vel * dt
        # 맵 경계 반사
        if self.pos.x < -MAP_HALF or self.pos.x > MAP_HALF:
            self.vel.x *= -1
            self.pos.x = max(min(self.pos.x, MAP_HALF), -MAP_HALF)
        if self.pos.y < -MAP_HALF or self.pos.y > MAP_HALF:
            self.vel.y *= -1
            self.pos.y = max(min(self.pos.y, MAP_HALF), -MAP_HALF)

    def draw(self, surface, camera_offset):
        draw_pos = self.pos - camera_offset + pygame.Vector2(WIDTH // 2, HEIGHT // 2)
        pygame.draw.circle(surface, self.color, draw_pos, PLANET_RADIUS)


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


def generate_planets():
    planets = []

    def place_planets(count, planet_type):
        tries = 0
        placed = 0
        while placed < count and tries < count * 100:
            tries += 1
            x = random.randint(-MAP_HALF, MAP_HALF)
            y = random.randint(-MAP_HALF, MAP_HALF)
            pos = pygame.Vector2(x, y)
            if pos.length() < PLANET_SAFE_DISTANCE:
                continue
            too_close = any((p.pos - pos).length() < (PLANET_RADIUS * 2 + 80) for p in planets)
            if not too_close:
                planets.append(Planet(x, y, planet_type))
                placed += 1

    place_planets(10, "red")
    place_planets(60, "blue")
    place_planets(30, "green")
    return planets


def generate_fuelpods(num_pods):
    pods = []
    for _ in range(num_pods):
        x = random.randint(-MAP_HALF, MAP_HALF)
        y = random.randint(-MAP_HALF, MAP_HALF)
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

    map_top_left = (-MAP_HALF - ship.pos.x, -MAP_HALF - ship.pos.y)
    map_top_left_scaled = pygame.Vector2(map_top_left) * MINIMAP_SCALE + center

    map_size_scaled = MAP_SIZE * MINIMAP_SCALE

    boundary_rect = pygame.Rect(map_top_left_scaled.x, map_top_left_scaled.y, map_size_scaled, map_size_scaled)
    pygame.draw.rect(minimap, WARNING_COLOR, boundary_rect, 2)

    for planet in planets:
        offset = (planet.pos - ship.pos) * MINIMAP_SCALE
        pos = center + offset
        if 0 <= pos.x < minimap_width and 0 <= pos.y < minimap_height:
            pygame.draw.circle(minimap, planet.color, pos, 3)

    for pod in fuelpods:
        if not pod.collected:
            offset = (pod.pos - ship.pos) * MINIMAP_SCALE
            pos = center + offset
            if 0 <= pos.x < minimap_width and 0 <= pos.y < minimap_height:
                pygame.draw.circle(minimap, (100, 255, 100), pos, 2)

    # === 우주선 위치 (중앙) ===
    pygame.draw.circle(minimap, SHIP_COLOR, center, 4)

    # === 미니맵 붙이기 ===
    surface.blit(minimap, (WIDTH - minimap_width - 10, HEIGHT - minimap_height - 10))


def draw_map_boundary_warning(surface, camera_offset):
    top_left = pygame.Vector2(-MAP_HALF, -MAP_HALF) - camera_offset + pygame.Vector2(WIDTH // 2, HEIGHT // 2)
    rect = pygame.Rect(top_left.x, top_left.y, MAP_SIZE, MAP_SIZE)
    pygame.draw.rect(surface, WARNING_COLOR, rect, 3)


def load_highscore():
    if os.path.exists(HIGHSCORE_FILE):
        with open(HIGHSCORE_FILE, "r", encoding="utf-8") as f:
            try:
                return float(f.read())
            except:
                return 0
    return 0


def save_highscore(score):
    with open(HIGHSCORE_FILE, "w", encoding="utf-8") as f:
        f.write(str(score))


def reset_game():
    global ship, planets, fuelpods, game_over, explosion_timer, shake_timer
    ship = Spaceship(0, 0)
    planets = generate_planets()
    fuelpods = generate_fuelpods(FUEL_POD_COUNT)
    game_over = False
    explosion_timer = 0
    shake_timer = 0


def draw_button(surface, rect, text, mouse_pos):
    color = (150, 150, 255) if rect.collidepoint(mouse_pos) else (100, 100, 255)
    pygame.draw.rect(surface, color, rect)
    pygame.draw.rect(surface, WHITE, rect, 2)
    try:
        font = pygame.font.SysFont("malgungothic", 36)
    except:
        font = pygame.font.SysFont(None, 36)
    text_surf = font.render(text, True, WHITE)
    text_rect = text_surf.get_rect(center=rect.center)
    surface.blit(text_surf, text_rect)


def draw_menu(surface, mouse_pos):
    global start_button_rect, instructions_button_rect
    try:
        font = pygame.font.SysFont("malgungothic", 72)
    except:
        font = pygame.font.SysFont(None, 72)
    title_surf = font.render("Gravity Ship", True, WHITE)
    title_rect = title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 3))
    surface.blit(title_surf, title_rect)

    start_button_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2, 200, 50)
    instructions_button_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 70, 200, 50)

    draw_button(surface, start_button_rect, "게임 시작", mouse_pos)
    draw_button(surface, instructions_button_rect, "게임 설명", mouse_pos)


def draw_instructions(surface, mouse_pos):
    try:
        font = pygame.font.SysFont("malgungothic", 28)
        title_font = pygame.font.SysFont("malgungothic", 48)
    except:
        font = pygame.font.SysFont(None, 28)
        title_font = pygame.font.SysFont(None, 48)

    y = 50
    line_height = 35

    # 타이틀
    title_surf = title_font.render("게임 설명", True, WHITE)
    surface.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, 10))

    planets_info = [
        ("빨간 행성", RED_COLOR, "가장 강한 중력을 가집니다."),
        ("초록 행성", GREEN_COLOR, "중간 정도의 중력을 가집니다."),
        ("파란 행성", BLUE_COLOR, "가장 약한 중력을 가집니다."),
    ]

    circle_x = 120
    text_x = 170

    for name, color, desc in planets_info:
        pygame.draw.circle(surface, color, (circle_x, y + 10), PLANET_RADIUS // 2)
        name_surf = font.render(name, True, WHITE)
        desc_surf = font.render(desc, True, WHITE)
        surface.blit(name_surf, (text_x, y))
        surface.blit(desc_surf, (text_x, y + 30))
        y += 70

    fuel_text = [
        "우주선은 연료를 사용해 움직입니다.",
        "연료가 다 떨어지면 움직일 수 없습니다.",
        "맵 곳곳에 연료 탱크가 있으며,",
        "연료 탱크를 먹으면 연료가 보충됩니다."
    ]
    y += 20
    for line in fuel_text:
        surf = font.render(line, True, WHITE)
        surface.blit(surf, (50, y))
        y += line_height

    global back_button_rect
    back_button_rect = pygame.Rect(WIDTH - 120, HEIGHT - 60, 110, 40)
    draw_button(surface, back_button_rect, "뒤로가기", mouse_pos)


# 한글 폰트 (게임 내 정보용)
try:
    game_font = pygame.font.SysFont("malgungothic", 30)
except:
    game_font = pygame.font.SysFont(None, 30)

# 초기 게임 설정
ship = None
planets = []
fuelpods = []
game_over = False
explosion_timer = 0
shake_timer = 0
highscore = load_highscore()

start_button_rect = None
instructions_button_rect = None
back_button_rect = None

state = "menu"
fullscreen = False  # 전체화면 상태 저장

running = True

while running:
    dt = clock.tick(60) / 1000
    mouse_pos = pygame.mouse.get_pos()
    mouse_pressed = pygame.mouse.get_pressed()
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.VIDEORESIZE and not fullscreen:
            WIDTH, HEIGHT = event.w, event.h
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                fullscreen = not fullscreen
                if fullscreen:
                    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    WIDTH, HEIGHT = screen.get_size()
                else:
                    WIDTH, HEIGHT = 800, 600
                    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

    screen.fill(BLACK)

    if state == "menu":
        draw_menu(screen, mouse_pos)
        if mouse_pressed[0]:
            if start_button_rect and start_button_rect.collidepoint(mouse_pos):
                reset_game()
                state = "playing"
            elif instructions_button_rect and instructions_button_rect.collidepoint(mouse_pos):
                state = "instructions"

    elif state == "instructions":
        draw_instructions(screen, mouse_pos)
        if mouse_pressed[0]:
            if back_button_rect and back_button_rect.collidepoint(mouse_pos):
                state = "menu"

    elif state == "playing":
        shake_offset = pygame.Vector2(0, 0)

        if not game_over:
            ship.update(planets, dt, keys)
            for planet in planets:
                planet.update(dt)
            for pod in fuelpods:
                pod.check_collect(ship)

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
                shake_timer = 1.5
                score = ship.distance_traveled / 10
                if score > highscore:
                    highscore = score
                    save_highscore(highscore)
        else:
            explosion_timer -= dt
            shake_timer -= dt

        if shake_timer > 0:
            shake_offset.x = random.uniform(-8, 8)
            shake_offset.y = random.uniform(-8, 8)

        camera_offset = ship.pos + shake_offset

        # 경계선 경고는 여전히 카메라 기준으로
        draw_map_boundary_warning(screen, camera_offset)

        # 행성과 연료캡슐 먼저 그리기
        for planet in planets:
            planet.draw(screen, camera_offset)
        for pod in fuelpods:
            pod.draw(screen, camera_offset)

        # 게임 오버 텍스트가 행성 뒤로 가지 않도록 게임 오버 텍스트는 이 후에 그림
        draw_warning(screen, ship, planets, camera_offset)
        ship.draw(screen, camera_offset)
        draw_minimap(screen, ship, planets, fuelpods)

        score = ship.distance_traveled / 10
        score_text = game_font.render(f"점수: {score:.0f}", True, WHITE)
        fuel_text = game_font.render(f"연료: {ship.fuel:.1f}", True, WHITE)
        highscore_text = game_font.render(f"최고 기록: {highscore:.0f}", True, WHITE)

        screen.blit(score_text, (10, 10))
        screen.blit(fuel_text, (10, 40))
        screen.blit(highscore_text, (10, 70))

        if game_over:
            try:
                font_gameover = pygame.font.SysFont("malgungothic", 72)
                font_score = pygame.font.SysFont("malgungothic", 48)
            except:
                font_gameover = pygame.font.SysFont(None, 72)
                font_score = pygame.font.SysFont(None, 48)

            go_surf = font_gameover.render("게임 오버", True, WARNING_COLOR)
            go_rect = go_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))
            screen.blit(go_surf, go_rect)

            final_score_surf = font_score.render(f"최종 점수: {score:.0f}", True, WHITE)
            final_score_rect = final_score_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40))
            screen.blit(final_score_surf, final_score_rect)

            restart_button_rect = pygame.Rect(WIDTH // 2 - 220, HEIGHT // 2 + 40, 200, 60)
            quit_button_rect = pygame.Rect(WIDTH // 2 + 20, HEIGHT // 2 + 40, 200, 60)

            draw_button(screen, restart_button_rect, "다시 시작", mouse_pos)
            draw_button(screen, quit_button_rect, "게임 종료", mouse_pos)

            if mouse_pressed[0]:
                if restart_button_rect.collidepoint(mouse_pos):
                    reset_game()
                    state = "playing"
                    game_over = False
                elif quit_button_rect.collidepoint(mouse_pos):
                    running = False

    pygame.display.flip()

pygame.quit()
sys.exit()
