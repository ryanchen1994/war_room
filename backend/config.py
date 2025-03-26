# config.py
import os

class Config:
    # 資料庫連線設定：請替換成你實際的 MS SQL 連線資訊
    SQL_SERVER = os.environ.get('SQL_SERVER', '192.168.2.50')
    SQL_DATABASE = os.environ.get('SQL_DATABASE', 'PT')
    SQL_USERNAME = os.environ.get('SQL_USERNAME', 'selecter')
    SQL_PASSWORD = os.environ.get('SQL_PASSWORD', 'YourStrongPassword!')
    SQL_DRIVER = os.environ.get('SQL_DRIVER', 'ODBC Driver 17 for SQL Server')

    DEBUG = True
