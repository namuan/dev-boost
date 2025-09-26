# File Optimization Tool - Configuration Guide

This guide provides detailed information about all configuration options and settings available in the File Optimization Tool.

## Configuration Overview

The File Optimization Tool offers extensive configuration options organized into several categories:

- **Quality Presets**: Pre-configured optimization profiles
- **Image Settings**: JPEG, PNG, GIF, and WebP specific options
- **Video Settings**: MP4, MOV, AVI, and format conversion options
- **PDF Settings**: Document compression and quality options
- **General Settings**: Backup, naming, and processing options

## Quality Presets

Quality presets provide quick configuration for common use cases. Each preset adjusts multiple parameters across all file types.

### Preset Definitions

| Preset  | Image Quality | Video CRF | PDF Quality | Use Case              |
| ------- | ------------- | --------- | ----------- | --------------------- |
| Maximum | 95%           | 18        | 90%         | Professional, print   |
| High    | 85%           | 23        | 80%         | Web publishing        |
| Medium  | 75%           | 28        | 70%         | General use (default) |
| Low     | 60%           | 35        | 60%         | Thumbnails, email     |
| Minimum | 40%           | 45        | 50%         | Maximum compression   |

### Custom Preset Creation

You can create custom presets by:

1. Adjusting individual settings
2. Saving the configuration
3. Naming your custom preset
4. Reusing across sessions

## Image Optimization Settings

### JPEG Settings

#### Quality Control

```
Quality Range: 1-100
Default: 75 (Medium preset)
Description: Higher values = better quality, larger files
Recommended:
- Web images: 70-85
- Print images: 85-95
- Thumbnails: 50-70
```

#### Progressive JPEG

```
Options: Enabled/Disabled
Default: Enabled
Description: Creates progressive JPEGs that load incrementally
Benefits: Better perceived loading performance on web
```

#### Metadata Preservation

```
Options: Preserve/Remove
Default: Remove
Description: Keeps or strips EXIF, IPTC, and other metadata
Considerations:
- Preserve: Keeps camera settings, GPS, copyright
- Remove: Reduces file size, improves privacy
```

#### Dimension Limits

```
Max Width: 1-10000 pixels (default: no limit)
Max Height: 1-10000 pixels (default: no limit)
Resize Method: Lanczos (high quality)
Aspect Ratio: Always preserved
```

### PNG Settings

#### Compression Level

```
Range: 0-9
Default: 6
Description: PNG compression level (0=fast, 9=best compression)
Performance Impact:
- 0-3: Fast compression, larger files
- 4-6: Balanced (recommended)
- 7-9: Slow compression, smaller files
```

#### Color Optimization

```
Options: Automatic/Force RGB/Force Palette
Default: Automatic
Description:
- Automatic: Chooses best color mode
- Force RGB: Maintains full color depth
- Force Palette: Converts to indexed color (smaller files)
```

#### Transparency Handling

```
Options: Preserve/Remove/Optimize
Default: Preserve
Description:
- Preserve: Keeps alpha channel intact
- Remove: Converts to opaque (smaller files)
- Optimize: Removes unnecessary transparency
```

### GIF Settings

#### Color Reduction

```
Max Colors: 2-256
Default: 256
Description: Maximum colors in palette
Quality Impact:
- 256: Best quality, larger files
- 128: Good balance
- 64: Acceptable for simple graphics
- 32: Minimal for basic animations
```

#### Animation Optimization

```
Options: Enabled/Disabled
Default: Enabled
Description: Optimizes frame differences and timing
Techniques:
- Frame differencing
- Disposal method optimization
- Color palette optimization
```

#### Loop Control

```
Options: Preserve/Force Loop/No Loop
Default: Preserve
Description: Controls animation looping behavior
```

### WebP Settings

#### Quality Mode

```
Options: Lossy/Lossless
Default: Lossy
Quality Range: 0-100 (lossy), 0-100 (lossless effort)
Description:
- Lossy: Similar to JPEG, smaller files
- Lossless: Perfect quality, larger files
```

#### Advanced Options

```
Method: 0-6 (compression effort)
Default: 4
Description: Higher values = better compression, slower processing

Alpha Quality: 0-100
Default: 100
Description: Quality of alpha channel compression
```

## Video Optimization Settings

### Quality Control

#### Constant Rate Factor (CRF)

```
Range: 0-51
Default: 28 (Medium preset)
Description: Video quality setting (lower = better quality)
Guidelines:
- 18-23: Visually lossless (large files)
- 23-28: High quality (recommended)
- 28-35: Medium quality
- 35-45: Low quality (small files)
```

#### Bitrate Control

```
Options: CRF (default) / Target Bitrate / Max Bitrate
Target Bitrate: 500k-50M
Max Bitrate: 1M-100M
Description:
- CRF: Variable bitrate, consistent quality
- Target: Fixed average bitrate
- Max: Bitrate ceiling for streaming
```

### Resolution and Frame Rate

#### Resolution Limits

```
Max Width: 480-4096 pixels
Max Height: 360-2160 pixels
Default: No limit
Scaling: Maintains aspect ratio
```

#### Frame Rate Control

```
Options: Preserve/Custom
Custom Range: 1-120 fps
Default: Preserve original
Common Values:
- 24 fps: Cinema standard
- 30 fps: Standard video
- 60 fps: Smooth motion
```

### Codec Settings

#### Video Codec

```
Options: H.264 (default) / H.265 / VP9
H.264: Best compatibility
H.265: Better compression, newer devices
VP9: Open standard, good compression
```

#### Audio Codec

```
Options: AAC (default) / MP3 / Opus
AAC: Best quality and compatibility
MP3: Universal compatibility
Opus: Best compression for web
```

#### Audio Quality

```
Bitrate: 64k-320k
Default: 128k
Sample Rate: 22050-48000 Hz
Default: 44100 Hz
```

### Format Conversion

#### Output Formats

```
Supported: MP4, MOV, AVI, MKV, WebM, GIF
Default: MP4 (best compatibility)
Recommendations:
- MP4: General use, web, mobile
- WebM: Web streaming
- GIF: Short clips, animations
```

#### Container Options

```
MP4: H.264 + AAC (recommended)
WebM: VP9 + Opus
MKV: Any codec combination
MOV: QuickTime compatibility
```

## PDF Optimization Settings

### Quality Control

#### Overall Quality

```
Range: 1-100
Default: 70 (Medium preset)
Description: General PDF quality setting
Impact: Affects image compression and text rendering
```

#### Image DPI

```
Range: 72-300 DPI
Default: 150 DPI
Description: Resolution for embedded images
Guidelines:
- 72 DPI: Screen viewing only
- 150 DPI: General use (recommended)
- 300 DPI: Print quality
```

### Compression Settings

#### Image Compression

```
JPEG Quality: 1-100
Default: 75
Description: Quality for JPEG images in PDF

PNG Compression: 0-9
Default: 6
Description: Compression level for PNG images
```

#### Text and Vector Handling

```
Options: Preserve/Optimize/Rasterize
Default: Optimize
Description:
- Preserve: No changes to text/vectors
- Optimize: Compress while maintaining quality
- Rasterize: Convert to images (smaller, less searchable)
```

### Document Structure

#### Metadata Preservation

```
Options: Preserve/Remove/Optimize
Default: Optimize
Description:
- Preserve: Keep all metadata
- Remove: Strip all metadata
- Optimize: Keep essential, remove bloat
```

#### Bookmark and Link Handling

```
Options: Preserve/Remove
Default: Preserve
Description: Maintains document navigation structure
```

## General Settings

### Backup Options

#### Automatic Backup

```
Options: Enabled/Disabled
Default: Enabled
Description: Creates backup copies before optimization
Location: Same directory with "_backup" suffix
```

#### Backup Naming

```
Pattern: {filename}_backup.{extension}
Custom Pattern: Available
Options: Timestamp, counter, custom suffix
```

### Output Configuration

#### File Naming

```
Pattern: {filename}_optimized.{extension}
Custom Options:
- {filename}: Original name
- {timestamp}: Current date/time
- {preset}: Quality preset name
- {compression}: Compression percentage
```

#### Output Directory

```
Options: Same as source/Custom directory
Default: Same as source
Description: Where optimized files are saved
```

### Processing Options

#### Parallel Processing

```
Thread Count: 1-16
Default: Auto (CPU cores)
Description: Number of files processed simultaneously
Performance: More threads = faster processing (up to CPU limit)
```

#### Memory Management

```
Options: Conservative/Balanced/Aggressive
Default: Balanced
Description:
- Conservative: Lower memory usage, slower
- Balanced: Good performance and stability
- Aggressive: Maximum speed, high memory usage
```

#### Error Handling

```
Options: Stop on Error/Continue/Retry
Default: Continue
Description:
- Stop: Halt processing on first error
- Continue: Skip failed files, process others
- Retry: Attempt failed files with fallback settings
```

### External Tool Integration

#### Tool Detection

```
Automatic: Scans system PATH for tools
Manual: Specify tool locations
Priority: External tools > built-in engines
```

#### Tool Configuration

```
ffmpeg: Video processing
ghostscript: PDF optimization
pngquant: PNG compression
jpegoptim: JPEG optimization
gifsicle: GIF optimization
```

## Advanced Configuration

### Performance Tuning

#### CPU Usage

```
Priority: Low/Normal/High
Default: Normal
Description: Process priority for optimization tasks
```

#### I/O Optimization

```
Buffer Size: 64KB-1MB
Default: 256KB
Description: File read/write buffer size
```

### Quality Profiles

#### Custom Profiles

```
Create: Save current settings as named profile
Load: Apply saved profile settings
Share: Export/import profile configurations
```

#### Profile Parameters

```
All settings can be saved in profiles:
- Quality presets
- Format-specific settings
- Processing options
- Output configuration
```

### Integration Settings

#### File Association

```
Options: Register file types/Manual selection
Description: Associate file types with optimization tool
```

#### Context Menu

```
Options: Enable/Disable system context menu
Description: Right-click optimization in file explorer
```

## Configuration Files

### Settings Storage

```
Location: ~/.devboost/file_optimization/
Files:
- settings.json: Main configuration
- presets.json: Quality presets
- tools.json: External tool paths
```

### Backup and Restore

```
Export: Save all settings to file
Import: Load settings from file
Reset: Restore default settings
```

### Version Compatibility

```
Settings are versioned for compatibility
Automatic migration on updates
Backup created before migration
```

## Troubleshooting Configuration

### Common Issues

#### Settings Not Saving

- Check file permissions
- Verify configuration directory exists
- Restart application

#### Poor Results

- Review quality settings
- Check external tool availability
- Verify input file characteristics

#### Performance Problems

- Adjust thread count
- Modify memory settings
- Check system resources

### Reset Options

#### Partial Reset

```
Reset specific categories:
- Quality presets only
- Tool configurations only
- Processing settings only
```

#### Complete Reset

```
Restore all default settings
Clear custom presets
Reset tool paths
```

This configuration guide provides comprehensive control over the File Optimization Tool's behavior. Start with the quality presets and adjust individual settings as needed for your specific use cases.
