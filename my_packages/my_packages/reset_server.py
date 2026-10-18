#!/usr/bin/env python3

# Step 5

import time
import rclpy
from rclpy.node import Node
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor

from std_srvs.srv import Trigger, Empty
from turtlesim.srv import SetPen, TeleportAbsolute


class ResetNode(Node):
    def __init__(self):
        super().__init__('reset_service_node')
        self.cb_group = ReentrantCallbackGroup()

        self.clear_client_ = self.create_client(
            Empty,
            '/clear',
            callback_group=self.cb_group
        )

        self.pen_client_ = self.create_client(
            SetPen,
            '/turtle1/set_pen',
            callback_group=self.cb_group
        )

        self.teleport_client_ = self.create_client(
            TeleportAbsolute,
            '/turtle1/teleport_absolute',
            callback_group=self.cb_group
        )

        self.reset_srv_ = self.create_service(
            Trigger,
            'reset_node',
            self.reset_callback,
            callback_group=self.cb_group
        )

        self.get_logger().info('Reset service has been started.')

    # Wait until each service is available. Method
    def wait_for_service(self, client):
        while not client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info(f'Waiting for service: {client.srv_name}')

    # Call each service request
    def call_service(self, client, request):
        future = client.call_async(request)

        while rclpy.ok() and not future.done():
            time.sleep(0.01)

        if not future.done():
            return False

        if future.exception() is not None:
            self.get_logger().error(str(future.exception()))
            return False

        return True

    # Set pen method
    def set_pen(self, off):
        request = SetPen.Request()
        request.r = 179
        request.g = 184
        request.b = 255
        request.width = 3
        request.off = off

        return self.call_service(self.pen_client_, request)

    def reset_callback(self, request, response):
        self.wait_for_service(self.pen_client_)
        self.wait_for_service(self.teleport_client_)
        self.wait_for_service(self.clear_client_)

        # Lift the pen so teleporting does not draw a line.
        if not self.set_pen(True):
            response.success = False
            response.message = 'Failed to lift the pen'
            return response

        # Return turtle to its initial pose.
        teleport_request = TeleportAbsolute.Request()
        teleport_request.x = 5.544445
        teleport_request.y = 5.544445
        teleport_request.theta = 0.0

        if not self.call_service(self.teleport_client_,teleport_request):
            response.success = False
            response.message = 'Failed to teleport turtle'
            return response

        if not self.call_service(self.clear_client_,Empty.Request()):
            response.success = False
            response.message = 'Failed to clear screen'
            return response

        if not self.set_pen(False):
            response.success = False
            response.message = 'Turtle reset, but failed to lower pen'
            return response

        response.success = True
        response.message = 'Turtle reset successfully'
        return response


def main(args=None):
    rclpy.init(args=args)
    node = ResetNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    executor.spin()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()