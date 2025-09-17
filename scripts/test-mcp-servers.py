#!/usr/bin/env python3
"""
MCP Server Connection Test Script

This script tests the connectivity and basic functionality of configured MCP servers.
Run this script to validate your MCP server setup.
"""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional


class MCPServerTester:
    """Test MCP server configurations and connectivity."""
    
    def __init__(self, config_path: str = ".kiro/settings/mcp.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.results = {}
    
    def _load_config(self) -> Dict:
        """Load MCP configuration from file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Configuration file not found: {self.config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in configuration file: {e}")
            sys.exit(1)
    
    def _check_uvx_installed(self) -> bool:
        """Check if uvx is installed and available."""
        try:
            result = subprocess.run(['uvx', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _test_server_availability(self, server_name: str, server_config: Dict) -> Dict:
        """Test if an MCP server can be started and responds."""
        if server_config.get('disabled', False):
            return {
                'status': 'skipped',
                'message': 'Server is disabled in configuration'
            }
        
        try:
            # Test if the server package can be found and help command works
            command = server_config['command']
            args = server_config['args'] + ['--help']
            env = os.environ.copy()
            env.update(server_config.get('env', {}))
            
            result = subprocess.run(
                [command] + args,
                capture_output=True,
                text=True,
                timeout=30,
                env=env
            )
            
            if result.returncode == 0:
                return {
                    'status': 'success',
                    'message': 'Server package available and responsive'
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Server failed to start: {result.stderr.strip()}'
                }
                
        except subprocess.TimeoutExpired:
            return {
                'status': 'error',
                'message': 'Server startup timed out'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Unexpected error: {str(e)}'
            }
    
    def _check_prerequisites(self, server_name: str, server_config: Dict) -> List[Dict]:
        """Check prerequisites for specific servers."""
        checks = []
        
        if server_name == 'postgresql':
            # Check if PostgreSQL connection string is configured
            conn_str = server_config.get('env', {}).get('POSTGRES_CONNECTION_STRING', '')
            if not conn_str or conn_str == 'postgresql://localhost:5432/coins_for_change':
                checks.append({
                    'check': 'PostgreSQL connection string',
                    'status': 'warning',
                    'message': 'Using default connection string - update with actual credentials'
                })
            else:
                checks.append({
                    'check': 'PostgreSQL connection string',
                    'status': 'success',
                    'message': 'Connection string configured'
                })
        
        elif server_name == 'github':
            # Check if GitHub token is configured
            token = server_config.get('env', {}).get('GITHUB_PERSONAL_ACCESS_TOKEN', '')
            if not token:
                checks.append({
                    'check': 'GitHub Personal Access Token',
                    'status': 'error',
                    'message': 'GitHub token not configured - server will not work'
                })
            else:
                checks.append({
                    'check': 'GitHub Personal Access Token',
                    'status': 'success',
                    'message': 'GitHub token configured'
                })
        
        elif server_name == 'kubernetes':
            # Check if kubeconfig exists
            kubeconfig = server_config.get('env', {}).get('KUBECONFIG', '~/.kube/config')
            kubeconfig_path = Path(kubeconfig).expanduser()
            if kubeconfig_path.exists():
                checks.append({
                    'check': 'Kubeconfig file',
                    'status': 'success',
                    'message': f'Kubeconfig found at {kubeconfig_path}'
                })
            else:
                checks.append({
                    'check': 'Kubeconfig file',
                    'status': 'warning',
                    'message': f'Kubeconfig not found at {kubeconfig_path}'
                })
        
        elif server_name == 'docker':
            # Check if Docker is running
            try:
                result = subprocess.run(['docker', 'version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    checks.append({
                        'check': 'Docker daemon',
                        'status': 'success',
                        'message': 'Docker is running'
                    })
                else:
                    checks.append({
                        'check': 'Docker daemon',
                        'status': 'error',
                        'message': 'Docker is not running or not accessible'
                    })
            except (subprocess.TimeoutExpired, FileNotFoundError):
                checks.append({
                    'check': 'Docker daemon',
                    'status': 'error',
                    'message': 'Docker command not found or not responding'
                })
        
        elif server_name in ['confluence', 'vault']:
            # Check if optional servers have required configuration
            if server_config.get('disabled', True):
                checks.append({
                    'check': f'{server_name.title()} configuration',
                    'status': 'info',
                    'message': f'{server_name.title()} server is disabled (optional)'
                })
            else:
                checks.append({
                    'check': f'{server_name.title()} configuration',
                    'status': 'warning',
                    'message': f'{server_name.title()} server enabled but may need configuration'
                })
        
        return checks
    
    def test_all_servers(self) -> Dict:
        """Test all configured MCP servers."""
        print("🔍 Testing MCP Server Configuration")
        print("=" * 50)
        
        # First check if uvx is available
        if not self._check_uvx_installed():
            print("❌ uvx is not installed or not in PATH")
            print("   Install uv first: curl -LsSf https://astral.sh/uv/install.sh | sh")
            print("   Or using homebrew: brew install uv")
            return {'overall_status': 'failed', 'error': 'uvx not available'}
        
        print("✅ uvx is available")
        print()
        
        servers = self.config.get('mcpServers', {})
        if not servers:
            print("❌ No MCP servers configured")
            return {'overall_status': 'failed', 'error': 'no servers configured'}
        
        print(f"📋 Found {len(servers)} configured servers")
        print()
        
        overall_success = True
        
        for server_name, server_config in servers.items():
            print(f"🔧 Testing {server_name}...")
            
            # Check prerequisites
            prereq_checks = self._check_prerequisites(server_name, server_config)
            for check in prereq_checks:
                status_icon = {
                    'success': '✅',
                    'warning': '⚠️',
                    'error': '❌',
                    'info': 'ℹ️'
                }.get(check['status'], '❓')
                print(f"   {status_icon} {check['check']}: {check['message']}")
                
                if check['status'] == 'error':
                    overall_success = False
            
            # Test server availability
            server_result = self._test_server_availability(server_name, server_config)
            status_icon = {
                'success': '✅',
                'error': '❌',
                'skipped': '⏭️'
            }.get(server_result['status'], '❓')
            
            print(f"   {status_icon} Server availability: {server_result['message']}")
            
            if server_result['status'] == 'error':
                overall_success = False
            
            self.results[server_name] = {
                'prerequisites': prereq_checks,
                'availability': server_result
            }
            
            print()
        
        # Summary
        print("📊 Test Summary")
        print("=" * 50)
        
        success_count = sum(1 for result in self.results.values() 
                          if result['availability']['status'] == 'success')
        skipped_count = sum(1 for result in self.results.values() 
                          if result['availability']['status'] == 'skipped')
        error_count = sum(1 for result in self.results.values() 
                        if result['availability']['status'] == 'error')
        
        print(f"✅ Successful: {success_count}")
        print(f"⏭️ Skipped: {skipped_count}")
        print(f"❌ Failed: {error_count}")
        
        if overall_success and error_count == 0:
            print("\n🎉 All enabled MCP servers are configured correctly!")
            print("   You can now use these servers in Kiro.")
        else:
            print(f"\n⚠️ {error_count} server(s) have issues that need to be resolved.")
            print("   Check the error messages above and refer to the documentation.")
        
        return {
            'overall_status': 'success' if overall_success and error_count == 0 else 'partial',
            'results': self.results,
            'summary': {
                'success': success_count,
                'skipped': skipped_count,
                'failed': error_count
            }
        }


def main():
    """Main function to run MCP server tests."""
    tester = MCPServerTester()
    results = tester.test_all_servers()
    
    # Exit with appropriate code
    if results['overall_status'] == 'success':
        sys.exit(0)
    elif results['overall_status'] == 'partial':
        sys.exit(1)  # Some issues but not complete failure
    else:
        sys.exit(2)  # Complete failure


if __name__ == "__main__":
    main()