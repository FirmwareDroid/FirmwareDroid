# Python


import os
import uuid
import logging
import re
from django.utils.text import get_valid_filename
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from model.StoreSetting import get_active_store_by_index
from django.conf import settings

ALLOWED_EXTENSIONS = [".zip", ".tar", ".gz", ".bz2", ".md5", ".lz4", ".tgz", ".rar", ".7z", ".lzma", ".xz", ".ozip", ".apk"]
ALLOWED_TYPES = ["firmware", "apk"]
MAX_FILE_SIZE = 1024 * 1024 * 1024 * 10 # 10GB

def sanitize_filename(filename):
    valid_name = get_valid_filename(filename)
    safe_name = os.path.basename(valid_name)
    return safe_name

class FileUploadView(ViewSet):
    permission_classes = [IsAuthenticated]

    @action(methods=['post'], detail=False, url_path='upload', url_name='upload')
    def upload(self, request, *args, **kwargs):
        logging.info(f"Request Headers: {request.headers}")
        logging.info(f"Request Data: {request.data}")
        try:
            file_type = request.data.get('type', None)
            if not file_type or str(file_type).strip() not in ALLOWED_TYPES:
                return Response(
                    {'error': f'Invalid type parameter. Allowed types: {", ".join(ALLOWED_TYPES)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate storage_index
            storage_index_raw = request.data.get('storage_index', 0)
            if not re.match(r'^\d+$', str(storage_index_raw)):
                return Response(
                    {'error': 'Invalid storage_index. Must be a positive integer.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            storage_index = int(storage_index_raw)

            # Check if file was provided
            if 'file' not in request.FILES:
                return Response(
                    {'error': 'No file provided. Please include a file with key "file".'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            file = request.FILES['file']

            if file.size == 0:
                return Response(
                    {'error': 'Uploaded file is empty.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if file.size > MAX_FILE_SIZE:
                return Response(
                    {'error': f'File too large. Max size is {MAX_FILE_SIZE // (1024 * 1024)}MB.'},
                    status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
                )

            safe_filename = sanitize_filename(file.name)
            if not safe_filename or len(safe_filename.strip()) == 0:
                return Response(
                    {'error': 'Invalid filename.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            file_extension = None
            for ext in ALLOWED_EXTENSIONS:
                if safe_filename.lower().endswith(ext.lower()):
                    file_extension = ext
                    break
            if not file_extension:
                return Response(
                    {'error': f'File type not supported. Allowed extensions: {", ".join(ALLOWED_EXTENSIONS)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if safe_filename.lower().endswith('.apk') and file_type != 'apk':
                return Response(
                    {'error': 'APK files must be uploaded with type "apk".'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                store_setting = get_active_store_by_index(storage_index)
                store_paths = store_setting.get_store_paths()

                if file_type == ALLOWED_TYPES[0]:
                    upload_path = str(store_paths['FIRMWARE_FOLDER_IMPORT'])
                elif file_type == ALLOWED_TYPES[1]:
                    upload_path = str(store_paths['ANDROID_APP_IMPORT'])
                else:
                    upload_root_dir_path = store_paths['UPLOADS']
                    type_dir = file_type
                    unique_folder_name = str(uuid.uuid4())
                    upload_path = str(os.path.join(upload_root_dir_path, type_dir, unique_folder_name))

            except (ValueError, KeyError) as e:
                logging.error(f"Storage configuration error: {e}")
                if settings.DEBUG:
                    return Response(
                        {'error': f'Storage configuration error: {str(e)}'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                else:
                    return Response({'error': 'Failed to save file'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            os.makedirs(upload_path, exist_ok=True)

            file_path = os.path.join(upload_path, safe_filename)

            try:
                with open(file_path, 'wb') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)
                os.chmod(file_path, 0o600)  # Restrict file permissions
            except IOError as e:
                logging.error(f"Error writing file {file_path}: {e}")
                if settings.DEBUG:
                    return Response(
                        {'error': f'Failed to save file: {str(e)}'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                else:
                    return Response({'error': 'Failed to save file'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            logging.info(f"File uploaded: {safe_filename} to {file_path}")

            return Response({
                'success': True,
                'message': 'File uploaded successfully.',
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logging.error(f"Error uploading file: {str(e)}")
            if settings.DEBUG:
                return Response(
                    {'error': f'Internal server error: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            else:
                return Response({'error': 'Failed to save file'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)