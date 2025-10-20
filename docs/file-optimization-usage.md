# File Optimization Tool - Usage Guide

This guide provides comprehensive examples and usage instructions for the File Optimization Tool in DevBoost.

## Getting Started

### Opening the Tool

1. Launch DevBoost
2. Click on "🗂️ File Optimization Tool" from the main menu
3. The tool interface will open with drag-and-drop area and optimization controls

### Interface Overview

The File Optimization Tool interface consists of:

- **Left Panel**: File list with drag-and-drop area
- **Right Panel**: Optimization settings and controls
- **Bottom Panel**: Progress tracking and status information
- **Results Dialog**: Detailed optimization results (appears after completion)

## Basic Usage

### Single File Optimization

1. **Add a file**:

   - Drag and drop a file onto the drop area, OR
   - Click "Add Files" button and select files, OR
   - Click "Add Folder" to add all supported files from a directory

2. **Configure settings** (optional):

   - Select a quality preset (Maximum, High, Medium, Low, Minimum)
   - Adjust specific settings in the Image/Video/PDF tabs
   - Enable/disable backup creation

3. **Start optimization**:
   - Click "Start Optimization" button
   - Monitor progress in the status area
   - View detailed results when complete

### Batch Processing

The tool excels at processing multiple files simultaneously:

```
Example batch operation:
- 50 JPEG images (total: 125 MB)
- Processing time: ~2 minutes
- Result: 89 MB (29% reduction)
- Success rate: 100%
```

## File Type Examples

### Image Optimization

#### JPEG Images

```
Input: photo.jpg (5.2 MB, 4000x3000)
Settings: Medium quality preset
Output: photo_optimized.jpg (2.1 MB, 4000x3000)
Compression: 59% size reduction
Method: jpegoptim (if available) or PIL/Pillow
```

#### PNG Images

```
Input: screenshot.png (1.8 MB, 1920x1080)
Settings: High quality preset
Output: screenshot_optimized.png (0.9 MB, 1920x1080)
Compression: 50% size reduction
Method: pngquant (if available) or PIL/Pillow
```

#### GIF Animations

```
Input: animation.gif (3.5 MB, 500x400, 30 frames)
Settings: Medium quality preset
Output: animation_optimized.gif (1.2 MB, 500x400, 30 frames)
Compression: 66% size reduction
Method: gifsicle (if available) or PIL/Pillow
```

### Video Optimization

#### MP4 Videos

```
Input: video.mp4 (45 MB, 1920x1080, 30fps)
Settings: Medium quality preset
Output: video_optimized.mp4 (18 MB, 1920x1080, 30fps)
Compression: 60% size reduction
Method: ffmpeg with H.264 codec
```

#### MOV to MP4 Conversion

```
Input: recording.mov (120 MB, 1920x1080, 60fps)
Settings: High quality preset, MP4 output format
Output: recording_optimized.mp4 (65 MB, 1920x1080, 60fps)
Compression: 46% size reduction
Method: ffmpeg conversion with optimization
```

#### Video to GIF Conversion

```
Input: clip.mp4 (25 MB, 1280x720, 24fps)
Settings: Medium quality, GIF output format, 15fps
Output: clip_optimized.gif (8 MB, 1280x720, 15fps)
Compression: 68% size reduction
Method: ffmpeg or gifski (if available)
```

### PDF Optimization

#### Document PDFs

```
Input: document.pdf (12 MB, 50 pages)
Settings: Medium quality preset
Output: document_optimized.pdf (4.2 MB, 50 pages)
Compression: 65% size reduction
Method: ghostscript with image compression
```

#### High-Resolution PDFs

```
Input: brochure.pdf (85 MB, 20 pages, high-res images)
Settings: High quality preset, 150 DPI
Output: brochure_optimized.pdf (28 MB, 20 pages)
Compression: 67% size reduction
Method: ghostscript with controlled image downsampling
```

## Quality Presets

### Maximum Quality

- **Use case**: Professional work, print materials
- **Image quality**: 95% (JPEG), minimal compression (PNG)
- **Video quality**: CRF 18 (excellent)
- **PDF quality**: 90%, 300 DPI
- **Trade-off**: Best quality, larger file sizes

### High Quality

- **Use case**: Web publishing, presentations
- **Image quality**: 85% (JPEG), good compression (PNG)
- **Video quality**: CRF 23 (very good)
- **PDF quality**: 80%, 200 DPI
- **Trade-off**: Excellent quality with moderate compression

### Medium Quality (Default)

- **Use case**: General use, sharing, storage
- **Image quality**: 75% (JPEG), balanced compression (PNG)
- **Video quality**: CRF 28 (good)
- **PDF quality**: 70%, 150 DPI
- **Trade-off**: Good balance of quality and file size

### Low Quality

- **Use case**: Web thumbnails, email attachments
- **Image quality**: 60% (JPEG), higher compression (PNG)
- **Video quality**: CRF 35 (acceptable)
- **PDF quality**: 60%, 100 DPI
- **Trade-off**: Smaller files, acceptable quality

### Minimum Quality

- **Use case**: Maximum compression, bandwidth-limited scenarios
- **Image quality**: 40% (JPEG), maximum compression (PNG)
- **Video quality**: CRF 45 (basic)
- **PDF quality**: 50%, 72 DPI
- **Trade-off**: Smallest files, basic quality

## Advanced Usage

### Custom Settings

#### Image Optimization

```
Custom JPEG settings:
- Quality: 80%
- Progressive: Enabled
- Max width: 1920px
- Max height: 1080px
- Output format: JPEG
- Preserve metadata: Disabled
```

#### Video Optimization

```
Custom video settings:
- Bitrate: 2M (2 Mbps)
- Frame rate: 30 fps
- Max resolution: 1280x720
- Output format: MP4
- Codec: H.264
```

#### PDF Optimization

```
Custom PDF settings:
- Quality: 75%
- DPI: 150
- Preserve metadata: Enabled
- Color space: RGB
- Compression: Maximum
```

### Batch Processing Scenarios

#### Website Image Optimization

```
Scenario: Optimize 200 product images for e-commerce site
Input: Mixed JPEG/PNG files (total: 450 MB)
Settings: High quality preset, max width 1200px
Result: 180 MB (60% reduction), web-optimized
Processing time: ~5 minutes
```

#### Video Library Compression

```
Scenario: Compress personal video collection
Input: 50 MP4 files (total: 15 GB)
Settings: Medium quality preset
Result: 6.8 GB (55% reduction)
Processing time: ~45 minutes
```

#### Document Archive Optimization

```
Scenario: Optimize PDF document archive
Input: 100 PDF files (total: 2.5 GB)
Settings: Medium quality preset, 150 DPI
Result: 950 MB (62% reduction)
Processing time: ~15 minutes
```

## Tips and Best Practices

### Performance Optimization

1. **Use external tools**: Install ffmpeg, ghostscript, pngquant, etc. for better performance
2. **Batch processing**: Process multiple files together for efficiency
3. **Quality presets**: Start with presets, then customize if needed
4. **Monitor progress**: Use the real-time progress tracking
5. **Enable backups**: Keep originals safe during optimization

### Quality Considerations

1. **Test settings**: Try different presets on sample files first
2. **Visual inspection**: Always check optimized files visually
3. **Format selection**: Choose appropriate output formats
4. **Resolution limits**: Set maximum dimensions for web use
5. **Metadata handling**: Decide whether to preserve or remove metadata

### File Management

1. **Backup strategy**: Enable automatic backups for important files
2. **Output naming**: Use descriptive suffixes (e.g., "\_optimized")
3. **Folder organization**: Process files in organized folder structures
4. **Results review**: Check the detailed results dialog after processing
5. **Error handling**: Review failed files and retry with different settings

## Troubleshooting

### Common Issues

#### Files Not Processing

- Check file format support
- Verify file permissions
- Ensure sufficient disk space
- Check for corrupted input files

#### Poor Compression Results

- Try different quality presets
- Install external optimization tools
- Check input file characteristics
- Adjust custom settings

#### Processing Errors

- Review error messages in results dialog
- Check external tool availability
- Verify file integrity
- Try processing files individually

### Performance Issues

#### Slow Processing

- Install external optimization tools (ffmpeg, pngquant, etc.)
- Process smaller batches
- Close other applications
- Check available system resources

#### Memory Usage

- Process files in smaller batches
- Restart application if needed
- Monitor system memory usage
- Consider file sizes and complexity

## Results Interpretation

### Compression Metrics

The results dialog provides detailed metrics:

- **Original Size**: Input file size
- **Optimized Size**: Output file size
- **Compression Ratio**: Percentage reduction
- **Processing Time**: Time taken per file
- **Method Used**: Optimization engine used
- **Success Rate**: Percentage of successful optimizations

### Quality Assessment

After optimization, consider:

1. **Visual quality**: Compare original and optimized files
2. **File size**: Check compression effectiveness
3. **Use case suitability**: Ensure quality meets requirements
4. **Format compatibility**: Verify output format works for intended use

## Integration with Other Tools

### Workflow Integration

The File Optimization Tool works well with other DevBoost tools:

1. **File Rename**: Organize files before optimization
2. **Scratch Pad**: Save optimization settings and results
3. **Image Optimizer**: Use for simple, single-image tasks

### External Workflow

Export optimization results and integrate with:

1. **Content Management Systems**: Upload optimized files
2. **Version Control**: Commit optimized assets
3. **Cloud Storage**: Sync compressed files
4. **Web Deployment**: Use optimized files for faster loading

This comprehensive guide should help you make the most of the File Optimization Tool's capabilities. For additional help, refer to the external tools setup documentation and the configuration options guide.

## Programmatic API

You can also use the File Optimization engines directly in code.

### Quick wrappers

```python
from pathlib import Path
from devboost.tools.file_optimization import (
    optimize_image,
    optimize_video,
    optimize_pdf,
    OptimizationSettings,
    QualityPreset,
)

# Common settings
settings = OptimizationSettings(quality_preset=QualityPreset.HIGH)

# Optimize an image
result_img = optimize_image(Path("photo.jpg"), Path("photo_optimized.jpg"), settings)
print(result_img)

# Optimize a video (MP4)
result_vid = optimize_video(Path("video.mp4"), Path("video_optimized.mp4"), settings)
print(result_vid)

# Optimize a PDF
result_pdf = optimize_pdf(Path("document.pdf"), Path("document_optimized.pdf"), settings)
print(result_pdf)
```

The wrappers instantiate the appropriate engine internally and return a result dictionary.

### Using engines directly

```python
from pathlib import Path
from devboost.tools.file_optimization import (
    ImageOptimizationEngine,
    VideoOptimizationEngine,
    PDFOptimizationEngine,
    OptimizationSettings,
    QualityPreset,
)

settings = OptimizationSettings(quality_preset=QualityPreset.MEDIUM)

# Images
img_engine = ImageOptimizationEngine()
res_img = img_engine.optimize_image(Path("input.png"), Path("output.png"), settings)

# Videos
vid_engine = VideoOptimizationEngine()
res_vid = vid_engine.optimize_video(Path("input.mov"), Path("output.mp4"), settings)

# PDFs
pdf_engine = PDFOptimizationEngine()
res_pdf = pdf_engine.optimize_pdf(Path("input.pdf"), Path("output.pdf"), settings)
```

Note: External tools like `ffmpeg`, `gifski`, and `ghostscript` improve results when installed. The engines automatically detect and use available tools.
