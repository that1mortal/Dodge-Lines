import pygame
import os
import random
from itertools import repeat
import asyncio

pygame.init()
pygame.font.init()
pygame.mixer.init()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
ORANGE = (170, 115, 55)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

HEALTH_PACK_MIN = 75
HEALTH_PACK_CHANCE = 1200
HEAL_MIN = 15
HEAL_MAX = 35

FPS = 60

HIT_SOUND = pygame.mixer.Sound(os.path.join('sfx', 'hit.wav'))
WALL_SOUND = pygame.mixer.Sound(os.path.join('sfx', 'wall.wav'))
DEATH_SOUND = pygame.mixer.Sound(os.path.join('sfx', 'death.wav'))
HEALTH_SOUND = pygame.mixer.Sound(os.path.join('sfx', 'health.wav'))
HEALTH_SOUND.set_volume(0.5)
BOUNCER_SOUND = pygame.mixer.Sound(os.path.join('sfx', 'bouncer.wav'))

LOSE_FONT = pygame.font.SysFont('framd', 200)
SUB_TEXT = pygame.font.SysFont('framd', 40)
HEALTH_TEXT = pygame.font.SysFont('framd', 80)
SCORE_TEXT = pygame.font.SysFont('famd', 60)

first = True

trail = []
mini_trail = []
bouncer_trails = []
bouncers_vel = []
health_packs = []
last_bounces = []
speed_packs = []

hit_on_bounce = 0

pu_goal = 100

MAX_MINI_SQUARES = 3

BOUNCER_VEL_X = 8
BOUNCER_VEL_Y = 0
BOUNCER_WIDTH = 25
BOUNCER_HEIGHT = 25
BOUNCER_TRAIL_LEN = 40
BOUNCER_TRAIL_REMOVE = 0.7
BOUNCER_MIN_DMG = 10
BOUNCER_MAX_DMG = 25

MINI_SQUARE_WIDTH = 15
MINI_SQUARE_HEIGHT = 15
MINI_SQUARE_TRAIL_LEN = 2000
MINI_SQUARE_TRAIL_REMOVE = 0.5
MINI_SQUARE_SPEED = 4
MINI_SQUARE_MIN_DMG = 20
MINI_SQUARE_MAX_DMG = 40

TRAIL_LENGTH = 50
SIZE_REMOVE_AMOUNT = 1
PLAYER_WIDTH = 30
PLAYER_HEIGHT = 30
PLAYER_VEL = 8

HEALTH_PACK_SIZE = 25
health_img = pygame.transform.scale(pygame.image.load(os.path.join('pictures', 'health.png')),
                                    (HEALTH_PACK_SIZE, HEALTH_PACK_SIZE))

PU_SPEED_SIZE = 50
speed_img = pygame.transform.scale(pygame.image.load(os.path.join('pictures', 'speed.png')),
                                    (PU_SPEED_SIZE, PU_SPEED_SIZE))
PU_SPEED_SOUND = pygame.mixer.Sound(os.path.join('sfx', 'speed.wav'))

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
shake_screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
screen = shake_screen.copy()
pygame.display.set_caption("Asteriods")

bounce_multiplier = 3

offset = repeat((0, 0))

diff_change = True


class particle():

    def __init__(self, x, y, x_velocity, y_velocity, width, height, color, gravity_scale):
        self.x = x
        self.y = y
        self.x_velocity = x_velocity
        self.y_velocity = y_velocity
        self.width = width
        self.height = height
        self.color = color
        self.gravity_scale = gravity_scale * random.randrange(1, 2)
        self.lifetime = random.randrange(50, 200)
        self.gravity = random.randrange(5, 10)

    def draw(self, display):
        self.lifetime -= 1
        self.gravity -= self.gravity_scale
        self.x += self.x_velocity
        self.y += self.y_velocity * self.gravity
        pygame.draw.rect(display, self.color, (self.x, self.y, self.width, self.height))


particles = []


def draw_window(player, mini_square):
    global trail, mini_trail, health, bouncer_trails, bouncers, offset, health_packs, particles, health_img, speed_packs, speed_img

    screen.fill(BLACK)

    health_text = HEALTH_TEXT.render("Health: " + str(health), 1, WHITE)
    screen.blit(health_text, (SCREEN_WIDTH / 2 - health_text.get_width() / 2, 20))

    score_text = SCORE_TEXT.render("Score: " + str(bounces_survived), 1, WHITE)
    screen.blit(score_text, (20, 20))

    pygame.draw.rect(screen, ORANGE, mini_square)

    pygame.draw.rect(screen, RED, player)

    if len(health_packs) > 0:
        for pack in health_packs:
            screen.blit(health_img, (pack.x, pack.y))
    
    if len(speed_packs) > 0:
        for pack in speed_packs:
            screen.blit(speed_img, (pack.x, pack.y))

    for bouncer in bouncers:
        pygame.draw.rect(screen, BLUE, bouncer)

    index = 0
    for p in particles:
        if p.lifetime == 0:
            particles.pop(index)
        p.draw(screen)
        index += 1

    trail_remove = 0
    i = 0

    for bouncer in bouncer_trails:
        trail_remove = 0
        for t in bouncer:
            pygame.draw.rect(screen, BLUE, (
                t[0] + trail_remove / 2, t[1] + trail_remove / 2, BOUNCER_WIDTH - trail_remove,
                BOUNCER_HEIGHT - trail_remove))
            trail_remove += BOUNCER_TRAIL_REMOVE
        i += 1

    size_remove = 0
    for t in trail:
        pygame.draw.rect(screen, RED, (
            t[0] + size_remove / 2, t[1] + size_remove / 2, PLAYER_WIDTH - size_remove, PLAYER_HEIGHT - size_remove))
        size_remove += SIZE_REMOVE_AMOUNT

    trail_remove = 0
    for t in mini_trail:
        pygame.draw.rect(screen, ORANGE, (
            t[0] + trail_remove / 2, t[1] + trail_remove / 2, MINI_SQUARE_WIDTH - trail_remove / 2,
            MINI_SQUARE_HEIGHT - trail_remove))
        trail_remove += MINI_SQUARE_TRAIL_REMOVE

    shake_screen.blit(screen, next(offset))

    pygame.display.update()


def screen_shake(intensity, amplitude):
    s = -1
    for i in range(0, 3):
        for x in range(0, amplitude, intensity):
            yield x * s, 0
        for x in range(amplitude, 0, intensity):
            yield x * s, 0
        s *= -1
    while True:
        yield 0, 0


def player_movement(player, keys_pressed):
    global PLAYER_VEL, trail, offset, health

    if keys_pressed[pygame.K_w] or keys_pressed[pygame.K_UP]:
        if player.y - PLAYER_VEL > 0:
            player.y -= PLAYER_VEL
        else:
            if not trail[1][1] == player.y:
                WALL_SOUND.play()
                health -= random.randint(2, 6)
                for i in range(15):
                    particles.append(
                        particle(player.x, player.y, random.randrange(-5, 5), random.randrange(-2, 0), 10, 10, RED, 1))
                offset = screen_shake(3, 10)
    if keys_pressed[pygame.K_s] or keys_pressed[pygame.K_DOWN]:
        if player.y + PLAYER_VEL + PLAYER_HEIGHT < SCREEN_HEIGHT:
            player.y += PLAYER_VEL
        else:
            if not trail[1][1] == player.y:
                WALL_SOUND.play()
                health -= random.randint(2, 6)
                for i in range(15):
                    particles.append(
                        particle(player.x, player.y, random.randrange(-5, 5), random.randrange(-2, 0), 10, 10, RED, 1))
                offset = screen_shake(3, 10)
    if keys_pressed[pygame.K_a] or keys_pressed[pygame.K_LEFT]:
        if player.x - PLAYER_VEL > 0:
            player.x -= PLAYER_VEL
        else:
            if not trail[1][0] == player.x:
                WALL_SOUND.play()
                health -= random.randint(2, 6)
                for i in range(15):
                    particles.append(
                        particle(player.x, player.y, random.randrange(-5, 5), random.randrange(-2, 0), 10, 10, RED, 1))
                offset = screen_shake(3, 10)
    if keys_pressed[pygame.K_d] or keys_pressed[pygame.K_RIGHT]:
        if player.x + PLAYER_VEL + PLAYER_WIDTH < SCREEN_WIDTH:
            player.x += PLAYER_VEL
        else:
            if not trail[1][0] == player.x:
                WALL_SOUND.play()
                health -= random.randint(2, 6)
                for i in range(15):
                    particles.append(
                        particle(player.x, player.y, random.randrange(-5, 5), random.randrange(-2, 0), 10, 10, RED, 1))
                offset = screen_shake(3, 10)


def mini_square_movement(player, mini_square):
    global health, offset, MINI_SQUARE_MIN_DMG, MINI_SQUARE_MAX_DMG, particles

    if player.x + PLAYER_WIDTH / 4 - mini_square.x < 0 and not player.x + PLAYER_WIDTH / 4 - mini_square.x == 0:
        mini_square.x -= MINI_SQUARE_SPEED
        if random.randint(1, 300) == 50:
            for i in range(3):
                particles.append(
                    particle(mini_square.x, mini_square.y, random.randrange(-5, 5), random.randrange(-2, 0), 5, 5,
                             ORANGE, 3))
    else:
        mini_square.x += MINI_SQUARE_SPEED
        if random.randint(1, 100) == 50:
            for i in range(3):
                particles.append(
                    particle(mini_square.x, mini_square.y, random.randrange(-5, 5), random.randrange(-2, 0), 5, 5,
                             ORANGE, 3))
    if player.y + PLAYER_HEIGHT / 4 - mini_square.y < 0 and not player.y + PLAYER_HEIGHT / 4 - mini_square.y == 0:
        mini_square.y -= MINI_SQUARE_SPEED
        if random.randint(1, 100) == 50:
            for i in range(3):
                particles.append(
                    particle(mini_square.x, mini_square.y, random.randrange(-5, 5), random.randrange(-2, 0), 5, 5,
                             ORANGE, 3))
    else:
        mini_square.y += MINI_SQUARE_SPEED
        if random.randint(1, 100) == 50:
            for i in range(3):
                particles.append(
                    particle(mini_square.x, mini_square.y, random.randrange(-5, 5), random.randrange(-2, 0), 5, 5,
                             ORANGE, 3))

    if mini_square.colliderect(player):
        health -= random.randint(MINI_SQUARE_MIN_DMG, MINI_SQUARE_MAX_DMG)
        HIT_SOUND.play()
        offset = screen_shake(5, 20)
        for i in range(15):
            particles.append(
                particle(mini_square.x, mini_square.y, random.randrange(-5, 5), random.randrange(-2, 0), 6, 6, ORANGE,
                         1))
        mini_square.x = random.randint(0, SCREEN_WIDTH)
        mini_square.y = random.randint(0, SCREEN_HEIGHT)
        for i in range(30):
            particles.append(
                particle(player.x, player.y, random.randrange(-5, 5), random.randrange(-2, 0), 16, 16, RED, 1))
        for i in range(40):
            particles.append(
                particle(mini_square.x, mini_square.y, random.randrange(-5, 5), random.randrange(-2, 0), 8, 8, ORANGE,
                         0))


async def lose_screen():
    global run, bounces_survived, bounce_multiplier

    lose_text = LOSE_FONT.render("You Died!", 1, RED)
    sub_text = SUB_TEXT.render("Press Space to play again", 1, WHITE)
    score_text = SCORE_TEXT.render("Score: " + str(bounces_survived), 1, WHITE)
    if bounce_multiplier == 4:
        diff_text = SCORE_TEXT.render("Easy Difficulty", 1, GREEN)
    if bounce_multiplier == 3:
        diff_text = SCORE_TEXT.render("Medium Diffuculty", 1, ORANGE)
    if bounce_multiplier == 2:
        diff_text = SCORE_TEXT.render("Hard Difficulty", 1, RED)
    if bounce_multiplier == 8:
        diff_text = SCORE_TEXT.render("R*tard Mode", 1, BLUE)

    dead = True

    while dead:

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    dead = False

        await asyncio.sleep(0)

        screen.fill(BLACK)
        screen.blit(lose_text,
                    (SCREEN_WIDTH / 2 - lose_text.get_width() / 2, SCREEN_HEIGHT / 2 - lose_text.get_height() / 2))
        screen.blit(sub_text,
                    (SCREEN_WIDTH / 2 - sub_text.get_width() / 2, SCREEN_HEIGHT / 2 - sub_text.get_height() / 2 + 160))
        screen.blit(score_text, (
            SCREEN_WIDTH / 2 - score_text.get_width() / 2, SCREEN_HEIGHT / 2 - score_text.get_height() / 2 - 140))
        screen.blit(diff_text, (SCREEN_WIDTH / 2 - diff_text.get_width() / 2, 100))
        shake_screen.blit(screen, (0, 0))
        pygame.display.update()
        run = False


def bouncer_movement(player):
    global bouncers, BOUNCER_VEL_X, BOUNCER_VEL_Y, bounces_survived, bouncers_vel, health, can_dmg, hit_on_bounce, offset, BOUNCER_MIN_DMG, BOUNCER_MAX_DMG, bouncer_trails, last_bounces

    index = 0
    for bouncer in bouncers:
        bouncer.x += bouncers_vel[index][0]
        bouncer.y += bouncers_vel[index][1]
        if bouncer.x + bouncer.width >= SCREEN_WIDTH and not last_bounces[index] == 'right':
            bouncers_vel[index][0] *= -1
            bouncers_vel[index][0] += random.randint(-4, 0)
            bouncers_vel[index][1] += random.choice([-1, 1])
            bouncers_vel[index][1] += (1 + random.randint(-5, 4))
            last_bounces[index] = "right"
            for i in range(3):
                particles.append(
                    particle(bouncer.x, bouncer.y, random.randrange(-5, 5), random.randrange(-2, 0), 5, 5, BLUE, 1))
            bounces_survived += 1
        elif bouncer.x <= 0 and not last_bounces[index] == 'left':
            bouncers_vel[index][0] *= -1
            bouncers_vel[index][0] += random.randint(0, 4)
            bouncers_vel[index][1] += random.choice([-1, 1])
            bouncers_vel[index][1] *= (1 + random.randint(-5, 4))
            last_bounces[index] = "left"
            for i in range(3):
                particles.append(
                    particle(bouncer.x, bouncer.y, random.randrange(-5, 5), random.randrange(-2, 0), 5, 5, BLUE, 1))
            bounces_survived += 1
        if bouncer.y + bouncer.height >= SCREEN_HEIGHT and not last_bounces[index] == 'down':
            bouncers_vel[index][1] *= -1
            bouncers_vel[index][1] += random.randint(-4, 0)
            bouncers_vel[index][0] += random.choice([-1, 1])
            bouncers_vel[index][0] *= (1 + random.randint(-5, 4))
            last_bounces[index] = "down"
            for i in range(3):
                particles.append(
                    particle(bouncer.x, bouncer.y, random.randrange(-5, 5), random.randrange(-2, 0), 5, 5, BLUE, 1))
            bounces_survived += 1
        elif bouncer.y <= 0 and not last_bounces[index] == 'up':
            bouncers_vel[index][1] *= -1
            bouncers_vel[index][1] += random.randint(0, 4)
            bouncers_vel[index][0] += random.choice([-1, 1])
            bouncers_vel[index][0] *= (1 + random.randint(-5, 4))
            last_bounces[index] = "up"
            for i in range(3):
                particles.append(
                    particle(bouncer.x, bouncer.y, random.randrange(-5, 5), random.randrange(-2, 0), 5, 5, BLUE, 1))
            bounces_survived += 1
        if bouncers_vel[index][0] > 10:
            bouncers_vel[index][0] = 10
        if bouncers_vel[index][1] > 10:
            bouncers_vel[index][1] = 10
        if bouncers_vel[index][0] < -10:
            bouncers_vel[index][0] = -10
        if bouncers_vel[index][1] < -10:
            bouncers_vel[index][1] = -10
        if bouncer.colliderect(player):
            if hit_on_bounce < bounces_survived - len(bouncers):
                health -= random.randint(BOUNCER_MIN_DMG, BOUNCER_MAX_DMG)
                HIT_SOUND.play()
                for i in range(30):
                    particles.append(
                        particle(player.x, player.y, random.randrange(-5, 5), random.randrange(-2, 0), 10, 10, RED, 1))
                offset = screen_shake(5, 20)
                hit_on_bounce = bounces_survived
        index += 1

def health_handler(player):
    global health, health_packs

    index = 0
    for pack in health_packs:
        if pack.colliderect(player):
            health += random.randint(HEAL_MIN, HEAL_MAX)
            health_packs.pop(index)
            HEALTH_SOUND.play()
            for i in range(30):
                particles.append(
                    particle(player.x, player.y, random.randrange(-5, 5), random.randrange(-1, 0), 10, 10, GREEN, 0))
            if health > 100:
                health = 100

        index += 1

def pu_speed_handler(player):
    global PLAYER_VEL, speed_packs

    index = 0
    for pack in speed_packs:
        if pack.colliderect(player):
            PLAYER_VEL += random.randint(1, 3)
            PU_SPEED_SOUND.play()
            speed_packs.pop(index)
            for i in range(50):
                particles.append(
                    particle(player.x, player.y, random.randrange(-5, 5), random.randrange(-1, 0), 10, 10, BLUE, 0))
        index += 1

async def main():
    global trail, bounces_survived, mini_trail, health, run, bouncer_trails, bouncers, bouncers_vel, hit_on_bounce, health_packs, diff_change, first, particles, last_bounces, health_img, HEALTH_PACK_SIZE, offset, bounce_multiplier, PLAYER_VEL, MINI_SQUARE_SPEED, HEAL_MAX, HEAL_MIN, HEALTH_PACK_CHANCE, MINI_SQUARE_MIN_DMG, MINI_SQUARE_MAX_DMG, pu_goal, speed_packs, PU_SPEED_SIZE

    pause = False

    health = 100

    first = True

    run = True

    last_bounces = [""]

    speed_packs = []

    health_packs = []

    bounce_multiplier = 3

    if first == True:
        while first:
            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        bounce_multiplier = 4
                        PLAYER_VEL = 12
                        MINI_SQUARE_MIN_DMG = 10
                        MINI_SQUARE_MAX_DMG = 25
                        MINI_SQUARE_SPEED = 4
                        HEALTH_PACK_MIN = 90
                        health_img = pygame.transform.scale(pygame.image.load(os.path.join('pictures', 'health.png')), (40, 40))
                        HEAL_MIN = 30
                        HEAL_MAX = 50
                        HEALTH_PACK_SIZE = 40
                        HEALTH_PACK_CHANCE = 2500
                        first = False
                    if event.key == pygame.K_2:
                        bounce_multiplier = 3
                        PLAYER_VEL = 10
                        MINI_SQUARE_MIN_DMG = 10
                        MINI_SQUARE_MAX_DMG = 25
                        MINI_SQUARE_SPEED = 5
                        HEALTH_PACK_MIN = 90
                        health_img = pygame.transform.scale(pygame.image.load(os.path.join('pictures', 'health.png')), (25, 25))
                        HEAL_MIN = 20
                        HEAL_MAX = 40
                        HEALTH_PACK_SIZE = 25
                        HEALTH_PACK_CHANCE = 4500
                        first = False
                    if event.key == pygame.K_3:
                        bounce_multiplier = 2
                        PLAYER_VEL = 8
                        MINI_SQUARE_MIN_DMG = 25
                        MINI_SQUARE_MAX_DMG = 45
                        MINI_SQUARE_SPEED = 6
                        HEALTH_PACK_MIN = 45
                        health_img = pygame.transform.scale(pygame.image.load(os.path.join('pictures', 'health.png')), (15, 15))
                        HEAL_MIN = 20
                        HEAL_MAX = 45
                        HEALTH_PACK_SIZE = 15
                        HEALTH_PACK_CHANCE = 5500
                        first = False
                    if event.key == pygame.K_0:
                        bounce_multiplier = 8
                        PLAYER_VEL = 16
                        MINI_SQUARE_MIN_DMG = 2
                        MINI_SQUARE_MAX_DMG = 5
                        MINI_SQUARE_SPEED = 1
                        HEALTH_PACK_MIN = 99
                        health_img = pygame.transform.scale(pygame.image.load(os.path.join('pictures', 'health.png')), (80, 80))
                        HEAL_MIN = 100
                        HEAL_MAX = 100
                        HEALTH_PACK_SIZE = 80
                        HEALTH_PACK_CHANCE = 1
                        first = False
            
            await asyncio.sleep(0)
            diff_text = HEALTH_TEXT.render("1: Easy 2: Medium 3: Hard", 1, WHITE)
            sub_text = SUB_TEXT.render("You can pause by pressing Esc", 1, WHITE)
            continue_text = SUB_TEXT.render("Select a difficulty to continue", 1, WHITE)
            shake_screen.fill(BLACK)
            shake_screen.blit(diff_text, (
                SCREEN_WIDTH / 2 - diff_text.get_width() / 2, SCREEN_HEIGHT / 2 - diff_text.get_height() / 2))
            shake_screen.blit(sub_text, (
                SCREEN_WIDTH / 2 - sub_text.get_width() / 2, SCREEN_HEIGHT / 2 - sub_text.get_height() / 2 - 150))
            shake_screen.blit(continue_text, (
                SCREEN_WIDTH / 2 - continue_text.get_width() / 2,
                SCREEN_HEIGHT / 2 - continue_text.get_height() / 2 + 220))
            pygame.display.update()

    trail = []
    mini_trail = []
    bouncer_trails = []
    bouncers_vel = []

    hit_on_bounce = 0

    clock = pygame.time.Clock()

    bounces_survived = 0
    bounce_limit = 5
    pu_goal = 100

    diff_change = True

    player = pygame.Rect(SCREEN_WIDTH / 2 - PLAYER_WIDTH / 2, SCREEN_HEIGHT / 2 - PLAYER_HEIGHT / 2, PLAYER_WIDTH,
                         PLAYER_HEIGHT)

    randx = random.randint(0, SCREEN_WIDTH)
    randy = random.randint(0, SCREEN_HEIGHT)

    mini_square = pygame.Rect(randx - MINI_SQUARE_WIDTH / 2, randy - MINI_SQUARE_HEIGHT / 2, MINI_SQUARE_WIDTH,
                              MINI_SQUARE_HEIGHT)

    randx = random.randint(0, SCREEN_WIDTH)
    randy = random.randint(0, SCREEN_HEIGHT)
    bouncers = [pygame.Rect(randx - BOUNCER_WIDTH / 2, randy - BOUNCER_WIDTH / 2, BOUNCER_WIDTH, BOUNCER_HEIGHT)]
    bouncers_vel = [[BOUNCER_VEL_X, BOUNCER_VEL_Y]]
    bouncer_trails.append([[randx, randy]])

    while run:

        clock.tick(FPS)

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pause = True

            while pause:
                for event in pygame.event.get():

                    if event.type == pygame.QUIT:
                        pygame.quit()
                        quit()

                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            pause = False
                            draw_window(player, mini_square)
                            pygame.time.delay(2000)
                        elif event.key == pygame.K_TAB:
                            health = 0
                            pause = False
                
                await asyncio.sleep(0)

                screen.fill(BLACK)
                pause_text = HEALTH_TEXT.render("Paused", 1, WHITE)
                restart_text = SCORE_TEXT.render("Press Tab to restart", 1, WHITE)
                sub_text = SCORE_TEXT.render("Press Esc to resume", 1, WHITE)
                screen.blit(pause_text, (
                    SCREEN_WIDTH / 2 - pause_text.get_width() / 2, SCREEN_HEIGHT / 2 - pause_text.get_height() / 2))
                screen.blit(sub_text, (
                    SCREEN_WIDTH / 2 - sub_text.get_width() / 2, SCREEN_HEIGHT / 2 - sub_text.get_height() / 2 + 120))
                screen.blit(restart_text, (SCREEN_WIDTH / 2 - restart_text.get_width() / 2,
                                           SCREEN_HEIGHT / 2 - restart_text.get_height() / 2 - 120))
                shake_screen.blit(screen, next(offset))
                pygame.display.update()

        trail.insert(0, [player.x, player.y])
        if len(trail) > TRAIL_LENGTH:
            trail.pop(TRAIL_LENGTH)

        i = 0
        for bouncer in bouncers:
            bouncer_trails[i].insert(0, [bouncer.x, bouncer.y])
            if len(bouncer_trails[i]) > BOUNCER_TRAIL_LEN:
                bouncer_trails[i].pop(BOUNCER_TRAIL_LEN)
            i += 1

        mini_trail.insert(0, [mini_square.x, mini_square.y])
        if len(mini_trail) > MINI_SQUARE_TRAIL_LEN:
            mini_trail.pop(MINI_SQUARE_TRAIL_LEN)

        if health <= 0:
            health = 0
            draw_window(player, mini_square)
            DEATH_SOUND.play()
            pygame.time.delay(1000)
            await lose_screen()

        if bounces_survived > 5:
            diff_change = False

        if bounces_survived >= bounce_limit:
            randx = random.randint(0, SCREEN_WIDTH)
            randy = random.randint(0, SCREEN_HEIGHT)
            bouncers.append(
                pygame.Rect(randx - BOUNCER_WIDTH / 2, randy - BOUNCER_WIDTH / 2, BOUNCER_WIDTH, BOUNCER_HEIGHT))
            bouncers_vel.append([BOUNCER_VEL_X, BOUNCER_VEL_Y])
            last_bounces.append("")
            bouncer_trails.append([[randx, randy]])
            bounce_limit *= bounce_multiplier
            BOUNCER_SOUND.play()
            for i in range(40):
                particles.append(
                    particle(randx, randy, random.randrange(-5, 5), random.randrange(-2, 0), 10, 10, BLUE, 0))

        if health < HEALTH_PACK_MIN:
            if random.randint(1, HEALTH_PACK_CHANCE) == 1:
                health_packs.append(pygame.Rect(random.randint(HEALTH_PACK_SIZE, SCREEN_WIDTH - HEALTH_PACK_SIZE),
                                                random.randint(15, SCREEN_HEIGHT - 15), HEALTH_PACK_SIZE,
                                                HEALTH_PACK_SIZE))

        if bounces_survived >= pu_goal:
            pu_goal += 100
            if True: # will be a random value when more powerups are added
                speed_packs.append(pygame.Rect(random.randint(PU_SPEED_SIZE, SCREEN_WIDTH - PU_SPEED_SIZE),
                                                random.randint(15, SCREEN_HEIGHT - 15), PU_SPEED_SIZE,
                                                PU_SPEED_SIZE))

        await asyncio.sleep(0)

        keys_pressed = pygame.key.get_pressed()
        player_movement(player, keys_pressed)
        mini_square_movement(player, mini_square)
        bouncer_movement(player)
        health_handler(player)
        pu_speed_handler(player)
        draw_window(player, mini_square)

    await main()


asyncio.run(main())
