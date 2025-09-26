# File Optimization Tool - External Dependencies Setup

The File Optimization Tool in DevBoost provides comprehensive optimization capabilities for images, videos, and PDFs. While the tool includes built-in optimization engines, installing external tools can significantly enhance performance and provide additional optimization options.

## Overview

The File Optimization Tool supports multiple optimization engines:

- **Image Optimization**: PIL/Pillow (built-in), pngquant, jpegoptim, gifsicle, libvips
- **Video Optimization**: ffmpeg (required), gifski
- **PDF Optimization**: ghostscript (required)

## Installation Instructions

### macOS

#### Using Homebrew (Recommended)

```bash
# Install all optimization tools at once
brew install ffmpeg ghostscript pngquant jpegoptim gifsicle vips gifski

# Or install individually:
brew install ffmpeg          # Video optimization (required)
brew install ghostscript     # PDF optimization (required)
brew install pngquant        # PNG compression
brew install jpegoptim       # JPEG optimization
brew install gifsicle        # GIF optimization
brew install vips            # Advanced image processing
brew install gifski          # High-quality GIF creation
```

#### Using MacPorts

```bash
sudo port install ffmpeg +universal
sudo port install ghostscript
sudo port install pngquant
sudo port install jpegoptim
sudo port install gifsicle
sudo port install vips
```

### Linux (Ubuntu/Debian)

```bash
# Update package list
sudo apt update

# Install all tools
sudo apt install ffmpeg ghostscript pngquant jpegoptim gifsicle libvips-tools

# For gifski (may need to install from source or snap)
sudo snap install gifski
```

### Linux (CentOS/RHEL/Fedora)

```bash
# For Fedora
sudo dnf install ffmpeg ghostscript pngquant jpegoptim gifsicle vips-tools

# For CentOS/RHEL (enable EPEL repository first)
sudo yum install epel-release
sudo yum install ffmpeg ghostscript pngquant jpegoptim gifsicle vips-tools
```

### Windows

#### Using Chocolatey (Recommended)

```powershell
# Install Chocolatey if not already installed
# Then install tools:
choco install ffmpeg
choco install ghostscript
choco install pngquant
choco install jpegoptim
choco install gifsicle
```

#### Manual Installation

1. **FFmpeg**: Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
2. **Ghostscript**: Download from [https://www.ghostscript.com/download/gsdnld.html](https://www.ghostscript.com/download/gsdnld.html)
3. **Other tools**: Download binaries and add to PATH

## Tool Descriptions and Benefits

### Required Tools

#### FFmpeg (Video Optimization)

- **Purpose**: Video compression, format conversion, and optimization
- **Benefits**:
  - Supports virtually all video formats
  - Advanced compression algorithms
  - Batch processing capabilities
  - Quality control and bitrate management
- **Formats**: MP4, WebM, AVI, MOV, GIF, and more

#### Ghostscript (PDF Optimization)

- **Purpose**: PDF compression and optimization
- **Benefits**:
  - Reduces PDF file sizes significantly
  - Maintains document quality
  - Supports various compression levels
  - Handles complex PDF structures

### Optional Enhancement Tools

#### pngquant (PNG Optimization)

- **Purpose**: PNG image compression with quality preservation
- **Benefits**:
  - Up to 70% size reduction
  - Maintains visual quality
  - Faster than built-in methods
  - Supports transparency

#### jpegoptim (JPEG Optimization)

- **Purpose**: JPEG compression and optimization
- **Benefits**:
  - Lossless and lossy compression options
  - Removes unnecessary metadata
  - Progressive JPEG support
  - Better compression ratios

#### gifsicle (GIF Optimization)

- **Purpose**: GIF animation and static image optimization
- **Benefits**:
  - Reduces GIF file sizes
  - Optimizes color palettes
  - Removes redundant frames
  - Maintains animation quality

#### libvips (Advanced Image Processing)

- **Purpose**: High-performance image processing
- **Benefits**:
  - Faster processing for large images
  - Memory efficient
  - Supports many formats
  - Advanced resizing algorithms

#### gifski (High-Quality GIF Creation)

- **Purpose**: Convert videos to high-quality GIFs
- **Benefits**:
  - Superior quality compared to ffmpeg
  - Better color handling
  - Optimized file sizes
  - Smooth animations

## Verification

After installation, you can verify that tools are properly installed by running:

```bash
# Check if tools are available
ffmpeg -version
gs -version
pngquant --version
jpegoptim --version
gifsicle --version
vips --version
gifski --version
```

## Tool Detection in DevBoost

The File Optimization Tool automatically detects which external tools are available on your system. You can check the detection status in the application:

1. Open DevBoost
2. Navigate to "File Optimization Tool"
3. The tool will display which optimization engines are available
4. Missing tools will show fallback options

## Performance Comparison

| Tool Type | Built-in Engine | External Tool | Performance Gain              |
| --------- | --------------- | ------------- | ----------------------------- |
| PNG       | PIL/Pillow      | pngquant      | 2-3x better compression       |
| JPEG      | PIL/Pillow      | jpegoptim     | 1.5-2x better compression     |
| GIF       | PIL/Pillow      | gifsicle      | 3-4x better compression       |
| Video     | N/A             | ffmpeg        | Required for video processing |
| PDF       | N/A             | ghostscript   | Required for PDF processing   |

## Troubleshooting

### Common Issues

#### Tool Not Detected

- Ensure the tool is installed and available in PATH
- Restart DevBoost after installation
- Check tool version compatibility

#### Permission Errors

- On macOS/Linux: Ensure tools have execute permissions
- On Windows: Run as administrator if needed

#### Path Issues

- Verify tools are in system PATH
- On Windows: Add installation directories to PATH environment variable

### Getting Help

If you encounter issues with external tool installation:

1. Check the tool's official documentation
2. Verify system requirements and compatibility
3. Test tools independently from command line
4. Check DevBoost logs for specific error messages

## Advanced Configuration

### Custom Tool Paths

If tools are installed in non-standard locations, you can configure custom paths in the DevBoost settings (feature planned for future release).

### Quality Presets

The File Optimization Tool includes several quality presets that automatically configure optimal settings for each external tool:

- **Maximum**: Best quality, larger file sizes
- **High**: Excellent quality with good compression
- **Medium**: Balanced quality and file size (default)
- **Low**: Smaller files with acceptable quality
- **Minimum**: Maximum compression, basic quality

### Batch Processing

External tools significantly improve batch processing performance:

- Parallel processing support
- Optimized memory usage
- Progress tracking and cancellation
- Detailed results reporting

## License and Legal

Please ensure you comply with the licenses of external tools:

- FFmpeg: LGPL/GPL (depending on build)
- Ghostscript: AGPL (commercial license available)
- Other tools: Various open-source licenses

Check each tool's license before use in commercial applications.
