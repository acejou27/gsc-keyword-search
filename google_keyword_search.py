#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
網頁關鍵字搜尋工具

這個腳本使用Selenium自動化瀏覽器，在Google搜尋結果中尋找特定關鍵字。
如果當前頁面沒有找到關鍵字，會自動翻到下一頁繼續搜尋。
腳本包含防機器人檢測功能，模擬人類行為並處理Google驗證碼。
腳本支援搜尋多個目標關鍵字，並在點擊進入結果頁面後模擬使用者行為。
腳本支援使用GSA Proxy獲取代理，實現IP輪換功能，避免被搜尋引擎封鎖。

使用方法:
    python google_keyword_search.py [搜尋詞] [目標關鍵字1] [目標關鍵字2] ... [--proxy-file PROXY_FILE]

例如:
    python google_keyword_search.py "Python 教學" "Django" "Flask"
    python google_keyword_search.py "Python 教學" "Django" "Flask" --proxy-file proxies.txt
"""

import sys
import time
import random
import logging
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementNotInteractableException
from webdriver_manager.chrome import ChromeDriverManager # 自動管理 ChromeDriver

# 導入代理管理器
try:
    from proxy_manager import ProxyManager
    PROXY_SUPPORT = True
except ImportError:
    PROXY_SUPPORT = False
    logging.warning("未找到proxy_manager模塊，代理功能將被禁用")
    print("⚠️ 未找到proxy_manager模塊，代理功能將被禁用")

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def setup_driver(proxy_manager=None):
    """設置並返回Chrome WebDriver，添加更多人為特徵，支持代理"""
    chrome_options = Options()
    # 取消下面的註釋可以在背景運行Chrome（無界面模式）
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # 添加更多選項以減少被檢測為機器人的可能性
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # Add options to potentially prevent IP leakage and disable direct geolocation
    prefs = {
        "profile.managed_default_content_settings.geolocation": 2,  # Block geolocation API
        "webrtc.ip_handling_policy": "disable_non_proxied_udp",  # Attempt to disable WebRTC leaks for non-proxied UDP
        "webrtc.multiple_routes_enabled": False, # Disable multiple WebRTC routes
        "webrtc.nonproxied_udp_enabled": False # Disable non-proxied UDP for WebRTC
    }
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument('--disable-features=WebRtcHideLocalIpsWithMdns') # Another attempt to hide local IPs with mDNS
    
    # 隨機用戶代理
    user_agents = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:95.0) Gecko/20100101 Firefox/95.0"
    ]
    chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")
    
    # 如果提供了代理管理器，則使用代理
    if proxy_manager:
        try:
            proxy_arg = proxy_manager.get_proxy_for_selenium()
            if proxy_arg:
                logging.info(f"使用代理: {proxy_arg}")
                print(f"✓ 使用代理設置: {proxy_arg}")
                chrome_options.add_argument(proxy_arg)
        except Exception as e:
            logging.error(f"設置代理時出錯: {str(e)}")
            print(f"❌ 設置代理時出錯: {str(e)}")
    
    # 初始化WebDriver
    driver = None
    wdm_error_occurred = False # Flag to track if webdriver_manager had an issue
    try:
        logging.info("Attempting to initialize Chrome WebDriver using webdriver_manager...")
        print("⏳ Attempting to initialize Chrome WebDriver using webdriver_manager...")
        
        # 使用 webdriver_manager 自動管理 ChromeDriver
        try:
            # 確保 webdriver_manager 日誌級別與應用程式一致或更詳細
            # import os
            # os.environ['WDM_LOG_LEVEL'] = str(logging.getLogger().getEffectiveLevel()) # Example: Sync with root logger
            # os.environ['WDM_PROGRESS_BAR'] = '0' # Disable progress bar if desired

            service = Service(ChromeDriverManager().install())
            logging.info("ChromeDriver setup via webdriver_manager successful.")
            print("✓ ChromeDriver setup via webdriver_manager successful.")
        except Exception as wdm_error:
            wdm_error_occurred = True
            logging.error(f"Failed to install/setup ChromeDriver using webdriver_manager: {str(wdm_error)}")
            print(f"❌ Failed to install/setup ChromeDriver using webdriver_manager: {str(wdm_error)}")
            logging.warning("Attempting to initialize ChromeDriver Service without explicit path (relying on PATH as a fallback)...")
            print("⚠️ Attempting to initialize ChromeDriver Service without explicit path (relying on PATH as a fallback)...")
            try:
                service = Service() # Fallback to PATH if webdriver_manager fails
            except Exception as fallback_service_init_error:
                logging.error(f"Failed to initialize ChromeDriver Service (fallback to PATH after webdriver_manager failure): {str(fallback_service_init_error)}")
                print(f"❌ Failed to initialize ChromeDriver Service (fallback to PATH after webdriver_manager failure): {str(fallback_service_init_error)}")
                raise # Re-raise if fallback also fails

        driver = webdriver.Chrome(service=service, options=chrome_options)
        logging.info("Chrome WebDriver initialized successfully.")
        print("✓ Chrome WebDriver initialized successfully.")
        
        # 修改navigator.webdriver屬性以避免檢測
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    except Exception as e:
        logging.error(f"Failed to initialize Chrome WebDriver: {str(e)}")
        print(f"❌ Failed to initialize Chrome WebDriver: {str(e)}")
        if wdm_error_occurred:
             print("ℹ️ Webdriver_manager failed. This might be due to network issues preventing ChromeDriver download, or permission problems. Ensure internet connectivity and appropriate permissions for the webdriver_manager cache directory.")
        elif "Service" in str(e) or "path" in str(e).lower():
             print("ℹ️ This might be due to ChromeDriver not being found in PATH (if webdriver_manager failed or was bypassed). Ensure ChromeDriver is installed and in your system's PATH.")
        else:
             print("ℹ️ An unexpected error occurred during WebDriver initialization. Check Chrome browser installation and compatibility.")

        if driver:
            try:
                driver.quit()
            except Exception as quit_error:
                logging.error(f"Error quitting driver after initialization failure: {str(quit_error)}")
        # Inform user about webdriver-manager dependency
        print("\n💡 Note: This script now uses 'webdriver-manager'. If not installed, please run: pip install webdriver-manager")
        raise

    return driver


def human_like_typing(element, text):
    """模擬人類輸入，帶有隨機延遲"""
    for char in text:
        element.send_keys(char)
        # 隨機延遲模擬人類打字速度
        time.sleep(random.uniform(0.05, 0.25))
    
    # 輸入完成後的隨機暫停
    time.sleep(random.uniform(0.5, 1.5))

def random_scroll(driver):
    """隨機滾動頁面以模擬人類行為"""
    scroll_amount = random.randint(100, 800)
    driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
    time.sleep(random.uniform(0.5, 2.0))

def check_for_captcha(driver):
    """檢查頁面是否出現驗證碼"""
    captcha_indicators = [
        "//iframe[contains(@src, 'recaptcha')]",
        "//div[contains(@class, 'g-recaptcha')]",
        "//textarea[@id='g-recaptcha-response']",
        "//h1[contains(text(), '請證明這不是自動操作')]",
        "//h1[contains(text(), 'Prove you')]",
        "//h1[contains(text(), 'unusual traffic')]"
    ]
    
    for indicator in captcha_indicators:
        try:
            if driver.find_elements(By.XPATH, indicator):
                return True
        except:
            continue
    
    return False

def handle_captcha(driver):
    """處理Google驗證碼 - 等待30秒，然後自動關閉瀏覽器並返回False以觸發重新啟動"""
    logging.warning("檢測到驗證碼！將等待30秒後關閉瀏覽器並觸發重新啟動...")
    print("\n⚠️ 檢測到Google驗證碼！將等待30秒後關閉瀏覽器並觸發重新啟動...")

    # 等待10秒
    wait_time = 10
    logging.info(f"等待 {wait_time} 秒...")
    print(f"⏳ 等待 {wait_time} 秒...")
    time.sleep(wait_time)
    
    # 關閉當前瀏覽器實例
    try:
        driver.quit()
        logging.info("已關閉瀏覽器")
        print("✓ 已關閉瀏覽器，準備重新啟動...")
    except Exception as e:
        logging.error(f"關閉瀏覽器時出錯: {str(e)}")
        print(f"❌ 關閉瀏覽器時出錯: {str(e)}")
    
    # 直接返回False，讓調用函數知道需要重新初始化瀏覽器
    return False

def search_google(driver, search_query):
    """在Google上搜尋指定查詢詞，使用更人性化的方式"""
    try:
        # 直接構造搜尋URL
        search_url = f"https://www.google.com/search?q={search_query}"
        logging.info(f"正在直接訪問Google搜尋結果頁面: {search_url}")
        driver.get(search_url)
        
        # 隨機等待，模擬人類行為
        time.sleep(random.uniform(1.0, 3.0))
        
        # 檢查是否有驗證碼
        if check_for_captcha(driver):
            # 如果檢測到驗證碼，handle_captcha會關閉瀏覽器並返回False
            return handle_captcha(driver)
        
        # 等待搜尋結果加載，增加等待時間
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "search"))
        )
        
        # 隨機滾動頁面
        random_scroll(driver)
        
        return True
            
    except TimeoutException:
        logging.error("等待搜尋結果頁面加載超時")
        print("❌ 等待搜尋結果頁面加載超時，可能是網絡問題或Google頁面結構變化")
        return False
            
    except Exception as e:
        logging.error(f"搜尋過程中發生錯誤: {str(e)}")
        print(f"❌ 搜尋過程中發生錯誤: {str(e)}")
        return False


def find_keyword_on_page(driver, target_keyword):
    """在當前頁面查找目標關鍵字，添加更多人為行為"""
    # 檢查是否有驗證碼
    if check_for_captcha(driver):
        # 如果檢測到驗證碼，handle_captcha會關閉瀏覽器並返回False
        return handle_captcha(driver)
    
    # 隨機滾動頁面，模擬閱讀行為
    for _ in range(random.randint(1, 3)):
        random_scroll(driver)
    
    # 獲取頁面內容
    page_source = driver.page_source.lower()
    keyword_lower = target_keyword.lower()
    
    if keyword_lower in page_source:
        logging.info(f"在當前頁面找到關鍵字 '{target_keyword}'")
        print(f"✓ 在當前頁面找到關鍵字 '{target_keyword}'!")
        
        # 嘗試找出包含關鍵字的元素並高亮顯示
        try:
            # 使用XPath查找包含關鍵字的元素
            elements = driver.find_elements(By.XPATH, 
                f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword_lower}')]")
            
            if elements:
                # 隨機選擇一個元素進行高亮（更像人類行為）
                highlight_element = elements[min(random.randint(0, len(elements)-1), 2)]  # 最多取前3個中的一個
                
                # 移動到元素位置
                actions = ActionChains(driver)
                actions.move_to_element(highlight_element).pause(random.uniform(0.3, 1.0)).perform()
                
                # 高亮顯示元素
                driver.execute_script(
                    "arguments[0].style.border='3px solid red';", 
                    highlight_element
                )
                # 平滑滾動到該元素
                driver.execute_script(
                    "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", 
                    highlight_element
                )
                logging.info(f"找到 {len(elements)} 個包含關鍵字的元素")
                print(f"找到 {len(elements)} 個包含關鍵字的元素")
        except Exception as e:
            logging.warning(f"高亮顯示元素時出錯: {e}")
            print(f"高亮顯示元素時出錯: {e}")
            
        return True
    else:
        logging.info(f"當前頁面未找到關鍵字 '{target_keyword}'")
        print(f"✗ 當前頁面未找到關鍵字 '{target_keyword}'")
        return False


def find_and_click_result(driver, target_keyword):
    """在搜尋結果中查找包含特定關鍵字的鏈接，點擊並在指定時間後返回"""
    # 檢查是否有驗證碼
    if check_for_captcha(driver):
        # 如果檢測到驗證碼，handle_captcha會關閉瀏覽器並返回False
        return handle_captcha(driver)
    
    # 隨機滾動頁面，模擬閱讀行為
    for _ in range(random.randint(1, 3)):
        random_scroll(driver)
    
    try:
        # 使用XPath查找包含關鍵字的搜尋結果鏈接
        # 這裡使用Google搜尋結果的常見結構，可能需要根據Google的變化進行調整
        result_links = driver.find_elements(By.XPATH, 
            f"//div[@id='search']//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{target_keyword.lower()}')]")
        
        if not result_links:
            logging.info(f"未找到包含關鍵字 '{target_keyword}' 的搜尋結果鏈接")
            print(f"✗ 未找到包含關鍵字 '{target_keyword}' 的搜尋結果鏈接")
            return False
        
        # 選擇第一個匹配的結果
        target_link = result_links[0]
        
        # 記錄當前窗口句柄，以便之後返回
        current_window = driver.current_window_handle
        
        # 移動到元素位置並高亮
        actions = ActionChains(driver)
        actions.move_to_element(target_link).pause(random.uniform(0.3, 1.0)).perform()
        
        driver.execute_script(
            "arguments[0].style.border='3px solid red';", 
            target_link
        )
        
        # 平滑滾動到該元素
        driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", 
            target_link
        )
        
        logging.info(f"找到包含關鍵字 '{target_keyword}' 的搜尋結果鏈接，準備點擊")
        print(f"✓ 找到包含關鍵字 '{target_keyword}' 的搜尋結果鏈接，準備點擊")
        
        # 隨機等待，模擬人類思考時間
        time.sleep(random.uniform(1.0, 2.0))
        
        # 點擊鏈接（在新標籤頁中打開）
        # 使用JavaScript點擊，避免可能的元素遮擋問題
        try:
            # 嘗試多種點擊方法，確保點擊成功
            try:
                # 方法1：使用JavaScript點擊
                driver.execute_script("arguments[0].click();", target_link)
            except Exception as click_error:
                logging.warning(f"JavaScript點擊失敗，嘗試其他方法: {str(click_error)}")
                try:
                    # 方法2：使用ActionChains點擊
                    ActionChains(driver).move_to_element(target_link).click().perform()
                except Exception as action_error:
                    logging.warning(f"ActionChains點擊失敗，嘗試直接點擊: {str(action_error)}")
                    # 方法3：直接點擊
                    target_link.click()
            
            # 等待新標籤頁打開
            WebDriverWait(driver, 3).until(EC.number_of_windows_to_be(2))
            
            # 切換到新打開的標籤頁
            new_window = [window for window in driver.window_handles if window != current_window][0]
            driver.switch_to.window(new_window)
            
            # 等待頁面加載
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            logging.info(f"已點擊並進入包含關鍵字 '{target_keyword}' 的頁面")
            print(f"✓ 已點擊並進入包含關鍵字 '{target_keyword}' 的頁面")
            
            # 在新頁面執行向下滾動，然後停留5秒
            logging.info("在新頁面執行向下滾動至底部，然後停留 5 秒")
            print("在新頁面執行向下滾動至底部，然後停留 5 秒...")
            
            # v21: Initial full scroll, then iterative partial viewport scrolls with pauses and checks
            logging.info("Attempting to scroll (v21 - INITIAL FULL SCROLL, THEN ITERATIVE PARTIAL VIEWPORT SCROLLS)...")
            print("Attempting to scroll (v21 - INITIAL FULL SCROLL, THEN ITERATIVE PARTIAL VIEWPORT SCROLLS)...")

            bottom_tolerance_px = 15
            scroll_completed_successfully = False

            # --- Part 1: Initial Full Scroll --- 
            initial_pause_s = 4.0
            logging.info(f"Part 1: Initial full scroll to document.body.scrollHeight, then pausing for {initial_pause_s}s.")
            print(f"Part 1: Initial full scroll, then pausing for {initial_pause_s}s.")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(initial_pause_s)

            # Check if already at bottom after initial scroll
            current_y = driver.execute_script("return window.pageYOffset || document.documentElement.scrollTop;")
            page_h = driver.execute_script("return document.body.scrollHeight;")
            viewport_h = driver.execute_script("return window.innerHeight;")
            if (current_y + viewport_h >= page_h - bottom_tolerance_px):
                logging.info("Part 1: Already at bottom after initial full scroll. Scroll complete.")
                print("✓ Part 1: Already at bottom after initial full scroll. Scroll complete.")
                scroll_completed_successfully = True
            else:
                logging.info(f"Part 1: Not yet at bottom. Y={current_y}, PageH={page_h}, ViewportH={viewport_h}. Proceeding to iterative scrolls.")
                print(f"Part 1: Not yet at bottom. Proceeding to iterative scrolls.")

            # --- Part 2: Iterative Partial Viewport Scrolls --- 
            if not scroll_completed_successfully:
                max_iterative_attempts = 10
                iterative_pause_s = 3.0
                last_iterative_y = -1
                consecutive_y_unchanged = 0
                logging.info(f"Part 2: Starting iterative scrolls (max {max_iterative_attempts} attempts, pause {iterative_pause_s}s each).")
                print(f"Part 2: Starting iterative scrolls...")

                for attempt in range(max_iterative_attempts):
                    current_y = driver.execute_script("return window.pageYOffset || document.documentElement.scrollTop;")
                    page_h = driver.execute_script("return document.body.scrollHeight;")
                    viewport_h = driver.execute_script("return window.innerHeight;")
                    scroll_step_px = int(viewport_h / 3) # Scroll by a third of the viewport
                    if scroll_step_px < 100: scroll_step_px = 100 # Minimum scroll step

                    logging.info(f"  Iterative Attempt {attempt + 1}/{max_iterative_attempts}: Y={current_y}, PageH={page_h}, ViewportH={viewport_h}. Scrolling by {scroll_step_px}px.")
                    print(f"  Iterative Attempt {attempt + 1}/{max_iterative_attempts}: Y={current_y}, PageH={page_h}. Scrolling by {scroll_step_px}px...")

                    if (current_y + viewport_h >= page_h - bottom_tolerance_px):
                        logging.info("  Iterative: Visually at or very near bottom. Scroll complete.")
                        print("  ✓ Iterative: Visually at or very near bottom. Scroll complete.")
                        scroll_completed_successfully = True
                        break

                    driver.execute_script(f"window.scrollBy(0, {scroll_step_px});")
                    logging.info(f"  Iterative Attempt {attempt + 1}: Pausing for {iterative_pause_s}s...")
                    print(f"  Iterative Attempt {attempt + 1}: Pausing for {iterative_pause_s}s...")
                    time.sleep(iterative_pause_s)

                    y_after_iterative_scroll = driver.execute_script("return window.pageYOffset || document.documentElement.scrollTop;")
                    if y_after_iterative_scroll == current_y: # If scrollBy didn't change Y (and not at bottom)
                        consecutive_y_unchanged += 1
                        logging.info(f"  Iterative: Y position unchanged ({y_after_iterative_scroll}) for {consecutive_y_unchanged} attempt(s).")
                        print(f"  Iterative: Y position unchanged for {consecutive_y_unchanged} attempt(s).")
                        if consecutive_y_unchanged >= 1: # If stuck for one attempt
                            logging.warning("  Iterative: Y position stable. Attempting one final full scroll.")
                            print("  ⚠️ Iterative: Y position stable. Attempting one final full scroll...")
                            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                            time.sleep(3.0)
                            scroll_completed_successfully = True # Assume this works
                            break
                    else:
                        consecutive_y_unchanged = 0
                    last_iterative_y = y_after_iterative_scroll
                
                if not scroll_completed_successfully and attempt == max_iterative_attempts -1:
                    logging.info(f"Part 2: Max iterative attempts ({max_iterative_attempts}) reached.")
                    print(f"Part 2: Max iterative attempts reached.")

            # --- Part 3: Final Failsafe Scroll --- 
            if not scroll_completed_successfully:
                final_failsafe_pause_s = 3.0
                logging.warning(f"Part 3: Scroll not confirmed complete. Performing final failsafe scroll to document.body.scrollHeight and pausing for {final_failsafe_pause_s}s.")
                print(f"⚠️ Part 3: Final failsafe scroll to bottom and pausing for {final_failsafe_pause_s}s...")
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(final_failsafe_pause_s)

            final_scroll_y_pos = driver.execute_script("return window.pageYOffset || document.documentElement.scrollTop;")
            final_page_h = driver.execute_script("return document.body.scrollHeight;") # Added semicolon for consistency
            final_viewport_h = driver.execute_script("return window.innerHeight;") # Get viewport height

            logging.info(f"Finished scrolling process (v21). Final Y: {final_scroll_y_pos}, PageH: {final_page_h}, ViewportH: {final_viewport_h}")
            print(f"✓ Finished scrolling process (v21). Final Y: {final_scroll_y_pos}, PageH: {final_page_h}, ViewportH: {final_viewport_h}")

            # Explicitly confirm if scrolled to bottom before the 5-second pause
            if (final_scroll_y_pos + final_viewport_h >= final_page_h - bottom_tolerance_px):
                logging.info(f"CONFIRMED: Page scrolled to bottom (Y+VH: {final_scroll_y_pos + final_viewport_h} >= PageH-Tol: {final_page_h - bottom_tolerance_px}).")
                print(f"✓ CONFIRMED: Page scrolled to bottom.")
            else:
                # This case should ideally not be hit if scrolling logic is robust, but good for diagnostics
                logging.warning(f"WARNING: Page may not be fully at bottom despite all efforts (Y+VH: {final_scroll_y_pos + final_viewport_h} < PageH-Tol: {final_page_h - bottom_tolerance_px}).")
                print(f"⚠️ WARNING: Page may not be fully at bottom despite all efforts.")

            # --- START: Added simple guaranteed scroll on target page ---
            logging.info("Performing additional simple scrolls on the target page...")
            print("🔄 Performing additional simple scrolls on the target page...")
            try:
                for _ in range(random.randint(2, 4)): # Scroll 2 to 4 times
                    scroll_amount = driver.execute_script("return window.innerHeight * random.uniform(0.6, 0.9);", random.uniform(0.6,0.9)) # Scroll 60-90% of viewport
                    driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                    time.sleep(random.uniform(0.7, 1.8)) # Human-like pause
                # Optionally scroll to top and then partway down for more human-like interaction
                # driver.execute_script("window.scrollTo(0, 0);"); time.sleep(random.uniform(0.4, 0.8))
                # driver.execute_script("window.scrollBy(0, document.body.scrollHeight * 0.15);"); time.sleep(random.uniform(0.4,0.8))
                logging.info("Finished additional simple scrolls on target page.")
                print("✓ Finished additional simple scrolls on target page.")
            except Exception as e_simple_scroll:
                logging.warning(f"Error during additional simple scroll on target page: {str(e_simple_scroll)}")
                print(f"⚠️ Error during additional simple scroll on target page: {str(e_simple_scroll)}")
            # --- END: Added simple guaranteed scroll on target page ---
            
            # 明確停留5秒 AFTER all scrolling attempts and confirmation
            logging.info("Now pausing for 5 seconds after scrolling and confirmation.")
            print("Now pausing for 5 seconds after scrolling and confirmation...")
            time.sleep(5)
            
            # 關閉當前標籤頁並返回搜尋結果頁
            driver.close()
            driver.switch_to.window(current_window)
            
            logging.info("已返回搜尋結果頁")
            print("✓ 已返回搜尋結果頁")
            
            return True
            
        except Exception as click_exception:
            logging.error(f"點擊鏈接失敗: {str(click_exception)}")
            print(f"❌ 點擊鏈接失敗: {str(click_exception)}")
            return False
        
    except Exception as e:
        logging.error(f"點擊搜尋結果時出錯: {str(e)}")
        print(f"❌ 點擊搜尋結果時出錯: {str(e)}")
        
        # 嘗試返回搜尋結果頁
        try:
            if len(driver.window_handles) > 1:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
        except:
            pass
            
        return False


def go_to_next_page(driver):
    """點擊下一頁按鈕，添加更多人為行為，並識別最後一頁的情況"""
    # 檢查是否有驗證碼
    if check_for_captcha(driver):
        # 如果檢測到驗證碼，handle_captcha會關閉瀏覽器並返回False
        return handle_captcha(driver)

    # --- START: Added scrolling before finding next button ---
    logging.info("Scrolling down before trying to find 'Next' button...")
    print("🔄 Scrolling down to find 'Next' button...")
    try:
        # Scroll down a few times to ensure 'Next' button is loaded/visible
        last_height = driver.execute_script("return document.body.scrollHeight")
        for i in range(3): # Scroll up to 3 times
            driver.execute_script("window.scrollBy(0, window.innerHeight * 0.8);") # Scroll 80% of viewport height
            time.sleep(random.uniform(0.5, 1.5)) # Short pause
            new_height = driver.execute_script("return document.body.scrollHeight")
            current_y = driver.execute_script("return window.pageYOffset || document.documentElement.scrollTop;")
            viewport_h = driver.execute_script("return window.innerHeight;")
            
            if new_height == last_height and (current_y + viewport_h >= new_height - 20): # Allow small tolerance for "bottom"
                logging.info(f"Scroll iteration {i+1}: Page height {new_height} unchanged and near bottom (Y:{current_y}, VH:{viewport_h}). Assuming end of scrollable content.")
                print(f"✓ Scroll iteration {i+1}: Page height unchanged and near bottom.")
                break
            elif new_height == last_height:
                 logging.info(f"Scroll iteration {i+1}: Page height {new_height} unchanged but not at bottom. Continuing scroll.")
                 print(f"ⓘ Scroll iteration {i+1}: Page height unchanged but not at bottom. Continuing scroll.")
            last_height = new_height
        
        # One final scroll to the very bottom
        logging.info("Attempting final scroll to document.body.scrollHeight to ensure 'Next' button is visible.")
        print("🔄 Attempting final scroll to document.body.scrollHeight.")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(1.0, 2.5)) # Pause after final scroll
        
        # Additional short scroll up and down to trigger lazy loaded elements if any
        driver.execute_script("window.scrollBy(0, -100);") # Scroll up a bit
        time.sleep(random.uniform(0.2, 0.5))
        driver.execute_script("window.scrollBy(0, 100);") # Scroll down again
        time.sleep(random.uniform(0.2, 0.5))

        logging.info("Finished scrolling before 'Next' button search.")
        print("✓ Finished scrolling before 'Next' button search.")
    except Exception as scroll_err:
        logging.warning(f"Error during pre-scroll in go_to_next_page: {str(scroll_err)}")
        print(f"⚠️ Error during pre-scroll in go_to_next_page: {str(scroll_err)}")
    # --- END: Added scrolling ---
    
    try:
        # 檢查是否有「沒有找到結果」或「已經是最後一頁」的指示
        try:
            # 檢查是否有「沒有找到結果」的訊息
            no_results = driver.find_elements(By.XPATH, "//div[contains(text(), '沒有找到') or contains(text(), '找不到') or contains(text(), 'No results found')]")
            if no_results:
                logging.info("搜尋結果頁面顯示沒有找到結果，視為已到達最後一頁")
                print("搜尋結果頁面顯示沒有找到結果，視為已到達最後一頁")
                return False
        except Exception as e:
            logging.warning(f"檢查'沒有找到結果'訊息時出錯: {str(e)}")
            # 繼續執行，不中斷流程
        
        # 使用多種選擇器嘗試找到下一頁按鈕，並加入重試機制
        next_button = None
        MAX_NEXT_BUTTON_RETRIES = 3  # 最多重試3次尋找按鈕
        
        selectors = [
            (By.ID, "pnnext"),
            (By.XPATH, "//a[@id='pnnext']"),
            (By.XPATH, "//span[text()='下一頁']/parent::a | //span[text()='下一页']/parent::a"), # Added '下一页' for simplified Chinese
            (By.XPATH, "//span[text()='Next']/parent::a"),
            (By.XPATH, "//a[.//span[text()='下一頁'] or .//span[text()='下一页'] or .//span[text()='Next']]"), # More robust span check
            (By.XPATH, "//a[contains(@aria-label, '下一頁') or contains(@aria-label, 'Next page') or contains(@aria-label, '下一页')]"), # Check aria-label
            (By.CSS_SELECTOR, "a#pnnext"),
            (By.CSS_SELECTOR, "a[aria-label*='Next'], a[aria-label*='下一頁'], a[aria-label*='下一页']"),
            (By.XPATH, "//a[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'next') and (contains(@role,'button') or contains(@class,'nav'))]"), # More generic text and role/class based
            (By.XPATH, "//a[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '下一頁') and (contains(@role,'button') or contains(@class,'nav'))]"),
            (By.XPATH, "//a[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '下一页') and (contains(@role,'button') or contains(@class,'nav'))]"),
            (By.XPATH, "//a[contains(@class, 'next') or contains(@class, 'pnnext') or contains(@id, 'pnnext') or contains(@data-ved)]") # Broader class/id/data-ved based
        ]

        for attempt in range(MAX_NEXT_BUTTON_RETRIES):
            logging.info(f"正在進行第 {attempt + 1}/{MAX_NEXT_BUTTON_RETRIES} 次下一頁按鈕查找...")
            print(f"🔄 正在進行第 {attempt + 1}/{MAX_NEXT_BUTTON_RETRIES} 次下一頁按鈕查找...")
            
            for selector_type, selector_value in selectors:
                try:
                    buttons = driver.find_elements(selector_type, selector_value)
                    if buttons:
                        for btn in buttons:
                            if btn.is_displayed() and btn.is_enabled():
                                btn_text = "".join(btn.text.lower().split()) # Normalize spaces
                                btn_aria_label = btn.get_attribute("aria-label").lower() if btn.get_attribute("aria-label") else ""
                                
                                is_next_button_text = any(kw in btn_text for kw in ["next", "下一頁", "下一页"])
                                is_next_button_aria = any(kw in btn_aria_label for kw in ["next", "下一頁", "下一页", "next page"])
                                is_pnnext_id = (selector_type == By.ID and selector_value == "pnnext") or (hasattr(btn, 'get_attribute') and btn.get_attribute('id') == 'pnnext')
                                
                                if is_next_button_text or is_next_button_aria or is_pnnext_id:
                                    next_button = btn
                                    logging.info(f"使用選擇器 {selector_type}:{selector_value} 找到可互動的下一頁按鈕 (嘗試 {attempt + 1}) [{btn_text if btn_text else btn_aria_label}]")
                                    print(f"✓ 使用選擇器 {selector_type}:{selector_value} 找到下一頁按鈕 (嘗試 {attempt + 1})")
                                    break  # Found a suitable button
                        if next_button:
                            break  # Break from selectors loop
                except NoSuchElementException:
                    logging.debug(f"選擇器 {selector_type}:{selector_value} 未找到元素 (嘗試 {attempt + 1})")
                except Exception as e:
                    logging.debug(f"使用選擇器 {selector_type}:{selector_value} 查找下一頁按鈕時出錯 (嘗試 {attempt + 1}): {str(e)}")
                
            if next_button:
                break  # Break from retry loop if button found

            if attempt < MAX_NEXT_BUTTON_RETRIES - 1:
                wait_time = random.uniform(1.5 + attempt * 0.5, 2.5 + attempt * 1.0) # Slightly increase wait variance
                logging.info(f"第 {attempt + 1} 次嘗試未找到可互動的下一頁按鈕，等待 {wait_time:.2f} 秒後重試...")
                print(f"⚠️ 第 {attempt + 1} 次嘗試未找到下一頁按鈕，等待後重試...")
                time.sleep(wait_time)
                try:
                    # A more gentle scroll to avoid disturbing page state too much, but enough to trigger lazy loads
                    driver.execute_script("window.scrollBy(0, Math.min(200, window.innerHeight * 0.3));") 
                    time.sleep(random.uniform(0.3, 0.7))
                    driver.execute_script("window.scrollBy(0, -Math.min(100, window.innerHeight * 0.1));")
                    time.sleep(random.uniform(0.3, 0.7))
                except Exception as scroll_ex:
                    logging.warning(f"重試前滾動失敗: {scroll_ex}")

        if not next_button:
            logging.info(f"嘗試所有選擇器和重試 ({MAX_NEXT_BUTTON_RETRIES} 次) 後仍找不到可互動的下一頁按鈕，可能已到達最後一頁或頁面結構已更改。")
            print(f"❌ 找不到下一頁按鈕（已嘗試 {MAX_NEXT_BUTTON_RETRIES} 次），已到達最後一頁或按鈕無法互動。")
            try:
                # Check for common "end of results" messages again, just in case
                end_messages_selectors = [
                    "//div[contains(text(), '沒有其他結果') or contains(text(), 'end of results') or contains(text(), '顯示的是所有結果') or contains(text(), '已顯示所有搜尋結果')]",
                    "//p[contains(text(), '沒有其他結果') or contains(text(), 'end of results') or contains(text(), '顯示的是所有結果') or contains(text(), '已顯示所有搜尋結果')]",
                    "//*[contains(@class, 'no-results') or contains(@class, 'noMoreResults') or contains(@id, 'noMoreResults')]"
                ]
                for em_selector in end_messages_selectors:
                    if driver.find_elements(By.XPATH, em_selector):
                        logging.info(f"偵測到明確的搜尋結束訊息 via: {em_selector}。")
                        print("ℹ️ 偵測到明確的搜尋結束訊息。")
                        return False # Explicitly return False if end message found
            except Exception as e_msg_ex:
                logging.debug(f"檢查結束訊息時發生錯誤: {e_msg_ex}")
            return False
        
        # 檢查按鈕是否可見和可點擊
        if not next_button.is_displayed() or not next_button.is_enabled():
            logging.info("下一頁按鈕不可見或不可點擊，已到達最後一頁")
            print("下一頁按鈕不可見或不可點擊，已到達最後一頁")
            return False
        
        # 記錄當前URL，用於後續比較
        current_url = driver.current_url
        
        # 隨機滾動到按鈕附近
        driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", 
            next_button
        )
        
        # 隨機等待，模擬人類思考時間
        time.sleep(random.uniform(1.0, 2.5))
        
        # 嘗試多種方式點擊按鈕
        click_success = False
        click_methods = [
            # 方法1：使用ActionChains
            lambda: ActionChains(driver).move_to_element(next_button).pause(random.uniform(0.3, 0.7)).click().perform(),
            # 方法2：使用JavaScript
            lambda: driver.execute_script("arguments[0].click();", next_button),
            # 方法3：直接點擊
            lambda: next_button.click()
        ]
        
        for click_method in click_methods:
            try:
                logging.info("嘗試點擊下一頁...")
                print("點擊下一頁...")
                click_method()
                
                # 等待頁面變化
                try:
                    WebDriverWait(driver, 15).until(
                        EC.staleness_of(next_button)
                    )
                    click_success = True
                    break
                except TimeoutException:
                    # 如果頁面沒有變化，嘗試檢查URL是否變化
                    new_url = driver.current_url
                    if new_url != current_url:
                        click_success = True
                        break
                    logging.warning("點擊後頁面沒有變化，嘗試其他點擊方法")
            except Exception as e:
                logging.warning(f"點擊方法失敗: {str(e)}，嘗試其他方法")
                continue
        
        if not click_success:
            logging.warning("所有點擊方法都失敗，可能已到達最後一頁")
            print("無法點擊下一頁按鈕，可能已到達最後一頁")
            return False
        
        # 頁面加載後的隨機等待
        time.sleep(random.uniform(1.5, 3.0))
        
        # 檢查點擊後的URL是否變化，確認是否真的前進到下一頁
        new_url = driver.current_url
        if new_url != current_url:
            logging.info(f"成功前進到下一頁: {new_url}")
            print(f"成功前進到下一頁: {new_url}")
            return True
        else:
            logging.warning("點擊後URL沒有變化，可能未成功前進到下一頁")
            print("點擊後URL沒有變化，可能未成功前進到下一頁")
            return False
            
    except NoSuchElementException:
        logging.info("沒有更多頁面或找不到下一頁按鈕")
        print("沒有更多頁面或找不到下一頁按鈕，已到達最後一頁")
        return False
    except TimeoutException:
        logging.warning("等待頁面加載超時")
        print("等待頁面加載超時，視為已到達最後一頁")
        # 超時可能意味著已經是最後一頁或出現其他問題，返回False以避免卡住
        return False
    except ElementNotInteractableException:
        logging.warning("無法點擊下一頁按鈕")
        print("無法點擊下一頁按鈕，可能被其他元素遮擋或已到達最後一頁")
        return False
    except Exception as e:
        logging.error(f"前往下一頁時出現未預期的錯誤: {str(e)}")
        print(f"前往下一頁時出現未預期的錯誤: {str(e)}，視為已到達最後一頁")
        # 任何未預期的錯誤都視為已到達最後一頁，避免卡住
        return False


def main():
    # 設定固定的搜尋詞和目標關鍵字
    search_query = "123"
    # target_keyword = "人力銀行"
    target_keywords = []
    max_pages = 10  # 默認最多搜尋10頁

    if len(sys.argv) < 3:
        print("使用方法: python google_keyword_search.py [搜尋詞] [目標關鍵字1] [目標關鍵字2] ... [最大頁數(可選)]")
        print("例如: python google_keyword_search.py \"Python 教學\" \"Django\" \"Flask\" 5")
        # 使用預設值進行演示
        search_query = "AI 工具"
        target_keywords = ["ChatGPT", "Midjourney", "Copilot"]
        print(f"\n未提供足夠參數，將使用預設搜尋詞: '{search_query}' 和目標關鍵字: {target_keywords}")
    else:
        search_query = sys.argv[1]
        # 最後一個參數可能是頁數
        if sys.argv[-1].isdigit():
            target_keywords = sys.argv[2:-1]
            try:
                max_pages = int(sys.argv[-1])
            except ValueError:
                print(f"警告: 無效的頁數參數 '{sys.argv[-1]}'，將使用預設值 {max_pages}")
                # 如果頁數參數無效，則將其視為關鍵字
                target_keywords = sys.argv[2:]
        else:
            target_keywords = sys.argv[2:]

    if not target_keywords:
        print("錯誤: 未指定目標關鍵字。")
        return
    
    print(f"搜尋詞: {search_query}")
    print(f"目標關鍵字列表: {target_keywords}")
    print(f"最大搜尋頁數 (對每個關鍵字): {max_pages}")
    print("注意: 當找到包含目標關鍵字的結果時，將點擊進入該頁面並停留10秒後返回，然後繼續搜尋下一個關鍵字")
    
    driver = None  # 初始化 driver 為 None
    initial_search_successful = False
    
    while not initial_search_successful:
        try:
            # 初始化瀏覽器
            logging.info("初始化瀏覽器...")
            driver = setup_driver()
            
            # 在Google上搜尋
            print("\n正在訪問Google...")
            if not search_google(driver, search_query):
                print("搜尋初始化失敗，將在10秒後重試...")
                if driver:
                    driver.quit()
                time.sleep(10) # 等待10秒
                continue # 重新開始迴圈，再次嘗試初始化和搜尋
            
            initial_search_successful = True # 首次搜尋成功
            
        except Exception as e:
            logging.error(f"初始化或首次搜尋過程中發生錯誤: {str(e)}")
            print(f"\n❌ 初始化或首次搜尋過程中發生錯誤: {str(e)}")
            if proxy_manager and current_proxy: # 確保 current_proxy 不是 None
                logging.warning(f"代理 {current_proxy['ip']}:{current_proxy['port']} 在初始化或首次搜尋過程中發生錯誤，將其移除")
                print(f"⚠️ 代理 {current_proxy['ip']}:{current_proxy['port']} 在初始化或首次搜尋過程中發生錯誤，將其移除")
                proxy_manager.remove_proxy(current_proxy)
            if driver:
                driver.quit()
            print("將在10秒後重試...")
            time.sleep(10) # 等待10秒
            continue # 重新開始迴圈

    # 首次搜尋成功後，繼續執行後續的頁面搜尋邏輯
    all_keywords_processed = True
    for current_target_keyword in target_keywords:
        print(f"\n{'='*20} 開始處理目標關鍵字: {current_target_keyword} {'='*20}")
        
        # 每次處理新的關鍵字時，如果不是第一次（即 driver 已經初始化），
        # 重新執行搜尋，確保是針對當前關鍵字的搜尋上下文
        # 但由於我們的 search_query 是固定的，這裡主要確保我們在 Google 搜尋結果首頁開始
        # 如果 driver 已經存在，我們需要重新導向到搜尋頁面
        if driver.current_url != f"https://www.google.com/search?q={search_query}":
            print(f"\n為關鍵字 '{current_target_keyword}' 重新導向至Google搜尋頁面...")
            if not search_google(driver, search_query):
                print(f"為關鍵字 '{current_target_keyword}' 重新搜尋失敗，跳過此關鍵字...")
                all_keywords_processed = False
                continue
        else:
            # 如果已經在搜尋結果頁，可能需要刷新或確保是第一頁
            # 為了簡化，我們假設 search_google 函數會處理好初始搜尋狀態
            # 或者，如果我們總是從 search_google 開始一個新的關鍵字搜尋，則不需要此else
            pass 

        try:
            page_num = 1
            found_current_keyword = False
            clicked_current_keyword = False
            retry_count = 0
            max_retries = 2
            captcha_retry_count = 0
            max_captcha_retries = 3  # 最多重試3次
            
            while page_num <= max_pages:
                logging.info(f"正在為 '{current_target_keyword}' 搜尋第 {page_num} 頁")
                print(f"\n正在為 '{current_target_keyword}' 搜尋第 {page_num} 頁...")
                
                # 在當前頁面查找關鍵字
                found_current_keyword = find_keyword_on_page(driver, current_target_keyword, proxy_manager, current_proxy)
                
                # 如果返回False且driver已關閉，可能是遇到了驗證碼
                if found_current_keyword is False and (driver is None or not driver.service.is_connectable()):
                    logging.warning(f"檢測到驗證碼，瀏覽器已關閉，準備重新啟動 (嘗試 {captcha_retry_count+1}/{max_captcha_retries})")
                    print(f"\n檢測到驗證碼，瀏覽器已關閉，準備重新啟動 (嘗試 {captcha_retry_count+1}/{max_captcha_retries})")
                    
                    # handle_captcha 內部已經處理了移除代理的邏輯
                    # 確保舊的瀏覽器已關閉
                    try:
                        if driver:
                            driver.quit()
                    except:
                        pass
                    
                    # 等待一段時間後重新啟動瀏覽器
                    wait_time = random.uniform(5.0, 10.0)
                    print(f"等待 {wait_time:.1f} 秒後重新啟動瀏覽器...")
                    time.sleep(wait_time)
                    
                    captcha_retry_count += 1
                    if captcha_retry_count <= max_captcha_retries:
                        # 重新初始化瀏覽器
                        try:
                            driver, current_proxy = setup_driver(proxy_manager) # 更新 current_proxy
                            if driver is None:
                                print("瀏覽器重新啟動失敗，跳過當前關鍵字...")
                                break # 跳出循環，處理下一個關鍵字
                            # 重新搜尋
                            if search_google(driver, search_query, proxy_manager, current_proxy):
                                print("瀏覽器重新啟動成功，繼續搜尋...")
                                page_num = 1  # 重置頁碼
                                # continue # 同上，這裡的 continue 會重新開始 page_num 循環
                                # 此處 break 是為了跳出 while page_num <= max_pages
                                # 修正：如果翻頁時 captcha，應該是 continue 當前 page_num 循環，或者重試當前頁
                                continue # 重新開始當前 page_num 的嘗試
                            else:
                                print("瀏覽器重新啟動後搜尋失敗，跳過當前關鍵字...")
                                break  # 跳出循環，處理下一個關鍵字
                        except Exception as e:
                            logging.error(f"重新啟動瀏覽器時出錯: {str(e)}")
                            print(f"❌ 重新啟動瀏覽器時出錯: {str(e)}")
                            break  # 跳出循環，處理下一個關鍵字
                    else:
                        logging.error(f"驗證碼重試次數已達上限 ({max_captcha_retries})，跳過當前關鍵字")
                        print(f"\n❌ 驗證碼重試次數已達上限 ({max_captcha_retries})，跳過當前關鍵字")
                        break  # 跳出循環，處理下一個關鍵字
                
                if found_current_keyword is True:  # 明確檢查是否為True
                    logging.info(f"成功在第 {page_num} 頁找到關鍵字 '{current_target_keyword}'")
                    print(f"成功在第 {page_num} 頁找到關鍵字 '{current_target_keyword}'")
                    
                    # 嘗試點擊包含關鍵字的搜尋結果
                    clicked_current_keyword = find_and_click_result(driver, current_target_keyword)
                    
                    # 如果返回False且driver已關閉，可能是遇到了驗證碼
                    if clicked_current_keyword is False and (driver is None or not driver.service.is_connectable()):
                        logging.warning(f"點擊結果時檢測到驗證碼，瀏覽器已關閉，準備重新啟動 (嘗試 {captcha_retry_count+1}/{max_captcha_retries})")
                        print(f"\n點擊結果時檢測到驗證碼，瀏覽器已關閉，準備重新啟動 (嘗試 {captcha_retry_count+1}/{max_captcha_retries})")
                        
                        # handle_captcha 內部已經處理了移除代理的邏輯
                        # 確保舊的瀏覽器已關閉
                        try:
                            if driver:
                                driver.quit()
                        except:
                            pass
                        
                        # 等待一段時間後重新啟動瀏覽器
                        wait_time = random.uniform(5.0, 10.0)
                        print(f"等待 {wait_time:.1f} 秒後重新啟動瀏覽器...")
                        time.sleep(wait_time)
                        
                        captcha_retry_count += 1
                        if captcha_retry_count <= max_captcha_retries:
                            # 重新初始化瀏覽器
                            try:
                                driver = setup_driver()
                                # 重新搜尋
                                if search_google(driver, search_query):
                                    print("瀏覽器重新啟動成功，繼續搜尋...")
                                    page_num = 1  # 重置頁碼
                                    break  # 跳出內層循環，重新開始搜尋
                                else:
                                    print("瀏覽器重新啟動後搜尋失敗，跳過當前關鍵字...")
                                    break  # 跳出循環，處理下一個關鍵字
                            except Exception as e:
                                logging.error(f"重新啟動瀏覽器時出錯: {str(e)}")
                                print(f"❌ 重新啟動瀏覽器時出錯: {str(e)}")
                                break  # 跳出循環，處理下一個關鍵字
                        else:
                            logging.error(f"驗證碼重試次數已達上限 ({max_captcha_retries})，跳過當前關鍵字")
                            print(f"\n❌ 驗證碼重試次數已達上限 ({max_captcha_retries})，跳過當前關鍵字")
                            break  # 跳出循環，處理下一個關鍵字
                    
                    if clicked_current_keyword is True:  # 明確檢查是否為True
                        logging.info(f"已成功點擊包含關鍵字 '{current_target_keyword}' 的結果並返回")
                        print(f"已成功點擊包含關鍵字 '{current_target_keyword}' 的結果並返回")
                        # 找到並點擊後，處理下一個關鍵字
                        break # 跳出當前關鍵字的頁面循環
                    else:
                        logging.warning(f"無法點擊包含關鍵字 '{current_target_keyword}' 的結果，繼續搜尋下一頁")
                        print(f"無法點擊包含關鍵字 '{current_target_keyword}' 的結果，繼續搜尋下一頁")
                
                # 如果沒找到或沒成功點擊，且還有下一頁，則繼續
                next_page_result = go_to_next_page(driver, proxy_manager, current_proxy)
                
                # 如果返回False且driver已關閉，可能是遇到了驗證碼
                if next_page_result is False and (driver is None or not driver.service.is_connectable()):
                    logging.warning(f"翻頁時檢測到驗證碼，瀏覽器已關閉，準備重新啟動 (嘗試 {captcha_retry_count+1}/{max_captcha_retries})")
                    print(f"\n翻頁時檢測到驗證碼，瀏覽器已關閉，準備重新啟動 (嘗試 {captcha_retry_count+1}/{max_captcha_retries})")
                    
                    # handle_captcha 內部已經處理了移除代理的邏輯
                    # 確保舊的瀏覽器已關閉
                    try:
                        if driver:
                            driver.quit()
                    except:
                        pass
                    
                    # 等待一段時間後重新啟動瀏覽器
                    wait_time = random.uniform(5.0, 10.0)
                    print(f"等待 {wait_time:.1f} 秒後重新啟動瀏覽器...")
                    time.sleep(wait_time)
                    
                    captcha_retry_count += 1
                    if captcha_retry_count <= max_captcha_retries:
                        # 重新初始化瀏覽器
                        try:
                            driver = setup_driver()
                            # 重新搜尋
                            if search_google(driver, search_query, proxy_manager, current_proxy):
                                print("瀏覽器重新啟動成功，繼續搜尋...")
                                page_num = 1  # 重置頁碼
                                break  # 跳出內層循環，重新開始搜尋
                            else:
                                print("瀏覽器重新啟動後搜尋失敗，跳過當前關鍵字...")
                                break  # 跳出循環，處理下一個關鍵字
                        except Exception as e:
                            logging.error(f"重新啟動瀏覽器時出錯: {str(e)}")
                            print(f"❌ 重新啟動瀏覽器時出錯: {str(e)}")
                            break  # 跳出循環，處理下一個關鍵字
                    else:
                        logging.error(f"驗證碼重試次數已達上限 ({max_captcha_retries})，跳過當前關鍵字")
                        print(f"\n❌ 驗證碼重試次數已達上限 ({max_captcha_retries})，跳過當前關鍵字")
                        break  # 跳出循環，處理下一個關鍵字
                
                if next_page_result is False:  # 正常情況下無法翻頁
                    if retry_count < max_retries:
                        retry_count += 1
                        logging.warning(f"嘗試重新加載頁面並再次查找下一頁按鈕 (嘗試 {retry_count}/{max_retries})")
                        print(f"嘗試重新加載頁面... (嘗試 {retry_count}/{max_retries})")
                        driver.refresh()
                        time.sleep(random.uniform(3.0, 5.0))
                        continue
                    else:
                        logging.info(f"已到達最後一頁或無法找到下一頁按鈕 (針對 '{current_target_keyword}')")
                        print(f"已到達最後一頁 (針對 '{current_target_keyword}')")
                        break
                
                # 重置重試計數
                retry_count = 0
                page_num += 1
                
                # 隨機暫停，避免過快請求
                pause_time = random.uniform(2.0, 4.0)
                logging.info(f"暫停 {pause_time:.1f} 秒後繼續")
                time.sleep(pause_time)
            
            if not found_current_keyword:
                logging.info(f"在搜尋的 {page_num-1} 頁中未找到關鍵字 '{current_target_keyword}'")
                print(f"\n在搜尋的 {page_num-1} 頁中未找到關鍵字 '{current_target_keyword}'")
                all_keywords_processed = False
            elif not clicked_current_keyword:
                logging.info(f"雖然找到關鍵字 '{current_target_keyword}'，但未能成功點擊相關結果")
                print(f"\n雖然找到關鍵字 '{current_target_keyword}'，但未能成功點擊相關結果")
                all_keywords_processed = False
            
            # 每個關鍵字處理完畢後，短暫停頓，準備處理下一個關鍵字或結束
            if target_keywords.index(current_target_keyword) < len(target_keywords) - 1:
                print(f"\n準備處理下一個關鍵字...")
                time.sleep(random.uniform(2.0, 4.0))

        except Exception as e:
            logging.error(f"處理關鍵字 '{current_target_keyword}' 過程中發生錯誤: {str(e)}")
            print(f"\n❌ 處理關鍵字 '{current_target_keyword}' 過程中發生錯誤: {str(e)}")
            all_keywords_processed = False
            # 可以選擇在這裡 continue 到下一個關鍵字，或者 break 整個循環
            # 這裡選擇 continue，嘗試處理剩餘的關鍵字
            continue

    if all_keywords_processed:
        print("\n所有目標關鍵字均已成功處理完畢。")
    else:
        print("\n部分目標關鍵字未能成功處理或找到。")

    # 程式結束前的操作
    try:
        input("\n按Enter鍵退出...")
    except EOFError:
        print("\n輸入被中斷，程式結束")
    except Exception as e:
        print(f"\n輸入過程中發生錯誤: {e}，程式結束")
        
    except KeyboardInterrupt:
        logging.info("用戶中斷程序")
        print("\n程序被用戶中斷")
    except Exception as e:
        logging.error(f"執行過程中發生錯誤: {str(e)}")
        print(f"\n❌ 執行過程中發生錯誤: {str(e)}")
    finally:
        # 關閉瀏覽器
        if driver: # 確保 driver 不是 None 才執行 quit
            logging.info("關閉瀏覽器")
            driver.quit()


if __name__ == "__main__":
    main()