#!/bin/env python3
import os,sys,math,pathlib
import pyglet
from pyglet.gl import *
from pyglet.window import key
from particlesystem import ParticleSystem
import imgui
from imgui.integrations.pyglet import create_renderer

# values for interface
textures=sorted([str(p.name) for p in pathlib.Path("./resource/particles/pixmaps").glob("*.png")])  
emittertypes={'Gravity':0,'Radial':1}
blendfunckeys=['GL_ZERO','GL_ONE','GL_SRC_COLOR','GL_ONE_MINUS_SRC_COLOR',
                    'GL_SRC_ALPHA','GL_ONE_MINUS_SRC_ALPHA','GL_DST_ALPHA',
                    'GL_ONE_MINUS_DST_ALPHA','GL_DST_COLOR','GL_ONE_MINUS_DST_COLOR']
blendfuncvalues=[GL_ZERO,GL_ONE,GL_SRC_COLOR,GL_ONE_MINUS_SRC_COLOR,
                    GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA,GL_DST_ALPHA,
                    GL_ONE_MINUS_DST_ALPHA,GL_DST_COLOR,GL_ONE_MINUS_DST_COLOR]
blendfuncdict = dict(zip(blendfunckeys,blendfuncvalues))

game_window = pyglet.window.Window(1024,768)    # main window
fps_display = pyglet.window.FPSDisplay(window=game_window)
imgui.create_context()
impl = create_renderer(game_window)
keys = key.KeyStateHandler()            # hack to enable key repeats
model=0
text_val='new.pex'
use_sliders=True

def renderinterface():
    global model,ps,text_val,use_sliders
    def key(v,d):
        for k,i in enumerate(d.keys()):
            if d[k]==v:
                return i
    
    def getfloat(lbl,value,mini,maxi):
        if use_sliders:
            return imgui.slider_float(lbl, value,mini,maxi)
        else:
            return imgui.input_float(lbl,value)

    imgui.new_frame()
    #
    use_sliders=imgui.checkbox("Use sliders", use_sliders)[1]
    if imgui.collapsing_header("Emitter & world")[0]:
        changed,ps.emitter_x_variance = getfloat("emitter_x_v", ps.emitter_x_variance, 0.0, 1500.0)
        changed,ps.emitter_y_variance = getfloat("emitter_y_v", ps.emitter_y_variance, 0.0, 1500.0)
        changed,ps.emitter_type = imgui.combo("emitter_type", ps.emitter_type, list(emittertypes.keys()))
        changed,ps.max_num_particles = imgui.slider_int("max_num_particles", ps.max_num_particles, -2,+999)
        changed,ps.emit_angle = getfloat("emit_angle", ps.emit_angle, -3.14159,3.14159)
        changed,ps.emit_angle_variance = getfloat("emit_angle_variance", ps.emit_angle_variance, -3.14159,3.14159)
        changed,ps.gravity_x = getfloat("gravity_x", ps.gravity_x, -3000, 3000)
        changed,ps.gravity_y = getfloat("gravity_y", ps.gravity_y, -3000,+3000)
        changed,ps.duration = getfloat("duration", ps.duration, 0,10.0)
        if ps.duration>=9.999:
            ps.duration=-1
    if imgui.collapsing_header("Particle")[0]:
        changed,t = imgui.combo("texture", textures.index(ps.texture_name), textures)
        if changed:
            ps.texture_path=ps.texture_path.replace(ps.texture_name,textures[t])
            ps.texture_name=textures[t]
            ps.texture=pyglet.image.load(ps.texture_path)
            ps.texture.anchor_x = ps.texture.width // 2           ## center picture
            ps.texture.anchor_y = ps.texture.height // 2
        changed,ps.life_span=getfloat("lifespan", ps.life_span, 0.0, 10.0)
        changed,ps.life_span_variance = getfloat("lifespan_v", ps.life_span_variance, 0.0, 1.0)
        changed,ps.start_size = getfloat("start_size", ps.start_size, 0,70)
        changed,ps.start_size_variance = getfloat("start_size_variance", ps.start_size_variance, 0,70)
        changed,ps.end_size = getfloat("end_size", ps.end_size, 0,70)
        changed,ps.end_size_variance = getfloat("end_size_variance", ps.end_size_variance, 0,70)
        changed,ps.start_rotation = getfloat("start_rotation", ps.start_rotation, 0,3.14159)
        changed,ps.start_rotation_variance = getfloat("start_rotation_variance", ps.start_rotation_variance, -3.14159,3.14159)
        changed,ps.end_rotation = getfloat("end_rotation", ps.end_rotation, 0,3.14159)
        changed,ps.end_rotation_variance = getfloat("end_rotation_variance", ps.end_rotation_variance, -3.14159,3.14159)
        changed,ps.speed = getfloat("speed", ps.speed, -500,500)
        changed,ps.speed_variance = getfloat("speed_variance", ps.speed_variance, -500,500)
        changed,ps.radial_acceleration = getfloat("radial_acceleration", ps.radial_acceleration, -500,500)
        changed,ps.radial_acceleration_variance = getfloat("radial_acceleration_variance", ps.radial_acceleration_variance, -500,500)
        changed,ps.tangential_acceleration = getfloat("tangential_acceleration", ps.tangential_acceleration, -500,500)
        changed,ps.tangential_acceleration_variance = getfloat("tangential_acceleration_variance", ps.tangential_acceleration_variance, -500,500)
        changed,ps.max_radius = getfloat("max_radius", ps.max_radius, 0,500)
        changed,ps.max_radius_variance = getfloat("max_radius_variance", ps.max_radius_variance, 0,500)
        changed,ps.min_radius = getfloat("min_radius", ps.min_radius, 0,500)
        changed,ps.rotate_per_second = getfloat("rotate_per_second", ps.rotate_per_second, -3.14159,3.14159)
        changed,ps.rotate_per_second_variance = getfloat("rotate_per_second_variance", ps.rotate_per_second_variance, -3.14159,3.14159)
    if imgui.collapsing_header("Colors & Blending")[0]:
        changed,ps.start_color=imgui.color_edit4("start_color", *ps.start_color)
        changed,ps.start_color_variance=imgui.color_edit4("start_color_variance", *ps.start_color_variance)
        changed,ps.end_color=imgui.color_edit4("end_color", *ps.end_color)
        changed,ps.end_color_variance=imgui.color_edit4("end_color_variance", *ps.end_color_variance)
        changed,ps.blend_factor_source = imgui.combo("blend_factor_source", blendfuncvalues.index(ps.blend_factor_source), blendfunckeys)
        ps.blend_factor_source=blendfuncvalues[ps.blend_factor_source]
        changed,ps.blend_factor_dest = imgui.combo("blend_factor_dest", blendfuncvalues.index(ps.blend_factor_dest), blendfunckeys)
        ps.blend_factor_dest=blendfuncvalues[ps.blend_factor_dest]
    if imgui.collapsing_header("Load model")[0]:
        changed,model = imgui.combo("load model", model, models)
        if changed:
            ps.stop()
            ps=ParticleSystem("resource/particles/"+models[model])
            ps.emitter_x=512
            ps.emitter_y=360
            print(ps.duration)
            ps.runfor(None)
        changed, text_val = imgui.input_text('Save as...',text_val,256)
        if imgui.button("save"):
            print(text_val)
            ps._dump_xml_config("resource/particles/"+text_val)
            if text_val in models:
                pass
            else:
                models.append(text_val)
            model=models.index(text_val)
    imgui.render()
    impl.render(imgui.get_draw_data())

@game_window.event
def on_draw():
    game_window.clear()
    fps_display.draw()
    ps.draw()
    renderinterface()
    
def on_key_press(symbol, modifiers):
    if imgui.get_io().want_capture_keyboard:
        return
    if symbol==pyglet.window.key.J:
        player.image=jumpanim
    if symbol==pyglet.window.key.W:
        player.image=walkanim

def on_key_release(symbol, modifiers):
    if imgui.get_io().want_capture_keyboard:
        return

def on_mouse_press(x, y, button, modifiers):
    if imgui.get_io().want_capture_mouse:
        return
    ps.emitter_x=x
    ps.emitter_y=y
    ps.runfor()

def on_mouse_release(x, y, button, modifiers):
    if imgui.get_io().want_capture_mouse:
        return
    pass

def on_mouse_motion(x, y, dx, dy):
    if imgui.get_io().want_capture_mouse:
        return
    pass

def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    if imgui.get_io().want_capture_mouse:
        return

def on_resize(width,height):
    pass

def update(dt):
    ## using onkeypress does not enable key repeats
    ## we need to use another handler
    ## it needs to be pushed each time
    if int(pyglet.__version__[0])<2.0:
        gl.glMatrixMode(pyglet.gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(0.0, 1024.0, 0.0,768.0, -1.0, 1.0)
        gl.glMatrixMode(pyglet.gl.GL_MODELVIEW)
        gl.glLoadIdentity()
    game_window.push_handlers(keys)
    ps.advance_system(dt)

game_window.push_handlers(on_mouse_motion,
            on_key_press,
            on_key_release,
            #on_text,
            on_mouse_drag,
            on_mouse_press,
            on_mouse_release,
            #on_mouse_scroll,
            on_resize,
            )
models=[]
for ext in["*.pex","*.json"]:
    #models=[str(s.name) for s in pathlib.Path("resource/particles/").glob("*.pex")]
    models.extend([str(s.name) for s in pathlib.Path("resource/particles/").glob(ext)])
models=sorted(models)
model=0
ps=ParticleSystem("resource/particles/"+models[0])
#ps=ParticleSystem("resource/particles/fire.json")
ps.runfor()
ps.emitter_x=512
ps.emitter_y=360
pyglet.clock.schedule_interval(update, 0.016)
pyglet.app.run()
impl.shutdown()
