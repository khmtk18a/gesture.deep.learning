from typing import Tuple
import threading
import pygame
from random import randrange as rnd, randint
import  cv2, torch
from khmt import camera, predict, BreakException

running = True
current_image = None

def game():
    global action, running, current_image
# Ratio between width and height
    ratio = 4.5/8

    pygame.init()

# Height and Width
    HEIGHT = int(pygame.display.Info().current_h * 0.8)
    WIDTH  = int(HEIGHT * ratio)

# Fps setting
    clock = pygame.time.Clock()
    fps:int = 24

# Screen setting
    sc      = pygame.display.set_mode((WIDTH, HEIGHT))

# Background setting
    ranBg   = randint(0, 4)
    bg      = pygame.image.load(f"./bg/{ranBg}.jpg").convert()
    bg_ratio= bg.get_width() / bg.get_height()
    bg_width= HEIGHT * bg_ratio
    bg_height= HEIGHT
    bg      = pygame.transform.scale(bg, (bg_width, bg_height))

# Block setting
    lines   = 6
    blocks_in_line = 5
    space_between_blocks:float = WIDTH / blocks_in_line * 0.1
    block_width:float = WIDTH / blocks_in_line
    block_height:float = block_width / 2 + space_between_blocks
    real_block_width:float = block_width - 2 * space_between_blocks
    real_block_height:float = real_block_width / 2

# Create blocks
    block_list:list = [pygame.Rect(space_between_blocks + block_width * i, space_between_blocks + block_height * j,
                            real_block_width, real_block_height) for i in range(blocks_in_line) for j in range(lines)]
    color_list:list = [(rnd(30, 256), rnd(30, 256), rnd(30, 256))
                for i in range(10) for j in range(4)]

# Paddle settings
    paddle_w = WIDTH/3
    paddle_h = paddle_w/5
    paddle_speed = int(WIDTH/30)
    paddle_margin_bottom = HEIGHT/20
    paddle = pygame.Rect(WIDTH // 2 - paddle_w // 2, HEIGHT -
                        paddle_h - paddle_margin_bottom, paddle_w, paddle_h)

# Ball settings
    ball_radius = HEIGHT/35
    ball_speed = 3
    ball_rect = int(ball_radius * 2 ** 0.5)
    ball = pygame.Rect(rnd(2*ball_rect, WIDTH -2*ball_rect),
                    HEIGHT // 2, ball_rect, ball_rect)
# Direct setting
    dx = 1
    dy =-1

# Title setting
    font = pygame.font.Font('font/font.ttf', int(WIDTH/5))
    title_ready  = font.render('Ready', True, pygame.Color('red'))
    title_ready_x, title_ready_y =  int(WIDTH/2 - title_ready.get_width()/2), int(HEIGHT/2 - title_ready.get_height()/2)
    title_win  = font.render('You win', True, pygame.Color('red'))
    title_win_x, title_win_y =  int(WIDTH/2 - title_win.get_width()/2), int(HEIGHT/2 - title_win.get_height()/2)
    title_lose  = font.render('You lose', True, pygame.Color('red'))
    title_lose_x, title_lose_y =  int(WIDTH/2 - title_lose.get_width()/2), int(HEIGHT/2 - title_lose.get_height()/2)

# Status: ready - play - win - lose
    status = "ready"

    def reset():
    # Reset fps
        nonlocal fps
        fps = 60
    # Reset background
        nonlocal ranBg, bg, bg_ratio, bg_width, bg_height
        ranBg   = randint(0, 4)
        bg      = pygame.image.load(f"./bg/{ranBg}.jpg").convert()
        bg_ratio= bg.get_width() / bg.get_height()
        bg_width= HEIGHT * bg_ratio
        bg_height= HEIGHT
        bg      = pygame.transform.scale(bg, (bg_width, bg_height))
    # Reset block
        nonlocal block_list, color_list
        block_list = [pygame.Rect(space_between_blocks + block_width * i, space_between_blocks + block_height * j,
                            real_block_width, real_block_height) for i in range(blocks_in_line) for j in range(lines)]
        color_list = [(rnd(30, 256), rnd(30, 256), rnd(30, 256))
                for i in range(10) for j in range(4)]
    # Reset paddle
        nonlocal paddle
        paddle = pygame.Rect(WIDTH // 2 - paddle_w // 2, HEIGHT -
                        paddle_h - paddle_margin_bottom, paddle_w, paddle_h)
    # Reset ball & direct
        nonlocal ball, dx, dy
        ball = pygame.Rect(rnd(2*ball_rect, WIDTH - 2*ball_rect),
                        HEIGHT // 2, ball_rect, ball_rect)
        dx, dy = 1, -1




    def detect_collision(dx, dy, ball, rect):
        if dx > 0:
            delta_x = ball.right - rect.left
        else:
            delta_x = rect.right - ball.left
        if dy > 0:
            delta_y = ball.bottom - rect.top
        else:
            delta_y = rect.bottom - ball.top

        if abs(delta_x - delta_y) < 10:
            dx, dy = -dx, -dy
        elif delta_x > delta_y:
            dy = -dy
        elif delta_y > delta_x:
            dx = -dx
        return dx, dy


    while running:
    # Allow quit
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                exit()

    #   Draw background
        sc.blit(bg, (0, 0))
        sc.blit(bg, (bg_width, 0))
        if status == "ready":
            sc.blit(title_ready, (title_ready_x, title_ready_y))
            if action == 2:
                status = 'play'
                continue
        elif status == "win":
            sc.blit(title_win, (title_win_x, title_win_y))
            if action == 2:
                status = 'play'
                continue
        elif status == 'lose':
            sc.blit(title_lose, (title_lose_x, title_lose_y))
            if action == 2:
                status = 'play'
                continue
        else :
        #   Draw blocks
            [pygame.draw.rect(sc, color_list[color], block)
            for color, block in enumerate(block_list)]
            pygame.draw.rect(sc, pygame.Color('darkorange'), paddle)
            pygame.draw.circle(sc, pygame.Color('gold'), ball.center, ball_radius)

            ball.x += ball_speed * dx
            ball.y += ball_speed * dy
        # Collision left right
            if ball.centerx < ball_radius or ball.centerx > WIDTH - ball_radius:
                dx = -dx
            # collision top
            if ball.centery < ball_radius:
                dy = -dy
        # Collision paddle
            if ball.colliderect(paddle) and dy > 0:
                dx, dy = detect_collision(dx, dy, ball, paddle)

        # Collision blocks
            hit_index = ball.collidelist(block_list)
            if hit_index != -1:
                hit_rect = block_list.pop(hit_index)
                hit_color = color_list.pop(hit_index)
                dx, dy = detect_collision(dx, dy, ball, hit_rect)
            # special effect
                hit_rect.inflate_ip(ball.width * 2, ball.height * 2)
                pygame.draw.rect(sc, hit_color, hit_rect)
                fps += 1
        # Win, game over
            if ball.bottom > HEIGHT:
                status = 'lose'
                reset()
            elif not len(block_list):
                status = 'win'
                reset()
                continue
        # Control
            if action == 0 and paddle.left > 0:
                paddle.left -= paddle_speed
            if action == 1 and paddle.right < WIDTH:
                paddle.right += paddle_speed

        if isinstance(current_image, pygame.Surface):
            hand = pygame.transform.scale(current_image, (50, 50)) # type: ignore
            sc.blit(hand, (WIDTH - 50, 0))

        pygame.display.flip()
        clock.tick(fps)



action = -1

net = torch.jit.load('./gesture.pt')  # type: ignore
net.eval()

def game_ctrl(_, hand_detect: Tuple[bool, cv2.Mat]):
    global action, running, current_image
    has_hand, hand_image = hand_detect
    if has_hand:
        conf, predicted = predict(net, hand_image)
        if conf > 0.8:
            action = predicted
        else:
            action = 0
        current_image = pygame.surfarray.make_surface(
            hand_image.transpose((1, 0, 2)))
    else:
        current_image = None

    if not running:
        raise BreakException('Game exited...')



if __name__ == '__main__':
    t = threading.Thread(target=camera, args=(game_ctrl,))
    t.start()
    game()
