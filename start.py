#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GSC關鍵字搜索工具啟動腳本

這個腳本提供了一個簡單的界面來啟動GSC關鍵字搜索工具。
用戶可以選擇運行單個關鍵詞搜索或CSV批量搜索。
"""

import os
import sys
import subprocess

# 定義顏色代碼（用於終端輸出）
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'

def print_colored(text, color):
    """打印彩色文本"""
    print(f"{color}{text}{Colors.ENDC}")

def check_dependencies():
    """檢查必要的依賴是否已安裝"""
    try:
        import selenium
        print_colored("✓ 已安裝 Selenium", Colors.GREEN)
        return True
    except ImportError:
        print_colored("❌ 未安裝 Selenium", Colors.RED)
        install = input("是否安裝必要的依賴？(y/n): ")
        if install.lower() == 'y':
            print_colored("正在安裝依賴...", Colors.BLUE)
            subprocess.run(["python3", "-m", "pip", "install", "-r", "requirements.txt"])
            print_colored("✓ 依賴安裝完成", Colors.GREEN)
            return True
        else:
            return False

def run_single_search():
    """運行單個關鍵詞搜索"""
    print_colored("\n=== 單個關鍵詞搜索 ===", Colors.BLUE)
    search_query = input("請輸入搜索詞: ")
    target_keywords = input("請輸入目標關鍵詞(多個關鍵詞用空格分隔): ").split()
    max_pages = input("請輸入最大搜索頁數(默認10): ") or "10"
    
    use_proxy = input("是否使用代理？(y/n, 默認n): ").lower() == 'y'
    proxy_args = []
    if use_proxy:
        proxy_file = input("請輸入代理文件路徑(默認resources/proxies.txt): ") or "resources/proxies.txt"
        proxy_args = ["--proxy-file", proxy_file]
    
    cmd = ["python3", "main.py", search_query] + target_keywords + ["--max-pages", max_pages] + proxy_args
    print_colored(f"\n執行命令: {' '.join(cmd)}", Colors.BLUE)
    subprocess.run(cmd)

def run_csv_search():
    """運行CSV批量搜索"""
    print_colored("\n=== CSV批量搜索 ===", Colors.BLUE)
    csv_file = input("請輸入CSV文件路徑(默認keywords.csv): ") or "keywords.csv"
    max_pages = input("請輸入最大搜索頁數(默認10): ") or "10"
    
    use_proxy = input("是否使用代理？(y/n, 默認n): ").lower() == 'y'
    proxy_args = []
    if use_proxy:
        proxy_file = input("請輸入代理文件路徑(默認resources/proxies.txt): ") or "resources/proxies.txt"
        proxy_args = ["--proxy-file", proxy_file]
    
    cmd = ["python3", "google_keyword_search_csv.py", csv_file, max_pages] + proxy_args
    print_colored(f"\n執行命令: {' '.join(cmd)}", Colors.BLUE)
    subprocess.run(cmd)

def run_auto_restart_csv_search():
    """運行自動重啟CSV批量搜索"""
    print_colored("\n=== 自動重啟CSV批量搜索 ===", Colors.BLUE)
    csv_file = input("請輸入CSV文件路徑(默認keywords.csv): ") or "keywords.csv"
    max_pages = input("請輸入最大搜索頁數(默認10): ") or "10"
    
    # 新增自動重啟間隔設定
    restart_interval = input("請輸入自動重啟間隔時間(分鐘，默認60): ") or "60"
    try:
        restart_minutes = int(restart_interval)
        if restart_minutes <= 0:
            print_colored("重啟間隔必須大於0，使用默認值60分鐘", Colors.YELLOW)
            restart_minutes = 60
    except ValueError:
        print_colored("無效的時間格式，使用默認值60分鐘", Colors.YELLOW)
        restart_minutes = 60
    
    use_proxy = input("是否使用代理？(y/n, 默認n): ").lower() == 'y'
    proxy_args = []
    if use_proxy:
        proxy_file = input("請輸入代理文件路徑(默認resources/proxies.txt): ") or "resources/proxies.txt"
        proxy_args = ["--proxy-file", proxy_file]
    
    cmd = ["python3", "auto_restart_search.py", csv_file, max_pages, str(restart_minutes)] + proxy_args
    print_colored(f"\n執行命令: {' '.join(cmd)}", Colors.BLUE)
    print_colored(f"將每隔 {restart_minutes} 分鐘自動重新執行所有關鍵字搜索", Colors.GREEN)
    print_colored("按 Ctrl+C 可以停止自動重啟功能", Colors.YELLOW)
    subprocess.run(cmd)

def show_help():
    """顯示幫助信息"""
    print_colored("\n=== GSC關鍵字搜索工具使用說明 ===", Colors.BLUE)
    print("\n1. 單個關鍵詞搜索")
    print("   - 手動輸入搜索詞和目標關鍵詞進行搜索")
    print("   - 可以設置最大搜索頁數和是否使用代理")
    print("\n2. CSV批量搜索")
    print("   - 從CSV文件中讀取多組搜索詞和目標關鍵詞進行批量搜索")
    print("   - CSV格式：每行包含'搜索詞,目標關鍵詞'")
    print("   - 例如：\n     Python 教學,Django\n     AI 工具,ChatGPT")
    print("\n3. 自動重啟CSV批量搜索")
    print("   - 與CSV批量搜索相同，但會在完成所有關鍵字後自動重啟")
    print("   - 可以設置重啟間隔時間（分鐘）")
    print("   - 適合需要持續監控關鍵字排名的場景")
    print("   - 按 Ctrl+C 可以停止自動重啟功能")
    print("\n4. 代理設置")
    print("   - 代理文件格式為每行一個代理，格式為ip:port")
    print("   - 使用代理可以減少被Google封鎖的可能性")
    print("\n5. 注意事項")
    print("   - 首次運行時，程序會自動下載ChromeDriver")
    print("   - 搜索過程中請勿關閉瀏覽器窗口")
    print("   - 如果遇到Google驗證碼，請手動完成驗證")
    print("   - 確保系統上已安裝Chrome瀏覽器")
    print("   - 自動重啟功能會持續運行，建議在穩定的網絡環境下使用")

def main():
    """主函數"""
    print_colored("\n歡迎使用GSC關鍵字搜索工具！", Colors.GREEN)
    
    # 檢查依賴
    if not check_dependencies():
        print_colored("請先安裝必要的依賴再運行程序。", Colors.RED)
        return
    
    while True:
        print_colored("\n請選擇功能：", Colors.BLUE)
        print("1. 單個關鍵詞搜索")
        print("2. CSV批量搜索")
        print("3. 自動重啟CSV批量搜索")
        print("4. 查看說明")
        print("0. 退出程序")
        
        choice = input("\n請輸入選項(0-4): ")
        
        if choice == '1':
            run_single_search()
        elif choice == '2':
            run_csv_search()
        elif choice == '3':
            run_auto_restart_csv_search()
        elif choice == '4':
            show_help()
        elif choice == '0':
            print_colored("\n感謝使用GSC關鍵字搜索工具！再見！", Colors.GREEN)
            break
        else:
            print_colored("\n無效的選項，請重新選擇。", Colors.RED)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_colored("\n程序被用戶中斷。", Colors.YELLOW)
        sys.exit(0)
    except Exception as e:
        print_colored(f"\n執行過程中發生意外錯誤: {str(e)}", Colors.RED)
        sys.exit(1)