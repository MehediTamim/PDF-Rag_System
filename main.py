import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    import subprocess
    import signal
    
    app_path = Path(__file__).parent / "presentation" / "streamlit" / "app.py"
    
    print("🚀 Starting RAG Chat System...")
    print("📍 Running Streamlit application...")
    print("🌐 Application will open at: http://localhost:8501")
    print("-" * 60)
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            str(app_path),
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n\n✋ Application stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        sys.exit(1)
else:
    from presentation.streamlit.app import *
