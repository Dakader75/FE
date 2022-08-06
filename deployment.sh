# deployment script
# version
python utilities/bump_ver.py
# editor build
source ./venv_editor/Scripts/activate
./utilities/build_tools/editor_build.sh
# Now there should be ./lt_editor folder at ..
python utilities/build_tools/zipify.py ../lt_editor
# generic engine build
source ./venv/Scripts/activate
./utilities/build_tools/generic_engine_build.sh
# Now there should be ./lt_engine folder at ..
python utilities/build_tools/zipify.py ../lt_engine
