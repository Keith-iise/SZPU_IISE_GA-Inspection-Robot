cmake_minimum_required(VERSION 3.8)
project(pointcloud_filter)

# 查找 ROS2 核心依赖
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)

# 添加可执行文件
add_executable(pointcloud_filter_node src/pointcloud_filter_node.cpp)

include_directories(
  ${PROJECT_SOURCE_DIR}/include
  
  ${rclcpp_INCLUDE_DIRS}
  ${sensor_msgs_INCLUDE_DIRS}
  /opt/ros/humble/include  # 手动添加 ROS 2 头文件根目录（可选）
  
)

# 链接 ROS2 库
target_link_libraries(pointcloud_filter_node
  ${rclcpp_LIBRARIES}
  ${sensor_msgs_LIBRARIES}
)

# 可选：添加 include 路径支持
target_include_directories(pointcloud_filter_node PRIVATE
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

# 安装目标
install(TARGETS pointcloud_filter_node
  DESTINATION lib/${PROJECT_NAME})



install(DIRECTORY launch config
  DESTINATION share/${PROJECT_NAME}
)


ament_package()