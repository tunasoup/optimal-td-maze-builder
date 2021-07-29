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
                    'basic': '#82add5',
                    'unbuildable': '#1f2d3a',
                    'void': 'transparent',
                    'spawn': '#ff0000',
                    'exit': '#00ff00',
                    'occupied': '#348bab',
                    'route': '#f7ed23',
                    #'tower': '#6bc614',
                },
                'background': '#141f2d',
                'outline': '#ffffff',
            },

            'Sanctum 2': {
                'ttypes': {
                    'basic': '#062844',
                    'unbuildable': '#6064660',# and '#54585a',
                    'void': 'transparent',
                    'spawn': '#a6442f',
                    'exit': '#c4c7ca',
                    'occupied': '#0561d0',
                    'route': '#fe5400',
                    #'tower': '#6bc614',
                },
                'background': '#141f2d',
                'outline': '#ffffff',
            }
        }

        self.color_profile_names = list(self.color_profiles.keys())

    def change_to_profile(self, color_profile_name: str) -> None:
        for ttype, color in self.color_profiles[color_profile_name]['ttypes'].items():
            TTYPES[ttype].color = color
