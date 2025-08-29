#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
"""
Example MCP Client for FirmwareDroid

This example demonstrates how an AI model or external application
can interact with the FirmwareDroid MCP server to perform automated
firmware analysis.
"""
import asyncio
import json
import httpx
from typing import Dict, Any, List


class FirmwareDroidMCPClient:
    """Simple MCP client for FirmwareDroid"""
    
    def __init__(self, server_url: str = "http://localhost:8001"):
        self.server_url = server_url
        self.client = httpx.AsyncClient()
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool on the FirmwareDroid server"""
        try:
            response = await self.client.post(
                f"{self.server_url}/call_tool",
                json={
                    "tool": tool_name,
                    "arguments": arguments
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools"""
        try:
            response = await self.client.get(f"{self.server_url}/list_tools")
            response.raise_for_status()
            return response.json().get("tools", [])
        except Exception as e:
            return [{"error": str(e)}]
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


async def example_firmware_analysis():
    """Example: Comprehensive firmware analysis workflow"""
    client = FirmwareDroidMCPClient()
    
    try:
        print("🔍 FirmwareDroid MCP Client Example")
        print("=" * 50)
        
        # Step 1: List available tools
        print("\n📋 Available Tools:")
        tools = await client.list_tools()
        for tool in tools:
            if "error" not in tool:
                print(f"  - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
        
        # Step 2: Query firmware samples
        print("\n🔎 Querying firmware samples...")
        firmware_query = await client.call_tool("query_firmware", {
            "query_type": "basic",
            "filters": {
                "os_vendor": "Samsung"
            },
            "limit": 5
        })
        
        if "error" not in firmware_query:
            print(f"Found {firmware_query.get('results_count', 0)} firmware samples")
            for firmware in firmware_query.get('results', [])[:2]:
                print(f"  📱 {firmware.get('filename', 'Unknown')} - {firmware.get('app_count', 0)} apps")
        
        # Step 3: Analyze an APK (example with mock ID)
        print("\n🔬 APK Analysis Example...")
        apk_analysis = await client.call_tool("analyze_apk", {
            "apk_id": "example_apk_id_12345",  # This would be a real APK ID
            "include_reports": ["basic", "androguard"]
        })
        
        if "error" in apk_analysis:
            print(f"  ⚠️  Example APK not found (expected for demo): {apk_analysis['error']}")
        else:
            print(f"  ✅ Analysis completed for {apk_analysis.get('filename', 'Unknown APK')}")
        
        # Step 4: Permission analysis example
        print("\n🔐 Permission Analysis Example...")
        permission_analysis = await client.call_tool("analyze_permissions", {
            "apk_id": "example_apk_id_12345",
            "analysis_type": "detailed"
        })
        
        if "error" in permission_analysis:
            print(f"  ⚠️  Example APK not found (expected for demo): {permission_analysis['error']}")
        else:
            perms = permission_analysis.get('permissions', {})
            print(f"  📊 Risk Level: {perms.get('analysis', {}).get('risk_level', 'Unknown')}")
        
        # Step 5: Vulnerability detection example
        print("\n🛡️  Vulnerability Detection Example...")
        vuln_scan = await client.call_tool("detect_vulnerabilities", {
            "apk_id": "example_apk_id_12345",
            "scan_types": ["basic", "permissions", "quark"]
        })
        
        if "error" in vuln_scan:
            print(f"  ⚠️  Example APK not found (expected for demo): {vuln_scan['error']}")
        else:
            summary = vuln_scan.get('vulnerabilities', {}).get('summary', {})
            print(f"  🎯 Risk Assessment: {summary.get('risk_level', 'Unknown')}")
            print(f"  🔢 Total Vulnerabilities: {summary.get('total_vulnerabilities', 0)}")
        
        # Step 6: Metadata retrieval example
        print("\n📊 Metadata Retrieval Example...")
        metadata = await client.call_tool("get_metadata", {
            "entity_type": "apk",
            "entity_id": "example_apk_id_12345",
            "metadata_types": ["basic", "reports"]
        })
        
        if "error" in metadata:
            print(f"  ⚠️  Example APK not found (expected for demo): {metadata['error']}")
        else:
            basic_info = metadata.get('metadata', {}).get('basic', {})
            print(f"  📁 File Size: {basic_info.get('file_size_bytes', 0)} bytes")
            available_reports = metadata.get('metadata', {}).get('available_reports', [])
            print(f"  📋 Available Reports: {', '.join(available_reports) or 'None'}")
        
        print("\n✅ Example completed!")
        print("\n💡 To use with real data:")
        print("   1. Start FirmwareDroid with sample firmware/APK data")
        print("   2. Start the MCP server: python manage.py runmcp")
        print("   3. Use real APK/firmware IDs from the database")
        
    except Exception as e:
        print(f"❌ Example failed: {e}")
    
    finally:
        await client.close()


async def example_ai_security_workflow():
    """Example: AI-driven security analysis workflow"""
    client = FirmwareDroidMCPClient()
    
    try:
        print("\n🤖 AI Security Analysis Workflow")
        print("=" * 50)
        
        # Simulated AI decision-making process
        print("\n🧠 AI Decision: Analyzing Samsung firmware for security issues...")
        
        # Step 1: Find high-risk firmware samples
        firmware_query = await client.call_tool("query_firmware", {
            "filters": {
                "os_vendor": "Samsung",
                "min_size_bytes": 1000000000  # Large firmware files
            },
            "limit": 10
        })
        
        if "error" not in firmware_query:
            print(f"🎯 AI found {firmware_query.get('results_count', 0)} large Samsung firmware samples")
            
            # Step 2: For each firmware, analyze contained apps
            for firmware in firmware_query.get('results', [])[:2]:  # Limit for demo
                print(f"\n📱 Analyzing: {firmware.get('filename', 'Unknown')}")
                
                # Get firmware metadata
                fw_metadata = await client.call_tool("get_metadata", {
                    "entity_type": "firmware", 
                    "entity_id": firmware.get('id', ''),
                    "metadata_types": ["basic", "apps"]
                })
                
                if "error" not in fw_metadata:
                    app_count = fw_metadata.get('metadata', {}).get('apps', {}).get('count', 0)
                    print(f"  📊 Contains {app_count} applications")
                    
                    # AI decides to focus on system apps (first few)
                    app_ids = fw_metadata.get('metadata', {}).get('apps', {}).get('app_ids', [])[:5]
                    
                    high_risk_apps = []
                    for app_id in app_ids:
                        # Scan each app for vulnerabilities
                        vuln_result = await client.call_tool("detect_vulnerabilities", {
                            "apk_id": app_id,
                            "scan_types": ["basic", "permissions", "quark"]
                        })
                        
                        if "error" not in vuln_result:
                            risk_level = vuln_result.get('vulnerabilities', {}).get('summary', {}).get('risk_level', 'LOW')
                            if risk_level in ['HIGH', 'CRITICAL']:
                                high_risk_apps.append({
                                    'app_id': app_id,
                                    'risk_level': risk_level,
                                    'vulnerability_count': vuln_result.get('vulnerabilities', {}).get('summary', {}).get('total_vulnerabilities', 0)
                                })
                    
                    # AI generates findings summary
                    if high_risk_apps:
                        print(f"  ⚠️  AI Detected {len(high_risk_apps)} high-risk applications:")
                        for app in high_risk_apps:
                            print(f"    🔴 App {app['app_id'][:8]}... - {app['risk_level']} ({app['vulnerability_count']} issues)")
                    else:
                        print(f"  ✅ AI Assessment: No critical vulnerabilities found")
        
        print("\n🎯 AI Analysis Complete!")
        print("🤖 AI can now generate detailed security reports, recommend patches, or trigger additional analysis")
        
    except Exception as e:
        print(f"❌ AI workflow failed: {e}")
    
    finally:
        await client.close()


async def main():
    """Main example function"""
    print("FirmwareDroid MCP Client Examples")
    print("=" * 60)
    
    print("\nNote: These examples demonstrate MCP client usage.")
    print("For real analysis, ensure:")
    print("  1. FirmwareDroid is running with sample data")
    print("  2. MCP server is started: python manage.py runmcp")
    print("  3. Replace example IDs with real database IDs")
    
    # Run basic functionality example
    await example_firmware_analysis()
    
    # Run AI workflow example
    await example_ai_security_workflow()
    
    print("\n" + "=" * 60)
    print("Examples completed! 🎉")
    print("\nThese examples show how AI models can:")
    print("  • Query firmware databases intelligently")
    print("  • Perform automated security analysis")
    print("  • Make decisions based on analysis results")
    print("  • Generate comprehensive security reports")


if __name__ == "__main__":
    asyncio.run(main())