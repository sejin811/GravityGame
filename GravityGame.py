import certifi
import pygame
import random
import sys
import os
import requests # 서버 통신용

def resource_path(relative_path):
    """ PyInstaller로 생성된 .app 내부 및 일반 환경의 리소스 경로를 가져옵니다. """
    try:
        # PyInstaller가 생성한 임시 폴더
        base_path = sys._MEIPASS
    except Exception:
        # 일반적인 Python 환경
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# 초기화
pygame.init()

# --- 리소스 경로 설정 ---
font_path = resource_path("NotoSansKR-Regular.ttf")
image_path = resource_path("space_background.jpg")

# --- 화면 설정 ---
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
clock = pygame.time.Clock()
pygame.display.set_caption("Gravity Game - Dense Galaxy")

# --- 이미지 로드 ---
space_bg = pygame.image.load(image_path).convert()
space_bg = pygame.transform.scale(space_bg, (WIDTH, HEIGHT))

# --- 폰트 설정 ---
game_font = pygame.font.Font(font_path, 30)

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
    "points": 0
}

# 고정 가격 (추진력 제외, 추진력은 동적 계산)
upgrade_prices = {
    "fuel_pod_recharge": 10
}

def score_to_coins(score):
    return int(score // 100)

def get_max_fuel_price():
    base_price = 10
    current_level = (upgrade_data["max_fuel"] - 100) // upgrade_effects["max_fuel"]
    return base_price + current_level * 10

def get_fuel_pod_price():
    base_price = 10
    current_level = (upgrade_data["fuel_pod_recharge"] - 50) // upgrade_effects["fuel_pod_recharge"]
    return base_price + current_level * 8

def get_thrust_price():
    base_price = 5
    current_level = (upgrade_data["thrust"] - 100) // upgrade_effects["thrust"]
    return base_price + current_level * 10

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

        if self.pos.x < -MAP_HALF: self.pos.x, self.vel.x = -MAP_HALF, 0
        elif self.pos.x > MAP_HALF: self.pos.x, self.vel.x = MAP_HALF, 0
        if self.pos.y < -MAP_HALF: self.pos.y, self.vel.y = -MAP_HALF, 0
        elif self.pos.y > MAP_HALF: self.pos.y, self.vel.y = MAP_HALF, 0

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
            self.mass, self.color, self.gravity_strength = 5000, RED_COLOR, 1500
        elif planet_type == "blue":
            self.mass, self.color, self.gravity_strength = 3000, BLUE_COLOR, 500
        elif planet_type == "green":
            self.mass, self.color, self.gravity_strength = 4000, GREEN_COLOR, 1000

    def update(self, dt):
        self.pos += self.vel * dt
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
        for _ in range(count * 10): # Limit tries
            x, y = random.randint(-MAP_HALF, MAP_HALF), random.randint(-MAP_HALF, MAP_HALF)
            pos = pygame.Vector2(x, y)
            if pos.length() < PLANET_SAFE_DISTANCE: continue
            if not any((p.pos - pos).length() < (PLANET_RADIUS * 2 + 80) for p in planets):
                planets.append(Planet(x, y, planet_type))
                if len([p for p in planets if p.type == planet_type]) >= count: return
    place_planets(10, "red")
    place_planets(60, "blue")
    place_planets(30, "green")
    return planets

def generate_fuelpods(num_pods):
    return [FuelPod(random.randint(-MAP_HALF, MAP_HALF), random.randint(-MAP_HALF, MAP_HALF)) for _ in range(num_pods)]

def draw_warning(surface, ship, planets, camera_offset):
    for planet in planets:
        if (ship.pos - planet.pos).length() < WARNING_DISTANCE + PLANET_RADIUS:
            draw_pos = planet.pos - camera_offset + pygame.Vector2(WIDTH // 2, HEIGHT // 2)
            pygame.draw.circle(surface, WARNING_COLOR, draw_pos, PLANET_RADIUS + 10, 2)

def draw_minimap(surface, ship, planets, fuelpods):
    minimap_width, minimap_height = int(WIDTH * 0.25), int(HEIGHT * 0.25)
    minimap = pygame.Surface((minimap_width, minimap_height)); minimap.fill(MINIMAP_COLOR)
    center = pygame.Vector2(minimap_width // 2, minimap_height // 2)
    map_top_left_scaled = pygame.Vector2(-MAP_HALF - ship.pos.x, -MAP_HALF - ship.pos.y) * MINIMAP_SCALE + center
    map_size_scaled = MAP_SIZE * MINIMAP_SCALE
    pygame.draw.rect(minimap, WARNING_COLOR, (*map_top_left_scaled, map_size_scaled, map_size_scaled), 2)
    for p in planets: pygame.draw.circle(minimap, p.color, center + (p.pos - ship.pos) * MINIMAP_SCALE, 3)
    for pod in fuelpods:
        if not pod.collected: pygame.draw.circle(minimap, (100, 255, 100), center + (pod.pos - ship.pos) * MINIMAP_SCALE, 2)
    pygame.draw.circle(minimap, SHIP_COLOR, center, 4)
    surface.blit(minimap, (WIDTH - minimap_width - 10, HEIGHT - minimap_height - 10))

def draw_map_boundary_warning(surface, camera_offset):
    top_left = pygame.Vector2(-MAP_HALF, -MAP_HALF) - camera_offset + pygame.Vector2(WIDTH // 2, HEIGHT // 2)
    pygame.draw.rect(surface, WARNING_COLOR, (*top_left, MAP_SIZE, MAP_SIZE), 3)

def load_highscore():
    if os.path.exists(HIGHSCORE_FILE):
        with open(HIGHSCORE_FILE, "r", encoding="utf-8") as f:
            try: return float(f.read())
            except: return 0
    return 0

def save_highscore(score):
    with open(HIGHSCORE_FILE, "w", encoding="utf-8") as f: f.write(str(score))

def send_score_to_server(name, score):
    url = "https://gravity-game-backend.onrender.com/add_score"
    data = {"name": name, "score": score}
    try:
        response = requests.post(url, json=data, timeout=5, verify=certifi.where())
        if response.status_code == 200: print("점수가 성공적으로 서버에 등록되었습니다.")
        else: print(f"서버에 점수 등록 실패: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"서버 연결에 실패했습니다: {e}")

def reset_game():
    global ship, planets, fuelpods, game_over, explosion_timer, shake_timer
    ship, planets, fuelpods = Spaceship(0, 0), generate_planets(), generate_fuelpods(FUEL_POD_COUNT)
    game_over, explosion_timer, shake_timer = False, 0, 0

def draw_button(surface, rect, text, mouse_pos):
    color = (150, 150, 255) if rect.collidepoint(mouse_pos) else (100, 100, 255)
    pygame.draw.rect(surface, color, rect)
    pygame.draw.rect(surface, WHITE, rect, 2)
    font = pygame.font.Font(font_path, 36)
    text_surf = font.render(text, True, WHITE)
    surface.blit(text_surf, text_surf.get_rect(center=rect.center))

def draw_menu(surface, mouse_pos):
    global start_button_rect, instructions_button_rect, upgrade_button_rect, quit_button_rect, highscore
    font = pygame.font.Font(font_path, 72)
    small_font = pygame.font.Font(font_path, 28)
    title_surf = font.render("Gravity Game", True, WHITE)
    surface.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 3 - 50)))
    start_button_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 - 70, 200, 50)
    instructions_button_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2, 200, 50)
    upgrade_button_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 70, 200, 50)
    quit_button_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT - 80, 200, 50)
    draw_button(surface, start_button_rect, "게임 시작", mouse_pos)
    draw_button(surface, instructions_button_rect, "게임 설명", mouse_pos)
    draw_button(surface, upgrade_button_rect, "업그레이드", mouse_pos)
    draw_button(surface, quit_button_rect, "게임 종료", mouse_pos)
    highscore_text = small_font.render(f"최고 기록: {int(highscore)}", True, WHITE)
    surface.blit(highscore_text, (20, HEIGHT - 40))

def draw_instructions(surface, mouse_pos):
    global back_button_rect
    font, title_font = pygame.font.Font(font_path, 28), pygame.font.Font(font_path, 48)
    y, line_height = 50, 35
    title_surf = title_font.render("게임 설명", True, WHITE)
    surface.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, 10))
    planets_info = [("빨간 행성", RED_COLOR, "가장 강한 중력"), ("초록 행성", GREEN_COLOR, "중간 중력"), ("파란 행성", BLUE_COLOR, "가장 약한 중력")]
    for name, color, desc in planets_info:
        pygame.draw.circle(surface, color, (120, y + 10), PLANET_RADIUS // 2)
        surface.blit(font.render(name, True, WHITE), (170, y))
        surface.blit(font.render(desc, True, WHITE), (170, y + 30)); y += 70
    fuel_text = ["우주선은 연료를 사용해 움직입니다.", "연료가 다 떨어지면 움직일 수 없습니다.", "맵 곳곳의 연료 탱크로 보충 가능합니다."]
    for line in fuel_text: surface.blit(font.render(line, True, WHITE), (50, y)); y += line_height
    back_button_rect = pygame.Rect(WIDTH - 120, HEIGHT - 60, 110, 40)
    draw_button(surface, back_button_rect, "뒤로가기", mouse_pos)

def draw_upgrade_menu(surface, mouse_pos):
    global back_button_rect, upgrade_button_areas
    font, title_font = pygame.font.Font(font_path, 28), pygame.font.Font(font_path, 48)
    surface.fill(BLACK)
    title_surf = title_font.render("업그레이드", True, WHITE)
    surface.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, 20))
    names = {"max_fuel": "연료 최대치", "fuel_pod_recharge": "연료 회복량", "thrust": "추진력"}
    prices = {"max_fuel": get_max_fuel_price, "fuel_pod_recharge": get_fuel_pod_price, "thrust": get_thrust_price}
    upgrade_button_areas = {} # Reset areas
    for i, key in enumerate(names.keys()):
        y = 120 + i * (50 + 20)
        price = prices[key]()
        text = f"{names[key]}: {upgrade_data[key]} -> {min(upgrade_data[key] + upgrade_effects[key], UPGRADE_LIMITS[key])} (비용: {price})"
        rect = pygame.Rect(WIDTH // 2 - 180, y, 360, 50)
        color = (100, 100, 255) if rect.collidepoint(mouse_pos) else (80, 80, 180)
        pygame.draw.rect(surface, color, rect); pygame.draw.rect(surface, WHITE, rect, 2)
        surface.blit(font.render(text, True, WHITE), font.render(text, True, WHITE).get_rect(center=rect.center))
        upgrade_button_areas[key] = rect
    coin_surf = font.render(f"현재 코인: {upgrade_data['points']}", True, WHITE)
    surface.blit(coin_surf, (20, HEIGHT - 60))
    back_button_rect = pygame.Rect(WIDTH - 120, HEIGHT - 60, 110, 40)
    draw_button(surface, back_button_rect, "뒤로가기", mouse_pos)

def draw_game_over(surface, mouse_pos, score):
    global restart_button_rect
    font, small_font = pygame.font.Font(font_path, 48), pygame.font.Font(font_path, 32)
    text_surf = font.render("게임 오버", True, EXPLOSION_COLOR)
    surface.blit(text_surf, text_surf.get_rect(center=(WIDTH // 2, HEIGHT // 3)))
    score_surf = small_font.render(f"점수: {int(score)}", True, WHITE)
    surface.blit(score_surf, score_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
    restart_button_rect = pygame.Rect(WIDTH // 2 - 120, HEIGHT // 2 + 80, 240, 50)
    draw_button(surface, restart_button_rect, "메뉴로 돌아가기", mouse_pos)

def draw_fuel_bar(surface, fuel):
    bar_width, bar_height, x, y = 200, 20, 10, 10
    fuel_ratio = fuel / upgrade_data["max_fuel"]
    pygame.draw.rect(surface, (50, 50, 50), (x, y, bar_width, bar_height))
    pygame.draw.rect(surface, (0, 255, 0), (x, y, bar_width * fuel_ratio, bar_height))
    fuel_text = game_font.render(f"연료: {int(fuel)}/{upgrade_data['max_fuel']}", True, WHITE)
    surface.blit(fuel_text, (x + 5, y + 22))

def draw_score(surface, score):
    score_text = game_font.render(f"{player_name} 점수: {int(score)}", True, WHITE)
    surface.blit(score_text, (WIDTH - 250, 10))

def main():
    global game_state, upgrade_button_areas, ship, planets, fuelpods, game_over, explosion_timer, shake_timer, highscore, fullscreen, player_name, input_text, WIDTH, HEIGHT, screen, space_bg
    fullscreen, player_name, input_text, game_state = False, "", "", "enter_name"
    upgrade_button_areas, score = {}, 0
    reset_game()
    highscore = load_highscore()
    running = True
    while running:
        dt = clock.tick(60) / 1000
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = event.w, event.h
                mode = pygame.FULLSCREEN if fullscreen else pygame.RESIZABLE
                screen = pygame.display.set_mode((WIDTH, HEIGHT), mode)
                bg_img = pygame.image.load(resource_path("space_background.jpg")).convert()
                space_bg = pygame.transform.scale(bg_img, (WIDTH, HEIGHT))
            elif event.type == pygame.KEYDOWN:
                if game_state == "enter_name":
                    if event.key == pygame.K_RETURN:
                        player_name = input_text.strip()
                        if player_name: game_state = "menu"
                    elif event.key == pygame.K_BACKSPACE: input_text = input_text[:-1]
                    elif len(input_text) < 12 and event.unicode.isprintable(): input_text += event.unicode
                if event.key == pygame.K_F11:
                    fullscreen = not fullscreen
                    mode = pygame.FULLSCREEN if fullscreen else pygame.RESIZABLE
                    screen = pygame.display.set_mode((WIDTH, HEIGHT), mode)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game_state == "menu":
                    if start_button_rect.collidepoint(mouse_pos): reset_game(); game_state = "playing"
                    elif instructions_button_rect.collidepoint(mouse_pos): game_state = "instructions"
                    elif upgrade_button_rect.collidepoint(mouse_pos): game_state = "upgrade"
                    elif quit_button_rect.collidepoint(mouse_pos): running = False
                elif game_state in ["instructions", "upgrade"]:
                    if back_button_rect.collidepoint(mouse_pos): game_state = "menu"
                    elif game_state == "upgrade":
                        for key, rect in upgrade_button_areas.items():
                            if rect.collidepoint(mouse_pos):
                                prices = {"max_fuel": get_max_fuel_price, "fuel_pod_recharge": get_fuel_pod_price, "thrust": get_thrust_price}
                                price = prices[key]()
                                if upgrade_data["points"] >= price and upgrade_data[key] < UPGRADE_LIMITS[key]:
                                    upgrade_data["points"] -= price
                                    upgrade_data[key] += upgrade_effects[key]
                elif game_state == "game_over":
                    if restart_button_rect.collidepoint(mouse_pos): game_state = "menu"

        screen.blit(space_bg, (0, 0))
        if game_state == "enter_name":
            font = pygame.font.Font(font_path, 40)
            screen.fill((0, 0, 30))
            prompt = font.render("당신의 이름을 입력하세요:", True, WHITE)
            name_display = font.render(input_text + "|", True, (200, 200, 0))
            screen.blit(prompt, prompt.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 80)))
            screen.blit(name_display, name_display.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))
        elif game_state == "menu": draw_menu(screen, mouse_pos)
        elif game_state == "instructions": draw_instructions(screen, mouse_pos)
        elif game_state == "upgrade": draw_upgrade_menu(screen, mouse_pos)
        elif game_state == "playing":
            keys = pygame.key.get_pressed()
            ship.update(planets, dt, keys)
            for p in planets: p.update(dt)
            for pod in fuelpods: pod.check_collect(ship)
            if ship.alive and ship.check_collision(planets):
                game_over, explosion_timer, shake_timer = True, 1.5, 0.3
            score = ship.distance_traveled / 10
            if not hasattr(ship, 'last_coin_score'): ship.last_coin_score = 0
            coin_diff = score_to_coins(score) - ship.last_coin_score
            if coin_diff > 0:
                upgrade_data["points"] += coin_diff
                ship.last_coin_score += coin_diff
            camera_offset = pygame.Vector2(ship.pos)
            if shake_timer > 0:
                shake_timer -= dt
                camera_offset += pygame.Vector2(random.randint(-10, 10), random.randint(-10, 10))
            for p in planets: p.draw(screen, camera_offset)
            for pod in fuelpods: pod.draw(screen, camera_offset)
            ship.draw(screen, camera_offset)
            draw_warning(screen, ship, planets, camera_offset)
            draw_minimap(screen, ship, planets, fuelpods)
            draw_map_boundary_warning(screen, camera_offset)
            draw_fuel_bar(screen, ship.fuel)
            draw_score(screen, score)
            if not ship.alive:
                game_state = "game_over"
                if score > highscore:
                    highscore = score
                    save_highscore(score)
                send_score_to_server(player_name, score)
        elif game_state == "game_over":
            draw_game_over(screen, mouse_pos, score)
        pygame.display.flip()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()