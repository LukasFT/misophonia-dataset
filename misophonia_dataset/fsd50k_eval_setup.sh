#!/bin/bash

FILES=("https://zenodo.org/records/4060432/files/FSD50K.eval_audio.z01?download=1" "https://zenodo.org/records/4060432/files/FSD50K.eval_audio.zip?download=1")

#Download files

for url in ${FILES[@]}; do
	filename=$(basename "$url")
	filename="${filename%%\?*}"

	echo "Downloading $filename..."

	aria2c -x 8 -s 8 -k 1M -c -d . -o "$filename" "$url"
done
