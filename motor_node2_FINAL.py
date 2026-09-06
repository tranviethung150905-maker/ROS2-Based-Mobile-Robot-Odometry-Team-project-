import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from gpiozero import LED, PWMLED

class MotorNode(Node):
    def __init__(self):
        super().__init__('motor_node')

        # 1. Initialize hardware ONCE
        # PWM pins
        self.ena = PWMLED("BOARD12")   # GPIO18
        self.enb = PWMLED("BOARD33")   # GPIO13

        # Right motor (motor b)
        self.in4 = LED("BOARD18")
        self.in3 = LED("BOARD22")

        # Left motor (motor a)
        self.in2 = LED("BOARD13")
        self.in1 = LED("BOARD15")

        self.compensate = 0.23

    

        self.subscription = self.create_subscription(
            Twist,
            'cmd_vel',
            self.callback,
            10)

        self.get_logger().info("Motor Node started, listening to /cmd_vel")

    def callback(self, msg):
        linear = msg.linear.x
        angular = msg.angular.z

        # 2. Decide and Execute in one place
        if linear > 0:
            self.move_forward()
        elif linear < 0:
            self.move_backward()
        elif angular > 0:
            self.turn_left()
        elif angular < 0:
            self.turn_right()
        else:
            self.stop_motors()

    # 3. Dedicated helper methods for cleaner logic
    def move_forward(self):
        self.ena.value = 1 - self.compensate    #right
        self.enb.value = 1    #left
        self.in4.on()
        self.in3.off()
        self.in2.on()
        self.in1.off()
        self.get_logger().info("Action: FORWARD")

    def turn_right(self):
        self.ena.value = 0.6
        self.enb.value = 0.6
        self.in4.on()
        self.in3.off()
        self.in2.off()
        self.in1.on()
        self.get_logger().info("Action: TURN RIGHT")

    def turn_left(self):
        self.ena.value = 0.6
        self.enb.value = 0.6
        self.in4.off()
        self.in3.on()
        self.in2.on()
        self.in1.off()
        self.get_logger().info("Action: TURN LEFT")

    def move_backward(self):
        self.ena.value = 1 - self.compensate
        self.enb.value = 1
        self.in4.off()
        self.in3.on()
        self.in2.off()
        self.in1.on()
        self.get_logger().info("Action: BACKWARD")

    def stop_motors(self):
        self.ena.value = 0
        self.enb.value = 0
        self.in4.off()
        self.in3.off()
        self.in2.off()
        self.in1.off()
        self.get_logger().info("Action: STOP")

def main(args=None):
    rclpy.init(args=args)
    node = MotorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Gpiozero cleans up pins automatically when the object is destroyed
        node.destroy_node()
        rclpy.shutdown()