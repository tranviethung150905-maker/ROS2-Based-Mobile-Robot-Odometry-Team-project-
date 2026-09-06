import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import sys, termios, tty, select

class ControlNode(Node):

    def __init__(self):
        super().__init__('control_node')

        self.publisher = self.create_publisher(Twist, 'cmd_vel', 10)

    def get_key(self):

        tty.setraw(sys.stdin.fileno())

        # wait 0.1 sec for key input
        rlist, _, _ = select.select([sys.stdin], [], [], 0.25)          #wait maixmum 0.25 second if a key is pressed
        #select check [sys.stdin] is readable or not, wait up to 0.25 second to check
        #if stdin readable then pass [sys.stdin] to return
        #else return empty list []

        if rlist:           #if rlist contain something => True
            key = sys.stdin.read(1)
        else:
            key = ''

        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)

        return key

    def run(self):

        print("Use WASD keys to control. Press q to quit.")
        counter = 0
        while True:

            key = self.get_key()

            if key == '\x03':
                raise KeyboardInterrupt

            msg = Twist()

            # FORWARD
            if key == 'w':
                counter += 1
                if counter > 1: msg.linear.x = 1.0

            # BACKWARD
            elif key == 's':
                counter += 1
                if counter> 1: msg.linear.x = -1.0

            # LEFT
            elif key == 'a':
                counter += 1
                if counter > 1: msg.angular.z = 1.0

            # RIGHT
            elif key == 'd':
                counter += 1
                if counter > 1: msg.angular.z = -1.0

            # QUIT
            elif key == 'q':
                break

            # NO KEY -> STOP
            else:
                if counter > 1:  
                    counter = 0
                    msg.linear.x = 0.0
                    msg.angular.z = 0.0
                else:
                    # Skip publishing and looping if we are just waiting out the OS delay
                    continue

            self.publisher.publish(msg)

            self.get_logger().info(
                f'Linear: {msg.linear.x}, Angular: {msg.angular.z}'
            )

def main(args=None):

    global settings

    settings = termios.tcgetattr(sys.stdin)

    rclpy.init(args=args)

    node = ControlNode()

    try:
        node.run()

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        rclpy.shutdown()
