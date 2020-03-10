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
     'steps': [{'pump': 'c',
                'label': 'H2O -> A',
                'volume': 1e-3}]},
    {'name': 'Rehydrate Wash Buffer',
     'steps': [{'pump': 'a',
                'label': 'H2O -> WB',
                'volume': 5e-3},
               {'pump': 'd',
                'label': 'Mix WB',
                'pulses': 60,
                'valves': [{'valve': 'k', 'path': 0}]}]},
    {'name': 'Rehydrate Elution Buffer',
     'steps': [{'pump': 'b',
                'label': 'H2O -> EB',
                'volume': 2e-3},
               {'pump': 'e',
                'label': 'Mix EB',
                'pulses': 60,
                'valves': [{'valve': 'l', 'path': 0}]}]},
    {'name': 'Mix Lysate/reagents',
     'steps': [{'pump': 'f',
                'label': 'A -> B',
                'pulses': 125},
               {'pump': 'g',
                'label': 'B -> A',
                'pulses': 125,
                'valves': [{'valve': 'm', 'path': 0}]}]},
    {'name': 'Purification I',
     'steps': [{'pump': ['d', 'h', 'i'],  # Multiple concurrent pumps
                'label': 'WB -> Beads 1',
                'pulses': 375,
                'valves': [{'valve': 'k', 'path': 1},
                           {'valve': 'n', 'path': 1},
                           {'valve': 'p', 'path': 0},]}]},
    {'name': 'Purification II',
     'steps': [{'pump': ['g', 'h', 'i'],  # Multiple concurrent pumps
                'label': 'B -> Beads 1',
                'pulses': 375,
                'valves': [{'valve': 'm', 'path': 1},
                           {'valve': 'o', 'path': 0},
                           {'valve': 'n', 'path': 0},
                           {'valve': 'p', 'path': 0}]}]},
   {'name': 'Purification III',
     'steps': [{'pump': ['e', 'h', 'i', 'j'],  # Multiple concurrent pumps
                'label': 'EB -> Beads 2',
                'pulses': 375,
                'valves': [{'valve': 'l', 'path': 1},
                           {'valve': 'o', 'path': 1},
                           {'valve': 'n', 'path': 0},
                           {'valve': 'p', 'path': 1}]}]},
]