#!/usr/bin/env python3
# Step 3

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter

from interfaces.srv import Speed


class PoseControlNode(Node):
    def __init__(self):
        super().__init__('pose_control')

        self.declare_parameter('linear_velocity', 2.0)
        self.declare_parameter('angular_velocity', 2.0)

        self.speed_srv_ = self.create_service(
            Speed, 
            'set_speed', 
            self.speed_callback
        )

        self.get_logger().info('Speed Control Service has been started.')

    def speed_callback(self, request, response):
        if request.linear_velocity <= 0.0 or request.angular_velocity <= 0.0:
            response.success = False
            response.message = 'Speeds must be greater than 0'
            return response

        self.set_parameters([Parameter('linear_velocity', value=request.linear_velocity),
                             Parameter('angular_velocity', value=request.angular_velocity)])

        response.success = True
        response.message = (
            f"Linear Speed = {request.linear_velocity}, "
            f"Angular Speed = {request.angular_velocity}"
        )
        return response


def main(args=None):
    rclpy.init(args=args)
    node = PoseControlNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()