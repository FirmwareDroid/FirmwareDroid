# Firmware Upload API

This document describes the REST API endpoint for uploading firmware files to FirmwareDroid.

## Endpoint

**URL:** `POST /upload/firmware`

**Content-Type:** `multipart/form-data`

## Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `firmware_file` | File | Yes | The firmware file to upload |
| `storage_index` | Integer | No | Storage index to use (default: 0) |

## Supported File Types

The following firmware file extensions are supported:
- `.zip`
- `.tar`
- `.gz`
- `.bz2`
- `.md5`
- `.lz4`
- `.tgz`
- `.rar`
- `.7z`
- `.lzma`
- `.xz`
- `.ozip`

## Response Format

### Success Response (201 Created)

```json
{
    "success": true,
    "message": "Firmware file uploaded successfully.",
    "filename": "firmware.zip",
    "size": 12345678,
    "path": "/path/to/firmware_import/firmware.zip",
    "storage_index": 0,
    "file_extension": ".zip"
}
```

### Error Responses

#### Missing File (400 Bad Request)
```json
{
    "error": "No firmware file provided. Please include a file with key \"firmware_file\"."
}
```

#### Empty File (400 Bad Request)
```json
{
    "error": "Uploaded file is empty."
}
```

#### Invalid File Type (400 Bad Request)
```json
{
    "error": "File type not supported. Allowed extensions: .zip, .tar, .gz, ...",
    "filename": "file.txt"
}
```

#### File Already Exists (409 Conflict)
```json
{
    "error": "File firmware.zip already exists in import directory."
}
```

#### Storage Configuration Error (500 Internal Server Error)
```json
{
    "error": "Storage configuration error: No active store setting found for index 0"
}
```

## Usage Examples

### Using curl

```bash
# Upload a firmware file
curl -X POST \
  -F "firmware_file=@/path/to/firmware.zip" \
  http://localhost:8000/upload/firmware

# Upload with specific storage index
curl -X POST \
  -F "firmware_file=@/path/to/firmware.zip" \
  -F "storage_index=1" \
  http://localhost:8000/upload/firmware
```

### Using JavaScript fetch API

```javascript
const formData = new FormData();
formData.append('firmware_file', fileInput.files[0]);

fetch('/upload/firmware', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        console.log('Upload successful:', data.filename);
    } else {
        console.error('Upload failed:', data.error);
    }
});
```

### Using Python requests

```python
import requests

files = {'firmware_file': open('firmware.zip', 'rb')}
response = requests.post('http://localhost:8000/upload/firmware', files=files)

if response.status_code == 201:
    data = response.json()
    print(f"Upload successful: {data['filename']}")
else:
    error = response.json()
    print(f"Upload failed: {error['error']}")
```

## Integration with Firmware Processing

Once uploaded, firmware files are stored in the configured `firmware_import/` directory where they can be processed by the existing firmware importer system. The files will be automatically discovered and processed during the next firmware import cycle.

## Notes

- Files are validated for supported extensions before upload
- Duplicate files (same filename) will be rejected  
- The upload directory is automatically created if it doesn't exist
- All operations are logged for debugging and audit purposes
- The storage configuration must be properly set up before using this endpoint