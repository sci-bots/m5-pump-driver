# # Configuration

# For each pump and valve:
#  - `addr`: I2C address of corresponding Grove motor control board
#  - `index`: output index (0-3) within the Grove motor control board
address_map = {
    'a': {'addr': 17, 'index':  0},
    'b': {'addr': 17, 'index':  1},
    'c': {'addr': 17, 'index':  2},
    'd': {'addr': 18, 'index':  0},
    'e': {'addr': 18, 'index':  1},
    'f': {'addr': 18, 'index':  2},
    'g': {'addr': 18, 'index':  3},
    'h': {'addr': 16, 'index':  2},
    'i': {'addr': 16, 'index':  3},
    'j': {'addr': 17, 'index':  3},
    'k': {'addr': 15, 'index':  0},
    'l': {'addr': 15, 'index':  1},
    'm': {'addr': 15, 'index':  2},
    'n': {'addr': 16, 'index':  1},
    'o': {'addr': 16, 'index':  0},
    'p': {'addr': 15, 'index':  3}
}

DEFAULT_SETTINGS = {
    'L/pulse': 20e-6,
    'L/minute': 5e-3,
    'volume': 1e-3,  # Default pump volume (in liters)
}

# Valve paths: A=0, B=1
steps = [
    {'name': 'Rehydrate Lysate',
     'steps': [{'pump': 'c', 'label': 'H20 -> A', 'volume': 1e-3}]},
    {'name': 'Mix Lysate/reagents',
     'steps': [{'pump': 'f', 'label': 'A -> B'},
               {'pump': 'g', 'label': 'B -> A',
                'valves': [{'valve': 'm', 'path': 0}]}]},
    {'name': 'Rehydrate Wash Buffer',
     'steps': [{'pump': 'a', 'label': 'H20 -> WB', 'volume': 5e-3},
               {'pump': 'd', 'label': 'Mix WB',
                'valves': [{'valve': 'k', 'path': 0}]}]},
    {'name': 'Purification I',
     'steps': [{'pump': ['g', 'h'],  # Multiple concurrent pumps
                'label': 'B -> Beads 1',
                'valves': [{'valve': 'm', 'path': 1},
                           {'valve': 'o', 'path': 0},
                           {'valve': 'n', 'path': 0},
                           {'valve': 'p', 'path': 0}]}]},
]