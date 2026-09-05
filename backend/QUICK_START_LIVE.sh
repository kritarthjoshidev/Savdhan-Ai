#!/bin/bash
# 🚀 Quick Start Script - Live Detection
# Run this to test everything

echo "═══════════════════════════════════════════════════════════════"
echo "  🎯 Live Detection Quick Start"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}1. Backend شروع ہو رہی ہے...${NC}"
echo ""
echo "Command:"
echo "  python run_backend.py"
echo ""
echo -e "${YELLOW}نوٹ: ایک نئی ونڈو میں یہ چلائیں یا Ctrl+C سے روکیں${NC}"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo ""
echo -e "${BLUE}2. Backend شروع ہو جانے کے بعد یہ commands استعمال کریں:${NC}"
echo ""

echo -e "${GREEN}A. WEBCAM سے Detection:${NC}"
echo "---"
echo 'curl -X POST "http://localhost:8000/api/v1/live/webcam/detect" \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '"'"'{"device_id": 0, "conf_threshold": 0.5, "max_frames": 50}'"'"''
echo ""

echo -e "${GREEN}B. CCTV سے Detection (RTSP):${NC}"
echo "---"
echo '# پہلے اپنا RTSP URL لگائیں!'
echo 'curl -X POST "http://localhost:8000/api/v1/live/rtsp/detect" \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '"'"'{'
echo '    "rtsp_url": "rtsp://admin:password@192.168.1.100:554/stream",'
echo '    "conf_threshold": 0.5,'
echo '    "max_frames": 100'
echo '  }'"'"''
echo ""

echo -e "${GREEN}C. Webcam Available کی جانچ:${NC}"
echo "---"
echo 'curl "http://localhost:8000/api/v1/live/webcam/available?device_id=0"'
echo ""

echo -e "${GREEN}D. RTSP Connection Test:${NC}"
echo "---"
echo 'curl -X POST "http://localhost:8000/api/v1/live/rtsp/test" \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '"'"'{"rtsp_url": "rtsp://your_url_here"}'"'"''
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo ""
echo -e "${BLUE}3. Python Test Client:${NC}"
echo "---"
echo "python test_live_detection.py"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo ""
echo -e "${BLUE}4. WebSocket سے Real-Time Streaming:${NC}"
echo "---"
echo "JavaScript/Python میں:"
echo ""
echo "  // Webcam"
echo "  ws://localhost:8000/api/v1/live/webcam/stream?device_id=0"
echo ""
echo "  // RTSP"
echo "  ws://localhost:8000/api/v1/live/rtsp/stream?rtsp_url=rtsp://..."
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo ""
echo -e "${GREEN}✓ تمام Features:${NC}"
echo ""
echo "  📷 Webcam Detection"
echo "  📹 RTSP/CCTV Detection"
echo "  🎬 Video File Detection"
echo "  🔗 WebSocket Real-Time Streaming"
echo "  🚀 Auto GPU/CPU Detection"
echo "  📊 Detection Statistics"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo ""
echo -e "${YELLOW}API Documentation:${NC}"
echo "  http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}Guide (اردو میں):${NC}"
echo "  LIVE_DETECTION_GUIDE.md"
echo ""
echo -e "${YELLOW}Summary:${NC}"
echo "  IMPLEMENTATION_SUMMARY_LIVE.md"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo ""
echo -e "${GREEN}🎉 شروhappy Detecting!${NC}"
echo ""
