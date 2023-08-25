import os

from ament_index_python.packages import get_package_share_directory


from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import RegisterEventHandler
from launch.event_handlers import OnProcessExit

from launch_ros.actions import Node
from launch import LaunchContext



def generate_launch_description():

    package_name='lapy_bot'

    use_ros2_control = LaunchConfiguration('use_ros2_control')

    rsp = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory(package_name),'launch','rsp.launch.py'
                )]), launch_arguments={'use_sim_time': 'true', 'use_ros2_control': use_ros2_control}.items()
    )

    gazebo_params_file = os.path.join(get_package_share_directory(package_name),'config','gazebo_params.yaml')
    gazebo_world_file = os.path.join(get_package_share_directory(package_name),'worlds','obstacles.world')

    # Include the Gazebo launch file, provided by the gazebo_ros package
    gazebo = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py')]),
                    launch_arguments={'extra_gazebo_args': '--ros-args --params-file ' + gazebo_params_file,
                                      'world': gazebo_world_file}.items()
             )

    # Run the spawner node from the gazebo_ros package. The entity name doesn't really matter if you only have a single robot.
    spawn_entity = Node(package='gazebo_ros', executable='spawn_entity.py',
                        arguments=['-topic', 'robot_description',
                                   '-entity', 'lapyBot'],
                        output='screen')


    if use_ros2_control:
        diff_drive_spawner = Node(
            package="controller_manager",
            executable="spawner",
            arguments=["diff_drive_controller", "-c", "/controller_manager"],
        )

        delayed_diff_drive_spawner = RegisterEventHandler(
            event_handler=OnProcessExit(
                    target_action=spawn_entity,
                    on_exit=[diff_drive_spawner],
            )
        )

        joint_broad_spawner = Node(
            package="controller_manager",
            executable="spawner",
            arguments=["joint_state_broadcaster", "-c", "/controller_manager"],
        )

        delayed_joint_broad_spawner = RegisterEventHandler(
            event_handler=OnProcessExit(
                    target_action=spawn_entity,
                    on_exit=[joint_broad_spawner],
            )
        )

    
    if use_ros2_control:
        return LaunchDescription([
            DeclareLaunchArgument(
                'use_ros2_control',
                default_value='true',
                description='Use ros2_control if true'),
            rsp,
            gazebo,
            spawn_entity,
            delayed_diff_drive_spawner,
            delayed_joint_broad_spawner
        ])
    else: 
        return LaunchDescription([
            DeclareLaunchArgument(
                'use_ros2_control',
                default_value='false',
                description='Use ros2_control if true'),
            rsp,
            gazebo,
            spawn_entity,
        ])
