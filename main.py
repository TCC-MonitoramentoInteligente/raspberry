import argparse
import socket

import cv2
import time
import sys

import numpy as np
import requests
import paho.mqtt.client as mqtt


BROKER_IP = 'localhost'
MAX_SIZE = 65536 - 8  # less 8 bytes of video time


def arg_parse():
    parser = argparse.ArgumentParser(description='Server')
    parser.add_argument("--video", help="Path to video file", default=0)
    parser.add_argument("--fps", help="Set video FPS", type=int, default=14)
    parser.add_argument("--gray", help="Convert video into gray scale", action="store_true")
    parser.add_argument("--ip", help="Server IP address", default="localhost")
    parser.add_argument("--port", help="UDP port number", type=int, default=60444)
    parser.add_argument("--rasp_simulator", help="This is not a Raspberry Pi", action="store_true")
    parser.add_argument("--debug_ip", help="IP where the server will retransmit the video", default=None)
    parser.add_argument("--debug_port", help="Port where the server will retransmit the video", default=None)

    return parser.parse_args()


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


def init_broker():
    mqtt_client = mqtt.Client()
    try:
        mqtt_client.connect(BROKER_IP)
    except ConnectionRefusedError:
        time.sleep(5)
        return False
    mqtt_client.loop_start()
    return mqtt_client


def main(args):
    register_url = 'http://{}:8000/object-detection/register/'.format(args.ip)
    cam_id = None

    while not connected_to_internet():
        time.sleep(5)
        pass

    mqtt_client = None
    while not mqtt_client:
        mqtt_client = init_broker()

    if args.rasp_simulator:
        cam_id = -1
    else:
        # TODO: Get rasp id, zerotier address.
        cam_id = 1
        # pass

    payload = {'cam_id': cam_id, 'port': args.port}
    if args.debug_ip:
        payload['debug_ip'] = args.debug_ip
    if args.debug_port:
        payload['debug_port'] = args.debug_port

    try:
        register = requests.post(url=register_url, data=payload)
        mqtt_client.publish(topic="raspberry/register", payload=cam_id)
    except requests.ConnectionError:
        print("Unable to connect with object detection service")
        mqtt_client.publish(topic="raspberry/fail_register", payload=cam_id)
        time.sleep(2)
        sys.exit(0)

    port = int(register.text)

    address = (args.ip, port)

    send_video(address, args.video, args.fps, args.gray)


if __name__ == '__main__':
    arguments = arg_parse()
    main(arguments)
