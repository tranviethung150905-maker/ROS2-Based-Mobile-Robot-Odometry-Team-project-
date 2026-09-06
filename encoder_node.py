import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32
from geometry_msgs.msg import Twist
from gpiozero import DigitalInputDevice

class EncoderNode(Node):

    def __init__(self):
        super().__init__('encoder_node')

        #Publishers
        self.pub_left = self.create_publisher(Int32, 'ticks_left', 10)
        self.pub_right = self.create_publisher(Int32, 'ticks_right', 10)

        #Subscriber (to get direction from control node)
        self.subscription = self.create_subscription(
            Twist,
            'cmd_vel',
            self.getdirection,              #function that get call when a topic is received
            10)

        self.sensor_left = DigitalInputDevice(17, pull_up=None, active_state=True)      #pull_up=None: floating, pull_up=true: pull up, pull_down: pull down
        self.sensor_right = DigitalInputDevice(23, pull_up=None, active_state=True)     #active_state=True: active when high, inactive when low (rising edge trigger)
                                                                                        #beam get through => voltage low ; block => voltage high

        self.left_ticks = 0
        self.right_ticks = 0

        #Variable to receive the direction from the control node
        self.dleft = 0
        self.dright = 0

        self.sensor_left.when_activated = self.count_left
        self.sensor_right.when_activated = self.count_right

        self.timer = self.create_timer(0.1, self.publish_ticks)
        self.get_logger().info("Encoder Node started with Hardware Interrupts")

    #Function to update direction
    def getdirection(self, msg):
        linear = msg.linear.x
        angular = msg.angular.z

        if linear > 0:
            self.dleft = 1
            self.dright = 1
        elif linear < 0:
            self.dleft = -1
            self.dright = -1
        elif angular > 0:
            self.dleft = -1
            self.dright = 1
        elif angular < 0:
            self.dleft = 1
            self.dright = -1
        else:
            self.dleft = 0
            self.dright = 0

    def count_left(self):
        self.left_ticks += self.dleft

    def count_right(self):
        self.right_ticks += self.dright

    def publish_ticks(self):
        msg_left = Int32()
        msg_left.data = self.left_ticks
        self.pub_left.publish(msg_left)

        msg_right = Int32()
        msg_right.data = self.right_ticks
        self.pub_right.publish(msg_right)

        self.get_logger().info(f'L: {self.left_ticks}, R: {self.right_ticks}')


def main(args=None):
    rclpy.init(args=args)
    node = EncoderNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
