#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自動重啟關鍵字搜索工具

這個腳本會自動重複執行CSV批量關鍵字搜索，在完成所有關鍵字搜索後等待指定時間，
然後自動重新開始搜索。適合需要持續監控關鍵字排名的場景。

使用方法:
    python auto_restart_search.py [CSV檔案路徑] [最大頁數] [重啟間隔分鐘] [--proxy-file PROXY_FILE]

例如:
    python auto_restart_search.py keywords.csv 10 60
    python auto_restart_search.py keywords.csv 10 30 --proxy-file proxies.txt
"""

import sys
import time
import datetime
import logging
import argparse
import subprocess
import signal
from pathlib import Path

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 全局變量用於優雅退出
should_stop = False

def signal_handler(signum, frame):
    """處理中斷信號"""
    global should_stop
    should_stop = True
    print("\n\n⚠️ 收到中斷信號，正在優雅退出...")
    print("如果當前正在執行搜索，將在本輪搜索完成後停止。")
    logging.info("收到中斷信號，設置停止標誌")

def parse_arguments():
    """解析命令行參數"""
    parser = argparse.ArgumentParser(description="自動重啟關鍵字搜索工具")
    parser.add_argument("csv_file", help="CSV關鍵字文件路徑")
    parser.add_argument("max_pages", type=int, help="最大搜索頁數")
    parser.add_argument("restart_interval", type=int, help="重啟間隔時間（分鐘）")
    parser.add_argument("--proxy-file", help="代理文件路徑")
    
    return parser.parse_args()

def run_csv_search(csv_file, max_pages, proxy_file=None):
    """執行一次CSV批量搜索"""
    cmd = ["python3", "google_keyword_search_csv.py", csv_file, str(max_pages)]
    
    if proxy_file:
        cmd.extend(["--proxy-file", proxy_file])
    
    logging.info(f"執行搜索命令: {' '.join(cmd)}")
    print(f"\n🔍 執行搜索命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=False)
        if result.returncode == 0:
            logging.info("搜索執行完成")
            print("✅ 搜索執行完成")
            return True
        else:
            logging.warning(f"搜索執行完成，但返回碼為: {result.returncode}")
            print(f"⚠️ 搜索執行完成，但返回碼為: {result.returncode}")
            return True  # 即使有警告也繼續
    except subprocess.CalledProcessError as e:
        logging.error(f"搜索執行失敗: {e}")
        print(f"❌ 搜索執行失敗: {e}")
        return False
    except KeyboardInterrupt:
        logging.info("搜索被用戶中斷")
        print("\n⚠️ 搜索被用戶中斷")
        return False

def wait_with_countdown(minutes):
    """帶倒計時的等待函數"""
    total_seconds = minutes * 60
    
    print(f"\n⏰ 等待 {minutes} 分鐘後重新開始搜索...")
    print("按 Ctrl+C 可以停止自動重啟功能")
    
    try:
        for remaining in range(total_seconds, 0, -1):
            if should_stop:
                return False
                
            mins, secs = divmod(remaining, 60)
            hours, mins = divmod(mins, 60)
            
            if hours > 0:
                time_str = f"{hours:02d}:{mins:02d}:{secs:02d}"
            else:
                time_str = f"{mins:02d}:{secs:02d}"
            
            print(f"\r⏳ 剩餘時間: {time_str}", end="", flush=True)
            time.sleep(1)
        
        print("\n")
        return True
        
    except KeyboardInterrupt:
        print("\n⚠️ 等待被中斷")
        return False

def main():
    """主函數"""
    global should_stop
    
    # 註冊信號處理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 解析命令行參數
    args = parse_arguments()
    
    # 驗證CSV文件是否存在
    csv_path = Path(args.csv_file)
    if not csv_path.exists():
        print(f"❌ CSV文件不存在: {args.csv_file}")
        logging.error(f"CSV文件不存在: {args.csv_file}")
        sys.exit(1)
    
    # 驗證代理文件（如果指定）
    if args.proxy_file:
        proxy_path = Path(args.proxy_file)
        if not proxy_path.exists():
            print(f"❌ 代理文件不存在: {args.proxy_file}")
            logging.error(f"代理文件不存在: {args.proxy_file}")
            sys.exit(1)
    
    print("\n" + "="*60)
    print("🚀 自動重啟關鍵字搜索工具啟動")
    print("="*60)
    print(f"📁 CSV文件: {args.csv_file}")
    print(f"📄 最大搜索頁數: {args.max_pages}")
    print(f"⏰ 重啟間隔: {args.restart_interval} 分鐘")
    if args.proxy_file:
        print(f"🌐 代理文件: {args.proxy_file}")
    else:
        print("🌐 代理: 未使用")
    print("="*60)
    
    cycle_count = 0
    
    try:
        while not should_stop:
            cycle_count += 1
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"\n🔄 開始第 {cycle_count} 輪搜索 ({current_time})")
            logging.info(f"開始第 {cycle_count} 輪搜索")
            
            # 執行搜索
            search_success = run_csv_search(
                args.csv_file, 
                args.max_pages, 
                args.proxy_file
            )
            
            if should_stop:
                break
            
            if not search_success:
                print("⚠️ 搜索執行失敗，但將繼續重試")
                logging.warning("搜索執行失敗，但將繼續重試")
            
            completion_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n✅ 第 {cycle_count} 輪搜索完成 ({completion_time})")
            logging.info(f"第 {cycle_count} 輪搜索完成")
            
            # 如果不是最後一輪，則等待
            if not should_stop:
                next_start_time = (datetime.datetime.now() + 
                                 datetime.timedelta(minutes=args.restart_interval))
                print(f"📅 下一輪搜索預計開始時間: {next_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                if not wait_with_countdown(args.restart_interval):
                    break
    
    except KeyboardInterrupt:
        print("\n⚠️ 程序被用戶中斷")
        logging.info("程序被用戶中斷")
    except Exception as e:
        print(f"\n❌ 程序執行過程中發生錯誤: {e}")
        logging.error(f"程序執行過程中發生錯誤: {e}", exc_info=True)
    finally:
        print("\n" + "="*60)
        print(f"🏁 自動重啟搜索工具結束")
        print(f"📊 總共完成 {cycle_count} 輪搜索")
        end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"⏰ 結束時間: {end_time}")
        print("="*60)
        logging.info(f"自動重啟搜索工具結束，總共完成 {cycle_count} 輪搜索")

if __name__ == "__main__":
    main()