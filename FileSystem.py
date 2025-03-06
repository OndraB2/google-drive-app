import os
import threading
import tkinter as tk
import time
from tkinter import messagebox, filedialog
from tkinter import simpledialog
from tkinter import Menu

from Cache import CachingFiles
from FileOperation import FileOperation
from FilesInfo import FilesInfoOperation
from GoogleDriveApi import GoogleDriveApi, MIME_TYPE_FOLDER
from datetime import datetime
class LoadingSpinner(tk.Canvas):
    def __init__(self, master=None, **kwargs):
        tk.Canvas.__init__(self, master, **kwargs)
        self.spinner_radius = 20
        self.spinner_color = 'blue'
        self.angle = 0
        self.update_spinner()

    def update_spinner(self):
        self.delete("spinner")
        x = self.winfo_width() // 2
        y = self.winfo_height() // 2
        self.create_arc(x - self.spinner_radius, y - self.spinner_radius, x + self.spinner_radius,
                        y + self.spinner_radius, start=self.angle, extent=60, style=tk.ARC, outline=self.spinner_color,
                        tags="spinner")
        self.angle += 30
        self.angle %= 360
        self.after(100, self.update_spinner)  # Update every 100 milliseconds


class OnlineFileManager(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.directories_and_files = {}
        self.listbox_items_id = []
        self.folder_index = []
        self.gdapi = GoogleDriveApi()
        self.files_info = FilesInfoOperation()
        self.download_path = "Downloads/"
        self.cache_path = "Cache/"
        self.cache_files = CachingFiles()

        self.title("Online File Manager")

        self.up_button = tk.Button(self, text="Directory Up", command=self.go_up_directory, state=tk.DISABLED)
        self.up_button.pack(padx=10, pady=10)

        # Create a listbox to display directories and files
        self.listbox = tk.Listbox(self, selectmode=tk.SINGLE, height=20, width=50)
        self.listbox.pack(padx=10, pady=10)

        self.get_all_files()
        self.check_cached_files()

        # Populate the listbox with directories and files

        # Create a right-click context menu
        self.context_menu = Menu(self, tearoff=0)
        self.context_menu.add_command(label="Copy", command=self.copy_file)
        self.context_menu.add_command(label="Cut", command=self.cut_file)
        # self.context_menu.add_command(label="Move", command=self.move_file)
        self.context_menu.add_command(label="Delete", command=self.delete_file)
        self.context_menu.add_command(label="Rename", command=self.rename_file)
        self.context_menu.add_command(label="Download", command=self.download_file)
        self.context_menu.add_command(label="Cache", command=self.cache_file)
        self.context_menu.add_command(label="UnCache", command=self.uncache_file)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Paste", command=self.paste_file)

        # Button to select a file for upload
        self.upload_button = tk.Button(self, text="Upload File", command=self.upload_file)
        self.upload_button.pack(padx=10, pady=10)

        self.loading_spinner = LoadingSpinner(self, width=100, height=100)
        # self.loading_spinner.pack(expand=True)
        self.show_spinner = tk.BooleanVar(value=False)
        # self.loading_spinner.pack_forget()

        # Bind right-click event to the listbox
        self.listbox.bind("<Button-3>", self.show_context_menu)

        self.listbox.bind("<Double-Button-1>", self.open_folder)

    def get_instance(self):
        return self

    def toggle_spinner(self):
        self.show_spinner.set(not self.show_spinner.get())
        if self.show_spinner.get():
            self.loading_spinner.pack(expand=True)
        else:
            self.loading_spinner.pack_forget()

    def go_up_directory(self):
        # self.gdapi.navigate_up()    # actual directory
        parent_dir = self.gdapi.navigate_up()
        self.get_all_files(parent_dir, is_going_up=True)

    def set_up_button_state(self, is_root):
        # Enable or disable the 'Up' button based on the provided boolean value
        if is_root:
            self.up_button.config(state=tk.DISABLED)
        else:
            self.up_button.config(state=tk.NORMAL)

    def get_all_files(self, folder_id="root", is_going_up=False, is_staying=False):
        self.gdapi.parent_dir = folder_id
        self.listbox_items_id = []
        self.folder_index = []
        self.directories_and_files = self.gdapi.get_all_files(folder_id=folder_id, is_going_up=is_going_up, is_staying=is_staying)
        self.put_data_to_listbox()
        self.set_up_button_state(self.gdapi.is_root_directory())

    def put_data_to_listbox(self):
        self.listbox.delete(0, tk.END)
        if self.directories_and_files:
            for id, item in self.directories_and_files.items():
                self.listbox.insert(tk.END, item["name"])

                # Store the ID as a hidden tag for the listbox item
                self.listbox_items_id.append(id)

                if item.get("mimeType") == "application/vnd.google-apps.folder":
                    listbox_index = len(self.listbox_items_id) - 1
                    self.folder_index.append(listbox_index)
                    self.listbox.itemconfig(listbox_index, {'bg': '#F0BF2E'})  # Light gray background for directories

    def refresh_listbox(self):
        # Clear the listbox
        self.listbox.delete(0, tk.END)

        # Populate the listbox with updated directories and files
        for item in self.directories_and_files:
            self.listbox.insert(tk.END, item["name"])

    def show_context_menu(self, event):
        # Show the context menu at the right-click location
        self.context_menu.post(event.x_root, event.y_root)

    def open_folder(self, _event):
        folder_id = FileOperation.get_folder_index(self.listbox, self.listbox_items_id, self.folder_index)
        if folder_id:
            self.get_all_files(folder_id)

    def copy_file(self):
        file_id = FileOperation.copy_file(self.listbox, self.listbox_items_id)
        if file_id:
            self.gdapi.set_file_id_to_copy(file_id)

    def cut_file(self):
        file_id = FileOperation.copy_file(self.listbox, self.listbox_items_id)
        if file_id:
            self.gdapi.set_file_id_to_cut(file_id)

    def cache_file(self):
        file_id = FileOperation.get_download_file_id(self.listbox, self.listbox_items_id)
        if file_id and not self.cache_files.file_cached(file_id):
            file_info = self.directories_and_files.get(file_id)
            bytes_file = self.gdapi.download_file(file_id)
            file_path = f"{self.cache_path}{file_info.get('name')}"
            with open(file_path, "wb") as f:
                f.write(bytes_file)
            self.cache_files.add_file(file_id, file_info.get('name', None), self.gdapi.get_actual_folder())

    def uncache_file(self):
        file_id = FileOperation.get_download_file_id(self.listbox, self.listbox_items_id)
        if file_id and self.cache_files.file_cached(file_id):
            file_id_to_delete = self.cache_files.delete_file_by_id(file_id)
            file_info = self.directories_and_files.get(file_id)
            file_path = f"{self.cache_path}{file_info.get('name')}"
            os.remove(file_path)

    def move_file(self):
        file_id, destination_folder_id = FileOperation.move_file(self.directories_and_files, self.listbox, self.listbox_items_id)
        if file_id and destination_folder_id:
            self.gdapi.set_file_id_to_cut(file_id)

    def delete_file(self):
        file_id = FileOperation.delete_file(self.directories_and_files, self.listbox, self.listbox_items_id)
        if file_id:
            self.gdapi.delete_file(file_id)
            self.get_all_files(self.gdapi.get_actual_folder(), is_staying=True)
            print(datetime.now().strftime('%H:%M:%S'), f"Deleting file with ID: {file_id}")
        else:
            print(datetime.now().strftime('%H:%M:%S'), "Error, dont have enough info to delete file")

    def rename_file(self):
        file_id, old_name, new_name = FileOperation.rename_file(self.directories_and_files, self.listbox, self.listbox_items_id)
        if file_id and old_name and new_name:
            self.files_info.update_name(old_name, new_name)
            self.gdapi.rename_file(file_id, new_name)
            self.get_all_files(self.gdapi.get_actual_folder(), is_staying=True)
        else:
            print(datetime.now().strftime('%H:%M:%S'), "Error, dont have enough info to rename file")

    def download_file(self):
        self.toggle_spinner()
        print(datetime.now().strftime('%H:%M:%S'), "stahuju")
        file_id = FileOperation.get_download_file_id(self.listbox, self.listbox_items_id)
        if file_id:
            print(datetime.now().strftime('%H:%M:%S'), "stahuju toto", file_id)
            file_info = self.directories_and_files.get(file_id)
            bytes_file = self.gdapi.download_file(file_id)
            file_path = f"{self.download_path}{file_info.get('name')}"
            with open(file_path, "wb") as f:
                f.write(bytes_file)

            self.files_info.add_file(file_name=file_info.get('name'), parent_dir=self.gdapi.get_actual_folder())
        self.toggle_spinner()

    def upload_file(self):
        # Open a file dialog to select a file for upload
        file_path = filedialog.askopenfilename()
        if file_path:
            print(datetime.now().strftime('%H:%M:%S'), "file_path", file_path)
            self.toggle_spinner()
            # Get the file name from the path
            file_name = file_path.split("/")[-1]
            print(datetime.now().strftime('%H:%M:%S'), "file_name", file_name)
            # Upload the selected file to Google Drive
            file_metadata = {
                'name': file_name,
                'parents': [self.gdapi.get_actual_folder()]
            }
            self.gdapi.upload_file(file_path, file_metadata)
            self.get_all_files(self.gdapi.get_actual_folder(), is_staying=True)
            self.toggle_spinner()



    def paste_file(self):
        print(datetime.now().strftime('%H:%M:%S'), "Pasting file")
        file_id = self.gdapi.file_id_to_copy or self.gdapi.file_id_to_cut
        if file_id:
            mime_type = self.gdapi.get_mime_type(file_id)
            if mime_type == MIME_TYPE_FOLDER:
                self.gdapi.paste_folder(file_id, True, self.gdapi.get_actual_folder())
            else:
                self.gdapi.paste_file_to_folder(self.gdapi.get_actual_folder())
            if self.gdapi.file_id_to_cut:
                self.gdapi.delete_file(file_id)
                self.gdapi.set_file_id_to_cut(None)
            self.get_all_files(self.gdapi.get_actual_folder(), is_staying=True)

    def check_cached_files(self):
        data = self.cache_files.load_data()
        for file_info in data:
            saved_last_mod_time = self.cache_files.get_file_modified_time(file_info['file_name'])

            service = self.gdapi.get_service()
            file = service.files().get(fileId=file_info['file_id'], fields='id, name, modifiedTime').execute()

            # Získání informací o souboru
            google_drive_last_mod_time = file.get('modifiedTime')
            datetime_object = datetime.fromisoformat(google_drive_last_mod_time[:-1])  # Removing 'Z' at the end of the string

            # Convert the datetime object to a timestamp (in seconds since the Unix epoch)
            google_timestamp = datetime_object.timestamp()
            if saved_last_mod_time > google_timestamp:
                file_metadata = {
                    'name': file_info['file_name'],
                    'parents': [file_info["parent_dir"]]
                }
                self.gdapi.upload_file(self.cache_files.get_file_path(file_info['file_name']), file_metadata)
                print(f"update of {file_info['file_id']}")




class FileHandler:
    def __init__(self, ofm):
        self.files_info_op = FilesInfoOperation()
        self.ofm = ofm

    def monitor_folder_in_thread(self):
        try:
            while True:
                self.check_modified()
                time.sleep(5)

        except KeyboardInterrupt:
            return

    def check_modified(self):
        files_json_data = self.files_info_op.load_data()

        for file_info in files_json_data:
            file_name = file_info["name"]
            parent_dir = file_info["parent_dir"]
            last_mod_time = file_info["last_mod_time"]

            saved_last_mod_time = self.files_info_op.get_file_modified_time(file_name)

            if saved_last_mod_time != last_mod_time:
                self.ofm.toggle_spinner()
                file_path = self.files_info_op.get_file_path(file_name)
                # Get the file name from the path
                print(datetime.now().strftime('%H:%M:%S'), "zmena v", file_name)
                # Upload the selected file to Google Drive
                file_metadata = {
                    'name': file_name,
                    'parents': [parent_dir]
                }
                self.ofm.gdapi.upload_file(file_path, file_metadata)
                self.ofm.get_all_files(self.ofm.gdapi.get_actual_folder(), is_staying=True)
                self.files_info_op.update_last_mod_time(file_name)
                self.ofm.toggle_spinner()




if __name__ == "__main__":
    # Specify the local folder to monitor (e.g., "Downloads")
    local_folder_path = os.path.expanduser("Downloads")  # Replace with the path to your local folder
    app = OnlineFileManager()

    file_monitoring = FileHandler(app)

    # Create a thread for monitoring the folder
    monitoring_thread = threading.Thread(target=file_monitoring.monitor_folder_in_thread)
    monitoring_thread.daemon = True  # Allow the program to exit even if the thread is still running
    monitoring_thread.start()

    app.mainloop()
