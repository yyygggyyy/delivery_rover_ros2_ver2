import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro

def generate_launch_description():
    pkg_path = get_package_share_directory('delivery_rover_description')
    xacro_file = os.path.join(pkg_path, 'urdf', 'rover.urdf.xacro')
    ekf_config_file = os.path.join(pkg_path, 'config', 'ekf.yaml')
    
    robot_description_config = xacro.process_file(xacro_file)

    # 0. Static TF Bridge for Gazebo LiDAR scoped frame (with use_sim_time=True)
    static_tf_node = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='gazebo_lidar_tf_bridge',
        arguments=['0', '0', '0', '0', '0', '0', 'lidar_link', 'delivery_rover/base_footprint/gpu_lidar'],
        parameters=[{'use_sim_time': True}]
    )

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

    world_file = os.path.join(pkg_path, 'worlds', 'world_1.sdf')

    # 2. Gazebo World
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': f'-r {world_file}'}.items()
    )

    # 3. Spawn Entity
    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-topic', 'robot_description', '-name', 'delivery_rover', '-z', '0.2'],
        output='screen'
    )

    # 4. Parameter Bridge (Configures reliable QoS for /scan so SLAM receives it)
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
            'qos_overrides./scan.publisher.reliability': 'reliable',
            'qos_overrides./joint_states.publisher.reliability': 'best_effort'
        }],
        output='screen'
    )

    # 5. Extended Kalman Filter Node
    robot_localization_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[ekf_config_file, {'use_sim_time': True}]
    )

    # 6. RViz2 Node
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        parameters=[{'use_sim_time': True}]
    )

    return LaunchDescription([
        static_tf_node,
        robot_state_publisher_node,
        gazebo,
        spawn_entity,
        bridge,
        robot_localization_node,
        rviz_node
    ])