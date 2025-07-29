#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
測試自動重啟功能的簡單腳本
"""

import subprocess
import sys

def test_auto_restart():
    """測試自動重啟功能"""
    print("🧪 測試自動重啟功能...")
    
    # 測試參數
    csv_file = "keywords.csv"
    max_pages = "2"  # 使用較小的頁數進行測試
    restart_interval = "1"  # 1分鐘間隔用於測試
    
    cmd = ["python3", "auto_restart_search.py", csv_file, max_pages, restart_interval]
    
    print(f"執行命令: {' '.join(cmd)}")
    print("注意：這是測試模式，將在1分鐘後重啟")
    print("按 Ctrl+C 可以停止測試")
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n測試被用戶中斷")
    except Exception as e:
        print(f"測試過程中發生錯誤: {e}")

if __name__ == "__main__":
    test_auto_restart()