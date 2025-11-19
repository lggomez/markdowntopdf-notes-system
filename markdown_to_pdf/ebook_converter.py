#!/usr/bin/env python3
"""
Markdown to Ebook converter supporting PDF, EPUB, and MOBI formats.
Extends the original PDF converter with multi-format support.

MIT License - Copyright (c) 2025 Markdown to PDF Converter
"""

import os
import sys
import subprocess
import tempfile
import shutil
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import asyncio
from playwright.async_api import async_playwright
import plantuml
from colorama import init, Fore, Back, Style
from PIL import Image, ImageFilter
from .verification import DocumentStateManager, calculate_file_hash
from .config import Config
from .dependencies import check_dependencies
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Initialize colorama for cross-platform colored output
init(autoreset=True)


class MarkdownToEbookConverter:
    """Markdown to Ebook converter supporting PDF, EPUB, and MOBI formats."""
    
    # Style profiles configuration
    STYLE_PROFILES = {
        "a4-print": {
            "name": "A4 Print (Default)",
            "description": "Standard print-optimized styling with 12px base font",
            "font_scale": 1.0,
            "base_font_size": "12px",
            "formats": ["pdf"]
        },
        "a4-screen": {
            "name": "A4 Screen (Large)",
            "description": "Screen-optimized styling with 30% larger fonts for better readability",
            "font_scale": 1.3,
            "base_font_size": "15.6px",
            "formats": ["pdf"]
        },
        "kindle-basic": {
            "name": "Kindle Basic",
            "description": "Basic Kindle formatting optimized for e-ink displays",
            "font_scale": 1.0,
            "base_font_size": "12px",
            "formats": ["epub", "mobi"]
        },
        "kindle-large": {
            "name": "Kindle Large Text",
            "description": "Large text for better readability on Kindle devices",
            "font_scale": 1.2,
            "base_font_size": "14px",
            "formats": ["epub", "mobi"]
        },
        "kindle-paperwhite-11": {
            "name": "Kindle Paperwhite 11th Gen",
            "description": "Optimized for Kindle Paperwhite 11th generation (6.8\" 300ppi display)",
            "font_scale": 1.1,
            "base_font_size": "13px",
            "formats": ["epub", "mobi"]
        }
    }
    
    def __init__(self, source_dir: str, output_dir: str, temp_dir: str, 
                 output_format: str = "pdf", page_margins: str = "1in 0.75in", 
                 debug: bool = False, db_path: Optional[str] = None, 
                 style_profile: str = "a4-print", max_workers: int = 4,
                 author: str = "Unknown Author", language: str = "en",
                 max_diagram_width = 1680, max_diagram_height = 2240):
        """Initialize the converter.
        
        Args:
            max_diagram_width: Max width in pixels (int, only resize if rendered exceeds) or percentage of rendered size (str like "80%")
            max_diagram_height: Max height in pixels (int, only resize if rendered exceeds) or percentage of rendered size (str like "80%")
        """
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.temp_dir = Path(temp_dir)
        self.output_format = output_format.lower()
        self.page_margins = page_margins
        self.debug = debug
        self.style_profile = style_profile
        self.max_workers = max_workers
        self.author = author
        self.language = language
        self.diagram_width = max_diagram_width
        self.diagram_height = max_diagram_height
        self._lock = threading.Lock()  # For thread-safe logging
        
        # Create format-specific output directory
        self.format_output_dir = self.output_dir / self.output_format
        
        # Validate output format
        valid_formats = ["pdf", "epub", "mobi"]
        if self.output_format not in valid_formats:
            raise ValueError(f"Invalid output format '{self.output_format}'. Valid formats: {valid_formats}")
        
        # Validate style profile
        if style_profile not in self.STYLE_PROFILES:
            available_profiles = ", ".join(self.STYLE_PROFILES.keys())
            raise ValueError(f"Invalid style profile '{style_profile}'. Available profiles: {available_profiles}")
        
        # Check if style profile supports the output format
        profile = self.STYLE_PROFILES[self.style_profile]
        if self.output_format not in profile["formats"]:
            supported_formats = ", ".join(profile["formats"])
            raise ValueError(f"Style profile '{style_profile}' does not support format '{self.output_format}'. Supported formats: {supported_formats}")
        
        # Initialize document state manager with configurable db_path
        if db_path is None:
            config = Config()
            db_path = config.get_db_path()
        self.state_manager = DocumentStateManager(db_path)
        
        # Create directories
        self.output_dir.mkdir(exist_ok=True)
        self.format_output_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        
        # Log configuration
        profile_info = self.STYLE_PROFILES[self.style_profile]
        self._log_info(f"Using style profile: {profile_info['name']} - {profile_info['description']}")
        self._log_info(f"Output format: {self.output_format.upper()}")
        self._log_debug(f"Default diagram dimensions: {self.diagram_width}x{self.diagram_height}px")
    
    def _log_debug(self, message: str) -> None:
        """Log debug message with color (only if debug mode is enabled)."""
        if self.debug:
            with self._lock:
                print(f"{Fore.CYAN}[DEBUG]{Style.RESET_ALL} {message}")
    
    def _log_info(self, message: str) -> None:
        """Log info message with color."""
        with self._lock:
            print(f"{Fore.GREEN}[INFO]{Style.RESET_ALL} {message}")
    
    def _log_warning(self, message: str) -> None:
        """Log warning message with color."""
        with self._lock:
            print(f"{Fore.YELLOW}[WARNING]{Style.RESET_ALL} {message}")
    
    def _log_error(self, message: str) -> None:
        """Log error message with color."""
        with self._lock:
            print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {message}")
    
    def _log_success(self, message: str) -> None:
        """Log success message with color."""
        with self._lock:
            print(f"{Fore.GREEN}[OK]{Style.RESET_ALL} {message}")
    
    def _validate_margin(self, margin_str: str) -> str:
        """Validate and normalize a single margin value."""
        import re
        
        # Extract numeric value and unit
        match = re.match(r'^(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*(cm|in|mm|pt|px)?$', margin_str.strip())
        if not match:
            raise ValueError(f"Invalid margin format: '{margin_str}'. Use format like '1in', '2.5cm', '10mm', etc.")
        
        value_str, unit = match.groups()
        value = float(value_str)
        
        # Set default unit to 'in' if not specified
        if not unit:
            unit = 'in'
        
        # Convert to inches for validation
        if unit == 'cm':
            value_inches = value / 2.54
        elif unit == 'mm':
            value_inches = value / 25.4
        elif unit == 'pt':
            value_inches = value / 72
        elif unit == 'px':
            value_inches = value / 96  # Assuming 96 DPI
        else:  # 'in'
            value_inches = value
        
        # Validate range: minimum 0 inches, maximum 3 inches
        if value_inches < 0:
            raise ValueError(f"Margin cannot be negative: '{margin_str}'. Minimum value is 0.")
        elif value_inches > 3:
            raise ValueError(f"Margin too large: '{margin_str}'. Maximum value is 3 inches (7.62cm).")
        
        return f"{value}{unit}"
    
    def _parse_margins(self) -> Dict[str, str]:
        """Parse margin string into individual margin values."""
        margin_parts = self.page_margins.split()
        
        if len(margin_parts) == 1:
            # All margins same
            margin = self._validate_margin(margin_parts[0])
            return {'top': margin, 'right': margin, 'bottom': margin, 'left': margin}
        elif len(margin_parts) == 2:
            # Vertical and horizontal
            vertical = self._validate_margin(margin_parts[0])
            horizontal = self._validate_margin(margin_parts[1])
            return {'top': vertical, 'right': horizontal, 'bottom': vertical, 'left': horizontal}
        elif len(margin_parts) == 4:
            # Top, right, bottom, left
            return {
                'top': self._validate_margin(margin_parts[0]),
                'right': self._validate_margin(margin_parts[1]),
                'bottom': self._validate_margin(margin_parts[2]),
                'left': self._validate_margin(margin_parts[3])
            }
        else:
            raise ValueError(f"Invalid margin format: '{self.page_margins}'. Use 1, 2, or 4 values.")
    
    def _convert_margin_to_cm(self, margin_str: str) -> float:
        """Convert margin string to centimeters for Puppeteer."""
        import re
        
        match = re.match(r'^(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*(cm|in|mm|pt|px)?$', margin_str.strip())
        if not match:
            return 2.54  # default 1 inch in cm
        
        value_str, unit = match.groups()
        value = float(value_str)
        
        if not unit:
            unit = 'in'
        
        # Convert to cm
        if unit == 'cm':
            return value
        elif unit == 'in':
            return value * 2.54
        elif unit == 'mm':
            return value / 10
        elif unit == 'pt':
            return value * 0.0352778
        elif unit == 'px':
            return value * 0.0264583
        else:
            return value * 2.54
    
    def _get_viewport_dimensions(self) -> tuple[int, int]:
        """Get viewport dimensions for diagram rendering (always integers).
        
        Returns:
            Tuple of (width, height) in pixels for viewport size
        """
        # Default viewport size for rendering
        default_width = 1680
        default_height = 2240
        
        # If diagram dimensions are integers, use them for viewport
        # If they're percentages, use defaults (resizing happens after rendering)
        if isinstance(self.diagram_width, int):
            width = self.diagram_width
        else:
            width = default_width
            
        if isinstance(self.diagram_height, int):
            height = self.diagram_height
        else:
            height = default_height
            
        return width, height
    
    def _parse_dimension_value(self, value, original_size: int) -> Optional[int]:
        """Parse dimension value that can be max pixels (int) or percentage (str).
        
        Args:
            value: int for max pixels (only resize if original exceeds), 
                   str like "80%" for percentage of original (always applied, max 100%)
            original_size: Original dimension in pixels (for percentage calculation)
            
        Returns:
            Target dimension in pixels, or None if no resizing needed
        """
        if value is None:
            return None
            
        # If it's already an int (max pixels constraint)
        if isinstance(value, int):
            # Only resize if original exceeds the max
            if original_size > value:
                return value
            else:
                return None  # Keep original size
            
        # If it's a string, check for percentage
        if isinstance(value, str):
            value_stripped = value.strip()
            if value_stripped.endswith('%'):
                try:
                    percent = float(value_stripped[:-1])
                    if percent > 0:
                        # Always apply percentage (supports both downsizing and upscaling)
                        return int(original_size * percent / 100.0)
                except ValueError:
                    pass
            else:
                # Try parsing as int string
                try:
                    parsed_int = int(value_stripped)
                    # Only resize if original exceeds the max
                    if original_size > parsed_int:
                        return parsed_int
                    else:
                        return None  # Keep original size
                except ValueError:
                    pass
        
        return None
    
    def _resize_image(self, image_path: Path, max_width = None, max_height = None) -> bool:
        """Resize image while maintaining aspect ratio.
        
        Args:
            image_path: Path to the image file
            max_width: Maximum width - int (pixels), str ("80%"), or None (uses self.diagram_width)
            max_height: Maximum height - int (pixels), str ("80%"), or None (uses self.diagram_height)
            
        Returns:
            True if resize was successful, False otherwise
        """
        try:
            if max_width is None:
                max_width = self.diagram_width
            if max_height is None:
                max_height = self.diagram_height
            
            # Open the image
            with Image.open(image_path) as img:
                # Get original dimensions
                orig_width, orig_height = img.size
                
                self._log_debug(f"Checking resize for {image_path.name}: original={orig_width}x{orig_height}, max={max_width}x{max_height}")
                
                # Parse dimensions (resolve percentages based on original size)
                target_width = self._parse_dimension_value(max_width, orig_width)
                target_height = self._parse_dimension_value(max_height, orig_height)
                
                self._log_debug(f"Parsed target dimensions: width={target_width}, height={target_height}")
                
                # If no valid dimensions, skip resize
                if target_width is None and target_height is None:
                    self._log_debug(f"Image {orig_width}x{orig_height} is within max constraints {max_width}x{max_height}, no resize needed")
                    return True
                
                # Calculate scaling factor to fit within target dimensions while maintaining aspect ratio
                if target_width is not None and target_height is not None:
                    width_ratio = target_width / orig_width
                    height_ratio = target_height / orig_height
                    scale_factor = min(width_ratio, height_ratio)
                elif target_width is not None:
                    scale_factor = target_width / orig_width
                else:  # target_height is not None
                    scale_factor = target_height / orig_height
                
                # Only resize if scale factor differs from 1.0
                if scale_factor != 1.0:
                    new_width = int(orig_width * scale_factor)
                    new_height = int(orig_height * scale_factor)
                    
                    is_upscaling = scale_factor > 1.0
                    
                    # Resize using high-quality Lanczos resampling (best for both up and downscaling)
                    resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Apply sharpening optimized for the scaling direction
                    if is_upscaling:
                        # For upscaling: Use stronger sharpening to enhance details and reduce softness
                        # radius: larger for upscaling to cover more area
                        # percent: higher to enhance edges more aggressively
                        # threshold: lower to sharpen more details
                        sharpened = resized_img.filter(ImageFilter.UnsharpMask(radius=1.0, percent=200, threshold=2))
                    else:
                        # For downscaling: Use moderate sharpening to compensate for resize blur
                        sharpened = resized_img.filter(ImageFilter.UnsharpMask(radius=0.5, percent=150, threshold=3))
                    
                    # Save with maximum quality settings
                    # For PNG: compress_level 0-9 (higher = smaller file but still lossless)
                    # For JPEG: quality 95-100 (near-lossless)
                    if image_path.suffix.lower() in ['.png']:
                        sharpened.save(image_path, format='PNG', compress_level=6, optimize=False)
                    elif image_path.suffix.lower() in ['.jpg', '.jpeg']:
                        sharpened.save(image_path, format='JPEG', quality=100, subsampling=0, optimize=False)
                    else:
                        sharpened.save(image_path, optimize=False)
                    
                    scale_direction = "upscaled" if is_upscaling else "downscaled"
                    self._log_debug(f"Resized image from {orig_width}x{orig_height} to {new_width}x{new_height} ({scale_direction} with optimized sharpening)")
                else:
                    self._log_debug(f"Image {orig_width}x{orig_height} already within target bounds, no resize needed")
            
            return True
            
        except Exception as e:
            self._log_error(f"Failed to resize image {image_path}: {e}")
            return False
    
    async def _render_mermaid_diagram(self, mermaid_code: str, output_path: Path) -> tuple[bool, str]:
        """Render Mermaid diagram to image using Playwright."""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Set viewport for high-resolution rendering using fixed pixel dimensions
                viewport_width, viewport_height = self._get_viewport_dimensions()
                await page.set_viewport_size({"width": viewport_width, "height": viewport_height})
                await page.emulate_media(media="screen")
                
                # Create HTML with Mermaid
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <script src="https://unpkg.com/mermaid@10.6.1/dist/mermaid.min.js"></script>
                    <style>
                        body {{
                            margin: 0;
                            padding: 10px;
                            background: white;
                            font-family: Arial, sans-serif;
                        }}
                        .mermaid {{
                            text-align: center;
                            background: white;
                            display: inline-block;
                            padding: 5px;
                        }}
                        .mermaid svg {{
                            max-width: none;
                            height: auto;
                            display: block;
                            font-family: Arial, sans-serif;
                        }}
                        .mermaid .node rect {{
                            rx: 3;
                            ry: 3;
                        }}
                        .mermaid .edgePath .path {{
                            stroke-width: 1.5px;
                        }}
                    </style>
                </head>
                <body>
                    <div class="mermaid">
                        {mermaid_code}
                    </div>
                    <script>
                        // Load Mermaid configuration from file if available
                        let mermaidConfig = {{
                            startOnLoad: true,
                            theme: 'default',
                            themeVariables: {{
                                primaryColor: '#ff6b6b',
                                primaryTextColor: '#333',
                                primaryBorderColor: '#ff6b6b',
                                lineColor: '#333',
                                secondaryColor: '#4ecdc4',
                                tertiaryColor: '#45b7d1'
                            }},
                            flowchart: {{
                                useMaxWidth: false,
                                htmlLabels: true,
                                curve: 'basis',
                                nodeSpacing: 30,
                                rankSpacing: 30,
                                diagramMarginX: 10,
                                diagramMarginY: 5
                            }},
                            sequence: {{
                                useMaxWidth: false,
                                diagramMarginY: 3,
                                diagramMarginX: 10,
                                messageFontSize: 12,
                                actorFontSize: 12,
                                actorMargin: 20,
                                messageMargin: 10
                            }},
                            gantt: {{
                                useMaxWidth: false
                            }},
                            graph: {{
                                useMaxWidth: false,
                                nodeSpacing: 30,
                                rankSpacing: 30,
                                diagramMarginX: 10,
                                diagramMarginY: 5
                            }}
                        }};
                        
                        mermaid.initialize(mermaidConfig);
                    </script>
                </body>
                </html>
                """
                
                await page.set_content(html_content)
                
                # Wait for Mermaid to render
                await page.wait_for_timeout(3000)
                
                # Get the mermaid element and take screenshot of just that element
                mermaid_element = await page.query_selector('.mermaid')
                if mermaid_element:
                    # Get the bounding box of the mermaid element
                    bounding_box = await mermaid_element.bounding_box()
                    if bounding_box:
                        # Take high-resolution screenshot of just the mermaid element
                        await mermaid_element.screenshot(
                            path=str(output_path), 
                            type='png',
                            scale='device'
                        )
                    else:
                        # Fallback to full page if bounding box not available
                        await page.screenshot(
                            path=str(output_path), 
                            type='png', 
                            full_page=True,
                            scale='device'
                        )
                else:
                    # Fallback to full page if mermaid element not found
                    await page.screenshot(
                        path=str(output_path), 
                        type='png', 
                        full_page=True,
                        scale='device'
                    )
                
                await browser.close()
                
                return True, ""
                
        except Exception as e:
            error_msg = f"Failed to render Mermaid diagram: {e}"
            self._log_error(error_msg)
            return False, error_msg
    
    def _render_plantuml_diagram(self, plantuml_code: str, output_path: Path) -> tuple[bool, str]:
        """Render PlantUML diagram to image using the plantuml library."""
        try:
            # Create PlantUML instance with HTTPS server URL and PNG endpoint
            puml = plantuml.PlantUML(url='https://www.plantuml.com/plantuml/png/')
            
            # Render the diagram to PNG and get raw image data
            image_data = puml.processes(plantuml_code)
            
            # Write the image data to file
            with open(output_path, 'wb') as f:
                f.write(image_data)
            
            # Check if the file was created successfully
            if output_path.exists() and output_path.stat().st_size > 0:
                self._log_debug(f"PlantUML diagram rendered successfully to: {output_path}")
                return True, ""
            else:
                error_msg = "PlantUML diagram file was not created or is empty"
                self._log_error(error_msg)
                return False, error_msg
                
        except Exception as e:
            # Handle exception carefully - some PlantUML exceptions don't have proper string representation
            error_type = type(e).__name__
            try:
                error_details = str(e)
            except:
                error_details = "Unknown error (exception string conversion failed)"
            error_msg = f"Failed to render PlantUML diagram: {error_type}: {error_details}"
            self._log_error(error_msg)
            return False, error_msg
    
    def _replace_mermaid_with_images(self, content: str, file_id: str = "") -> str:
        """Replace Mermaid code blocks with image references.
        
        Supports HTML comment modifiers on line above diagram:
        <!-- no-resize -->
        ```mermaid
        graph TD
            A --> B
        ```
        
        <!-- upscale:150% -->
        ```mermaid
        graph TD
            A --> B
        ```
        """
        import re
        
        # Pattern to match optional HTML comment modifiers on line above, followed by mermaid block
        # Handles both Unix (\n) and Windows (\r\n) line endings
        # Captures: no-resize OR upscale:X% OR downscale:X%
        mermaid_pattern = r'(?:<!--\s*(?:(no-resize)|upscale:(\d+)%|downscale:(\d+)%)\s*-->\s*\r?\n)?```mermaid\r?\n(.*?)\r?\n```'
        
        # Find all matches with their modifiers
        matches = list(re.finditer(mermaid_pattern, content, re.DOTALL | re.IGNORECASE))
        
        for i, match in enumerate(matches):
            no_resize_modifier = match.group(1)  # "no-resize" or None
            upscale_percent = match.group(2)  # percentage digits for upscale or None
            downscale_percent = match.group(3)  # percentage digits for downscale or None
            mermaid_code = match.group(4)
            full_block = match.group(0)
            
            # Determine resize behavior
            skip_resize = no_resize_modifier is not None
            custom_scale = None
            scale_type = None
            if upscale_percent:
                custom_scale = f"{upscale_percent}%"
                scale_type = "upscale"
            elif downscale_percent:
                # For downscale, use percentage directly (must be 0-99%)
                # downscale:67% means scale to 67% of original size
                percent_value = float(downscale_percent)
                if percent_value > 0 and percent_value < 100:
                    custom_scale = f"{downscale_percent}%"
                    scale_type = "downscale"
                else:
                    self._log_warning(f"Downscale percentage must be between 0-99%, got {downscale_percent}%. Ignoring modifier.")
            
            # Create unique image path using file_id to avoid race conditions
            image_path = self.temp_dir / f"mermaid_diagram_{file_id}_{i}.png"
            
            # Render Mermaid diagram
            modifier_info = ""
            if skip_resize:
                modifier_info = " (no-resize)"
            elif custom_scale and scale_type:
                modifier_info = f" ({scale_type}:{custom_scale})"
            self._log_debug(f"Rendering Mermaid diagram {i} to: {image_path}{modifier_info}")
            
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                success, error_msg = loop.run_until_complete(
                    self._render_mermaid_diagram(mermaid_code, image_path)
                )
                if success:
                    # Resize the rendered image based on modifiers
                    if skip_resize:
                        self._log_debug(f"Skipping resize for Mermaid diagram {i} due to no-resize modifier")
                    elif custom_scale:
                        action = "upscaling" if scale_type == "upscale" else "downscaling"
                        self._log_debug(f"Applying custom {action} {custom_scale} to Mermaid diagram {i}")
                        self._resize_image(image_path, max_width=custom_scale, max_height=custom_scale)
                    else:
                        # Use default resize settings
                        self._resize_image(image_path)
                    
                    self._log_debug(f"Mermaid diagram rendered successfully, using path: {image_path}")
                    # Replace the code block with image reference
                    content = content.replace(
                        full_block,
                        f"![]({image_path})"
                    )
                else:
                    self._log_error(f"Failed to render Mermaid diagram {i}")
                    # Insert error placeholder with actual error message
                    error_placeholder = self._create_diagram_error_placeholder("Mermaid", i, mermaid_code, error_msg)
                    content = content.replace(
                        full_block,
                        error_placeholder
                    )
            finally:
                loop.close()
        
        return content
    
    def _replace_plantuml_with_images(self, content: str, file_id: str = "") -> str:
        """Replace PlantUML code blocks with image references.
        
        Supports HTML comment modifiers on line above diagram:
        <!-- no-resize -->
        ```plantuml
        @startuml
        A -> B
        @enduml
        ```
        
        <!-- upscale:150% -->
        ```plantuml
        @startuml
        A -> B
        @enduml
        ```
        """
        import re
        
        # Pattern to match optional HTML comment modifiers on line above, followed by plantuml block
        # Handles both Unix (\n) and Windows (\r\n) line endings
        # Captures: no-resize OR upscale:X% OR downscale:X%
        plantuml_pattern = r'(?:<!--\s*(?:(no-resize)|upscale:(\d+)%|downscale:(\d+)%)\s*-->\s*\r?\n)?```plantuml\r?\n(.*?)\r?\n```'
        
        # Find all matches with their modifiers
        matches = list(re.finditer(plantuml_pattern, content, re.DOTALL | re.IGNORECASE))
        
        for i, match in enumerate(matches):
            no_resize_modifier = match.group(1)  # "no-resize" or None
            upscale_percent = match.group(2)  # percentage digits for upscale or None
            downscale_percent = match.group(3)  # percentage digits for downscale or None
            plantuml_code = match.group(4)
            full_block = match.group(0)
            
            # Determine resize behavior
            skip_resize = no_resize_modifier is not None
            custom_scale = None
            scale_type = None
            if upscale_percent:
                custom_scale = f"{upscale_percent}%"
                scale_type = "upscale"
            elif downscale_percent:
                # For downscale, use percentage directly (must be 0-99%)
                # downscale:67% means scale to 67% of original size
                percent_value = float(downscale_percent)
                if percent_value > 0 and percent_value < 100:
                    custom_scale = f"{downscale_percent}%"
                    scale_type = "downscale"
                else:
                    self._log_warning(f"Downscale percentage must be between 0-99%, got {downscale_percent}%. Ignoring modifier.")
            
            # Create unique image path using file_id to avoid race conditions
            image_path = self.temp_dir / f"plantuml_diagram_{file_id}_{i}.png"
            
            # Render PlantUML diagram
            modifier_info = ""
            if skip_resize:
                modifier_info = " (no-resize)"
            elif custom_scale and scale_type:
                modifier_info = f" ({scale_type}:{custom_scale})"
            self._log_debug(f"Rendering PlantUML diagram {i} to: {image_path}{modifier_info}")
            
            success, error_msg = self._render_plantuml_diagram(plantuml_code, image_path)
            if success:
                # Resize the rendered image based on modifiers
                if skip_resize:
                    self._log_debug(f"Skipping resize for PlantUML diagram {i} due to no-resize modifier")
                elif custom_scale:
                    action = "upscaling" if scale_type == "upscale" else "downscaling"
                    self._log_debug(f"Applying custom {action} {custom_scale} to PlantUML diagram {i}")
                    self._resize_image(image_path, max_width=custom_scale, max_height=custom_scale)
                else:
                    # Use default resize settings
                    self._resize_image(image_path)
                
                self._log_debug(f"PlantUML diagram rendered successfully, using path: {image_path}")
                # Replace the code block with image reference
                content = content.replace(
                    full_block,
                    f"![]({image_path})"
                )
            else:
                self._log_error(f"Failed to render PlantUML diagram {i}")
                # Insert error placeholder with actual error message
                error_placeholder = self._create_diagram_error_placeholder("PlantUML", i, plantuml_code, error_msg)
                content = content.replace(
                    full_block,
                    error_placeholder
                )
        
        return content
    
    def _create_diagram_error_placeholder(self, diagram_type: str, diagram_index: int, diagram_code: str, error_message: str = "") -> str:
        """Create a formatted error placeholder for failed diagram rendering."""
        # Truncate diagram code for display (first 60 characters)
        truncated_code = diagram_code[:60] + "..." if len(diagram_code) > 60 else diagram_code
        
        # Create a compact formatted error message
        error_placeholder = f"""
<div style="border: 1px solid #ff6b6b; border-radius: 4px; padding: 8px; margin: 8px 0; background-color: #fff5f5; font-family: Arial, sans-serif; font-size: 0.85em;">
    <div style="color: #d63031; font-weight: bold; margin-bottom: 4px;">
        ⚠️ {diagram_type} Diagram Failed
    </div>
    <div style="color: #2d3436; margin-bottom: 4px; font-size: 0.9em;">
        <strong>Error:</strong> {error_message if error_message else "Unknown error occurred during diagram rendering"}
    </div>
    <div style="color: #636e72; font-size: 0.8em; margin-bottom: 2px;">
        <strong>Code:</strong> <code style="background-color: #f8f9fa; padding: 1px 3px; border-radius: 2px;">{truncated_code}</code>
    </div>
</div>
"""
        return error_placeholder
    
    def _process_page_breaks(self, content: str) -> str:
        """Process page break markers in markdown content."""
        import re
        
        # For ebook formats, convert page breaks to chapter breaks or remove them
        if self.output_format in ["epub", "mobi"]:
            # Remove page breaks for ebook formats as they don't make sense
            content = re.sub(r'<!--\s*page-break\s*-->', '', content, flags=re.IGNORECASE)
            content = re.sub(r'<div class="page-break"></div>', '', content)
            content = re.sub(r'```page-break\n```', '', content, flags=re.IGNORECASE)
            content = re.sub(r'<page-break>', '', content, flags=re.IGNORECASE)
            content = re.sub(r'---\s*\n\s*\{\.page-break\}', '', content, flags=re.IGNORECASE | re.MULTILINE)
        else:
            # Keep page breaks for PDF
            content = re.sub(r'<!--\s*page-break\s*-->', '<div class="page-break"></div>', content, flags=re.IGNORECASE)
            content = re.sub(r'```page-break\n```', '<div class="page-break"></div>', content, flags=re.IGNORECASE)
            content = re.sub(r'<page-break>', '<div class="page-break"></div>', content, flags=re.IGNORECASE)
            content = re.sub(r'---\s*\n\s*\{\.page-break\}', '<div class="page-break"></div>', content, flags=re.IGNORECASE | re.MULTILINE)
        
        return content
    
    def _filter_sections_for_print(self, content: str) -> str:
        """Filter out sections that should be ignored for print profiles."""
        import re
        
        # For print profiles, remove Table of contents sections
        if self.style_profile in ["a4-print", "a4-screen"]:
            # Pattern to match "## Table of contents" or "### Table of contents" heading and everything until the next heading
            toc_pattern = r'^#{2,3}\s+Table\s+of\s+contents\s*$.*?(?=^#{1,3}\s|\Z)'
            
            # Use MULTILINE and DOTALL flags to match across lines
            filtered_content = re.sub(toc_pattern, '', content, flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)
            
            # Clean up any extra whitespace that might be left
            filtered_content = re.sub(r'\n\s*\n\s*\n', '\n\n', filtered_content)
            
            # Log the filtering action
            if filtered_content != content:
                self._log_debug("Filtered out 'Table of contents' section for print profile")
            
            return filtered_content
        
        return content
    
    def _process_and_embed_images(self, content: str, md_file: Path) -> str:
        """Process and embed referenced images into the temp directory."""
        import re
        import shutil
        
        # Find all image references (both markdown and HTML img tags)
        markdown_img_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        html_img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
        
        processed_content = content
        md_dir = md_file.parent
        
        # Process markdown image references
        for match in re.finditer(markdown_img_pattern, content):
            alt_text = match.group(1)
            img_path = match.group(2)
            
            # Skip if it's already a temp file or absolute URL
            if img_path.startswith('http') or img_path.startswith('data:'):
                continue
            
            # Check if this is a diagram generated by our script (Mermaid or PlantUML)
            if img_path.startswith('temp/') or img_path.startswith('temp\\'):
                # Convert relative temp path to absolute path for pandoc
                if not os.path.isabs(img_path):
                    # Convert to absolute path
                    abs_img_path = self.temp_dir / img_path.replace('temp/', '').replace('temp\\', '')
                    if abs_img_path.exists():
                        # Replace the relative path with absolute path
                        processed_content = processed_content.replace(
                            f"]({img_path})",
                            f"]({abs_img_path})"
                        )
                        self._log_debug(f"Converted temp image path to absolute: {img_path} -> {abs_img_path}")
                    else:
                        self._log_warning(f"Temp image not found: {abs_img_path}")
                continue
                
            # Resolve relative path from markdown file location
            if not os.path.isabs(img_path):
                full_img_path = md_dir / img_path
            else:
                full_img_path = Path(img_path)
            
            if full_img_path.exists():
                # Copy image to temp directory
                temp_img_name = f"embedded_{full_img_path.stem}_{full_img_path.suffix}"
                temp_img_path = self.temp_dir / temp_img_name
                
                try:
                    shutil.copy2(full_img_path, temp_img_path)
                    self._log_debug(f"Embedded image: {img_path} -> {temp_img_name}")
                    
                    # Update the reference in content
                    old_ref = f"![{alt_text}]({img_path})"
                    new_ref = f"![{alt_text}]({temp_img_path})"
                    processed_content = processed_content.replace(old_ref, new_ref)
                    
                except Exception as e:
                    self._log_warning(f"Failed to embed image {img_path}: {e}")
            else:
                self._log_warning(f"Image not found: {full_img_path}")
        
        # Process HTML img tags
        for match in re.finditer(html_img_pattern, content):
            img_path = match.group(1)
            
            # Skip if it's already a temp file or absolute URL
            if img_path.startswith('http') or img_path.startswith('data:'):
                continue
            
            # Check if this is a diagram generated by our script (Mermaid or PlantUML)
            if img_path.startswith('temp/') or img_path.startswith('temp\\'):
                # Convert relative temp path to absolute path for pandoc
                if not os.path.isabs(img_path):
                    # Convert to absolute path
                    abs_img_path = self.temp_dir / img_path.replace('temp/', '').replace('temp\\', '')
                    if abs_img_path.exists():
                        # Replace the relative path with absolute path
                        processed_content = processed_content.replace(
                            f"]({img_path})",
                            f"]({abs_img_path})"
                        )
                        self._log_debug(f"Converted temp image path to absolute: {img_path} -> {abs_img_path}")
                    else:
                        self._log_warning(f"Temp image not found: {abs_img_path}")
                continue
                
            # Resolve relative path from markdown file location
            if not os.path.isabs(img_path):
                full_img_path = md_dir / img_path
            else:
                full_img_path = Path(img_path)
            
            if full_img_path.exists():
                # Copy image to temp directory
                temp_img_name = f"embedded_{full_img_path.stem}_{full_img_path.suffix}"
                temp_img_path = self.temp_dir / temp_img_name
                
                try:
                    shutil.copy2(full_img_path, temp_img_path)
                    self._log_debug(f"Embedded HTML image: {img_path} -> {temp_img_name}")
                    
                    # Update the reference in content
                    old_ref = match.group(0)
                    new_ref = old_ref.replace(img_path, str(temp_img_path))
                    processed_content = processed_content.replace(old_ref, new_ref)
                    
                except Exception as e:
                    self._log_warning(f"Failed to embed HTML image {img_path}: {e}")
            else:
                self._log_warning(f"HTML image not found: {full_img_path}")
        
        return processed_content
    
    def _extract_title(self, md_file: Path, content: str) -> str:
        """Extract the document title from markdown content."""
        import re

        # 1) ATX H1: lines that start with '# ' but not '## '
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith('# '):
                heading_text = stripped[2:].strip()
                if heading_text:
                    return heading_text

        # 2) Setext H1: a line followed by a line of '=' (at least 3)
        lines = content.splitlines()
        for i in range(len(lines) - 1):
            current_line = lines[i].rstrip()
            underline = lines[i + 1].strip()
            if current_line and re.fullmatch(r"=\s*=+", underline) or re.fullmatch(r"=+", underline):
                return current_line.strip()

        # 3) Fallback to humanized filename stem
        stem = md_file.stem.replace('_', ' ').replace('-', ' ').strip()
        return stem.title() if stem else md_file.stem
    
    def _create_html_template(self, content: str, margins: Dict[str, str], title: str) -> str:
        """Create HTML template with proper styling, margins, and document title."""
        
        # Get style profile configuration
        profile = self.STYLE_PROFILES[self.style_profile]
        font_scale = profile["font_scale"]
        base_font_size = profile["base_font_size"]
        
        # Convert margins to cm for CSS
        top_cm = self._convert_margin_to_cm(margins['top'])
        right_cm = self._convert_margin_to_cm(margins['right'])
        bottom_cm = self._convert_margin_to_cm(margins['bottom'])
        left_cm = self._convert_margin_to_cm(margins['left'])
        
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        @page {{
            margin: {top_cm}cm {right_cm}cm {bottom_cm}cm {left_cm}cm;
            size: A4 portrait;
            width: 210mm;
            height: 297mm;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.4;
            color: #333;
            max-width: none;
            margin: 0;
            padding: 0;
            font-size: {base_font_size};
            width: 100%;
            box-sizing: border-box;
        }}
        
        /* Ensure content fits within A4 page boundaries */
        * {{
            box-sizing: border-box;
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            color: #2c3e50;
            margin-top: 0.8em;
            margin-bottom: 0.3em;
            font-weight: 600;
        }}
        
        h1 {{
            font-size: {1.6 * font_scale:.1f}em;
            border-bottom: 2px solid #3498db;
            padding-bottom: 0.2em;
        }}
        
        h2 {{
            font-size: {1.3 * font_scale:.1f}em;
            border-bottom: 1px solid #bdc3c7;
            padding-bottom: 0.1em;
        }}
        
        h3 {{
            font-size: {1.1 * font_scale:.1f}em;
        }}
        
        h4 {{
            font-size: {1.0 * font_scale:.1f}em;
            text-decoration: underline;
        }}
        
        h5 {{
            font-size: {0.9 * font_scale:.1f}em;
            text-decoration: underline;
        }}
        
        h6 {{
            font-size: {0.8 * font_scale:.1f}em;
            text-decoration: underline;
        }}
        
        p {{
            margin: 0.5em 0;
            text-align: justify;
        }}
        
        code {{
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 3px;
            padding: 0.1em 0.3em;
            font-family: 'Courier New', Consolas, monospace;
            font-size: {0.8 * font_scale:.1f}em;
            color: #e83e8c;
        }}
        
        pre {{
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 5px;
            padding: 0.5em;
            overflow-x: auto;
            margin: 0.5em 0;
            font-size: {0.8 * font_scale:.1f}em;
        }}
        
        pre code {{
            background: none;
            border: none;
            padding: 0;
            color: #333;
        }}
        
        blockquote {{
            border-left: 4px solid #3498db;
            margin: 0.5em 0;
            padding: 0.3em 0.8em;
            background-color: #f8f9fa;
            color: #555;
        }}
        
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 0.5em 0;
            font-size: {base_font_size} !important;
            font-family: inherit !important;
        }}
        
        th, td {{
            border: 1px solid #ddd;
            padding: 0.3em;
            text-align: left;
            font-size: {base_font_size} !important;
            font-family: inherit !important;
        }}
        
        th {{
            background-color: #f8f9fa;
            font-weight: 600;
            font-size: {base_font_size} !important;
            font-family: inherit !important;
        }}
        
        ul, ol {{
            margin: 0.5em 0;
            padding-left: 1.5em;
            display: block;
        }}
        
        li {{
            margin: 0.2em 0;
            display: list-item;
            list-style-type: disc;
        }}
        
        ul li {{
            list-style-type: disc;
        }}
        
        ol li {{
            list-style-type: decimal;
        }}
        
        /* Ensure nested lists work properly */
        ul ul, ol ol, ul ol, ol ul {{
            margin: 0.2em 0;
            padding-left: 1.2em;
        }}
        
        ul ul li {{
            list-style-type: circle;
        }}
        
        ul ul ul li {{
            list-style-type: square;
        }}
        
        img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 0.5em auto;
        }}
        
        /* Specific styling for Mermaid diagram images */
        img[alt*=""] {{
            margin: 0.3em auto;
            padding: 0;
            border: none;
            background: transparent;
        }}
        
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        
        a:hover {{
            text-decoration: underline;
        }}
        
        .page-break {{
            page-break-before: always;
        }}
        
        /* Better page break handling for A4 */
        h1, h2, h3 {{
            page-break-after: avoid;
            break-after: avoid;
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            page-break-inside: avoid;
            break-inside: avoid;
        }}
        
        p, li {{
            orphans: 3;
            widows: 3;
        }}
        
        /* Prevent large elements from breaking across pages */
        pre, blockquote, table, img {{
            page-break-inside: avoid;
            break-inside: avoid;
        }}
        
        /* Ensure tables fit within page width */
        table {{
            max-width: 100%;
            table-layout: auto;
        }}
        
        /* Force table font inheritance and override any defaults */
        table, table *, table th, table td, table tr {{
            font-size: {base_font_size} !important;
            font-family: inherit !important;
            line-height: inherit !important;
        }}
        
        /* Additional specificity for markdown-generated tables */
        body table, body table th, body table td {{
            font-size: {base_font_size} !important;
            font-family: inherit !important;
        }}
    </style>
</head>
<body>
    {content}
</body>
</html>
        """
        
        return html_template
    
    async def _convert_html_to_pdf(self, html_file: Path, output_pdf: Path, margins: Dict[str, str]) -> bool:
        """Convert HTML to PDF using Playwright (Puppeteer approach)."""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                # Load HTML file
                await page.goto(html_file.absolute().as_uri())
                
                # Wait for content to load
                await page.wait_for_load_state('networkidle')
                
                # Convert margins to cm for PDF generation
                top_cm = self._convert_margin_to_cm(margins['top'])
                right_cm = self._convert_margin_to_cm(margins['right'])
                bottom_cm = self._convert_margin_to_cm(margins['bottom'])
                left_cm = self._convert_margin_to_cm(margins['left'])
                
                # Generate PDF with precise A4 settings
                await page.pdf(
                    path=str(output_pdf),
                    format='A4',
                    width='210mm',
                    height='297mm',
                    margin={
                        'top': f'{top_cm}cm',
                        'right': f'{right_cm}cm',
                        'bottom': f'{bottom_cm}cm',
                        'left': f'{left_cm}cm'
                    },
                    print_background=True,
                    prefer_css_page_size=True,
                    display_header_footer=False,
                    scale=1.0
                )
                
                await browser.close()
                return True
                
        except Exception as e:
            self._log_error(f"Failed to convert HTML to PDF: {e}")
            return False
    
    def _convert_to_epub(self, md_file: Path, output_epub: Path, title: str) -> bool:
        """Convert markdown to EPUB format using Pandoc."""
        try:
            # Create temporary markdown file
            temp_md = self.temp_dir / f"temp_{md_file.name}"
            
            # Read and process markdown content
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Process content (same as PDF processing)
            processed_content = self._filter_sections_for_print(content)
            file_id = md_file.stem
            processed_content = self._replace_mermaid_with_images(processed_content, file_id)
            processed_content = self._replace_plantuml_with_images(processed_content, file_id)
            processed_content = self._process_page_breaks(processed_content)
            processed_content = self._process_and_embed_images(processed_content, md_file)
            
            # Write processed content to temp file
            with open(temp_md, 'w', encoding='utf-8') as f:
                f.write(processed_content)
            
            # Create device-specific CSS if needed
            css_file = None
            if self.style_profile == "kindle-paperwhite-11":
                css_file = self._create_paperwhite_css()
            
            # Convert to EPUB using Pandoc
            cmd = [
                "pandoc",
                str(temp_md),
                "-o", str(output_epub),
                "--standalone",
                "--self-contained",
                f"--metadata=title:{title}",
                f"--metadata=author:{self.author}",
                f"--metadata=language:{self.language}",
                "--toc",
                "--toc-depth=3"
            ]
            
            # Add CSS file if created
            if css_file:
                cmd.extend(["--css", str(css_file)])
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                self._log_error(f"Pandoc EPUB conversion failed: {result.stderr}")
                return False
            
            return True
            
        except Exception as e:
            self._log_error(f"Failed to convert to EPUB: {e}")
            return False
    
    def _create_paperwhite_css(self) -> Path:
        """Create device-specific CSS for Kindle Paperwhite 11th generation."""
        css_content = """
/* Kindle Paperwhite 11th Generation Optimized CSS */
/* 6.8" E Ink Carta screen, 1648 x 1236 pixels, 300 ppi */

/* Base styles optimized for 300ppi display */
body {
    font-family: "Bookerly", "Caecilia", "Helvetica", "Arial", sans-serif;
    font-size: 13px;
    line-height: 1.6;
    color: #000000;
    margin: 0;
    padding: 0.8em;
    text-align: justify;
    hyphens: auto;
    -webkit-hyphens: auto;
    -moz-hyphens: auto;
    -ms-hyphens: auto;
}

/* Media query for Kindle Paperwhite 11th generation */
@media only screen and (min-width: 1648px) and (max-width: 1648px) and (min-height: 1236px) and (max-height: 1236px) {
    body {
        font-size: 14px;
        line-height: 1.7;
        padding: 1em;
    }
    
    h1 {
        font-size: 1.8em;
        margin-top: 1.2em;
        margin-bottom: 0.6em;
        page-break-after: avoid;
    }
    
    h2 {
        font-size: 1.5em;
        margin-top: 1em;
        margin-bottom: 0.5em;
        page-break-after: avoid;
    }
    
    h3 {
        font-size: 1.3em;
        margin-top: 0.8em;
        margin-bottom: 0.4em;
        page-break-after: avoid;
    }
    
    h4 {
        font-size: 1.2em;
        margin-top: 0.7em;
        margin-bottom: 0.3em;
        page-break-after: avoid;
    }
    
    h5 {
        font-size: 1.1em;
        margin-top: 0.6em;
        margin-bottom: 0.3em;
        page-break-after: avoid;
    }
    
    h6 {
        font-size: 1.05em;
        margin-top: 0.5em;
        margin-bottom: 0.3em;
        page-break-after: avoid;
    }
    
    p {
        margin: 0.6em 0;
        text-indent: 0;
    }
    
    /* Code blocks optimized for e-ink */
    pre {
        background-color: #f5f5f5;
        border: 1px solid #ddd;
        border-radius: 3px;
        padding: 0.8em;
        margin: 1em 0;
        font-size: 11px;
        line-height: 1.4;
        overflow-x: auto;
        page-break-inside: avoid;
    }
    
    code {
        background-color: #f5f5f5;
        border: 1px solid #ddd;
        border-radius: 2px;
        padding: 0.2em 0.4em;
        font-size: 11px;
        font-family: "Courier New", "Monaco", monospace;
    }
    
    /* Tables optimized for 6.8" screen */
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 1em 0;
        font-size: 12px;
        page-break-inside: avoid;
    }
    
    th, td {
        border: 1px solid #ddd;
        padding: 0.4em 0.6em;
        text-align: left;
        vertical-align: top;
    }
    
    th {
        background-color: #f8f8f8;
        font-weight: bold;
    }
    
    /* Images optimized for 300ppi */
    img {
        max-width: 100%;
        height: auto;
        display: block;
        margin: 1em auto;
        page-break-inside: avoid;
    }
    
    /* Lists with better spacing */
    ul, ol {
        margin: 0.8em 0;
        padding-left: 1.5em;
    }
    
    li {
        margin: 0.3em 0;
        line-height: 1.5;
    }
    
    /* Blockquotes */
    blockquote {
        border-left: 3px solid #ccc;
        margin: 1em 0;
        padding: 0.5em 1em;
        background-color: #f9f9f9;
        font-style: italic;
    }
    
    /* Links */
    a {
        color: #0066cc;
        text-decoration: none;
    }
    
    a:visited {
        color: #663399;
    }
    
    /* Page breaks */
    .page-break {
        page-break-before: always;
    }
    
    /* Avoid widows and orphans */
    p, li {
        orphans: 2;
        widows: 2;
    }
    
    /* Chapter breaks */
    h1, h2 {
        page-break-before: auto;
    }
    
    /* Ensure headings don't break across pages */
    h1, h2, h3, h4, h5, h6 {
        page-break-after: avoid;
        page-break-inside: avoid;
    }
}

/* Fallback styles for other devices */
h1, h2, h3, h4, h5, h6 {
    color: #000000;
    font-weight: bold;
    page-break-after: avoid;
}

h1 { font-size: 1.6em; margin: 1em 0 0.5em 0; }
h2 { font-size: 1.4em; margin: 0.8em 0 0.4em 0; }
h3 { font-size: 1.2em; margin: 0.7em 0 0.3em 0; }
h4 { font-size: 1.1em; margin: 0.6em 0 0.3em 0; text-decoration: underline; }
h5 { font-size: 1.05em; margin: 0.5em 0 0.3em 0; text-decoration: underline; }
h6 { font-size: 1em; margin: 0.5em 0 0.3em 0; text-decoration: underline; }

p { margin: 0.5em 0; }
pre { background-color: #f5f5f5; padding: 0.5em; margin: 0.5em 0; }
code { background-color: #f5f5f5; padding: 0.1em 0.3em; }
table { border-collapse: collapse; width: 100%; margin: 0.5em 0; }
th, td { border: 1px solid #ddd; padding: 0.3em; }
th { background-color: #f8f8f8; }
img { max-width: 100%; height: auto; display: block; margin: 0.5em auto; }
ul, ol { margin: 0.5em 0; padding-left: 1.5em; }
li { margin: 0.2em 0; }
blockquote { border-left: 3px solid #ccc; margin: 0.5em 0; padding: 0.3em 0.8em; background-color: #f9f9f9; }
a { color: #0066cc; text-decoration: none; }
"""
        
        css_file = self.temp_dir / "kindle_paperwhite_11.css"
        with open(css_file, 'w', encoding='utf-8') as f:
            f.write(css_content)
        
        self._log_debug(f"Created Paperwhite 11th gen CSS: {css_file}")
        return css_file
    
    def _convert_epub_to_mobi(self, epub_file: Path, output_mobi: Path) -> bool:
        """Convert EPUB to MOBI using Calibre."""
        try:
            cmd = [
                "ebook-convert",
                str(epub_file),
                str(output_mobi),
                "--mobi-file-type", "both",  # Create both old and new MOBI formats
                "--personal-doc",  # Mark as personal document
                "--no-inline-toc"  # Don't create inline table of contents
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                self._log_error(f"Calibre MOBI conversion failed: {result.stderr}")
                return False
            
            return True
            
        except Exception as e:
            self._log_error(f"Failed to convert EPUB to MOBI: {e}")
            return False
    
    def _convert_single_file(self, md_file: Path) -> tuple[bool, str]:
        """Convert a single markdown file to the specified format."""
        try:
            filename = md_file.name
            output_file = self.format_output_dir / f"{md_file.stem}.{self.output_format}"
            
            # Check if conversion is needed
            current_markdown_hash = calculate_file_hash(md_file)
            
            if not self.state_manager.needs_regeneration(
                filename, current_markdown_hash, output_file, self.style_profile,
                self.diagram_width, self.diagram_height, None, False
            ):
                self._log_info(f"Skipping {filename} - {self.output_format.upper()} is up to date")
                return True, filename
            
            if self._convert_md_to_format(md_file, output_file):
                return True, filename
            else:
                return False, filename
                
        except Exception as e:
            self._log_error(f"Error processing {md_file.name}: {e}")
            return False, md_file.name
    
    def _convert_md_to_format(self, md_file: Path, output_file: Path) -> bool:
        """Convert markdown file to the specified format."""
        try:
            current_markdown_hash = calculate_file_hash(md_file)
            filename = md_file.name
            
            self._log_info(f"Converting {filename} to {self.output_format.upper()} - markdown has changed or file missing")
            
            # Read markdown content
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract title
            doc_title = self._extract_title(md_file, content)
            
            if self.output_format == "pdf":
                return self._convert_to_pdf(md_file, output_file, doc_title)
            elif self.output_format == "epub":
                return self._convert_to_epub(md_file, output_file, doc_title)
            elif self.output_format == "mobi":
                return self._convert_to_mobi(md_file, output_file, doc_title)
            else:
                self._log_error(f"Unsupported output format: {self.output_format}")
                return False
                
        except Exception as e:
            self._log_error(f"Error converting {md_file.name}: {e}")
            return False
    
    def _convert_to_pdf(self, md_file: Path, output_pdf: Path, title: str) -> bool:
        """Convert markdown to PDF (reuse existing logic)."""
        try:
            # Read markdown content
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Process content
            processed_content = self._filter_sections_for_print(content)
            file_id = md_file.stem
            processed_content = self._replace_mermaid_with_images(processed_content, file_id)
            processed_content = self._replace_plantuml_with_images(processed_content, file_id)
            processed_content = self._process_page_breaks(processed_content)
            processed_content = self._process_and_embed_images(processed_content, md_file)
            
            # Convert markdown to HTML using pandoc
            temp_md = self.temp_dir / f"temp_{md_file.name}"
            with open(temp_md, 'w', encoding='utf-8') as f:
                f.write(processed_content)
            
            html_file = self.temp_dir / f"{md_file.stem}.html"
            cmd = [
                "pandoc",
                str(temp_md),
                "-o", str(html_file),
                "--standalone",
                "--self-contained",
                "--css", "data:text/css,",  # Empty CSS, we'll add our own
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                self._log_error(f"Pandoc failed: {result.stderr}")
                return False
            
            # Read the generated HTML
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Parse margins
            margins = self._parse_margins()
            
            # Create enhanced HTML template
            enhanced_html = self._create_html_template(html_content, margins, title)
            
            # Write enhanced HTML
            enhanced_html_file = self.temp_dir / f"enhanced_{md_file.stem}.html"
            with open(enhanced_html_file, 'w', encoding='utf-8') as f:
                f.write(enhanced_html)
            
            # Convert HTML to PDF using Playwright
            self._log_debug(f"Converting HTML to PDF with margins: {margins}")
            
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                success = loop.run_until_complete(
                    self._convert_html_to_pdf(enhanced_html_file, output_pdf, margins)
                )
                if success:
                    # Calculate PDF hash and save document state
                    pdf_hash = calculate_file_hash(output_pdf)
                    self.state_manager.save_document_state(
                        filename, current_markdown_hash, pdf_hash, self.style_profile,
                        self.diagram_width, self.diagram_height, None, False
                    )
                    self._log_success(f"Converted {md_file.name} to {output_pdf.name}")
                    return True
                else:
                    self._log_error(f"Failed to convert {md_file.name}")
                    return False
            finally:
                loop.close()
                
        except Exception as e:
            self._log_error(f"Error converting {md_file.name} to PDF: {e}")
            return False
    
    def _convert_to_mobi(self, md_file: Path, output_mobi: Path, title: str) -> bool:
        """Convert markdown to MOBI format."""
        try:
            # First convert to EPUB
            epub_file = self.temp_dir / f"{md_file.stem}.epub"
            
            if not self._convert_to_epub(md_file, epub_file, title):
                return False
            
            # Then convert EPUB to MOBI
            if not self._convert_epub_to_mobi(epub_file, output_mobi):
                return False
            
            # Save document state
            current_markdown_hash = calculate_file_hash(md_file)
            mobi_hash = calculate_file_hash(output_mobi)
            self.state_manager.save_document_state(
                md_file.name, current_markdown_hash, mobi_hash, self.style_profile,
                self.diagram_width, self.diagram_height, None, False
            )
            
            self._log_success(f"Converted {md_file.name} to {output_mobi.name}")
            return True
            
        except Exception as e:
            self._log_error(f"Error converting {md_file.name} to MOBI: {e}")
            return False
    
    def convert_all(self, cleanup: bool = True, parallel: bool = True) -> None:
        """Convert all markdown files in source directory to the specified format."""
        md_files = list(self.source_dir.glob("*.md"))
        
        if not md_files:
            self._log_warning("No markdown files found in source directory.")
            return
        
        # Filter out README.md
        md_files = [f for f in md_files if f.name != "README.md"]
        
        self._log_info(f"Starting markdown to {self.output_format.upper()} conversion...")
        self._log_info(f"Source directory: {self.source_dir.absolute()}")
        self._log_info(f"Output directory: {self.format_dir.absolute()}")
        self._log_info(f"Found {len(md_files)} markdown files: {[f.name for f in md_files]}")
        
        if parallel and len(md_files) > 1:
            self._log_info(f"Using parallel processing with {self.max_workers} workers")
            self._convert_all_parallel(md_files, cleanup)
        else:
            self._log_info("Using sequential processing")
            self._convert_all_sequential(md_files, cleanup)
    
    def _convert_all_parallel(self, md_files: List[Path], cleanup: bool) -> None:
        """Convert files in parallel using ThreadPoolExecutor."""
        success_count = 0
        skipped_count = 0
        failed_count = 0
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_file = {executor.submit(self._convert_single_file, md_file): md_file for md_file in md_files}
            
            # Process completed tasks
            for future in as_completed(future_to_file):
                md_file = future_to_file[future]
                try:
                    success, filename = future.result()
                    if success:
                        # Check if it was actually converted or just skipped
                        current_markdown_hash = calculate_file_hash(md_file)
                        output_file = self.format_output_dir / f"{md_file.stem}.{self.output_format}"
                        
                        if not self.state_manager.needs_regeneration(filename, current_markdown_hash, output_file, self.style_profile,
                                                                     self.diagram_width, self.diagram_height, None, False):
                            skipped_count += 1
                        else:
                            success_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    self._log_error(f"Exception in parallel processing for {md_file.name}: {e}")
                    failed_count += 1
        
        total_processed = success_count + skipped_count + failed_count
        self._log_success(f"Parallel conversion complete: {success_count} files converted, {skipped_count} files skipped, {failed_count} files failed ({total_processed}/{len(md_files)} total)")
        self._log_info(f"{self.output_format.upper()} files saved to: {self.format_output_dir.absolute()}")
        
        if cleanup:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            self._log_debug(f"Cleaned up temporary directory: {self.temp_dir}")
    
    def _convert_all_sequential(self, md_files: List[Path], cleanup: bool) -> None:
        """Convert files sequentially."""
        success_count = 0
        skipped_count = 0
        
        for md_file in md_files:
            success, filename = self._convert_single_file(md_file)
            if success:
                # Check if it was actually converted or just skipped
                current_markdown_hash = calculate_file_hash(md_file)
                output_file = self.format_output_dir / f"{md_file.stem}.{self.output_format}"
                
                if not self.state_manager.needs_regeneration(
                    filename, current_markdown_hash, output_file, self.style_profile,
                    self.diagram_width, self.diagram_height, None, False
                ):
                    skipped_count += 1
                else:
                    success_count += 1
        
        total_processed = success_count + skipped_count
        self._log_success(f"Sequential conversion complete: {success_count} files converted, {skipped_count} files skipped ({total_processed}/{len(md_files)} total)")
        self._log_info(f"{self.output_format.upper()} files saved to: {self.format_output_dir.absolute()}")
        
        if cleanup:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            self._log_debug(f"Cleaned up temporary directory: {self.temp_dir}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert markdown files to PDF, EPUB, or MOBI format with Mermaid and PlantUML support")
    parser.add_argument("--source", default=None, help="Source directory (default: from config/env/docs)")
    parser.add_argument("--output-dir", default=None, help="Output directory (default: from config/env/output). Files will be saved in subfolders by format (e.g., output/pdf/, output/mobi/)")
    parser.add_argument("--temp-dir", default=None, help="Temporary files directory (default: from config/env/temp)")
    parser.add_argument("--db-path", default=None, help="Database path (default: from config/env/user config dir)")
    parser.add_argument("--format", default="pdf", choices=["pdf", "epub", "mobi"], help="Output format (default: pdf)")
    parser.add_argument("--margins", default="1in 0.75in", help="Page margins in CSS format (default: '1in 0.75in'). Only applies to PDF format.")
    parser.add_argument("--profile", default="a4-print", choices=["a4-print", "a4-screen", "kindle-basic", "kindle-large", "kindle-paperwhite-11"], help="Style profile for conversion (default: 'a4-print')")
    parser.add_argument("--author", default="Unknown Author", help="Author name for ebook metadata (default: 'Unknown Author')")
    parser.add_argument("--language", default="en", help="Language code for ebook metadata (default: 'en')")
    parser.add_argument("--no-cleanup", action="store_true", help="Keep temporary files")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging for detailed output")
    parser.add_argument("--cleanup-db", action="store_true", help="Clear all document state records from database and exit")
    parser.add_argument("--max-workers", type=int, default=4, help="Maximum number of parallel workers for conversion (default: 4)")
    parser.add_argument("--no-parallel", action="store_true", help="Disable parallel processing and use sequential conversion")
    parser.add_argument("--max-diagram-width", type=str, default=None, help="Maximum diagram width: pixels (e.g., 1680, only if rendered exceeds) or percentage of rendered size (e.g., 80%%, max 100%%). Default: 1680")
    parser.add_argument("--max-diagram-height", type=str, default=None, help="Maximum diagram height: pixels (e.g., 2240, only if rendered exceeds) or percentage of rendered size (e.g., 80%%, max 100%%). Default: 2240")
    
    args = parser.parse_args()
    
    # Build config from CLI args
    cli_config = {}
    if args.source:
        cli_config["source_dir"] = args.source
    if args.output_dir:
        cli_config["output_dir"] = args.output_dir
    if args.temp_dir:
        cli_config["temp_dir"] = args.temp_dir
    if args.db_path:
        cli_config["db_path"] = args.db_path
    if args.max_diagram_width:
        # Parse dimension value (can be int string or percentage)
        from .config import parse_dimension_value
        parsed = parse_dimension_value(args.max_diagram_width)
        if parsed is not None:
            cli_config["max_diagram_width"] = parsed
    if args.max_diagram_height:
        # Parse dimension value (can be int string or percentage)
        from .config import parse_dimension_value
        parsed = parse_dimension_value(args.max_diagram_height)
        if parsed is not None:
            cli_config["max_diagram_height"] = parsed
    
    config = Config(cli_config)
    
    # Handle database cleanup if requested
    if args.cleanup_db:
        try:
            state_manager = DocumentStateManager(config.get_db_path())
            count = state_manager.clear_all_documents()
            print(f"{Fore.GREEN}[OK]{Style.RESET_ALL} Cleared {count} document state records from database")
            return
        except Exception as e:
            print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Failed to cleanup database: {e}")
            sys.exit(1)
    
    # Check dependencies (include optional for MOBI)
    if not check_dependencies(check_optional=(args.format == "mobi")):
        sys.exit(1)
    
    # Run conversion
    converter = MarkdownToEbookConverter(
        config.get_source_dir(), 
        config.get_output_dir(), 
        config.get_temp_dir(), 
        args.format,
        args.margins, 
        args.debug, 
        db_path=config.get_db_path(),
        style_profile=args.profile,
        max_workers=args.max_workers,
        author=args.author,
        language=args.language,
        max_diagram_width=config.get_max_diagram_width(),
        max_diagram_height=config.get_max_diagram_height()
    )
    converter.convert_all(cleanup=not args.no_cleanup, parallel=not args.no_parallel)


if __name__ == "__main__":
    main()
