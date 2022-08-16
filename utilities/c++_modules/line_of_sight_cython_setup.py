from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize

# Compile with `python line_of_sight_cython_setup.py build_ext --inplace`
# Can get cython from `pip install cython`
# Can get Windows compilation tools from Visual Studio 2019 build tools
# Follow: https://stackoverflow.com/a/50210015
setup(
    ext_modules=cythonize(
        Extension("line_of_sight_cython", ["line_of_sight_cython.pyx"], 
                  extra_compile_args=["/fp:fast", "/O2"],
                  language="c"),
    language_level="3"),
)
