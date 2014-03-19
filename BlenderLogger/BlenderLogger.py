#The Sign Language Synthesis and Interaction Research Tools
#    Copyright (C) 2014  Fabrizio Nunnari, Alexis Heloir, DFKI
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

#
# This script is logging in real time all the events generated by Blender.
# It can log events only into the console or also into a text buffer of the Blender scene.
# It can optionally run a timer loggin the position, rotation, and scale of the active object.
#
# Press alt+fhift+c to activate. Same to end.
#

# Modal listening method taken from Screencast Key Status Tool
# http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/3D_interaction/Screencast_Key_Status_Tool

import bpy
import bgl
import blf

from bpy.props import * # for properties


import time

from math import pi


LOG_PREFIX = "LOG"



# properties used by the script
def init_properties():
    # Runstate initially always set to False
    # note: it is not stored in the Scene, but in window manager:
    bpy.types.WindowManager.logging = bpy.props.BoolProperty(default=False)


# removal of properties when script is disabled
def clear_properties():
    if(bpy.context.window_manager.logging):
        del(bpy.context.window_manager.logging)



def draw_callback_px(self, context):
    #print("callback_px")
    # Maybe print a nice red circle in some corner

    bgl.glPushAttrib(bgl.GL_CLIENT_ALL_ATTRIB_BITS)

    FONT_RGBA = (0.8, 0.1, 0.1, 0.5)
    bgl.glColor4f(*FONT_RGBA)

    font_size = 11
    DPI = 72

    blf.size(0, font_size, DPI)
    msg = "Logging..."
    
    msg_w,msg_h = blf.dimensions(0, msg)

    pos_x = context.region.width - msg_w
    pos_y = font_size / 2
    blf.position(0, pos_x, pos_y, 0)
    #blf.position(0, 10, 10, 0)

    blf.draw(0, msg)

    bgl.glPopAttrib()

    pass
    
    
#KEYS_TO_LOG = ['G','R', 'LEFTMOUSE', 'ESC', 'RIGHTMOUSE']

class LoggerOn(bpy.types.Operator):
    bl_idname = "view3d.logger_on"
    bl_label = "Switch key logger on (if not already)"
    bl_description = "log all events into an internal text buffer"
    
    useInternalBuffer = BoolProperty(name="Write to internal buffer", description="If true, the log will be written as well in an internal Text buffer. A new text buffer will be created at each logging activity start.", default=False)

    logActiveObjectTransform = BoolProperty(name="Log loc/rot/scale of the active object", description="If true, the log will include a sampling of the current active object location x y z, rotation_quaternion w x y z and scale x y z.", default=False)

    def invoke(self, context, event):
        return self.execute(context)
        
    def execute(self, context):
        print("Invoked LoggerOn")

        if context.window_manager.logging is False:
            bpy.ops.view3d.logger_switch(useInternalBuffer=self.useInternalBuffer, logActiveObjectTransform=self.logActiveObjectTransform)

        return {'FINISHED'}


class LoggerOff(bpy.types.Operator):
    bl_idname = "view3d.logger_off"
    bl_label = "Switch key logger off (if not already)"
    bl_description = "Stop logging all events into an internal text buffer"

    def invoke(self, context, event):
        return self.execute(context)
        
    def execute(self, context):
        print("Invoked LoggerOff")

        if context.window_manager.logging is True:
            bpy.ops.view3d.logger_switch()

        return {'FINISHED'}
        

class LoggerMessage(bpy.types.Operator):
    bl_idname = "view3d.logger_message"
    bl_label = "Log Message"
    bl_description = "Write a custom message to the current log, if active, otherwise nothing happens"
    
    message = StringProperty(name="message", description="The message to write in the log")
    
    def invoke(self, context, event):
        return self.execute(context)
    
    def execute(self, context):
        #print("Invoked LoggerOff")
        
        log(self.message)
        
        return {'FINISHED'}




def getActiveInstance():
    return SwitchLoggerStatus.s_active_instance


def log(message):
    if(SwitchLoggerStatus.s_active_instance != None):
        SwitchLoggerStatus.s_active_instance.log(message)


class SwitchLoggerStatus(bpy.types.Operator):
    bl_idname = "view3d.logger_switch"
    bl_label = "Switch key logger"
    bl_description = "log all events into an internal text buffer"
    
    useInternalBuffer = BoolProperty(name="Write to internal buffer", description="If true, the log will be written as well in an internal Text buffer. A new text buffer will be created at each logging activity start.", default=False)
    
    logActiveObjectTransform = BoolProperty(name="Log loc/rot/scale of the active object", description="If true, the log will include a sampling of the current active object location x y z, rotation_quaternion w x y z and scale x y z.", default=False)

    # Reference to a bpy.data.texts entry, where log is eventually written
    text_buffer = None

    _handle = None
    _timer = None

    @staticmethod
    def handle_add(self, context):
        SwitchLoggerStatus._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, (self, context), 'WINDOW', 'POST_PIXEL')
        SwitchLoggerStatus._timer = context.window_manager.event_timer_add(0.04, context.window)

    @staticmethod
    def handle_remove(context):
        if SwitchLoggerStatus._handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(SwitchLoggerStatus._handle, 'WINDOW')
            SwitchLoggerStatus._handle = None

        if SwitchLoggerStatus._timer is not None:
            context.window_manager.event_timer_remove(SwitchLoggerStatus._timer)
            SwitchLoggerStatus._timer = None


    s_active_instance = None

        

    def invoke(self, context, event):
        return self.execute(context)
        
    def execute(self, context):
        print("Invoked SwitchLoggerStatus")

        if context.window_manager.logging is False:
            # operator is called for the first time, start everything
            print("Logger first call")
            
            if(self.useInternalBuffer):
                buffer_name = "LOG-" + time.ctime()
                self.text_buffer = bpy.data.texts.new(buffer_name)
            
            SwitchLoggerStatus.s_active_instance = self
            
            context.window_manager.logging = True
            SwitchLoggerStatus.handle_add(self, context)
            context.window_manager.modal_handler_add(self)
            
                        
            if context.area:
                context.area.tag_redraw()

            return {'RUNNING_MODAL'}

        else:
            # operator is called again, stop displaying
            print("Logger stop")
            context.window_manager.logging = False
            return {'CANCELLED'}


    def modal(self, context, event):
        #if context.area:
        #    context.area.tag_redraw()

        if not context.window_manager.logging:
            # stop script
            SwitchLoggerStatus.handle_remove(context)
            if context.area:
                context.area.tag_redraw()
                
            SwitchLoggerStatus.s_active_instance = None

            #return {'CANCELLED'}
            return {'FINISHED'}

        if event.type == 'MOUSEMOVE':
            return {'PASS_THROUGH'}
            

        if event.type == 'TIMER':
            #experimentsColorHandler()
            # Log active object position
            if(self.logActiveObjectTransform):
                self.logActiveObject(context)
            return {'PASS_THROUGH'}

        if event.type == 'TIMER_REPORT':
            return {'PASS_THROUGH'}

        self.logEvent(event)

        return {'PASS_THROUGH'}


    def cancel(self, context):
        if context.window_manager.logger:
            SwitchLoggerStatus.handle_remove(context)
            #context.window_manager.screencast_keys_keys = False
        return {'CANCELLED'}



    def logEvent(self, event):
        """Print out the log prefix, the start/end marker, the key and the timestamp"""
        msg = LOG_PREFIX +"_EVENT "+ str(time.time()) +" "+ event.type +" "+ event.value 
        print(msg)
        if(self.useInternalBuffer):
            self.text_buffer.write(msg)
            self.text_buffer.write("\n")

    def logActiveObject(self, context):
        ao = context.active_object
        if(ao):
            lx,ly,lz = ao.location
            qw,qx,qy,qz = ao.rotation_quaternion
            sx,sy,sz = ao.scale
            string_values = [str(x) for x in (lx,lz,lz,qw,qx,qy,qz,sx,sy,sz)]
            msg = LOG_PREFIX +"_ACTIVE_OBJ "+ str(time.time()) +" "+ ao.name +" "+ (" ".join(string_values))
            print(msg)
            if(self.useInternalBuffer):
                self.text_buffer.write(msg)
                self.text_buffer.write("\n")



    def log(self, msg):
        msg = LOG_PREFIX +"_CUSTOM "+ str(time.time()) +" "+ msg
        print(msg)
        if(self.useInternalBuffer):
            self.text_buffer.write(msg)
            self.text_buffer.write("\n")
        

# store keymaps here to access after registration
addon_keymaps = []


def register():
    print("Registering Logger classes")
    init_properties()
    
    bpy.utils.register_class(SwitchLoggerStatus)
    bpy.utils.register_class(LoggerOn)
    bpy.utils.register_class(LoggerOff)
    bpy.utils.register_class(LoggerMessage)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new('view3d.logger_switch', 'L', 'PRESS', shift=True, alt=True)
        kmi.properties.useInternalBuffer = True
        addon_keymaps.append((km, kmi))


def unregister():
    print("Unregistering Logger classes")

    # in case its enabled
    SwitchLoggerStatus.handle_remove(bpy.context)

    bpy.utils.unregister_class(SwitchLoggerStatus)
    bpy.utils.unregister_class(LoggerOn)
    bpy.utils.unregister_class(LoggerOff)
    bpy.utils.unregister_class(LoggerMessage)

    # handle the keymap
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    clear_properties()


if __name__ == "__main__":
    register()
