from numpy import mean
from collections import deque

from pypot.primitive import LoopPrimitive

class TorsoTurnCompliant(LoopPrimitive):
    """ Automatically turns the torso motors compliant when a force is applied. """

    def setup(self):
        self.compliance_torque_threshold = {
            'head_z' : 0,
            'head_y' : 0,

            'abs_z' : 3,

            'bust_y' : 14,
            'bust_x' : 14,

            'l_shoulder_y' : 11,
            'l_shoulder_x' : 9,
            'l_arm_z' : 3,
            'l_elbow_y' : 3,

            'r_shoulder_y' : 11,
            'r_shoulder_x' : 9,
            'r_arm_z' : 3,
            'r_elbow_y' : 3,
        }

        for m in self.robot.motors:
            m.compliant = False
            m.torque_limit = self.compliance_torque_threshold[m.name]

    def update(self):
        for m in self.robot.motors:
            if abs(m.present_load) > self.compliance_torque_threshold[m.name]:
                m.compliant = True
            elif abs(m.present_speed) < 2:
                m.compliant = False


class ArmsTurnCompliant(LoopPrimitive):
    """ Automatically turns the arms compliant when a force is applied. """
    def setup(self):
        for m in self.robot.arms:
            m.compliant = False
            m.torque_limit = 20

        freq = 1. / self.period
        self.l_arm_torque = deque([0], int(0.2 * freq))
        self.r_arm_torque = deque([0], int(0.2 * freq))

    def update(self):
        for side in ('l', 'r'):
            recent_arm_torques = getattr(self, '{}_arm_torque'.format(side))
            motors = getattr(self.robot, '{}_arm'.format(side))

            recent_arm_torques.append(max([abs(m.present_load) for m in motors]))

            mt = mean(recent_arm_torques)

            if mt > 20:
                for m in motors:
                    m.compliant = True
            elif mt < 7:
                for m in motors:
                    m.compliant = False


class PuppetMaster(LoopPrimitive):
    """ Apply the motion made on the left arm to the right arm. """
    def setup(self):
        for m in self.robot.arms:
            m.moving_speed = 0.
            m.torque_limit = 50.

        for m in self.robot.l_arm:
            m.compliant = True

        for m in self.robot.r_arm:
            m.compliant = False

    def update(self):
        for lm, rm in zip(self.robot.l_arm, self.robot.r_arm):
            rm.goal_position = lm.present_position * (1 if lm.direct else -1)

    def teardown(self):
        for m in self.robot.arms:
            m.compliant = False

        self.robot.goto_position({m.name: 0. for m in self.robot.arms},
                                 2., wait=True)

        for m in self.robot.arms:
            m.moving_speed = 0.
