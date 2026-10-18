#!/usr/bin/env python3

# Step 6

import asyncio
import math

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, ActionClient
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from action_msgs.msg import GoalStatus

from std_srvs.srv import Trigger
from interfaces.action import DrawSquare, GoToPose
from interfaces.msg import TargetPose


class DrawSquareNode(Node):

    def __init__(self):
        super().__init__('draw_square_node')

        self.cb_group = ReentrantCallbackGroup()

        self.reset_client_ = self.create_client(
            Trigger,
            'reset_node',
            callback_group=self.cb_group
        )

        self.goto_client_ = ActionClient(
            self,
            GoToPose,
            'go_to_pose',
            callback_group=self.cb_group
        )

        self.square_server_ = ActionServer(
            self,
            DrawSquare,
            'draw_square',
            execute_callback=self.execute_callback,
            callback_group=self.cb_group
        )

        self.get_logger().info('Draw Square Server started.')


    async def execute_callback(self, goal_handle):
        result = DrawSquare.Result()
        side = float(goal_handle.request.side_length)

        # Validate side length.
        if not 0.0 < side <= 5.0:
            result.success = False
            result.message = "Side length must be greater than 0 and at most 5."
            goal_handle.abort()
            return result

        # Checking reset service.
        while not self.reset_client_.service_is_ready():
            if goal_handle.is_cancel_requested:
                result.success = False
                result.message = "Square drawing canceled. due to an error in reset service."
                goal_handle.canceled()
                return result

            await asyncio.sleep(0.1)

        # Checking GoToPose action server.
        while not self.goto_client_.server_is_ready():
            if goal_handle.is_cancel_requested:
                result.success = False
                result.message = "Square drawing canceled. due to an error in GoToPose action server."
                goal_handle.canceled()
                return result

            await asyncio.sleep(0.1)

        # Reset the turtle.
        reset_response = await self.reset_client_.call_async(Trigger.Request())

        if not reset_response.success:
            result.success = False
            result.message = f"Reset failed: {reset_response.message}"
            goal_handle.abort()
            return result

        # Initial pose for the turtle.
        x0 = 5.544445
        y0 = 5.544445

        # Four corners, producing four sides.
        corners = [
            (x0 + side, y0, 0.0),
            (x0 + side, y0 + side, math.pi / 2.0),
            (x0, y0 + side, math.pi),
            (x0, y0, -math.pi / 2.0),
        ]

        for index, (x, y, yaw) in enumerate(corners, start=1):
            if goal_handle.is_cancel_requested:
                result.success = False
                result.message = "Square drawing canceled."
                goal_handle.canceled()
                return result

            # Publish current side feedback.
            feedback = DrawSquare.Feedback()
            feedback.current_side = float(index)
            goal_handle.publish_feedback(feedback)

            # Construct the GoToPose goal.
            goto_goal = GoToPose.Goal()
            goto_goal.target_pose = TargetPose(
                x=float(x),
                y=float(y),
                yaw=float(yaw)
            )

            # Send one goal and wait for its response.
            goal_future = self.goto_client_.send_goal_async(goto_goal)
            goto_handle = await goal_future

            if not goto_handle.accepted:
                result.success = False
                result.message = f"GoToPose goal for side {index} was rejected."
                goal_handle.abort()
                return result

            # Wait for this side to finish before sending the next.
            action_result = await goto_handle.get_result_async()

            if (action_result.status != GoalStatus.STATUS_SUCCEEDED or not action_result.result.success):
                result.success = False
                result.message = (
                    f"Side {index} failed: "
                    f"{action_result.result.message}"
                )
                goal_handle.abort()
                return result

            self.get_logger().info(f"Side {index}/4 completed.")

        result.success = True
        result.message = "Square drawn successfully."
        goal_handle.succeed()
        return result


def main(args=None):
    rclpy.init(args=args)
    node = DrawSquareNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    executor.spin()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()