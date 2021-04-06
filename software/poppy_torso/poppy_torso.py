import numpy
import os

from functools import partial

from pypot.creatures import AbstractPoppyCreature
from pypot.creatures.ik import IKChain

from .primitives.safe import LimitTorque, TemperatureMonitor
from .primitives.dance import SimpleBodyBeatMotion
from .primitives.posture import InitPosition
from .primitives.idle import UpperBodyIdleMotion, HeadIdleMotion
from .primitives.interaction import TorsoTurnCompliant, ArmsTurnCompliant, PuppetMaster


class PoppyTorso(AbstractPoppyCreature):
    @classmethod
    def setup(cls, robot):
        robot._primitive_manager._filter = partial(numpy.sum, axis=0)

        if robot.simulated:
            cls.vrep_hack(robot)
        for m in robot.motors:
            m.compliant_behavior = 'dummy'
            m.goto_behavior = 'dummy'

        # Add Kinematic chains for each arm
        lc = IKChain.from_poppy_creature(robot,
                                         motors=robot.torso + robot.l_arm,
                                         passiv=robot.torso,
                                         tip=[0, 0.18, 0])

        rc = IKChain.from_poppy_creature(robot,
                                         motors=robot.torso + robot.r_arm,
                                         passiv=robot.torso,
                                         tip=[0, 0.18, 0],
                                         reversed_motors=[robot.r_shoulder_x])

        robot.l_arm_chain = lc
        robot.r_arm_chain = rc

        robot.attach_primitive(LimitTorque(robot, torque_max=80), 'limit_torque')
        #robot.limit_torque.start()

        # Temperature monitoring if not in vrep
        if not robot.simulated:
            sound_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      'media', 'sounds', 'error.wav')
            robot.attach_primitive(TemperatureMonitor(robot, sound=sound_file), 'temperature_monitoring')
            robot.temperature_monitoring.start()

        robot.attach_primitive(SimpleBodyBeatMotion(robot, 50), 'dance_beat_motion')
        robot.attach_primitive(InitPosition(robot), 'init_position')



        # Idle primitives
        robot.attach_primitive(UpperBodyIdleMotion(robot, 50), 'upper_body_idle_motion')
        robot.attach_primitive(HeadIdleMotion(robot, 50), 'head_idle_motion')

        # Interaction primitives
        robot.attach_primitive(TorsoTurnCompliant(robot, 300), 'torso_turn_compliant')
        robot.attach_primitive(ArmsTurnCompliant(robot, 50), 'arms_turn_compliant')
        robot.attach_primitive(PuppetMaster(robot, 50), 'arms_copy_motion')

    @classmethod
    def vrep_hack(cls, robot):
        # fix vrep orientation bug
        wrong_motor = [robot.bust_x, ]

        for m in wrong_motor:
            m.direct = not m.direct
            m.offset = -m.offset
            
        # Fix bad motors orientation at startup (see #22)
        for m in robot.motors:
            m.goal_position = 0
