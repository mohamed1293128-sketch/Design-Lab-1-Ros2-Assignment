from setuptools import find_packages, setup

package_name = 'my_packages'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='m',
    maintainer_email='mohamed1293128@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'reset = my_packages.reset_server:main',
            'square_draw = my_packages.square_server:main',
            'pose_control = my_packages.pose_control_server:main',
            'speed_control = my_packages.speed_control_test:main',
            'pose_set = my_packages.pose_set:main',
            'square_client = my_packages.square_client:main',
        ],
    },
)
