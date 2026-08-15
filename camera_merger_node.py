import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import message_filters
import cv2

class CameraMergerNode(Node):
    def __init__(self):
        super().__init__('camera_merger_node')

        # 파라미터 설정
        self.declare_parameter('left_topic', '/camera_left/color/image_raw')
        self.declare_parameter('front_topic', '/camera_front/color/image_raw')
        self.declare_parameter('right_topic', '/camera_right/color/image_raw')
        self.declare_parameter('output_topic', '/camera_merged/image_raw')
        self.declare_parameter('target_height', 240) # 합칠 이미지의 세로 높이 (240으로 고정 시 480인 front는 축소됨)
        self.declare_parameter('sync_slop', 0.1)

        left_topic = self.get_parameter('left_topic').value
        front_topic = self.get_parameter('front_topic').value
        right_topic = self.get_parameter('right_topic').value
        output_topic = self.get_parameter('output_topic').value
        self.target_height = self.get_parameter('target_height').value
        slop = self.get_parameter('sync_slop').value

        self.bridge = CvBridge()
        self.pub = self.create_publisher(Image, output_topic, 10)

        # 메시지 필터를 이용한 시간 동기화 구독
        sub_left = message_filters.Subscriber(self, Image, left_topic)
        sub_front = message_filters.Subscriber(self, Image, front_topic)
        sub_right = message_filters.Subscriber(self, Image, right_topic)

        self.sync = message_filters.ApproximateTimeSynchronizer(
            [sub_left, sub_front, sub_right],
            queue_size=10,
            slop=slop,
        )
        self.sync.registerCallback(self.callback)

        self.get_logger().info(f'병합 노드 실행 중... 목표 높이: {self.target_height}')

    def _resize_to_height(self, img, height):
        h, w = img.shape[:2]
        if h == height:
            return img
        # 비율 유지하며 높이에 맞춰 리사이즈 (480p -> 240p 시 가로도 848 -> 424가 됨)
        scale = height / float(h)
        return cv2.resize(img, (int(w * scale), height))

    def callback(self, left_msg, front_msg, right_msg):
        try:
            # ROS 이미지를 OpenCV 이미지로 변환
            left_img = self.bridge.imgmsg_to_cv2(left_msg, desired_encoding='bgr8')
            front_img = self.bridge.imgmsg_to_cv2(front_msg, desired_encoding='bgr8')
            right_img = self.bridge.imgmsg_to_cv2(right_msg, desired_encoding='bgr8')
            
            # 높이 통일 (front는 여기서 축소됨)
            h = self.target_height
            left_img = self._resize_to_height(left_img, h)
            front_img = self._resize_to_height(front_img, h)
            right_img = self._resize_to_height(right_img, h)

            # 가로로 이어 붙이기
            merged = cv2.hconcat([left_img, front_img, right_img])

            # 결과 발행
            out_msg = self.bridge.cv2_to_imgmsg(merged, encoding='bgr8')
            out_msg.header = front_msg.header
            self.pub.publish(out_msg)

        except Exception as e:
            self.get_logger().error(f'이미지 병합 에러: {e}')

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
