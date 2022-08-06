# Build Script for lt_engine
# source ./venv/Scripts/activate
if [ "$#" -ne 1 ];
then 
    echo 'Error: expected one argument (name of the project)'
    exit 2
fi
name=$1

cp ./utilities/build_tools/engine.spec .
pyinstaller -y engine.spec "$name"
rm -f engine.spec

rm -rf "../$name"
mkdir "../$name"
# mkdir "../$name/$name"
mv "dist/$name" "../$name/$name"
# cp utilities/audio_dlls/* "../$name/$name"
# cp -r favicon.ico "../$name/$name"
cp utilities/install/double_click_to_play.bat "../$name"

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
cp metadata.txt "../$name/$name"

# Now zip up directory
# rm -f "../$name.zip"
# backup="../$name_v${version}.zip"
# rm -f "$backup"
# 7z a "../$name.zip" "../$name"
# cp "../$name.zip" "$backup"

echo Done