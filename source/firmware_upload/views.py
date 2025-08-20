# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
from django.http import JsonResponse
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from model.StoreSetting import get_active_store_by_index

# Allowed firmware file extensions based on firmware_importer.py
ALLOWED_FIRMWARE_EXTENSIONS = [".zip", ".tar", ".gz", ".bz2", ".md5", ".lz4", ".tgz", ".rar", ".7z", ".lzma", ".xz", ".ozip"]


class FirmwareUploadView(ViewSet):
    
    @action(methods=['post'], detail=False, url_path='upload', url_name='upload')
    def upload(self, request, *args, **kwargs):
        """
        Upload a firmware file to the firmware_import directory for processing.
        
        :param request: Django HTTP POST request with file in request.FILES
        Expected form data:
          - firmware_file: The firmware file to upload
          - storage_index: (optional) Storage index to use (defaults to 0)
        
        :return: JSON response with upload status and file information
        """
        try:
            # Check if file was provided
            if 'firmware_file' not in request.FILES:
                return Response(
                    {'error': 'No firmware file provided. Please include a file with key "firmware_file".'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            firmware_file = request.FILES['firmware_file']
            
            # Parse storage index with validation
            try:
                storage_index = int(request.data.get('storage_index', 0))
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Invalid storage_index. Must be a valid integer.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate file
            if firmware_file.size == 0:
                return Response(
                    {'error': 'Uploaded file is empty.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate filename
            if not firmware_file.name or len(firmware_file.name.strip()) == 0:
                return Response(
                    {'error': 'Invalid filename.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate file extension
            file_extension = None
            for ext in ALLOWED_FIRMWARE_EXTENSIONS:
                if firmware_file.name.lower().endswith(ext.lower()):
                    file_extension = ext
                    break
            
            if not file_extension:
                return Response(
                    {
                        'error': f'File type not supported. Allowed extensions: {", ".join(ALLOWED_FIRMWARE_EXTENSIONS)}',
                        'filename': firmware_file.name
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get storage paths
            try:
                store_setting = get_active_store_by_index(storage_index)
                store_paths = store_setting.get_store_paths()
                firmware_import_path = store_paths['FIRMWARE_FOLDER_IMPORT']
            except (ValueError, KeyError) as e:
                logging.error(f"Storage configuration error: {e}")
                return Response(
                    {'error': f'Storage configuration error: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Ensure import directory exists
            os.makedirs(firmware_import_path, exist_ok=True)
            
            # Save file to firmware import directory
            file_path = os.path.join(firmware_import_path, firmware_file.name)
            
            # Check if file already exists
            if os.path.exists(file_path):
                return Response(
                    {'error': f'File {firmware_file.name} already exists in import directory.'},
                    status=status.HTTP_409_CONFLICT
                )
            
            # Write file
            try:
                with open(file_path, 'wb') as destination:
                    for chunk in firmware_file.chunks():
                        destination.write(chunk)
            except IOError as e:
                logging.error(f"Error writing file {file_path}: {e}")
                return Response(
                    {'error': f'Failed to save file: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Log successful upload
            logging.info(f"Firmware file uploaded successfully: {firmware_file.name} to {file_path}")
            
            return Response({
                'success': True,
                'message': 'Firmware file uploaded successfully.',
                'filename': firmware_file.name,
                'size': firmware_file.size,
                'path': file_path,
                'storage_index': storage_index,
                'file_extension': file_extension
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logging.error(f"Error uploading firmware file: {str(e)}")
            return Response(
                {'error': f'Internal server error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )