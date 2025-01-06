# historian
historian is a tool to organize PNGs, JPGs, MP4s, and MOVs into folders based on their date. For example, if you had the following:

## Example
```
my_folder/
    chinatown_2024/
        restaurant.png
        photo2.png
        recorded_2024_05.mp4
    20240508/
        IMG_2018_08_10.JPEG
    2022_04_12_29387462.jpg
    Screenshot of August 10th 2025.png
    VID_20240506_92837.MOV
    ...
```

Running `historian.py my_folder sorted/` would look through every file and use its filename or its metadata to turn that messy directory into:

```
sorted/
    2024_04_april/
        2022_04_12_d354a6.jpg
    2024_05_may/
        2024_05_06_a3dfa3.mov
        2024_05_08_a01ba0.jpg
    2024_08_april/
        2025_08_10_198a91.png 
    ...
```

## Installation and Requirements
For best results, please have at least 8GB of VRAM for the model used, `dolphin-llama3`:
1. Install [ollama](https://ollama.com/download)
2. pip install -r requirements.txt
3. `sudo apt-get install exiftool`

With that, you're ready to run `historian.py my_folder sorted/`.

## Specifics
Using the example above, a file would be moved from `my_folder` to `sorted` if and only if:
1. Through ollama analysis, the filename contains the date.
2. Or if the filename doesn't work, look to see if exiftool has the date. 

If neither method contains the date, the file remains untouched. 

However, if one of those methods did contain the date, it gets moved to the correct subdirectory in `sorted` in the following format:

```
YYYY_MM_DD_XXXXXX.EXT
```

Where YYYY is the four digit year, MM is the two digit month, DD is the two digit date, and XXXXXX is the trimmed md5 hash of the original filename. The hash only looks at the filename, not the extension:

```bash
/my/path/IMG_2025_06_01.png # Renamed to 2025_06_01_1eb4b5.png
/my/path2/IMG_2025_06_01.jpg # Renamed to 2025_06_01_1eb4b5.jpg
/root/IMG_2025_06_02.jpg # Renamed to 2025_06_02_53d30f.jpg
```

Finally, if in `my_folder` there was an image that was already in the format YYYY_MM_DD_XXXXXX.EXT exactly, it will simply get moved to `sorted` and not have its hash recalculated.





