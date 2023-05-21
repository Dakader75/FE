# Build Script for lex talionis editor
# source ./venv_editor/Scripts/activate

# cp ./utilities/build_tools/autoupdater.spec .
# pyinstaller -y autoupdater.spec
# rm -f autoupdater.spec
# echo "Built Autoupdater! Now building main editor..."
cp ./utilities/build_tools/editor.spec .
pyinstaller -y editor.spec
rm -f editor.spec

rm -rf ../lt_editor
mkdir ../lt_editor
mv dist/lt_editor ../lt_editor/lt_editor
cp utilities/install/double_click_to_run.bat ../lt_editor
# cp dist/autoupdater.exe ../lt_editor/lt_editor
# cp autoupdater.py ../lt_editor/lt_editor
echo "Copying default lt project..."
cp -r default.ltproj ../lt_editor/lt_editor

# Now zip up directory
# rm -f "../$name.zip"
# backup="../$name_v${version}.zip"
# rm -f "$backup"
# 7z a "../$name.zip" "../$name"
# cp "../$name.zip" "$backup"

echo Done