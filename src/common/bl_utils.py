import filecmp
import os
import shutil


def copy_folder(source_folder: str, destination_folder: str):
    for file in os.listdir(source_folder):
        if os.path.isdir(f"{source_folder}/{file}"):
            if not os.path.exists(f"{destination_folder}/{file}"):
                os.makedirs(f"{destination_folder}/{file}")
            copy_folder(f"{source_folder}/{file}", f"{destination_folder}/{file}")
        elif not os.path.exists(f"{destination_folder}/{file}") or not filecmp.cmp(
            f"{source_folder}/{file}", f"{destination_folder}/{file}"
        ):
            shutil.copy(f"{source_folder}/{file}", f"{destination_folder}/{file}")
