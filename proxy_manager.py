#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GSA Proxy 管理模塊

這個模塊負責與GSA Proxy軟體整合，獲取代理列表並提供代理輪換功能。
它支持從GSA Proxy導出的代理列表文件讀取代理，或者通過GSA Proxy API獲取代理。

使用方法:
    from proxy_manager import ProxyManager
    
    # 初始化代理管理器
    proxy_manager = ProxyManager(proxy_file_path="proxies.txt")
    
    # 獲取一個代理
    proxy = proxy_manager.get_proxy()
    
    # 標記代理為無效（如果代理不可用）
    proxy_manager.mark_proxy_invalid(proxy)
"""

import os
import random
import logging
import time
import json
import requests
from urllib.parse import urlparse

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class ProxyManager:
    """代理管理器類，負責管理和輪換代理"""
    
    def __init__(self, proxy_file_path=None, gsa_api_url=None, max_failed_attempts=3, refresh_interval=600):
        """
        初始化代理管理器
        
        參數:
            proxy_file_path (str): GSA Proxy導出的代理列表文件路徑
            gsa_api_url (str): GSA Proxy API的URL（如果使用API獲取代理）
            max_failed_attempts (int): 代理失敗嘗試的最大次數
            refresh_interval (int): 刷新代理列表的時間間隔（秒）
        """
        self.proxy_file_path = proxy_file_path
        self.gsa_api_url = gsa_api_url
        self.max_failed_attempts = max_failed_attempts
        self.refresh_interval = refresh_interval
        
        # 代理列表，格式為 {"proxy": "ip:port", "failed_attempts": 0, "last_used": timestamp}
        self.proxies = []
        
        # 上次刷新代理列表的時間
        self.last_refresh_time = 0
        
        # 初始化代理列表
        self.refresh_proxies()
        
    def refresh_proxies(self):
        """刷新代理列表，從文件或API獲取新的代理"""
        current_time = time.time()
        
        # 如果距離上次刷新時間不足刷新間隔，則跳過
        if current_time - self.last_refresh_time < self.refresh_interval and self.proxies:
            return
        
        self.last_refresh_time = current_time
        new_proxies = []
        
        # 優先從文件讀取代理
        if self.proxy_file_path and os.path.exists(self.proxy_file_path):
            try:
                with open(self.proxy_file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        proxy = line.strip()
                        if proxy and self._is_valid_proxy_format(proxy):
                            new_proxies.append({
                                "proxy": proxy,
                                "failed_attempts": 0,
                                "last_used": 0
                            })
                if new_proxies: # 只有成功從文件讀取到代理才打印日誌
                    logging.info(f"從文件 {self.proxy_file_path} 讀取了 {len(new_proxies)} 個代理")
                    print(f"✓ 從文件 {self.proxy_file_path} 讀取了 {len(new_proxies)} 個代理")
                else:
                    logging.warning(f"從文件 {self.proxy_file_path} 未讀取到有效代理，嘗試從API獲取。")
                    print(f"⚠️ 從文件 {self.proxy_file_path} 未讀取到有效代理，嘗試從API獲取。")
            except Exception as e:
                logging.error(f"讀取代理文件 {self.proxy_file_path} 時出錯: {str(e)}，嘗試從API獲取。")
                print(f"❌ 讀取代理文件 {self.proxy_file_path} 時出錯: {str(e)}，嘗試從API獲取。")
        
        # 如果文件讀取失敗或未配置，且配置了API URL，則從API獲取代理
        if not new_proxies and self.gsa_api_url:
            try:
                response = requests.get(self.gsa_api_url, timeout=10)
                if response.status_code == 200:
                    # 假設API返回的是JSON格式的代理列表
                    # 根據實際API調整解析邏輯
                    proxies_data = response.json()
                    for proxy_data in proxies_data:
                        proxy = proxy_data.get("proxy") or f"{proxy_data.get('ip')}:{proxy_data.get('port')}"
                        if proxy and self._is_valid_proxy_format(proxy):
                            new_proxies.append({
                                "proxy": proxy,
                                "failed_attempts": 0,
                                "last_used": 0
                            })
                    logging.info(f"從API獲取了 {len(new_proxies)} 個代理")
                    print(f"✓ 從API獲取了 {len(new_proxies)} 個代理")
                else:
                    logging.error(f"API請求失敗，狀態碼: {response.status_code}")
                    print(f"❌ API請求失敗，狀態碼: {response.status_code}")
            except Exception as e:
                logging.error(f"從API獲取代理時出錯: {str(e)}")
                print(f"❌ 從API獲取代理時出錯: {str(e)}")
        
        # 如果獲取到新代理，則更新代理列表
        if new_proxies:
            # 保留舊代理中未達到最大失敗次數的代理
            valid_old_proxies = [p for p in self.proxies if p["failed_attempts"] < self.max_failed_attempts]
            
            # 合併新舊代理列表，去重
            merged_proxies = {}
            for proxy in valid_old_proxies + new_proxies:
                if proxy["proxy"] not in merged_proxies:
                    merged_proxies[proxy["proxy"]] = proxy
            
            self.proxies = list(merged_proxies.values())
            logging.info(f"代理列表更新完成，當前共有 {len(self.proxies)} 個可用代理")
            print(f"✓ 代理列表更新完成，當前共有 {len(self.proxies)} 個可用代理")
        else:
            logging.warning("未獲取到任何代理")
            print("⚠️ 未獲取到任何代理，請檢查代理來源設置")
    
    def get_proxy(self):
        """獲取一個代理，優先選擇使用次數少的代理"""
        # 刷新代理列表
        self.refresh_proxies()
        
        # 如果沒有可用代理，返回None
        if not self.proxies:
            logging.warning("沒有可用的代理")
            print("⚠️ 沒有可用的代理，將直接連接")
            return None
        
        # 過濾出未達到最大失敗次數的代理
        valid_proxies = [p for p in self.proxies if p["failed_attempts"] < self.max_failed_attempts]
        if not valid_proxies:
            logging.warning("所有代理都已達到最大失敗次數")
            print("⚠️ 所有代理都已達到最大失敗次數，將重置代理列表")
            # 重置所有代理的失敗次數
            for proxy in self.proxies:
                proxy["failed_attempts"] = 0
            valid_proxies = self.proxies
        
        # 按照上次使用時間排序，優先使用最久未使用的代理
        valid_proxies.sort(key=lambda x: x["last_used"])
        
        # 從前50%的代理中隨機選擇一個，避免總是使用同一個代理
        proxy_count = len(valid_proxies)
        selected_index = random.randint(0, min(proxy_count - 1, max(0, int(proxy_count * 0.5))))
        selected_proxy = valid_proxies[selected_index]
        
        # 更新代理的最後使用時間
        selected_proxy["last_used"] = time.time()
        
        logging.info(f"選擇代理: {selected_proxy['proxy']}")
        return selected_proxy["proxy"]

    def remove_proxy(self, proxy_str):
        """從代理列表中移除指定的代理
        
        參數:
            proxy_str (str): 要移除的代理字符串（格式：ip:port）
        """
        if not proxy_str:
            return
            
        # 從列表中移除指定的代理
        self.proxies = [p for p in self.proxies if p["proxy"] != proxy_str]
        logging.info(f"已移除失敗的代理: {proxy_str}")
        print(f"✗ 已移除失敗的代理: {proxy_str}")
        
        # 如果代理列表為空，嘗試刷新
        if not self.proxies:
            logging.warning("代理列表為空，嘗試刷新代理列表")
            print("⚠️ 代理列表為空，嘗試刷新代理列表")
            self.refresh_proxies()
    
    def get_current_proxy_string(self):
        """獲取當前正在使用的代理的字符串表示，如果有的話。"""
        # 這是一個簡化的示例，假設 get_proxy 或 get_next_proxy
        # 會設置一個類似 self.current_proxy 的屬性。
        # 或者，如果我們總是從 self.proxies 中選擇，我們需要一種方式來識別"當前"的那個。
        # 為了簡單起見，如果沒有明確的"當前"代理，我們可以返回最後一個被標記為"last_used"最新的那個。
        if not self.proxies:
            return "無 (列表為空)"
        
        # 查找最近使用的代理
        # 這假設 last_used 時間戳是可靠的
        try:
            # 過濾掉失敗次數過多的代理，除非所有代理都失敗了
            active_proxies = [p for p in self.proxies if p["failed_attempts"] < self.max_failed_attempts]
            if not active_proxies:
                active_proxies = self.proxies # 如果都失敗了，就從所有代理中找
            
            if not active_proxies: # 如果連 self.proxies 都為空
                 return "無 (無有效代理)"

            latest_used_proxy = max(active_proxies, key=lambda p: p.get('last_used', 0), default=None)
            if latest_used_proxy and latest_used_proxy['last_used'] > 0:
                return latest_used_proxy['proxy']
            else:
                # 如果沒有代理被使用過，或者 last_used 都是0
                return "無 (尚未使用或無有效代理)"
        except Exception as e:
            logging.error(f"獲取當前代理字符串時出錯: {e}")
            return "錯誤"

    def get_stats(self):
        """獲取代理使用情況的統計數據"""
        total_proxies_available = len(self.proxies)
        total_failed_attempts = sum(p.get('failed_attempts', 0) for p in self.proxies)
        proxies_maxed_out_failures = sum(1 for p in self.proxies if p.get('failed_attempts', 0) >= self.max_failed_attempts)
        
        # 嘗試獲取 "successful_rotations" - 這需要一個計數器
        # 為了簡化，我們暫時不直接追蹤輪換次數，因為 get_next_proxy 只是選擇一個代理
        # 可以考慮在 get_next_proxy 中增加一個計數器 self.rotations_count
        # 此處的 "proxies_tried_count" 也可以通過類似方式實現，或者基於日誌分析
        
        stats = {
            "total_proxies_available": total_proxies_available,
            "total_failed_attempts_sum": total_failed_attempts, # 所有代理失敗次數的總和
            "proxies_maxed_out_count": proxies_maxed_out_failures, # 達到最大失敗次數的代理數量
            # 以下為之前日誌中期望的鍵名，我們盡量匹配
            "proxies_tried_count": "N/A (未追蹤)", # 需要額外邏輯追蹤
            "successful_rotations": "N/A (未追蹤)", # 需要額外邏輯追蹤
            "failed_attempts_count": total_failed_attempts # 使用總和作為一個指標
        }
        logging.info(f"生成代理統計: {stats}")
        return stats
        
    def get_next_proxy(self):
        """獲取下一個代理，確保每次搜索都使用新的代理"""
        # 刷新代理列表
        self.refresh_proxies()
        
        # 如果沒有可用代理，返回None
        if not self.proxies:
            logging.warning("沒有可用的代理")
            print("⚠️ 沒有可用的代理，將直接連接")
            return None
        
        # 過濾出未達到最大失敗次數的代理
        valid_proxies = [p for p in self.proxies if p["failed_attempts"] < self.max_failed_attempts]
        if not valid_proxies:
            logging.warning("所有代理都已達到最大失敗次數")
            print("⚠️ 所有代理都已達到最大失敗次數，將重置代理列表")
            # 重置所有代理的失敗次數
            for proxy in self.proxies:
                proxy["failed_attempts"] = 0
            valid_proxies = self.proxies
        
        # 隨機選擇一個代理，確保每次搜索都使用不同的代理
        selected_proxy = random.choice(valid_proxies)
        selected_proxy["last_used"] = time.time()
        
        logging.info(f"切換到新代理: {selected_proxy['proxy']}")
        print(f"✓ 切換到新代理: {selected_proxy['proxy']}")
        return selected_proxy["proxy"]
    
    def mark_proxy_invalid(self, proxy):
        """標記代理為無效，增加失敗次數"""
        if not proxy:
            return
            
        for p in self.proxies:
            if p["proxy"] == proxy:
                p["failed_attempts"] += 1
                logging.warning(f"代理 {proxy} 標記為無效，當前失敗次數: {p['failed_attempts']}")
                if p["failed_attempts"] >= self.max_failed_attempts:
                    logging.warning(f"代理 {proxy} 已達到最大失敗次數，將不再使用")
                break
    
    def _is_valid_proxy_format(self, proxy):
        """檢查代理格式是否有效"""
        # 簡單檢查格式是否為 ip:port
        parts = proxy.split(":")
        if len(parts) != 2:
            return False
            
        ip, port = parts
        # 檢查IP格式
        ip_parts = ip.split(".")
        if len(ip_parts) != 4:
            return False
            
        for part in ip_parts:
            try:
                num = int(part)
                if num < 0 or num > 255:
                    return False
            except ValueError:
                return False
                
        # 檢查端口格式
        try:
            port_num = int(port)
            if port_num < 1 or port_num > 65535:
                return False
        except ValueError:
            return False
            
        return True

    def get_proxy_for_selenium(self):
        """獲取適用於Selenium的代理設置"""
        proxy = self.get_proxy()
        if not proxy:
            return None
            
        return f"--proxy-server=http://{proxy}"

# 測試代碼
if __name__ == "__main__":
    # 測試從文件讀取代理
    proxy_manager = ProxyManager(proxy_file_path="proxies.txt")
    proxy = proxy_manager.get_proxy()
    print(f"獲取到代理: {proxy}")
    
    # 測試獲取Selenium代理設置
    selenium_proxy = proxy_manager.get_proxy_for_selenium()
    print(f"Selenium代理設置: {selenium_proxy}")