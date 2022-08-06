# Build Script for lex talionis editor
# source ./venv_editor/Scripts/activate

cp ./utilities/build_tools/autoupdater.spec .
pyinstaller -y autoupdater.spec
rm -f autoupdater.spec
echo "Built Autoupdater! Now building main editor..."
cp ./utilities/build_tools/editor.spec .
pyinstaller -y editor.spec
rm -f editor.spec

rm -rf ../lt_editor
mkdir ../lt_editor
mv dist/lt_editor ../lt_editor/lt_editor
cp utilities/install/double_click_to_run.bat ../lt_editor
cp dist/autoupdater.exe ../lt_editor/lt_editor
cp autoupdater.py ../lt_editor/lt_editor
echo "Copying default lt project..."
cp -r default.ltproj ../lt_editor/lt_editor
echo "Copying lion throne lt project"
cp -r lion_throne.ltproj ../lt_editor/lt_editor

# Get version
version="0.1"
constants="./app/constants.py"
while IFS='=' read -r col1 col2
do
    echo "$col1"
    echo "$col2"
    if [ $col1 == "VERSION" ]
    then
        version=$col2
        version=${version:2:${#version}-3}
    fi
done < "$constants"
touch metadata.txt
echo "$version" > metadata.txt
cp metadata.txt ../lt_editor/lt_editor

# Now zip up directory
# rm -f "../$name.zip"
# backup="../$name_v${version}.zip"
# rm -f "$backup"
# 7z a "../$name.zip" "../$name"
# cp "../$name.zip" "$backup"

echo Done