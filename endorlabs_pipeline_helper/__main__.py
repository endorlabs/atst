from .main import *

Status.loglevel = Status.DEBUG
Status.debug("Test DEBUG")
Status.info("Test INFO")
Status.info("Continued INFO line", cont=True)