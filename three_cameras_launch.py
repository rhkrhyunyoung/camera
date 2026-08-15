#!/usr/bin/env python3
"""
three_cameras_launch.py
- camera_front: 848x480x15 + IMU(Gyro/Accel) ON
- camera_left/right: 424x240x6
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

    # 공통 설정
    common_args = {
        'enable_depth': 'false',
        'camera_namespace': '',
    }

    def cam(name, serial, res='424x240x6', imu=False):
        args = {
            'camera_name': name,
            'serial_no': serial,
            'rgb_camera.color_profile': res,
            'enable_gyro': 'true' if imu else 'false',
            'enable_accel': 'true' if imu else 'false',
            'unite_imu_method': '2' if imu else '0',  # 2: Linear Interpolation (IMU 사용 시 권장)
        }
        args.update(common_args)
        return IncludeLaunchDescription(
            PythonLaunchDescriptionSource(realsense_launch),
            launch_arguments=args.items(),
        )

    # 이전 프로세스 정리
    kill_old = ExecuteProcess(
        cmd=['bash', '-c', 'killall -9 realsense2_camera_node 2>/dev/null || true'],
        output='screen',
    )

    # 카메라 정의
    # 1. 왼쪽 (기본 해상도)
    left = cam('camera_left', '_233722072176')
    
    # 2. 오른쪽 (기존 코드에서 시리얼 4056...은 오른쪽이었으므로 명칭 유지)
    right = cam('camera_right', '_405622076406')
    
    # 3. 정면 (라인트레이싱용: 고해상도 + IMU 활성화)
    front = cam('camera_front', '_234322302402', res='848x480x15', imu=True)

    return LaunchDescription([
        kill_old,
        TimerAction(period=1.0, actions=[left]),
        TimerAction(period=6.0, actions=[right]),
        TimerAction(period=11.0, actions=[front]),
    ])
