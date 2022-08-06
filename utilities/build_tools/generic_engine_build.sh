# Build Script for generic lt_engine
# source ./venv/Scripts/activate

cp ./utilities/build_tools/generic_engine.spec .
pyinstaller -y generic_engine.spec lt_engine
rm -f generic_engine.spec

rm -rf ../lt_engine
mkdir ../lt_engine
mv dist/lt_engine ../lt_engine/lt_engine
# cp utilities/audio_dlls/* "../$name/$name"
# cp -r favicon.ico "../$name/$name"
cp utilities/install/double_click_to_play.bat ../lt_engine
# cp autoupdater.exe ../lt_engine/lt_engine
# cp autoupdater.py "../$name/$name"

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
cp metadata.txt ../lt_engine/lt_engine

# Now zip up directory
# rm -f "../$name.zip"
# backup="../$name_v${version}.zip"
# rm -f "$backup"
# 7z a "../$name.zip" "../$name"
# cp "../$name.zip" "$backup"

echo Done