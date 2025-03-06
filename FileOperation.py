import tkinter as tk
from tkinter import simpledialog
from datetime import datetime

def refresh_listbox(directories_and_files, listbox):
    # Clear the listbox
    listbox.delete(0, tk.END)

    # Populate the listbox with updated directories and files
    for key, item in directories_and_files.items():
        listbox.insert(tk.END, item["name"])


def get_selected_file_id(listbox, listbox_items_id):
    selected_id = listbox.curselection()
    if selected_id:
        file_id = listbox_items_id[selected_id[0]]
        return file_id
    else:
        return None


def get_selected_folder_id(listbox, listbox_items_id):
    selected_id = listbox.curselection()
    if selected_id:
        return [selected_id[0]]
    else:
        return None


class FileOperation:
    @staticmethod
    def copy_file(listbox, listbox_items_id):
        # Get the ID of the selected file or directory
        file_id = get_selected_file_id(listbox, listbox_items_id)
        if file_id:
            return file_id
        return None

    @staticmethod
    def cut_file(listbox, listbox_items_id):
        # Get the ID of the selected file or directory
        file_id = get_selected_file_id(listbox, listbox_items_id)
        if file_id:
            return file_id
        return None

    @staticmethod
    def delete_file(directories_and_files, listbox, listbox_items_id):
        # Get the ID of the selected file or directory
        file_id = get_selected_file_id(listbox, listbox_items_id)
        if file_id:
            return file_id

    @staticmethod
    def rename_file(directories_and_files, listbox, listbox_items_id):
        # Get the ID of the selected file or directory
        file_id = get_selected_file_id(listbox, listbox_items_id)
        print(datetime.now().strftime('%H:%M:%S'), "file_id", file_id)
        if file_id:
            new_name = simpledialog.askstring("Rename", "Enter new name:")
            if new_name:
                print(datetime.now().strftime('%H:%M:%S'), f"Renaming file with ID {file_id} to {new_name}")
                # Add your rename logic here
                old_name = directories_and_files[file_id]["name"]
                if old_name:
                    return file_id, old_name, new_name

        return None, None, None

    @staticmethod
    def paste_file(directories_and_files, listbox, listbox_items_id):
        print(datetime.now().strftime('%H:%M:%S'), "Pasting file")
        # Add your paste logic here
        refresh_listbox(directories_and_files, listbox)

    @classmethod
    def get_folder_index(cls, listbox, listbox_items_id, folder_index):
        f_index = get_selected_folder_id(listbox, listbox_items_id)
        if f_index and f_index[0] in folder_index:
            file_id = get_selected_file_id(listbox, listbox_items_id)
            if file_id:
                return file_id
            else:
                return None
        else:
            return None

    @classmethod
    def get_download_file_id(cls, listbox, listbox_items_id):
        file_id = get_selected_file_id(listbox, listbox_items_id)
        return file_id

    @classmethod
    def move_file(cls, directories_and_files, listbox, listbox_items_id):
        pass

