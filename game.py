import threading
import pygame
from random import randrange as rnd, randint

import  cv2, numpy as np, torch
from mediapipe.python.solutions import drawing_utils, hands, hands_connections
from torch import Tensor
from torchvision.transforms import Compose, Grayscale, ToTensor, ToPILImage


class Camera():
    def __init__(self) -> None:
        self.vid = cv2.VideoCapture(0)

    def __enter__(self):
        print('Camera is open.')
        return self.vid

    def __exit__(self, *args):
        self.vid.release()
        cv2.destroyAllWindows()
        print('Camera is closed.')

action = 0


def game():
    global action
# Ratio between width and height
    ratio = 4.5/8

    pygame.init()

# Height and Width 
    HEIGHT = int(pygame.display.Info().current_h * 0.8)
    WIDTH  = int(HEIGHT * ratio)

# Fps setting
    clock = pygame.time.Clock()
    fps:int = 60

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


    while True:
    # Allow quit
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()

    #   Draw background
        sc.blit(bg, (0, 0))
        sc.blit(bg, (bg_width, 0))
        if status == "ready":
            sc.blit(title_ready, (title_ready_x, title_ready_y))
            if action == 1:
                status = 'play'
                continue
        elif status == "win":
            sc.blit(title_win, (title_win_x, title_win_y))
            if action == 1:
                status = 'play'
                continue
        elif status == 'lose':
            sc.blit(title_lose, (title_lose_x, title_lose_y))
            if action == 1:
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
            if action ==2 and paddle.left > 0:
                paddle.left -= paddle_speed
            if action ==3 and paddle.right < WIDTH:
                paddle.right += paddle_speed

        pygame.display.flip()
        clock.tick(fps)




def recognized():
    global action
    net = torch.jit.load('./gesture.pt') # type: ignore
    net.eval()
    transforms = Compose([ToPILImage(), Grayscale(), ToTensor()])
    with Camera() as cap, hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as hand:
        while cap.isOpened():
            success: bool; image: cv2.Mat
            success, image = cap.read()

            if not success:
                print("Ignoring empty camera frame.")
                continue

            image = cv2.flip(image, 1)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False

            background = np.ones(image.shape, np.uint8)
            background = 255* background
            handImage = np.ones((32,32,3), np.uint8)
            handImage = 255* handImage

            result = hand.process(image)

            if result.multi_hand_landmarks: # type: ignore
                for hand_landmarks in result.multi_hand_landmarks: # type: ignore
                
                    points = [(int(landmark.x*image.shape[1]), int(landmark.y*image.shape[0]))
                              for landmark in hand_landmarks.landmark]

                    (x, y), r = cv2.minEnclosingCircle(np.array(points))
                    r = r*1.1
                    x_min, y_min = int(x - r), int(y - r)
                    x_max, y_max = int(x + r), int(y + r)
                    tn = int(r/8)
                    drawing_utils.draw_landmarks(
                        background,
                        hand_landmarks,
                        hands_connections.HAND_CONNECTIONS, # type: ignore
                        drawing_utils.DrawingSpec(
                            color=(0,0,0),
                            thickness=tn),
                        drawing_utils.DrawingSpec(
                            color=(0,0,0),
                            thickness=tn)
                    )
                    try:
                        handImage = cv2.resize(background[y_min: y_max, x_min: x_max ], (32, 32))
                        cv2.rectangle(background, (x_max, y_max), (x_min, y_min), (0, 0, 0))
                        tensor = transforms(handImage)
                        assert isinstance(tensor, Tensor)

                        output = net(tensor.unsqueeze(0))
                        probs = torch.nn.functional.softmax(output, 1)
                        score, predicted = torch.max(probs, 1)
                        if score[0] > 0.9:
                            action = predicted
                        else:
                            action = 0
                    except :
                        pass

            cv2.imshow('camera', background)

            if cv2.waitKey(5) & 0xFF == 115:
                    isCapture = True
            elif  cv2.waitKey(5) & 0xFF == 27:
                    break





if __name__ == '__main__':
    t1 = threading.Thread(target=recognized, args=())
    t1.start()
    game()
    t1.join()
