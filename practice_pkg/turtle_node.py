import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose
from turtlesim.srv import TeleportAbsolute
from std_srvs.srv import Empty  # Service type for clearing background trace


class TurtleControllerNode(Node):
    def __init__(self):
        super().__init__('turtle_gui_node')

        # 1. Publisher for velocity commands (/turtle1/cmd_vel)
        self.cmd_vel_pub = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)

        # 2. Subscriber for position updates (/turtle1/pose)
        self.pose_sub = self.create_subscription(
            Pose,
            '/turtle1/pose',
            self._pose_callback,
            10
        )

        # 3. Service client for resetting position (/turtle1/teleport_absolute)
        self.teleport_client = self.create_client(TeleportAbsolute, '/turtle1/teleport_absolute')

        # 4. Service client for clearing background trace (/clear)
        self.clear_client = self.create_client(Empty, '/clear')

        # Variable to store current pose
        self.current_pose = Pose()

    def _pose_callback(self, msg: Pose):
        """Update real-time pose from turtlesim"""
        self.current_pose = msg

    def publish_cmd_vel(self, linear_x: float = 0.0, angular_z: float = 0.0):
        """Publish velocity command topic"""
        msg = Twist()
        msg.linear.x = float(linear_x)
        msg.angular.z = float(angular_z)
        self.cmd_vel_pub.publish(msg)

    # --- Directional movement methods ---
    def move_forward(self, speed: float = 2.0):
        self.publish_cmd_vel(linear_x=speed, angular_z=0.0)

    def move_backward(self, speed: float = 2.0):
        self.publish_cmd_vel(linear_x=-speed, angular_z=0.0)

    def turn_left(self, speed: float = 2.0):
        self.publish_cmd_vel(linear_x=0.0, angular_z=speed)

    def turn_right(self, speed: float = 2.0):
        self.publish_cmd_vel(linear_x=0.0, angular_z=-speed)

    def stop(self):
        self.publish_cmd_vel(linear_x=0.0, angular_z=0.0)

    # --- Reset pose (5.44, 5.44) and clear trace method ---
    def reset_pose(self, x: float = 5.44, y: float = 5.44, theta: float = 0.0):
        if not self.teleport_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().warn("Teleport service is not available.")
            return False

        # 1. Teleport 요청 보내기
        req = TeleportAbsolute.Request()
        req.x = float(x)
        req.y = float(y)
        req.theta = float(theta)
        future = self.teleport_client.call_async(req)

        # 2. Teleport 처리가 완료(Done)된 직후 /clear 호출
        def _on_teleport_done(fut):
            if self.clear_client.wait_for_service(timeout_sec=1.0):
                clear_req = Empty.Request()
                self.clear_client.call_async(clear_req)
            else:
                self.get_logger().warn("Clear service is not available.")

        future.add_done_callback(_on_teleport_done)
        return True

    def get_pose_info(self) -> dict:
        """Format current pose for GUI delivery"""
        return {
            'x': round(self.current_pose.x, 2),
            'y': round(self.current_pose.y, 2),
            'theta': round(self.current_pose.theta, 2)
        }