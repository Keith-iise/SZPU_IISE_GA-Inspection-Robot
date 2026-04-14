from setuptools import find_packages, setup
import os
package_name = 'model_communication'
communication_node = 'communication_node'
setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name), ['package.xml']),

            # 安装包的默认资源（通常包含包名的空文件，ROS 2 规范）
    (os.path.join('share', package_name, 'resource'), [
        os.path.join('resource', package_name)
    ]),
    # 安装 vosk 模型目录（递归包含所有子文件和子目录）
    (os.path.join('share', package_name, 'resource', 'vosk-model-small-cn-0.22'), 
     [os.path.join('resource', 'vosk-model-small-cn-0.22', f) 
      for f in os.listdir('resource/vosk-model-small-cn-0.22') 
      if os.path.isfile(os.path.join('resource/vosk-model-small-cn-0.22', f))]
    ),
    # 安装模型的子目录（如 am、conf、graph 等）
    (os.path.join('share', package_name, 'resource', 'vosk-model-small-cn-0.22', 'am'), 
     [os.path.join('resource', 'vosk-model-small-cn-0.22', 'am', f) 
      for f in os.listdir('resource/vosk-model-small-cn-0.22/am') 
      if os.path.isfile(os.path.join('resource/vosk-model-small-cn-0.22/am', f))]
    ),
    (os.path.join('share', package_name, 'resource', 'vosk-model-small-cn-0.22', 'conf'), 
     [os.path.join('resource', 'vosk-model-small-cn-0.22', 'conf', f) 
      for f in os.listdir('resource/vosk-model-small-cn-0.22/conf') 
      if os.path.isfile(os.path.join('resource/vosk-model-small-cn-0.22/conf', f))]
    ),
    (os.path.join('share', package_name, 'resource', 'vosk-model-small-cn-0.22', 'graph'), 
     [os.path.join('resource', 'vosk-model-small-cn-0.22', 'graph', f) 
      for f in os.listdir('resource/vosk-model-small-cn-0.22/graph') 
      if os.path.isfile(os.path.join('resource/vosk-model-small-cn-0.22/graph', f))]
    ),
    (os.path.join('share', package_name, 'resource', 'vosk-model-small-cn-0.22', 'graph', 'phones'), 
     [os.path.join('resource', 'vosk-model-small-cn-0.22', 'graph', 'phones', f) 
      for f in os.listdir('resource/vosk-model-small-cn-0.22/graph/phones') 
      if os.path.isfile(os.path.join('resource/vosk-model-small-cn-0.22/graph/phones', f))]
    ),
    (os.path.join('share', package_name, 'resource', 'vosk-model-small-cn-0.22', 'ivector'), 
     [os.path.join('resource', 'vosk-model-small-cn-0.22', 'ivector', f) 
      for f in os.listdir('resource/vosk-model-small-cn-0.22/ivector') 
      if os.path.isfile(os.path.join('resource/vosk-model-small-cn-0.22/ivector', f))]
    ),





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
            f'{communication_node}={package_name}.{communication_node}:main',
        ],
    },
)
