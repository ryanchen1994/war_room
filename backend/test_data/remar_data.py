from datetime import datetime
import json
import os

# 定義測試資料的檔案路徑
TEST_DATA_FILE = os.path.join(os.path.dirname(__file__), 'test_data.json')

def get_test_data():
    """獲取測試資料，並自動更新日期時間"""
    # 每次呼叫時重新讀取測試資料
    with open(TEST_DATA_FILE, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 檢查是否啟用測試資料
    if config.get('enable_test_data') != 'Y':
        return None
        
    data = config.get('test_data', {})
    current_time = datetime.now()
    
    if data["DAY_DATE"] == "AUTO_DATE":
        data["DAY_DATE"] = current_time.strftime('%Y-%m-%d')
    
    if data["UPDATE_DATE"] == "AUTO_TIMESTAMP":
        data["UPDATE_DATE"] = current_time.strftime('%Y-%m-%d %H:%M:%S')
    
    return data

def update_test_data(key, value):
    """更新測試資料中的特定欄位"""
    with open(TEST_DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    data[key] = value
    
    with open(TEST_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)