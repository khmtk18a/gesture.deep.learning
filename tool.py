import click, cv2, numpy as np
from khmt import Camera, cropped_frame
from mediapipe.python.solutions import drawing_utils, hands, hands_connections

@click.group()
def main():
    pass

@main.command()
@click.option('-n', default=100, help='Number of capture images', type=int)
@click.option('-c', default=0, help='Class of images', type=int)
def generate(n: int, c: int):
    i = 0
    isCapture = False
    with Camera() as cap, hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as hand:
        while cap.isOpened() and i < n:
            success: bool; image: cv2.Mat
            success, image = cap.read()

            if not success:
                print("Ignoring empty camera frame.")
                continue

            image = cv2.flip(image, 1)

            x_offset, y_offset = image.shape[1] - 300, 0

            cv2.rectangle(image, (x_offset, y_offset), (x_offset+300, y_offset+300), (255, 0, 0))
            cv2.putText(image, f'{i}/{n}', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            cv2.imshow('camera', image)

            area = cropped_frame(image, x_offset, y_offset, 300, 300)
            area = cv2.cvtColor(area, cv2.COLOR_BGR2RGB)
            area.flags.writeable = False
            result = hand.process(area)


            handArea = np.zeros((300, 300, 3), np.uint8)
            if result.multi_hand_landmarks: # type: ignore
                for hand_landmarks in result.multi_hand_landmarks: # type: ignore
                    drawing_utils.draw_landmarks(
                        handArea,
                        hand_landmarks,
                        hands_connections.HAND_CONNECTIONS, # type: ignore
                        drawing_utils.DrawingSpec(thickness=10),
                        drawing_utils.DrawingSpec(thickness=10)
                    )
            cv2.imshow('hand', handArea)

            if isCapture:
                output = cv2.resize(handArea, (32,32))
                cv2.imwrite(f"./data/{c}/{i}.jpg", output)
                i += 1

            match cv2.waitKey(5) & 0xFF:
                case 115:
                    isCapture = True
                case 27:
                    break

if __name__ == '__main__':
    main()
