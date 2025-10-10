# Markdown to PDF Converter

A Python script that converts all markdown files in the current directory to PDF format, with support for rendering Mermaid and PlantUML diagrams as images.

python convert_md_to_pdf.py --margins "20mm 25mm"

## Features

- Page breaks via <div class="page-break"></div>
- Converts all `.md` files in the current directory to PDF
- Renders Mermaid diagrams as images and embeds them in the PDF
- Renders PlantUML diagrams as images and embeds them in the PDF
- Supports custom page breaks for better document structure
- Uses your existing `mermaid-config.json` for consistent Mermaid diagram styling
- **Style Profiles**: Choose between print-optimized and screen-optimized styling
- Saves PDFs in a `pdf/` subdirectory
- Uses `temp/` subdirectory for intermediate files (with cleanup option)
- No LaTeX dependencies - uses Playwright (Chromium) for clean HTML-to-PDF conversion

## Prerequisites

### External Dependencies
You need to install these tools separately:

1. **Pandoc** - Document converter
   - Windows: Download from https://pandoc.org/installing.html
   - macOS: `brew install pandoc`
   - Linux: `sudo apt-get install pandoc` or `sudo yum install pandoc`

### Python Dependencies
The script uses Playwright for Mermaid diagram rendering and the plantuml library for PlantUML diagram rendering.

## Installation

1. **Run the setup script** (recommended):
   ```bash
   python setup.py
   ```

2. **Or install manually**:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

## Usage

### Basic Usage
```bash
python convert_md_to_pdf.py
```

This will:
- Find all `.md` files in the current directory
- Convert them to PDF with rendered Mermaid and PlantUML diagrams
- Save PDFs in the `pdf/` folder
- Clean up temporary files

### Advanced Usage
```bash
# Specify custom directories
python convert_md_to_pdf.py --source ./docs --pdf-dir ./output --temp-dir ./working

# Use screen-optimized style profile (30% larger fonts)
python convert_md_to_pdf.py --profile a4-screen

# Use print-optimized style profile (default)
python convert_md_to_pdf.py --profile a4-print

# Keep temporary files for debugging
python convert_md_to_pdf.py --no-cleanup

# Enable debug logging for detailed output
python convert_md_to_pdf.py --debug

# Clear document verification database (forces regeneration of all PDFs)
python convert_md_to_pdf.py --cleanup-db

# Combine options
python convert_md_to_pdf.py --debug --no-cleanup --margins "20mm 25mm" --profile a4-screen

# Get help
python convert_md_to_pdf.py --help
```

## How It Works

1. **Verification Check**: For each markdown file, calculates SHA-256 hash and checks against stored state
2. **Style Profile Check**: Compares current style profile with the one used for the last generation
3. **Smart Processing**: Only processes files that have changed, are missing, or have a different style profile
4. **Diagram Processing**: The script finds all `\`\`\`mermaid` and `\`\`\`plantuml` code blocks in your markdown files
5. **Diagram Rendering**: 
   - Mermaid diagrams are rendered to PNG images using Playwright
   - PlantUML diagrams are rendered to PNG images using the plantuml library
6. **Content Replacement**: Diagram code blocks are replaced with image references
7. **PDF Generation**: The processed markdown is converted to PDF using Pandoc + Playwright (Chromium) with the selected style profile
8. **State Update**: Saves markdown hash, PDF hash, and style profile to SQLite database for future verification
9. **Cleanup**: Temporary files are removed (unless `--no-cleanup` is specified)

## Verification System

The converter includes a verification system that avoids unnecessary file recreations:
- **SHA-256 Hashing**: Each markdown file is hashed to detect changes
- **Style Profile Tracking**: Database tracks which style profile was used for each document
- **SQLite Database**: Document state is stored in `state/document_state.db` 
- **Smart Skipping**: Unchanged files with same style profile are skipped entirely (no processing, no diagram rendering)
- **Automatic Updates**: State is updated after successful PDF generation
- **Profile Change Detection**: Switching style profiles triggers regeneration of affected documents

### Database Management

```bash
# Clear all verification state (forces regeneration of all PDFs)
python convert_md_to_pdf.py --cleanup-db

# Normal run (uses verification to skip unchanged files)
python convert_md_to_pdf.py
```

## Style Profiles

The converter supports different style profiles optimized for different use cases:

### Available Profiles

- **`a4-print`** (default): Standard print-optimized styling
  - Base font size: 12px
  - Optimized for physical printing
  - Standard margins and spacing

- **`a4-screen`**: Screen-optimized styling with larger fonts
  - Base font size: 15.6px (30% larger)
  - Optimized for screen reading
  - Better readability on digital displays

### Usage Examples

```bash
# Use default print profile
python convert_md_to_pdf.py

# Use screen-optimized profile
python convert_md_to_pdf.py --profile a4-screen

# Switch back to print profile (triggers regeneration)
python convert_md_to_pdf.py --profile a4-print
```

### Smart Regeneration

The system tracks which style profile was used for each document. When you switch profiles:
- Documents are automatically regenerated with the new styling
- Same profile runs skip unchanged files for efficiency
- Database tracks both content changes and style profile changes

## Configuration

The script automatically uses your `mermaid-config.json` file if present, ensuring consistent Mermaid diagram styling across all generated PDFs. PlantUML diagrams use default styling.

## Page Breaks

You can control page breaks in your PDF output using any of these methods:

### Supported Page Break Syntax

**Option 1: HTML Comment (Recommended)**
```markdown
<!-- page-break -->
```

**Option 2: HTML Div**
```markdown
<div class="page-break"></div>
```

**Option 3: Custom Tag**
```markdown
<page-break>
```

### Common Issues

1. **"pandoc not found"**
   - Install Pandoc from https://pandoc.org/installing.html
   - Make sure it's in your PATH

2. **"wkhtmltopdf not found"**
   - Install wkhtmltopdf from https://wkhtmltopdf.org/downloads.html
   - Make sure it's in your PATH

3. **"Playwright browser not found"**
   - Run: `playwright install chromium`

4. **Mermaid diagrams not rendering**
   - Check your Mermaid syntax
   - Ensure you have internet connection (for Mermaid CDN)
   - Check the temp directory for error messages

5. **PlantUML diagrams not rendering**
   - Check your PlantUML syntax
   - Ensure the plantuml library is installed: `pip install plantuml`
   - Check the temp directory for error messages

6. **Style profile not working as expected**
   - Verify the profile name is correct: `a4-print` or `a4-screen`
   - Check that the database was updated: `python convert_md_to_pdf.py --cleanup-db` to reset
   - Use `--debug` to see which profile is being used

### Debug Mode
Use `--debug` to enable detailed logging and `--no-cleanup` to keep temporary files for inspection:
```bash
# Enable debug logging to see detailed processing information
python convert_md_to_pdf.py --debug

# Keep temporary files for inspection
python convert_md_to_pdf.py --no-cleanup

# Combine both for full debugging
python convert_md_to_pdf.py --debug --no-cleanup
```
## Examples

### Minimal Example
Convert `docs/example.md` to PDF:

```bash
python convert_md_to_pdf.py --source ./docs
```

## License

This script is provided as-is
