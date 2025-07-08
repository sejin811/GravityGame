import pygame
import random
import sys
import os


# 초기화
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
clock = pygame.time.Clock()
pygame.display.set_caption("Gravity Game - Dense Galaxy")

space_bg = pygame.image.load("space_background.jpg").convert()
space_bg = pygame.transform.scale(space_bg, (WIDTH, HEIGHT))  # 창 크기에 맞게 조절

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

FUEL_CONSUMPTION = 10
FUEL_POD_COUNT = 20

WARNING_DISTANCE = 120
MINIMAP_SCALE = 0.05

HIGHSCORE_FILE = "highscore.txt"

# 업그레이드 효과 및 제한
upgrade_effects = {
    "max_fuel": 20,
    "fuel_pod_recharge": 10,
    "thrust": 10
}

UPGRADE_LIMITS = {
    "max_fuel": 240,
    "fuel_pod_recharge": 150,
    "thrust": 200
}

# 업그레이드 데이터 초기값 및 코인
upgrade_data = {
    "max_fuel": 100,
    "fuel_pod_recharge": 50,
    "thrust": 100,
    "points": 0  # 코인 수
}

# 고정 가격 (추진력 제외, 추진력은 동적 계산)
upgrade_prices = {
    "fuel_pod_recharge": 10  # 실제 비용은 동적 계산하므로 무시 가능
}

# 한글 폰트 (게임 내 정보용)
try:
    game_font = pygame.font.SysFont("malgungothic", 30)
except:
    game_font = pygame.font.SysFont(None, 30)

def score_to_coins(score):
    return int(score // 100)  # 100점당 1코인 지급

def get_max_fuel_price():
    base_price = 10
    current_level = (upgrade_data["max_fuel"] - 100) // upgrade_effects["max_fuel"]
    return base_price + current_level * 10  # 10, 20, 30, ...

def get_fuel_pod_price():
    base_price = 10
    current_level = (upgrade_data["fuel_pod_recharge"] - 50) // upgrade_effects["fuel_pod_recharge"]
    return base_price + current_level * 8  # 10, 18, 26, ...

def get_thrust_price():
    base_price = 5
    current_level = (upgrade_data["thrust"] - 100) // upgrade_effects["thrust"]
    return base_price + current_level * 10  # 5, 15, 25, ...

class Spaceship:
    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.acc = pygame.Vector2(0, 0)
        self.time_alive = 0
        self.fuel = upgrade_data["max_fuel"]
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
        thrust_val = upgrade_data["thrust"]

        if self.fuel > 0:
            if keys[pygame.K_LEFT]:
                thrust.x -= thrust_val
            if keys[pygame.K_RIGHT]:
                thrust.x += thrust_val
            if keys[pygame.K_UP]:
                thrust.y -= thrust_val
            if keys[pygame.K_DOWN]:
                thrust.y += thrust_val

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
            ship.fuel = min(upgrade_data["max_fuel"], ship.fuel + upgrade_data["fuel_pod_recharge"])

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

    # 우주선 위치 (중앙)
    pygame.draw.circle(minimap, SHIP_COLOR, center, 4)

    # 미니맵 붙이기
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
    global start_button_rect, instructions_button_rect, upgrade_button_rect, quit_button_rect, highscore, small_font
    try:
        font = pygame.font.SysFont("malgungothic", 72)
        small_font = pygame.font.SysFont("malgungothic", 28)
    except:
        font = pygame.font.SysFont(None, 72)
        small_font = pygame.font.SysFont(None, 28)
    title_surf = font.render("Gravity Game", True, WHITE)
    title_rect = title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 3 - 50))
    surface.blit(title_surf, title_rect)

    start_button_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 70, 200, 50)
    instructions_button_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2, 200, 50)
    upgrade_button_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 70, 200, 50)
    quit_button_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT - 80, 200, 50)

    draw_button(surface, start_button_rect, "게임 시작", mouse_pos)
    draw_button(surface, instructions_button_rect, "게임 설명", mouse_pos)
    draw_button(surface, upgrade_button_rect, "업그레이드", mouse_pos)
    draw_button(surface, quit_button_rect, "게임 종료", mouse_pos)

    highscore_text = small_font.render(f"최고 기록: {int(highscore)}", True, WHITE)
    surface.blit(highscore_text, (20, HEIGHT - 40))

    
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

def draw_upgrade_menu(surface, mouse_pos):
    try:
        font = pygame.font.SysFont("malgungothic", 32)
        title_font = pygame.font.SysFont("malgungothic", 48)
    except:
        font = pygame.font.SysFont(None, 32)
        title_font = pygame.font.SysFont(None, 48)

    surface.fill(BLACK)

    title_surf = title_font.render("업그레이드", True, WHITE)
    surface.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, 20))

    names = {
        "max_fuel": "연료 최대치 증가",
        "fuel_pod_recharge": "연료 탱크 회복량 증가",
        "thrust": "추진력 증가"
    }

    keys_list = ["max_fuel", "fuel_pod_recharge", "thrust"]

    y_start = 120
    btn_width, btn_height = 280, 50
    btn_x = WIDTH // 2 - btn_width // 2

    for i, key in enumerate(keys_list):
        y = y_start + i * (btn_height + 20)

        # 가격 계산
        if key == "max_fuel":
            price = get_max_fuel_price()
        elif key == "fuel_pod_recharge":
            price = get_fuel_pod_price()
        elif key == "thrust":
            price = get_thrust_price()
        else:
            price = 10

        # 현재 레벨 및 최대치 표시
        current = upgrade_data[key]
        max_val = UPGRADE_LIMITS[key]
        text = f"{names[key]}: {current} -> {min(current + upgrade_effects[key], max_val)} (비용: {price} 코인)"

        rect = pygame.Rect(btn_x, y, btn_width, btn_height)
        pygame.draw.rect(surface, (100, 100, 255) if rect.collidepoint(mouse_pos) else (80, 80, 180), rect)
        pygame.draw.rect(surface, WHITE, rect, 2)

        text_surf = font.render(text, True, WHITE)
        text_rect = text_surf.get_rect(center=rect.center)
        surface.blit(text_surf, text_rect)

        # 버튼 영역 저장
        upgrade_button_areas[key] = rect

    # 코인 표시
    coin_text = f"현재 코인: {upgrade_data['points']}"
    coin_surf = font.render(coin_text, True, WHITE)
    surface.blit(coin_surf, (20, HEIGHT - 60))

    global back_button_rect
    back_button_rect = pygame.Rect(WIDTH - 120, HEIGHT - 60, 110, 40)
    draw_button(surface, back_button_rect, "뒤로가기", mouse_pos)

def draw_game_over(surface, mouse_pos, score):
    try:
        font = pygame.font.SysFont("malgungothic", 48)
        small_font = pygame.font.SysFont("malgungothic", 32)
    except:
        font = pygame.font.SysFont(None, 48)
        small_font = pygame.font.SysFont(None, 32)

    text_surf = font.render("게임 오버", True, EXPLOSION_COLOR)
    text_rect = text_surf.get_rect(center=(WIDTH // 2, HEIGHT // 3))
    surface.blit(text_surf, text_rect)

    score_text = f"점수: {int(score)}"
    score_surf = small_font.render(score_text, True, WHITE)
    score_rect = score_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    surface.blit(score_surf, score_rect)

    global restart_button_rect
    restart_button_rect = pygame.Rect(WIDTH // 2 - 120, HEIGHT // 2 + 80, 240, 50)
    draw_button(surface, restart_button_rect, "메뉴로 돌아가기", mouse_pos)

def draw_fuel_bar(surface, fuel):
    bar_width = 200
    bar_height = 20
    x = 10
    y = 10
    fuel_ratio = fuel / upgrade_data["max_fuel"]
    pygame.draw.rect(surface, (50, 50, 50), (x, y, bar_width, bar_height))
    pygame.draw.rect(surface, (0, 255, 0), (x, y, bar_width * fuel_ratio, bar_height))
    fuel_text = game_font.render(f"연료: {int(fuel)}/{upgrade_data['max_fuel']}", True, WHITE)
    surface.blit(fuel_text, (x + 5, y + 22))

def draw_score(surface, score):
    score_text = game_font.render(f"점수: {int(score)}", True, WHITE)
    surface.blit(score_text, (WIDTH - 180, 10))

def main():
    global game_state, upgrade_button_areas, ship, planets, fuelpods, game_over
    global explosion_timer, shake_timer, highscore
    global fullscreen  # 추가: 전체화면 상태 저장 변수

    fullscreen = False  # 시작은 창모드

    upgrade_button_areas = {}

    # 게임 상태: "menu", "instructions", "playing", "game_over", "upgrade"
    game_state = "menu"

    reset_game()

    highscore = load_highscore()

    score = 0

    running = True
    while running:
        dt = clock.tick(60) / 1000  # 초 단위 dt
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            elif event.type == pygame.VIDEORESIZE:
                global WIDTH, HEIGHT, screen, space_bg
                WIDTH, HEIGHT = event.w, event.h
                space_bg = pygame.transform.scale(pygame.image.load("space_background.jpg").convert(), (WIDTH, HEIGHT))
                if fullscreen:
                    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
                else:
                    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game_state == "menu":
                    screen.blit(space_bg, (0, 0))
                    draw_menu(screen, mouse_pos)
                    if start_button_rect.collidepoint(mouse_pos):
                        reset_game()
                        game_state = "playing"
                    elif instructions_button_rect.collidepoint(mouse_pos):
                        game_state = "instructions"
                    elif upgrade_button_rect.collidepoint(mouse_pos):
                        game_state = "upgrade"
                    elif quit_button_rect.collidepoint(mouse_pos):  # 👈 추가
                        pygame.quit()
                        sys.exit()
                elif game_state == "instructions":
                    if back_button_rect.collidepoint(mouse_pos):
                        game_state = "menu"
                elif game_state == "upgrade":
                    if back_button_rect.collidepoint(mouse_pos):
                        game_state = "menu"
                    else:
                        for key, rect in upgrade_button_areas.items():
                            if rect.collidepoint(mouse_pos):
                                # 업그레이드 가능 여부 체크 및 실행
                                if key == "max_fuel":
                                    price = get_max_fuel_price()
                                    if upgrade_data["points"] >= price and upgrade_data[key] < UPGRADE_LIMITS[key]:
                                        upgrade_data["points"] -= price
                                        upgrade_data[key] = min(upgrade_data[key] + upgrade_effects[key], UPGRADE_LIMITS[key])
                                        if key == "max_fuel":
                                            ship.fuel = min(ship.fuel, upgrade_data[key])
                                elif key == "fuel_pod_recharge":
                                    price = get_fuel_pod_price()
                                    if upgrade_data["points"] >= price and upgrade_data[key] < UPGRADE_LIMITS[key]:
                                        upgrade_data["points"] -= price
                                        upgrade_data[key] = min(upgrade_data[key] + upgrade_effects[key], UPGRADE_LIMITS[key])
                                elif key == "thrust":
                                    price = get_thrust_price()
                                    if upgrade_data["points"] >= price and upgrade_data[key] < UPGRADE_LIMITS[key]:
                                        upgrade_data["points"] -= price
                                        upgrade_data[key] = min(upgrade_data[key] + upgrade_effects[key], UPGRADE_LIMITS[key])
                elif game_state == "game_over":
                    if restart_button_rect.collidepoint(mouse_pos):
                        game_state = "menu"

        screen.blit(space_bg, (0, 0))

        if game_state == "menu":
            draw_menu(screen, mouse_pos)
        elif game_state == "instructions":
            draw_instructions(screen, mouse_pos)
        elif game_state == "upgrade":
            draw_upgrade_menu(screen, mouse_pos)
        elif game_state == "playing":
            keys = pygame.key.get_pressed()
            ship.update(planets, dt, keys)
            for planet in planets:
                planet.update(dt)
            for pod in fuelpods:
                pod.check_collect(ship)

            # 충돌 체크
            if ship.alive and ship.check_collision(planets):
                game_over = True
                explosion_timer = 1.5
                shake_timer = 0.3

            # 점수 (거리 traveled)
            score = ship.distance_traveled / 10
            
            if not hasattr(ship, 'last_coin_score'):
                ship.last_coin_score = 0
            
            current_coin_score = score_to_coins(score)
            coin_diff = current_coin_score - ship.last_coin_score
            if coin_diff > 0:
             upgrade_data["points"] += coin_diff
             ship.last_coin_score = current_coin_score

            # 화면 흔들림 (충돌 시)
            camera_offset = pygame.Vector2(ship.pos)
            if shake_timer > 0:
                shake_timer -= dt
                camera_offset += pygame.Vector2(random.randint(-10, 10), random.randint(-10, 10))
            else:
                shake_timer = 0

            # 그리기
            for planet in planets:
                planet.draw(screen, camera_offset)
            for pod in fuelpods:
                pod.draw(screen, camera_offset)

            ship.draw(screen, camera_offset)

            draw_warning(screen, ship, planets, camera_offset)
            draw_minimap(screen, ship, planets, fuelpods)
            draw_map_boundary_warning(screen, camera_offset)

            draw_fuel_bar(screen, ship.fuel)
            draw_score(screen, score)

            # 게임 오버 처리
            if not ship.alive:
                game_state = "game_over"
                # 최고점수 저장
                highscore = load_highscore()
                if score > highscore:
                    save_highscore(score)

        elif game_state == "game_over":
            draw_game_over(screen, mouse_pos, score)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
