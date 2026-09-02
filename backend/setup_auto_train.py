#!/usr/bin/env python
"""
Quick installer for auto-train pipeline dependencies
Installs YOLO-World model and ensures all dependencies are present
"""

import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def install_packages():
    """Install required packages"""
    packages = [
        "ultralytics>=8.0.0",  # YOLO
        "opencv-python>=4.5.0",  # cv2
        "pyyaml>=5.1",  # YAML parsing
        "pydantic>=2.0",  # Already installed
        "requests>=2.25.0",  # Already installed
    ]
    
    logger.info("Installing/verifying packages...")
    for package in packages:
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-q", package]
            )
            logger.info(f"✓ {package}")
        except Exception as e:
            logger.warning(f"⚠ {package}: {e}")


def download_yolo_world_model():
    """Download YOLO-World model for zero-shot detection"""
    logger.info("\nDownloading YOLO-World model (one-time)...")
    logger.info("This may take 1-2 minutes (~500MB)...\n")
    
    try:
        from ultralytics import YOLO
        
        logger.info("Loading yolov8s-world.pt...")
        model = YOLO("yolov8s-world.pt")
        logger.info("✓ YOLO-World model ready!\n")
        
        return True
    except Exception as e:
        logger.error(f"✗ Failed to download YOLO-World: {e}\n")
        return False


def verify_installation():
    """Verify all components are installed"""
    logger.info("Verifying installation...\n")
    
    checks = {
        "ultralytics": lambda: __import__("ultralytics").__version__,
        "cv2": lambda: __import__("cv2").__version__,
        "yaml": lambda: __import__("yaml").__version__,
        "pydantic": lambda: __import__("pydantic").__version__,
        "requests": lambda: __import__("requests").__version__,
    }
    
    all_good = True
    for name, check in checks.items():
        try:
            version = check()
            logger.info(f"✓ {name}: {version}")
        except Exception as e:
            logger.error(f"✗ {name}: {e}")
            all_good = False
    
    return all_good


def main():
    logger.info("="*60)
    logger.info("AUTO-TRAIN PIPELINE - SETUP")
    logger.info("="*60 + "\n")
    
    # Step 1: Install packages
    install_packages()
    
    # Step 2: Verify installation
    logger.info()
    if not verify_installation():
        logger.warning("\n⚠ Some packages failed to install")
        logger.info("Try running manually: pip install ultralytics opencv-python")
        return False
    
    # Step 3: Download YOLO-World model
    if not download_yolo_world_model():
        return False
    
    # Success!
    logger.info("="*60)
    logger.info("✓ SETUP COMPLETE!")
    logger.info("="*60)
    logger.info("\nYou can now run:")
    logger.info("  python auto_train.py --video sample.mp4 --classes person,bike --epochs 15")
    logger.info("  OR")
    logger.info("  python run_backend.py")
    logger.info("  (Then use API endpoints)")
    logger.info("\nFor more info, see: AUTO_TRAIN_GUIDE.md\n")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
