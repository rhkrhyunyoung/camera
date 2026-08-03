#!/usr/bin/env python3
"""
three_cameras_launch.py

start_cameras.sh(bash + sleep)를 대체하는 ROS2 launch 파일.
- ros2 launch가 프로세스 트리를 직접 관리하므로 Ctrl+C 한 번으로 3개 카메라가 깔끔하게 종료됨
  (bash & 방식은 종종 realsense2_camera_node가 좀비로 남는 문제가 있음)
- TimerAction으로 기동 시점을 분산해 USB 대역폭/전원 순간 부하를 줄임

사용법:
  1. 이 파일을 아무 패키지의 launch/ 폴더에 넣거나, 그냥
     ros2 launch <이 파일 경로> 로 직접 실행 가능
  2. serial_no 값은 본인 카메라 실제 시리얼로 이미 맞춰져 있음 (기존 start_cameras.sh 값 그대로)
"""

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import PathJoinSubstitution


def generate_launch_description():
    realsense_launch = PathJoinSubstitution(
        [FindPackageShare('realsense2_camera'), 'launch', 'rs_launch.py']
    )

    common_args = {
        'rgb_camera.color_profile': '424x240x6',
        'enable_depth': 'false',
        'enable_gyro': 'false',
        'enable_accel': 'false',
        # realsense2_camera의 camera_namespace 기본값은 'camera'라서
        # 이걸 안 비우면 실제 토픽이 /camera/camera_left/color/image_raw 처럼
        # 뜬다 (spring_node.cpp가 구독하는 /camera_left/color/image_raw와 다름 -> 콜백이 영원히 안 불림)
        'camera_namespace': '',
    }

    def cam(name, serial):
        args = {'camera_name': name, 'serial_no': serial}
        args.update(common_args)
        return IncludeLaunchDescription(
            PythonLaunchDescriptionSource(realsense_launch),
            launch_arguments=args.items(),
        )

    # 기존에 떠 있던 카메라 노드 정리 (없어도 에러 무시)
    kill_old = ExecuteProcess(
        cmd=['bash', '-c', 'killall -9 realsense2_camera_node 2>/dev/null || true'],
        output='screen',
    )

    left = cam('camera_left', '_233722072176')
    front = cam('camera_right', '_405622076406')
    right = cam('camera_front', '_234322302402')

    return LaunchDescription([
        kill_old,
        TimerAction(period=1.0, actions=[left]),
        TimerAction(period=6.0, actions=[front]),
        TimerAction(period=11.0, actions=[right]),
    ])
