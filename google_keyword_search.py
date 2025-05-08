#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
網頁關鍵字搜尋工具

這個腳本使用Selenium自動化瀏覽器，在Google搜尋結果中尋找特定關鍵字。
如果當前頁面沒有找到關鍵字，會自動翻到下一頁繼續搜尋。
腳本包含防機器人檢測功能，模擬人類行為並處理Google驗證碼。

使用方法:
    python google_keyword_search.py [搜尋詞] [目標關鍵字]

例如:
    python google_keyword_search.py "Python 教學" "Django"
"""

import sys
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementNotInteractableException

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def setup_driver():
    """設置並返回Chrome WebDriver，添加更多人為特徵"""
    chrome_options = Options()
    # 取消下面的註釋可以在背景運行Chrome（無界面模式）
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # 添加更多選項以減少被檢測為機器人的可能性
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # 隨機用戶代理
    user_agents = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:95.0) Gecko/20100101 Firefox/95.0"
    ]
    chrome_options.add_argument(f"--user-agent={random.choice(user_agents)}")
    
    # 初始化WebDriver
    driver = webdriver.Chrome(options=chrome_options)
    
    # 修改navigator.webdriver屬性以避免檢測
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
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
    """處理Google驗證碼"""
    logging.warning("檢測到驗證碼！請手動完成驗證...")
    print("\n⚠️ 檢測到Google驗證碼！")
    print("請在瀏覽器中手動完成驗證，完成後按Enter繼續...")
    try:
        input("按Enter繼續...")
    except EOFError:
        print("\n輸入被中斷，繼續執行...")
    except Exception as e:
        print(f"\n輸入過程中發生錯誤: {e}，繼續執行...")
    
    # 等待用戶完成驗證後，檢查是否成功
    max_wait = 60  # 最多等待60秒
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        if not check_for_captcha(driver):
            logging.info("驗證碼已成功處理")
            print("✓ 驗證碼已成功處理，繼續執行...")
            return True
        time.sleep(2)
    
    logging.error("驗證碼處理超時")
    print("❌ 驗證碼處理超時，請重新運行程序")
    return False

def search_google(driver, search_query):
    """在Google上搜尋指定查詢詞，使用更人性化的方式"""
    try:
        logging.info(f"正在訪問Google搜尋頁面")
        driver.get("https://www.google.com")
        
        # 隨機等待，模擬人類行為
        time.sleep(random.uniform(1.0, 3.0))
        
        # 檢查是否有驗證碼
        if check_for_captcha(driver):
            if not handle_captcha(driver):
                return False
        
        # 等待搜尋框出現，增加等待時間
        try:
            search_box = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.NAME, "q"))
            )
            
            # 隨機移動鼠標到搜尋框
            actions = ActionChains(driver)
            actions.move_to_element(search_box).pause(random.uniform(0.2, 0.8)).click().perform()
            
            # 清空搜尋框（以防有預填內容）
            search_box.clear()
            time.sleep(random.uniform(0.3, 0.7))
            
            # 使用人性化輸入
            logging.info(f"正在輸入搜尋詞: {search_query}")
            human_like_typing(search_box, search_query)
            
            # 隨機暫停後提交
            time.sleep(random.uniform(0.5, 1.5))
            search_box.submit()
            
            # 等待搜尋結果加載，增加等待時間
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "search"))
            )
            
            # 隨機滾動頁面
            random_scroll(driver)
            
            return True
            
        except TimeoutException:
            logging.error("等待搜尋框超時")
            print("❌ 無法找到Google搜尋框，可能是網絡問題或Google頁面結構變化")
            return False
            
    except Exception as e:
        logging.error(f"搜尋過程中發生錯誤: {str(e)}")
        print(f"❌ 搜尋過程中發生錯誤: {str(e)}")
        return False


def find_keyword_on_page(driver, target_keyword):
    """在當前頁面查找目標關鍵字，添加更多人為行為"""
    # 檢查是否有驗證碼
    if check_for_captcha(driver):
        if not handle_captcha(driver):
            return False
    
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
        if not handle_captcha(driver):
            return False
    
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
        driver.execute_script("arguments[0].click();", target_link)
        
        # 等待新標籤頁打開
        WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
        
        # 切換到新打開的標籤頁
        new_window = [window for window in driver.window_handles if window != current_window][0]
        driver.switch_to.window(new_window)
        
        # 等待頁面加載
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        logging.info(f"已點擊並進入包含關鍵字 '{target_keyword}' 的頁面")
        print(f"✓ 已點擊並進入包含關鍵字 '{target_keyword}' 的頁面")
        
        # 在頁面停留指定時間
        stay_time = 5  # 停留5秒
        logging.info(f"在頁面停留 {stay_time} 秒")
        print(f"在頁面停留 {stay_time} 秒...")
        time.sleep(stay_time)
        
        # 關閉當前標籤頁並返回搜尋結果頁
        driver.close()
        driver.switch_to.window(current_window)
        
        logging.info("已返回搜尋結果頁")
        print("✓ 已返回搜尋結果頁")
        
        return True
        
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
    """點擊下一頁按鈕，添加更多人為行為"""
    # 檢查是否有驗證碼
    if check_for_captcha(driver):
        if not handle_captcha(driver):
            return False
    
    try:
        # 尋找下一頁按鈕
        next_button = driver.find_element(By.ID, "pnnext")
        
        # 隨機滾動到按鈕附近
        driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", 
            next_button
        )
        
        # 隨機等待，模擬人類思考時間
        time.sleep(random.uniform(1.0, 2.5))
        
        # 使用ActionChains模擬真實的鼠標移動和點擊
        actions = ActionChains(driver)
        actions.move_to_element(next_button)
        actions.pause(random.uniform(0.3, 0.7))
        actions.click()
        
        logging.info("點擊下一頁...")
        print("點擊下一頁...")
        actions.perform()
        
        # 等待新頁面加載，增加等待時間
        WebDriverWait(driver, 15).until(
            EC.staleness_of(next_button)
        )
        
        # 頁面加載後的隨機等待
        time.sleep(random.uniform(1.5, 3.0))
        
        return True
    except NoSuchElementException:
        logging.info("沒有更多頁面或找不到下一頁按鈕")
        print("沒有更多頁面或找不到下一頁按鈕")
        return False
    except TimeoutException:
        logging.warning("等待頁面加載超時")
        print("等待頁面加載超時，嘗試繼續...")
        # 即使超時也嘗試繼續
        time.sleep(5)
        return True
    except ElementNotInteractableException:
        logging.warning("無法點擊下一頁按鈕")
        print("無法點擊下一頁按鈕，可能被其他元素遮擋")
        return False


def main():
    # 設定固定的搜尋詞和目標關鍵字
    search_query = "123"
    target_keyword = "人力銀行"
    
    # 可選參數：最大頁數
    max_pages = 5  # 默認最多搜尋5頁
    if len(sys.argv) > 1:
        try:
            max_pages = int(sys.argv[1])
        except ValueError:
            print(f"警告: 無效的頁數參數 '{sys.argv[1]}'，使用默認值5")
    
    print(f"搜尋詞: {search_query}")
    print(f"目標關鍵字: {target_keyword}")
    print(f"最大搜尋頁數: {max_pages}")
    print("注意: 當找到包含目標關鍵字的結果時，將點擊進入該頁面並停留5秒後返回")
    
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
            if driver:
                driver.quit()
            print("將在10秒後重試...")
            time.sleep(10) # 等待10秒
            continue # 重新開始迴圈

    # 首次搜尋成功後，繼續執行後續的頁面搜尋邏輯
    try:
        page_num = 1
        found = False
        clicked = False
        retry_count = 0
        max_retries = 2
        
        while page_num <= max_pages:
            logging.info(f"正在搜尋第 {page_num} 頁")
            print(f"\n正在搜尋第 {page_num} 頁...")
            
            # 在當前頁面查找關鍵字
            found = find_keyword_on_page(driver, target_keyword)
            
            if found:
                logging.info(f"成功在第 {page_num} 頁找到關鍵字 '{target_keyword}'")
                print(f"成功在第 {page_num} 頁找到關鍵字 '{target_keyword}'")
                
                # 嘗試點擊包含關鍵字的搜尋結果
                clicked = find_and_click_result(driver, target_keyword)
                
                if clicked:
                    logging.info(f"已成功點擊包含關鍵字 '{target_keyword}' 的結果並返回")
                    print(f"已成功點擊包含關鍵字 '{target_keyword}' 的結果並返回")
                    # 任務完成，結束程式
                    print("任務完成，程式自動結束")
                    break
                else:
                    logging.warning(f"無法點擊包含關鍵字 '{target_keyword}' 的結果，繼續搜尋下一頁")
                    print(f"無法點擊包含關鍵字 '{target_keyword}' 的結果，繼續搜尋下一頁")
            
            # 如果沒找到或沒成功點擊，且還有下一頁，則繼續
            if not go_to_next_page(driver):
                if retry_count < max_retries:
                    retry_count += 1
                    logging.warning(f"嘗試重新加載頁面並再次查找下一頁按鈕 (嘗試 {retry_count}/{max_retries})")
                    print(f"嘗試重新加載頁面... (嘗試 {retry_count}/{max_retries})")
                    driver.refresh()
                    time.sleep(random.uniform(3.0, 5.0))
                    continue
                else:
                    logging.info("已到達最後一頁或無法找到下一頁按鈕")
                    print("已到達最後一頁")
                    break
            
            # 重置重試計數
            retry_count = 0
            page_num += 1
            
            # 隨機暫停，避免過快請求
            pause_time = random.uniform(2.0, 4.0)
            logging.info(f"暫停 {pause_time:.1f} 秒後繼續")
            time.sleep(pause_time)
        
        if not found:
            logging.info(f"在搜尋的 {page_num} 頁中未找到關鍵字 '{target_keyword}'")
            print(f"\n在搜尋的 {page_num} 頁中未找到關鍵字 '{target_keyword}'")
        elif not clicked:
            logging.info(f"雖然找到關鍵字 '{target_keyword}'，但未能成功點擊相關結果")
            print(f"\n雖然找到關鍵字 '{target_keyword}'，但未能成功點擊相關結果")
        
        # 如果成功點擊了結果，直接結束程式，不等待用戶按Enter
        if clicked:
            print("程式執行完成，自動退出")
            return
        else:
            # 如果沒找到關鍵字或沒成功點擊，等待用戶按任意鍵退出
            try:
                input("\n按Enter鍵退出...")
            except EOFError:
                print("\n輸入被中斷，程式結束")
            except Exception as e:
                print(f"\n輸入過程中發生錯誤: {e}，程式結束")
            return
        
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