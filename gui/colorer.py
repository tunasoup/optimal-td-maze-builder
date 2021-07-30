from typing import List

from tiles.tile_type import TTYPES


class Colorer:
    def __init__(self):
        """
        Changes the colors of the GUI objects to the selected color profile.
        """
        self.color_profiles = {

            'Default': {
                'ttypes': {
                    'basic': '#a16b55',
                    'unbuildable': '#6e3b27',
                    'void': 'transparent',
                    'spawn': '#ff0000',
                    'exit': '#00ff00',
                    'occupied': '#6e1fa6',
                    'route': '#f7ed23',
                    # 'tower': '#c716de',
                },
                'background': 'transparent',
                'outline': '#ffffff',
            },

            'Sanctum 2': {
                'ttypes': {
                    'basic': '#0a304f',
                    'unbuildable': '#6c7478',# and '#54585a',
                    'void': 'transparent',
                    'spawn': '#a6442f',
                    'exit': '#86a0ba',
                    'occupied': '#0561d0',
                    'route': '#fe5400',
                    #'tower': '#6bc614',
                },
                'background': '#141f2d',
                'outline': '#ffffff',
            }
        }

        self.color_profile_names = list(self.color_profiles.keys())

    def get_background_color(self, color_profile_name: str) -> str:
        return self.color_profiles[color_profile_name]['background']

    def change_to_profile(self, color_profile_name: str) -> None:
        for ttype, color in self.color_profiles[color_profile_name]['ttypes'].items():
            TTYPES[ttype].color = color
