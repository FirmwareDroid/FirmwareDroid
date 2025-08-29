# FirmwareDroid MCP Server

## Overview

The FirmwareDroid Model Context Protocol (MCP) server provides a standardized interface for AI models to interact with FirmwareDroid's firmware analysis capabilities. This enables automated security analysis, vulnerability detection, and intelligent reporting through AI assistants.

## Features

### Available MCP Tools

1. **analyze_apk** - Comprehensive APK analysis
   - Static analysis reports (AndroGuard, APKiD, Quark Engine)
   - Android manifest parsing
   - Certificate analysis
   - Code flow analysis

2. **query_firmware** - Firmware database queries
   - Filter by vendor, version, size, filename
   - Retrieve firmware metadata and statistics
   - Support for paginated results

3. **analyze_permissions** - Permission security analysis
   - Permission categorization (dangerous, signature, normal)
   - Risk assessment and scoring
   - Privacy implications analysis

4. **detect_vulnerabilities** - Multi-tool vulnerability detection
   - Malware behavior patterns (Quark Engine)
   - Anti-analysis detection (APKiD)
   - Permission-based attack vectors
   - Comprehensive risk scoring

5. **get_metadata** - Entity metadata retrieval
   - APK and firmware file information
   - Available analysis reports
   - Certificate and manifest data

### AI Assistant Prompts

The MCP server includes built-in prompts to guide AI models:

- **firmware_analysis_guide** - Comprehensive analysis workflow
- **security_assessment_workflow** - Security research methodology  
- **vulnerability_hunting_tips** - Best practices for finding vulnerabilities

## Installation & Setup

### Prerequisites

- FirmwareDroid development environment
- Python 3.11+ with required dependencies
- MongoDB database with firmware/APK samples

### Installation

The MCP server is included as a Django app in FirmwareDroid:

```bash
# Install dependencies
pip install -r requirements.txt
pip install mcp httpx uvicorn

# Set up environment
python setup.py

# The MCP server app is automatically installed with FirmwareDroid
```

### Configuration

The MCP server uses existing FirmwareDroid configuration:

- Database connections (MongoDB)
- Authentication (JWT tokens)
- Logging and debugging settings

## Usage

### Starting the MCP Server

```bash
# Start the standalone MCP server
cd source/
python manage.py runmcp --host localhost --port 8001

# Options:
#   --host: Host to bind to (default: localhost)
#   --port: Port to bind to (default: 8001)
```

### Integration with AI Models

The MCP server exposes tools that AI models can call directly:

```python
# Example tool call (AI model perspective)
{
    "tool": "analyze_apk",
    "arguments": {
        "apk_id": "64f8b2c1a7b2d5e3f1234567",
        "include_reports": ["androguard", "apkid", "quark"]
    }
}
```

### API Endpoints

FirmwareDroid also exposes MCP information via REST API:

- `GET /mcp/info/` - MCP server information and available tools
- `GET /mcp/status/` - Current server status and configuration

## Tool Reference

### analyze_apk

Performs comprehensive APK analysis using FirmwareDroid's integrated tools.

**Parameters:**
- `apk_id` (required): Database ID of the APK to analyze
- `include_reports` (optional): List of report types to include
  - `"basic"` - Basic file information and manifest
  - `"androguard"` - AndroGuard static analysis
  - `"apkid"` - APKiD packer/obfuscator detection
  - `"quark"` - Quark Engine malware detection
  - `"flowdroid"` - FlowDroid data flow analysis

**Returns:**
```json
{
  "apk_id": "...",
  "filename": "example.apk",
  "packagename": "com.example.app",
  "file_size_bytes": 1234567,
  "android_manifest": {...},
  "reports": {
    "androguard": {
      "permissions": [...],
      "activities": [...],
      "services": [...],
      "min_sdk_version": 21,
      "target_sdk_version": 33
    }
  }
}
```

### query_firmware

Searches and filters firmware samples in the database.

**Parameters:**
- `query_type` (optional): "basic" or "detailed"
- `filters` (optional): Filter criteria
  - `os_vendor`: Firmware vendor/manufacturer
  - `version_detected`: Android version
  - `filename_contains`: Filename substring search
  - `min_size_bytes`/`max_size_bytes`: Size range
- `limit` (optional): Maximum results (1-100, default 10)

**Returns:**
```json
{
  "query_type": "basic",
  "filters": {...},
  "results_count": 5,
  "results": [
    {
      "id": "...",
      "filename": "firmware.zip",
      "os_vendor": "Samsung",
      "version_detected": 13,
      "file_size_bytes": 2147483648,
      "app_count": 156
    }
  ]
}
```

### analyze_permissions

Analyzes app permissions and assesses security risks.

**Parameters:**
- `apk_id` (required): Database ID of the APK
- `analysis_type` (optional): "basic" or "detailed"

**Returns:**
```json
{
  "apk_id": "...",
  "permissions": {
    "declared": [...],
    "dangerous": ["CAMERA", "ACCESS_FINE_LOCATION"],
    "signature": ["INSTALL_PACKAGES"],
    "normal": ["INTERNET", "VIBRATE"],
    "analysis": {
      "risk_score": 8,
      "risk_level": "MEDIUM",
      "dangerous_count": 2
    }
  }
}
```

### detect_vulnerabilities

Scans for vulnerabilities using multiple analysis engines.

**Parameters:**
- `apk_id` (required): Database ID of the APK
- `scan_types` (optional): List of scan types
  - `"basic"` - Basic vulnerability checks
  - `"quark"` - Malware behavior detection
  - `"apkid"` - Anti-analysis techniques
  - `"permissions"` - Permission-based vulnerabilities

**Returns:**
```json
{
  "apk_id": "...",
  "vulnerabilities": {
    "critical": [],
    "high": [
      {
        "source": "quark",
        "type": "malware_behavior", 
        "description": "Suspicious data exfiltration pattern",
        "confidence": 85
      }
    ],
    "medium": [...],
    "low": [...],
    "summary": {
      "total_vulnerabilities": 3,
      "risk_level": "HIGH"
    }
  }
}
```

### get_metadata

Retrieves comprehensive metadata for APKs or firmware.

**Parameters:**
- `entity_type` (required): "apk" or "firmware"
- `entity_id` (required): Database ID of the entity
- `metadata_types` (optional): List of metadata types
  - `"basic"` - Basic file information
  - `"manifest"` - Android manifest (APK only)
  - `"certificates"` - Signing certificates (APK only)
  - `"reports"` - Available analysis reports
  - `"apps"` - Contained apps (firmware only)
  - `"partitions"` - Partition information (firmware only)

## Security Considerations

### Authentication

The MCP server integrates with FirmwareDroid's existing authentication:

- Uses JWT tokens from the main FirmwareDroid API
- Inherits user permissions and access controls
- Rate limiting and request validation

### Access Control

- MCP tools respect existing database access permissions
- Sensitive operations require authenticated access
- Audit logging for all MCP tool invocations

### Data Protection

- No sensitive data is exposed in tool schemas
- Results are filtered based on user permissions
- Secure handling of analysis results and metadata

## Development

### Adding New Tools

To add new MCP tools:

1. Define the tool in `FirmwareDroidMCPServer.setup_tools()`
2. Implement the tool handler function
3. Add the tool schema to `get_tool_definitions()`
4. Update documentation

### Testing

```bash
# Run the MCP server test suite
cd source/
python test_mcp_server.py

# Test with real data (requires database)
python manage.py runmcp --host localhost --port 8001
```

### Integration Testing

The MCP server can be tested with AI models that support the MCP protocol:

- Claude Desktop
- Custom AI applications
- MCP-compatible development tools

## Troubleshooting

### Common Issues

1. **Django setup errors**: Ensure all dependencies are installed
2. **Database connection**: Verify MongoDB is running and accessible
3. **Import errors**: Check Python path and module dependencies
4. **Authentication errors**: Verify JWT token configuration

### Debugging

Enable debug logging in Django settings:

```python
LOGGING = {
    'loggers': {
        'mcp_server': {
            'level': 'DEBUG',
            'handlers': ['console'],
        }
    }
}
```

### Performance

For large datasets:

- Use appropriate query limits
- Consider pagination for large result sets
- Monitor database performance during analysis
- Cache frequently accessed metadata

## Examples

### AI Assistant Integration

```python
# Example AI model interaction
async def analyze_firmware_security(firmware_id):
    # Query firmware
    firmware = await mcp_call("query_firmware", {
        "filters": {"id": firmware_id},
        "query_type": "detailed"
    })
    
    # Analyze contained APKs
    vulnerabilities = []
    for app_id in firmware["results"][0]["app_ids"]:
        vulns = await mcp_call("detect_vulnerabilities", {
            "apk_id": app_id,
            "scan_types": ["quark", "permissions", "apkid"]
        })
        vulnerabilities.extend(vulns["vulnerabilities"]["high"])
    
    # Generate security report
    return generate_security_report(firmware, vulnerabilities)
```

### Automated Vulnerability Research

```python
# Example vulnerability hunting workflow
async def hunt_vulnerabilities(vendor="Samsung"):
    # Find firmware samples
    firmware_list = await mcp_call("query_firmware", {
        "filters": {"os_vendor": vendor},
        "limit": 50
    })
    
    critical_findings = []
    for firmware in firmware_list["results"]:
        # Analyze system apps
        for app_id in firmware["app_ids"][:10]:  # Limit for demo
            vulns = await mcp_call("detect_vulnerabilities", {
                "apk_id": app_id,
                "scan_types": ["quark", "permissions"]
            })
            
            if vulns["vulnerabilities"]["summary"]["risk_level"] == "CRITICAL":
                critical_findings.append({
                    "firmware": firmware["filename"],
                    "app_id": app_id,
                    "vulnerabilities": vulns["vulnerabilities"]["critical"]
                })
    
    return critical_findings
```