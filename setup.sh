#!/usr/bin/env bash
# Build and run FLAC downloader

set -e

echo "🔨 Building FLAC Downloader..."

# Check Python version
python_version=$(python3 --version | awk '{print $2}')
echo "✅ Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate

# Upgrade pip
echo "📝 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Optional: Install dev dependencies
if [ "$1" == "--dev" ]; then
    echo "📦 Installing dev dependencies..."
    pip install -e ".[dev]"
fi

echo ""
echo "✅ Build complete!"
echo ""
echo "To run the downloader:"
echo "  source venv/bin/activate  # On Windows: venv\\Scripts\\activate"
echo "  python run.py"
echo ""
