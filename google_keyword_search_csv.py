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

# 導入 proxy_manager
from proxy_manager import ProxyManager # Added ProxyManager import

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
    
    返回：包含(搜尋關鍵字, [目標關鍵字], [所有搜尋關鍵字])元組的列表
    支持每行包含不同的搜尋關鍵字和目標關鍵字組合
    
    根據README說明：
    - 第一個關鍵字作為主要搜尋詞
    - 中間的關鍵字作為額外的搜尋詞
    - 最後一個關鍵字作為目標關鍵字
    """
    keyword_pairs = []
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            for row in csv_reader:
                # 跳過空行或格式不正確的行
                if not row or not row[0].strip():
                    logging.warning(f"跳過無效行: {row}")
                    continue
                
                # 處理CSV行，支持多種格式
                # 如果只有一個元素，將其作為搜尋關鍵字，目標關鍵字設為空
                if len(row) == 1:
                    search_query = row[0].strip()
                    if search_query:
                        keyword_pairs.append((search_query, [], [search_query]))
                        logging.info(f"讀取到搜尋關鍵字: {search_query}，無目標關鍵字")
                    continue
                
                # 處理標準格式：關鍵字1,關鍵字2,關鍵字3,目標關鍵字
                search_query = row[0].strip()
                
                # 最後一個關鍵字作為目標關鍵字
                target_keyword = row[-1].strip()
                target_keywords = [target_keyword] if target_keyword else []
                
                # 收集所有搜尋關鍵字（第一個到倒數第二個）
                search_keywords = []
                for i in range(0, len(row) - 1):  # 不包括最後一個元素
                    keyword = row[i].strip()
                    if keyword:
                        search_keywords.append(keyword)
                
                if not search_query:
                    logging.warning(f"沒有有效的搜尋關鍵字，跳過此行: {row}")
                    continue
                
                # 將搜尋關鍵字和目標關鍵字添加到列表中
                keyword_pairs.append((search_query, target_keywords, search_keywords))
                logging.info(f"讀取到搜尋關鍵字: {search_query}，所有搜尋關鍵字: {search_keywords}，目標關鍵字: {target_keywords}")
                
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
                            break # Exit while page_num loop
                        else:
                            # Normal end of pages or non-critical error
                            print(f"沒有更多頁面或無法翻到下一頁，已搜尋 {page_num} 頁")
                            if f"{current_search_keyword} -> {current_target_keyword}" not in results:
                                results[f"{current_search_keyword} -> {current_target_keyword}"] = f"在 {page_num} 頁內未找到"
                            break # Exit while page_num loop
                    else:
                        page_num += 1
                
                if driver_died: # If driver died while processing targets for current_search_keyword
                    break # Exit from the target_keywords loop

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
        
        if driver_died: # If driver died while processing current_search_keyword
            break # Exit from the main search_keywords loop

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
    parser.add_argument("--proxy-file", help="代理伺服器列表檔案路徑 (每行一個代理，格式 ip:port 或 ip:port:user:pass)")

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

    proxy_manager = None
    if args.proxy_file:
        try:
            proxy_manager = ProxyManager(proxy_file_path=args.proxy_file)
            logging.info(f"已初始化代理管理器，使用代理文件: {args.proxy_file}")
            print(f"✓ 已初始化代理管理器，使用代理文件: {args.proxy_file}")
        except Exception as e:
            logging.warning(f"初始化代理管理器失敗: {e}，將不使用代理")
            print(f"⚠️ 初始化代理管理器失敗: {e}，將不使用代理")

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
        print(f"開始處理 {len(keyword_pairs)} 組CSV項目")
        print(f"最大搜尋頁數: {args.max_pages}")
        if proxy_manager and proxy_manager.proxies:
            print(f"✓ 使用代理，代理數量: {len(proxy_manager.proxies)}")
        elif proxy_manager:
            print("✓ 已配置代理文件，但代理列表為空或加載失敗，將不使用代理")
        else:
            print("ⓘ 未配置代理文件，不使用代理")
        print(f"{'='*50}\n")

        print(f"DEBUG: Entering keyword processing loop. Number of keyword pairs: {len(keyword_pairs)}") # DEBUG
        if not keyword_pairs:
            print("DEBUG: keyword_pairs is EMPTY right before the loop!") # DEBUG

        for i, (main_search_query_from_csv, target_keywords_from_csv, all_search_keywords_from_csv) in enumerate(keyword_pairs):
            logging.info(f"準備處理CSV項目 {i+1}/{len(keyword_pairs)}: 主要搜尋詞='{main_search_query_from_csv}'")
            print(f"DEBUG: Inside loop, processing item {i+1}: {main_search_query_from_csv}") # DEBUG
            print(f"\n{'='*80}")
            print(f"準備處理CSV項目 {i+1}/{len(keyword_pairs)}: {main_search_query_from_csv}")

            # 為每個CSV主要搜尋詞輪換代理並重置驅動程式
            if proxy_manager:
                logging.info(f"為 '{main_search_query_from_csv}' 嘗試輪換代理並重置驅動程式...")
                print(f"🔄 為 '{main_search_query_from_csv}' 嘗試輪換代理...")
                rotated_proxy = proxy_manager.get_next_proxy() # Corrected: Changed from rotate_proxy()
                if rotated_proxy:
                    logging.info(f"代理已輪換至: {rotated_proxy}")
                    print(f"✓ 代理已輪換至: {proxy_manager.get_current_proxy_string()}")
                elif proxy_manager.get_current_proxy_string(): # No new proxy rotated, but one might still be active from previous or initial load
                    logging.info(f"未能輪換到新代理，但仍有當前代理: {proxy_manager.get_current_proxy_string()}")
                    print(f"⚠️ 未能輪換到新代理，但仍使用當前代理: {proxy_manager.get_current_proxy_string()}")
                else:
                    logging.warning("代理輪換失敗且無可用代理。將嘗試不使用代理進行操作。")
                    print("⚠️ 代理輪換失敗且無可用代理。將嘗試不使用代理進行操作或跳過此項目。")
                    # 在這種情況下，我們應該明確地不使用代理，或者如果強制使用代理，則跳過
                    # For now, let setup_driver handle proxy_manager which might have no active proxy.
                    # The key is that setup_driver should gracefully handle a proxy_manager with no usable proxies.

                if driver: # 關閉舊的驅動程式實例
                    logging.info("關閉現有驅動程式以準備下一次搜尋...")
                    try:
                        driver.quit()
                    except Exception as e_quit:
                        logging.error(f"關閉舊驅動程式時出錯: {e_quit}")
                    driver = None # 確保舊驅動程式被清除
                
                logging.info("嘗試重新初始化驅動程式...")
                print("⏳ 嘗試重新初始化驅動程式...")
                # 如果代理輪換失敗且無可用代理，proxy_manager.get_current_proxy_string() 會是 None
                # setup_driver 應該能處理 proxy_manager 實例本身，並在內部檢查是否有可用代理
                driver = setup_driver(proxy_manager) 
                if not driver:
                    logging.error(f"為CSV項目 '{main_search_query_from_csv}' 重新初始化驅動程式失敗。跳過此項目。")
                    print(f"❌ 為CSV項目 '{main_search_query_from_csv}' 重新初始化驅動程式失敗。跳過此項目。")
                    all_results_summary[main_search_query_from_csv] = {"error": "驅動程式重新初始化失敗"}
                    # 確保在 continue 前記錄此CSV項目的失敗
                    if main_search_query_from_csv not in all_results_summary:
                         all_results_summary[main_search_query_from_csv] = {}
                    all_results_summary[main_search_query_from_csv][f"{main_search_query_from_csv} (overall)"] = "驅動程式初始化失敗，跳過"
                    continue # 跳到下一個CSV項目
                
                current_proxy_for_log = proxy_manager.get_current_proxy_string() if proxy_manager and proxy_manager.get_current_proxy_string() else "無代理"
                logging.info(f"驅動程式已重新初始化。本次使用代理: {current_proxy_for_log}")
                print(f"✓ 驅動程式已重新初始化。本次使用代理: {current_proxy_for_log}")
            elif not driver: # No proxy_manager, but driver might have died from previous CSV item
                logging.info("無代理管理器，但驅動程式不存在，嘗試重新初始化（無代理）。")
                print("⏳ 無代理管理器，但驅動程式不存在，嘗試重新初始化（無代理）。")
                driver = setup_driver(None)
                if not driver:
                    logging.error(f"為CSV項目 '{main_search_query_from_csv}' 重新初始化驅動程式失敗（無代理）。跳過此項目。")
                    print(f"❌ 為CSV項目 '{main_search_query_from_csv}' 重新初始化驅動程式失敗（無代理）。跳過此項目。")
                    all_results_summary[main_search_query_from_csv] = {"error": "驅動程式重新初始化失敗（無代理）"}
                    continue # 跳到下一個CSV項目
                logging.info("驅動程式已重新初始化（無代理）。")
                print("✓ 驅動程式已重新初始化（無代理）。")


            print(f"\n{'#'*50}")
            logging.info(f"處理CSV項目 {i+1}/{len(keyword_pairs)}: 主要搜尋詞='{main_search_query_from_csv}', 目標={target_keywords_from_csv}, 所有搜尋詞={all_search_keywords_from_csv}")
            print(f"處理CSV項目 {i+1}/{len(keyword_pairs)}")
            print(f"  主要搜尋詞 (來自CSV): {main_search_query_from_csv}")
            print(f"  所有搜尋詞 (來自CSV此行): {all_search_keywords_from_csv}")
            print(f"  目標關鍵字 (來自CSV此行): {target_keywords_from_csv}")
            print(f"{'#'*50}\n")

            current_csv_row_results = {} # Initialize results for this CSV row
            attempt_csv_item = 0
            max_attempts_csv_item = 3  # Max retries for this CSV item if driver dies
            csv_item_processed_successfully = False

            while attempt_csv_item < max_attempts_csv_item and not csv_item_processed_successfully:
                if attempt_csv_item > 0:  # This is a retry for the CSV item
                    logging.info(f"CSV項目 '{main_search_query_from_csv}' 因驅動程式故障，重試 {attempt_csv_item}/{max_attempts_csv_item -1}...")
                    print(f"🔄 CSV項目 '{main_search_query_from_csv}' 因驅動程式故障，重試 {attempt_csv_item}/{max_attempts_csv_item -1}...")
                    if driver:  # Try to quit the old driver if it exists
                        try:
                            driver.quit()
                            logging.info("舊的瀏覽器驅動程式已關閉。")
                        except Exception as e:
                            logging.warning(f"關閉舊瀏覽器驅動程式時出錯: {e}")
                    
                    driver = setup_driver(proxy_manager) # Re-initialize driver
                    if not driver:
                        logging.error(f"重試CSV項目 '{main_search_query_from_csv}' 時瀏覽器驅動程式初始化失敗。將跳過此CSV項目。")
                        print(f"❌ 重試CSV項目 '{main_search_query_from_csv}' 時瀏覽器驅動程式初始化失敗。將跳過此CSV項目。")
                        # Record failure for this CSV item and break from retry loop for this item
                        current_csv_row_results[f"{main_search_query_from_csv} (overall)"] = "驅動程式初始化失敗，無法重試"
                        break # Break from while loop (attempts for this CSV item)
                    logging.info(f"為CSV項目 '{main_search_query_from_csv}' 重試初始化瀏覽器成功。")
                    print(f"✓ 為CSV項目 '{main_search_query_from_csv}' 重試初始化瀏覽器成功。")

                # Call process_keyword_pair, which now returns driver_died status
                results_for_this_attempt, all_targets_processed_status, driver_died = \
                    process_keyword_pair(driver, main_search_query_from_csv, target_keywords_from_csv, 
                                         args.max_pages, all_search_keywords_from_csv)
                
                current_csv_row_results.update(results_for_this_attempt) # Update with results from this attempt

                if driver_died:
                    attempt_csv_item += 1
                    logging.warning(f"CSV項目 '{main_search_query_from_csv}' 處理過程中驅動程式故障。準備重試 (嘗試 {attempt_csv_item}/{max_attempts_csv_item-1}).")
                    # Results from this failed attempt are already in current_csv_row_results.
                    # If retrying, these might be overwritten or merged depending on keys.
                    # For simplicity, if a retry happens, we might want to clear results from the failed attempt
                    # or ensure keys are unique per attempt if we want to log all attempts.
                    # Current logic: results are updated, so a successful retry will overwrite/add to them.
                    # If all retries fail, the last attempt's (failed) results will remain.
                else:
                    csv_item_processed_successfully = True # Processed without driver dying
            
            if not csv_item_processed_successfully:
                logging.error(f"未能成功處理CSV項目 '{main_search_query_from_csv}' 經過 {max_attempts_csv_item} 次嘗試。")
                # Ensure a general failure message if not already specific from process_keyword_pair
                if not any(key.startswith(main_search_query_from_csv) for key in current_csv_row_results):
                     current_csv_row_results[f"{main_search_query_from_csv} (overall)"] = f"處理失敗，達到最大重試次數 {max_attempts_csv_item}"
            
            all_results_summary[main_search_query_from_csv] = current_csv_row_results

            # Always try to process the next CSV item, even if the current one had issues (unless it's a KeyboardInterrupt)
            if i < len(keyword_pairs) - 1:
                wait_time = random.uniform(5.0, 10.0) # Increased wait time between CSV entries
                logging.info(f"完成CSV項目 '{main_search_query_from_csv}' 的處理，等待 {wait_time:.1f} 秒後處理下一個CSV項目...")
                print(f"\n完成CSV項目 '{main_search_query_from_csv}' 的處理，等待 {wait_time:.1f} 秒後處理下一個CSV項目...")
                time.sleep(wait_time)
                # If driver died, it should be re-initialized at the start of the next CSV item's attempt loop
                # or if the next item starts, its own setup_driver call (if it were per item) would handle it.
                # Current logic: driver is re-initialized if an *attempt* for a CSV item fails and retries.
                # If a CSV item exhausts retries, the driver might be dead. We need to ensure it's fresh for the *next* CSV item.
                if driver_died: # If the driver died processing the *current* CSV item
                    logging.warning(f"驅動程式在處理 '{main_search_query_from_csv}' 後失效，嘗試為下一個CSV項目重新初始化。")
                    print(f"⚠️ 驅動程式在處理 '{main_search_query_from_csv}' 後失效，嘗試為下一個CSV項目重新初始化。")
                    if driver:
                        try:
                            driver.quit()
                        except Exception as e_quit:
                            logging.error(f"關閉失效的驅動程式時出錯: {e_quit}")
                    driver = setup_driver(proxy_manager)
                    if not driver:
                        logging.error("為下一個CSV項目重新初始化驅動程式失敗。可能影響後續處理。")
                        print("❌ 為下一個CSV項目重新初始化驅動程式失敗。後續項目可能無法處理。")
                        # Decide if we should stop all processing or try to continue
                        # For now, let the loop continue, and the next item will fail its setup if driver is None.

        print(f"\n{'='*50}")
        print("🎉 所有CSV項目處理完成")
        logging.info("所有CSV項目處理完成")

    except KeyboardInterrupt:
        logging.warning("使用者手動中斷程式")
        print("\n⚠️ 使用者手動中斷程式...")
    except Exception as e:
        logging.error(f"主處理過程中發生未預期錯誤: {e}", exc_info=True)
        print(f"❌ 主處理過程中發生未預期錯誤: {e}")
    finally:
        logging.info("進入 finally 區塊，準備關閉資源並顯示統計信息。")
        print("\n⏳ 進入 finally 區塊，準備關閉資源並顯示統計信息。")
        # 顯示代理統計信息
        pm_instance = locals().get('proxy_manager') # Safely get proxy_manager
        if pm_instance and hasattr(pm_instance, 'get_stats'):
            logging.info("嘗試獲取並顯示代理統計信息。")
            try:
                stats = pm_instance.get_stats()
                print("\n--- 代理使用情況總結 (CSV) ---")
                if stats:
                    print(f"  總共嘗試代理數量: {stats.get('proxies_tried_count', 'N/A')}")
                    print(f"  代理輪換次數: {stats.get('successful_rotations', 'N/A')}")
                    print(f"  代理失敗次數: {stats.get('failed_attempts_count', 'N/A')}")
                    logging.info(f"代理統計: {stats}")
                else:
                    print("  未能獲取代理統計信息 (get_stats 返回空) 或未使用代理。")
                    logging.info("未能獲取代理統計信息 (get_stats 返回空) 或未使用代理。")
                print("-----------------------------")
            except Exception as e_stats_display:
                logging.error(f"顯示代理統計時發生錯誤: {str(e_stats_display)}", exc_info=True)
                print(f"⚠️ 顯示代理統計時發生錯誤: {str(e_stats_display)}")
        elif pm_instance:
            logging.info("Proxy_manager 實例存在但沒有 get_stats 方法，或未使用代理。")
            print("\n--- 代理統計信息不可用 (Proxy_manager 問題或未使用代理) ---")
        else:
            logging.info("未配置代理 (proxy_manager is None)。")
            print("\n--- 未配置代理 (proxy_manager is None) --- ")
        
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
            print(f"\n📜 CSV 主要搜尋詞: {main_csv_query}")
            if not results_for_main_query:
                print("  - 此CSV項目沒有結果。")
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