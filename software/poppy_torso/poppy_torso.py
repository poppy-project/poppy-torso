import numpy
import os

from functools import partial

from poppy.creatures import AbstractPoppyCreature

from .primitives.safe import LimitTorque, TemperatureMonitor
from .primitives.dance import SimpleBodyBeatMotion
from .primitives.idle import UpperBodyIdleMotion, HeadIdleMotion
from .primitives.interaction import ArmsTurnCompliant, PuppetMaster


class PoppyTorso(AbstractPoppyCreature):

    @classmethod
    def setup(cls, robot):
        robot._primitive_manager._filter = partial(numpy.sum, axis=0)

        if robot.simulated:
            cls.vrep_hack(robot)

        for m in robot.motors:
            m.goto_behavior = 'minjerk'
            # Avoid motor block with safe compliance at startup
            if m.present_position < min(m.angle_limit):
                m.compliant = False
                m.goto_position(min(m.angle_limit) + 10, 0.5, wait=True)
                m.compliant = True

            if m.present_position > max(m.angle_limit):
                m.compliant = False
                m.goto_position(max(m.angle_limit) - 10, 0.5, wait=True)
                m.compliant = True

            m.compliant_behavior = 'safe'

        robot.attach_primitive(LimitTorque(robot, torque_max=80), 'limit_torque')
        # robot.limit_torque.start()

        # Temperature monitoring
        sound_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  'media', 'sounds', 'error.wav')
        robot.attach_primitive(TemperatureMonitor(robot, sound=sound_file), 'temperature_monitoring')
        robot.temperature_monitoring.start()

        robot.attach_primitive(SimpleBodyBeatMotion(robot, 50), 'dance_beat_motion')

        # Idle primitives
        robot.attach_primitive(UpperBodyIdleMotion(robot, 50), 'upper_body_idle_motion')
        robot.attach_primitive(HeadIdleMotion(robot, 50), 'head_idle_motion')

        # Interaction primitives
        robot.attach_primitive(ArmsTurnCompliant(robot, 50), 'arms_turn_compliant')
        robot.attach_primitive(PuppetMaster(robot, 50), 'arms_copy_motion')

    @classmethod
    def vrep_hack(cls, robot):
        # fix vrep orientation bug
        wrong_motor = [robot.bust_x, ]

        for m in wrong_motor:
            m.direct = not m.direct
            m.offset = -m.offset
