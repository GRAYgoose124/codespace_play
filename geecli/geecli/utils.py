from pathlib import Path
import logging


def init_logger(
    name: str = __name__,
    parent: str = None,
    root_dir: Path = Path(__file__).parent.parent,
    level: int = logging.INFO,
) -> logging.Logger:
    if parent is None:
        logging.basicConfig(level=level)
        logger = logging.getLogger(name)
    else:
        # make sub logger for this module
        logger = logging.getLogger(parent).getChild(name)

    logger.setLevel(level)
    fh = logging.FileHandler(root_dir / f"{level}-{name}.log")
    fh.setLevel(level)
    logger.addHandler(fh)

    return logger
