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
import random
from mathutils import Vector, Matrix, Euler
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
        min=0.0,
        max=100.0,
        soft_min=0.0,
        soft_max=20.0,
        step=10,
        precision=3,
        unit='LENGTH'
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
        name="Use Random",
        description="Apply random variations to the array objects",
        default=False
    )
    random_seed: bpy.props.IntProperty(
        name="Seed",
        description="Random seed for consistent results",
        default=1,
        min=1
    )
    random_scale: bpy.props.FloatProperty(
        name="Scale",
        description="Random scale variation",
        default=0.0,
        min=0.0,
        max=1.0,
        precision=3
    )
    random_rotation: bpy.props.FloatProperty(
        name="Rotation",
        description="Random rotation variation in degrees",
        default=0.0,
        min=0.0,
        max=180.0
    )
    random_offset: bpy.props.FloatProperty(
        name="Offset",
        description="Random position offset",
        default=0.0,
        min=0.0,
        precision=3,
        unit='LENGTH'
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

        # Source objenin konumunu sakla
        source_pos = source_obj.location.copy()
        
        # Çemberin merkezi, source'dan X ekseninde radius kadar mesafede
        array_center = source_pos + Vector((props.radius, 0, 0))
        
        # Calculate positions for all objects
        for i in range(props.count):
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

                    # Calculate offset
                    if props.curve_offset_units == 'FACTOR':
                        offset = props.curve_offset
                    else:  # DISTANCE
                        # Mesafe bazlı offset'i curve uzunluğuna göre normalize et
                        offset = (props.curve_offset_distance % curve_length) / curve_length

                    # Calculate positions and rotations for all objects
                    for i in range(props.count):
                        # Eşit dağılım için factor hesapla
                        base_factor = i / props.count
                        
                        # Offset'i uygula ve 0-1 aralığında tut
                        eval_factor = (base_factor + offset) % 1.0

                        # Evaluate curve point
                        pos, tangent = self.evaluate_curve_point(curve, curve.data.splines[0], eval_factor)
                        positions.append(pos)

                        # Calculate rotation based on curve tangent
                        if props.follow_curve_rotation:
                            # Get world up vector
                            if props.curve_up_axis == 'Z':
                                world_up = Vector((0, 0, 1))
                            elif props.curve_up_axis == 'Y':
                                world_up = Vector((0, 1, 0))
                            else:
                                world_up = Vector((1, 0, 0))

                            # Calculate rotation matrix
                            forward = tangent.normalized()
                            
                            # Right vektörünü hesapla
                            right = forward.cross(world_up)
                            if right.length < 0.001:
                                right = Vector((1, 0, 0))
                            right.normalize()
                            
                            # Up vektörünü forward ve right'a göre hesapla
                            up = right.cross(forward)
                            up.normalize()
                            
                            # Rotasyon matrisini oluştur
                            rot_mat = Matrix.Identity(3)
                            rot_mat.col[0] = right
                            rot_mat.col[1] = forward
                            rot_mat.col[2] = up
                            
                            # Convert to euler angles - önemli: sıralama XYZ olmalı
                            rot = rot_mat.to_euler('XYZ')
                            
                            # Source objenin orijinal rotasyonunu koru
                            base_rot = source_obj.rotation_euler.copy()
                            
                            # Rotasyonları birleştir
                            final_rot = Euler((
                                base_rot.x,
                                base_rot.y,
                                rot.z  # Sadece Z eksenindeki rotasyonu uygula
                            ))
                            
                            rotations.append(final_rot)
                        else:
                            rot = source_obj.rotation_euler.copy()
                            rotations.append(rot)

                    # Update source object position and rotation
                    source_obj.location = positions[0]
                    source_obj.rotation_euler = rotations[0]

                except Exception as e:
                    self.report({'ERROR'}, f"Error processing curve: {str(e)}")
                    return {'CANCELLED'}

            else:
                # Normal circular/elliptical array için açı hesaplaması
                angle = (2 * math.pi * i) / props.count - math.pi
                offset_angle = math.radians(props.rotation_offset)
                total_angle = angle + offset_angle

                if props.distribution_mode == 'ELLIPTICAL':
                    # Elliptical koordinatları hesapla
                    a = props.radius  # Major axis
                    b = props.radius * props.ellipse_ratio  # Minor axis
                    
                    # Çember üzerindeki pozisyonu hesapla
                    x = array_center.x + (a * math.cos(total_angle))
                    y = array_center.y + (b * math.sin(total_angle))
                    
                    if props.ellipse_rotation != 0:
                        rot_angle = math.radians(props.ellipse_rotation)
                        rel_x = x - array_center.x
                        rel_y = y - array_center.y
                        x = array_center.x + (rel_x * math.cos(rot_angle) - rel_y * math.sin(rot_angle))
                        y = array_center.y + (rel_x * math.sin(rot_angle) + rel_y * math.cos(rot_angle))
                else:  # CIRCULAR
                    # Çember üzerindeki pozisyonu hesapla
                    x = array_center.x + (props.radius * math.cos(total_angle))
                    y = array_center.y + (props.radius * math.sin(total_angle))

                # Calculate vertical offset
                if props.vertical_mode == 'SINGLE':
                    z = source_pos.z + props.vertical_offset
                elif props.vertical_mode == 'INCREMENTAL':
                    z = source_pos.z + (props.vertical_offset * i)
                elif props.vertical_mode == 'SPIRAL':
                    current_revolution = i / props.count * props.spiral_revolutions
                    z = source_pos.z + (props.vertical_offset * current_revolution)
                    if props.spiral_direction == 'DOWN':
                        z = source_pos.z - (props.vertical_offset * current_revolution)

                pos = Vector((x, y, z))
                positions.append(pos)

                # Calculate rotation
                angle = math.atan2(y - array_center.y, x - array_center.x)
                rot = Euler((0, 0, angle + math.pi/2))
                rot.x += source_obj.rotation_euler.x
                rot.y += source_obj.rotation_euler.y
                rot.z += source_obj.rotation_euler.z

                rotations.append(rot)

        # Update or create objects
        created_objects = []
        
        # Source objeyi listeye ekle
        created_objects.append(source_obj)

        # Update or create other objects
        for i in range(1, props.count):
            if i-1 < len(array_objects):
                obj = array_objects[i-1]
            else:
                obj = source_obj.copy()
                obj.data = source_obj.data
                context.scene.collection.objects.link(obj)
            
            # Reset transforms to base values first
            obj.location = positions[i]
            obj.rotation_euler = rotations[i]
            obj.scale = source_obj.scale.copy()  # Reset scale to source object's scale

            # Apply randomization if enabled
            if props.use_random:
                # Set random seed for consistent results
                random.seed(props.random_seed + i)
                
                # Random scale
                if props.random_scale > 0:
                    random_scale = 1.0 + (random.uniform(-props.random_scale, props.random_scale))
                    obj.scale = source_obj.scale * random_scale
                
                # Random rotation
                if props.random_rotation > 0:
                    random_rot_x = random.uniform(-props.random_rotation, props.random_rotation)
                    random_rot_y = random.uniform(-props.random_rotation, props.random_rotation)
                    random_rot_z = random.uniform(-props.random_rotation, props.random_rotation)
                    obj.rotation_euler.x += math.radians(random_rot_x)
                    obj.rotation_euler.y += math.radians(random_rot_y)
                    obj.rotation_euler.z += math.radians(random_rot_z)
                
                # Random offset
                if props.random_offset > 0:
                    random_offset_x = random.uniform(-props.random_offset, props.random_offset)
                    random_offset_y = random.uniform(-props.random_offset, props.random_offset)
                    random_offset_z = random.uniform(-props.random_offset, props.random_offset)
                    obj.location += Vector((random_offset_x, random_offset_y, random_offset_z))
            
            created_objects.append(obj)

        # Remove extra objects
        if len(array_objects) > (props.count - 1):
            for obj in array_objects[props.count-1:]:
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

    def evaluate_curve_point(self, curve, spline, factor):
        """Evaluate point and tangent on curve at given distance"""
        if spline.type == 'BEZIER':
            points = spline.bezier_points
            segments = len(points) - 1
            segment_idx = int(factor * segments)
            t = (factor * segments) % 1.0
            
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
            segment_idx = int(factor * segments)
            t = (factor * segments) % 1.0
            
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

        # Preset Row
        row = layout.row(align=True)
        row.menu("CIRCULARARRAY_MT_presets", text="Presets", icon='PRESET')
        row.operator("circular_array.preset_add", text="", icon='ADD')
        row.operator("circular_array.preset_add", text="", icon='REMOVE').remove_active = True

        # Basic Settings
        box = layout.box()
        box.label(text="Basic Settings:", icon='SETTINGS')
        col = box.column(align=True)
        col.prop(props, "count")
        col.prop(props, "radius", slider=True)
        col.prop(props, "rotation_offset")

        # Distribution Settings
        box = layout.box()
        box.label(text="Distribution:", icon='DRIVER_DISTANCE')
        box.prop(props, "distribution_mode", text="Type")
        
        if props.distribution_mode == 'ELLIPTICAL':
            col = box.column(align=True)
            row = col.row(align=True)
            row.prop(props, "ellipse_ratio", slider=True)
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
            
            # Curve object selection
            row = col.row(align=True)
            row.prop(props, "curve_object")
            row.operator("curve.primitive_bezier_curve_add", text="", icon='ADD')
            
            if props.curve_object:
                col.prop(props, "follow_curve_rotation", icon='ORIENTATION_GIMBAL')
                if props.follow_curve_rotation:
                    col.prop(props, "curve_up_axis", expand=True)
                
                # Curve offset settings
                row = col.row(align=True)
                row.prop(props, "curve_offset_units", expand=True)
                if props.curve_offset_units == 'FACTOR':
                    col.prop(props, "curve_offset", slider=True)
                else:
                    col.prop(props, "curve_offset_distance")

        # Create/Update Button
        layout.separator()
        is_array = (context.active_object and 
                    ("Circular_Array_Center_" in context.active_object.name or
                     (context.active_object.parent and "Circular_Array_Center_" in context.active_object.parent.name)))
        
        row = layout.row(align=True)
        row.scale_y = 1.5
        row.operator("object.circular_array",
                    text="Update Array" if is_array else "Create Array",
                    icon='MOD_ARRAY')

# Preset operatörü
class OBJECT_OT_add_circular_array_preset(AddPresetBase, Operator):
    bl_idname = "circular_array.preset_add"
    bl_label = "Add Circular Array Preset"
    bl_description = "Add or remove a preset"
    preset_menu = "CIRCULARARRAY_MT_presets"

    # Preset tanımlamaları
    spiral_preset = {
        'count': 36,
        'radius': 3.0,
        'rotation_offset': 0,
        'vertical_offset': 0.5,  # Daha belirgin spiral için arttırıldı
        'vertical_mode': 'SPIRAL',
        'spiral_revolutions': 2.0,  # İki tam dönüş için
        'distribution_mode': 'CIRCULAR',
        'parent_mode': 'EMPTY'
    }

    # Diğer presetler de eklenebilir...

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
    OBJECT_OT_add_circular_array_preset,
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