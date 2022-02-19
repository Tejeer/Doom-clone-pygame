from random import randint
from pygame import Surface


class TextureManager:
    def __init__(self, renderer):
        self.textures = {}
        self.renderer = renderer
        self.load_textures()

    def load_textures(self):
        for seg in self.renderer.game_map.data['SEGS']:
            texture_name = seg.linedef.rightSideDef.middleTexture
            if texture_name not in self.textures:
                color = tuple([randint(0, 255) for i in range(3)])
                surf = Surface((1, 1))
                surf.fill(color)
                self.textures[texture_name] = surf.copy()
