import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'delivery_rover_description'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Include all launch files
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        # Include all URDF / Xacro files
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*')),
        # Include all RViz configs
        (os.path.join('share', package_name, 'rviz'), glob('rviz/*')),
        # Include all YAML configs
        (os.path.join('share', package_name, 'config'), glob('config/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='serdar',
    maintainer_email='serdar@todo.todo',
    description='Delivery Rover Description Package',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
        ],
    },
)