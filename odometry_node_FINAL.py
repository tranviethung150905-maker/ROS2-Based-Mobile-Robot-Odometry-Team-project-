import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

import matplotlib.pyplot as plt
import math


class OdometryNode(Node):

    def __init__(self):
        super().__init__('odometry_node')

        # Current robot pose
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.yaw_deg = 0.0

        # Subscribe to Fusion Node output
        self.create_subscription(
            Twist,
            'processed_data',
            self.odom_callback,
            10
        )

        # Update graph every 100 ms
        self.timer = self.create_timer(
            0.1,
            self.update_plot
        )

        # Create graph window
        plt.ion()
        self.fig, self.ax = plt.subplots()

        self.get_logger().info("Odometry Node Started")

    def odom_callback(self, msg):

        self.x = msg.linear.x
        self.y = msg.linear.y
        self.yaw = msg.angular.z
        self.yaw_deg = math.degrees(self.yaw) % 360             #normalize the yaw angle to [0:360]

    def update_plot(self):

        self.ax.clear()

        # Draw current robot position
        self.ax.plot(
            self.x,
            self.y,
            'o',
            markersize=5
        )

        # Draw heading vector
        arrow_length = 0.6

        # Robot convention:
        # WORLD Forward = +X
        # WORLD LEFT   = +Y
        dx = arrow_length * math.cos(self.yaw)
        dy = arrow_length * math.sin(self.yaw)

        self.ax.arrow(
            self.x,
            self.y,
            dx,
            dy,
            head_width=0.15,
            length_includes_head=True
        )

        self.ax.set_title("Robot Odometry")
        self.ax.set_xlabel("X Position (m)")
        self.ax.set_ylabel("Y Position (m)")
        self.ax.grid(True)

        # Keep robot centered in view
        self.ax.set_xlim(-2, 2)
        self.ax.set_ylim(-2, 2)

        self.ax.set_aspect('equal')

        plt.pause(0.02)

        self.get_logger().info(
            f"X={self.x:.3f} m, "
            f"Y={self.y:.3f} m, "
            f"Yaw={self.yaw_deg:.1f} deg"
        )

    def destroy_node(self):
        plt.close('all')
        super().destroy_node()


def main(args=None):

    rclpy.init(args=args)

    node = OdometryNode()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()