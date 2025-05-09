#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
網頁關鍵字搜尋工具 - CSV版本

這個腳本是google_keyword_search.py的擴展版本，允許通過CSV檔案輸入多個搜尋關鍵字和目標關鍵字。
每一行CSV格式為：搜尋關鍵字,目標關鍵字

使用方法:
    python google_keyword_search_csv.py [CSV檔案路徑] [最大頁數(可選)]

例如:
    python google_keyword_search_csv.py keywords.csv 5

CSV檔案格式範例:
    Python 教學,Django
    AI 工具,ChatGPT
"""

import sys
import time
import random
import logging
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementNotInteractableException

# 導入原始腳本中的函數
from google_keyword_search import (
    setup_driver, 
    human_like_typing, 
    random_scroll, 
    check_for_captcha, 
    handle_captcha, 
    search_google, 
    find_keyword_on_page, 
    find_and_click_result, 
    go_to_next_page
)

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def read_csv_keywords(csv_file_path):
    """
    從CSV檔案讀取搜尋關鍵字和目標關鍵字
    CSV格式：關鍵字1,關鍵字2,關鍵字3,目標關鍵字
    
    返回：包含(搜尋關鍵字, [目標關鍵字], [所有搜尋關鍵字])元組的列表，其中第一個關鍵字作為主要搜尋詞，
    最後一個關鍵字作為目標關鍵字，中間的所有關鍵字也會被用於搜尋
    """
    keyword_pairs = []
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            for row in csv_reader:
                if not row or len(row) < 2 or not row[0].strip():
                    logging.warning(f"跳過無效行: {row}")
                    continue
                    
                # 確保行中至少有兩個元素（至少一個搜尋關鍵字和一個目標關鍵字）
                if len(row) < 2:
                    logging.warning(f"行格式不正確，需要至少一個搜尋關鍵字和一個目標關鍵字: {row}")
                    continue
                
                # 最後一個關鍵字作為目標關鍵字
                target_keyword = row[-1].strip() if row[-1].strip() else None
                
                if not target_keyword:
                    logging.warning(f"沒有有效的目標關鍵字，跳過此行: {row}")
                    continue
                
                # 收集所有搜尋關鍵字（除了最後一個目標關鍵字）
                search_keywords = []
                for i in range(len(row) - 1):
                    keyword = row[i].strip()
                    if keyword:
                        search_keywords.append(keyword)
                
                if not search_keywords:
                    logging.warning(f"沒有有效的搜尋關鍵字，跳過此行: {row}")
                    continue
                
                # 第一個關鍵字作為主要搜尋詞
                primary_search_query = search_keywords[0]
                
                # 將目標關鍵字放入列表中，以保持與原有代碼兼容
                # 同時將所有搜尋關鍵字作為第三個元素返回
                keyword_pairs.append((primary_search_query, [target_keyword], search_keywords))
                
                logging.info(f"讀取到搜尋關鍵字: {search_keywords}，目標關鍵字: {target_keyword}")
                
        if not keyword_pairs:
            logging.error("CSV檔案中沒有有效的關鍵字對")
            print("❌ CSV檔案中沒有有效的關鍵字對，請檢查檔案格式")
            return []
            
        logging.info(f"成功從CSV檔案讀取 {len(keyword_pairs)} 組關鍵字對")
        print(f"✓ 成功從CSV檔案讀取 {len(keyword_pairs)} 組關鍵字對")
        return keyword_pairs
        
    except FileNotFoundError:
        logging.error(f"找不到CSV檔案: {csv_file_path}")
        print(f"❌ 找不到CSV檔案: {csv_file_path}")
        return []
    except Exception as e:
        logging.error(f"讀取CSV檔案時出錯: {str(e)}")
        print(f"❌ 讀取CSV檔案時出錯: {str(e)}")
        return []


def process_keyword_pair(search_query, target_keywords, max_pages=10, search_keywords=None):
    """
    處理搜尋關鍵字和對應的目標關鍵字列表
    
    參數:
        search_query: 主要搜尋關鍵字
        target_keywords: 目標關鍵字列表
        max_pages: 最大搜尋頁數
        search_keywords: 所有搜尋關鍵字列表（包括主要搜尋關鍵字）
    """
    print(f"\n{'='*50}")
    print(f"開始處理搜尋詞: {search_query}")
    if search_keywords:
        print(f"所有搜尋關鍵字: {search_keywords}")
    print(f"目標關鍵字列表: {target_keywords}")
    print(f"最大搜尋頁數: {max_pages}")
    print(f"{'='*50}\n")
    
    all_keywords_processed = True
    results = {}
    
    # 對每個搜尋關鍵字單獨進行搜尋
    for i, current_search_keyword in enumerate(search_keywords):
        print(f"\n{'#'*20} 使用搜尋關鍵字: {current_search_keyword} {'#'*20}")
        
        driver = None
        search_successful = False
        
        while not search_successful:
            try:
                # 初始化瀏覽器
                logging.info(f"初始化瀏覽器，準備搜尋關鍵字: {current_search_keyword}...")
                driver = setup_driver()
                
                # 在Google上搜尋當前關鍵字
                print(f"\n正在訪問Google搜尋關鍵字: {current_search_keyword}...")
                
                if not search_google(driver, current_search_keyword):
                    print(f"搜尋關鍵字 '{current_search_keyword}' 初始化失敗，將在10秒後重試...")
                    if driver:
                        driver.quit()
                    time.sleep(10)  # 等待10秒
                    continue  # 重新開始迴圈，再次嘗試初始化和搜尋
                
                search_successful = True  # 搜尋成功
                
            except Exception as e:
                logging.error(f"初始化或搜尋關鍵字 '{current_search_keyword}' 過程中發生錯誤: {str(e)}")
                print(f"\n❌ 初始化或搜尋關鍵字 '{current_search_keyword}' 過程中發生錯誤: {str(e)}")
                if driver:
                    driver.quit()
                print("將在10秒後重試...")
                time.sleep(10)  # 等待10秒
                continue  # 重新開始迴圈
        
        # 搜尋成功後，對每個目標關鍵字進行處理
        for current_target_keyword in target_keywords:
            print(f"\n{'='*20} 在搜尋 '{current_search_keyword}' 中尋找目標關鍵字: {current_target_keyword} {'='*20}")
            
            # 確保我們在正確的搜尋結果頁面
            if driver.current_url != f"https://www.google.com/search?q={current_search_keyword}":
                print(f"\n為目標關鍵字 '{current_target_keyword}' 重新導向至Google搜尋頁面...")
                if not search_google(driver, current_search_keyword):
                    print(f"為目標關鍵字 '{current_target_keyword}' 重新搜尋失敗，跳過此關鍵字...")
                    all_keywords_processed = False
                    results[f"{current_search_keyword} -> {current_target_keyword}"] = "搜尋失敗"
                    continue

        try:
            page_num = 1
            found_current_keyword = False
            clicked_current_keyword = False
            captcha_retry_count = 0
            max_captcha_retries = 3  # 最多重試3次
            
            while page_num <= max_pages:
                logging.info(f"正在為 '{current_search_keyword}' 搜尋中尋找目標關鍵字 '{current_target_keyword}' 第 {page_num} 頁")
                print(f"\n正在為 '{current_search_keyword}' 搜尋中尋找目標關鍵字 '{current_target_keyword}' 第 {page_num} 頁...")
                
                # 在當前頁面查找關鍵字
                found_current_keyword = find_keyword_on_page(driver, current_target_keyword)
                
                # 處理驗證碼情況
                if found_current_keyword is False and (driver is None or not driver.service.is_connectable()):
                    # 驗證碼處理邏輯...
                    captcha_retry_count += 1
                    if captcha_retry_count > max_captcha_retries:
                        results[f"{current_search_keyword} -> {current_target_keyword}"] = "驗證碼重試次數已達上限"
                        break
                    # 重新初始化瀏覽器邏輯...
                    continue
                
                if found_current_keyword is True:
                    logging.info(f"成功在 '{current_search_keyword}' 搜尋的第 {page_num} 頁找到目標關鍵字 '{current_target_keyword}'")
                    print(f"成功在 '{current_search_keyword}' 搜尋的第 {page_num} 頁找到目標關鍵字 '{current_target_keyword}'")
                    results[f"{current_search_keyword} -> {current_target_keyword}"] = f"在第 {page_num} 頁找到"
                    
                    # 嘗試點擊包含關鍵字的搜尋結果
                    clicked_current_keyword = find_and_click_result(driver, current_target_keyword)
                    
                    # 處理點擊時的驗證碼情況...
                    
                    if clicked_current_keyword is True:
                        results[f"{current_search_keyword} -> {current_target_keyword}"] = f"在第 {page_num} 頁找到並成功點擊"
                        break  # 找到並點擊後，處理下一個關鍵字
                
                # 如果沒找到或沒成功點擊，且還有下一頁，則繼續
                next_page_result = go_to_next_page(driver)
                
                # 處理翻頁時的驗證碼情況...
                
                if next_page_result is True:
                    page_num += 1
                else:
                    print(f"沒有更多頁面或無法翻到下一頁，已搜尋 {page_num} 頁")
                    if f"{current_search_keyword} -> {current_target_keyword}" not in results:
                        results[f"{current_search_keyword} -> {current_target_keyword}"] = f"在 {page_num} 頁內未找到"
                    break
            
            # 如果搜尋完所有頁面仍未找到
            if f"{current_search_keyword} -> {current_target_keyword}" not in results:
                results[f"{current_search_keyword} -> {current_target_keyword}"] = f"在 {max_pages} 頁內未找到"
                
        except Exception as e:
            logging.error(f"處理搜尋關鍵字 '{current_search_keyword}' 中的目標關鍵字 '{current_target_keyword}' 時出錯: {str(e)}")
            print(f"❌ 處理搜尋關鍵字 '{current_search_keyword}' 中的目標關鍵字 '{current_target_keyword}' 時出錯: {str(e)}")
            results[f"{current_search_keyword} -> {current_target_keyword}"] = f"處理出錯: {str(e)}"
    
        # 每個搜尋關鍵字處理完畢後關閉瀏覽器
        try:
            if driver:
                driver.quit()
                logging.info(f"已關閉搜尋關鍵字 '{current_search_keyword}' 的瀏覽器")
                print(f"✓ 已關閉搜尋關鍵字 '{current_search_keyword}' 的瀏覽器")
        except Exception as e:
            logging.error(f"關閉搜尋關鍵字 '{current_search_keyword}' 的瀏覽器時出錯: {str(e)}")
            print(f"❌ 關閉搜尋關鍵字 '{current_search_keyword}' 的瀏覽器時出錯: {str(e)}")
        
        # 在處理下一個搜尋關鍵字前暫停一段時間，避免過於頻繁的請求
        if i < len(search_keywords) - 1:
            wait_time = random.uniform(3.0, 8.0)
            print(f"\n等待 {wait_time:.1f} 秒後處理下一個搜尋關鍵字...")
            time.sleep(wait_time)
    
    return results, all_keywords_processed


def main():
    # 解析命令行參數
    if len(sys.argv) < 2:
        print("使用方法: python google_keyword_search_csv.py [CSV檔案路徑] [最大頁數(可選)]")
        print("例如: python google_keyword_search_csv.py keywords.csv 5")
        return
    
    csv_file_path = sys.argv[1]
    max_pages = 5  # 默認最多搜尋5頁
    
    # 如果提供了最大頁數參數
    if len(sys.argv) > 2 and sys.argv[2].isdigit():
        try:
            max_pages = int(sys.argv[2])
        except ValueError:
            print(f"警告: 無效的頁數參數 '{sys.argv[2]}'，將使用預設值 {max_pages}")
    
    # 從CSV檔案讀取關鍵字對
    keyword_pairs = read_csv_keywords(csv_file_path)
    if not keyword_pairs:
        return
    
    print(f"\n{'='*50}")
    print(f"開始處理 {len(keyword_pairs)} 組關鍵字對")
    print(f"最大搜尋頁數: {max_pages}")
    print(f"{'='*50}\n")
    
    # 處理每一組關鍵字對
    all_results = {}
    for i, (search_query, target_keywords, search_keywords) in enumerate(keyword_pairs):
        print(f"\n{'#'*50}")
        print(f"處理第 {i+1}/{len(keyword_pairs)} 組關鍵字對")
        print(f"主要搜尋詞: {search_query}")
        print(f"所有搜尋關鍵字: {search_keywords}")
        print(f"目標關鍵字: {target_keywords[0]}")
        print(f"{'#'*50}\n")
        
        # 處理搜尋詞和對應的目標關鍵字列表，傳入所有搜尋關鍵字
        results, success = process_keyword_pair(search_query, target_keywords, max_pages, search_keywords)
        all_results[search_query] = results
        
        # 在處理下一組關鍵字前暫停一段時間，避免過於頻繁的請求
        if i < len(keyword_pairs) - 1:
            wait_time = random.uniform(3.0, 8.0)
            print(f"\n等待 {wait_time:.1f} 秒後處理下一組關鍵字...")
            time.sleep(wait_time)
    
    # 輸出所有結果摘要
    print(f"\n{'='*50}")
    print("搜尋結果摘要:")
    print(f"{'='*50}")
    
    for search_query, results in all_results.items():
        print(f"\n主要搜尋詞: {search_query}")
        # 按搜尋關鍵字分組顯示結果
        search_keyword_groups = {}
        for result_key, result_value in results.items():
            if " -> " in result_key:
                search_keyword, target_keyword = result_key.split(" -> ")
                if search_keyword not in search_keyword_groups:
                    search_keyword_groups[search_keyword] = []
                search_keyword_groups[search_keyword].append((target_keyword, result_value))
            else:
                # 兼容舊格式的結果
                print(f"  - {result_key}: {result_value}")
        
        # 顯示分組結果
        for search_keyword, target_results in search_keyword_groups.items():
            print(f"  搜尋關鍵字: {search_keyword}")
            for target_keyword, result in target_results:
                print(f"    - 目標關鍵字 '{target_keyword}': {result}")
    
    print(f"\n{'='*50}")
    print("搜尋完成!")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()