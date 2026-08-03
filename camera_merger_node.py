#!/usr/bin/env python3
"""
camera_merger_node.py

camera_left / camera_front / camera_right 3대의 RGB 이미지를 시간 동기화 후
가로로 이어붙여(hconcat) 하나의 토픽으로 재발행하는 노드.

yolo_xyz_publisher는 원래 구독하던 단일 카메라 토픽 대신
이 노드가 발행하는 output_topic(기본 /camera_merged/image_raw)을 구독하도록
수정해서 쓰면 됨.

실행 예:
  ros2 run <your_package> camera_merger_node
  또는
  python3 camera_merger_node.py --ros-args \
      -p left_topic:=/camera_left/color/image_raw \
      -p front_topic:=/camera_front/color/image_raw \
      -p right_topic:=/camera_right/color/image_raw \
      -p output_topic:=/camera_merged/image_raw

주의:
  - 실제 realsense 토픽 이름은 launch 시 camera_namespace 설정에 따라
    /camera/camera_left/color/image_raw 처럼 앞에 네임스페이스가 붙을 수 있음.
    `ros2 topic list`로 실제 이름 확인 후 파라미터로 맞춰줄 것.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import message_filters
import cv2


class CameraMergerNode(Node):
    def __init__(self):
        super().__init__('camera_merger_node')

        self.declare_parameter('left_topic', '/camera_left/color/image_raw')
        self.declare_parameter('front_topic', '/camera_front/color/image_raw')
        self.declare_parameter('right_topic', '/camera_right/color/image_raw')
        self.declare_parameter('output_topic', '/camera_merged/image_raw')
        self.declare_parameter('target_height', 240)
        self.declare_parameter('sync_slop', 0.05)

        left_topic = self.get_parameter('left_topic').value
        front_topic = self.get_parameter('front_topic').value
        right_topic = self.get_parameter('right_topic').value
        output_topic = self.get_parameter('output_topic').value
        self.target_height = self.get_parameter('target_height').value
        slop = self.get_parameter('sync_slop').value

        self.bridge = CvBridge()
        self.pub = self.create_publisher(Image, output_topic, 10)

        sub_left = message_filters.Subscriber(self, Image, left_topic)
        sub_front = message_filters.Subscriber(self, Image, front_topic)
        sub_right = message_filters.Subscriber(self, Image, right_topic)

        self.sync = message_filters.ApproximateTimeSynchronizer(
            [sub_left, sub_front, sub_right],
            queue_size=10,
            slop=slop,
        )
        self.sync.registerCallback(self.callback)

        self.get_logger().info(
            f'카메라 병합 노드 시작: {left_topic} + {front_topic} + {right_topic} -> {output_topic}'
        )

    def _resize_to_height(self, img, height):
        h, w = img.shape[:2]
        if h == height:
            return img
        scale = height / float(h)
        return cv2.resize(img, (int(w * scale), height))

    def callback(self, left_msg, front_msg, right_msg):
        try:
            left_img = self.bridge.imgmsg_to_cv2(left_msg, desired_encoding='bgr8')
            front_img = self.bridge.imgmsg_to_cv2(front_msg, desired_encoding='bgr8')
            right_img = self.bridge.imgmsg_to_cv2(right_msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f'이미지 변환 실패: {e}')
            return

        h = self.target_height
        left_img = self._resize_to_height(left_img, h)
        front_img = self._resize_to_height(front_img, h)
        right_img = self._resize_to_height(right_img, h)

        merged = cv2.hconcat([left_img, front_img, right_img])

        out_msg = self.bridge.cv2_to_imgmsg(merged, encoding='bgr8')
        out_msg.header = front_msg.header  # 정면 카메라 타임스탬프 기준
        self.pub.publish(out_msg)


def main(args=None):
    rclpy.init(args=args)
    node = CameraMergerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
