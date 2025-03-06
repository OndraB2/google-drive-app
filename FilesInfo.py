import json

import hashlib
import os
from datetime import datetime
DOWNLOAD_DIR = "Downloads"
JSON_FILE_PATH = "data.json"


def calculate_sha256(file_path):
    # Initialize the SHA-256 hash object
    sha256 = hashlib.sha256()

    # Open the file in binary mode and read it in chunks
    with open(file_path, 'rb') as file:
        # Read the file in small blocks of 4096 bytes
        for block in iter(lambda: file.read(4096), b''):
            # Update the hash object with the block of data
            sha256.update(block)

    # Get the hexadecimal representation of the hash
    sha256_hash = sha256.hexdigest()

    return sha256_hash


class FilesInfoOperation:
    # Load data from JSON file
    @staticmethod
    def load_data():
        try:
            with open(JSON_FILE_PATH, 'r') as json_file:
                data = json.load(json_file)
        except FileNotFoundError:
            data = []
        return data

    @staticmethod
    def get_file_path(file_name):
        return f"{DOWNLOAD_DIR}/{file_name}"

    def get_file_modified_time(self, file_name):
        # return os.path.getmtime(self.get_file_path(file_name))
        return calculate_sha256(self.get_file_path(file_name))

    # Function to add a new file
    def add_file(self, file_name, parent_dir):
        data = self.load_data()
        file_info = {
            "name": file_name,
            "parent_dir": parent_dir,
            # "sha256": calculate_sha256()
            "last_mod_time": self.get_file_modified_time(file_name)
        }
        data.append(file_info)
        with open(JSON_FILE_PATH, 'w') as json_file:
            json.dump(data, json_file, indent=4)
        print(datetime.now().strftime('%H:%M:%S'), f"File '{file_name}' added successfully.")

    # Function to update last_mod_time by file name
    def update_last_mod_time(self, file_name):
        data = self.load_data()
        for file_info in data:
            if file_info["name"] == file_name:
                new_last_mod_time = self.get_file_modified_time(file_name)
                file_info["last_mod_time"] = new_last_mod_time
                with open(JSON_FILE_PATH, 'w') as json_file:
                    json.dump(data, json_file, indent=4)
                print(datetime.now().strftime('%H:%M:%S'), f"Last modification time for file '{file_name}' updated to '{new_last_mod_time}'.")
                return
        print(datetime.now().strftime('%H:%M:%S'), f"File '{file_name}' not found.")

    def rename_downloaded_file(self, old_name, new_name):
        try:
            os.rename(self.get_file_path(old_name), self.get_file_path(new_name))
            print(f"File '{old_name}' renamed to '{new_name}' successfully.")
        except Exception as e:
            print(datetime.now().strftime('%H:%M:%S'), f"An error occurred: {e}")

    def update_name(self, old_name, new_name):
        data = self.load_data()
        for file_info in data:
            if file_info["name"] == old_name:
                file_info["name"] = new_name
                with open(JSON_FILE_PATH, 'w') as json_file:
                    json.dump(data, json_file, indent=4)
                print(datetime.now().strftime('%H:%M:%S'), f"File renamed from '{old_name}' to '{new_name}'.")
                self.rename_downloaded_file(old_name, new_name)
                return
        # print(datetime.now().strftime('%H:%M:%S'), f"Info: File '{old_name}' not found, not downloaded file.")

    # Function to delete a file by its name
    def delete_file_by_name(self, file_name):
        data = self.load_data()
        for file_info in data:
            if file_info['name'] == file_name:
                # Get information about the file before deleting
                file_info_to_delete = file_info.copy()
                # Delete the file from the data
                data.remove(file_info)
                with open(JSON_FILE_PATH, 'w') as json_file:
                    json.dump(data, json_file, indent=4)
                print(datetime.now().strftime('%H:%M:%S'), f"File '{file_name}' found and deleted.")
                return file_info_to_delete
        print(datetime.now().strftime('%H:%M:%S'), f"File '{file_name}' not found.")
        return None
