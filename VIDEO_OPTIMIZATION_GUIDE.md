# 🎬 비디오 파일 최적화 가이드

## 문제 상황
- 현재 비디오 파일 크기: **291MB** (`roha_conversion_demo.mp4.mp4`)
- 파일이 너무 커서 초기 로딩이 느리고, 메타데이터 로드에 시간이 오래 걸림
- 사용자 경험 저하

## 해결 방법

### 방법 1: FFmpeg를 사용한 비디오 압축 (권장)

#### 1단계: FFmpeg 설치 확인
```bash
# Windows (PowerShell)
winget install ffmpeg

# 또는 Chocolatey 사용
choco install ffmpeg

# Linux/Mac
sudo apt install ffmpeg  # Ubuntu/Debian
brew install ffmpeg      # Mac
```

#### 2단계: 비디오 압축 실행
```bash
# 현재 위치: homepage1/static/videos/
cd homepage1/static/videos

# 고품질 압축 (용량 약 50-70% 감소, 품질 유지)
ffmpeg -i roha_conversion_demo.mp4.mp4 -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k -movflags +faststart roha_conversion_demo_optimized.mp4

# 더 강한 압축 (용량 약 70-80% 감소, 약간의 품질 저하)
ffmpeg -i roha_conversion_demo.mp4.mp4 -c:v libx264 -crf 28 -preset medium -c:a aac -b:a 96k -movflags +faststart roha_conversion_demo_optimized.mp4
```

**옵션 설명:**
- `-crf 23`: 고품질 (18-28 범위, 낮을수록 고품질)
- `-crf 28`: 중간 품질 (용량 절감 우선)
- `-preset medium`: 인코딩 속도와 압축률의 균형
- `-movflags +faststart`: 웹 스트리밍 최적화 (메타데이터를 파일 앞부분에 배치)
- `-c:a aac -b:a 128k`: 오디오 코덱 및 비트레이트

#### 3단계: 파일 크기 비교
```bash
# Windows
dir roha_conversion_demo*.mp4

# Linux/Mac
ls -lh roha_conversion_demo*.mp4
```

#### 4단계: 최적화된 파일로 교체
```bash
# 백업
mv roha_conversion_demo.mp4.mp4 roha_conversion_demo.mp4.mp4.backup

# 최적화된 파일로 교체
mv roha_conversion_demo_optimized.mp4 roha_conversion_demo.mp4.mp4
```

### 방법 2: WebM 형식으로 변환 (더 작은 용량)

```bash
# WebM 변환 (VP9 코덱 사용)
ffmpeg -i roha_conversion_demo.mp4.mp4 -c:v libvpx-vp9 -crf 30 -b:v 0 -c:a libopus -b:a 128k roha_conversion_demo.webm

# HTML에서 WebM 우선 사용
# templates/components/video_player.html 수정 필요:
# <source src="/static/videos/roha_conversion_demo.webm" type="video/webm">
# <source src="/static/videos/roha_conversion_demo.mp4.mp4" type="video/mp4">
```

### 방법 3: 해상도 및 프레임레이트 조정

```bash
# 해상도 1080p로 다운스케일 (1920x1080 → 1280x720)
ffmpeg -i roha_conversion_demo.mp4.mp4 -vf "scale=1280:720" -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k -movflags +faststart roha_conversion_demo_720p.mp4

# 프레임레이트 30fps로 제한 (60fps → 30fps)
ffmpeg -i roha_conversion_demo.mp4.mp4 -r 30 -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k -movflags +faststart roha_conversion_demo_30fps.mp4
```

## 권장 설정

### 목표 용량: 50-100MB (현재 291MB의 1/3 ~ 1/6)

### 🎯 화질 보존 우선 설정 (권장)

**고품질 압축 (화질 거의 동일, 용량 50-60% 감소):**
```bash
ffmpeg -i roha_conversion_demo.mp4.mp4 \
  -c:v libx264 \
  -crf 20 \
  -preset slow \
  -c:a aac \
  -b:a 128k \
  -movflags +faststart \
  roha_conversion_demo_optimized.mp4
```
- **CRF 20**: 매우 고품질 (원본과 거의 구분 불가)
- **preset slow**: 최고 압축 효율 (인코딩 시간은 길지만 용량 최소화)
- **예상 용량**: 약 100-150MB (원본 291MB의 50-60%)
- **화질**: 전문가도 차이 인지 어려움

**균형잡힌 설정 (화질 우수, 용량 60-70% 감소):**
```bash
ffmpeg -i roha_conversion_demo.mp4.mp4 \
  -c:v libx264 \
  -crf 23 \
  -preset medium \
  -c:a aac \
  -b:a 128k \
  -movflags +faststart \
  roha_conversion_demo_optimized.mp4
```
- **CRF 23**: 고품질 (일반 사용자 차이 인지 어려움)
- **preset medium**: 속도와 압축의 균형
- **예상 용량**: 약 80-120MB (원본 291MB의 40-50%)
- **화질**: 시각적으로 거의 동일

**용량 우선 설정 (화질 양호, 용량 70-80% 감소):**
```bash
ffmpeg -i roha_conversion_demo.mp4.mp4 \
  -c:v libx264 \
  -crf 25 \
  -preset medium \
  -vf "scale=1280:720" \
  -r 30 \
  -c:a aac \
  -b:a 128k \
  -movflags +faststart \
  roha_conversion_demo_optimized.mp4
```
- **CRF 25**: 양호한 품질 (약간의 압축 아티팩트 가능)
- **해상도 다운스케일**: 1080p → 720p (용량 대폭 감소)
- **예상 용량**: 약 50-80MB (원본 291MB의 20-30%)
- **화질**: 데모용으로 충분한 품질

### 📊 CRF 값별 화질 비교

| CRF 값 | 화질 수준 | 용량 감소 | 권장 용도 |
|--------|----------|----------|----------|
| 18-20 | **거의 무손실** | 40-50% | 전문가용, 최고 품질 필요 |
| 21-23 | **고품질** | 50-60% | **일반 사용 (권장)** |
| 24-26 | **양호** | 60-70% | 웹 스트리밍, 용량 중요 |
| 27-28 | 보통 | 70-80% | 용량 우선 |

### ✅ 화질 보존 팁

1. **CRF 20-23 사용**: 화질 손실 최소화
2. **preset slow 사용**: 같은 CRF에서 더 작은 용량 (인코딩 시간 증가)
3. **해상도 유지**: 원본 해상도 그대로 유지 (scale 옵션 제거)
4. **프레임레이트 유지**: 원본 프레임레이트 유지 (-r 옵션 제거)
5. **2-Pass 인코딩**: 더 정밀한 용량 제어 (선택사항)

## 배포 서버 업로드

최적화된 파일을 배포 서버에 업로드:

```bash
# Windows PowerShell
scp homepage1\static\videos\roha_conversion_demo_optimized.mp4 ubuntu@52.78.116.159:~/RohaTax-App/static/videos/roha_conversion_demo.mp4.mp4

# 또는 기존 파일 백업 후 교체
ssh ubuntu@52.78.116.159 "cd ~/RohaTax-App/static/videos && mv roha_conversion_demo.mp4.mp4 roha_conversion_demo.mp4.mp4.backup"
scp homepage1\static\videos\roha_conversion_demo_optimized.mp4 ubuntu@52.78.116.159:~/RohaTax-App/static/videos/roha_conversion_demo.mp4.mp4
```

## 참고사항

### 🔍 화질에 대한 자세한 설명

**CRF (Constant Rate Factor)란?**
- H.264 인코딩의 품질 제어 방식
- 값이 낮을수록 고품질 (용량 큼)
- 값이 높을수록 저품질 (용량 작음)
- **중요**: CRF는 "시각적 품질"을 기준으로 하므로, 같은 CRF 값이면 비슷한 시각적 품질 유지

**화질 손실이 걱정되시나요?**
- ✅ **CRF 20-23 사용 시**: 전문가도 원본과 구분하기 어려움
- ✅ **CRF 20**: 거의 무손실 압축 (원본의 95-98% 품질)
- ✅ **CRF 23**: 고품질 압축 (원본의 90-95% 품질, 일반 사용자 차이 인지 어려움)
- ⚠️ **CRF 25 이상**: 약간의 압축 아티팩트 가능 (데모용으로는 충분)

**실제 테스트 권장:**
1. CRF 20으로 먼저 압축
2. 원본과 나란히 비교 재생
3. 차이가 보이면 CRF를 더 낮춤 (18-19)
4. 차이가 안 보이면 CRF를 높여 용량 더 절감 (23-25)

### 📋 기타 최적화 옵션

1. **faststart 플래그**: 웹 스트리밍에 필수. 메타데이터를 파일 앞부분에 배치하여 초기 로딩 속도 향상
2. **preset 옵션**:
   - `ultrafast`: 빠른 인코딩, 큰 용량
   - `fast`: 빠른 인코딩, 큰 용량
   - `medium`: 균형 (권장)
   - `slow`: 느린 인코딩, 작은 용량 (화질 보존에 최적)
   - `veryslow`: 매우 느린 인코딩, 최소 용량
3. **해상도**: 원본 해상도 유지 권장 (화질 보존)
4. **프레임레이트**: 원본 프레임레이트 유지 권장 (화질 보존)

## 검증

최적화 후 다음을 확인:
1. 파일 크기 확인
2. 브라우저에서 재생 테스트
3. 로딩 속도 확인 (개발자 도구 Network 탭)
4. **품질 확인 (시각적 비교)**: 원본과 나란히 재생하여 차이 확인

### 🎬 화질 비교 방법

**방법 1: VLC 플레이어 사용 (권장)**
```bash
# VLC에서 두 비디오를 나란히 재생
# 도구 → 효과 및 필터 → 비디오 효과 → Clone
```

**방법 2: 브라우저에서 직접 비교**
- 원본과 최적화된 파일을 각각 다른 탭에서 재생
- 같은 구간을 동시에 재생하며 비교

**방법 3: FFmpeg로 품질 측정 (선택사항)**
```bash
# PSNR (Peak Signal-to-Noise Ratio) 측정
ffmpeg -i roha_conversion_demo.mp4.mp4 -i roha_conversion_demo_optimized.mp4 -lavfi psnr -f null -
```

### ✅ 최종 권장사항

**화질이 가장 중요하다면:**
```bash
# CRF 20, preset slow (최고 품질, 용량 100-150MB)
ffmpeg -i roha_conversion_demo.mp4.mp4 -c:v libx264 -crf 20 -preset slow -c:a aac -b:a 128k -movflags +faststart roha_conversion_demo_optimized.mp4
```

**균형을 원한다면:**
```bash
# CRF 23, preset medium (고품질, 용량 80-120MB) - 권장
ffmpeg -i roha_conversion_demo.mp4.mp4 -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k -movflags +faststart roha_conversion_demo_optimized.mp4
```

**결론**: CRF 20-23을 사용하면 **화질 저하 없이** 용량을 50-60% 줄일 수 있습니다! 🎯

