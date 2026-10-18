#!/usr/bin/env python3

# Step 4

import math
import time

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.parameter import Parameter

from interfaces.srv import Speed
from interfaces.action import GoToPose

from geometry_msgs.msg import Twist
from turtlesim.msg import Pose


class PoseControlNode(Node):
    def __init__(self):
        super().__init__('pose_control')
        self.pose_ = None
        self.cb_group = ReentrantCallbackGroup()

        self.declare_parameter('linear_velocity', 2.0)
        self.declare_parameter('angular_velocity', 2.0)

        self.pose_sub_ = self.create_subscription(
            Pose,
            '/turtle1/pose', 
            self.pose_callback, 
            10,
            callback_group=self.cb_group
        )

        self.cmd_pub_ = self.create_publisher(
            Twist, 
            '/turtle1/cmd_vel', 
            10
        )

        self.speed_srv_ = self.create_service(
            Speed, 
            'set_speed', 
            self.speed_callback,
            callback_group=self.cb_group
        )

        self.goto_server_ = ActionServer(
            self, 
            GoToPose, 
            'go_to_pose',
            execute_callback=self.execute_callback,
            callback_group=self.cb_group
        )

        self.get_logger().info('Pose Control has been started.')

    def pose_callback(self, msg: Pose):
        self.pose_ = msg

    def speed_callback(self, request, response):
        if request.linear_velocity <= 0.0 or request.angular_velocity <= 0.0:
            response.success = False
            response.message = 'Speeds must be greater than 0'
            return response

        self.set_parameters(Parameter('linear_velocity', value=request.linear_velocity))
        self.set_parameters(Parameter('angular_velocity', value=request.angular_velocity))

        response.success = True
        response.message = (
            f"Linear Speed = {request.linear_velocity}, "
            f"Angular Speed = {request.angular_velocity}"
        )
        return response

    def _cancel(self, goal_handle, result):
        self.cmd_pub_.publish(Twist())
        goal_handle.canceled()
        result.success = False
        result.message = 'Canceled'
        return result


    async def execute_callback(self, goal_handle):
        target = goal_handle.request.target_pose
        x, y, yaw = target.x, target.y, target.yaw

        feedback = GoToPose.Feedback()
        result = GoToPose.Result()

        # Wait for the first pose message.
        while rclpy.ok() and self.pose_ is None:
            if goal_handle.is_cancel_requested:
                return self._cancel(goal_handle, result)

            time.sleep(0.05)

        # Go to target position.
        while rclpy.ok():
            if goal_handle.is_cancel_requested:
                return self._cancel(goal_handle, result)

            dx = x - self.pose_.x
            dy = y - self.pose_.y
            distance = math.hypot(dx, dy)

            if distance < 0.01:
                break

            angle_err = math.atan2(dy, dx) - self.pose_.theta
            angle_err = math.atan2(
                math.sin(angle_err),
                math.cos(angle_err)
            )

            lin_v = self.get_parameter('linear_velocity').value
            ang_v = self.get_parameter('angular_velocity').value

            cmd = Twist()
            cmd.angular.z = max(-ang_v, min(ang_v, 4.0 * angle_err))

            if abs(angle_err) < 0.02:
                cmd.linear.x = min(lin_v, 1.5 * distance)

            self.cmd_pub_.publish(cmd)

            feedback.remaining_distance = float(distance)
            feedback.remaining_angle = float(angle_err)
            goal_handle.publish_feedback(feedback)

            time.sleep(0.1)

        # Stop translation before rotating to the requested yaw.
        self.cmd_pub_.publish(Twist())

        # Rotate to the requested final orientation.
        while rclpy.ok():
            if goal_handle.is_cancel_requested:
                return self._cancel(goal_handle, result)

            yaw_err = yaw - self.pose_.theta
            yaw_err = math.atan2(
                math.sin(yaw_err),
                math.cos(yaw_err)
            )

            if abs(yaw_err) < 0.001:
                break

            ang_v = self.get_parameter('angular_velocity').value

            cmd = Twist()
            cmd.angular.z = max(-ang_v, min(ang_v, 4.0 * yaw_err))
            self.cmd_pub_.publish(cmd)

            feedback.remaining_distance = 0.0
            feedback.remaining_angle = float(yaw_err)
            goal_handle.publish_feedback(feedback)

            time.sleep(0.1)

        self.cmd_pub_.publish(Twist())

        result.success = True
        result.message = 'Reached target pose'
        goal_handle.succeed()
        return result



def main(args=None):
    rclpy.init(args=args)
    node = PoseControlNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    executor.spin()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()