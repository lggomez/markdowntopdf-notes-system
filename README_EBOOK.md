# Markdown to Ebook Converter

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Convert markdown files to EPUB or MOBI formats with Mermaid and PlantUML diagram support.

## Features

- **Multi-Format Support**: Convert to EPUB or MOBI formats
- **Diagram Rendering**: Renders Mermaid and PlantUML diagrams as images with configurable dimensions
- **Style Profiles**: Kindle-optimized profiles for different devices
- **Smart Processing**: Skips unchanged files using SHA-256 verification
- **Parallel Processing**: Fast batch conversion with configurable workers
- **Metadata Support**: Author and language metadata for ebooks
- **Table of Contents**: Automatic TOC generation

## Supported Formats

- **EPUB**: Standard ebook format compatible with most readers
- **MOBI**: Amazon Kindle format optimized for e-ink displays

## Prerequisites

- **Python 3.8+**
- **Pandoc**: https://pandoc.org/installing.html
- **Calibre** (for MOBI): https://calibre-ebook.com/download

## Installation

```bash
poetry install
poetry run playwright install chromium
```

## Usage

### Basic Usage

```bash
# Convert to EPUB
poetry run md2ebook --format epub --source ./docs

# Convert to MOBI (requires Calibre)
poetry run md2ebook --format mobi --source ./docs
```

### Advanced Examples

```bash
# Kindle with large text and metadata
poetry run md2ebook --format mobi --profile kindle-large --author "Your Name" --language "en" --source ./docs

# Kindle Paperwhite 11th gen optimized
poetry run md2ebook --format mobi --profile kindle-paperwhite-11 --author "Your Name" --source ./docs

# EPUB with custom diagram sizing
poetry run md2ebook --format epub --max-diagram-width 80% --max-diagram-height 80% --source ./docs

# Debug mode with temp files preserved
poetry run md2ebook --format epub --debug --no-cleanup --source ./docs

# Clear cache and regenerate
poetry run md2ebook --cleanup-db && poetry run md2ebook --format mobi --source ./docs
```

## Style Profiles

- **`kindle-basic`**: Basic Kindle formatting for e-ink displays
- **`kindle-large`**: Large text for better readability
- **`kindle-paperwhite-11`**: Optimized for Kindle Paperwhite 11th gen (6.8" 300ppi, 1648x1236 resolution)

## Command Line Options

```
--source DIR              Source directory (default: docs)
--output-dir DIR          Output directory (default: output)
--format {epub,mobi}      Output format
--profile PROFILE         Style profile (default: kindle-basic)
--author "NAME"           Author metadata (default: "Unknown Author")
--language CODE           Language code (default: "en")
--max-diagram-width VAL   Max width: pixels or percentage (default: 1680)
--max-diagram-height VAL  Max height: pixels or percentage (default: 2240)
--max-workers NUM         Parallel workers (default: 4)
--no-parallel             Disable parallel processing
--debug                   Enable debug logging
--no-cleanup              Keep temporary files
--cleanup-db              Clear verification database
```

## How It Works

1. **Verification**: Calculates SHA-256 hash and checks against stored state (format, profile, hash)
2. **Smart Processing**: Skips unchanged files with matching format and profile
3. **Diagram Rendering**: Renders Mermaid (Playwright) and PlantUML diagrams to PNG
4. **Content Processing**: Replaces diagram blocks with image references, embeds images
5. **Conversion**: 
   - **EPUB**: Markdown → EPUB (via Pandoc)
   - **MOBI**: Markdown → EPUB → MOBI (via Pandoc + Calibre)
6. **State Update**: Saves hashes and metadata to SQLite database
7. **Cleanup**: Removes temporary files (unless `--no-cleanup` specified)

## Output Structure

```
output/
├── epub/  # EPUB files
└── mobi/  # MOBI files
```

## Troubleshooting

**Debug Mode:**
```bash
poetry run md2ebook --format mobi --debug --no-cleanup --source ./docs
```

**Common Issues:**
1. **Pandoc not found**: Install from https://pandoc.org/installing.html
2. **Calibre not found** (MOBI only): Install from https://calibre-ebook.com/download
3. **Diagrams not rendering**: Run `poetry run playwright install chromium`
4. **Cache issues**: Clear database with `poetry run md2ebook --cleanup-db`

## Additional Features

- **Parallel Processing**: Uses multiple workers (default: 4)
- **Smart Caching**: Skips unchanged files automatically
- **Diagram Resizing**: Supports pixel or percentage-based sizing
- **Ebook Metadata**: Author, language, TOC generation

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2025 Markdown to PDF Converter
