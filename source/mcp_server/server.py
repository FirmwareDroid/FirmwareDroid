# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
"""
MCP Server implementation for FirmwareDroid

This module implements the Model Context Protocol server that provides
standardized access to FirmwareDroid's firmware analysis tools and data.
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional, Sequence
from mcp.server import Server
from mcp.types import (
    Tool, 
    TextContent, 
    CallToolRequest, 
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    InitializeRequest,
    InitializeResult,
    GetPromptRequest,
    GetPromptResult,
    ListPromptsRequest,
    ListPromptsResult,
    Prompt,
    PromptMessage,
    Role
)
import json

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from context.context_creator import create_db_context, create_log_context

logger = logging.getLogger(__name__)


class FirmwareDroidMCPServer:
    """
    MCP Server for FirmwareDroid that exposes firmware analysis capabilities
    as standardized tools for AI model interaction.
    """
    
    def __init__(self):
        self.server = Server("firmwaredroid-mcp")
        self.setup_tools()
        self.setup_prompts()
        
    def setup_tools(self):
        """Register all available tools with the MCP server"""
        
        # APK Analysis Tool
        @self.server.call_tool()
        async def analyze_apk(arguments: Dict[str, Any]) -> Sequence[TextContent]:
            """Analyze an APK file and return comprehensive analysis results"""
            try:
                apk_id = arguments.get("apk_id")
                include_reports = arguments.get("include_reports", ["basic"])
                
                if not apk_id:
                    return [TextContent(
                        type="text",
                        text="Error: apk_id parameter is required"
                    )]
                
                result = await self._analyze_apk_impl(apk_id, include_reports)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
            except Exception as e:
                logger.error(f"APK analysis error: {e}")
                return [TextContent(
                    type="text", 
                    text=f"Error analyzing APK: {str(e)}"
                )]
        
        # Firmware Query Tool
        @self.server.call_tool()
        async def query_firmware(arguments: Dict[str, Any]) -> Sequence[TextContent]:
            """Query firmware databases and return matching results"""
            try:
                query_type = arguments.get("query_type", "basic")
                filters = arguments.get("filters", {})
                limit = arguments.get("limit", 10)
                
                result = await self._query_firmware_impl(query_type, filters, limit)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
            except Exception as e:
                logger.error(f"Firmware query error: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error querying firmware: {str(e)}"
                )]
        
        # Permission Analysis Tool  
        @self.server.call_tool()
        async def analyze_permissions(arguments: Dict[str, Any]) -> Sequence[TextContent]:
            """Analyze app permissions and identify potential security risks"""
            try:
                apk_id = arguments.get("apk_id")
                analysis_type = arguments.get("analysis_type", "basic")
                
                if not apk_id:
                    return [TextContent(
                        type="text",
                        text="Error: apk_id parameter is required"
                    )]
                
                result = await self._analyze_permissions_impl(apk_id, analysis_type)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
            except Exception as e:
                logger.error(f"Permission analysis error: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error analyzing permissions: {str(e)}"
                )]
        
        # Vulnerability Detection Tool
        @self.server.call_tool()
        async def detect_vulnerabilities(arguments: Dict[str, Any]) -> Sequence[TextContent]:
            """Detect vulnerabilities in APK files using multiple analysis tools"""
            try:
                apk_id = arguments.get("apk_id")
                scan_types = arguments.get("scan_types", ["basic"])
                
                if not apk_id:
                    return [TextContent(
                        type="text",
                        text="Error: apk_id parameter is required"
                    )]
                
                result = await self._detect_vulnerabilities_impl(apk_id, scan_types)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
            except Exception as e:
                logger.error(f"Vulnerability detection error: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error detecting vulnerabilities: {str(e)}"
                )]
        
        # Metadata Retrieval Tool
        @self.server.call_tool()
        async def get_metadata(arguments: Dict[str, Any]) -> Sequence[TextContent]:
            """Retrieve comprehensive metadata for firmware or APK files"""
            try:
                entity_type = arguments.get("entity_type")  # "apk" or "firmware"
                entity_id = arguments.get("entity_id")
                metadata_types = arguments.get("metadata_types", ["basic"])
                
                if not entity_type or not entity_id:
                    return [TextContent(
                        type="text",
                        text="Error: entity_type and entity_id parameters are required"
                    )]
                
                result = await self._get_metadata_impl(entity_type, entity_id, metadata_types)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
                
            except Exception as e:
                logger.error(f"Metadata retrieval error: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error retrieving metadata: {str(e)}"
                )]

    def setup_prompts(self):
        """Register prompts that provide context about FirmwareDroid capabilities"""
        
        @self.server.list_prompts()
        async def list_prompts() -> ListPromptsResult:
            return ListPromptsResult(
                prompts=[
                    Prompt(
                        name="firmware_analysis_guide",
                        description="Guide for performing comprehensive firmware analysis using FirmwareDroid tools"
                    ),
                    Prompt(
                        name="security_assessment_workflow",
                        description="Workflow for conducting security assessments of Android firmware"
                    ),
                    Prompt(
                        name="vulnerability_hunting_tips",
                        description="Tips and best practices for vulnerability discovery in Android apps"
                    )
                ]
            )
        
        @self.server.get_prompt()
        async def get_prompt(name: str, arguments: Dict[str, str] | None = None) -> GetPromptResult:
            if name == "firmware_analysis_guide":
                return GetPromptResult(
                    description="Comprehensive guide for firmware analysis",
                    messages=[
                        PromptMessage(
                            role=Role.user,
                            content=TextContent(
                                type="text",
                                text="""# FirmwareDroid Analysis Guide

## Available Tools:
1. **analyze_apk**: Comprehensive APK analysis including static analysis reports
2. **query_firmware**: Search and filter firmware databases
3. **analyze_permissions**: Permission analysis and risk assessment
4. **detect_vulnerabilities**: Multi-tool vulnerability detection
5. **get_metadata**: Retrieve detailed metadata for any entity

## Typical Workflow:
1. Query firmware to find relevant samples
2. Analyze APKs within firmware for security issues
3. Check permissions for privacy/security concerns
4. Run vulnerability detection across multiple tools
5. Generate comprehensive security reports

Use these tools to systematically analyze Android firmware for security research."""
                            )
                        )
                    ]
                )
            elif name == "security_assessment_workflow":
                return GetPromptResult(
                    description="Security assessment workflow for Android firmware",
                    messages=[
                        PromptMessage(
                            role=Role.user,
                            content=TextContent(
                                type="text", 
                                text="""# Security Assessment Workflow

## Phase 1: Discovery
- Use query_firmware to identify target firmware samples
- Get metadata to understand firmware characteristics

## Phase 2: APK Analysis  
- Extract and analyze all APKs using analyze_apk
- Focus on system apps and pre-installed applications

## Phase 3: Permission Analysis
- Use analyze_permissions to identify overprivileged apps
- Look for dangerous permission combinations

## Phase 4: Vulnerability Detection
- Run detect_vulnerabilities with multiple scan types
- Cross-reference findings across different tools

## Phase 5: Reporting
- Compile findings into security assessment report
- Prioritize vulnerabilities by impact and exploitability"""
                            )
                        )
                    ]
                )
            elif name == "vulnerability_hunting_tips":
                return GetPromptResult(
                    description="Tips for effective vulnerability hunting",
                    messages=[
                        PromptMessage(
                            role=Role.user,
                            content=TextContent(
                                type="text",
                                text="""# Vulnerability Hunting Tips

## High-Value Targets:
- System applications with privileged permissions
- Network-facing applications and services
- Applications handling sensitive data

## Analysis Focus Areas:
- Intent filters and exported components
- Custom permissions and protection levels
- Native code and JNI interfaces
- Cryptographic implementations
- Input validation and sanitization

## Tool Combinations:
- Use AndroGuard for deep static analysis
- FlowDroid for data flow analysis
- APKiD for packer/obfuscation detection
- Quark Engine for malware behavior patterns

## Red Flags:
- Weak cryptographic algorithms
- Hardcoded credentials or keys
- Excessive permissions
- Debug features in production builds"""
                            )
                        )
                    ]
                )
            else:
                raise ValueError(f"Unknown prompt: {name}")

    @create_db_context
    async def _analyze_apk_impl(self, apk_id: str, include_reports: List[str]) -> Dict[str, Any]:
        """Implementation of APK analysis functionality"""
        from model.AndroidApp import AndroidApp
        
        try:
            # Get the APK document
            android_app = AndroidApp.objects.get(pk=apk_id)
            
            result = {
                "apk_id": apk_id,
                "filename": android_app.filename,
                "packagename": android_app.packagename,
                "md5": android_app.md5,
                "sha256": android_app.sha256,
                "file_size_bytes": android_app.file_size_bytes,
                "indexed_date": android_app.indexed_date.isoformat() if android_app.indexed_date else None,
                "reports": {}
            }
            
            # Include basic manifest information
            if android_app.android_manifest_dict:
                result["android_manifest"] = android_app.android_manifest_dict
            
            # Include various analysis reports based on request
            if "androguard" in include_reports and android_app.androguard_report_reference:
                try:
                    androguard_report = android_app.androguard_report_reference.fetch()
                    result["reports"]["androguard"] = {
                        "permissions": androguard_report.permissions,
                        "activities": androguard_report.activities,
                        "services": androguard_report.services,
                        "receivers": androguard_report.receivers,
                        "main_activity": androguard_report.main_activity,
                        "min_sdk_version": androguard_report.min_sdk_version,
                        "target_sdk_version": androguard_report.target_sdk_version,
                    }
                except Exception as e:
                    logger.warning(f"Could not fetch AndroGuard report: {e}")
            
            if "apkid" in include_reports and android_app.apkid_report_reference:
                try:
                    apkid_report = android_app.apkid_report_reference.fetch()
                    result["reports"]["apkid"] = {
                        "matches": apkid_report.matches,
                        "anti_vm": apkid_report.anti_vm,
                        "anti_disassembly": apkid_report.anti_disassembly,
                        "anti_debug": apkid_report.anti_debug,
                        "obfuscator": apkid_report.obfuscator,
                    }
                except Exception as e:
                    logger.warning(f"Could not fetch APKiD report: {e}")
                    
            if "quark" in include_reports and android_app.quark_engine_report_reference:
                try:
                    quark_report = android_app.quark_engine_report_reference.fetch()
                    result["reports"]["quark"] = {
                        "crime_description": quark_report.crime_description,
                        "confidence": quark_report.confidence,
                        "score": quark_report.score,
                        "summary": quark_report.summary
                    }
                except Exception as e:
                    logger.warning(f"Could not fetch Quark report: {e}")
            
            return result
            
        except AndroidApp.DoesNotExist:
            raise ValueError(f"APK with ID {apk_id} not found")
        except Exception as e:
            raise RuntimeError(f"Failed to analyze APK: {str(e)}")

    @create_db_context
    async def _query_firmware_impl(self, query_type: str, filters: Dict[str, Any], limit: int) -> Dict[str, Any]:
        """Implementation of firmware query functionality"""
        from model.AndroidFirmware import AndroidFirmware
        
        try:
            # Build query based on filters
            query = AndroidFirmware.objects()
            
            if "os_vendor" in filters:
                query = query.filter(os_vendor=filters["os_vendor"])
            
            if "version_detected" in filters:
                query = query.filter(version_detected=filters["version_detected"])
                
            if "filename_contains" in filters:
                query = query.filter(filename__icontains=filters["filename_contains"])
            
            if "min_size_bytes" in filters:
                query = query.filter(file_size_bytes__gte=filters["min_size_bytes"])
                
            if "max_size_bytes" in filters:
                query = query.filter(file_size_bytes__lte=filters["max_size_bytes"])
            
            # Apply limit
            firmware_list = query.limit(limit)
            
            results = []
            for firmware in firmware_list:
                firmware_data = {
                    "id": str(firmware.id),
                    "filename": firmware.filename,
                    "original_filename": firmware.original_filename,
                    "os_vendor": firmware.os_vendor,
                    "version_detected": firmware.version_detected,
                    "file_size_bytes": firmware.file_size_bytes,
                    "md5": firmware.md5,
                    "sha256": firmware.sha256,
                    "indexed_date": firmware.indexed_date.isoformat() if firmware.indexed_date else None,
                    "app_count": len(firmware.android_app_id_list) if firmware.android_app_id_list else 0
                }
                
                if query_type == "detailed":
                    firmware_data["build_prop_count"] = len(firmware.build_prop_file_id_list) if firmware.build_prop_file_id_list else 0
                    firmware_data["partition_info"] = firmware.partition_info_dict
                
                results.append(firmware_data)
            
            return {
                "query_type": query_type,
                "filters": filters,
                "limit": limit,
                "results_count": len(results),
                "results": results
            }
            
        except Exception as e:
            raise RuntimeError(f"Failed to query firmware: {str(e)}")

    @create_db_context  
    async def _analyze_permissions_impl(self, apk_id: str, analysis_type: str) -> Dict[str, Any]:
        """Implementation of permission analysis functionality"""
        from model.AndroidApp import AndroidApp
        
        try:
            android_app = AndroidApp.objects.get(pk=apk_id)
            
            result = {
                "apk_id": apk_id,
                "filename": android_app.filename,
                "packagename": android_app.packagename,
                "analysis_type": analysis_type,
                "permissions": {
                    "declared": [],
                    "dangerous": [],
                    "signature": [],
                    "normal": [],
                    "analysis": {}
                }
            }
            
            # Get permissions from AndroGuard report if available
            if android_app.androguard_report_reference:
                try:
                    androguard_report = android_app.androguard_report_reference.fetch()
                    permissions = androguard_report.permissions if androguard_report.permissions else []
                    
                    result["permissions"]["declared"] = permissions
                    
                    # Categorize permissions by protection level
                    dangerous_perms = []
                    signature_perms = []
                    normal_perms = []
                    
                    # Define some common dangerous permissions
                    dangerous_permission_patterns = [
                        "CAMERA", "RECORD_AUDIO", "ACCESS_FINE_LOCATION", "ACCESS_COARSE_LOCATION",
                        "READ_CONTACTS", "WRITE_CONTACTS", "READ_SMS", "SEND_SMS", "CALL_PHONE",
                        "READ_PHONE_STATE", "WRITE_EXTERNAL_STORAGE", "READ_EXTERNAL_STORAGE",
                        "INSTALL_PACKAGES", "DELETE_PACKAGES", "SYSTEM_ALERT_WINDOW"
                    ]
                    
                    for perm in permissions:
                        if any(pattern in perm for pattern in dangerous_permission_patterns):
                            dangerous_perms.append(perm)
                        elif "SIGNATURE" in perm or "SYSTEM" in perm:
                            signature_perms.append(perm)
                        else:
                            normal_perms.append(perm)
                    
                    result["permissions"]["dangerous"] = dangerous_perms
                    result["permissions"]["signature"] = signature_perms  
                    result["permissions"]["normal"] = normal_perms
                    
                    # Basic risk analysis
                    risk_score = len(dangerous_perms) * 2 + len(signature_perms) * 3
                    risk_level = "LOW"
                    if risk_score > 10:
                        risk_level = "HIGH"
                    elif risk_score > 5:
                        risk_level = "MEDIUM"
                    
                    result["permissions"]["analysis"] = {
                        "risk_score": risk_score,
                        "risk_level": risk_level,
                        "dangerous_count": len(dangerous_perms),
                        "signature_count": len(signature_perms),
                        "total_count": len(permissions)
                    }
                    
                except Exception as e:
                    logger.warning(f"Could not analyze permissions from AndroGuard: {e}")
            
            # Get additional permission info from manifest if available
            if android_app.android_manifest_dict:
                manifest = android_app.android_manifest_dict
                if "uses-permission" in manifest:
                    manifest_perms = manifest["uses-permission"]
                    if isinstance(manifest_perms, list):
                        result["manifest_permissions"] = manifest_perms
                    else:
                        result["manifest_permissions"] = [manifest_perms]
            
            return result
            
        except AndroidApp.DoesNotExist:
            raise ValueError(f"APK with ID {apk_id} not found")
        except Exception as e:
            raise RuntimeError(f"Failed to analyze permissions: {str(e)}")

    @create_db_context
    async def _detect_vulnerabilities_impl(self, apk_id: str, scan_types: List[str]) -> Dict[str, Any]:
        """Implementation of vulnerability detection functionality"""
        from model.AndroidApp import AndroidApp
        
        try:
            android_app = AndroidApp.objects.get(pk=apk_id)
            
            result = {
                "apk_id": apk_id,
                "filename": android_app.filename,
                "packagename": android_app.packagename,
                "scan_types": scan_types,
                "vulnerabilities": {
                    "critical": [],
                    "high": [],
                    "medium": [],
                    "low": [],
                    "summary": {}
                }
            }
            
            # Check Quark Engine results for malware patterns
            if "quark" in scan_types and android_app.quark_engine_report_reference:
                try:
                    quark_report = android_app.quark_engine_report_reference.fetch()
                    if quark_report.confidence and quark_report.confidence > 80:
                        result["vulnerabilities"]["high"].append({
                            "source": "quark",
                            "type": "malware_behavior",
                            "description": quark_report.crime_description,
                            "confidence": quark_report.confidence,
                            "score": quark_report.score
                        })
                except Exception as e:
                    logger.warning(f"Could not check Quark report: {e}")
            
            # Check APKiD for packing/obfuscation (potential evasion techniques)
            if "apkid" in scan_types and android_app.apkid_report_reference:
                try:
                    apkid_report = android_app.apkid_report_reference.fetch()
                    
                    if apkid_report.anti_debug or apkid_report.anti_vm or apkid_report.anti_disassembly:
                        result["vulnerabilities"]["medium"].append({
                            "source": "apkid",
                            "type": "anti_analysis",
                            "description": "Application contains anti-analysis techniques",
                            "details": {
                                "anti_debug": apkid_report.anti_debug,
                                "anti_vm": apkid_report.anti_vm,
                                "anti_disassembly": apkid_report.anti_disassembly
                            }
                        })
                    
                    if apkid_report.obfuscator:
                        result["vulnerabilities"]["low"].append({
                            "source": "apkid",
                            "type": "obfuscation",
                            "description": "Application uses code obfuscation",
                            "obfuscator": apkid_report.obfuscator
                        })
                        
                except Exception as e:
                    logger.warning(f"Could not check APKiD report: {e}")
            
            # Check permissions for potential privilege escalation
            if "permissions" in scan_types and android_app.androguard_report_reference:
                try:
                    androguard_report = android_app.androguard_report_reference.fetch()
                    permissions = androguard_report.permissions if androguard_report.permissions else []
                    
                    # Check for dangerous permission combinations
                    if "android.permission.SYSTEM_ALERT_WINDOW" in permissions:
                        result["vulnerabilities"]["high"].append({
                            "source": "permission_analysis",
                            "type": "overlay_attack",
                            "description": "App can display system alert windows (potential overlay attacks)",
                            "permission": "SYSTEM_ALERT_WINDOW"
                        })
                    
                    if "android.permission.BIND_DEVICE_ADMIN" in permissions:
                        result["vulnerabilities"]["medium"].append({
                            "source": "permission_analysis", 
                            "type": "device_admin",
                            "description": "App can bind as device administrator",
                            "permission": "BIND_DEVICE_ADMIN"
                        })
                    
                    # Check for excessive permissions
                    dangerous_count = sum(1 for perm in permissions if any(dp in perm for dp in 
                        ["CAMERA", "RECORD_AUDIO", "LOCATION", "CONTACTS", "SMS", "PHONE", "STORAGE"]))
                    
                    if dangerous_count > 5:
                        result["vulnerabilities"]["medium"].append({
                            "source": "permission_analysis",
                            "type": "excessive_permissions",
                            "description": f"App requests {dangerous_count} dangerous permissions",
                            "count": dangerous_count
                        })
                        
                except Exception as e:
                    logger.warning(f"Could not analyze permissions for vulnerabilities: {e}")
            
            # Generate summary
            total_critical = len(result["vulnerabilities"]["critical"])
            total_high = len(result["vulnerabilities"]["high"])
            total_medium = len(result["vulnerabilities"]["medium"])
            total_low = len(result["vulnerabilities"]["low"])
            
            result["vulnerabilities"]["summary"] = {
                "total_vulnerabilities": total_critical + total_high + total_medium + total_low,
                "critical_count": total_critical,
                "high_count": total_high,
                "medium_count": total_medium,
                "low_count": total_low,
                "risk_level": "CRITICAL" if total_critical > 0 else "HIGH" if total_high > 0 else "MEDIUM" if total_medium > 0 else "LOW"
            }
            
            return result
            
        except AndroidApp.DoesNotExist:
            raise ValueError(f"APK with ID {apk_id} not found")
        except Exception as e:
            raise RuntimeError(f"Failed to detect vulnerabilities: {str(e)}")

    @create_db_context
    async def _get_metadata_impl(self, entity_type: str, entity_id: str, metadata_types: List[str]) -> Dict[str, Any]:
        """Implementation of metadata retrieval functionality"""
        
        try:
            if entity_type == "apk":
                from model.AndroidApp import AndroidApp
                entity = AndroidApp.objects.get(pk=entity_id)
                
                result = {
                    "entity_type": "apk",
                    "entity_id": entity_id,
                    "metadata_types": metadata_types,
                    "metadata": {
                        "basic": {
                            "filename": entity.filename,
                            "original_filename": entity.original_filename,
                            "packagename": entity.packagename,
                            "file_size_bytes": entity.file_size_bytes,
                            "md5": entity.md5,
                            "sha256": entity.sha256,
                            "sha1": entity.sha1,
                            "indexed_date": entity.indexed_date.isoformat() if entity.indexed_date else None,
                            "relative_firmware_path": entity.relative_firmware_path
                        }
                    }
                }
                
                if "manifest" in metadata_types and entity.android_manifest_dict:
                    result["metadata"]["manifest"] = entity.android_manifest_dict
                
                if "certificates" in metadata_types and entity.certificate_id_list:
                    cert_info = []
                    for cert_ref in entity.certificate_id_list:
                        try:
                            cert = cert_ref.fetch()
                            cert_info.append({
                                "subject": cert.subject if hasattr(cert, 'subject') else None,
                                "issuer": cert.issuer if hasattr(cert, 'issuer') else None,
                                "serial_number": cert.serial_number if hasattr(cert, 'serial_number') else None,
                                "fingerprint": cert.fingerprint if hasattr(cert, 'fingerprint') else None
                            })
                        except Exception as e:
                            logger.warning(f"Could not fetch certificate: {e}")
                    result["metadata"]["certificates"] = cert_info
                
                if "reports" in metadata_types:
                    available_reports = []
                    if entity.androguard_report_reference:
                        available_reports.append("androguard")
                    if entity.apkid_report_reference:
                        available_reports.append("apkid")
                    if entity.quark_engine_report_reference:
                        available_reports.append("quark")
                    if entity.flowdroid_report_reference:
                        available_reports.append("flowdroid")
                    result["metadata"]["available_reports"] = available_reports
                    
            elif entity_type == "firmware":
                from model.AndroidFirmware import AndroidFirmware
                entity = AndroidFirmware.objects.get(pk=entity_id)
                
                result = {
                    "entity_type": "firmware",
                    "entity_id": entity_id,
                    "metadata_types": metadata_types,
                    "metadata": {
                        "basic": {
                            "filename": entity.filename,
                            "original_filename": entity.original_filename,
                            "file_size_bytes": entity.file_size_bytes,
                            "md5": entity.md5,
                            "sha256": entity.sha256,
                            "sha1": entity.sha1,
                            "os_vendor": entity.os_vendor,
                            "version_detected": entity.version_detected,
                            "indexed_date": entity.indexed_date.isoformat() if entity.indexed_date else None,
                            "tag": entity.tag
                        }
                    }
                }
                
                if "apps" in metadata_types:
                    app_count = len(entity.android_app_id_list) if entity.android_app_id_list else 0
                    result["metadata"]["apps"] = {
                        "count": app_count,
                        "app_ids": [str(app_ref.id) for app_ref in entity.android_app_id_list] if entity.android_app_id_list else []
                    }
                
                if "partitions" in metadata_types and entity.partition_info_dict:
                    result["metadata"]["partitions"] = entity.partition_info_dict
                
                if "build_props" in metadata_types:
                    build_prop_count = len(entity.build_prop_file_id_list) if entity.build_prop_file_id_list else 0
                    result["metadata"]["build_props"] = {
                        "count": build_prop_count,
                        "build_prop_ids": [str(bp_ref.id) for bp_ref in entity.build_prop_file_id_list] if entity.build_prop_file_id_list else []
                    }
            else:
                raise ValueError(f"Unsupported entity type: {entity_type}")
            
            return result
            
        except Exception as e:
            raise RuntimeError(f"Failed to get metadata: {str(e)}")

    def get_tool_definitions(self) -> List[Tool]:
        """Return tool definitions for MCP discovery"""
        return [
            Tool(
                name="analyze_apk",
                description="Analyze an APK file and return comprehensive analysis results including static analysis reports",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "apk_id": {
                            "type": "string",
                            "description": "The ID of the APK to analyze"
                        },
                        "include_reports": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Types of reports to include (basic, androguard, apkid, quark, flowdroid)",
                            "default": ["basic"]
                        }
                    },
                    "required": ["apk_id"]
                }
            ),
            Tool(
                name="query_firmware",
                description="Query firmware databases and return matching results with filtering capabilities",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query_type": {
                            "type": "string",
                            "enum": ["basic", "detailed"],
                            "description": "Type of query to perform",
                            "default": "basic"
                        },
                        "filters": {
                            "type": "object",
                            "properties": {
                                "os_vendor": {"type": "string"},
                                "version_detected": {"type": "integer"},
                                "filename_contains": {"type": "string"},
                                "min_size_bytes": {"type": "integer"},
                                "max_size_bytes": {"type": "integer"}
                            },
                            "description": "Filters to apply to the query"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 100
                        }
                    }
                }
            ),
            Tool(
                name="analyze_permissions",
                description="Analyze app permissions and identify potential security risks",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "apk_id": {
                            "type": "string",
                            "description": "The ID of the APK to analyze permissions for"
                        },
                        "analysis_type": {
                            "type": "string",
                            "enum": ["basic", "detailed"],
                            "description": "Type of permission analysis to perform",
                            "default": "basic"
                        }
                    },
                    "required": ["apk_id"]
                }
            ),
            Tool(
                name="detect_vulnerabilities",
                description="Detect vulnerabilities in APK files using multiple analysis tools",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "apk_id": {
                            "type": "string",
                            "description": "The ID of the APK to scan for vulnerabilities"
                        },
                        "scan_types": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["basic", "quark", "apkid", "permissions", "manifest"]
                            },
                            "description": "Types of vulnerability scans to perform",
                            "default": ["basic"]
                        }
                    },
                    "required": ["apk_id"]
                }
            ),
            Tool(
                name="get_metadata",
                description="Retrieve comprehensive metadata for firmware or APK files",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "entity_type": {
                            "type": "string",
                            "enum": ["apk", "firmware"],
                            "description": "Type of entity to get metadata for"
                        },
                        "entity_id": {
                            "type": "string",
                            "description": "The ID of the entity"
                        },
                        "metadata_types": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["basic", "manifest", "certificates", "reports", "apps", "partitions", "build_props"]
                            },
                            "description": "Types of metadata to retrieve",
                            "default": ["basic"]
                        }
                    },
                    "required": ["entity_type", "entity_id"]
                }
            )
        ]

    async def run(self, host: str = "localhost", port: int = 8001):
        """Run the MCP server"""
        import uvicorn
        
        # Set up the server handlers
        @self.server.list_tools()
        async def list_tools() -> ListToolsResult:
            return ListToolsResult(tools=self.get_tool_definitions())
        
        # Create ASGI app
        app = self.server.create_asgi_app()
        
        logger.info(f"Starting FirmwareDroid MCP Server on {host}:{port}")
        
        # Run the server
        config = uvicorn.Config(
            app,
            host=host,
            port=port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()


# Django management command to run the MCP server
class Command(BaseCommand):
    help = 'Run the FirmwareDroid MCP Server'

    def add_arguments(self, parser):
        parser.add_argument(
            '--host',
            type=str,
            default='localhost',
            help='Host to bind the server to (default: localhost)'
        )
        parser.add_argument(
            '--port',
            type=int,
            default=8001,
            help='Port to bind the server to (default: 8001)'
        )

    def handle(self, *args, **options):
        """Handle the management command"""
        
        # Initialize Django and database connections
        import django
        from django.conf import settings
        
        if not settings.configured:
            django.setup()
            
        # Create and run the server
        server = FirmwareDroidMCPServer()
        
        # Run the server using asyncio
        asyncio.run(server.run(
            host=options['host'],
            port=options['port']
        ))