import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32
from geometry_msgs.msg import TwistStamped
from geometry_msgs.msg import Twist
import math

class FusionNode(Node):

    def __init__(self):
        super().__init__('fusion_node')

        # variables
        self.x = 0.0
        self.y = 0.0
        self.left_ticks = 0
        self.right_ticks = 0
        self.yaw = 0.0                #rad
        self.sensor_offset = 0.075 # distance from optical sensor to the rear axle [m] (because the optical is not centered)
        self.delta_x = 0.0
        self.delta_y = 0.0

        self.offset_left = 0.0          #offset for left ticks when the wheel is moving but the car is stuck and the ticks still cummulate in encoder_node
        self.offset_right = 0.0         #offset for right ticks when the wheel is moving but the car is stuck and the ticks still cummulate in encoder_node
 
        #vehicle information
        self.wheel_diameter = 0.071
        self.wheel_track = 0.142
        self.ticks_per_rev = 20

        self.dist_per_tick = (math.pi * self.wheel_diameter/ self.ticks_per_rev)

        self.rad_per_tick_diff = (self.dist_per_tick/ self.wheel_track)
        
        self.meters_per_count = 1.0 / 29750.0 # measure and input the correct number!!!

        #publish time
        self.timer = self.create_timer(0.1, self.compute)

        

        # subscribers
        self.create_subscription(Int32, 'ticks_left', self.left_callback, 10)
        self.create_subscription(Int32, 'ticks_right', self.right_callback, 10)
        self.create_subscription(
        TwistStamped,
        'optical_flow',
        self.flow_callback,
        10
        )
        # publisher
        self.publisher_ = self.create_publisher(Twist, 'processed_data', 10)

    def flow_callback(self, msg):
        delta_x_real = msg.twist.linear.x * self.meters_per_count
        delta_y_real = msg.twist.linear.y * self.meters_per_count

        self.delta_x = msg.twist.linear.x
        self.delta_y = msg.twist.linear.y

        self.x += (delta_x_real * math.sin(self.yaw) + delta_y_real * math.cos(self.yaw))

        self.y += ( - delta_x_real * math.cos(self.yaw) + delta_y_real * math.sin(self.yaw))

    def left_callback(self, msg):
        if (abs(self.delta_x) > 3 and abs(self.delta_y) > 3): #condition for cummulative ticks
            self.left_ticks = msg.data - self.offset_left
        else:
            self.offset_left = msg.data - self.left_ticks
        self.yaw = self.rad_per_tick_diff * (self.right_ticks - self.left_ticks)

    def right_callback(self, msg):
        if (abs(self.delta_x) > 3 and abs(self.delta_y) > 3): #condition for cummulative ticks
            self.right_ticks = msg.data - self.offset_right
        else:
            self.offset_right = msg.data - self.right_ticks
        self.yaw = self.rad_per_tick_diff * (self.right_ticks - self.left_ticks)

    def compute(self):
        msg = Twist()

        msg.linear.x = (self.x - self.sensor_offset * math.cos(self.yaw))

        msg.linear.y = (self.y - self.sensor_offset * math.sin(self.yaw))

        msg.angular.z = self.yaw

        self.publisher_.publish(msg)
        self.get_logger().info(f"X={self.x:.3f}, Y={self.y:.3f}, "f"L={self.left_ticks}, R={self.right_ticks}"f"Yaw={self.yaw:.3f}" f"Yawdeg={self.yaw*180/math.pi:.3f}")


def main(args=None):
    rclpy.init(args=args)
    node = FusionNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
