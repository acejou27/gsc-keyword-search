#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
網頁關鍵字搜尋工具 - CSV版本

這個腳本是google_keyword_search.py的擴展版本，允許通過CSV檔案輸入多個搜尋關鍵字和目標關鍵字。
每一行CSV格式為：關鍵字1,關鍵字2,關鍵字3,目標關鍵字

使用方法:
    python google_keyword_search_csv.py [CSV檔案路徑] [最大頁數(可選)]

例如:
    python google_keyword_search_csv.py keywords.csv 5

CSV檔案格式範例:
    Python 教學,Flask,Django
    AI 工具,機器學習,ChatGPT

格式說明:
    - 第一個關鍵字作為主要搜尋詞
    - 中間的關鍵字作為額外的搜尋詞
    - 最後一個關鍵字作為目標關鍵字
"""

import sys
import time
import random
import logging
import csv
import argparse # Added argparse
from urllib.parse import quote_plus
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
    從CSV檔案讀取搜尋關鍵字
    CSV格式：關鍵字1,關鍵字2,關鍵字3,...,目標字
    
    返回：包含(搜尋關鍵字, [目標字], [所有搜尋關鍵字])元組的列表
    每行最後一個關鍵字作為目標字，前面的都作為搜尋關鍵字
    
    格式說明：
    - 每行最後一個關鍵字是目標字
    - 前面的關鍵字都是搜尋關鍵字
    - 每個搜尋關鍵字會搜尋目標字
    - 失敗3次後會跳到下一個搜尋關鍵字
    - 同一行處理完畢後才會處理下一行
    """
    keyword_pairs = []
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            for row_index, row in enumerate(csv_reader):
                # 跳過空行
                if not row:
                    logging.warning(f"跳過空行: 第{row_index + 1}行")
                    continue
                
                # 清理關鍵字
                cleaned_keywords = [keyword.strip() for keyword in row if keyword.strip()]
                
                if len(cleaned_keywords) < 2:
                    logging.warning(f"第{row_index + 1}行關鍵字數量不足（至少需要2個：搜尋關鍵字和目標字），跳過此行")
                    continue
                
                # 最後一個關鍵字是目標字，前面的都是搜尋關鍵字
                target_keyword = cleaned_keywords[-1]
                search_keywords = cleaned_keywords[:-1]
                
                # 為每個搜尋關鍵字創建一個搜尋項目
                for search_keyword in search_keywords:
                    # 格式：(搜尋關鍵字, 目標關鍵字列表, 所有搜尋關鍵字列表)
                    keyword_pairs.append((search_keyword, [target_keyword], [search_keyword]))
                    logging.info(f"讀取到搜尋關鍵字: '{search_keyword}' -> 目標字: '{target_keyword}' (第{row_index + 1}行)")
                
        if not keyword_pairs:
            logging.error("CSV檔案中沒有有效的關鍵字")
            print("❌ CSV檔案中沒有有效的關鍵字，請檢查檔案格式")
            return []
            
        logging.info(f"成功從CSV檔案讀取 {len(keyword_pairs)} 個搜尋項目")
        print(f"✓ 成功從CSV檔案讀取 {len(keyword_pairs)} 個搜尋項目")
        return keyword_pairs
        
    except FileNotFoundError:
        logging.error(f"找不到CSV檔案: {csv_file_path}")
        print(f"❌ 找不到CSV檔案: {csv_file_path}")
        return []
    except Exception as e:
        logging.error(f"讀取CSV檔案時出錯: {str(e)}")
        print(f"❌ 讀取CSV檔案時出錯: {str(e)}")
        return []


def process_keyword_pair(driver, search_query, target_keywords, max_pages=10, search_keywords=None): # Added driver as parameter, removed proxy_manager initialization from here
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
    driver_died = False # NEW: Flag to indicate if driver died
    
    # 對每個搜尋關鍵字單獨進行搜尋
    for i, current_search_keyword in enumerate(search_keywords):
        print(f"\n{'#'*20} 使用搜尋關鍵字: {current_search_keyword} {'#'*20}")
        
        # driver is now passed as an argument, no need to initialize here
        search_successful = False
        
        # 在Google上搜尋當前關鍵字
        # This part is simplified as driver is managed by main
        logging.info(f"使用傳入的瀏覽器實例搜尋關鍵字: {current_search_keyword}...")
        print(f"\n正在訪問Google搜尋關鍵字: {current_search_keyword}...")
        
        if not search_google(driver, current_search_keyword):
            print(f"搜尋關鍵字 '{current_search_keyword}' 失敗。")
            logging.error(f"搜尋關鍵字 '{current_search_keyword}' 失敗。")
            results[f"{search_query} -> {current_search_keyword} (overall)"] = "Google搜尋初始化失敗 (CAPTCHA?)"
            all_keywords_processed = False # Mark as not all processed
            driver_died = True # NEW: Signal driver death
            break # NEW: Exit this loop as driver is dead
        
        search_successful = True # Assuming search_google is successful if it returns True
        
        # 搜尋成功後，對每個目標關鍵字進行處理
        for current_target_keyword in target_keywords:
            print(f"\n{'='*20} 在搜尋 '{current_search_keyword}' 中尋找目標關鍵字: {current_target_keyword} {'='*20}")
            
            # 確保我們在正確的搜尋結果頁面
            encoded_search_keyword = quote_plus(current_search_keyword)
            expected_search_page_prefix = f"https://www.google.com/search?q={encoded_search_keyword}"

            if not driver.current_url.startswith(expected_search_page_prefix):
                print(f"  偵測到URL不符或已離開搜尋頁面。")
                print(f"  目前URL: {driver.current_url}")
                print(f"  預期URL應以 '{expected_search_page_prefix}' 開頭。")
                print(f"  將為目標關鍵字 '{current_target_keyword}' (於 '{current_search_keyword}' 的搜尋結果中) 重新導向至Google搜尋頁面...")
                if not search_google(driver, current_search_keyword):
                    print(f"  為目標關鍵字 '{current_target_keyword}' 重新搜尋 '{current_search_keyword}' 失敗，跳過此目標關鍵字...")
                    all_keywords_processed = False
                    results[f"{current_search_keyword} -> {current_target_keyword}"] = "重新搜尋失敗"
                    continue

            try:
                page_num = 1
                found_current_keyword = False
                clicked_current_keyword = False
                # captcha_retry_count = 0 # OLD: This internal retry is removed
                # max_captcha_retries = 3  # OLD: Max retries for CAPTCHA within this function
            
                while page_num <= max_pages:
                    logging.info(f"正在為 '{current_search_keyword}' 搜尋中尋找目標關鍵字 '{current_target_keyword}' 第 {page_num} 頁")
                    print(f"\n正在為 '{current_search_keyword}' 搜尋中尋找目標關鍵字 '{current_target_keyword}' 第 {page_num} 頁...")
                    
                    # 在當前頁面查找關鍵字
                    found_current_keyword = find_keyword_on_page(driver, current_target_keyword)
                    
                    # 處理驗證碼情況
                    if found_current_keyword is False:
                        # Check if driver died (e.g., due to CAPTCHA handled by find_keyword_on_page)
                        if not driver.service.is_connectable():
                            logging.warning(f"CAPTCHA or driver issue detected after find_keyword_on_page for '{current_target_keyword}' in '{current_search_keyword}'. Driver closed.")
                            print(f"⚠️ CAPTCHA or driver issue detected for '{current_target_keyword}' in '{current_search_keyword}'.")
                            results[f"{current_search_keyword} -> {current_target_keyword}"] = "CAPTCHA/Driver中止 (find_keyword_on_page)"
                            driver_died = True
                            # 注意：這裡不需要等待5分鐘，因為在main函數中已經添加了等待邏輯
                            break # Exit while page_num loop
                    
                    if found_current_keyword is True:
                        logging.info(f"成功在 '{current_search_keyword}' 搜尋的第 {page_num} 頁找到目標關鍵字 '{current_target_keyword}'")
                        print(f"成功在 '{current_search_keyword}' 搜尋的第 {page_num} 頁找到目標關鍵字 '{current_target_keyword}'")
                        results[f"{current_search_keyword} -> {current_target_keyword}"] = f"在第 {page_num} 頁找到"
                        
                        # 嘗試點擊包含關鍵字的搜尋結果
                        clicked_current_keyword = find_and_click_result(driver, current_target_keyword)
                        
                        if clicked_current_keyword is False:
                            if not driver.service.is_connectable():
                                logging.warning(f"CAPTCHA or driver issue detected after find_and_click_result for '{current_target_keyword}' in '{current_search_keyword}'. Driver closed.")
                                print(f"⚠️ CAPTCHA or driver issue detected during click for '{current_target_keyword}' in '{current_search_keyword}'.")
                                results[f"{current_search_keyword} -> {current_target_keyword}"] = "CAPTCHA/Driver中止 (find_and_click_result)"
                                driver_died = True
                                # 注意：這裡不需要等待5分鐘，因為在main函數中已經添加了等待邏輯
                                break # Exit while page_num loop
                        
                        if clicked_current_keyword is True:
                            results[f"{current_search_keyword} -> {current_target_keyword}"] = f"在第 {page_num} 頁找到並成功點擊"
                            break  # 找到並點擊後，處理下一個目標關鍵字
                    
                    if driver_died: # Check if driver died in previous step
                        break # Exit while page_num loop

                    # 如果沒找到或沒成功點擊，且還有下一頁，則繼續
                    next_page_result = go_to_next_page(driver)
                    
                    if next_page_result is False:
                        if not driver.service.is_connectable():
                            logging.warning(f"CAPTCHA or driver issue detected after go_to_next_page for '{current_search_keyword}'. Driver closed.")
                            print(f"⚠️ CAPTCHA or driver issue detected during pagination for '{current_search_keyword}'.")
                            results[f"{current_search_keyword} -> {current_target_keyword}"] = "CAPTCHA/Driver中止 (go_to_next_page)" # Or a general pagination failure message
                            driver_died = True
                            # 注意：這裡不需要等待5分鐘，因為在main函數中已經添加了等待邏輯
                            break # Exit while page_num loop
                        else:
                            # Normal end of pages or non-critical error
                            print(f"沒有更多頁面或無法翻到下一頁，已搜尋 {page_num} 頁")
                            if f"{current_search_keyword} -> {current_target_keyword}" not in results:
                                results[f"{current_search_keyword} -> {current_target_keyword}"] = f"在 {page_num} 頁內未找到"
                            break # Exit while page_num loop
                    else:
                        page_num += 1
                
                # 移除這裡的break，即使驅動程式失效，也會在main函數中重新初始化並重試
                # if driver_died: # If driver died while processing targets for current_search_keyword
                #     break # Exit from the target_keywords loop

                # 如果搜尋完所有頁面仍未找到
                if f"{current_search_keyword} -> {current_target_keyword}" not in results:
                    results[f"{current_search_keyword} -> {current_target_keyword}"] = f"在 {max_pages} 頁內未找到"
                    
            except Exception as e:
                logging.error(f"處理搜尋關鍵字 '{current_search_keyword}' 中的目標關鍵字 '{current_target_keyword}' 時出錯: {str(e)}")
                print(f"❌ 處理搜尋關鍵字 '{current_search_keyword}' 中的目標關鍵字 '{current_target_keyword}' 時出錯: {str(e)}")
                results[f"{current_search_keyword} -> {current_target_keyword}"] = f"處理出錯: {str(e)}"
                # If a generic exception occurs, we might not know if driver died, but good to check
                if not driver.service.is_connectable():
                    driver_died = True # Assume driver died if connection lost
        
        # 移除這裡的break，即使驅動程式失效，也會在main函數中重新初始化並重試
        # if driver_died: # If driver died while processing current_search_keyword
        #     break # Exit from the main search_keywords loop

        # Pause between processing different target_keywords for the same search_keyword if needed, or between search_keywords in main loop
        # The pause between different search_keywords (from the search_keywords list) is handled in this loop
        if i < len(search_keywords) - 1:
            wait_time = random.uniform(3.0, 8.0)
            logging.info(f"完成 '{current_search_keyword}' 的目標關鍵字處理，等待 {wait_time:.1f} 秒後處理此CSV列中的下一個搜尋關鍵字...")
            print(f"\n完成 '{current_search_keyword}' 的目標關鍵字處理，等待 {wait_time:.1f} 秒後處理此CSV列中的下一個搜尋關鍵字...")
            time.sleep(wait_time)
    
    return results, all_keywords_processed, driver_died # NEW: Return driver_died status


def main():
    print("DEBUG: Entered main function") # DEBUG
    parser = argparse.ArgumentParser(
        description="網頁關鍵字搜尋工具 - CSV版本",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="CSV檔案格式範例 (每行一個搜尋任務):\n  Python 教學,Flask,Django\n  AI 工具,機器學習,ChatGPT\n\n格式說明:\n  - 第一個關鍵字作為主要搜尋詞\n  - 中間的關鍵字作為額外的搜尋詞\n  - 最後一個關鍵字作為目標關鍵字"
    )
    parser.add_argument("csv_file", help="包含搜尋關鍵字和目標關鍵字的CSV檔案路徑")
    parser.add_argument("max_pages", type=int, nargs='?', default=10, help="最大搜尋頁數 (預設: 10)")

    args = parser.parse_args()

    if args.max_pages <= 0:
        logging.error("最大頁數必須是正整數")
        print("❌ 最大頁數必須是正整數")
        sys.exit(1)

    keyword_pairs = read_csv_keywords(args.csv_file)
    print(f"DEBUG: After read_csv_keywords, keyword_pairs: {keyword_pairs}") # DEBUG
    if not keyword_pairs:
        logging.error("CSV檔案中沒有有效的關鍵字對，或讀取失敗")
        print("❌ CSV檔案中沒有有效的關鍵字對，或讀取失敗。請檢查檔案路徑和內容格式。")
        print("DEBUG: Exiting because keyword_pairs is empty or failed to load.") # DEBUG
        sys.exit(1)

    driver = None # 初始化 driver 為 None
    all_results_summary = {}
    print(f"DEBUG: Initialized all_results_summary. Length: {len(all_results_summary)}") # DEBUG

    print(f"DEBUG: keyword_pairs before try block: {keyword_pairs}") # DEBUG

    try:
        # The keyword_pairs are already loaded and checked before this try block.
        # The redundant driver initializations were already commented out.

        # logging.info("開始初始化主瀏覽器驅動程式...")
        # print("⏳ 開始初始化主瀏覽器驅動程式...")
        # driver = setup_driver(proxy_manager) # Initial setup
        # if not driver:
        #     logging.error("主瀏覽器驅動程式初始化失敗。腳本將無法繼續處理關鍵字。")
        #     print("❌ 主瀏覽器驅動程式初始化失敗。腳本將無法繼續處理關鍵字。")
        #     return # 這裡的 return 會執行 finally

        print(f"\n{'='*50}")
        print(f"開始處理 {len(keyword_pairs)} 個搜尋項目")
        print(f"最大搜尋頁數: {args.max_pages}")
        print("ⓘ 未配置代理文件，不使用代理")
        print(f"{'='*50}\n")

        print(f"DEBUG: Entering keyword processing loop. Number of keyword pairs: {len(keyword_pairs)}") # DEBUG
        if not keyword_pairs:
            print("DEBUG: keyword_pairs is EMPTY right before the loop!") # DEBUG

        for i, (main_search_query_from_csv, target_keywords_from_csv, all_search_keywords_from_csv) in enumerate(keyword_pairs):
            target_display = target_keywords_from_csv[0] if target_keywords_from_csv else "無目標"
            logging.info(f"準備處理搜尋項目 {i+1}/{len(keyword_pairs)}: 搜尋詞='{main_search_query_from_csv}' -> 目標='{target_display}'")
            print(f"DEBUG: Inside loop, processing item {i+1}: {main_search_query_from_csv} -> {target_display}") # DEBUG
            print(f"\n{'='*80}")
            print(f"準備處理搜尋項目 {i+1}/{len(keyword_pairs)}: {main_search_query_from_csv} -> {target_display}")

            if not driver: # 如果驅動程式尚未初始化或先前已關閉
                logging.info("初始化驅動程式...")
                print("⏳ 初始化驅動程式...")
                driver = setup_driver()
                if not driver:
                    logging.error(f"為搜尋項目 '{main_search_query_from_csv} -> {target_display}' 初始化驅動程式失敗。跳過此搜尋項目。")
                    print(f"❌ 為搜尋項目 '{main_search_query_from_csv} -> {target_display}' 初始化驅動程式失敗。跳過此搜尋項目。")
                    all_results_summary[main_search_query_from_csv] = {"error": "驅動程式初始化失敗"}
                    if main_search_query_from_csv not in all_results_summary:
                        all_results_summary[main_search_query_from_csv] = {}
                    all_results_summary[main_search_query_from_csv][f"{main_search_query_from_csv} (overall)"] = "驅動程式初始化失敗，跳過"
                    continue # 跳到下一個搜尋項目
                logging.info("驅動程式已初始化。")
                print("✓ 驅動程式已初始化。")


            print(f"\n{'#'*50}")
            logging.info(f"處理搜尋項目 {i+1}/{len(keyword_pairs)}: 搜尋詞='{main_search_query_from_csv}' -> 目標='{target_display}'")
            print(f"處理搜尋項目 {i+1}/{len(keyword_pairs)}")
            print(f"  搜尋詞: {main_search_query_from_csv}")
            print(f"  目標關鍵字: {target_display}")
            print(f"{'#'*50}\n")

            current_csv_row_results = {} # Initialize results for this CSV row
            attempt_keyword = 0
            max_attempts_keyword = 3  # 最多重試3次，第4次開始換下個關鍵字
            keyword_processed_successfully = False

            while attempt_keyword < max_attempts_keyword and not keyword_processed_successfully:
                if attempt_keyword > 0:  # This is a retry for the keyword
                    logging.info(f"搜尋項目 '{main_search_query_from_csv} -> {target_display}' 因驅動程式故障，第 {attempt_keyword} 次重試 (最多 {max_attempts_keyword} 次)...")
                    print(f"🔄 搜尋項目 '{main_search_query_from_csv} -> {target_display}' 因驅動程式故障，第 {attempt_keyword} 次重試 (最多 {max_attempts_keyword} 次)...")
                    if driver:  # Try to quit the old driver if it exists
                        try:
                            driver.quit()
                            logging.info("舊的瀏覽器驅動程式已關閉。")
                        except Exception as e:
                            logging.warning(f"關閉舊瀏覽器驅動程式時出錯: {e}")
                    
                    driver = setup_driver() # Re-initialize driver
                    if not driver:
                        logging.error(f"重試搜尋項目 '{main_search_query_from_csv} -> {target_display}' 時瀏覽器驅動程式初始化失敗。將跳過此搜尋項目。")
                        print(f"❌ 重試搜尋項目 '{main_search_query_from_csv} -> {target_display}' 時瀏覽器驅動程式初始化失敗。將跳過此搜尋項目。")
                        # Record failure for this keyword and break from retry loop for this item
                        current_csv_row_results[f"{main_search_query_from_csv} (overall)"] = "驅動程式初始化失敗，無法重試"
                        break # Break from while loop (attempts for this keyword)
                    logging.info(f"為搜尋項目 '{main_search_query_from_csv} -> {target_display}' 重試初始化瀏覽器成功。")
                    print(f"✓ 為搜尋項目 '{main_search_query_from_csv} -> {target_display}' 重試初始化瀏覽器成功。")

                # Call process_keyword_pair, which now returns driver_died status
                results_for_this_attempt, all_targets_processed_status, driver_died = \
                    process_keyword_pair(driver, main_search_query_from_csv, target_keywords_from_csv, 
                                         args.max_pages, all_search_keywords_from_csv)
                
                current_csv_row_results.update(results_for_this_attempt) # Update with results from this attempt

                if driver_died:
                    attempt_keyword += 1
                    logging.warning(f"搜尋項目 '{main_search_query_from_csv} -> {target_display}' 處理過程中驅動程式故障。準備第 {attempt_keyword} 次重試 (最多 {max_attempts_keyword} 次)。")
                    # Results from this failed attempt are already in current_csv_row_results.
                    # If retrying, these might be overwritten or merged depending on keys.
                    # For simplicity, if a retry happens, we might want to clear results from the failed attempt
                    # or ensure keys are unique per attempt if we want to log all attempts.
                    # Current logic: results are updated, so a successful retry will overwrite/add to them.
                    # 如果達到最大重試次數，將跳到下一個關鍵字
                else:
                    keyword_processed_successfully = True # Processed without driver dying
            
            # 如果達到最大重試次數仍未成功，跳到下一個搜尋項目
            if not keyword_processed_successfully:
                logging.error(f"未能成功處理搜尋項目 '{main_search_query_from_csv} -> {target_display}' 經過 {max_attempts_keyword} 次嘗試，跳到下一個搜尋項目。")
                # Ensure a general failure message if not already specific from process_keyword_pair
                if not any(key.startswith(main_search_query_from_csv) for key in current_csv_row_results):
                     current_csv_row_results[f"{main_search_query_from_csv} (overall)"] = f"處理失敗，達到最大重試次數 {max_attempts_keyword}，跳到下一個搜尋項目"
            
            all_results_summary[main_search_query_from_csv] = current_csv_row_results

            # 如果當前項目處理成功且還有下一個項目，則處理下一個項目
            if keyword_processed_successfully and i < len(keyword_pairs) - 1:
                wait_time = random.uniform(5.0, 10.0) # Increased wait time between keyword entries
                logging.info(f"成功完成搜尋項目 '{main_search_query_from_csv} -> {target_display}' 的處理，等待 {wait_time:.1f} 秒後處理下一個搜尋項目...")
                print(f"\n成功完成搜尋項目 '{main_search_query_from_csv} -> {target_display}' 的處理，等待 {wait_time:.1f} 秒後處理下一個搜尋項目...")
                time.sleep(wait_time)
            # 如果驅動程式失效，需要等待30-60秒隨機時間後重新初始化，然後重試當前項目
            elif driver_died: # 如果驅動程式在處理當前項目時失效
                # 隨機等待30-60秒，模擬真人行為
                wait_time = random.uniform(30, 60)
                logging.warning(f"驅動程式在處理 '{main_search_query_from_csv}' 時失效，等待 {wait_time:.1f} 秒後重新初始化並重試當前項目。")
                print(f"⚠️ 驅動程式在處理 '{main_search_query_from_csv}' 時失效，等待 {wait_time:.1f} 秒後重新初始化並重試當前項目。")
                
                # 確保舊的瀏覽器已關閉
                if driver:
                    try:
                        driver.quit()
                    except Exception as e_quit:
                        logging.error(f"關閉失效的驅動程式時出錯: {e_quit}")
                
                # 等待隨機時間後重新啟動瀏覽器
                print(f"等待 {wait_time:.1f} 秒後重新啟動瀏覽器...")
                time.sleep(wait_time)
                
                driver = setup_driver()
                if not driver:
                    logging.error("重新初始化驅動程式失敗。將繼續重試。")
                    print("❌ 重新初始化驅動程式失敗。將繼續重試。")
                    # 即使驅動程式初始化失敗，也會繼續重試

        print(f"\n{'='*50}")
        print("🎉 所有搜尋項目處理完成")
        logging.info("所有搜尋項目處理完成")

    except KeyboardInterrupt:
        logging.warning("使用者手動中斷程式")
        print("\n⚠️ 使用者手動中斷程式...")
    except Exception as e:
        logging.error(f"主處理過程中發生未預期錯誤: {e}", exc_info=True)
        print(f"❌ 主處理過程中發生未預期錯誤: {e}")
    finally:
        logging.info("進入 finally 區塊，準備關閉資源。")
        print("\n⏳ 進入 finally 區塊，準備關閉資源。")
        
        current_driver = locals().get('driver') # Safely get driver
        if current_driver:
            logging.info("關閉瀏覽器驅動程式...")
            print("⏳ 關閉瀏覽器驅動程式...")
            try:
                current_driver.quit()
                logging.info("瀏覽器驅動程式已關閉。")
                print("✓ 瀏覽器驅動程式已關閉。")
            except Exception as e_quit_driver:
                logging.error(f"關閉瀏覽器時發生錯誤: {e_quit_driver}", exc_info=True)
                print(f"❌ 關閉瀏覽器時發生錯誤: {e_quit_driver}")
        else:
            logging.info("瀏覽器驅動程式未初始化或已被關閉。")
            print("ⓘ 瀏覽器驅動程式未初始化或已被關閉。")

    # 輸出所有結果摘要
    print(f"\n{'='*60}")
    print("最終搜尋結果摘要:")
    print(f"{'='*60}")
    
    if not all_results_summary:
        print("沒有處理任何結果。")
    else:
        for main_csv_query, results_for_main_query in all_results_summary.items():
            print(f"\n📜 主要搜尋詞: {main_csv_query}")
            if not results_for_main_query:
                print("  - 此關鍵字沒有結果。")
                continue

            # Group results by the actual search keyword used for Google search
            # The keys in results_for_main_query are like "ActualSearchKeyword -> TargetKeyword"
            grouped_by_actual_search = {}
            for result_key, result_value in results_for_main_query.items():
                if " -> " in result_key:
                    actual_search_term, target = result_key.split(" -> ", 1)
                    if actual_search_term not in grouped_by_actual_search:
                        grouped_by_actual_search[actual_search_term] = []
                    grouped_by_actual_search[actual_search_term].append({'target': target, 'status': result_value})
                else:
                    # Fallback for unexpected result_key format
                    if "_direct_" not in grouped_by_actual_search:
                         grouped_by_actual_search["_direct_"] = []
                    grouped_by_actual_search["_direct_"].append({'target': result_key, 'status': result_value})
            
            for actual_term, target_details_list in grouped_by_actual_search.items():
                if actual_term != "_direct_":
                    print(f"  🔍 Google搜尋使用: {actual_term}")
                else:
                    print("  (直接結果):") # Should not happen with current structure
                for detail in target_details_list:
                    print(f"    🎯 目標 '{detail['target']}': {detail['status']}")
    
    print(f"\n{'='*60}")
    print("👋 搜尋程序結束")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()