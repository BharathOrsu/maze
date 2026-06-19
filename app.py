import os
import re
import sys
import json
import uuid
import time
import subprocess
import shutil
import threading
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
_base_dir = os.path.dirname(os.path.abspath(__file__))

# Fallback to /tmp if the app directory is read-only (e.g. serverless)
try:
    _test_write = os.path.join(_base_dir, '.write_test')
    with open(_test_write, 'w') as _f:
        _f.write('ok')
    os.remove(_test_write)
    _data_dir = _base_dir
except OSError:
    _data_dir = '/tmp/manim_studio'
    os.makedirs(_data_dir, exist_ok=True)

app.config['RENDER_DIR'] = os.path.join(_data_dir, 'renders')
app.config['HISTORY_FILE'] = os.path.join(_data_dir, 'render_history.json')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['MAX_HISTORY'] = 50

# Ensure render directory exists
os.makedirs(app.config['RENDER_DIR'], exist_ok=True)

# ============================================
# Docker Detection
# ============================================
DOCKER_AVAILABLE = False
docker_client = None
try:
    import docker as docker_sdk
    docker_client = docker_sdk.from_env()
    docker_client.ping()
    DOCKER_AVAILABLE = True
except ImportError:
    # docker package not installed
    pass
except Exception:
    # Docker daemon not running or other error
    pass

# ============================================
# Render History Management
# ============================================
def load_history():
    """Load render history from JSON file."""
    try:
        if os.path.exists(app.config['HISTORY_FILE']):
            with open(app.config['HISTORY_FILE'], 'r') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError):
        pass
    return []

def save_history(history):
    """Save render history to JSON file."""
    try:
        with open(app.config['HISTORY_FILE'], 'w') as f:
            json.dump(history, f, indent=2)
    except IOError:
        pass

def add_to_history(job_id, code, status, filename=None, error=None):
    """Add a render job to history."""
    history = load_history()
    entry = {
        'job_id': job_id,
        'code_preview': code[:200] + ('...' if len(code) > 200 else ''),
        'full_code': code,
        'status': status,
        'filename': filename,
        'error': error,
        'timestamp': datetime.now().isoformat(),
        'video_url': f'/api/video/{job_id}/{filename}' if filename else None,
        'download_url': f'/api/download/{job_id}/{filename}' if filename else None,
    }
    history.insert(0, entry)
    # Keep only last N entries
    history = history[:app.config['MAX_HISTORY']]
    save_history(history)
    return entry

# ============================================
# Syntax Validation
# ============================================
def validate_python_syntax(code):
    """Validate Python syntax without executing."""
    try:
        compile(code, '<manim_code>', 'exec')
        return True, None
    except SyntaxError as e:
        return False, {
            'line': e.lineno,
            'column': e.offset,
            'message': e.msg,
            'text': e.text
        }

def validate_manim_code(code):
    """Validate that code is safe and has proper Manim structure."""
    errors = []
    warnings = []

    # Check for dangerous imports
    dangerous_modules = ['os', 'sys', 'subprocess', 'shutil', 'socket',
                         'http', 'urllib', 'requests', 'ctypes', 'importlib']
    for module in dangerous_modules:
        if re.search(rf'\bimport\s+{module}\b', code) or \
           re.search(rf'\bfrom\s+{module}\b', code):
            warnings.append(f'Discouraged import: {module}')

    # Check for file operations
    if re.search(r'\b(open|exec|eval|compile|__import__)\s*\(', code):
        warnings.append('Potentially unsafe function call detected')

    # Check for network operations
    if re.search(r'\burlopen|requests\.(get|post|put|delete)\b', code):
        warnings.append('Network operation detected')

    # Check for class inheriting from Scene
    if 'class' in code and 'Scene' not in code:
        warnings.append('No Scene class found - Manim animations should define a Scene subclass')

    return errors, warnings

# ============================================
# Routes
# ============================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/validate', methods=['POST'])
def validate_code():
    """Validate Manim code syntax and safety before rendering."""
    data = request.json
    code = data.get('code', '')

    if not code.strip():
        return jsonify({'valid': True, 'errors': [], 'warnings': []})

    # Python syntax check
    syntax_ok, syntax_error = validate_python_syntax(code)
    if not syntax_ok:
        return jsonify({
            'valid': False,
            'errors': [syntax_error],
            'warnings': []
        })

    # Manim-specific validation
    errors, warnings = validate_manim_code(code)

    return jsonify({
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    })

@app.route('/api/render', methods=['POST'])
def render_code():
    """Render Manim code, optionally in a Docker container."""
    data = request.json
    code = data.get('code', '')
    quality = data.get('quality', 'low')
    use_docker = data.get('use_docker', DOCKER_AVAILABLE)

    if not code.strip():
        return jsonify({'error': 'No code provided'}), 400

    # Validate quality parameter
    if quality not in ('low', 'medium', 'high', '4k'):
        quality = 'low'

    # Syntax validation first
    syntax_ok, syntax_error = validate_python_syntax(code)
    if not syntax_ok:
        return jsonify({
            'error': f'Syntax error: {syntax_error["message"]}',
            'details': f'Line {syntax_error["line"]}: {syntax_error["text"]}',
            'syntax_error': syntax_error
        }), 400

    # Create unique job ID
    job_id = str(uuid.uuid4())[:8]
    job_dir = os.path.join(app.config['RENDER_DIR'], job_id)
    os.makedirs(job_dir, exist_ok=True)

    # Ensure code imports manim
    if 'from manim import' not in code and 'import manim' not in code:
        code = 'from manim import *\n\n' + code

    # Save code to file
    code_file = os.path.join(job_dir, 'scene.py')
    with open(code_file, 'w') as f:
        f.write(code)

    # Map quality settings
    quality_map = {
        'low': '-ql',
        'medium': '-qm',
        'high': '-qh',
        '4k': '-qk'
    }
    quality_flag = quality_map.get(quality, '-ql')

    # Choose rendering method
    if use_docker and DOCKER_AVAILABLE:
        return _render_in_docker(job_id, job_dir, code_file, quality_flag, code)
    else:
        return _render_locally(job_id, job_dir, code_file, quality_flag, code)

def _render_locally(job_id, job_dir, code_file, quality_flag, code):
    """Render Manim code directly on the host."""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'manim', quality_flag, '-o',
             os.path.join(job_dir, 'output'), code_file],
            capture_output=True,
            text=True,
            timeout=180,
            cwd=job_dir
        )

        if result.returncode != 0:
            error_msg = result.stderr if result.stderr else result.stdout
            lines = error_msg.split('\n')
            meaningful_lines = [l for l in lines if l.strip() and 'File' not in l[:5]]
            error_text = meaningful_lines[-1] if meaningful_lines else 'Render failed'
            add_to_history(job_id, code, 'error', error=error_text)
            return jsonify({
                'error': error_text,
                'details': error_msg,
                'job_id': job_id
            }), 500

        # Find the output video
        output_files = list(Path(job_dir).rglob('*.mp4'))
        if not output_files:
            add_to_history(job_id, code, 'error', error='No output video generated')
            return jsonify({'error': 'No output video generated'}), 500

        add_to_history(job_id, code, 'success', filename=output_files[0].name)
        return jsonify({
            'success': True,
            'job_id': job_id,
            'video_url': f'/api/video/{job_id}/{output_files[0].name}',
            'filename': output_files[0].name
        })

    except subprocess.TimeoutExpired:
        add_to_history(job_id, code, 'error', error='Render timed out (180s limit)')
        return jsonify({'error': 'Render timed out (180s limit)'}), 500
    except Exception as e:
        add_to_history(job_id, code, 'error', error=str(e))
        return jsonify({'error': str(e)}), 500

def _render_in_docker(job_id, job_dir, code_file, quality_flag, code):
    """Render Manim code inside a Docker container."""
    try:
        # Build the render command
        render_cmd = f'cd /workspace && python -m manim {quality_flag} -o output scene.py'

        # Run container with volume mount
        container = docker_client.containers.run(
            'manimcommunity/manim:stable',
            command=['sh', '-c', render_cmd],
            volumes={
                os.path.abspath(job_dir): {
                    'bind': '/workspace',
                    'mode': 'rw'
                }
            },
            mem_limit='1g',
            nano_cpus=2 * 10 ** 9,  # 2 CPUs
            detach=True,
            remove=False,
            working_dir='/workspace'
        )

        # Wait for container with timeout
        result = container.wait(timeout=180)
        exit_code = result.get('StatusCode', -1)

        # Get container logs
        logs = container.logs().decode('utf-8', errors='replace')

        # Cleanup container
        try:
            container.remove(force=True)
        except Exception:
            pass

        if exit_code != 0:
            error_msg = logs
            lines = error_msg.split('\n')
            meaningful_lines = [l for l in lines if l.strip() and 'File' not in l[:5]]
            error_text = meaningful_lines[-1] if meaningful_lines else 'Render failed'
            add_to_history(job_id, code, 'error', error=error_text)
            return jsonify({
                'error': error_text,
                'details': error_msg,
                'job_id': job_id
            }), 500

        # Find the output video
        output_files = list(Path(job_dir).rglob('*.mp4'))
        if not output_files:
            add_to_history(job_id, code, 'error', error='No output video generated')
            return jsonify({'error': 'No output video generated'}), 500

        add_to_history(job_id, code, 'success', filename=output_files[0].name)
        return jsonify({
            'success': True,
            'job_id': job_id,
            'video_url': f'/api/video/{job_id}/{output_files[0].name}',
            'filename': output_files[0].name,
            'rendered_in': 'docker'
        })

    except Exception as e:
        add_to_history(job_id, code, 'error', error=str(e))
        return jsonify({'error': f'Docker render failed: {str(e)}'}), 500

@app.route('/api/video/<job_id>/<filename>')
def serve_video(job_id, filename):
    """Serve a rendered video file."""
    safe_job_id = os.path.basename(job_id)
    safe_filename = os.path.basename(filename)

    if not re.match(r'^[a-f0-9-]+$', safe_job_id):
        return jsonify({'error': 'Invalid job ID'}), 400

    job_dir = os.path.join(app.config['RENDER_DIR'], safe_job_id)
    output_files = list(Path(job_dir).rglob(f'*{safe_filename}*'))

    if output_files:
        return send_file(str(output_files[0]), mimetype='video/mp4', as_attachment=False)

    all_mp4 = list(Path(job_dir).rglob('*.mp4'))
    if all_mp4:
        return send_file(str(all_mp4[0]), mimetype='video/mp4', as_attachment=False)

    return jsonify({'error': 'Video not found'}), 404

@app.route('/api/download/<job_id>/<filename>')
def download_video(job_id, filename):
    """Download a rendered video file."""
    safe_job_id = os.path.basename(job_id)
    safe_filename = os.path.basename(filename)

    if not re.match(r'^[a-f0-9-]+$', safe_job_id):
        return jsonify({'error': 'Invalid job ID'}), 400

    job_dir = os.path.join(app.config['RENDER_DIR'], safe_job_id)
    output_files = list(Path(job_dir).rglob(f'*{safe_filename}*'))

    if not output_files:
        output_files = list(Path(job_dir).rglob('*.mp4'))

    if output_files:
        return send_file(
            str(output_files[0]),
            mimetype='video/mp4',
            as_attachment=True,
            download_name=f'manim_render_{job_id}.mp4'
        )

    return jsonify({'error': 'Video not found'}), 404

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get render history."""
    history = load_history()
    return jsonify(history)

@app.route('/api/history', methods=['DELETE'])
def clear_history():
    """Clear render history."""
    save_history([])
    return jsonify({'success': True})

@app.route('/api/history/<job_id>', methods=['DELETE'])
def delete_history_entry(job_id):
    """Delete a specific history entry."""
    history = load_history()
    history = [h for h in history if h['job_id'] != job_id]
    save_history(history)
    return jsonify({'success': True})

@app.route('/api/examples', methods=['GET'])
def get_examples():
    """Get example Manim code snippets."""
    examples = {
        "Circle": '''class Circle(Scene):
    def construct(self):
        circle = Circle()
        circle.set_fill(BLUE, opacity=0.5)
        self.play(Create(circle))
        self.wait()''',

        "Square to Circle": '''class SquareToCircle(Scene):
    def construct(self):
        circle = Circle()
        circle.set_fill(PINK, opacity=0.5)

        square = Square()
        square.set_fill(TEAL, opacity=0.5)

        self.play(Create(square))
        self.wait()
        self.play(Transform(square, circle))
        self.wait()''',

        "Sine Wave": '''class SineWave(Scene):
    def construct(self):
        axes = Axes(
            x_range=[0, 4 * PI, PI / 2],
            y_range=[-1.5, 1.5, 0.5],
            x_length=10,
            y_length=5,
        )

        sine_curve = axes.plot(
            lambda x: np.sin(x),
            color=BLUE,
        )

        self.play(Create(axes))
        self.play(Create(sine_curve))
        self.wait()''',

        "Dot Grid": '''class DotGrid(Scene):
    def construct(self):
        dots = VGroup()
        for x in range(-5, 6):
            for y in range(-3, 4):
                dot = Dot(point=[x, y, 0], radius=0.05)
                dot.set_color(interpolate_color(BLUE, RED, (x + 5) / 10))
                dots.add(dot)

        self.play(LaggedStart(*[FadeIn(d) for d in dots], lag_ratio=0.02))
        self.wait()''',

        "Math Formula": '''class MathFormula(Scene):
    def construct(self):
        formula = MathTex(
            r"e^{i\\\\pi} + 1 = 0"
        )
        formula.scale(2)

        self.play(Write(formula))
        self.wait(2)''',

        "Graph": '''class GraphExample(Scene):
    def construct(self):
        axes = Axes(
            x_range=[-3, 3, 1],
            y_range=[-1, 9, 2],
            x_length=6,
            y_length=5,
            axis_config={"include_numbers": True},
        )

        graph = axes.plot(lambda x: x**2, color=GREEN)
        label = axes.get_graph_label(graph, "x^2", x_val=2, direction=UR)

        self.play(Create(axes))
        self.play(Create(graph), Write(label))
        self.wait()''',

        "Bar Chart": '''class BarChartExample(Scene):
    def construct(self):
        bar_chart = BarChart(
            values=[5, 3, 4, 2, 1],
            bar_names=["A", "B", "C", "D", "E"],
            y_range=[0, 6, 1],
            y_length=5,
            x_length=8,
            x_axis_config={"font_size": 30},
        )

        self.play(Create(bar_chart))
        self.wait()'''
    }
    return jsonify(examples)

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status including Docker availability."""
    return jsonify({
        'docker_available': DOCKER_AVAILABLE,
        'python_version': sys.version,
        'manim_installed': _check_manim_installed(),
        'ffmpeg_installed': _check_ffmpeg_installed(),
    })

def _check_manim_installed():
    """Check if manim is installed."""
    try:
        import manim
        return True
    except ImportError:
        return False

def _check_ffmpeg_installed():
    """Check if ffmpeg is installed."""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        return result.returncode == 0
    except Exception:
        return False

# ============================================
# Cleanup old renders (run periodically)
# ============================================
def cleanup_old_renders():
    """Remove render directories older than 1 hour."""
    while True:
        time.sleep(3600)  # Run every hour
        try:
            render_dir = app.config['RENDER_DIR']
            now = time.time()
            for item in os.listdir(render_dir):
                item_path = os.path.join(render_dir, item)
                if os.path.isdir(item_path):
                    # Remove if older than 1 hour
                    if now - os.path.getmtime(item_path) > 3600:
                        shutil.rmtree(item_path, ignore_errors=True)
        except Exception:
            pass

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_old_renders, daemon=True)
cleanup_thread.start()

if __name__ == '__main__':
    print(f"🐳 Docker available: {DOCKER_AVAILABLE}")
    print(f"🎬 Manim IDE starting on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
