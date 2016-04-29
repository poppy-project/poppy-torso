from __future__ import division

import time
import itertools

import pypot.primitive


class InitPosition(pypot.primitive.Primitive):

    def run(self):
        self.robot.compliant = False
        self.robot.power_up()

        self.robot.goto_position(dict(zip((m.name for m in self.robot.motors), itertools.repeat(0))), 3, wait=True)
        self.robot.bust_y.goto_position(4, 1)

        time.sleep(0.5)
