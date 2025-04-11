# app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import pyodbc
from config import Config
import threading
import time
import os
from datetime import datetime, timedelta
import random
from test_data.remar_data import get_test_data
from flask_restx import Api, Resource, fields, Namespace
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config.from_object(Config)

# 設置 HTTP Basic Auth
auth = HTTPBasicAuth()

# 設置用户名和密碼 (實際應用中應存儲在數據庫或配置文件中)
users = {
    "admin": generate_password_hash("thm")
}

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username
    return None

# 設置 Swagger API 文檔
authorizations = {
    'basicAuth': {
        'type': 'basic',
        'in': 'header',
        'name': 'Authorization'
    }
}

api = Api(app, version='1.0', title='戰情室 API',
          description='建設公司戰情室 API 文檔',
          doc='/api/docs',
          authorizations=authorizations,
          security='basicAuth')

# 創建命名空間
ns_progress = api.namespace('progress', description='工程進度相關操作')
ns_performance = api.namespace('performance', description='績效指標相關操作')
ns_remar = api.namespace('remar', description='工程進度相關操作')

CORS(app, resources={
    r"/*": {
        "origins": "*",  # 允許所有來源
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# 修改 Socket.IO 設定
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='eventlet',
    ping_timeout=30,
    ping_interval=15,
    transports=['websocket', 'polling']
)

def get_db_connection():
    connection_string = (
        f"DRIVER={app.config.get('SQL_DRIVER')};"
        f"SERVER={app.config.get('SQL_SERVER')};"
        f"DATABASE={app.config.get('SQL_DATABASE')};"
        f"UID={app.config.get('SQL_USERNAME')};"
        f"PWD={app.config.get('SQL_PASSWORD')};"
    )

    conn = pyodbc.connect(connection_string, timeout=5)

    return conn


def load_sql(file_name):
    """ 讀取 sql 資料夾內的 SQL 檔案 """
    # 使用相對於 backend 資料夾的路徑
    sql_path = os.path.join(os.path.dirname(__file__), "sql", file_name)
    if not os.path.exists(sql_path):
        raise FileNotFoundError(f"SQL 檔案不存在: {sql_path}")
    with open(sql_path, "r", encoding="utf-8") as file:
        return file.read()

# 定義響應模型
progress_model = api.model('Progress', {
    'PROJM_NO': fields.String(description='專案編號'),
    'PROJM_SNAME': fields.String(description='專案名稱'),
    'PST': fields.String(description='計劃開始日期'),
    'PFI': fields.String(description='計劃完成日期'),
    'WORK_DAY': fields.Integer(description='計劃工作天數'),
    'ACTUAL_WORK_DAY': fields.Integer(description='實際工作天數'),
    'COP_NO': fields.String(description='公司編號')
})

remar_model = api.model('Remar', {
    'PROJM_NO': fields.String(description='專案編號'),
    'PROJM_NAME': fields.String(description='專案名稱'),
    'BUILD_REM202': fields.String(description='進度狀態'),
    'PST': fields.String(description='計劃開始日期'),
    'PFI': fields.String(description='計劃完成日期'),
    'AST': fields.String(description='實際開始日期'),
    'AFI': fields.String(description='實際完成日期'),
    'PWORK_DAY': fields.Integer(description='計劃工作天數'),
    'AWORK_DAY': fields.Integer(description='實際工作天數'),
    'PPER': fields.Float(description='計劃進度百分比'),
    'APER': fields.Float(description='實際進度百分比'),
    'PMDAY': fields.Integer(description='進度天數差異'),
    'REMARK_601': fields.String(description='備註'),
    'YPPER': fields.Float(description='昨日計劃進度百分比'),
    'DAY_DATE': fields.String(description='更新日期')
})

# 將原有路由轉換為 RESTx 資源
@ns_progress.route('')
class ProgressList(Resource):
    @ns_progress.doc('get_progress')
    @ns_progress.marshal_list_with(progress_model)
    @auth.login_required
    def get(self):
        """獲取所有工程進度數據"""
        try:
            print(f"目前工作目錄: {os.getcwd()}")  # 除錯訊息
            conn = get_db_connection()
            cursor = conn.cursor()

            sql_query = load_sql("progress.sql")  # 讀取 SQL 檔案
            cursor.execute(sql_query)

            rows = cursor.fetchall()
            data = [
                {
                    'PROJM_NO': row[0],
                    'PROJM_SNAME': row[1],
                    'PST': row[2],
                    'PFI': row[3],
                    'WORK_DAY': row[4],
                    'ACTUAL_WORK_DAY': row[5],
                    'COP_NO': row[6]
                } for row in rows
            ]

            cursor.close()
            conn.close()
            return data
        except Exception as e:
            ns_progress.abort(500, e.__doc__, status="無法獲取進度數據", statusCode="500")

@ns_progress.route('/mock')
class ProgressMock(Resource):
    @ns_progress.doc('get_progress_mock')
    @auth.login_required
    def get(self):
        """獲取模擬工程進度數據"""
        # 模擬專案進度數據
        projects = [
            {
                "PROJM_NO": "P2023001",
                "PROJM_SNAME": "台北商辦大樓",
                "PST": (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'),
                "PFI": (datetime.now() + timedelta(days=120)).strftime('%Y-%m-%d'),
                "WORK_DAY": 180,
                "ACTUAL_WORK_DAY": 60,
                "STATUS": "active"
            },
            {
                "PROJM_NO": "P2023002",
                "PROJM_SNAME": "新竹科技園區",
                "PST": (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),
                "PFI": (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d'),
                "WORK_DAY": 180,
                "ACTUAL_WORK_DAY": 90,
                "STATUS": "active"
            },
            {
                "PROJM_NO": "P2023003",
                "PROJM_SNAME": "台中住宅社區",
                "PST": (datetime.now() - timedelta(days=150)).strftime('%Y-%m-%d'),
                "PFI": (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                "WORK_DAY": 120,
                "ACTUAL_WORK_DAY": 120,
                "STATUS": "completed"
            },
            {
                "PROJM_NO": "P2023004",
                "PROJM_SNAME": "高雄港口擴建",
                "PST": (datetime.now() - timedelta(days=45)).strftime('%Y-%m-%d'),
                "PFI": (datetime.now() + timedelta(days=135)).strftime('%Y-%m-%d'),
                "WORK_DAY": 180,
                "ACTUAL_WORK_DAY": 45,
                "STATUS": "active"
            },
            {
                "PROJM_NO": "P2023005",
                "PROJM_SNAME": "花蓮觀光飯店",
                "PST": (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                "PFI": (datetime.now() + timedelta(days=210)).strftime('%Y-%m-%d'),
                "WORK_DAY": 180,
                "ACTUAL_WORK_DAY": 0,
                "STATUS": "planned"
            }
        ]
        
        return projects

@ns_performance.route('')
class Performance(Resource):
    @ns_performance.doc('get_performance')
    @auth.login_required
    def get(self):
        """獲取績效指標數據"""
        try:
            # 模擬績效指標數據
            kpi_data = {
                "onTimeProjects": 85,
                "budgetCompliance": 92,
                "qualityScore": 4.7,
                "activeProjects": 12
            }
            
            # 模擬月度數據
            monthly_data = [
                {"month": "一月", "completed": 2, "delayed": 1, "budget": 85},
                {"month": "二月", "completed": 3, "delayed": 0, "budget": 95},
                {"month": "三月", "completed": 1, "delayed": 1, "budget": 90},
                {"month": "四月", "completed": 4, "delayed": 1, "budget": 88},
                {"month": "五月", "completed": 2, "delayed": 0, "budget": 92},
                {"month": "六月", "completed": 3, "delayed": 2, "budget": 85}
            ]
            
            return {
                "kpi": kpi_data,
                "monthly": monthly_data
            }
        except Exception as e:
            ns_performance.abort(500, e.__doc__, status="無法獲取績效數據", statusCode="500")

@ns_remar.route('')
class RemarData(Resource):
    @ns_remar.doc('get_remar_data')
    @ns_remar.marshal_list_with(remar_model)
    @auth.login_required
    def get(self):
        """取得工程日報數據"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # 讀取 SQL 檔案
            sql_query = load_sql("remar_data.sql")
            cursor.execute(sql_query)

            # 獲取列名
            columns = [column[0] for column in cursor.description]
            
            # 將查詢結果轉換為字典列表
            rows = cursor.fetchall()
            data = []
            for row in rows:
                item = {}
                for i, column in enumerate(columns):
                    item[column] = row[i]
                data.append(item)

            cursor.close()
            conn.close()
            
            # 檢查並加入測試資料
            test_data = get_test_data()
            if test_data:
                data.append(test_data)

            return data
        except Exception as e:
            print(f"獲取 Remar 數據錯誤: {str(e)}")
            ns_remar.abort(500, e.__doc__, status="無法獲取 Remar 數據", statusCode="500")

# 保留原有的 Socket.IO 功能
def background_thread():
    """
    背景執行緒範例，每10秒發送一次更新訊息，可依需求改為讀取最新資料並傳送
    """
    while True:
        socketio.sleep(10)  # 用 socketio.sleep() 替代 time.sleep()
        socketio.emit('update', {'message': '最新進度更新！'})


@socketio.on('connect')
def handle_connect():
    print('客户端已連線')


# 為了向後兼容，保留原有的路由
@app.route('/api/progress', methods=['GET'])
@auth.login_required
def get_progress():
    resource = ProgressList()
    return jsonify(resource.get())

@app.route('/api/progress_mock', methods=['GET'])
@auth.login_required
def get_progress_data_mock():
    resource = ProgressMock()
    return jsonify(resource.get())

@app.route('/api/performance', methods=['GET'])
@auth.login_required
def get_performance_data():
    resource = Performance()
    return jsonify(resource.get())

@app.route('/api/remar', methods=['GET'])
@auth.login_required
def get_remar_data():
    resource = RemarData()
    return jsonify(resource.get())

if __name__ == '__main__':
    # 啟動背景執行緒
    thread = threading.Thread(target=background_thread)
    thread.daemon = True
    thread.start()
    
    app.run(host='0.0.0.0', port=5000)