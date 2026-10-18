#!/usr/bin/env python3

import sys

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.action import ActionClient

from interfaces.action import DrawSquare


class DrawSquareClient(Node):
    def __init__(self):
        super().__init__('draw_square_client')

        self.declare_parameter("side_length",2.0)

        self.client_ = ActionClient(
            self,
            DrawSquare,
            'draw_square'
        )

        self.get_logger().info("Drawing the square ;)")

    def send_goal(self, side_length):
        goal = DrawSquare.Goal()
        goal.side_length = side_length

        self.client_.wait_for_server()

        self.send_goal_future_ = self.client_.send_goal_async(
            goal,
            feedback_callback=self.feedback_callback
        )

        self.send_goal_future_.add_done_callback(
            self.goal_response_callback
        )

    def goal_response_callback(self, future):
        goal_handle = future.result()

        if not goal_handle.accepted:
            self.get_logger().error('Square goal rejected')
            return

        self.get_logger().info('Square goal accepted')

        self.result_future_ = goal_handle.get_result_async()
        self.result_future_.add_done_callback(self.result_callback)

    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        
        self.get_logger().info(f'Drawing side {feedback.current_side}/4')

    def result_callback(self, future):
        wrapped_result = future.result()
        result = wrapped_result.result

        if result.success:
            self.get_logger().info(f'Square completed: {result.message}')
        else:
            self.get_logger().error(f'Square failed: {result.message}')


def main(args=None):
    rclpy.init(args=args)
    node = DrawSquareClient()

    side_length = node.get_parameter('side_length').value
    node.send_goal(side_length)
    node.get_logger().info(f'Side length: {side_length}')

    rclpy.spin(node)

    node.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()

if __name__ == '__main__':
    main()