import os
import sys

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import socketio
from app.core.pipeline_manager import PipelineManager

print('[RUN] 创建Flask应用...', flush=True)
app = create_app()
print('[RUN] 创建PipelineManager...', flush=True)
manager = PipelineManager()
print(f'[RUN] PipelineManager实例ID: {id(manager)}', flush=True)
print('[RUN] 初始化PipelineManager...', flush=True)
manager.init_app(app, socketio)
print('[RUN] 初始化完成', flush=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
