import random
import os

PRIMARY_COLOR = "#0072ff"
HOVER_COLOR   = "#2892ff"
SUCCESS_COLOR = "#4caf50"
ERROR_COLOR   = "#f44336"

COLORS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "colors.txt")

with open(COLORS_PATH, "r") as f:
    RANDOM_COLORS = [line.strip() for line in f if line.strip()]




def random_color():
    return random.choice(RANDOM_COLORS)