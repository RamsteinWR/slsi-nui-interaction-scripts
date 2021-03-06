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
#
#

import bpy
import bgl
import blf
import mathutils

import math
import time

from LeapNUI.LeapReceiver import LeapReceiver
from LeapNUI.LeapReceiver import HandSelector
from LeapNUI.LeapReceiver import HandMotionAnalyzer
from LeapNUI.LeapModalController import LeapModal
from LeapNUI import Icons



        
#
#
#

#
# Some constants carefully fine-tuned by hand.
#

class LeapInteractionConstants:
    
    EDIT_ON_THRESHOLD_SECS = 0.5 #0.1
    EDIT_OFF_THRESHOLD_SECS = 1.0 #0.5
    EDIT_STABILITY_THRESHOLD = 10 #20
    EDIT_ON_MAX_FINGERS = 2

    DROP_OFF_RADIUS_THRESHOLD_MM = 1
    
    FAST_MOVEMENT_SPEED = 1000
    FAST_MOVEMENT_LOOKBACK_SECS = 0.1

    PINCH_FAST_MOVEMENT_SPEED = 100


    CARRIAGE_RETURN_TOTAL_LOOKBACK_SECS = 0.4
    CARRIAGE_RETURN_CHANGE_LOOKBACK_SECS = 0.2
    CARRIAGE_RETURN_MIN_BACKSPEED = 100


    GRAB_MODE_GRASP = "grasp"
    GRAB_MODE_TIMED = "timed"
    GRAB_MODE_PINCH = "pinch"


    #Used by grabStrength
    GRAB_STRENGTH_ACTIVATION_THRESHOLD = 1.0
    GRAB_STRENGTH_DEACTIVATION_THRESHOLD = 0.05

    PINCH_STRENGTH_ACTIVATION_THRESHOLD = 0.95
    PINCH_STRENGTH_DEACTIVATION_THRESHOLD = 0.2

    

    # def __init__(self):
    #     self.tracking = False
        
    #     self.last_drop_pos = None
        
    #     self.hand_changed = False
        
    
    # def isTracking(self):
    #     return self.tracking
    
    # def setTracking(self,b):
    #     self.tracking = b

    # def clearLastDrop():
    #     self.last_drop_pos = None
        
        
#
# This class defines the listener for the Leap Motion.
# Its method is invoked each time a new Leap Information is received.
# Essentially, its contains all the logic to start the interaction and run the LeapController
#
class LeapDictListener:
    
    def __init__(self):
    
        self.hand_selector = HandSelector()

        self.hand_motion_analyzer = HandMotionAnalyzer()
    
        self.tracking_start = -1
        
        self.last_hand_id = None
        
        self.last_dict_received = None
    
        # end __init__
        
    def getHandId(self):
        """Returns the ID of the last hand detected as valid for motion.
        Or None if no hand is detected."""
        
        return self.last_hand_id
    
    def resetHandId(self):
        self.last_hand_id = None
    
    def getLeapDict(self):
        return self.last_dict_received
    
     
    
    def newDictReceived(self, leap_dict):
    
        self.last_dict_received = leap_dict
    

        li = bpy.context.window_manager.leap_info
        grab_mode = bpy.context.window_manager.leap_keyboardless_grab_mode
        #leap_logic = li.leap_logic
        
    
        li.hand_changed = False
        pinchStrength = 0
    
        hand = self.hand_selector.select(leap_dict)
        if(hand != None):
            #print("HHH ID "+str(hand["id"]))
            if(hand["id"] != self.last_hand_id):
                li.hand_changed = True
                self.hand_motion_analyzer.reset()
    
            self.hand_motion_analyzer.update(hand)

            grabStrength = hand["grabStrength"]
            #print("EXPLICIT UNGRASP ="+ str(li.explicitely_ungrasped))
            if(li.explicitely_ungrasped == False):
                if(grabStrength < LeapInteractionConstants.GRAB_STRENGTH_DEACTIVATION_THRESHOLD):
                    li.explicitely_ungrasped = True

            pinchStrength = hand["pinchStrength"]
            confidence = hand["confidence"]

    
        #
        # Memories for next cycle
        if(hand != None):
            self.last_hand_id = hand["id"]
        else:
            self.last_hand_id = None
            

        #print("gmode="+grab_mode+"\t"+str(leap_logic.EDIT_ON_THRESHOLD_SECS))
    
        #
        # Handle tracking condition    
        if(li.isTracking() == True):
            #print("t")
            # Deactivatino logic is in the LeapManipulator Operator
            pass
                   
        if(li.isTracking() == False):
            if(hand != None):
                #active_time = hand["timeVisible"]
                #print(str(hand["id"]) + ": " + str(active_time))
                
                distant_from_last_drop = True
                if(li.last_drop_pos!=None):
                    curr_pos = mathutils.Vector(hand["palmPosition"])
                    dist = (curr_pos - li.last_drop_pos).length
                
                    distant_from_last_drop = dist > LeapInteractionConstants.DROP_OFF_RADIUS_THRESHOLD_MM
                    #print("DISTANT ENOUGH? " + str(dist) + "\t" + str(distant_from_last_drop))
        
                #n_fingers = HandMotionAnalyzer.countFingers(hand_id=hand["id"], leap_dict=leap_dict)

                palm_vel_xyz = hand["palmVelocity"]
                palm_vel_vect = mathutils.Vector(palm_vel_xyz)
                palm_vel = palm_vel_vect.length


                #fm = li.leap_listener.hand_motion_analyzer.handFastMovement(LeapInteractionConstants.FAST_MOVEMENT_SPEED, LeapInteractionConstants.FAST_MOVEMENT_LOOKBACK_SECS)
                #print("Palm Velocity="+str(palm_vel)+" (threshold="+str(LeapInteractionConstants.PINCH_FAST_MOVEMENT_SPEED))

                #print("pinchStrength="+str(pinchStrength)+"\tconf="+str(confidence))
            
                # Activate tracking!!!
                #print("hand age="+str(self.hand_motion_analyzer.handAge()))
                if( (grab_mode == LeapInteractionConstants.GRAB_MODE_TIMED
                    and self.hand_motion_analyzer.handAge()>LeapInteractionConstants.EDIT_ON_THRESHOLD_SECS
                    and self.hand_motion_analyzer.isHandStable(LeapInteractionConstants.EDIT_ON_THRESHOLD_SECS, LeapInteractionConstants.EDIT_STABILITY_THRESHOLD)
                    and distant_from_last_drop==True
                    )
                    or
                    (
                    grab_mode == LeapInteractionConstants.GRAB_MODE_GRASP and
                    grabStrength >= LeapInteractionConstants.GRAB_STRENGTH_ACTIVATION_THRESHOLD and
                    li.explicitely_ungrasped
                    )
                    or
                    (
                    grab_mode == LeapInteractionConstants.GRAB_MODE_PINCH and
                    pinchStrength >= (LeapInteractionConstants.PINCH_STRENGTH_ACTIVATION_THRESHOLD * confidence)
                    )
                    ):


                    if(palm_vel <= LeapInteractionConstants.PINCH_FAST_MOVEMENT_SPEED):


                        #print(str(self.hand_motion_analyzer.handAge()) + " ... ")
                        li.setTracking(True)
                        if grab_mode == LeapInteractionConstants.GRAB_MODE_TIMED:
                            reason = "Stable"
                        elif grab_mode == LeapInteractionConstants.GRAB_MODE_GRASP:
                            reason = "Grabbing"
                        elif grab_mode == LeapInteractionConstants.GRAB_MODE_PINCH:
                            reason = "Pinching"
                        else:
                            reason = "Unknown!!!"
                        li.logMessage("ON Hand "+reason)
                        print("Tracking ACTIVATED")

                        li.explicitely_ungrasped = False

                        self.tracking_start = time.time()
        
                        # Run LeapModal operator
                        # @see http://www.blender.org/documentation/blender_python_api_2_68_release/bpy.ops.html
                        li.leap_listener.hand_motion_analyzer.reset()

                        tr = False
                        rot = False
                        op = bpy.context.window_manager.leap_keyboardless_grasp_operation
                        if(op == "tr"):
                            tr = True
                            rot = False
                        elif(op == "rot"):
                            tr = False
                            rot = True
                        elif(op == "tr-rot"):
                            tr = True
                            rot = True

                        bpy.ops.object.leap_modal(isRotating=rot, isTranslating=tr)
                    else:
                        print("Not pinched: too fast.")
                        print("Palm Velocity="+str(palm_vel)+" (threshold="+str(LeapInteractionConstants.PINCH_FAST_MOVEMENT_SPEED)+")")
                    
            else:
                #assert (self.tracking == False and hand==None)
                
                # We reset the location of the last stable position
                if( grab_mode == LeapInteractionConstants.GRAB_MODE_TIMED ):
                    if(li.last_drop_pos != None):
                        print("Clearing last drop position")
                        li.last_drop_pos = None
                pass
        
        
        pass # end newDictReceived
    
#
# This class defines the listener for the LeapReceiver.
# Its method is invoked at each frame received by the Leap.
# Essentially, this class contains the logic to DE-activate a control and turn off the LeapOperator.
#
class KeyboardLessLogicModalListener:
    
    tracking_start = None

    def cancelled(self, leap_modal, context):
        print("listening CANCELLED")
        li = context.window_manager.leap_info
        li.setTracking(False)
        #self.tracking_start = None
        li.leap_listener.resetHandId()
        li.last_drop_pos = None
        leap_modal.obj_translator.setScale(1.0)
        pass


    def finished(self, leap_modal, context):
        print("listening FINISHED")
        li = context.window_manager.leap_info
        li.setTracking(False)
        #self.tracking_start = None
        li.leap_listener.resetHandId()
        li.last_drop_pos = None
        leap_modal.obj_translator.setScale(1.0)
        pass
    
    def controllersUpdated(self, leap_modal, context):
        li = context.window_manager.leap_info
        #assert(li!=None) # otherwise the command wouldn't have started
        assert (li.isTracking() == True)
    
        now = time.time()
        if(self.tracking_start == None):
            self.tracking_start = now

        tracking_time = now - self.tracking_start

        leap_dict = li.leap_listener.getLeapDict()
        hand_id = li.leap_listener.getHandId()
        hand = li.leap_listener.hand_selector.getHandFromId(hand_id, leap_dict)

        
        #if(hand == None or hand_changed):
        if(hand_id == None or li.hand_changed):
            # Hand out of sight
            # or hand changed: DEACTIVATE TRACKING
            li.setTracking(False)
            self.tracking_start = None
            #li.leap_listener.resetHandId()
            li.last_drop_pos = None
            reason = "Unknown"
            if(hand_id == None): reason = "lost"
            elif(li.hand_changed) : reason = "changed"
            li.logMessage("OFF Hand " + reason)
            print("Tracking DEACTIVATED (hand " + reason + ")")
            return {'FINISHED'}

        else:
            grab_mode = bpy.context.window_manager.leap_keyboardless_grab_mode
            
            #
            # if "HAND REMOVED"
            if(grab_mode == LeapInteractionConstants.GRAB_MODE_TIMED
                and li.leap_listener.hand_motion_analyzer.handFastMovement(LeapInteractionConstants.FAST_MOVEMENT_SPEED, LeapInteractionConstants.FAST_MOVEMENT_LOOKBACK_SECS)
                ):
                # put the object in previous stable position
                x,y,z = li.leap_listener.hand_motion_analyzer.getStablePosition()

                leap_modal.obj_translator.setTargetPositionHandSpace(x,y,z)
                # switch tracking to deactiveted
                li.setTracking(False)
                self.tracking_start = None
                li.leap_listener.resetHandId()
                li.last_drop_pos = None
                li.logMessage("OFF Fast Movement")
                print("Tracking DEACTIVATED (Hand fast movement)")
                return {'FINISHED'}

        
            #
            # handle "CARRAGE RETURN"
            if(grab_mode == LeapInteractionConstants.GRAB_MODE_TIMED
                and li.leap_listener.hand_motion_analyzer.changeOfDirection(
                    LeapInteractionConstants.CARRIAGE_RETURN_CHANGE_LOOKBACK_SECS,
                    LeapInteractionConstants.CARRIAGE_RETURN_TOTAL_LOOKBACK_SECS,
                    LeapInteractionConstants.CARRIAGE_RETURN_MIN_BACKSPEED)
                ):
                li.setTracking(False)
                self.tracking_start = None
                li.leap_listener.resetHandId()
                li.last_drop_pos = None
                li.logMessage("OFF Change of Direction")
                print("Tracking DEACTIVATED (Change of direction)")
                return {'FINISHED'}


            #
            # if "HAND IS STABLE"
            #print("stable="+str((li.leap_listener.hand_motion_analyzer.isHandStable(leap_logic.EDIT_OFF_THRESHOLD_SECS, leap_logic.EDIT_STABILITY_THRESHOLD))) + "\ttracinktime="+str(tracking_time))
            if(grab_mode == LeapInteractionConstants.GRAB_MODE_TIMED
                and li.leap_listener.hand_motion_analyzer.isHandStable(LeapInteractionConstants.EDIT_OFF_THRESHOLD_SECS, LeapInteractionConstants.EDIT_STABILITY_THRESHOLD)
                and tracking_time>LeapInteractionConstants.EDIT_OFF_THRESHOLD_SECS
                ):
                li.setTracking(False)
                self.tracking_start = None
                li.leap_listener.resetHandId()
                li.last_drop_pos = mathutils.Vector(hand["palmPosition"])
                li.leap_listener.hand_motion_analyzer.reset()
                li.logMessage("OFF Hand Stable")
                print("Tracking DEACTIVATED (Hand stable)")
                return {'FINISHED'}



            grabStrength = hand["grabStrength"]
            #print("GS="+str(grabStrength))

            # Available only since protocol v6
            pinchStrength = hand["pinchStrength"]
            confidence = hand["confidence"]

            #thr = (LeapInteractionConstants.PINCH_STRENGTH_DEACTIVATION_THRESHOLD * confidence)
            #print("Confidence "+str(confidence)+"\tpinchStr "+ str(pinchStrength) +"\tDeactivation thr="+str(thr))

            #
            # Use pinch strength to modulate translation sensibility
            #
            # Available only since protocol v6
            if(grab_mode == LeapInteractionConstants.GRAB_MODE_PINCH):
                # When pinch is at activation threshold, we want scale at 1. When pinch is at deactivation threshold, we want scale at 0.
                # assert 0 <= pinchStrength <= 1
                scale = (pinchStrength - LeapInteractionConstants.PINCH_STRENGTH_DEACTIVATION_THRESHOLD) / (LeapInteractionConstants.PINCH_STRENGTH_ACTIVATION_THRESHOLD - LeapInteractionConstants.PINCH_STRENGTH_DEACTIVATION_THRESHOLD)
                #print("PinchStr="+str(pinchStrength)+"\tSetting translation scale to "+str(scale))
                leap_modal.obj_translator.setScale(scale)
            else:
                leap_modal.obj_translator.setScale(1.0)

                
            #
            # if "FINGERS OPENED"
            if( (grab_mode == LeapInteractionConstants.GRAB_MODE_GRASP and
                grabStrength <= LeapInteractionConstants.GRAB_STRENGTH_DEACTIVATION_THRESHOLD
                )
                or
                (grab_mode == LeapInteractionConstants.GRAB_MODE_PINCH and
                pinchStrength <= (LeapInteractionConstants.PINCH_STRENGTH_DEACTIVATION_THRESHOLD * confidence)
                )
                ):
                li.setTracking(False)
                self.tracking_start = None
                li.leap_listener.resetHandId()
                li.last_drop_pos = mathutils.Vector(hand["palmPosition"])
                #op.hand_motion_analyzer.reset()
                if grab_mode == LeapInteractionConstants.GRAB_MODE_TIMED:
                    reason = "Stable"
                elif grab_mode == LeapInteractionConstants.GRAB_MODE_GRASP:
                    reason = "Ungrabbed"
                elif grab_mode == LeapInteractionConstants.GRAB_MODE_PINCH:
                    reason = "Unpinched"
                else:
                    reason = "Unknown!!!"

                li.logMessage("OFF "+reason)
                print("Tracking DEACTIVATED ("+reason+")")
                return {'FINISHED'}
                                
        
        pass # end (op.tracking==True && hand!=None)

        return None


#
#
#

class LeapInfo:
    """Support class to collect global shared data: the receiver thread, and the listener taking care of new incoming leap dictionaries.
    """

    MAX_LOG_MESSAGES = 10
    LOG_MESSAGE_MAX_LIFE_SECS = 3

    def __init__(self):
        self.leap_receiver = None
        self.leap_listener = None
        
        # Run-time info
        self.dict_last_id = -1
        self.tracking = False
        self.last_drop_pos = None
        self.hand_changed = False

        self.explicitely_ungrasped = False

        self.log_messages = []



    def isTracking(self):
        return self.tracking
    

    def setTracking(self,b):
        self.tracking = b


    def clearLastDrop():
        self.last_drop_pos = None

        
    def start(self):
        self.leap_receiver = LeapReceiver.getSingleton()
        self.leap_listener = LeapDictListener()

        self.dict_last_id = -1
        self.tracking = False        
        self.last_drop_pos = None


    def update(self):
        
        # Local copy (Should be protected, but is atomic enough)
        leap_dict = self.leap_receiver.leapDict
        
        #print("update called on "+str(self))
        #print(leap_dict)
        if(leap_dict == None):
            print("No Leap data yet...")
            return

        if(not "id" in leap_dict):
            print("No id in dict (must be version frame...)")
            return

        new_id = leap_dict["id"]
        # Check if the dictionary has been updated
        if(new_id > self.dict_last_id):
            #print("Old dict, skipping...")
            self.dict_last_id = new_id

            self.leap_listener.newDictReceived(leap_dict)
            
        # update log list
        now = time.time()
        if(len(self.log_messages) > 0):
            ins_time, msg = self.log_messages[0]  # insertion time of the oldest message
            msg_age = now - ins_time
            if(msg_age > self.LOG_MESSAGE_MAX_LIFE_SECS):
                self.log_messages.pop(0)
                if(bpy.context.area):
                    bpy.context.area.tag_redraw()


        
    def stop(self):
        if(self.leap_receiver != None):
            self.leap_receiver.releaseSingleton()
            self.leap_receiver = None


    def logMessage(self, msg):
        while(len(self.log_messages) > LeapInfo.MAX_LOG_MESSAGES):
            self.log_messages.pop(0)
        self.log_messages.append((time.time(),msg))

#
#
#

class KeyboardlessControlOn(bpy.types.Operator):
    bl_idname = "wm.leap_nui_keyboardless_control_on"
    bl_label = "Keyboardless Daemon On"
    bl_description = "Activate the modal operator enabling Keyboardless interaction"

    def invoke(self, context, event):
        return self.execute(context)

    def execute(self, context):
        if (context.window_manager.leap_nui_keyboardless_active == False):
            bpy.ops.wm.leap_nui_keyboardless_control_switch()

        return {'FINISHED'}


#
#
#

class KeyboardlessControlOff(bpy.types.Operator):
    bl_idname = "wm.leap_nui_keyboardless_control_off"
    bl_label = "Keyboardless Daemon Off"
    bl_description = "Deactivate the modal operator enabling Keyboardless interaction"
    
    def invoke(self, context, event):
        return self.execute(context)
    
    def execute(self, context):
        if (context.window_manager.leap_nui_keyboardless_active == True):
            bpy.ops.wm.leap_nui_keyboardless_control_switch()
        
        return {'FINISHED'}


#
#
#


class KeyboardlessControlSwitch(bpy.types.Operator):
    bl_idname = "wm.leap_nui_keyboardless_control_switch"
    bl_label = "Leap Daemon Switch"
    bl_description = "De/Activate reception of Leap Motion data into Blender"
    
    ACTIVATION_KEY = 'K'    # characters in upcase, please.

    _draw_handle = None

    _time_handle = None
    

    @staticmethod
    def handle_add(self, context):
        KeyboardlessControlSwitch._draw_handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, (self, context), 'WINDOW', 'POST_PIXEL')
        KeyboardlessControlSwitch._time_handle = context.window_manager.event_timer_add(0.025, context.window)
        if(bpy.context.area):
            bpy.context.area.tag_redraw()

    @staticmethod
    def handle_remove(context):
        if KeyboardlessControlSwitch._draw_handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(KeyboardlessControlSwitch._draw_handle, 'WINDOW')
        KeyboardlessControlSwitch._draw_handle = None
        if(bpy.context.area):
            bpy.context.area.tag_redraw()


    _leap_modal_listener = None


    REDRAW_MAX_DELAY = 0.1
    last_redraw = 0


    def invoke(self, context, event):
        return self.execute(context)

    def execute(self, context):
        print(str(self.__class__)+ " invoked on area type " + context.area.type)


        if (context.window_manager.leap_nui_keyboardless_active == False):
            #
            # ACTIVATION CALL
            #
            print("KeyboardlessControlSwitch activating...")

            KeyboardlessControlSwitch.handle_add(self, context)            
            context.window_manager.leap_info.start()
            
            context.window_manager.modal_handler_add(self)
            
            KeyboardlessControlSwitch._leap_modal_listener = KeyboardLessLogicModalListener()
            LeapModal.modalCallbacks.append(KeyboardlessControlSwitch._leap_modal_listener)
            
            KeyboardlessControlSwitch._terminate = False

            context.window_manager.leap_nui_keyboardless_active = True

            return {'RUNNING_MODAL'}

        else:
            print("KeyboardlessControlSwitch asking termination...")
            # The command was already running. Flag to finish it at next modal call
            context.window_manager.leap_nui_keyboardless_active = False
            # and finish this instance
            return {'FINISHED'}
        
        
    def modal(self, context, event):
        
#        print(event.type
#            +"\t"+str(context.window_manager.leap_info.isActive())
#            +"\t"+str(LeapDaemonSwitch._terminate))
        if(not event.type == 'TIMER'):
            return {'PASS_THROUGH'}

        if(context.area):
            now = time.time()
            redraw_age = now - self.last_redraw
            if(redraw_age > KeyboardlessControlSwitch.REDRAW_MAX_DELAY):
                #print("Force redraw")
                context.area.tag_redraw()
                self.last_redraw = now


        
        if(context.window_manager.leap_nui_keyboardless_active == False):
            print("LeapDaemonSwitch stopping...")

            LeapModal.modalCallbacks.remove(KeyboardlessControlSwitch._leap_modal_listener)
            KeyboardlessControlSwitch._leap_modal_listener = None

            context.window_manager.leap_info.stop()

            KeyboardlessControlSwitch.handle_remove(context)
                        
            return {'FINISHED'}
            
        else:
            context.window_manager.leap_info.update()
            return {'PASS_THROUGH'}
        
        return {'PASS_THROUGH'}


    def cancel(self, context):
        if context.window_manager.leap_nui_keyboardless_active:
            KeyboardlessControlSwitch.handle_remove(context)
            context.window_manager.leap_info.stop()
            KeyboardlessControlSwitch._terminate = False
        return {'CANCELLED'}



#
#
#

def draw_callback_px(self, context):
    wm = context.window_manager
    r=0.8
    g=0.1
    b=0.2
    

    if(context.window_manager.leap_nui_keyboardless_active):
        #print("Draw Callback True")
        # draw text in the 3D View
        bgl.glPushClientAttrib(bgl.GL_CURRENT_BIT|bgl.GL_ENABLE_BIT)
        
        blf.size(0, 12, 72)
        blf.position(0, 10, 10, 0)
        bgl.glColor4f(r, g, b, 0.7)
        blf.blur(0, 1)
        # shadow?
        blf.enable(0, blf.SHADOW)
        blf.shadow_offset(0, 1, -1)
        blf.shadow(0, 5, 0.0, 0.0, 0.0, 0.8)
    
        blf.draw(0, "Leap Active!")
        
        bgl.glPopClientAttrib()
    else:
        #print("Draw Callback False")
        pass


    #
    # Draw the LeapInfo log messages
    font_size = 24
    messages = wm.leap_info.log_messages
    n_messages = len(messages)
    log_y_size = LeapInfo.MAX_LOG_MESSAGES * font_size
    #pos_y = context.region.height - ((context.region.height - log_y_size) / 2)
    pos_y = ((context.region.height - log_y_size) / 2)
    pos_x = 0
    bgl.glPushClientAttrib(bgl.GL_CURRENT_BIT|bgl.GL_ENABLE_BIT)
    blf.size(0, font_size, 72)
    bgl.glColor4f(r, g, b, 0.7)

    for time,msg in reversed(messages):
        blf.position(0, pos_x, pos_y, 0)    
        blf.draw(0, msg)
        pos_y += font_size

    bgl.glPopClientAttrib()


    #
    # Draw icon if the hand is visible to the Leap
    if(wm.leap_info.leap_listener.getHandId() == None):     # NO HAND
        pass
    else:
        pos_x = context.region.width - (Icons.ICON_SIZE * 1.5)
        pos_y = (Icons.ICON_SIZE / 2)

        if(wm.leap_info.isTracking()):           # GREEN HAND
            Icons.drawIcon("5-spreadfingers-icon-green.png", pos_x, pos_y)
            pass
        else:                                               # RED HAND
            Icons.drawIcon("5-spreadfingers-icon-red.png", pos_x, pos_y)
            pass


#
#
#

# Format: [(identifier, name, description, icon, number), ...] 
# Only the first 3 elements are mandatory
LEAP_ACTIVATION_MODES = [
    (LeapInteractionConstants.GRAB_MODE_TIMED, "Timed", "Control acticated and deativate by stability timeout"),
    (LeapInteractionConstants.GRAB_MODE_GRASP, "Grasp", "Control (de-)activated by grasping with the fingers"),
    (LeapInteractionConstants.GRAB_MODE_PINCH, "Pinch", "Control (de-)activated by pinching with the fingers (only with protocol v6)")
]

LEAP_OPERATION_MODES = [
    ("tr", "Translate", "Activate Translation"),
    ("rot", "Rotate", "Activate Rotation"),
    ("tr-rot", "Tr & Rot", "Activate Translation and Rotation")
]

# store keymaps here to access after registration
addon_keymaps = []


def register():
    # Init global properties

    # Runstate initially always set to False
    # note: it is not stored in the Scene, but in window manager:
    bpy.types.WindowManager.leap_info = LeapInfo()
    
    # Register properties
    bpy.types.WindowManager.leap_keyboardless_grab_mode = bpy.props.EnumProperty(items=LEAP_ACTIVATION_MODES, name="Grab Mode", description="The way the Leap Control is de(activated): by hand stability, full hand grabbing, or pinching.")
    #bpy.types.WindowManager.leap_keyboardless_grasp_uses_grabStrength = bpy.props.BoolProperty(name="Grasp use grabStrength", description="What to use for grabbing. The finger count or the grabStrength attribute of new protocol v6.")
    bpy.types.WindowManager.leap_keyboardless_grasp_operation = bpy.props.EnumProperty(items=LEAP_OPERATION_MODES, name="Operation", description="Whether Keyboardless activates only translation, only rotation, or both.")

    
    # Register classes    
    bpy.utils.register_class(KeyboardlessControlSwitch)
    bpy.utils.register_class(KeyboardlessControlOn)
    bpy.utils.register_class(KeyboardlessControlOff)

    # Init key shortcuts control
    
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='Window', space_type='EMPTY', region_type='WINDOW')
        kmi = km.keymap_items.new(KeyboardlessControlSwitch.bl_idname, KeyboardlessControlSwitch.ACTIVATION_KEY, 'PRESS', shift=True, alt=True)
        addon_keymaps.append((km, kmi))

    print("Registered")


def unregister():
    
    # in case its enabled
    #GlobalTimedCallbackOperator.handle_remove(bpy.context)

    bpy.utils.unregister_class(KeyboardlessControlOff)
    bpy.utils.unregister_class(KeyboardlessControlOn)
    bpy.utils.unregister_class(KeyboardlessControlSwitch)


    # Unregister properties
    del bpy.context.window_manager.leap_keyboardless_grab_mode
    del bpy.context.window_manager.leap_keyboardless_grasp_operation
    

    # handle the keymap
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    # removal of properties when script is disabled
    del bpy.context.window_manager.leap_info


    print("Unregistered")


if __name__ == "__main__":
    register()

