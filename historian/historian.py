"""historian

Usage:
  historian <source> <dest>
"""


from ollama import chat
from ollama import ChatResponse
from pydantic import BaseModel
from hashlib import md5
from datetime import datetime
from rich import print
from docopt import docopt
import shutil
import os
import re

class ContainsDate(BaseModel):
    contains_date: bool

class SpecificDate(BaseModel):
  year: int
  month: int
  day: int


def ask_gpt_json(prompt, model) -> str:
    response: ChatResponse = chat(model='dolphin-llama3', messages=[
      {
        'role': 'user',
        'content': prompt
      },
    ], 
    options={'temperature': 0},
    format=model.model_json_schema()
      )
    return model.model_validate_json(response.message.content)

def ask_gpt(prompt) -> str:
    response: ChatResponse = chat(model='dolphin-llama3', messages=[
      {
        'role': 'user',
        'content': prompt
      },
    ], 
    options={'temperature': 0})

    return response['message']['content']

def find_files(directory, extensions):
    matching_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                matching_files.append(os.path.join(root, file))
    return matching_files


def run_linux_command(command) -> str:
    import subprocess

    process = subprocess.run(command, shell=True, capture_output=True, text=True)
    return process.stdout

def get_filename_only(path) -> str:
    return os.path.splitext(os.path.basename(path))[0]

def get_filename_with_extension(path) -> str:
    return ''.join(os.path.splitext(os.path.basename(path)))

def get_a_date(filepath: str, metadata: str, name_of_tool: str):
    filename_has_date = ask_gpt_json('Output {contains_date: bool }' + f' only, where contains_date is either true or false depending on whether the string "{get_filename_with_extension(filepath)}" contains the date the file was created or not. You should be extremely sure of your answer. Valid dates in files contain the entire year (YYYY), month, and day.', ContainsDate)
    exiftool_has_date = ask_gpt_json('Output {contains_date: bool }' + f' only, where contains_date is either true or false depending on whether the {name_of_tool} output contains the date the file was created or not. You should be extremely sure of your answer. Valid dates in files contain the entire year (YYYY), month, and day. Here is the {name_of_tool} output:\n\n{metadata}', ContainsDate)

    exiftool_date = None
    filename_date = None

    if exiftool_has_date.contains_date:
        exiftool_date = ask_gpt_json(f'Output the date to this question: What date is this file from given this {name_of_tool} output? Answer in JSON ' + 'format {year: int, month: int, day: int}. Here is ' + 'the {name_of_tool} output: \n\n' + metadata, SpecificDate)

    if filename_has_date.contains_date:
        filename_date = ask_gpt_json('Output the date to this question: What date is this file from given only its filename? Answer JSON format {year: int, month: int, day: int}. Here is the filename: \n\n' + get_filename_only(filepath), SpecificDate)

    date: SpecificDate = None

    # Combine both to get the oldest:
    if exiftool_date and filename_date:
        #date = ask_gpt_json(f'Output the date to this question: What is the more reasonable date given that first date came from the metadata of a file and the second date is from the filename, {exiftool_date} or {filename_date}? Answer in JSON format ' + '{year: int, month: int, date: int}', SpecificDate)
        date = filename_date # Prefer what the filename says, its usually right
    elif filename_date:
        date = filename_date
    elif exiftool_date:
        date = exiftool_date

    print(get_filename_with_extension(filepath))
    print(f"filename thinks its {filename_date}")
    print(f"exiftool thinks its {exiftool_date}")

    return date


def rename_file(file_path: str, date: SpecificDate) -> str:
    # Extract directory, file name, and extension
    directory, original_file_name = os.path.split(file_path)
    name_without_extension, extension = os.path.splitext(original_file_name)

    # Generate truncated MD5 hash
    hash_object = md5(name_without_extension.encode())
    truncated_md5 = hash_object.hexdigest()[:15]

    # Create new file name
    new_file_name = f"{date.year:04d}_{date.month:02d}_{date.day:02d}_{truncated_md5}{extension}"
    new_file_path = os.path.join(directory, new_file_name)

    base, ext = os.path.splitext(new_file_path)
    new_file_path = base + ext.lower()

    if new_file_path.endswith('.jpeg'):
        new_file_path = new_file_path.replace('.jpeg', '.jpg')

    # Rename the file
    os.rename(file_path, new_file_path)

    return new_file_path


def extract_date(filepath):
    # Extract the filename from the filepath
    filename = filepath.split('/')[-1]
    
    # Match the filename format using regex
    match = re.match(r'(\d{4})_(\d{2})_(\d{2})_\w{15}\.\w+$', filename)
    
    if match:
        year, month, day = map(int, match.groups())
        return SpecificDate(year=year, month=month, day=day)
    else:
        return None


def move_file_to_sorted_folder(file_path, sorted_folder):
    # Extract the date from the filename
    filename = os.path.basename(file_path)
    date_str = filename[:10]  # YYYY_MM_DD
    
    # Parse the date
    date_obj = datetime.strptime(date_str, "%Y_%m_%d")
    
    # Create the destination folder name
    dest_folder = os.path.join(f"{sorted_folder}/", f"{date_obj.year}_{date_obj.month:02d}_{date_obj.strftime('%B').lower()}")
    
    # Create the destination folder if it doesn't exist
    os.makedirs(dest_folder, exist_ok=True)
    
    # Move the file
    shutil.move(file_path, os.path.join(dest_folder, filename))
    
    print(f"Moved {filename} to {dest_folder}")


def main():
    args = docopt(__doc__)
    directory = args["<source>"]
    sorted_folder = args["<dest>"]

    supported_extensions = [
        ".mp4",
        ".mov",
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".heic",
        ".heif",
        ".webp",
        ".avi",
        ".mkv",
        ".m4a",
        ".3gp",
        ".amr"
        ]
    capitalized_ext = [item.upper() for item in supported_extensions]
    supported_extensions.extend(capitalized_ext)
    
    files = find_files(directory, supported_extensions)

    for file in files:
        print("\n")
        date = extract_date(file)

        if date == None:
            print(f"[red]{file}[/red] is not processed.")
            out = run_linux_command(f'exiftool -CreateDate -s -s -s "{file}"')
            #out = run_linux_command(f'mediainfo "{file}"')
            date = get_a_date(file, out, "exiftool")
            if date == None:
                continue

            file = rename_file(file, date)
            print(f"The date for this file will be {date}")
            print(file)
        else:
            print(f"[cyan]{file}[/cyan] is processed, skipping analysis.")

        if date != None and not (date.year == 0 or date.month == 0 or date.day == 0) and not (date.year == -1 and date.month == -1 and date.day == -1):
            move_file_to_sorted_folder(file, sorted_folder)




