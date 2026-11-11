#!/usr/bin/env python3
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node  # Node 클래스 추가

def generate_launch_description():
    realsense_launch = PathJoinSubstitution(
        [FindPackageShare('realsense2_camera'), 'launch', 'rs_launch.py']
    )

    def format_serial(sn):
        sn = str(sn).strip()
        return f"_{sn}" if not sn.startswith('_') else sn

    # [좌/우측 카메라용 공통 설정]
    common_args = {
        'enable_depth': 'false',
        'enable_gyro': 'false',
        'enable_accel': 'false',
        'unite_imu_method': '0',
        'enable_infra1': 'false',
        'enable_infra2': 'false',
        'enable_metadata': 'false',
        'publish_tf': 'false',
        'initial_reset': 'true',
        'rgb_camera.power_line_frequency': '2',
    }

    # 1. 정면 카메라 (요청하신 Node 방식으로 변경)
    # 시리얼 번호는 기존 번호('234322302402')를 그대로 사용합니다.
    front = Node(
        package="realsense2_camera",
        executable="realsense2_camera_node",
        namespace="camera",
        name="camera",
        output="screen",
        parameters=[{
            "serial_no": "336222300167",  # 정면 카메라 식별을 위해 필요
            "enable_color": True,
            "enable_depth": True,
            "enable_infra1": False,
            "enable_infra2": False,
            "enable_gyro": False,
            "enable_accel": False,
            "align_depth.enable": True,
            "enable_sync": True,
            "initial_reset": True,
            "rgb_camera.color_profile": "848x480x15",
            "depth_module.depth_profile": "848x480x15",
        }]
    )

    # 2. 왼쪽 카메라 (기존 방식 유지)
    left = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(realsense_launch),
        launch_arguments={
            'camera_name': 'camera_left', # 기존 코드의 이름 유지
            'camera_namespace': '',
            'serial_no': format_serial('233722072176'),
            'rgb_camera.color_profile': '424x240x6',
            'enable_color': 'true',
            **common_args
        }.items()
    )

    # 3. 오른쪽 카메라 (기존 방식 유지)
    right = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(realsense_launch),
        launch_arguments={
            'camera_name': 'camera_right', # 기존 코드의 이름 유지
            'camera_namespace': '',
            'serial_no': format_serial('405622076406'),
            'rgb_camera.color_profile': '424x240x6',
            'enable_color': 'true',
            **common_args
        }.items()
    )

    # 좀비 프로세스 정리
    kill_old = ExecuteProcess(
        cmd=['bash', '-c', 'pkill -9 -f realsense2_camera_node || true'],
        output='screen'
    )

    return LaunchDescription([
        kill_old,
        # 정면부터 순서대로 기동
        TimerAction(period=2.0, actions=[front]),
        TimerAction(period=7.0, actions=[left]),
        TimerAction(period=12.0, actions=[right]),
    ])
