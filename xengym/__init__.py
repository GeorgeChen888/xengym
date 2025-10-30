from pathlib import Path
PROJ_DIR = Path(__file__).resolve().parent
ASSET_DIR = PROJ_DIR / "assets"

from .render.robotScene import RobotScene as Xensim
from .main import main