#!/bin/env python3
import pyglet
from pyglet.gl import *
import random
from particlesystem import ParticleSystem

class HelloWorldWindow(pyglet.window.Window):
    def __init__(self):
        super().__init__()
        self.spritesheet=pyglet.image.load('./earth.png')
        self.spriterects=[]
        ## pyglet places coordinates at bottom of picture
        for row in range(7,-1,-1):
            for col in range(8):
                self.spriterects.append([col*128,row*128,128,128])
        image_grid= [self.spritesheet.get_region(*self.spriterects[i]) for i in range(64)]
        for img in image_grid:
            img.anchor_x=64
            img.anchor_y=64
        self.earth = pyglet.image.Animation.from_image_sequence(image_grid, duration=0.025)
        self.sprites=[]
        for _ in range(2):
            sprite= pyglet.sprite.Sprite(img=self.earth)
            sprite.update(scale_x=0.5,scale_y=0.5,x=random.randint(64,self._width),y=random.randint(128,self._height-64))
            sprite.speed=pyglet.math.Vec2(random.random()*4-2,0)
            sprite.pos=pyglet.math.Vec2(sprite.x,sprite.y)
            self.sprites.append(sprite)

        ps=ParticleSystem("resource/particles/galaxy_04.pex")
        ps.emitter_x=self._width//2
        ps.emitter_y=self.height//2
        ps.runfor()
        self.emitters=[ps]

        pyglet.clock.schedule_interval(self.physics,0.002)
        pyglet.clock.schedule_interval(self.animate,0.016)

    def animate(self,dt):
        for ps in self.emitters:
            ps.advance_system(dt)
        for i in range(len(self.emitters)-1,-1,-1): ## going backward as we will delete
            if not self.emitters[i].running and len(self.emitters[i].particles)<1:
                print("removing particle generator")
                del self.emitters[i]

    def physics(self,dt):
        ## very inaccurate physics, but avoids pymunk dependency.
        for idx,s1 in enumerate(self.sprites[0:-1]):
            for s2 in self.sprites[idx+1:]:
                if s1.pos.distance(s2.pos)<=64:
                    v=(s1.pos-s2.pos).normalize()
                    s1.speed=s1.speed.reflect(v)
                    s2.speed=s2.speed.reflect(v)
                    ## add paticle emitter
                    ps=ParticleSystem("resource/particles/treasure.pex")
                    ps.emitter_x=(s1.pos.x+s2.pos.x)//2
                    ps.emitter_y=(s1.pos.y+s2.pos.y)//2
                    ps.runfor()
                    self.emitters.append(ps)
        for sprite in self.sprites:
            sprite.speed.y-=0.005
            if sprite.pos.x<64 or sprite.pos.x>self._width-64:
                sprite.speed.x=-sprite.speed.x
                sprite.pos.x=sprite.pos.x+sprite.speed.x
            if sprite.pos.y<64 or sprite.pos.y>self._height-64:
                sprite.speed.y=-sprite.speed.y
                sprite.pos.y=sprite.pos.y+sprite.speed.y
            sprite.pos.x=sprite.pos.x+sprite.speed.x
            sprite.pos.y=sprite.pos.y+sprite.speed.y
            sprite.update(x=sprite.pos.x,y=sprite.pos.y)

    def on_draw(self):
        self.clear()
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        for ps in self.emitters:
            ps.draw()
        for sprite in self.sprites:
            sprite.draw()


if __name__ == '__main__':
    window = HelloWorldWindow()
    pyglet.app.run()