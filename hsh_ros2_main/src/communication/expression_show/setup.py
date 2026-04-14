from setuptools import find_packages, setup
import os ,glob
package_name = 'expression_show'
show_node = 'show_node'


resource_files = []
for file in glob.glob('resource/**/*', recursive=True):
    if os.path.isfile(file):  # 只处理文件（跳过目录本身）
        # 计算文件的相对路径（相对于 resource 目录）
        relative_path = os.path.relpath(file, 'resource')
        # 目标目录：share/package_name/resource/ + 相对路径的父目录
        target_dir = os.path.join('share', package_name, 'resource', os.path.dirname(relative_path))
        resource_files.append((target_dir, [file]))



setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name), ['package.xml']),
        *resource_files,

        (os.path.join('launch', package_name), ['launch/show.launch.py']),


    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='iise',
    maintainer_email='2257761605@qq.com',
    description='TODO: Package description',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            f'{show_node}={package_name}.{show_node}:main',
        ],
    },
)
