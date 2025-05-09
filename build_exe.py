#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
打包腳本 - 將GSC應用程序打包為Windows可執行文件

這個腳本使用PyInstaller將Python應用程序打包為獨立的Windows可執行文件(.exe)，
使用戶無需安裝Python環境即可運行程序。

使用方法:
    1. 安裝必要的依賴: pip install pyinstaller
    2. 運行此腳本: python build_exe.py
    3. 打包完成後，可執行文件將位於dist目錄中
"""

import os
import sys
import shutil
import subprocess
import platform

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
    """檢查並安裝必要的依賴"""
    required_packages = ['pyinstaller', 'selenium']
    
    print_colored("正在檢查必要的依賴...", Colors.BLUE)
    
    for package in required_packages:
        try:
            __import__(package)
            print_colored(f"✓ {package} 已安裝", Colors.GREEN)
        except ImportError:
            print_colored(f"! {package} 未安裝，正在安裝...", Colors.YELLOW)
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print_colored(f"✓ {package} 安裝成功", Colors.GREEN)

def build_executable():
    """使用PyInstaller打包應用程序"""
    print_colored("\n開始打包應用程序...", Colors.BLUE)
    
    # 檢查操作系統
    if platform.system() != "Windows":
        print_colored("警告: 當前不是Windows系統，生成的可執行文件可能無法在Windows上運行。", Colors.YELLOW)
        response = input("是否繼續? (y/n): ")
        if response.lower() != 'y':
            print_colored("打包已取消", Colors.RED)
            return
    
    # 清理之前的構建文件
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print_colored(f"✓ 已清理 {dir_name} 目錄", Colors.GREEN)
    
    # 創建資源目錄
    if not os.path.exists('resources'):
        os.makedirs('resources')
        print_colored("✓ 已創建resources目錄", Colors.GREEN)
    
    # 複製必要的資源文件
    resource_files = ['proxies.txt', 'keywords.csv']
    for file in resource_files:
        if os.path.exists(file):
            shutil.copy(file, os.path.join('resources', file))
            print_colored(f"✓ 已複製 {file} 到resources目錄", Colors.GREEN)
        else:
            print_colored(f"! 警告: {file} 不存在，將創建空文件", Colors.YELLOW)
            with open(os.path.join('resources', file), 'w', encoding='utf-8') as f:
                if file == 'proxies.txt':
                    f.write("# 在此文件中添加代理，每行一個，格式為: ip:port\n")
                elif file == 'keywords.csv':
                    f.write("# 搜索詞,目標關鍵詞\n# 例如:\n# Python 教學,Django\n# AI 工具,ChatGPT\n")
    
    # 創建主程序入口點
    with open('gsc_app.py', 'w', encoding='utf-8') as f:
        f.write('''
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GSC應用程序入口點

這個文件是打包後應用程序的主入口點，它提供了一個簡單的命令行界面，
允許用戶選擇運行單個關鍵詞搜索或從CSV文件批量搜索。
"""

import os
import sys
import time

# 確保資源路徑正確
def get_resource_path(relative_path):
    """獲取資源文件的絕對路徑，適用於PyInstaller打包後的環境"""
    if getattr(sys, 'frozen', False):
        # 如果是打包後的環境
        base_path = sys._MEIPASS
    else:
        # 如果是開發環境
        base_path = os.path.abspath("resources")
    
    return os.path.join(base_path, relative_path)

# 修改工作目錄
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 導入主要模塊
from main import main as single_search
from google_keyword_search_csv import main as csv_search

def clear_screen():
    """清除屏幕"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """打印應用程序標題"""
    clear_screen()
    print("="*60)
    print("\033[1m\033[94m  Google搜索關鍵詞工具  \033[0m")
    print("="*60)
    print("這個工具可以幫助您在Google上搜索特定關鍵詞，並檢查目標關鍵詞是否出現在結果中。")
    print("\n")

def main_menu():
    """顯示主菜單並處理用戶選擇"""
    while True:
        print_header()
        print("請選擇操作:")
        print("  1. 單個關鍵詞搜索")
        print("  2. 從CSV文件批量搜索")
        print("  3. 查看說明")
        print("  4. 退出程序")
        print("\n")
        
        choice = input("請輸入選項 (1-4): ")
        
        if choice == "1":
            run_single_search()
        elif choice == "2":
            run_csv_search()
        elif choice == "3":
            show_help()
        elif choice == "4":
            print("\n感謝使用，再見！")
            time.sleep(1)
            sys.exit(0)
        else:
            print("\n無效的選項，請重新選擇。")
            time.sleep(1)

def run_single_search():
    """運行單個關鍵詞搜索"""
    clear_screen()
    print("="*60)
    print("\033[1m\033[94m  單個關鍵詞搜索  \033[0m")
    print("="*60)
    
    # 準備命令行參數
    search_query = input("\n請輸入搜索詞: ")
    if not search_query.strip():
        print("\n搜索詞不能為空！按任意鍵返回主菜單...")
        input()
        return
    
    target_keywords = input("\n請輸入目標關鍵詞 (多個關鍵詞用逗號分隔): ")
    if not target_keywords.strip():
        print("\n目標關鍵詞不能為空！按任意鍵返回主菜單...")
        input()
        return
    
    target_keywords_list = [k.strip() for k in target_keywords.split(",")]
    
    max_pages = input("\n請輸入最大搜索頁數 (默認為5): ")
    max_pages = int(max_pages) if max_pages.strip().isdigit() else 5
    
    # 檢查代理文件
    proxy_file = "proxies.txt"
    proxy_path = get_resource_path(proxy_file)
    
    # 構建參數
    sys.argv = [
        "main.py",
        "--search-query", search_query,
        "--target-keywords"] + target_keywords_list + [
        "--max-pages", str(max_pages)
    ]
    
    # 如果代理文件存在且不為空，添加代理參數
    if os.path.exists(proxy_path) and os.path.getsize(proxy_path) > 0:
        use_proxy = input("\n是否使用代理? (y/n, 默認n): ")
        if use_proxy.lower() == 'y':
            sys.argv.extend(["--proxy-file", proxy_path])
    
    print("\n開始搜索...\n")
    try:
        single_search()
    except Exception as e:
        print(f"\n執行過程中發生錯誤: {str(e)}")
    
    print("\n搜索完成！按任意鍵返回主菜單...")
    input()

def run_csv_search():
    """運行CSV批量搜索"""
    clear_screen()
    print("="*60)
    print("\033[1m\033[94m  CSV批量搜索  \033[0m")
    print("="*60)
    
    # 檢查CSV文件
    csv_file = "keywords.csv"
    csv_path = get_resource_path(csv_file)
    
    if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:
        print(f"\n錯誤: CSV文件 {csv_path} 不存在或為空！")
        print("\n請確保CSV文件格式正確，每行包含'搜索詞,目標關鍵詞'")
        print("例如:\nPython 教學,Django\nAI 工具,ChatGPT")
        print("\n按任意鍵返回主菜單...")
        input()
        return
    
    max_pages = input("\n請輸入最大搜索頁數 (默認為5): ")
    max_pages = int(max_pages) if max_pages.strip().isdigit() else 5
    
    # 檢查代理文件
    proxy_file = "proxies.txt"
    proxy_path = get_resource_path(proxy_file)
    
    # 構建參數
    sys.argv = [
        "google_keyword_search_csv.py",
        "--csv-file", csv_path,
        "--max-pages", str(max_pages)
    ]
    
    # 如果代理文件存在且不為空，添加代理參數
    if os.path.exists(proxy_path) and os.path.getsize(proxy_path) > 0:
        use_proxy = input("\n是否使用代理? (y/n, 默認n): ")
        if use_proxy.lower() == 'y':
            sys.argv.extend(["--proxy-file", proxy_path])
    
    print("\n開始批量搜索...\n")
    try:
        csv_search()
    except Exception as e:
        print(f"\n執行過程中發生錯誤: {str(e)}")
    
    print("\n搜索完成！按任意鍵返回主菜單...")
    input()

def show_help():
    """顯示幫助信息"""
    clear_screen()
    print("="*60)
    print("\033[1m\033[94m  使用說明  \033[0m")
    print("="*60)
    print("\n這個工具可以幫助您在Google上搜索特定關鍵詞，並檢查目標關鍵詞是否出現在結果中。")
    print("\n功能說明:")
    print("  1. 單個關鍵詞搜索: 手動輸入搜索詞和目標關鍵詞進行搜索")
    print("  2. CSV批量搜索: 從CSV文件中讀取多組搜索詞和目標關鍵詞進行批量搜索")
    print("\nCSV文件格式:")
    print("  每行一組搜索詞和目標關鍵詞，用逗號分隔")
    print("  例如:\n  Python 教學,Django\n  AI 工具,ChatGPT")
    print("\n代理設置:")
    print("  在proxies.txt文件中添加代理，每行一個，格式為: ip:port")
    print("\n注意事項:")
    print("  1. 搜索過程中請勿關閉瀏覽器窗口")
    print("  2. 如果遇到Google驗證碼，請手動完成驗證")
    print("  3. 使用代理可以減少被Google封鎖的可能性")
    print("\n按任意鍵返回主菜單...")
    input()

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n程序被用戶中斷，正在退出...")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n程序發生錯誤: {str(e)}")
        print("按任意鍵退出...")
        input()
        sys.exit(1)
''')
    
    # 使用PyInstaller打包
    print_colored("\n正在使用PyInstaller打包應用程序...", Colors.BLUE)
    
    # 構建PyInstaller命令
    pyinstaller_cmd = [
        'pyinstaller',
        '--name=GSC搜索工具',
        '--onefile',  # 生成單個可執行文件
        '--windowed',  # 使用窗口模式（不顯示控制台）
        '--add-data=resources/proxies.txt;resources',  # 添加代理文件
        '--add-data=resources/keywords.csv;resources',  # 添加關鍵詞文件
        '--icon=NONE',  # 可以替換為實際圖標文件
        '--clean',  # 清理臨時文件
        'gsc_app.py'  # 主程序入口點
    ]
    
    # 根據操作系統調整路徑分隔符
    if platform.system() != "Windows":
        # 在非Windows系統上，路徑分隔符使用冒號
        pyinstaller_cmd[5] = '--add-data=resources/proxies.txt:resources'
        pyinstaller_cmd[6] = '--add-data=resources/keywords.csv:resources'
    
    try:
        subprocess.check_call(pyinstaller_cmd)
        print_colored("\n✓ 打包成功！", Colors.GREEN)
        print_colored(f"\n可執行文件位於: {os.path.abspath('dist')} 目錄", Colors.GREEN)
        print_colored("\n注意事項:", Colors.YELLOW)
        print_colored("1. 如果在Windows系統上運行，請確保已安裝Chrome瀏覽器", Colors.YELLOW)
        print_colored("2. 首次運行時，程序會自動下載ChromeDriver", Colors.YELLOW)
        print_colored("3. 如需使用代理，請在應用程序中選擇使用代理選項", Colors.YELLOW)
    except subprocess.CalledProcessError as e:
        print_colored(f"\n❌ 打包失敗: {str(e)}", Colors.RED)
        print_colored("請確保已正確安裝PyInstaller和所有依賴", Colors.RED)

def main():
    """主函數"""
    print_colored("\n===== GSC應用程序打包工具 =====\n", Colors.BLUE)
    
    # 檢查依賴
    check_dependencies()
    
    # 打包可執行文件
    build_executable()
    
    print_colored("\n打包過程完成！", Colors.GREEN)

if __name__ == "__main__":
    main()