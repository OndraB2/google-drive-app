import json
import os
from datetime import datetime, timezone

CACHE_FILE_PATH = "cache.json"
CACHE_DIR = "Cache"


class CachingFiles:
    @staticmethod
    def get_file_path(file_name):
        return f"{CACHE_DIR}/{file_name}"

    # Load data from JSON file
    @staticmethod
    def load_data():
        try:
            with open(CACHE_FILE_PATH, 'r') as json_file:
                data = json.load(json_file)
        except FileNotFoundError:
            data = []
        return data

    def get_file_modified_time(self, file_name):
        mod_ts = os.path.getmtime(self.get_file_path(file_name))
        # Convert local modified time to UTC
        utc_modified_time = datetime.fromtimestamp(mod_ts, tz=timezone.utc)

        # Get the timestamp of the UTC time
        return utc_modified_time.timestamp()

    def file_cached(self, file_id):
        data = self.load_data()
        return any(file_info['file_id'] == file_id for file_info in data)

    def add_file(self, file_id, file_name, parent_dir):
        data = self.load_data()
        file_id_exists = any(file_info['file_id'] == file_id for file_info in data)
        if not file_id_exists:
            file_info = {
                "file_id": file_id,
                "file_name": file_name,
                "parent_dir": parent_dir,
                "parent_dir": parent_dir,
                "last_mod_time": self.get_file_modified_time(file_name)
            }
            data.append(file_info)
            with open(CACHE_FILE_PATH, 'w') as json_file:
                json.dump(data, json_file, indent=4)
            print(datetime.now().strftime('%H:%M:%S'), f"CACHE - File '{file_id}' added successfully.")
            return file_id
        print(datetime.now().strftime('%H:%M:%S'), f"CACHE - File '{file_id}' already cached.")
        return None

    # # Function to update last_mod_time by file name
    # def update_last_mod_time(self, file_name):
    #     data = self.load_data()
    #     for file_info in data:
    #         if file_info["name"] == file_name:
    #             new_last_mod_time = self.get_file_modified_time(file_name)
    #             file_info["last_mod_time"] = new_last_mod_time
    #             with open(JSON_FILE_PATH, 'w') as json_file:
    #                 json.dump(data, json_file, indent=4)
    #             print(datetime.now().strftime('%H:%M:%S'), f"Last modification time for file '{file_name}' updated to '{new_last_mod_time}'.")
    #             return
    #     print(datetime.now().strftime('%H:%M:%S'), f"File '{file_name}' not found.")

    # Function to delete a file by its name sds
    def delete_file_by_id(self, file_id):
        data = self.load_data()
        for file_info in data:
            if file_info['file_id'] == file_id:
                # Get information about the file before deleting
                file_info_to_delete = file_info.copy()
                # Delete the file from the data
                data.remove(file_info)
                with open(CACHE_FILE_PATH, 'w') as json_file:
                    json.dump(data, json_file, indent=4)
                print(datetime.now().strftime('%H:%M:%S'), f"CACHE - File '{file_id}' found and deleted.")
                return file_info_to_delete
        print(datetime.now().strftime('%H:%M:%S'), f"CACHE - File '{file_id}' not cached.")
        return None


