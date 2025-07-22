#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Google關鍵字搜尋工具 - 主程序

這個腳本是google_keyword_search.py的主程序入口，支持命令行參數和代理功能。

使用方法:
    python main.py [搜尋詞] [目標關鍵字1] [目標關鍵字2] ... [--proxy-file PROXY_FILE]

例如:
    python main.py "Python 教學" "Django" "Flask"
    python main.py "Python 教學" "Django" "Flask" --proxy-file proxies.txt
"""

import sys
import time
import random
import logging
import argparse
from selenium import webdriver

# 導入原始腳本中的函數
from google_keyword_search import (
    setup_driver, 
    search_google, 
    find_keyword_on_page, 
    find_and_click_result, 
    go_to_next_page,
    random_scroll
)



# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def parse_arguments():
    """解析命令行參數"""
    parser = argparse.ArgumentParser(description="Google關鍵字搜尋工具")
    parser.add_argument("search_query", help="要搜尋的關鍵詞")
    parser.add_argument("target_keywords", nargs="+", help="要在搜尋結果中尋找的目標關鍵字")
    parser.add_argument("--max-pages", type=int, default=5, help="最大搜尋頁數 (默認: 5)")
    parser.add_argument("--max-retries", type=int, default=3, help="最大重試次數 (默認: 3)")
    
    return parser.parse_args()

def main():
    """主函數"""
    # 解析命令行參數
    args = parse_arguments()
    
    # 獲取搜尋詞和目標關鍵字
    search_query = args.search_query
    target_keywords = args.target_keywords
    max_pages = args.max_pages
    max_retries = args.max_retries
    
    print(f"\n🔍 搜尋詞: {search_query}")
    print(f"🎯 目標關鍵字: {', '.join(target_keywords)}")
    print(f"📄 最大搜尋頁數: {max_pages}")
    print(f"🔄 最大重試次數: {max_retries}\n")
    
    # 初始化WebDriver
    driver = setup_driver()
    
    try:
        # 搜尋Google
        search_success = search_google(driver, search_query)
        retry_count = 0
        
        # 如果搜尋失敗，嘗試使用不同代理重試
        while not search_success and retry_count < max_retries:
            retry_count += 1
            print(f"\n🔄 搜尋失敗，正在重試 ({retry_count}/{max_retries})...\n")
            
            # 關閉當前WebDriver
            try:
                driver.quit()
            except:
                pass
            
            # 重新初始化WebDriver
            driver = setup_driver()
            
            # 重新嘗試搜尋
            search_success = search_google(driver, search_query)
        
        if not search_success:
            print("\n❌ 搜尋失敗，請稍後再試或檢查網絡連接\n")
            driver.quit()
            sys.exit(1)
        
        # 在搜尋結果中查找目標關鍵字
        found_keyword = False
        current_page = 1
        
        while current_page <= max_pages and not found_keyword:
            print(f"\n📄 正在搜尋第 {current_page} 頁...")
            
            # 在當前頁面查找目標關鍵字
            for keyword in target_keywords:
                result = find_keyword_on_page(driver, keyword)
                
                # 如果檢測到驗證碼或其他錯誤
                if result is False:
                    retry_count = 0
                    while retry_count < max_retries and result is False:
                        retry_count += 1
                        print(f"\n🔄 檢測到問題，正在重試 ({retry_count}/{max_retries})...\n")
                        
                        # 關閉當前WebDriver
                        try:
                            driver.quit()
                        except:
                            pass
                        
                        # 重新初始化WebDriver
                        driver = setup_driver()
                        
                        # 重新搜尋
                        if not search_google(driver, search_query):
                            continue
                        
                        # 跳到正確的頁面
                        page_success = True
                        for i in range(1, current_page):
                            if not go_to_next_page(driver):
                                page_success = False
                                break
                        
                        if not page_success:
                            continue
                        
                        # 重新檢查關鍵字
                        result = find_keyword_on_page(driver, keyword)
                    
                    # 如果重試後仍然失敗
                    if result is False:
                        print(f"\n❌ 多次重試後仍然失敗，跳過當前關鍵字 '{keyword}'")
                        continue
                
                if result:  # 找到關鍵字
                    found_keyword = True
                    print(f"\n✅ 在第 {current_page} 頁找到目標關鍵字 '{keyword}'!")
                    
                    # 嘗試點擊包含關鍵字的結果
                    if find_and_click_result(driver, keyword):
                        print(f"\n🖱️ 已點擊包含關鍵字 '{keyword}' 的搜尋結果")
                        
                        # 在新頁面上模擬人類行為
                        time.sleep(random.uniform(3.0, 5.0))  # 等待頁面加載
                        
                        # 隨機滾動頁面幾次
                        scroll_times = random.randint(2, 5)
                        for _ in range(scroll_times):
                            random_scroll(driver)
                        
                        # 停留一段時間
                        time.sleep(random.uniform(5.0, 10.0))
                    
                    break
            
            if not found_keyword:
                # 如果當前頁面沒有找到關鍵字，跳到下一頁
                if current_page < max_pages:
                    next_page_success = go_to_next_page(driver)
                    
                    # 如果無法跳到下一頁，嘗試使用新代理
                    if not next_page_success and proxy_manager:
                        retry_count = 0
                        while not next_page_success and retry_count < max_retries:
                            retry_count += 1
                            print(f"\n🔄 無法跳轉到下一頁，正在使用新代理重試 ({retry_count}/{max_retries})...\n")
                            
                            # 標記當前代理為無效並獲取新代理
                            if current_proxy:
                                proxy_manager.mark_proxy_invalid(current_proxy)
                                current_proxy = None
                            
                            # 關閉當前WebDriver
                            try:
                                driver.quit()
                            except:
                                pass
                            
                            # 重新初始化WebDriver（使用新代理）
                            driver = setup_driver(proxy_manager)
                            current_proxy = proxy_manager.get_proxy() if proxy_manager else None
                            
                            # 重新搜尋
                            if not search_google(driver, search_query):
                                continue
                            
                            # 跳到正確的頁面
                            page_success = True
                            for i in range(1, current_page):
                                if not go_to_next_page(driver):
                                    page_success = False
                                    break
                            
                            if not page_success:
                                continue
                            
                            # 嘗試跳到下一頁
                            next_page_success = go_to_next_page(driver)
                    
                    if next_page_success:
                        current_page += 1
                    else:
                        print(f"\n❌ 無法跳轉到第 {current_page+1} 頁，可能已經到達最後一頁")
                        break
                else:
                    print(f"\n❌ 已搜尋 {max_pages} 頁，未找到目標關鍵字")
                    break
        
        if not found_keyword:
            print("\n❌ 未找到任何目標關鍵字")
        
    except KeyboardInterrupt:
        logging.info("用戶中斷程序")
        print("\n程序被用戶中斷")
    except Exception as e:
        logging.error(f"執行過程中發生錯誤: {str(e)}")
        print(f"\n❌ 執行過程中發生錯誤: {str(e)}")
    
    finally:


        # 關閉WebDriver
        try:
            if driver:
                driver.quit()
                logging.info("已關閉WebDriver")
                print("\n✓ 已關閉WebDriver")
        except: # 保持原始的 bare except 行為
            pass

if __name__ == "__main__":
    main()