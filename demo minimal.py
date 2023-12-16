#!/bin/env python3
import pyglet
from particlesystem import ParticleSystem

class ParticleSystemWindow(pyglet.window.Window):
    def __init__(self):
        super().__init__()
        self.ps=ParticleSystem("resource/particles/galaxy_04.pex")
        self.ps.emitter_x=self._width//2
        self.ps.emitter_y=self.height//2
        self.ps.runfor()
        pyglet.clock.schedule_interval(self.ps.advance_system,0.016)

    def on_draw(self):
        self.clear()
        self.ps.draw()

if __name__ == '__main__':
    window = ParticleSystemWindow()
    pyglet.app.run()