import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TwistStamped
from pmw3901 import PMW3901, PAA5100

class OpticalFlowNode(Node):
    def __init__(self):
        super().__init__('optical_flow_node')

        # --- Parameters ---
        # Allow configuration via ROS params
        self.declare_parameter('spi_port', 0)
        self.declare_parameter('spi_cs', 0)
        self.declare_parameter('pub_rate', 10.0) # Hz
        self.declare_parameter('frame_id', 'optical_flow_link')
        # Use 'paa5100je' if using the Pimoroni breakout for that specific chip
        self.declare_parameter('sensor_type', 'pmw3901')

        spi_port = self.get_parameter('spi_port').value
        spi_cs = self.get_parameter('spi_cs').value
        pub_rate = self.get_parameter('pub_rate').value
        self.frame_id = self.get_parameter('frame_id').value
        sensor_type = self.get_parameter('sensor_type').value



        # --- Publisher ---
        # Publish x and y inside optical_flow namespace
        self.publisher_ = self.create_publisher(
        TwistStamped,
        'optical_flow',
        10
        )

        # --- Sensor Initialization ---
        self.get_logger().info(f"Initializing {sensor_type} on SPI port {spi_port}, CS {spi_cs}...")
        try:
            if sensor_type == 'paa5100je':
                self.sensor = PAA5100(spi_port=spi_port, spi_cs=spi_cs)
            else:
                self.sensor = PMW3901(spi_port=spi_port, spi_cs=spi_cs)         

            # The library requires setting the rotation depending on how it's mounted
            self.sensor.set_rotation(0)
            self.get_logger().info("Sensor initialized successfully.")
        except Exception as e:
            self.get_logger().error(f"Failed to initialize sensor: {e}")
            raise e

        # --- Timer ---
        timer_period = 1.0 / pub_rate
        self.timer = self.create_timer(timer_period, self.timer_callback)

    def timer_callback(self):
        try:
            # Read relative motion delta since last read
            # Note: get_motion() returns raw optical flow counts (pixels)
            delta_x, delta_y = self.sensor.get_motion()
        except RuntimeError:
            # The library throws a RuntimeError if no motion data is ready yet
            return

        # --- Publish Data ---
        msg = TwistStamped()

        # Populate Header
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.frame_id

        # Populate linear velocity (raw counts converted/scaled if needed)
        # Note: True m/s requires scaling by altitude/distance to surface
        msg.twist.linear.x = float(delta_x)
        msg.twist.linear.y = float(delta_y)
        msg.twist.linear.z = 0.0

        # Rotational velocities are zero for this sensor
        msg.twist.angular.x = 0.0
        msg.twist.angular.y = 0.0
        msg.twist.angular.z = 0.0

        self.get_logger().info(f"delta_X:{delta_x}, delta_Y:{delta_y}")

        self.publisher_.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = OpticalFlowNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down optical flow node.")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
