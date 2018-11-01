import argparse
import socket

import cv2
import time

import numpy as np
import requests

MAX_SIZE = 65536 - 8  # less 8 bytes of video time
GPU_SERVER = '10.1.0.2'


def arg_parse():
    parser = argparse.ArgumentParser(description='Raspberry client')
    parser.add_argument("--video", help="Path to video file", default=0)
    parser.add_argument("--fps", help="Set video FPS", type=int, default=14)
    parser.add_argument("--gray", help="Convert video into gray scale", action="store_true")
    parser.add_argument("--rasp_simulator", help="This is not a Raspberry Pi", action="store_true")

    return parser.parse_args()


def get_id():
    # TODO: get zerotier id
    return 1


def connected_to_internet(url='http://www.google.com/', timeout=5):
    try:
        _ = requests.get(url, timeout=timeout)
        return True
    except requests.ConnectionError:
        print("No internet connection available.")
    return False


def send_video(address, video, desired_fps, gray):
    cap = cv2.VideoCapture(video)

    video_fps = cap.get(cv2.CAP_PROP_FPS)

    if desired_fps > video_fps:
        desired_fps = video_fps

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        transmission_start = time.time()
        processing_start = time.time()
        jpg_quality = 80

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                if video == 0:
                    print('Could not read next frame')
                else:
                    print('End of video file')
                break

            if gray:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), jpg_quality]
            result, encoded_img = cv2.imencode('.jpg', frame, encode_param)

            # Decrease quality until frame size is less than 65k
            while encoded_img.nbytes > MAX_SIZE:
                jpg_quality -= 5
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), jpg_quality]
                result, encoded_img = cv2.imencode('.jpg', frame, encode_param)

            if not result:
                print('Could no compress frame')
                break

            # video time
            vt = np.array([cap.get(cv2.CAP_PROP_POS_MSEC) / 1000], dtype=np.float64)
            data = encoded_img.tobytes() + vt.tobytes()

            sock.sendto(data, address)

            end = time.time()
            print('FPS: {0:0.2f}'.format(1 / (end - transmission_start)))
            transmission_start = time.time()

            # Sync
            processing_time = end - processing_start
            desired_time = 1 / desired_fps
            if desired_time > processing_time:
                time.sleep(desired_time - processing_time)
            processing_start = time.time()

    except KeyboardInterrupt:
        pass

    cap.release()
    sock.close()


def main(args):
    register_url = 'http://{}:8000/object-detection/register/'.format(GPU_SERVER)

    while not connected_to_internet():
        print('Waiting internet connection...')
        time.sleep(3)
        pass

    if args.rasp_simulator:
        cam_id = 1
    else:
        cam_id = get_id()

    tries = 1
    while tries <= 5:
        try:
            print('Registering. Attempt {}'.format(tries))
            register = requests.post(url=register_url, timeout=10, data={'cam_id': cam_id})

            port = int(register.text)
            address = (GPU_SERVER, port)
            send_video(address, args.video, args.fps, args.gray)
            break

        except requests.ConnectionError:
            print("Unable to connect with object detection service")
            tries += 1
        except ValueError:
            print(register.text)
            break


if __name__ == '__main__':
    arguments = arg_parse()
    main(arguments)
