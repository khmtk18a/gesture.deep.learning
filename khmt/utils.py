import cv2
import numpy as np
import torch
from mediapipe.python.solutions import drawing_utils, hands, hands_connections
from typing import Optional, Tuple, Callable
from torch import Tensor
from torchvision.transforms import Compose, Resize, ToTensor, ToPILImage, Grayscale


class BreakException(Exception):
    pass


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


_transforms = Compose(
    [ToPILImage(), Grayscale(), Resize((32, 32)), ToTensor()])


def predict(net, image: cv2.Mat):
    tensor: Tensor = _transforms(image)  # type: ignore
    output = net(tensor.unsqueeze(0))
    probs = torch.softmax(output, 1)
    conf, predicted = torch.max(probs, 1)
    return round(float(conf), 2), int(predicted)


def camera(fn: Callable[[cv2.Mat, Tuple[bool, cv2.Mat]], None]):
    with Camera() as cap, hands.Hands(max_num_hands=1) as hand:
        try:
            while cap.isOpened():
                success: bool
                image: cv2.Mat

                success, image = cap.read()

                if not success:
                    raise BreakException(
                        "Can't receive frame (stream end?). Exiting ...")

                image = cv2.flip(image, 1)

                rgb_img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                result = hand.process(rgb_img)

                hand_image: Optional[cv2.Mat] = None
                if result.multi_hand_landmarks:  # type: ignore
                    hand_landmarks = result.multi_hand_landmarks[0]  # type: ignore

                    points = [(int(landmark.x*image.shape[1]), int(landmark.y*image.shape[0]))
                              for landmark in hand_landmarks.landmark]

                    (x, y), r = cv2.minEnclosingCircle(np.array(points))

                    x_min, y_min = int(x - r), int(y - r)
                    x_max, y_max = int(x + r), int(y + r)

                    black_image = np.zeros(image.shape, dtype=np.uint8)
                    thickness = int(r/8)  # thanks to Vu Ding Dung
                    drawing_utils.draw_landmarks(
                        black_image,
                        hand_landmarks,
                        hands_connections.HAND_CONNECTIONS,  # type: ignore
                        drawing_utils.DrawingSpec(thickness=thickness),
                        drawing_utils.DrawingSpec(thickness=thickness)
                    )

                    hand_image = cv2.getRectSubPix(
                        black_image, (x_max - x_min, y_max - y_min), (x, y))

                    del black_image  # release memory

                    image = cv2.rectangle(
                        image, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

                fn(image, (isinstance(hand_image, np.ndarray),
                           hand_image))  # type: ignore

        except BreakException as e:
            print(e)
