import os

def get_library_path() -> str:
    """ Return the absolute path of the library already installed"""
    script_path = os.path.realpath(__file__)
    script_directory = os.path.dirname(script_path)
    return script_directory