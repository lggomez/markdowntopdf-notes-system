#!/usr/bin/env python3
"""
Dependency checking and validation for markdown-to-pdf converter.
Provides platform-specific installation guidance.

MIT License - Copyright (c) 2025 Markdown to PDF Converter
"""

import subprocess
import sys
import platform
from typing import Tuple, List, Optional
from colorama import Fore, Style, init

init(autoreset=True)


class DependencyChecker:
    """Check and report on required and optional dependencies."""
    
    def __init__(self):
        """Initialize dependency checker."""
        self.system = platform.system()
        self.missing_python_packages: List[str] = []
        self.missing_external_tools: List[Tuple[str, str]] = []  # (name, install_instructions)
    
    def check_python_package(self, package_name: str, import_name: Optional[str] = None) -> bool:
        """Check if a Python package is installed."""
        if import_name is None:
            import_name = package_name
        
        try:
            __import__(import_name)
            return True
        except ImportError:
            self.missing_python_packages.append(package_name)
            return False
    
    def check_external_tool(self, command: str, name: str, install_instructions: str) -> bool:
        """Check if an external tool is available."""
        try:
            subprocess.run(
                [command, "--version"],
                capture_output=True,
                check=True,
                timeout=5
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            self.missing_external_tools.append((name, install_instructions))
            return False
    
    def check_playwright_browsers(self) -> bool:
        """Check if Playwright browsers are installed."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "playwright", "install", "--dry-run", "chromium"],
                capture_output=True,
                text=True,
                timeout=10
            )
            # If chromium is already installed, dry-run will succeed
            # If not installed, it will mention installation
            return "chromium" in result.stdout.lower() or result.returncode == 0
        except Exception:
            return False
    
    def get_playwright_install_command(self) -> str:
        """Get platform-specific Playwright install command."""
        return f"{sys.executable} -m playwright install chromium"
    
    def get_pandoc_install_instructions(self) -> str:
        """Get platform-specific Pandoc installation instructions."""
        if self.system == "Windows":
            return "Download from https://pandoc.org/installing.html and add to PATH"
        elif self.system == "Darwin":  # macOS
            return "brew install pandoc"
        else:  # Linux
            return "sudo apt-get install pandoc  # or: sudo yum install pandoc"
    
    def get_calibre_install_instructions(self) -> str:
        """Get platform-specific Calibre installation instructions."""
        if self.system == "Windows":
            return "Download from https://calibre-ebook.com/download and install"
        elif self.system == "Darwin":  # macOS
            return "brew install --cask calibre"
        else:  # Linux
            return "Visit https://calibre-ebook.com/download_linux for installation instructions"
    
    def check_all(self, check_optional: bool = False) -> Tuple[bool, List[str]]:
        """Check all dependencies and return status and messages."""
        messages: List[str] = []
        all_ok = True
        
        # Check Python packages
        print(f"{Fore.CYAN}Checking Python packages...{Style.RESET_ALL}")
        
        if not self.check_python_package("playwright", "playwright"):
            all_ok = False
            messages.append(f"{Fore.RED}[MISSING]{Style.RESET_ALL} playwright - Run: pip install playwright")
            messages.append(f"  Then install browser: {self.get_playwright_install_command()}")
        else:
            print(f"{Fore.GREEN}[OK]{Style.RESET_ALL} playwright is available")
            
            if not self.check_playwright_browsers():
                all_ok = False
                messages.append(f"{Fore.YELLOW}[WARNING]{Style.RESET_ALL} Playwright browsers not installed")
                messages.append(f"  Run: {self.get_playwright_install_command()}")
            else:
                print(f"{Fore.GREEN}[OK]{Style.RESET_ALL} Playwright browsers are installed")
        
        if not self.check_python_package("plantuml", "plantuml"):
            all_ok = False
            messages.append(f"{Fore.RED}[MISSING]{Style.RESET_ALL} plantuml - Run: pip install plantuml")
        else:
            print(f"{Fore.GREEN}[OK]{Style.RESET_ALL} plantuml is available")
        
        if not self.check_python_package("colorama", "colorama"):
            all_ok = False
            messages.append(f"{Fore.RED}[MISSING]{Style.RESET_ALL} colorama - Run: pip install colorama")
        else:
            print(f"{Fore.GREEN}[OK]{Style.RESET_ALL} colorama is available")
        
        # Check external tools
        print(f"\n{Fore.CYAN}Checking external tools...{Style.RESET_ALL}")
        
        if not self.check_external_tool("pandoc", "Pandoc", self.get_pandoc_install_instructions()):
            all_ok = False
            messages.append(f"{Fore.RED}[MISSING]{Style.RESET_ALL} pandoc (required)")
            messages.append(f"  {self.get_pandoc_install_instructions()}")
        else:
            print(f"{Fore.GREEN}[OK]{Style.RESET_ALL} Pandoc is available")
        
        # Check optional dependencies
        if check_optional:
            if not self.check_external_tool("ebook-convert", "Calibre", self.get_calibre_install_instructions()):
                messages.append(f"{Fore.YELLOW}[OPTIONAL]{Style.RESET_ALL} Calibre (required for MOBI format)")
                messages.append(f"  {self.get_calibre_install_instructions()}")
            else:
                print(f"{Fore.GREEN}[OK]{Style.RESET_ALL} Calibre is available")
        
        return all_ok, messages
    
    def print_summary(self, check_optional: bool = False) -> bool:
        """Check dependencies and print summary. Returns True if all required deps are available."""
        all_ok, messages = self.check_all(check_optional)
        
        if messages:
            print(f"\n{Fore.YELLOW}Dependency Summary:{Style.RESET_ALL}")
            for msg in messages:
                print(f"  {msg}")
        else:
            print(f"\n{Fore.GREEN}All dependencies are available!{Style.RESET_ALL}")
        
        return all_ok


def check_dependencies(check_optional: bool = False) -> bool:
    """Convenience function to check dependencies."""
    checker = DependencyChecker()
    return checker.print_summary(check_optional)

