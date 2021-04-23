#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import math
from typing import Optional
import arcade

import time



SCREEN_TITLE = "Arcadia"

# How big are our image tiles?
SPRITE_IMAGE_SIZE = 128

# Scale sprites up or down
SPRITE_SCALING_PLAYER = 0.5
SPRITE_SCALING_TILES = 0.5

# Scaled sprite size for tiles
SPRITE_SIZE = int(SPRITE_IMAGE_SIZE * SPRITE_SCALING_PLAYER)

# Size of grid to show on screen, in number of tiles
SCREEN_GRID_WIDTH = 25
SCREEN_GRID_HEIGHT = 15

# Size of screen to show, in pixels
SCREEN_WIDTH = SPRITE_SIZE * SCREEN_GRID_WIDTH
SCREEN_HEIGHT = SPRITE_SIZE * SCREEN_GRID_HEIGHT

HALF_SCREEN_WIDTH = SCREEN_WIDTH // 2
HALF_SCREEN_HEIGHT = SCREEN_HEIGHT // 2

# --- Physics forces. Higher number, faster accelerating.

# Gravity
GRAVITY = 1500

# Damping - Amount of speed lost per second
DEFAULT_DAMPING = 1.0
PLAYER_DAMPING = 0.4

#PLAYER_DAMPING = 0.9


# Friction between objects
PLAYER_FRICTION = 1.0
WALL_FRICTION = 0.7
DYNAMIC_ITEM_FRICTION = 0.6

# Mass (defaults to 1)
PLAYER_MASS = 2.0

# Keep player from going too fast
PLAYER_MAX_HORIZONTAL_SPEED = 450
PLAYER_MAX_VERTICAL_SPEED = 1600

# Force applied while on the ground
PLAYER_MOVE_FORCE_ON_GROUND = 8000

# Force applied when moving left/right in the air
PLAYER_MOVE_FORCE_IN_AIR = 900

# Strength of a jump
PLAYER_JUMP_IMPULSE = 1800

# Close enough to not-moving to have the animation go to idle.
DEAD_ZONE = 0.1

# Constants used to track if the player is facing left or right
RIGHT_FACING = 0
LEFT_FACING = 1

# How many pixels to move before we change the texture in the walking animation
DISTANCE_TO_CHANGE_TEXTURE = 20

# How much force to put on the bullet
BULLET_MOVE_FORCE = 4500

# Mass of the bullet
BULLET_MASS = 0.1

# Make bullet less affected by gravity
BULLET_GRAVITY = 300

# GAMEPAD BUTTON CONFIG

JUMPBTN = 0 # A

class PlayerSprite(arcade.Sprite):
    """ Player Sprite """
    def __init__(self,
                 ladder_list: arcade.SpriteList,
                 hit_box_algorithm):
        """ Init """
        # Let parent initialize
        super().__init__()

        

        # Set our scale
        self.scale = SPRITE_SCALING_PLAYER

        # Images from Kenney.nl's Character pack
        
        main_path = ":resources:images/animated_characters/female_person/femalePerson"
        

        # Load textures for idle standing
        self.idle_texture_pair = arcade.load_texture_pair(f"{main_path}_idle.png",
                                                          hit_box_algorithm=hit_box_algorithm)
        self.jump_texture_pair = arcade.load_texture_pair(f"{main_path}_jump.png")
        self.fall_texture_pair = arcade.load_texture_pair(f"{main_path}_fall.png")

        # Load textures for walking
        self.walk_textures = []
        for i in range(8):
            texture = arcade.load_texture_pair(f"{main_path}_walk{i}.png")
            self.walk_textures.append(texture)

        # Load textures for climbing
        self.climbing_textures = []
        texture = arcade.load_texture(f"{main_path}_climb0.png")
        self.climbing_textures.append(texture)
        texture = arcade.load_texture(f"{main_path}_climb1.png")
        self.climbing_textures.append(texture)

        # Set the initial texture
        self.texture = self.idle_texture_pair[0]

        # Hit box will be set based on the first image used.
        self.hit_box = self.texture.hit_box_points

        # Default to face-right
        self.character_face_direction = RIGHT_FACING

        # Index of our current texture
        self.cur_texture = 0

        # How far have we traveled horizontally since changing the texture
        self.x_odometer = 0
        self.y_odometer = 0

        self.ladder_list = ladder_list
        self.is_on_ladder = False

    def pymunk_moved(self, physics_engine, dx, dy, d_angle):
        """ Handle being moved by the pymunk engine """
        # Figure out if we need to face left or right
        if dx < -DEAD_ZONE and self.character_face_direction == RIGHT_FACING:
            self.character_face_direction = LEFT_FACING
        elif dx > DEAD_ZONE and self.character_face_direction == LEFT_FACING:
            self.character_face_direction = RIGHT_FACING

        # Are we on the ground?
        is_on_ground = physics_engine.is_on_ground(self)

        # Are we on a ladder?
        if len(arcade.check_for_collision_with_list(self, self.ladder_list)) > 0:
            if not self.is_on_ladder:
                self.is_on_ladder = True
                self.pymunk.gravity = (0, 0)
                self.pymunk.damping = 0.0001
                self.pymunk.max_vertical_velocity = PLAYER_MAX_HORIZONTAL_SPEED
        else:
            if self.is_on_ladder:
                self.pymunk.damping = 1.0
                self.pymunk.max_vertical_velocity = PLAYER_MAX_VERTICAL_SPEED
                self.is_on_ladder = False
                self.pymunk.gravity = None

        # Add to the odometer how far we've moved
        self.x_odometer += dx
        self.y_odometer += dy

        if self.is_on_ladder and not is_on_ground:
            # Have we moved far enough to change the texture?
            if abs(self.y_odometer) > DISTANCE_TO_CHANGE_TEXTURE:

                # Reset the odometer
                self.y_odometer = 0

                # Advance the walking animation
                self.cur_texture += 1

            if self.cur_texture > 1:
                self.cur_texture = 0
            self.texture = self.climbing_textures[self.cur_texture]
            return

        # Jumping animation
        if not is_on_ground:
            if dy > DEAD_ZONE:
                self.texture = self.jump_texture_pair[self.character_face_direction]
                return
            elif dy < -DEAD_ZONE:
                self.texture = self.fall_texture_pair[self.character_face_direction]
                return

        # Idle animation
        if abs(dx) <= DEAD_ZONE:
            self.texture = self.idle_texture_pair[self.character_face_direction]
            return

        # Have we moved far enough to change the texture?
        if abs(self.x_odometer) > DISTANCE_TO_CHANGE_TEXTURE:

            # Reset the odometer
            self.x_odometer = 0

            # Advance the walking animation
            self.cur_texture += 1
            if self.cur_texture > 7:
                self.cur_texture = 0
            self.texture = self.walk_textures[self.cur_texture][self.character_face_direction]

class BulletSprite(arcade.SpriteSolidColor):
    """ Bullet Sprite """
    def pymunk_moved(self, physics_engine, dx, dy, d_angle):
        """ Handle when the sprite is moved by the physics engine. """
        # If the bullet falls below the screen, remove it
        if self.center_y < -100:
            self.remove_from_sprite_lists()


class GameWindow(arcade.Window):
    """ Main Window """

    def __init__(self, width, height, title):
        """ Create the variables """

        # Init the parent class
        super().__init__(width, height, title)


        #............................................................

        #camera demo example vsync:
        self.set_vsync(True)

        #mouse tracker:
        self.mouse_pos = 0, 0
        #.............................................
        self.time = 0
        #*********





        # ////////////////////////////////////////////////////////////////
        self.joysticks = None
        #....................

        # Get list of game controllers that are available
        joysticks = arcade.get_joysticks()

        # If we have any...
        if joysticks:
            # Grab the first one in  the list
            self.joystick = joysticks[0]

            # Open it for input
            self.joystick.open()

            print("joystick open")

            # Push this object as a handler for joystick events.
            # Required for the on_joy* events to be called.
            self.joystick.push_handlers(self)
        else:
            # Handle if there are no joysticks.
            print("There are no joysticks, plug in a joystick and run again.")
            self.joystick = None

        # ////////////////////////////////////////////////////////////////





        # Player sprite
        self.player_sprite: Optional[PlayerSprite] = None

        # Sprite lists we need
        self.player_list: Optional[arcade.SpriteList] = None
        self.wall_list: Optional[arcade.SpriteList] = None
        self.bullet_list: Optional[arcade.SpriteList] = None
        self.item_list: Optional[arcade.SpriteList] = None
        #self.autonom_moving_sprites_list: Optional[arcade.SpriteList] = None
        self.ladder_list: Optional[arcade.SpriteList] = None

        self.trap_list: Optional[arcade.SpriteList] = None
        self.mechanics_list: Optional[arcade.SpriteList] = None
        self.mechandler_list: Optional[arcade.SpriteList] = None
        self.stairs_list: Optional[arcade.SpriteList] = None
        self.enemy_list: Optional[arcade.SpriteList] = None

        self.lowfric_list: Optional[arcade.SpriteList] = None




        # Track the current state of what key is pressed
        self.left_pressed: bool = False
        self.right_pressed: bool = False
        self.up_pressed: bool = False
        self.down_pressed: bool = False

        # Physics engine
        self.physics_engine = Optional[arcade.PymunkPhysicsEngine]

        # Set background color
        arcade.set_background_color(arcade.color.AMAZON)

    def setup(self):
        """ Set up everything with the game """

        # Create the sprite lists
        self.player_list = arcade.SpriteList()
        self.bullet_list = arcade.SpriteList()

        # Read in the tiled map
        map_name = "resources/tmx_maps/pymunk_test_map.tmx"
        my_map = arcade.tilemap.read_tmx(map_name)

        # Read in the map layers
        self.wall_list = arcade.tilemap.process_layer(my_map,
                                                      'Platforms',
                                                      SPRITE_SCALING_TILES,
                                                      hit_box_algorithm="Detailed")
        #self.item_list = arcade.tilemap.process_layer(my_map,
        #                                              'Dynamic Items',
        #                                              SPRITE_SCALING_TILES,
        #                                              hit_box_algorithm="Detailed")
        self.item_list = arcade.tilemap.process_layer(my_map,
                                                      'Dynamic_items',
                                                      SPRITE_SCALING_TILES,
                                                      hit_box_algorithm="Detailed")
        self.ladder_list = arcade.tilemap.process_layer(my_map,
                                                        'ladders',
                                                        SPRITE_SCALING_TILES,
                                                        use_spatial_hash=True,
                                                        hit_box_algorithm="Detailed")

        self.trap_list = arcade.tilemap.process_layer(my_map,
                                                        'traps',
                                                        SPRITE_SCALING_TILES,
                                                        use_spatial_hash=True,
                                                        hit_box_algorithm="Detailed")
        self.mechanics_list = arcade.tilemap.process_layer(my_map,
                                                        'mechanics',
                                                        SPRITE_SCALING_TILES,
                                                        use_spatial_hash=True,
                                                        hit_box_algorithm="Detailed")
        
        self.mechandler_list = arcade.tilemap.process_layer(my_map,
                                                        'mec_handlers',
                                                        SPRITE_SCALING_TILES,
                                                        use_spatial_hash=True,
                                                        hit_box_algorithm="Detailed")
        self.stairs_list = arcade.tilemap.process_layer(my_map,
                                                        'Stairs',
                                                        SPRITE_SCALING_TILES,
                                                        use_spatial_hash=True,
                                                        hit_box_algorithm="Detailed")
        self.enemy_list = arcade.tilemap.process_layer(my_map,
                                                        'enemies',
                                                        SPRITE_SCALING_TILES,
                                                        use_spatial_hash=True,
                                                        hit_box_algorithm="Detailed")

        self.lowfric_list = arcade.tilemap.process_layer(my_map,
                                                        'low_friction_platforms',
                                                        SPRITE_SCALING_TILES,
                                                        use_spatial_hash=True,
                                                        hit_box_algorithm="Detailed")


        # Create player sprite
        self.player_sprite = PlayerSprite(self.ladder_list, hit_box_algorithm="Detailed")

        # Set player location
        #grid_x = 1
        #grid_y = 1
       

        grid_x = 7
        grid_y = 15




        self.player_sprite.center_x = SPRITE_SIZE * grid_x + SPRITE_SIZE / 2
        self.player_sprite.center_y = SPRITE_SIZE * grid_y + SPRITE_SIZE / 2
        # Add to player sprite list
        self.player_list.append(self.player_sprite)

        # Moving Sprite
        self.autonom_moving_sprites_list = arcade.tilemap.process_layer(my_map,
                                                                'Moving Platforms',
                                                                SPRITE_SCALING_TILES)

        # --- Pymunk Physics Engine Setup ---

        # The default damping for every object controls the percent of velocity
        # the object will keep each second. A value of 1.0 is no speed loss,
        # 0.9 is 10% per second, 0.1 is 90% per second.
        # For top-down games, this is basically the friction for moving objects.
        # For platformers with gravity, this should probably be set to 1.0.
        # Default value is 1.0 if not specified.
        damping = DEFAULT_DAMPING

        # Set the gravity. (0, 0) is good for outer space and top-down.
        gravity = (0, -GRAVITY)

        # Create the physics engine
        self.physics_engine = arcade.PymunkPhysicsEngine(damping=damping,
                                                         gravity=gravity)

        def wall_hit_handler(bullet_sprite, _wall_sprite, _arbiter, _space, _data):
            """ Called for bullet/wall collision """
            bullet_sprite.remove_from_sprite_lists()

        self.physics_engine.add_collision_handler("bullet", "wall", post_handler=wall_hit_handler)

        def item_hit_handler(bullet_sprite, item_sprite, _arbiter, _space, _data):
            """ Called for bullet/wall collision """
            bullet_sprite.remove_from_sprite_lists()
            item_sprite.remove_from_sprite_lists()

        self.physics_engine.add_collision_handler("bullet", "item", post_handler=item_hit_handler)

        # Add the player.
        # For the player, we set the damping to a lower value, which increases
        # the damping rate. This prevents the character from traveling too far
        # after the player lets off the movement keys.
        # Setting the moment to PymunkPhysicsEngine.MOMENT_INF prevents it from
        # rotating.
        # Friction normally goes between 0 (no friction) and 1.0 (high friction)
        # Friction is between two objects in contact. It is important to remember
        # in top-down games that friction moving along the 'floor' is controlled
        # by damping.
        self.physics_engine.add_sprite(self.player_sprite,
                                       friction=PLAYER_FRICTION,
                                       mass=PLAYER_MASS,
                                       moment=arcade.PymunkPhysicsEngine.MOMENT_INF,
                                       collision_type="player",
                                       max_horizontal_velocity=PLAYER_MAX_HORIZONTAL_SPEED,
                                       max_vertical_velocity=PLAYER_MAX_VERTICAL_SPEED)

        # Create the walls.
        # By setting the body type to PymunkPhysicsEngine.STATIC the walls can't
        # move.
        # Movable objects that respond to forces are PymunkPhysicsEngine.DYNAMIC
        # PymunkPhysicsEngine.KINEMATIC objects will move, but are assumed to be
        # repositioned by code and don't respond to physics forces.
        # Dynamic is default.
        self.physics_engine.add_sprite_list(self.wall_list,
                                            friction=WALL_FRICTION,
                                            collision_type="wall",
                                            body_type=arcade.PymunkPhysicsEngine.STATIC)

        # Create the items
        self.physics_engine.add_sprite_list(self.item_list,
                                            friction=DYNAMIC_ITEM_FRICTION,
                                            collision_type="item")

        # Add kinematic sprites
        self.physics_engine.add_sprite_list(self.autonom_moving_sprites_list,
                                            body_type=arcade.PymunkPhysicsEngine.KINEMATIC)


        self.physics_engine.add_sprite_list(self.trap_list,
                                            friction=WALL_FRICTION,
                                            #collision_type="wall",
                                            collision_type="trap",
                                            body_type=arcade.PymunkPhysicsEngine.STATIC)






    def trap_hit_handler(player_sprite, _trap_sprite, _arbiter, _space, _data):

        self.physics_engine.add_collision_handler("player", "trap", post_handler=trap_hit_handler)
        print("___trap_hit_handler  , calling **********  respawn") # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< ! ! !


    




    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed. """

        if key == arcade.key.LEFT:
            self.left_pressed = True
        elif key == arcade.key.RIGHT:
            self.right_pressed = True
        elif key == arcade.key.UP:
            self.up_pressed = True
            # find out if player is standing on ground, and not on a ladder
            if self.physics_engine.is_on_ground(self.player_sprite) \
                    and not self.player_sprite.is_on_ladder:
                # She is! Go ahead and jump
                impulse = (0, PLAYER_JUMP_IMPULSE)
                self.physics_engine.apply_impulse(self.player_sprite, impulse)
        elif key == arcade.key.DOWN:
            self.down_pressed = True

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key. """

        if key == arcade.key.LEFT:
            self.left_pressed = False
        elif key == arcade.key.RIGHT:
            self.right_pressed = False
        elif key == arcade.key.UP:
            self.up_pressed = False
        elif key == arcade.key.DOWN:
            self.down_pressed = False

    def on_mouse_press(self, x, y, button, modifiers):
        """ Called whenever the mouse button is clicked. """

        bullet = BulletSprite(20, 5, arcade.color.DARK_YELLOW)
        self.bullet_list.append(bullet)

        # Position the bullet at the player's current location
        start_x = self.player_sprite.center_x
        start_y = self.player_sprite.center_y
        bullet.position = self.player_sprite.position

        # Get from the mouse the destination location for the bullet
        # IMPORTANT! If you have a scrolling screen, you will also need
        # to add in self.view_bottom and self.view_left.
        dest_x, dest_y = self.mouse_coordinates_to_world(x, y)

        # Do math to calculate how to get the bullet to the destination.
        # Calculation the angle in radians between the start points
        # and end points. This is the angle the bullet will travel.
        x_diff = dest_x - start_x
        y_diff = dest_y - start_y
        angle = math.atan2(y_diff, x_diff)

        # What is the 1/2 size of this sprite, so we can figure out how far
        # away to spawn the bullet
        size = max(self.player_sprite.width, self.player_sprite.height) / 2

        # Use angle to to spawn bullet away from player in proper direction
        bullet.center_x += size * math.cos(angle)
        bullet.center_y += size * math.sin(angle)

        # Set angle of bullet
        bullet.angle = math.degrees(angle)

        # Gravity to use for the bullet
        # If we don't use custom gravity, bullet drops too fast, or we have
        # to make it go too fast.
        # Force is in relation to bullet's angle.
        bullet_gravity = (0, -BULLET_GRAVITY)

        # Add the sprite. This needs to be done AFTER setting the fields above.
        self.physics_engine.add_sprite(bullet,
                                       mass=BULLET_MASS,
                                       damping=1.0,
                                       friction=0.6,
                                       collision_type="bullet",
                                       gravity=bullet_gravity,
                                       elasticity=0.9)

        # Add force to bullet
        force = (BULLET_MOVE_FORCE, 0)
        self.physics_engine.apply_force(bullet, force)


    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_pos = x, y


    # noinspection PyMethodMayBeStatic
    def on_joybutton_press(self, _joystick, button):
        """ Handle button-down event for the joystick """
        print("Button {} down".format(button))
        if button == JUMPBTN:
            if self.physics_engine.is_on_ground(self.player_sprite) \
                    and not self.player_sprite.is_on_ladder:
                # She is! Go ahead and jump
                impulse = (0, PLAYER_JUMP_IMPULSE)
                self.physics_engine.apply_impulse(self.player_sprite, impulse)

    def on_update(self, delta_time):
        # Movement and game logic 

        # //////////////////////////////////////////////////////////////////////////
         # If there is a joystick, grab the speed.
        if self.joystick:

            #print(self.joystick.x)
            print(f"joystick   {self.joystick.x}  {self.joystick.y}")


            #MOVEMENT_SPEED = 1000

            # x-axis
            #self.change_x = self.joystick.x * MOVEMENT_SPEED
            # Set a "dead zone" to prevent drive from a centered joystick
            #if abs(self.change_x) > DEAD_ZONE:
            #    self.change_x = 0
            #    print("DZ")



            if self.joystick.x < -0.3: #and not self.right_pressed:
                # Create a force to the left. Apply it.

                #if is_on_ground or self.player_sprite.is_on_ladder:
                if self.physics_engine.is_on_ground(self.player_sprite):# or self.player_sprite.is_on_ladder:

                    force = (-PLAYER_MOVE_FORCE_ON_GROUND, 0)
                else:
                    force = (-PLAYER_MOVE_FORCE_IN_AIR, 0)
                self.physics_engine.apply_force(self.player_sprite, force)
                # Set friction to zero for the player while moving
                self.physics_engine.set_friction(self.player_sprite, 0)
            elif self.joystick.x > 0.3: #and not self.left_pressed:
                # Create a force to the right. Apply it.
                if self.physics_engine.is_on_ground(self.player_sprite):# or self.player_sprite.is_on_ladder:
                    force = (PLAYER_MOVE_FORCE_ON_GROUND, 0)
                else:
                    force = (PLAYER_MOVE_FORCE_IN_AIR, 0)
                self.physics_engine.apply_force(self.player_sprite, force)
                # Set friction to zero for the player while moving
                self.physics_engine.set_friction(self.player_sprite, 0)


            #if self.player_sprite.is_on_ladder:
            if self.player_sprite.is_on_ladder:
            


                if self.joystick.y > 0.3:
                    
                    force = (0, -PLAYER_MOVE_FORCE_ON_GROUND)
                    self.physics_engine.apply_force(self.player_sprite, force)
                    # Set friction to zero for the player while moving
                    self.physics_engine.set_friction(self.player_sprite, 0)

                elif self.joystick.y < -0.3:
                    
                    force = (0, PLAYER_MOVE_FORCE_ON_GROUND)
                    self.physics_engine.apply_force(self.player_sprite, force)
                    # Set friction to zero for the player while moving
                    self.physics_engine.set_friction(self.player_sprite, 0)


        # /////////////////////////////////////////////////////////////////////////

        is_on_ground = self.physics_engine.is_on_ground(self.player_sprite)
        # Update player forces based on keys pressed
        if self.left_pressed and not self.right_pressed:
            # Create a force to the left. Apply it.
            if is_on_ground or self.player_sprite.is_on_ladder:
                force = (-PLAYER_MOVE_FORCE_ON_GROUND, 0)
            else:
                force = (-PLAYER_MOVE_FORCE_IN_AIR, 0)
            self.physics_engine.apply_force(self.player_sprite, force)
            # Set friction to zero for the player while moving
            self.physics_engine.set_friction(self.player_sprite, 0)
        elif self.right_pressed and not self.left_pressed:
            # Create a force to the right. Apply it.
            if is_on_ground or self.player_sprite.is_on_ladder:
                force = (PLAYER_MOVE_FORCE_ON_GROUND, 0)
            else:
                force = (PLAYER_MOVE_FORCE_IN_AIR, 0)
            self.physics_engine.apply_force(self.player_sprite, force)
            # Set friction to zero for the player while moving
            self.physics_engine.set_friction(self.player_sprite, 0)
        elif self.up_pressed and not self.down_pressed:
            # Create a force to the right. Apply it.
            if self.player_sprite.is_on_ladder:
                force = (0, PLAYER_MOVE_FORCE_ON_GROUND)
                self.physics_engine.apply_force(self.player_sprite, force)
                # Set friction to zero for the player while moving
                self.physics_engine.set_friction(self.player_sprite, 0)
        elif self.down_pressed and not self.up_pressed:
            # Create a force to the right. Apply it.
            if self.player_sprite.is_on_ladder:
                force = (0, -PLAYER_MOVE_FORCE_ON_GROUND)
                self.physics_engine.apply_force(self.player_sprite, force)
                # Set friction to zero for the player while moving
                self.physics_engine.set_friction(self.player_sprite, 0)

        else:
            # Player's feet are not moving. Therefore up the friction so we stop.
            self.physics_engine.set_friction(self.player_sprite, 1.0)

        # Move items in the physics engine
        self.physics_engine.step()

        # For each moving sprite, see if we've reached a boundary and need to
        # reverse course.
        for moving_sprite in self.autonom_moving_sprites_list:
            if moving_sprite.boundary_right and \
                    moving_sprite.change_x > 0 and \
                    moving_sprite.right > moving_sprite.boundary_right:
                moving_sprite.change_x *= -1
            elif moving_sprite.boundary_left and \
                    moving_sprite.change_x < 0 and \
                    moving_sprite.left > moving_sprite.boundary_left:
                moving_sprite.change_x *= -1
            if moving_sprite.boundary_top and \
                    moving_sprite.change_y > 0 and \
                    moving_sprite.top > moving_sprite.boundary_top:
                moving_sprite.change_y *= -1
            elif moving_sprite.boundary_bottom and \
                    moving_sprite.change_y < 0 and \
                    moving_sprite.bottom < moving_sprite.boundary_bottom:
                moving_sprite.change_y *= -1

            # Figure out and set our moving platform velocity.
            # Pymunk uses velocity is in pixels per second. If we instead have
            # pixels per frame, we need to convert.
            velocity = (moving_sprite.change_x * 1 / delta_time, moving_sprite.change_y * 1 / delta_time)
            self.physics_engine.set_velocity(moving_sprite, velocity)
    
        #self.time += delta_time
        #self.camera.scroll = (
        #    2800 + math.sin(self.time / 3) * 2900,
        #    -20 + math.cos(self.time / 3) * 100,
        #)

        

        #self.camera.viewport = tuple((self.player_sprite.center_x - HALF_SCREEN_WIDTH, SCREEN_WIDTH, self.player_sprite.center_y - HALF_SCREEN_HEIGHT, SCREEN_HEIGHT,))
        
        #self.camera.viewport = tuple((self.player_sprite.center_x , SCREEN_WIDTH, self.player_sprite.center_y , SCREEN_HEIGHT,))
        

        
        #self.camera.viewport = tuple((self.player_sprite.center_x, self.player_sprite.center_y , SCREEN_WIDTH, SCREEN_HEIGHT,))

    def center_on_player(self):
        w_width, w_height = self.get_size()
        arcade.set_viewport(
        self.player_sprite.center_x - w_width // 2,
        self.player_sprite.center_x + w_width // 2,
        self.player_sprite.center_y - w_height // 2,
        self.player_sprite.center_y + w_height // 2,
    )

    def mouse_coordinates_to_world(self, x, y):
        """
        Calculates in game position of mouse
        """
        w_width, w_height = self.get_size()
        left, right, bottom, top = self.get_viewport()

        x = left + (right - left) * x / w_width
        y = bottom + (top - bottom) * y / w_height

        return x, y
        
    def on_draw(self):
        """ Draw everything """
        arcade.start_render()
        self.center_on_player()

        self.wall_list.draw()
        self.ladder_list.draw()
        self.autonom_moving_sprites_list.draw()
        self.bullet_list.draw()
        self.item_list.draw()
        self.player_list.draw()


        self.trap_list.draw()



        self.mechanics_list.draw()
        self.mechandler_list.draw()
        self.stairs_list.draw()
        self.enemy_list.draw()
        self.lowfric_list.draw()

        

        # for item in self.player_list:
        #     item.draw_hit_box(arcade.color.RED)
        # for item in self.item_list:
        #     item.draw_hit_box(arcade.color.RED)

        #____________________
        world_pos = self.mouse_coordinates_to_world(*self.mouse_pos)
        arcade.draw_circle_filled(*world_pos, 10, arcade.color.BLUE)

        

def main():
    """ Main method """
    window = GameWindow(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
