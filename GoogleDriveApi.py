from __future__ import print_function

import os.path
import io

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from datetime import datetime

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive']
MIME_TYPE_FOLDER = 'application/vnd.google-apps.folder'


class GoogleDriveApi:
    creds = None
    is_root_dir = True
    file_id_to_copy = None
    file_id_to_cut = None

    def __init__(self):
        self.auth()
        self.parent_dir_stack = []

    def get_instance(self):
        return self

    def get_service(self):
        return build('drive', 'v3', credentials=self.creds)
    def is_root_directory(self):
        return self.is_root_dir

    def get_actual_folder(self):
        return self.parent_dir_stack[-1]

    def navigate_up(self):
        # Function to handle navigating up one directory
        if len(self.parent_dir_stack) > 0:
            _folder_id = self.parent_dir_stack.pop()
            parent_folder_id = self.get_actual_folder()
            self.is_root_dir = False
            return parent_folder_id
        else:
            # Already at the root directory
            self.is_root_dir = True
            return "root"

    def auth(self):
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                self.creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())

    def get_all_files(self, folder_id: str, is_going_up: bool, is_staying: bool):
        results = {}
        if folder_id == "root":
            self.is_root_dir = True
        else:
            self.is_root_dir = False
        try:
            service = build('drive', 'v3', credentials=self.creds)
            q = f"'{folder_id}' in parents and trashed=false"
            # Call the Drive v3 API
            response = service.files().list(q=q,
                                            spaces='drive',
                                            fields='nextPageToken, files(id, name, mimeType, modifiedTime)').execute()

            items = response.get('files', [])
            if not items:
                print(datetime.now().strftime('%H:%M:%S'), 'No files found.')

            for item in items:
                results[item['id']] = {'name': item['name'], 'mimeType': item['mimeType'], "modifiedTime": item['modifiedTime']}

            # Store the previous folder ID in the stack
            if not is_going_up and not is_staying:
                print(datetime.now().strftime('%H:%M:%S'), "pridavam", folder_id)
                self.parent_dir_stack.append(folder_id)

            print(datetime.now().strftime('%H:%M:%S'), self.parent_dir_stack)
            return results

        except HttpError as error:
            # TODO(developer) - Handle errors from drive API.
            print(datetime.now().strftime('%H:%M:%S'), f'An error occurred: {error}')
            return []

    def download_file(self, real_file_id):
        try:
            # create drive api client
            service = build('drive', 'v3', credentials=self.creds)

            file_id = real_file_id

            request = service.files().get_media(fileId=file_id)
            print(datetime.now().strftime('%H:%M:%S'), "request", request)
            file = io.BytesIO()
            downloader = MediaIoBaseDownload(file, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print(datetime.now().strftime('%H:%M:%S'), F'Download {int(status.progress() * 100)}.')

        except HttpError as error:
            print(datetime.now().strftime('%H:%M:%S'), F'An error occurred: {error}')
            file = None

        return file.getvalue()

    def _check_file_in_folder(self, file_name, folder_id):
        try:
            # Create Drive API client
            service = build('drive', 'v3', credentials=self.creds)

            # Check if the file already exists in the specified folder on Google Drive
            query = f"name='{file_name}' and '{folder_id}' in parents and trashed=false"
            existing_files = service.files().list(q=query).execute()

            if existing_files.get('files'):
                # If the file exists in the specified folder, return True
                return existing_files['files'][0]['id'], True
            else:
                # If the file doesn't exist in the specified folder, return False
                return -1, False

        except HttpError as error:
            print(datetime.now().strftime('%H:%M:%S'), F'An error occurred: {error}')
            return -1, False

    def upload_file(self, file_path, file_metadata):
        try:
            # create drive api client
            service = build('drive', 'v3', credentials=self.creds)

            media = MediaFileUpload(file_path)

            file_id, file_exists = self._check_file_in_folder(file_metadata["name"], file_metadata["parents"][0])
            if file_exists:
                file = service.files().update(fileId=file_id, media_body=media).execute()
                print(datetime.now().strftime('%H:%M:%S'), f'File updated! File ID: {file.get("id")}')
            else:
                file = service.files().create(body=file_metadata, media_body=media,
                                              fields='id').execute()
                print(datetime.now().strftime('%H:%M:%S'), f'File created on disc! File ID: {file.get("id")}')

        except HttpError as error:
            print(datetime.now().strftime('%H:%M:%S'), F'An error occurred: {error}')
            file = None

        return file.get('id')

    def rename_file(self, file_id, new_name):
        try:
            service = build('drive', 'v3', credentials=self.creds)
            # Get the file metadata
            file_metadata = {'name': new_name}

            # Update the file with the new name
            updated_file = service.files().update(fileId=file_id, body=file_metadata).execute()

            print(datetime.now().strftime('%H:%M:%S'), f'File renamed! New name: {updated_file.get("name")}')
        except Exception as error:
            print(datetime.now().strftime('%H:%M:%S'), f'An error occurred - renaming file GDAPI: {error}')

    def delete_file(self, file_id):
        try:
            service = build('drive', 'v3', credentials=self.creds)
            # Delete the file by its ID
            service.files().delete(fileId=file_id).execute()
            print(datetime.now().strftime('%H:%M:%S'), f"File with ID '{file_id}' deleted successfully.")
        except Exception as e:
            print(datetime.now().strftime('%H:%M:%S'), f"An error occurred - deleting file GDAPI: {e}")

    def set_file_id_to_copy(self, file_id):
        print(datetime.now().strftime('%H:%M:%S'), "Copying this file", file_id)
        self.file_id_to_cut = None
        self.file_id_to_copy = file_id

    def set_file_id_to_cut(self, file_id):
        print(datetime.now().strftime('%H:%M:%S'), "Cutting this file", file_id)
        self.file_id_to_copy = None
        self.file_id_to_cut = file_id

    def get_mime_type(self, file_id):
        service = build('drive', 'v3', credentials=self.creds)
        # Get the metadata of the source folder
        file = service.files().get(fileId=file_id).execute()

        return file.get("mimeType", None)

    def paste_file_to_folder(self, destination_folder_id):
        try:
            service = build('drive', 'v3', credentials=self.creds)
            # Copy the file to the new folder (add it to the new parent)
            copied_file = service.files().copy(fileId=self.file_id_to_copy or self.file_id_to_cut,
                                               body={"parents": [destination_folder_id]}).execute()

            if self.file_id_to_cut:  # delete source file
                self.delete_file(self.file_id_to_cut)

            print(datetime.now().strftime('%H:%M:%S'),
                  f"File with ID '{self.file_id_to_copy}' copied to folder with ID '{destination_folder_id}' successfully. New file ID: {copied_file.get('id')}")
        except Exception as e:
            print(datetime.now().strftime('%H:%M:%S'), f"An error occurred: {e}")

    def paste_folder(self, source_folder_id, first_call, destination_folder_id=None):  # after copy or after cut
        try:
            service = build('drive', 'v3', credentials=self.creds)
            # Get the metadata of the source folder
            source_folder = service.files().get(fileId=source_folder_id).execute()

            # Create a new folder with the same name in the destination folder
            new_folder_metadata = {
                'name': source_folder['name'],
                'parents': [destination_folder_id] if destination_folder_id else [],
                'mimeType': MIME_TYPE_FOLDER
            }
            new_folder = service.files().create(body=new_folder_metadata, fields='id').execute()

            # Get the list of files and subfolders in the source folder
            results = service.files().list(q=f"'{source_folder_id}' in parents",
                                           fields="files(id, name, mimeType)").execute()
            items = results.get('files', [])

            if items == []:
                print("empty")
            # Copy each file and recursively copy subfolders
            for item in items:
                print(item["name"], item['mimeType'])
                if item['mimeType'] == MIME_TYPE_FOLDER:
                    # If it's a subfolder, recursively copy it
                    self.paste_folder(item['id'], False, new_folder['id'])
                else:
                    # If it's a file, copy it to the new folder
                    service.files().copy(fileId=item['id'], body={"parents": [new_folder['id']]}).execute()

        except Exception as e:
            print(f"An error occurred: {e}")

    def move_file(self, file_id, new_parent_folder_id):
        try:
            service = build('drive', 'v3', credentials=self.creds)
            # Retrieve the file's metadata to get the current parents
            file_metadata = service.files().get(fileId=file_id, fields='parents').execute()

            # Remove the file from its current parent folder(s)
            previous_parents = ",".join(file_metadata.get('parents'))
            service.files().update(fileId=file_id, removeParents=previous_parents).execute()

            # Add the file to the new parent folder
            service.files().update(fileId=file_id, addParents=new_parent_folder_id).execute()

            print(f"File with ID '{file_id}' moved to folder with ID '{new_parent_folder_id}' successfully.")
        except Exception as e:
            print(f"An error occurred: {e}")
