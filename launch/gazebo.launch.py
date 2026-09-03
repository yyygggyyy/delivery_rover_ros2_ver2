import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro

def generate_launch_description():
    pkg_path = get_package_share_directory('delivery_rover_description')
    xacro_file = os.path.join(pkg_path, 'urdf', 'rover.urdf.xacro')
    ekf_config_file = os.path.join(pkg_path, 'config', 'ekf.yaml')
    slam_params_file = os.path.join(pkg_path, 'config', 'mapper_params_online_async.yaml')
    
    robot_description_config = xacro.process_file(xacro_file)

    # 1. Robot State Publisher
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description_config.toxml(),
            'use_sim_time': True
        }]
    )

    # 2. Gazebo World
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': '-r empty.sdf'}.items()
    )

    # 3. Spawn Entity
    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-topic', 'robot_description', '-name', 'delivery_rover', '-z', '0.2'],
        output='screen'
    )

    # 4. Parameter Bridge
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/scan@sensor_msgs/msg/LaserScan[ignition.msgs.LaserScan',
            '/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry[ignition.msgs.Odometry',
            '/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock',
            '/joint_states@sensor_msgs/msg/JointState[ignition.msgs.Model',
            '/imu/data@sensor_msgs/msg/Imu[ignition.msgs.IMU'
        ],
        parameters=[{
            'use_sim_time': True,
            'qos_overrides./scan.subscriber.reliability': 'best_effort',
            'qos_overrides./joint_states.subscriber.reliability': 'best_effort'
        }],
        output='screen'
    )

    # 5. EKF Node
    robot_localization_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[ekf_config_file, {'use_sim_time': True}]
    )

    # 6. RViz2
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        parameters=[{'use_sim_time': True}]
    )

    # 7. SLAM Toolbox
    slam_toolbox_launch = TimerAction(
        period=5.0,
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(get_package_share_directory('slam_toolbox'), 'launch', 'online_async_launch.py')
                ),
                launch_arguments={
                    'use_sim_time': 'true',
                    'slam_params_file': slam_params_file
                }.items()
            )
        ]
    )

    return LaunchDescription([
        robot_state_publisher_node,
        gazebo,
        spawn_entity,
        bridge,
        robot_localization_node,
        rviz_node,
        slam_toolbox_launch
    ])