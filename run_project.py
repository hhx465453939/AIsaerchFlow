import subprocess
import time
import webbrowser

backend_cmd = ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
frontend_cmd = ["streamlit", "run", "webui/app.py", "--server.port", "8501"]

backend = subprocess.Popen(backend_cmd)
time.sleep(2)
webbrowser.open("http://localhost:8501")
frontend = subprocess.Popen(frontend_cmd)

try:
    backend.wait()
    frontend.wait()
except KeyboardInterrupt:
    backend.terminate()
    frontend.terminate() 