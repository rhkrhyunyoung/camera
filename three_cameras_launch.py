#!/usr/bin/env python3
"""
three_cameras_launch.py
- camera_front: 848x480x15 + IMU(Gyro/Accel) ON + Sync ON (터미널 명령어와 동일 설정)
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

    # 공통 기본 설정 (모든 카메라에 적용)
    common_args_base = {
        'camera_namespace': '',
    }

    def cam(name, serial, res='424x240x6', imu=False, sync=True):
        """
        카메라 설정을 생성하는 함수
        imu=True일 경우 gyro, accel, unite_imu 설정 활성화
        sync=True일 경우 enable_sync 활성화
        """
        args = {
            'camera_name': name,
            'serial_no': serial,
            'rgb_camera.color_profile': res,
            'enable_color': 'true',
            'enable_depth': 'false',           # 뎁스 비활성화
            'align_depth.enable': 'false',    # 뎁스 정렬 비활성화
            'enable_sync': 'true' if sync else 'false',
            'enable_gyro': 'true' if imu else 'false',
            'enable_accel': 'true' if imu else 'false',
            'unite_imu_method': '2' if imu else '0',  # 2: Linear Interpolation
        }
        args.update(common_args_base)
        
        return IncludeLaunchDescription(
            PythonLaunchDescriptionSource(realsense_launch),
            launch_arguments=args.items(),
        )

    # 이전 노드 프로세스 정리 (안정적인 재실행을 위함)
    kill_old = ExecuteProcess(
        cmd=['bash', '-c', 'killall -9 realsense2_camera_node 2>/dev/null || true'],
        output='screen',
    )

    # 카메라 정의
    # 1. 왼쪽 (기본 해상도, 동기화 사용)
    left = cam('camera_left', '_233722072176')
    
    # 2. 오른쪽 (기본 해상도, 동기화 사용)
    right = cam('camera_right', '_405622076406')
    
    # 3. 정면 (요청하신 CLI 명령어와 100% 동일한 설정)
    # 848x480x15, IMU ON, Sync ON, Depth OFF, Align Depth OFF
    front = cam('camera_front', '_234322302402', res='848x480x15', imu=True, sync=True)

    return LaunchDescription([
        kill_old,
        # 카메라 간 충돌 방지를 위해 순차적 실행 (간격 유지)
        TimerAction(period=1.0, actions=[left]),
        TimerAction(period=6.0, actions=[right]),
        TimerAction(period=11.0, actions=[front]),
    ])
