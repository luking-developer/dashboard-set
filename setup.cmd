call pip install uv

call "uv venv .venv --python=3.11.13"
call ".venv/Scripts/activate"

call "uv pip install -r requirements.txt"
