import os,sys,math
import pyglet
from pyglet.gl import *
from random import randint,uniform,random
from xml.dom.minidom import parse as parse_xml

def random_variance(base, variance):
    return base + variance * (random() * 2.0 - 1.0)

def random_color_variance(base, variance):
    return [min(max(0.0, (random_variance(base[i], variance[i]))), 1.0) for i in range(4)]

__all__ = ['EMITTER_TYPE_GRAVITY', 'EMITTER_TYPE_RADIAL', 'Particle', 'ParticleSystem']

EMITTER_TYPE_GRAVITY = 0
EMITTER_TYPE_RADIAL = 1

BLEND_FUNC = {
            0: GL_ZERO,
            1: GL_ONE,
            0x300: GL_SRC_COLOR,
            0x301: GL_ONE_MINUS_SRC_COLOR,
            0x302: GL_SRC_ALPHA,
            0x303: GL_ONE_MINUS_SRC_ALPHA,
            0x304: GL_DST_ALPHA,
            0x305: GL_ONE_MINUS_DST_ALPHA,
            0x306: GL_DST_COLOR,
            0x307: GL_ONE_MINUS_DST_COLOR
}
BLEND_FUNC_REV={value:key for key, value in BLEND_FUNC.items()}

class Particle(object):
    def __init__(self,img,batch,blend_src,blend_dst):
        self.sp=pyglet.sprite.Sprite(img,x=-1000,y=-1000,batch=batch,blend_src=blend_src,blend_dest=blend_dst)

class ParticleSystem(object):
    def __init__(self,config):
        self.particles=[]
        self.batch=pyglet.graphics.Batch()
        self.running=True
        if config:
            if config.endswith(".pex"):
                self._parse_xml_config(config)
            elif config.endswith(".json"):
                self._parse_json_config(config)
        else:
            print("A config is mandatory")
        self.running=False

    def runfor(self,duration=None):
        self.running=True
        self.runtime=0
        if duration!=None:
            self.duration=duration

    def stop(self):
        self.running=False

    def advance_system(self,dt):
        if self.life_span>0:
            emission_rate = self.max_num_particles / self.life_span
        else:
            return
        numparticles=int(dt*emission_rate)
        for p in self.particles:
            try:
                if p.current_time>=p.total_time-0.0001:
                    p.sp.delete()
                    self.particles.remove(p)
                else:
                    self.advance_particle(p,dt)
            except:
                pass
        # only add particles if emitter is running
        if self.running and (self.runtime<self.duration or self.duration<0):
            self.runtime+=dt
            while numparticles:
                numparticles-=1
                p=Particle(self.texture,self.batch,blend_src=self.blend_factor_source,blend_dst=self.blend_factor_dest)
                self.init_particle(p)
                self.particles.append(p)
        else:
            self.running=False
    
    def init_particle(self,particle):
        life_span = random_variance(self.life_span, self.life_span_variance)
        if life_span <= 0.0:
            return
        particle.current_time = 0.0
        particle.total_time = life_span
        angle = random_variance(self.emit_angle, self.emit_angle_variance)
        speed = random_variance(self.speed, self.speed_variance)
        particle.velocity_x = speed * math.cos(angle)
        particle.velocity_y = speed * math.sin(angle)
        particle.emit_rotation = random_variance(self.emit_angle, self.emit_angle_variance)
        particle.emit_rotation_delta = random_variance(self.rotate_per_second, self.rotate_per_second_variance)
        particle.emit_radius = random_variance(self.max_radius, self.max_radius_variance)
        particle.emit_radius_delta = (self.max_radius - self.min_radius) / life_span
        particle.x = random_variance(self.emitter_x, self.emitter_x_variance)
        particle.y = random_variance(self.emitter_y, self.emitter_y_variance)
        particle.start_x = self.emitter_x
        particle.start_y = self.emitter_y
        particle.radial_acceleration = random_variance(self.radial_acceleration, self.radial_acceleration_variance)
        particle.tangent_acceleration = random_variance(self.tangential_acceleration, self.tangential_acceleration_variance)
        start_size = random_variance(self.start_size, self.start_size_variance)
        end_size = random_variance(self.end_size, self.end_size_variance)
        start_size = max(0.1, start_size)
        end_size = max(0.1, end_size)
        particle.scale = start_size / self.texture.width
        particle.scale_delta = ((end_size - start_size) / life_span) / self.texture.width
        start_rotation = random_variance(self.start_rotation, self.start_rotation_variance)
        end_rotation = random_variance(self.end_rotation, self.end_rotation_variance)
        particle.rotation = start_rotation
        particle.rotation_delta = (end_rotation - start_rotation) / life_span
        start_color = random_color_variance(self.start_color, self.start_color_variance)
        end_color = random_color_variance(self.end_color, self.end_color_variance)
        particle.color_delta = [(end_color[i] - start_color[i]) / life_span for i in range(4)]
        particle.color = start_color

    def advance_particle(self,particle,passed_time):
        passed_time = min(passed_time, particle.total_time - particle.current_time)
        particle.current_time += passed_time
        if self.emitter_type == EMITTER_TYPE_RADIAL:
            particle.emit_rotation += particle.emit_rotation_delta * passed_time
            particle.emit_radius -= particle.emit_radius_delta * passed_time
            particle.x = self.emitter_x - math.cos(particle.emit_rotation) * particle.emit_radius
            particle.y = self.emitter_y - math.sin(particle.emit_rotation) * particle.emit_radius
            if particle.emit_radius < self.min_radius:
                particle.current_time = particle.total_time
        else:
            distance_x = particle.x - particle.start_x
            distance_y = particle.y - particle.start_y
            distance_scalar = math.sqrt(distance_x * distance_x + distance_y * distance_y)
            if distance_scalar < 0.01:
                distance_scalar = 0.01
            radial_x = distance_x / distance_scalar
            radial_y = distance_y / distance_scalar
            tangential_x = radial_x
            tangential_y = radial_y
            radial_x *= particle.radial_acceleration
            radial_y *= particle.radial_acceleration
            new_y = tangential_x
            tangential_x = -tangential_y * particle.tangent_acceleration
            tangential_y = new_y * particle.tangent_acceleration
            particle.velocity_x += passed_time * (self.gravity_x + radial_x + tangential_x)
            particle.velocity_y += passed_time * (self.gravity_y + radial_y + tangential_y)
            particle.x += particle.velocity_x * passed_time
            particle.y += particle.velocity_y * passed_time

        particle.scale += particle.scale_delta * passed_time
        particle.rotation += particle.rotation_delta * passed_time
        particle.color = [particle.color[i] + particle.color_delta[i] * passed_time for i in range(4)]
        particle.sp.x=particle.x
        particle.sp.y=particle.y
        particle.sp.scale=particle.scale
        particle.sp.rotation=math.degrees(particle.rotation)
        particle.sp.color=tuple([i*255 for i in particle.color[0:3]])
        particle.sp.opacity=particle.color[3]*255

    def _parse_json_config(self,config):
        import json
        with open(config) as json_file:
            data = json.load(json_file)
            texture_path=data["textureFileName"]
            self.texture_name=texture_path
            config_dir_path = os.path.dirname(os.path.abspath(config))
            path = os.path.join(config_dir_path,"pixmaps", texture_path)
            if os.path.exists(path):
                self.texture_path = path
            else:
                self.texture_name="particle.png"
                self.texture_path=os.path.join(config_dir_path,"pixmaps", "particle.png")
                #self.texture_path = texture_path
            self.texture = pyglet.image.load(self.texture_path)
            self.texture.anchor_x = self.texture.width // 2           ## center picture
            self.texture.anchor_y = self.texture.height // 2
            self.emitter_x = 100.0
            self.emitter_y = 100.0
            self.emitter_x_variance = float(data['sourcePositionVariancex'])
            self.emitter_y_variance = float(data['sourcePositionVariancey'])
            self.gravity_x = float(data['gravityx'])
            self.gravity_y = float(data['gravityy'])
            self.emitter_type = int(data['emitterType'])
            self.max_num_particles = int(data['maxParticles'])
            self.life_span = max(0.01, float(data['particleLifespan']))
            
            self.life_span_variance = float(data['particleLifespanVariance'])
            self.start_size = float(data['startParticleSize'])
            self.start_size_variance = float(data['startParticleSizeVariance'])
            self.end_size = float(data['finishParticleSize'])
            self.end_size_variance = float(data['finishParticleSizeVariance'])
            self.emit_angle = math.radians(float(data['angle']))
            self.emit_angle_variance = math.radians(float(data['angleVariance']))
            self.start_rotation = math.radians(float(data['rotationStart']))
            self.start_rotation_variance = math.radians(float(data['rotationStartVariance']))
            self.end_rotation = math.radians(float(data['rotationEnd']))
            self.end_rotation_variance = math.radians(float(data['rotationEndVariance']))
            self.speed = float(data['speed'])
            self.speed_variance = float(data['speedVariance'])
            self.radial_acceleration = float(data['radialAcceleration'])
            self.radial_acceleration_variance = float(data['radialAccelVariance'])
            self.tangential_acceleration = float(data['tangentialAcceleration'])
            self.tangential_acceleration_variance = float(data['tangentialAccelVariance'])
            self.max_radius = float(data['maxRadius'])
            self.max_radius_variance = float(data['maxRadiusVariance'])
            self.min_radius = float(data['minRadius'])
            self.rotate_per_second = math.radians(float(data['rotatePerSecond']))
            self.rotate_per_second_variance = math.radians(float(data['rotatePerSecondVariance']))
            start_red=float(data["startColorRed"])
            start_red_variance=float(data["startColorVarianceRed"])
            finish_red=float(data["finishColorRed"])
            finish_red_variance=float(data["startColorVarianceRed"])
            start_green=float(data["startColorGreen"])
            start_green_variance=float(data["startColorVarianceGreen"])
            finish_green=float(data["finishColorGreen"])
            finish_green_variance=float(data["startColorVarianceGreen"])
            start_blue=float(data["startColorBlue"])
            start_blue_variance=float(data["startColorVarianceBlue"])
            finish_blue=float(data["finishColorBlue"])
            finish_blue_variance=float(data["startColorVarianceBlue"])
            start_alpha=float(data["startColorAlpha"])
            start_alpha_variance=float(data["startColorVarianceAlpha"])
            finish_alpha=float(data["finishColorAlpha"])
            finish_alpha_variance=float(data["startColorVarianceAlpha"])
            self.start_color=[start_red,start_green,start_blue,start_alpha]
            self.start_color_variance=[start_red_variance,start_green_variance,start_blue_variance,start_alpha_variance]
            self.end_color=[finish_red,finish_green,finish_blue,finish_alpha]
            self.end_color_variance=[finish_red_variance,finish_green_variance,finish_blue_variance,finish_alpha_variance]
            #self.start_color = self._parse_color('startColor')
            #self.start_color_variance = self._parse_color('startColorVariance')
            #self.end_color = self._parse_color('finishColor')
            #self.end_color_variance = self._parse_color('finishColorVariance')
            self.blend_factor_source = BLEND_FUNC[data['blendFuncSource']]
            self.blend_factor_dest = BLEND_FUNC[data['blendFuncDestination']]
            try:
                self.duration = float(data['duration'])
            except:
                self.duration=-1

    def _parse_xml_config(self, config):
        self._config = parse_xml(config)
        texture_path = self._parse_data('texture', 'name')
        self.texture_name=texture_path
        config_dir_path = os.path.dirname(os.path.abspath(config))
        path = os.path.join(config_dir_path,"pixmaps", texture_path)
        if os.path.exists(path):
            self.texture_path = path
        else:
            self.texture_path = texture_path
        self.texture = pyglet.image.load(self.texture_path)
        self.texture.anchor_x = self.texture.width // 2           ## center picture
        self.texture.anchor_y = self.texture.height // 2
        try:
            self.emitter_x = float(self._parse_data('sourcePosition', 'x'))
            self.emitter_y = float(self._parse_data('sourcePosition', 'y'))
        except:
            self.emitter_x = 100.0
            self.emitter_y = 100.0
        self.emitter_x_variance = float(self._parse_data('sourcePositionVariance', 'x'))
        self.emitter_y_variance = float(self._parse_data('sourcePositionVariance', 'y'))
        self.gravity_x = float(self._parse_data('gravity', 'x'))
        self.gravity_y = float(self._parse_data('gravity', 'y'))
        self.emitter_type = int(self._parse_data('emitterType'))
        self.max_num_particles = int(self._parse_data('maxParticles'))
        self.life_span = max(0.01, float(self._parse_data('particleLifeSpan')))
        self.life_span_variance = float(self._parse_data('particleLifespanVariance'))
        self.start_size = float(self._parse_data('startParticleSize'))
        self.start_size_variance = float(self._parse_data('startParticleSizeVariance'))
        self.end_size = float(self._parse_data('finishParticleSize'))
        self.end_size_variance = float(self._parse_data('FinishParticleSizeVariance'))
        self.emit_angle = math.radians(float(self._parse_data('angle')))
        self.emit_angle_variance = math.radians(float(self._parse_data('angleVariance')))
        self.start_rotation = math.radians(float(self._parse_data('rotationStart')))
        self.start_rotation_variance = math.radians(float(self._parse_data('rotationStartVariance')))
        self.end_rotation = math.radians(float(self._parse_data('rotationEnd')))
        self.end_rotation_variance = math.radians(float(self._parse_data('rotationEndVariance')))
        self.speed = float(self._parse_data('speed'))
        self.speed_variance = float(self._parse_data('speedVariance'))
        self.radial_acceleration = float(self._parse_data('radialAcceleration'))
        self.radial_acceleration_variance = float(self._parse_data('radialAccelVariance'))
        self.tangential_acceleration = float(self._parse_data('tangentialAcceleration'))
        self.tangential_acceleration_variance = float(self._parse_data('tangentialAccelVariance'))
        self.max_radius = float(self._parse_data('maxRadius'))
        self.max_radius_variance = float(self._parse_data('maxRadiusVariance'))
        self.min_radius = float(self._parse_data('minRadius'))
        self.rotate_per_second = math.radians(float(self._parse_data('rotatePerSecond')))
        self.rotate_per_second_variance = math.radians(float(self._parse_data('rotatePerSecondVariance')))
        self.start_color = self._parse_color('startColor')
        self.start_color_variance = self._parse_color('startColorVariance')
        self.end_color = self._parse_color('finishColor')
        self.end_color_variance = self._parse_color('finishColorVariance')
        self.blend_factor_source = self._parse_blend('blendFuncSource')
        self.blend_factor_dest = self._parse_blend('blendFuncDestination')
        try:
            self.duration = float(self._parse_data('duration'))
        except:
            self.duration=-1

    def _dump_xml_config(self, config):
        with open(config,"w") as f:
            f.write('<?xml version="1.0"?>\n')
            f.write('<particleEmitterConfig>\n')
            f.write(f'  <texture name="{self.texture_name}"/>\n')
            f.write(f'  <sourcePosition x="{self.emitter_x}" y="{self.emitter_y}"/>\n')
            f.write(f'  <sourcePositionVariance x="{self.emitter_x_variance}" y="{self.emitter_y_variance}"/>\n')
            f.write(f'  <speed value="{self.speed}"/>\n')
            f.write(f'  <speedVariance value="{self.speed_variance}"/>\n')
            f.write(f'  <particleLifeSpan value="{self.life_span}"/>\n')
            f.write(f'  <particleLifespanVariance value="{self.life_span_variance}"/>\n')
            f.write(f'  <angle value="{math.degrees(self.emit_angle)}"/>\n')
            f.write(f'  <angleVariance value="{math.degrees(self.emit_angle_variance)}"/>\n')
            f.write(f'  <gravity x="{self.gravity_x}" y="{self.gravity_y}"/>\n')
            f.write(f'  <radialAcceleration value="{self.radial_acceleration}"/>\n')
            f.write(f'  <tangentialAcceleration value="{self.tangential_acceleration}"/>\n')
            f.write(f'  <radialAccelVariance value="{self.radial_acceleration_variance}"/>\n')
            f.write(f'  <tangentialAccelVariance value="{self.tangential_acceleration_variance}"/>\n')
            f.write(f'  <startColor red="{self.start_color[0]}" green="{self.start_color[1]}" blue="{self.start_color[2]}" alpha="{self.start_color[3]}"/>\n')
            f.write(f'  <startColorVariance red="{self.start_color_variance[0]}" green="{self.start_color_variance[1]}" blue="{self.start_color_variance[2]}" alpha="{self.start_color_variance[3]}"/>\n')
            f.write(f'  <finishColor red="{self.end_color[0]}" green="{self.end_color[1]}" blue="{self.end_color[2]}" alpha="{self.end_color[3]}"/>\n')
            f.write(f'  <finishColorVariance red="{self.end_color_variance[0]}" green="{self.end_color_variance[1]}" blue="{self.end_color_variance[2]}" alpha="{self.end_color_variance[3]}"/>\n')
            f.write(f'  <maxParticles value="{self.max_num_particles}"/>\n')
            f.write(f'  <startParticleSize value="{self.start_size}"/>\n')
            f.write(f'  <startParticleSizeVariance value="{self.start_size_variance}"/>\n')
            f.write(f'  <finishParticleSize value="{self.end_size}"/>\n')
            f.write(f'  <FinishParticleSizeVariance value="{self.end_size_variance}"/>\n')
            f.write(f'  <emitterType value="{self.emitter_type}"/>\n')
            f.write(f'  <maxRadius value="{self.max_radius}"/>\n')
            f.write(f'  <maxRadiusVariance value="{self.max_radius_variance}"/>\n')
            f.write(f'  <minRadius value="{self.min_radius}"/>\n')
            f.write(f'  <rotatePerSecond value="{math.degrees(self.rotate_per_second)}"/>\n')
            f.write(f'  <rotatePerSecondVariance value="{math.degrees(self.rotate_per_second_variance)}"/>\n')
            f.write(f'  <blendFuncSource value="{BLEND_FUNC_REV[self.blend_factor_source]}"/>\n')
            f.write(f'  <blendFuncDestination value="{BLEND_FUNC_REV[self.blend_factor_dest]}"/>\n')
            f.write(f'  <rotationStart value="{math.degrees(self.start_rotation)}"/>\n')
            f.write(f'  <rotationStartVariance value="{math.degrees(self.start_rotation_variance)}"/>\n')
            f.write(f'  <rotationEnd value="{math.degrees(self.end_rotation)}"/>\n')
            f.write(f'  <rotationEndVariance value="{math.degrees(self.end_rotation_variance)}"/>\n')
            f.write(f'  <duration value="{self.duration}"/>\n')
            f.write(f'</particleEmitterConfig>\n')
        f.close()

    def _parse_data(self, name, attribute='value'):
        return self._config.getElementsByTagName(name)[0].getAttribute(attribute)

    def _parse_color(self, name):
        return [float(self._parse_data(name, 'red')), float(self._parse_data(name, 'green')), float(self._parse_data(name, 'blue')), float(self._parse_data(name, 'alpha'))]

    def _parse_blend(self, name):
        value = int(self._parse_data(name))
        return BLEND_FUNC[value]

    def draw(self):
        self.batch.draw()
