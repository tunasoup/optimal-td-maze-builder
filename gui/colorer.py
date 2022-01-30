from tiles.tile_type import TTYPES


class Colorer:
    def __init__(self):
        """
        Changes the colors of the GUI objects to the selected color profile.
        """
        self.color_profiles = {

            'Default': {
                'ttypes': {
                    'basic': TTYPES['basic'].color,
                    'unbuildable': TTYPES['unbuildable'].color,
                    'void': TTYPES['void'].color,
                    'spawn': TTYPES['spawn'].color,
                    'exit': TTYPES['exit'].color,
                    'occupied': TTYPES['occupied'].color,
                    'path': TTYPES['path'].color,
                    # 'tower': TTYPES['basic'].color,
                },
                'background': 'transparent',
                'outline': '#ffffff',
            },

            'Sanctum 2': {
                'ttypes': {
                    'basic': '#0a304f',
                    'unbuildable': '#6c7478',  # and '#54585a',
                    'void': 'transparent',
                    'spawn': '#a6442f',
                    'exit': '#86a0ba',
                    'occupied': '#0561d0',
                    'path': '#fe5400',
                    # 'tower': '#6bc614',
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
