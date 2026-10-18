#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

from interfaces.msg import TargetPose
from interfaces.action import GoToPose


class PoseSetNode(Node):
    def __init__(self):
        super().__init__('pose_set')

        self.declare_parameter('x', 0.0)
        self.declare_parameter('y', 0.0)
        self.declare_parameter('yaw', 0.0)

        self.client_ = ActionClient(
            self, 
            GoToPose, 
            'go_to_pose'
        )

        

    def send_goal(self):
        self.client_.wait_for_server()

        goal = GoToPose.Goal()
        goal.target_pose = TargetPose(
            x=self.get_parameter('x').value,
            y=self.get_parameter('y').value,
            yaw=self.get_parameter('yaw').value)

        self.get_logger().info('Sending goal')
        future = self.client_.send_goal_async(
            goal, feedback_callback=self.feedback_callback)
        future.add_done_callback(self.response_callback)

    def feedback_callback(self, msg):
        self.get_logger().info(
            f'distance remaining: {msg.feedback.distance_remaining:.2f}')

    def response_callback(self, future):
        handle = future.result()
        if not handle.accepted:
            self.get_logger().error('Goal rejected')
            rclpy.shutdown()
            return
        handle.get_result_async().add_done_callback(self.result_callback)

    def result_callback(self, future):
        self.get_logger().info(f'Result: success = {future.result().result.success}')
        rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = PoseSetNode()
    node.send_goal()
    rclpy.spin(node)


if __name__ == "__main__":
    main()