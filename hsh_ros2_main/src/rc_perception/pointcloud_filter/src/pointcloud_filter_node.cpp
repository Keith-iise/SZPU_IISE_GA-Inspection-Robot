#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/point_cloud2.hpp>
#include <sensor_msgs/point_cloud2_iterator.hpp>

class PointCloudFilter : public rclcpp::Node {
public:
    PointCloudFilter() : Node("pointcloud_filter_node") {
        // 获取参数
        this->declare_parameter("min_height", -1.0);
        this->declare_parameter("max_height", 1.0);
        this->declare_parameter("cloud_in_topic", std::string("/input_cloud"));
        this->declare_parameter("cloud_out_topic", std::string("/filtered_cloud"));

        this->get_parameter("min_height", min_height_);
        this->get_parameter("max_height", max_height_);
        this->get_parameter("cloud_in_topic", cloud_in_);
        this->get_parameter("cloud_out_topic", cloud_out_);

        RCLCPP_INFO(this->get_logger(), "Filtering between z = %.2f and z = %.2f", min_height_, max_height_);

        // 订阅原始点云话题
        sub_ = this->create_subscription<sensor_msgs::msg::PointCloud2>(
            cloud_in_,
            10,
            [this](const sensor_msgs::msg::PointCloud2::SharedPtr msg) {
                this->cloudCallback(msg);
            });

        // 发布过滤后的点云
        pub_ = this->create_publisher<sensor_msgs::msg::PointCloud2>(cloud_out_, 10);
    }

private:
    void cloudCallback(const sensor_msgs::msg::PointCloud2::SharedPtr input_cloud) {
        // 创建输出点云消息
        sensor_msgs::msg::PointCloud2 output_cloud;
        output_cloud.header = input_cloud->header;
        output_cloud.height = 1;
        output_cloud.width = 0;
        output_cloud.fields = input_cloud->fields;
        output_cloud.is_bigendian = input_cloud->is_bigendian;
        output_cloud.point_step = input_cloud->point_step;
        output_cloud.data.clear();

        // 查找 x, y, z 的偏移量
        int x_offset = -1, y_offset = -1, z_offset = -1;
        for (const auto& field : input_cloud->fields) {
            if (field.name == "x") x_offset = field.offset;
            else if (field.name == "y") y_offset = field.offset;
            else if (field.name == "z") z_offset = field.offset;
        }

        if (x_offset == -1 || y_offset == -1 || z_offset == -1) {
            RCLCPP_WARN(this->get_logger(), "Missing x/y/z fields in PointCloud2");
            return;
        }

        // 遍历所有点
        const uint8_t* data = &input_cloud->data[0];
        int point_step = input_cloud->point_step;

        for (size_t i = 0; i < input_cloud->height * input_cloud->width; ++i) {
            float z = *(float*)(data + z_offset);
            if (z >= min_height_ && z <= max_height_) {
                // 拷贝整个点的数据
                output_cloud.data.insert(output_cloud.data.end(), data, data + point_step);
                output_cloud.width++;
            }
            data += point_step;
        }

        output_cloud.row_step = output_cloud.point_step * output_cloud.width;
        output_cloud.is_dense = true;

        // 发布过滤后的点云
        pub_->publish(output_cloud);
    }

    double min_height_;
    double max_height_;
    std::string cloud_in_;
    std::string cloud_out_;
    rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_;
    rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub_;
};

int main(int argc, char* argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<PointCloudFilter>());
    rclcpp::shutdown();
    return 0;
}








// #include <rclcpp/rclcpp.hpp>
// #include <string>
// #include <sensor_msgs/msg/point_cloud2.hpp>
// #include <pcl_conversions/pcl_conversions.h>
// #include <pcl/point_cloud.h>
// #include <pcl/point_types.h>

// class PointCloudFilter : public rclcpp::Node {
// public:
//     PointCloudFilter() : Node("pointcloud_filter_node") {
//         // 获取参数
//         this->declare_parameter("min_height", -1.0);
//         this->declare_parameter("max_height", 1.0);
//         this->get_parameter("min_height", min_height_);
//         this->get_parameter("max_height", max_height_);
//         this->get_parameter("cloud_in_topic", cloud_in);
//         this->get_parameter("cloud_out_topic", cloud_out);




//         RCLCPP_INFO(this->get_logger(), "Filtering between z = %.2f and z = %.2f", min_height_, max_height_);

//         // 订阅原始点云话题
//         sub_ = this->create_subscription<sensor_msgs::msg::PointCloud2>(
//             cloud_in, 10,
//             [this](const sensor_msgs::msg::PointCloud2::SharedPtr msg) {
//                 this->cloudCallback(msg);
//             });

//         // 发布过滤后的点云
//         pub_ = this->create_publisher<sensor_msgs::msg::PointCloud2>(cloud_out, 10);
//     }

// private:
//     void cloudCallback(const sensor_msgs::msg::PointCloud2::SharedPtr input_cloud) {
//         pcl::PointCloud<pcl::PointXYZ>::Ptr cloud(new pcl::PointCloud<pcl::PointXYZ>);
//         pcl::PointCloud<pcl::PointXYZ>::Ptr filtered_cloud(new pcl::PointCloud<pcl::PointXYZ>);

//         // 转换为 PCL 点云
//         pcl::fromROSMsg(*input_cloud, *cloud);

//         // 过滤 Z 值范围
//         for (const auto& point : cloud->points) {
//             if (point.z >= min_height_ && point.z <= max_height_) {
//                 filtered_cloud->points.push_back(point);
//             }
//         }

//         filtered_cloud->header = cloud->header;
//         filtered_cloud->height = 1;
//         filtered_cloud->width = static_cast<uint32_t>(filtered_cloud->points.size());

//         // 转换回 ROS2 消息并发布
//         sensor_msgs::msg::PointCloud2 output;
//         pcl::toROSMsg(*filtered_cloud, output);
//         output.header.stamp = this->now();
//         output.header.frame_id = "laser";  // 根据实际情况修改 frame_id
//         pub_->publish(output);
//     }

//     double min_height_;
//     double max_height_;
//     string cloud_in;
//     string cloud_out;
//     rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_;
//     rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub_;
// };

// int main(int argc, char* argv[]) {
//     rclcpp::init(argc, argv);
//     rclcpp::spin(std::make_shared<PointCloudFilter>());
//     rclcpp::shutdown();
//     return 0;
// }