bl_info = {
    "name": "Circular Array",
    "author": "Gunduzhan Gunduz",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Circular Array",
    "description": "Creates circular arrays of objects",
    "category": "Object",
    "license": "GPL-3.0",
}

import bpy
import math
from mathutils import Vector, Matrix, Euler
import random
import os
import bpy.utils.previews
from bpy.types import Operator, Menu
from bpy.props import StringProperty, BoolProperty
from bl_operators.presets import AddPresetBase

class CircularArrayProperties(bpy.types.PropertyGroup):
    count: bpy.props.IntProperty(
        name="Count",
        description="Number of copies",
        default=6,
        min=2,
        max=360
    )
    radius: bpy.props.FloatProperty(
        name="Radius",
        description="Circle radius",
        default=2.0,
        min=0.0
    )
    rotation_offset: bpy.props.FloatProperty(
        name="Rotation Offset",
        description="Rotation offset in degrees",
        default=0.0,
        subtype='ANGLE'
    )
    vertical_offset: bpy.props.FloatProperty(
        name="Vertical Offset",
        description="Offset each object vertically",
        default=0.0,
        unit='LENGTH'
    )
    vertical_mode: bpy.props.EnumProperty(
        name="Vertical Mode",
        description="How vertical offset is applied",
        items=[
            ('SINGLE', "Single", "Same height for all objects"),
            ('INCREMENTAL', "Incremental", "Increase height for each object"),
            ('SPIRAL', "Spiral", "Create a spiral pattern"),
        ],
        default='SINGLE'
    )
    rotation_enable: bpy.props.BoolProperty(
        name="Custom Rotation",
        description="Enable custom rotation settings",
        default=False
    )
    rotation_initial: bpy.props.FloatVectorProperty(
        name="Initial Rotation",
        description="Starting rotation for objects (degrees)",
        default=(0.0, 0.0, 0.0),
        subtype='EULER',
        unit='ROTATION'
    )
    rotation_progressive: bpy.props.FloatVectorProperty(
        name="Progressive Rotation",
        description="Additional rotation for each object (degrees)",
        default=(0.0, 0.0, 0.0),
        subtype='EULER',
        unit='ROTATION'
    )
    parent_to_empty: bpy.props.BoolProperty(
        name="Parent to Center",
        description="Parent all objects to the center empty",
        default=True
    )
    use_selected: bpy.props.BoolProperty(
        name="Use All Selected",
        description="Create arrays from all selected objects",
        default=False
    )
    spacing_angle: bpy.props.FloatProperty(
        name="Object Spacing",
        description="Angular spacing between different objects (degrees)",
        default=0.0,
        subtype='ANGLE'
    )
    parent_mode: bpy.props.EnumProperty(
        name="Parent Mode",
        description="Choose parent type for array objects",
        items=[
            ('EMPTY', "Empty", "Create and parent to center empty"),
            ('OBJECT', "Object", "Parent to original object"),
            ('NONE', "None", "No parenting"),
        ],
        default='EMPTY'
    )
    spiral_revolutions: bpy.props.FloatProperty(
        name="Revolutions",
        description="Number of complete revolutions for the spiral",
        default=1.0,
        min=0.0,
        soft_max=10.0
    )
    spiral_direction: bpy.props.EnumProperty(
        name="Spiral Direction",
        description="Direction of the spiral",
        items=[
            ('UP', "Up", "Spiral goes upward"),
            ('DOWN', "Down", "Spiral goes downward"),
        ],
        default='UP'
    )
    use_random: bpy.props.BoolProperty(
        name="Use Randomization",
        description="Enable random variations",
        default=False
    )
    random_scale: bpy.props.FloatVectorProperty(
        name="Random Scale",
        description="Random scale variation range",
        default=(0.0, 0.0, 0.0),
        min=0.0,
        max=1.0,
        subtype='XYZ'
    )
    random_rotation: bpy.props.FloatVectorProperty(
        name="Random Rotation",
        description="Random rotation variation range (degrees)",
        default=(0.0, 0.0, 0.0),
        subtype='EULER',
        unit='ROTATION'
    )
    random_offset: bpy.props.FloatVectorProperty(
        name="Random Offset",
        description="Random position offset range",
        default=(0.0, 0.0, 0.0),
        subtype='TRANSLATION',
        unit='LENGTH'
    )
    random_seed: bpy.props.IntProperty(
        name="Random Seed",
        description="Seed for random variations",
        default=1,
        min=1
    )
    distribution_mode: bpy.props.EnumProperty(
        name="Distribution Mode",
        description="Choose how objects are distributed in space",
        items=[
            ('CIRCULAR', "Circular", "Distribute objects in a perfect circle (equal spacing)"),
            ('ELLIPTICAL', "Elliptical", "Distribute objects in an elliptical pattern (stretched circle)"),
            ('CURVE', "Follow Curve", "Distribute objects along a selected curve")
        ],
        default='CIRCULAR'
    )
    ellipse_ratio: bpy.props.FloatProperty(
        name="Ellipse Ratio",
        description="Ratio between width and height of ellipse (1.0 = circle, smaller values = more elliptical)",
        default=0.5,
        min=0.01,
        max=1.0,
        subtype='FACTOR'
    )
    ellipse_rotation: bpy.props.FloatProperty(
        name="Ellipse Rotation",
        description="Rotate the entire elliptical pattern (in degrees)",
        default=0.0,
        subtype='ANGLE'
    )
    curve_object: bpy.props.PointerProperty(
        name="Follow Curve",
        description="Distribute objects along this curve",
        type=bpy.types.Object,
        poll=lambda self, obj: obj and obj.type == 'CURVE'
    )
    follow_curve_rotation: bpy.props.BoolProperty(
        name="Follow Curve Rotation",
        description="Rotate objects to follow curve direction",
        default=True
    )
    curve_offset: bpy.props.FloatProperty(
        name="Curve Offset",
        description="Offset position along the curve",
        default=0.0,
        min=-1.0,
        max=1.0,
        subtype='FACTOR'
    )
    curve_offset_units: bpy.props.EnumProperty(
        name="Offset Units",
        description="Units for curve offset",
        items=[
            ('FACTOR', "Factor", "Offset as a factor (0-1)"),
            ('DISTANCE', "Distance", "Offset in world units"),
        ],
        default='FACTOR'
    )
    curve_offset_distance: bpy.props.FloatProperty(
        name="Offset Distance",
        description="Offset distance along curve",
        default=0.0,
        unit='LENGTH'
    )
    curve_up_axis: bpy.props.EnumProperty(
        name="Up Axis",
        description="Which axis to use as up direction",
        items=[
            ('Z', "Z Up", "Use Z axis as up"),
            ('Y', "Y Up", "Use Y axis as up"),
            ('X', "X Up", "Use X axis as up"),
            ('CUSTOM', "Custom", "Use custom up vector"),
        ],
        default='Z'
    )
    curve_up_vector: bpy.props.FloatVectorProperty(
        name="Custom Up Vector",
        description="Custom up vector for curve following",
        default=(0.0, 0.0, 1.0),
        subtype='DIRECTION'
    )
    source_offset: bpy.props.FloatVectorProperty(
        name="Source Offset",
        description="Offset distance for source object from center",
        default=(0.0, 0.0, 0.0),
        subtype='TRANSLATION'
    )

class OBJECT_OT_circular_array(bpy.types.Operator):
    bl_idname = "object.circular_array"
    bl_label = "Update Circular Array"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.circular_array_props
        active_obj = context.active_object
        selected_objects = context.selected_objects

        if not active_obj:
            self.report({'ERROR'}, "No active object")
            return {'CANCELLED'}

        # Find existing array and source object
        array_empty = None
        array_objects = []
        source_obj = None

        # Check if active object is an empty for an array
        if "Circular_Array_Center_" in active_obj.name:
            array_empty = active_obj
            array_objects = [obj for obj in array_empty.children]
            # Find source object (object at empty's location)
            for obj in array_objects:
                if (obj.location - array_empty.location).length < 0.0001:
                    source_obj = obj
                    break
            if not source_obj and array_objects:
                source_obj = array_objects[0]
            if source_obj:
                array_objects = [obj for obj in array_objects if obj != source_obj]
        # Check if active object is part of an array
        elif active_obj.parent and "Circular_Array_Center_" in active_obj.parent.name:
            # Empty-based array
            array_empty = active_obj.parent
            source_obj = active_obj
            array_objects = [obj for obj in array_empty.children if obj != source_obj]
        elif active_obj.children:
            # Object-based array (active object is the parent)
            source_obj = active_obj
            array_objects = [obj for obj in active_obj.children]
        else:
            source_obj = active_obj

        if not source_obj:
            self.report({'ERROR'}, "No valid source object found")
            return {'CANCELLED'}

        # Calculate positions
        positions = []
        rotations = []

        # Calculate array center (will be different from source location)
        array_center = source_obj.location.copy()

        # Calculate positions for all objects
        for i in range(props.count):
            angle = (2 * math.pi * i) / props.count
            offset_angle = math.radians(props.rotation_offset)
            total_angle = angle + offset_angle

            # Z değişkenini başlangıçta tanımla
            z = 0

            if props.distribution_mode == 'CURVE':
                if not props.curve_object:
                    self.report({'ERROR'}, "No curve object selected")
                    return {'CANCELLED'}

                try:
                    curve = props.curve_object
                    
                    # Check if curve has any splines
                    if not curve.data.splines:
                        self.report({'ERROR'}, "Selected curve has no splines")
                        return {'CANCELLED'}
                    
                    # Get curve length
                    curve_length = sum(spline.calc_length() for spline in curve.data.splines)
                    if curve_length == 0:
                        self.report({'ERROR'}, "Curve has zero length")
                        return {'CANCELLED'}

                    # Calculate factor along curve
                    if props.curve_offset_units == 'FACTOR':
                        factor = i / (props.count - 1) if props.count > 1 else 0
                        factor = (factor + props.curve_offset) % 1.0
                    else:  # DISTANCE
                        total_length = curve_length
                        base_distance = (i / (props.count - 1)) * total_length if props.count > 1 else 0
                        offset_distance = props.curve_offset_distance
                        final_distance = (base_distance + offset_distance) % total_length
                        factor = final_distance / total_length

                    # Evaluate curve point
                    pos, tangent = self.evaluate_curve_point(curve, curve.data.splines[0], factor)
                    positions.append(pos)

                    # Calculate rotation
                    if props.follow_curve_rotation:
                        # Get world up vector
                        if props.curve_up_axis == 'Z':
                            up = Vector((0, 0, 1))
                        elif props.curve_up_axis == 'Y':
                            up = Vector((0, 1, 0))
                        elif props.curve_up_axis == 'X':
                            up = Vector((1, 0, 0))
                        else:  # CUSTOM
                            up = props.curve_up_vector.normalized()

                        # Calculate rotation matrix
                        forward = tangent.normalized()
                        right = forward.cross(up)
                        if right.length < 0.001:
                            right = Vector((1, 0, 0))
                        right.normalize()
                        up = right.cross(forward)
                        
                        rot_mat = Matrix((right, forward, up)).to_4x4().transposed()
                        rot = rot_mat.to_euler()
                    else:
                        rot = source_obj.rotation_euler.copy()

                    rotations.append(rot)
                    continue

                except Exception as e:
                    self.report({'ERROR'}, f"Error processing curve: {str(e)}")
                    return {'CANCELLED'}

            elif props.distribution_mode == 'ELLIPTICAL':
                # Elliptical koordinatları hesapla
                a = props.radius  # Major axis
                b = props.radius * props.ellipse_ratio  # Minor axis
                
                # Temel pozisyonu hesapla
                x = a * math.cos(total_angle)
                y = b * math.sin(total_angle)
                
                # Ellipse rotasyonunu uygula
                if props.ellipse_rotation != 0:
                    rot_angle = math.radians(props.ellipse_rotation)
                    old_x = x
                    old_y = y
                    x = old_x * math.cos(rot_angle) - old_y * math.sin(rot_angle)
                    y = old_x * math.sin(rot_angle) + old_y * math.cos(rot_angle)
                
                # Z pozisyonunu hesapla
                if props.vertical_mode == 'INCREMENTAL':
                    z = props.vertical_offset * i
                elif props.vertical_mode == 'SPIRAL':
                    current_revolution = i / props.count * props.spiral_revolutions
                    z = props.vertical_offset * current_revolution
                    if props.spiral_direction == 'DOWN':
                        z = -z
                
                # Final pozisyonu hesapla
                pos = array_center + Vector((x, y, z))
                positions.append(pos)
                
                # Rotasyonu hesapla
                if i == 0:
                    rot = source_obj.rotation_euler.copy()
                else:
                    # Objelerin merkeze bakmasını sağla
                    tangent_angle = math.atan2(y, x)
                    rot = Euler((0, 0, tangent_angle + math.pi/2))
                    # Source object'in rotasyonunu ekle
                    rot.x += source_obj.rotation_euler.x
                    rot.y += source_obj.rotation_euler.y
                    rot.z += source_obj.rotation_euler.z
                
                rotations.append(rot)
                continue  # Diğer hesaplamaları atla

            # Default to circular distribution
            x = math.cos(angle) * props.radius
            y = math.sin(angle) * props.radius

            # Calculate vertical offset (only for non-curve modes)
            if props.distribution_mode != 'CURVE':
                if props.vertical_mode == 'SINGLE':
                    z = props.vertical_offset
                elif props.vertical_mode == 'INCREMENTAL':
                    z = props.vertical_offset * i
                elif props.vertical_mode == 'SPIRAL':
                    current_revolution = i / props.count * props.spiral_revolutions
                    z = props.vertical_offset * current_revolution
                    if props.spiral_direction == 'DOWN':
                        z = -z

            pos = source_obj.location + Vector((x, y, z))
            
            # Update rotation calculation in execute method (for non-curve modes)
            if props.distribution_mode != 'CURVE':
                # Calculate base rotation
                if props.distribution_mode == 'ELLIPTICAL':
                    # Calculate tangent direction for ellipse
                    tangent_angle = math.atan2(y, x)
                    if props.ellipse_rotation != 0:
                        tangent_angle += math.radians(props.ellipse_rotation * 2)
                    # Rotate objects to face outward from center
                    rot = Euler((0, 0, tangent_angle))
                else:  # CIRCULAR
                    # Keep original rotation for first object (source)
                    if i == 0:
                        rot = source_obj.rotation_euler.copy()
                    else:
                        # Calculate rotation based on position in circle
                        angle = math.atan2(y, x)
                        # Objects should face outward from center
                        rot = Euler((0, 0, angle))

                # Apply custom rotation if enabled
                if props.rotation_enable and i > 0:
                    # Add initial rotation
                    rot.x += math.radians(props.rotation_initial.x)
                    rot.y += math.radians(props.rotation_initial.y)
                    rot.z += math.radians(props.rotation_initial.z)
                    
                    # Add progressive rotation
                    rot.x += math.radians(props.rotation_progressive.x) * i
                    rot.y += math.radians(props.rotation_progressive.y) * i
                    rot.z += math.radians(props.rotation_progressive.z) * i

                # Add source object's base rotation for consistent orientation
                if i > 0:
                    rot.x += source_obj.rotation_euler.x
                    rot.y += source_obj.rotation_euler.y
                    rot.z += source_obj.rotation_euler.z

            positions.append(pos)
            rotations.append(rot)

        # Update or create objects
        created_objects = []
        created_objects.append(source_obj)  # First object is source, don't modify it

        # Update or create other objects
        for i in range(1, props.count):
            if i-1 < len(array_objects):
                obj = array_objects[i-1]
            else:
                obj = source_obj.copy()
                obj.data = source_obj.data
                context.scene.collection.objects.link(obj)
            
            # Update transform
            obj.location = positions[i]  # Use positions[i] directly
            obj.rotation_euler = rotations[i]
            created_objects.append(obj)

        # Remove extra objects
        for obj in array_objects[max(0, props.count-1):]:
            bpy.data.objects.remove(obj, do_unlink=True)

        # Handle parenting based on mode
        if props.parent_mode == 'EMPTY':
            if array_empty:
                empty = array_empty
            else:
                bpy.ops.object.empty_add(type='PLAIN_AXES', location=source_obj.location)
                empty = context.active_object
                empty.name = f"Circular_Array_Center_{source_obj.name}_{source_obj.as_pointer()}"

            # Update empty and source object locations
            empty.location = source_obj.location
            source_obj.location = source_obj.location

            # Update parenting
            for obj in created_objects:
                if obj.parent != empty:
                    obj.parent = empty
                    obj.matrix_parent_inverse = empty.matrix_world.inverted()
        else:
            # Remove empty if it exists
            if array_empty:
                # Unparent all objects before removing empty
                for obj in array_empty.children:
                    obj.parent = None
                bpy.data.objects.remove(array_empty, do_unlink=True)
            
            if props.parent_mode == 'OBJECT':
                # Update parent relationships
                for obj in created_objects[1:]:
                    if obj.parent != source_obj:
                        obj.parent = source_obj
                        obj.matrix_parent_inverse = source_obj.matrix_world.inverted()

        # Select source object after operation
        bpy.ops.object.select_all(action='DESELECT')
        source_obj.select_set(True)
        context.view_layer.objects.active = source_obj

        # Add undo message
        is_update = array_empty is not None
        self.report({'INFO'}, f"{'Updated' if is_update else 'Created'} array with {props.count} objects")

        return {'FINISHED'}

    def evaluate_curve_point(self, curve, spline, local_distance):
        """Evaluate point and tangent on curve at given distance"""
        if spline.type == 'BEZIER':
            points = spline.bezier_points
            segments = len(points) - 1
            segment_idx = int(local_distance * segments)
            t = (local_distance * segments) % 1.0
            
            # Get control points in world space
            p0 = curve.matrix_world @ points[segment_idx].co
            h1 = curve.matrix_world @ points[segment_idx].handle_right
            h2 = curve.matrix_world @ points[min(segment_idx + 1, len(points) - 1)].handle_left
            p1 = curve.matrix_world @ points[min(segment_idx + 1, len(points) - 1)].co
            
            # Calculate point using Bezier interpolation
            t1 = 1.0 - t
            pos = t1 * t1 * t1 * p0 + \
                 3.0 * t * t1 * t1 * h1 + \
                 3.0 * t * t * t1 * h2 + \
                 t * t * t * p1
            
            # Calculate tangent
            tangent = (3.0 * t1 * t1 * (h1 - p0) + \
                     6.0 * t * t1 * (h2 - h1) + \
                     3.0 * t * t * (p1 - h2))
        else:
            # For non-bezier splines
            points = spline.points
            segments = len(points) - 1
            segment_idx = int(local_distance * segments)
            t = (local_distance * segments) % 1.0
            
            p0 = curve.matrix_world @ points[segment_idx].co
            p1 = curve.matrix_world @ points[min(segment_idx + 1, len(points) - 1)].co
            
            pos = p0.lerp(p1, t)
            tangent = p1 - p0
        
        return pos, tangent

class VIEW3D_PT_circular_array(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Circular Array'
    bl_label = "Circular Array"
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout
        props = context.scene.circular_array_props

        # Preset menüsünü ekle
        row = layout.row(align=True)
        row.menu("CIRCULARARRAY_MT_presets", icon='PRESET')
        row.operator("circular_array.preset_add", text="", icon='ADD')
        row.operator("circular_array.preset_add", text="", icon='REMOVE').remove_active = True

        # Basic Settings
        box = layout.box()
        box.label(text="Basic Settings:", icon='SETTINGS')
        col = box.column(align=True)
        col.prop(props, "count")
        col.prop(props, "radius")
        col.prop(props, "rotation_offset")

        # Distribution Settings
        box = layout.box()
        box.label(text="Distribution:", icon='MOD_ARRAY')
        box.prop(props, "distribution_mode", text="Type")
        
        if props.distribution_mode == 'ELLIPTICAL':
            col = box.column(align=True)
            row = col.row(align=True)
            row.prop(props, "ellipse_ratio", slider=True)  # Slider for better UX
            row = col.row(align=True)
            row.prop(props, "ellipse_rotation")

        # Multiple Object Settings
        if context.selected_objects and len(context.selected_objects) > 1:
            box = layout.box()
            box.label(text="Multiple Objects:", icon='OUTLINER_OB_GROUP_INSTANCE')
            box.prop(props, "use_selected")
            if props.use_selected:
                box.prop(props, "spacing_angle")

        # Vertical Settings
        box = layout.box()
        box.label(text="Height Settings:", icon='ARROW_LEFTRIGHT')
        box.prop(props, "vertical_mode", text="Mode")
        col = box.column(align=True)
        col.prop(props, "vertical_offset")
        
        if props.vertical_mode == 'SPIRAL':
            col.prop(props, "spiral_revolutions")
            col.prop(props, "spiral_direction")

        # Advanced Settings
        box = layout.box()
        row = box.row()
        row.prop(props, "rotation_enable", text="Advanced Rotation", icon='DRIVER_ROTATIONAL_DIFFERENCE')
        if props.rotation_enable:
            col = box.column(align=True)
            col.prop(props, "rotation_initial")
            col.prop(props, "rotation_progressive")

        # Randomization Settings
        box = layout.box()
        row = box.row()
        row.prop(props, "use_random", text="Randomize", icon='MOD_NOISE')
        if props.use_random:
            col = box.column(align=True)
            col.prop(props, "random_seed")
            col.separator()
            col.prop(props, "random_scale")
            col.prop(props, "random_rotation")
            col.prop(props, "random_offset")

        # Parenting Settings
        box = layout.box()
        box.label(text="Organization:", icon='OUTLINER_OB_EMPTY')
        box.prop(props, "parent_mode")

        # Curve Controls
        if props.distribution_mode == 'CURVE':
            box = layout.box()
            box.label(text="Curve Settings:", icon='CURVE_DATA')
            col = box.column(align=True)
            col.prop(props, "curve_object")
            if props.curve_object:
                col.prop(props, "follow_curve_rotation")
                col.prop(props, "curve_up_axis")
                if props.curve_up_axis == 'CUSTOM':
                    col.prop(props, "curve_up_vector")
                
                row = col.row(align=True)
                row.prop(props, "curve_offset_units", expand=True)
                if props.curve_offset_units == 'FACTOR':
                    col.prop(props, "curve_offset", slider=True)
                else:
                    col.prop(props, "curve_offset_distance")

        # Create/Update Button
        is_array = (context.active_object and 
                   ("Circular_Array_Center_" in context.active_object.name or
                    (context.active_object.parent and "Circular_Array_Center_" in context.active_object.parent.name) or
                    any(obj.parent == context.active_object for obj in bpy.data.objects)))

        row = layout.row(align=True)
        row.scale_y = 1.5  # Bigger button
        row.operator("object.circular_array", 
                    icon='MOD_ARRAY',
                    text="Update Array" if is_array else "Create Array")

# Preset operatörü
class CIRCULARARRAY_OT_add_preset(AddPresetBase, Operator):
    bl_idname = "circular_array.preset_add"
    bl_label = "Add Circular Array Preset"
    bl_description = "Add or remove a preset"
    preset_menu = "CIRCULARARRAY_MT_presets"

    # Preset değerlerini belirle
    preset_defines = [
        "scene = bpy.context.scene",
        "props = scene.circular_array_props"
    ]

    # Hangi özelliklerin kaydedileceğini belirle
    preset_values = [
        "props.count",
        "props.radius",
        "props.rotation_offset",
        "props.vertical_offset",
        "props.vertical_mode",
        "props.distribution_mode",
        "props.ellipse_ratio",
        "props.ellipse_rotation",
        "props.spiral_revolutions",
        "props.spiral_direction",
        "props.rotation_enable",
        "props.rotation_initial",
        "props.rotation_progressive",
        "props.parent_mode",
        "props.use_random",
        "props.random_scale",
        "props.random_rotation",
        "props.random_offset",
        "props.random_seed",
    ]

    # Preset dosyalarının konumu
    preset_subdir = "circular_array"

# Preset menüsü
class CIRCULARARRAY_MT_presets(Menu):
    bl_idname = "CIRCULARARRAY_MT_presets"
    bl_label = "Array Presets"
    preset_subdir = "circular_array"
    preset_operator = "script.execute_preset"
    draw = Menu.draw_preset

# Varsayılan presetleri oluştur
def create_default_presets():
    presets = [
        {
            "name": "Basic Circle",
            "values": {
                "count": 6,
                "radius": 2.0,
                "rotation_offset": 0.0,
                "vertical_mode": 'SINGLE',
                "distribution_mode": 'CIRCULAR',
                "parent_mode": 'EMPTY'
            }
        },
        {
            "name": "Basic Spiral",
            "values": {
                "count": 12,
                "radius": 2.0,
                "vertical_mode": 'SPIRAL',
                "vertical_offset": 0.5,
                "spiral_revolutions": 1.0,
                "distribution_mode": 'CIRCULAR',
                "parent_mode": 'EMPTY'
            }
        },
        {
            "name": "Elliptical Array",
            "values": {
                "count": 8,
                "radius": 3.0,
                "distribution_mode": 'ELLIPTICAL',
                "ellipse_ratio": 0.5,
                "ellipse_rotation": 0.0,
                "parent_mode": 'EMPTY'
            }
        },
        {
            "name": "Random Circle",
            "values": {
                "count": 10,
                "radius": 2.5,
                "distribution_mode": 'CIRCULAR',
                "use_random": True,
                "random_scale": (0.2, 0.2, 0.2),
                "random_rotation": (15.0, 15.0, 15.0),
                "random_offset": (0.1, 0.1, 0.1),
                "parent_mode": 'EMPTY'
            }
        }
    ]
    
    # Preset dizini oluştur
    preset_path = os.path.join(bpy.utils.user_resource('SCRIPTS'), 
                              "presets", 
                              "circular_array")
    os.makedirs(preset_path, exist_ok=True)
    
    # Varsayılan presetleri oluştur
    for preset in presets:
        preset_file = os.path.join(preset_path, f"{preset['name']}.py")
        if not os.path.exists(preset_file):
            with open(preset_file, 'w') as f:
                f.write("import bpy\n")
                f.write("props = bpy.context.scene.circular_array_props\n\n")
                for key, value in preset['values'].items():
                    if isinstance(value, str):
                        f.write(f"props.{key} = '{value}'\n")
                    elif isinstance(value, tuple):
                        f.write(f"props.{key} = {value}\n")
                    else:
                        f.write(f"props.{key} = {value}\n")

classes = (
    CircularArrayProperties,
    OBJECT_OT_circular_array,
    VIEW3D_PT_circular_array,
    CIRCULARARRAY_OT_add_preset,
    CIRCULARARRAY_MT_presets,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.circular_array_props = bpy.props.PointerProperty(type=CircularArrayProperties)
    create_default_presets()

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.circular_array_props

if __name__ == "__main__":
    register() 