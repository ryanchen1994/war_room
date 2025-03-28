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
from test_data.remar_data import get_test_data

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


@app.route('/api/remar-data', methods=['GET'])
def get_remar_data():
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


        return jsonify(data)
    except Exception as e:
        print(f"獲取 Remar 數據錯誤: {str(e)}")
        return jsonify({"error": str(e)}), 500


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

