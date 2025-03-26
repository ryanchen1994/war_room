# app.py
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import pyodbc
from config import Config
import threading
import time
import os
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

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


@app.route('/api/progress', methods=['GET'])
def get_progress():
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
    except Exception as e:
        data = {'error': str(e)}

    return jsonify(data)


@app.route('/api/mapdata', methods=['GET'])
def get_map_data():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        sql_query = load_sql("mapdata.sql")  # 讀取 SQL 檔案
        cursor.execute(sql_query)

        rows = cursor.fetchall()
        data = [
            {
                'PROJM_NO': row[0],
                'PROJM_SNAME': row[1],
                'PST': row[2],
                'PFI': row[3],
                'WORK_DAY': row[4],
                'ACTUAL_WORK_DAY': row[5]
            } for row in rows
        ]

        cursor.close()
        conn.close()
    except Exception as e:
        data = {'error': str(e)}

    return jsonify(data)


# 修改第二個 /api/progress 路由名稱，避免衝突
@app.route('/api/progress_mock', methods=['GET'])
def get_progress_data_mock():
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
    
    return jsonify(projects)


@app.route('/api/performance', methods=['GET'])
def get_performance_data():
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
        
        # 實際應用中，這些數據應該從資料庫獲取
        # conn = get_db_connection()
        # cursor = conn.cursor()
        # sql_query = load_sql("performance.sql")
        # cursor.execute(sql_query)
        # rows = cursor.fetchall()
        # 處理資料庫返回的數據...
        
        return jsonify({
            "kpi": kpi_data,
            "monthly": monthly_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/weekly-report', methods=['GET'])
def get_weekly_report():
    try:
        # 這裡應該從資料庫獲取周報數據
        # 目前使用模擬數據
        today = datetime.now()
        
        projects = [
            {
                "id": "P001",
                "name": "台北商辦大樓",
                "progress": 65,
                "startDate": "20230315",
                "endDate": "20240520",
                "actualDays": 180,
                "totalDays": 280,
                "workItems": [
                    { 
                        "name": "基礎工程", 
                        "plannedStart": "20230315", 
                        "plannedEnd": "20230615", 
                        "actualStart": "20230320", 
                        "actualEnd": "20230620", 
                        "progress": 100 
                    },
                    { 
                        "name": "結構工程", 
                        "plannedStart": "20230601", 
                        "plannedEnd": "20231015", 
                        "actualStart": "20230610", 
                        "actualEnd": "20231020", 
                        "progress": 100 
                    },
                    { 
                        "name": "機電工程", 
                        "plannedStart": "20230815", 
                        "plannedEnd": "20240215", 
                        "actualStart": "20230825", 
                        "actualEnd": None, 
                        "progress": 70 
                    },
                    { 
                        "name": "裝修工程", 
                        "plannedStart": "20231115", 
                        "plannedEnd": "20240415", 
                        "actualStart": "20231125", 
                        "actualEnd": None, 
                        "progress": 40 
                    },
                    { 
                        "name": "驗收", 
                        "plannedStart": "20240415", 
                        "plannedEnd": "20240520", 
                        "actualStart": None, 
                        "actualEnd": None, 
                        "progress": 0 
                    }
                ],
                "operationItems": [
                    { "name": "鋼筋綁紮", "unit": "噸", "plannedQuantity": 450, "completedQuantity": 450, "completionRate": 100, "notes": "已完成" },
                    { "name": "模板組立", "unit": "㎡", "plannedQuantity": 12000, "completedQuantity": 12000, "completionRate": 100, "notes": "已完成" },
                    { "name": "混凝土澆置", "unit": "㎥", "plannedQuantity": 8500, "completedQuantity": 8500, "completionRate": 100, "notes": "已完成" },
                    { "name": "機電管線", "unit": "式", "plannedQuantity": 1, "completedQuantity": 0.7, "completionRate": 70, "notes": "進行中" },
                    { "name": "內部裝修", "unit": "㎡", "plannedQuantity": 9500, "completedQuantity": 3800, "completionRate": 40, "notes": "進行中" }
                ]
            },
            {
                "id": "P002",
                "name": "新竹科技園區",
                "progress": 80,
                "startDate": "20230110",
                "endDate": "20240310",
                "actualDays": 220,
                "totalDays": 270,
                "workItems": [
                    { 
                        "name": "基礎工程", 
                        "plannedStart": "20230110", 
                        "plannedEnd": "20230410", 
                        "actualStart": "20230115", 
                        "actualEnd": "20230415", 
                        "progress": 100 
                    },
                    { 
                        "name": "結構工程", 
                        "plannedStart": "20230401", 
                        "plannedEnd": "20230815", 
                        "actualStart": "20230405", 
                        "actualEnd": "20230820", 
                        "progress": 100 
                    },
                    { 
                        "name": "機電工程", 
                        "plannedStart": "20230715", 
                        "plannedEnd": "20231215", 
                        "actualStart": "20230720", 
                        "actualEnd": "20231220", 
                        "progress": 100 
                    },
                    { 
                        "name": "裝修工程", 
                        "plannedStart": "20231015", 
                        "plannedEnd": "20240215", 
                        "actualStart": "20231020", 
                        "actualEnd": None, 
                        "progress": 75 
                    },
                    { 
                        "name": "驗收", 
                        "plannedStart": "20240215", 
                        "plannedEnd": "20240310", 
                        "actualStart": None, 
                        "actualEnd": None, 
                        "progress": 0 
                    }
                ],
                "operationItems": [
                    { "name": "鋼筋綁紮", "unit": "噸", "plannedQuantity": 380, "completedQuantity": 380, "completionRate": 100, "notes": "已完成" },
                    { "name": "模板組立", "unit": "㎡", "plannedQuantity": 10500, "completedQuantity": 10500, "completionRate": 100, "notes": "已完成" },
                    { "name": "混凝土澆置", "unit": "㎥", "plannedQuantity": 7200, "completedQuantity": 7200, "completionRate": 100, "notes": "已完成" },
                    { "name": "機電管線", "unit": "式", "plannedQuantity": 1, "completedQuantity": 1, "completionRate": 100, "notes": "已完成" },
                    { "name": "內部裝修", "unit": "㎡", "plannedQuantity": 8200, "completedQuantity": 6150, "completionRate": 75, "notes": "進行中" }
                ]
            }
        ]
        
        return jsonify(projects)
    except Exception as e:
        print(f"獲取周報數據錯誤: {str(e)}")
        return jsonify([])


def background_thread():
    """
    背景執行緒範例，每10秒發送一次更新訊息，可依需求改為讀取最新資料並傳送
    """
    while True:
        socketio.sleep(10)  # 用 socketio.sleep() 替代 time.sleep()
        socketio.emit('update', {'message': '最新進度更新！'})


@socketio.on('connect')
def handle_connect():
    print('客戶端已連線')


if __name__ == '__main__':
    # 啟動背景執行緒
    thread = threading.Thread(target=background_thread)
    thread.daemon = True
    thread.start()
    # socketio.run(app, host='0.0.0.0', port=5000, debug=True) 可能會觸發 Flask 的 「自動重新載入」(auto-reload) 機制，但有時會導致卡住。
    socketio.run(app, host="0.0.0.0", port=5000, debug=False, use_reloader=False)

