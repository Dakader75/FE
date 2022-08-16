from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
# Compile with `python invert_surface_setup.py build_ext --inplace`
# Can get cython from `pip install cython`
# Can get Windows compilation tools from Visual Studio 2019 build tools
# Follow: https://stackoverflow.com/a/50210015

# To import from the engine
# from app.shaders.invert_surface import invert
setup(
    ext_modules=cythonize(
        Extension("invert_surface", ["invert_surface.pyx"],
                  extra_compile_args=["/fp:fast", "/O2"],
                  language="c"),
    language_level="3"),
)