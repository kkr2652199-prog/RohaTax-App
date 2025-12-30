#!/bin/bash
# 배포 서버에서 비디오 파일 최적화 스크립트
# 화질 보존 우선 설정 (CRF 23, preset medium)

# UTF-8 encoding settings
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

PROJECT_DIR="/home/ubuntu/RohaTax-App"
VIDEO_DIR="$PROJECT_DIR/static/videos"
VIDEO_FILE="roha_conversion_demo.mp4.mp4"
VIDEO_PATH="$VIDEO_DIR/$VIDEO_FILE"
OPTIMIZED_FILE="roha_conversion_demo_optimized.mp4"
OPTIMIZED_PATH="$VIDEO_DIR/$OPTIMIZED_FILE"
BACKUP_FILE="roha_conversion_demo.mp4.mp4.backup"
BACKUP_PATH="$VIDEO_DIR/$BACKUP_FILE"

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "Starting video optimization on deployment server..."

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    log "FFmpeg is not installed. Installing FFmpeg..."
    sudo apt-get update
    sudo apt-get install -y ffmpeg
    if [ $? -ne 0 ]; then
        log "ERROR: Failed to install FFmpeg"
        exit 1
    fi
    log "FFmpeg installed successfully"
else
    log "FFmpeg is already installed: $(ffmpeg -version | head -n 1)"
fi

# Check if video file exists
if [ ! -f "$VIDEO_PATH" ]; then
    log "ERROR: Video file not found: $VIDEO_PATH"
    exit 1
fi

# Get original file size
ORIGINAL_SIZE=$(du -h "$VIDEO_PATH" | cut -f1)
log "Original video file size: $ORIGINAL_SIZE"

# Backup original file
log "Backing up original file..."
cp "$VIDEO_PATH" "$BACKUP_PATH"
if [ $? -ne 0 ]; then
    log "ERROR: Failed to backup original file"
    exit 1
fi
log "Backup created: $BACKUP_PATH"

# Optimize video (CRF 23, preset medium - balanced quality and size)
log "Starting video optimization (this may take several minutes)..."
log "Settings: CRF 23, preset medium (high quality, 50-60% size reduction)"

ffmpeg -i "$VIDEO_PATH" \
  -c:v libx264 \
  -crf 23 \
  -preset medium \
  -c:a aac \
  -b:a 128k \
  -movflags +faststart \
  -y \
  "$OPTIMIZED_PATH" 2>&1 | tee /tmp/ffmpeg_output.log

if [ $? -ne 0 ]; then
    log "ERROR: Video optimization failed"
    log "Check /tmp/ffmpeg_output.log for details"
    exit 1
fi

# Get optimized file size
OPTIMIZED_SIZE=$(du -h "$OPTIMIZED_PATH" | cut -f1)
log "Optimized video file size: $OPTIMIZED_SIZE"

# Calculate size reduction
ORIGINAL_BYTES=$(stat -f%z "$VIDEO_PATH" 2>/dev/null || stat -c%s "$VIDEO_PATH" 2>/dev/null)
OPTIMIZED_BYTES=$(stat -f%z "$OPTIMIZED_PATH" 2>/dev/null || stat -c%s "$OPTIMIZED_PATH" 2>/dev/null)
REDUCTION_PERCENT=$((100 - (OPTIMIZED_BYTES * 100 / ORIGINAL_BYTES)))
log "Size reduction: ${REDUCTION_PERCENT}%"

# Replace original with optimized file
log "Replacing original file with optimized version..."
mv "$OPTIMIZED_PATH" "$VIDEO_PATH"
if [ $? -ne 0 ]; then
    log "ERROR: Failed to replace original file"
    log "Restoring from backup..."
    mv "$BACKUP_PATH" "$VIDEO_PATH"
    exit 1
fi

log "✅ Video optimization completed successfully!"
log "Original file backed up to: $BACKUP_PATH"
log "Optimized file: $VIDEO_PATH ($OPTIMIZED_SIZE, ${REDUCTION_PERCENT}% reduction)"

