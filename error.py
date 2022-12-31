import sys
import traceback

def print_e(e : Exception):
    traceback.print_exception(type(e), e, e.__traceback__, file=sys.stderr)