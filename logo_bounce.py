__author__ = 'Mark'

import game

# "Cairocffi" could be also installed as "cairo"
try:
    import cairocffi as cairo
except ImportError:
    import cairo

from game_elements_library import Rectangle, Moving, \
    collide_to_left_wall, collide_to_bottom_wall, collide_to_right_wall, collide_to_top_wall


class LogoBounce(game.Game):
    def __init__(self, field_dims, image, left=10, top=10, width=25, height=25, speed=0.1, heading=0.6):
        self.field_dims = field_dims
        self.logo = Logo(image, left, top, width, height, speed, heading)

    def step(self):
        self.logo.step()
        collide_to_left_wall(self.logo)
        collide_to_right_wall(self.logo, self.field_dims[0])
        collide_to_top_wall(self.logo)
        collide_to_bottom_wall(self.logo, self.field_dims[1])

    def draw(self, context):
        self.logo.draw(context)


class Logo(Rectangle, Moving):
    def __init__(self, image, left, top, width, height, speed, heading):
        self.logo_surface = cairo.ImageSurface.create_from_png(image)
        super().__init__(left, top, width, height)
        self.speed = speed
        self.heading = heading

        # calculate proportional scaling
        width_ratio = float(self.width) / float(self.logo_surface.get_width())
        height_ratio = float(self.height) / float(self.logo_surface.get_height())
        self.scale_xy = min(height_ratio, width_ratio)

    def step(self):
        self.center_x += self.speed_x
        self.center_y += self.speed_y

    def draw(self, ctx):

        # scale image and add it
        ctx.save()
        ctx.translate(self.left, self.top)
        ctx.scale(self.scale_xy, self.scale_xy)
        ctx.set_source_surface(self.logo_surface)

        ctx.paint()
        ctx.restore()