#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Web Crawler - 网页爬虫程序
功能：抓取网页中的文本内容和图片资源，并进行结构化存储
作者：AI助手
版本：1.0.0
"""

import os
import sys
import re
import time
import hashlib
import logging
import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
import concurrent.futures
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("crawler.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("WebCrawler")

class WebCrawler:
    """网页爬虫类，用于抓取网页内容和图片"""
    
    def __init__(self, base_url, max_pages=10, max_depth=2, timeout=10):
        """
        初始化爬虫
        
        Args:
            base_url (str): 起始URL
            max_pages (int): 最大爬取页面数
            max_depth (int): 最大爬取深度
            timeout (int): 请求超时时间(秒)
        """
        self.base_url = base_url
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.timeout = timeout
        self.visited_urls = set()
        self.image_hashes = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # 创建存储目录
        self.setup_storage()
    
    def setup_storage(self):
        """设置存储目录"""
        # 在用户桌面创建存储目录
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        date_str = datetime.now().strftime("%Y%m%d")
        self.storage_dir = os.path.join(desktop, f"WebCrawlerData_{date_str}")
        
        # 创建文本和图片子目录
        self.text_dir = os.path.join(self.storage_dir, "texts")
        self.image_dir = os.path.join(self.storage_dir, "images")
        
        # 确保目录存在
        os.makedirs(self.text_dir, exist_ok=True)
        os.makedirs(self.image_dir, exist_ok=True)
        
        logger.info(f"存储目录已创建: {self.storage_dir}")
    
    def get_url_hash(self, url):
        """生成URL的哈希值"""
        return hashlib.md5(url.encode('utf-8')).hexdigest()
    
    def get_image_hash(self, image_data):
        """生成图片内容的哈希值"""
        return hashlib.md5(image_data).hexdigest()
    
    def download_page(self, url, depth=0):
        """
        下载并解析网页
        
        Args:
            url (str): 要下载的URL
            depth (int): 当前爬取深度
            
        Returns:
            tuple: (soup对象, 响应对象) 或 (None, None)
        """
        if url in self.visited_urls or len(self.visited_urls) >= self.max_pages or depth > self.max_depth:
            return None, None
        
        try:
            logger.info(f"正在爬取: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            
            self.visited_urls.add(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup, response
        except Exception as e:
            logger.error(f"爬取 {url} 时出错: {str(e)}")
            return None, None
    
    def extract_text(self, soup, url):
        """
        提取网页文本内容
        
        Args:
            soup (BeautifulSoup): 解析后的网页
            url (str): 网页URL
            
        Returns:
            str: 提取的文本内容
        """
        # 移除脚本和样式元素
        for script in soup(["script", "style"]):
            script.extract()
        
        # 获取文本
        text = soup.get_text(separator='\n', strip=True)
        
        # 处理多余的空行
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = '\n'.join(lines)
        
        # 保存文本
        url_hash = self.get_url_hash(url)
        timestamp = int(time.time())
        filename = f"{url_hash}_{timestamp}.txt"
        filepath = os.path.join(self.text_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            # 添加元数据
            f.write(f"URL: {url}\n")
            f.write(f"爬取时间: {datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*50}\n\n")
            f.write(text)
        
        logger.info(f"已保存文本: {filepath}")
        return text
    
    def extract_images(self, soup, base_url):
        """
        提取并下载网页中的图片
        
        Args:
            soup (BeautifulSoup): 解析后的网页
            base_url (str): 基础URL，用于解析相对路径
            
        Returns:
            int: 成功下载的图片数量
        """
        img_tags = soup.find_all('img')
        downloaded_count = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for img in img_tags:
                src = img.get('src')
                if not src:
                    continue
                
                # 处理相对URL
                img_url = urljoin(base_url, src)
                futures.append(executor.submit(self.download_image, img_url))
            
            for future in concurrent.futures.as_completed(futures):
                if future.result():
                    downloaded_count += 1
        
        return downloaded_count
    
    def download_image(self, img_url):
        """
        下载单个图片
        
        Args:
            img_url (str): 图片URL
            
        Returns:
            bool: 下载是否成功
        """
        try:
            response = self.session.get(img_url, timeout=self.timeout)
            response.raise_for_status()
            
            # 检查内容类型
            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                return False
            
            # 计算图片哈希值用于去重
            img_data = response.content
            img_hash = self.get_image_hash(img_data)
            
            # 如果图片已存在，跳过
            if img_hash in self.image_hashes:
                logger.info(f"跳过重复图片: {img_url}")
                return False
            
            self.image_hashes.add(img_hash)
            
            # 生成文件名
            url_hash = self.get_url_hash(img_url)
            timestamp = int(time.time())
            
            # 从URL中提取文件扩展名
            parsed_url = urlparse(img_url)
            path = parsed_url.path
            ext = os.path.splitext(path)[1]
            if not ext or ext.lower() not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
                ext = '.jpg'  # 默认扩展名
            
            filename = f"{url_hash}_{timestamp}{ext}"
            filepath = os.path.join(self.image_dir, filename)
            
            # 保存图片
            with open(filepath, 'wb') as f:
                f.write(img_data)
            
            logger.info(f"已下载图片: {filepath}")
            return True
        except Exception as e:
            logger.error(f"下载图片 {img_url} 时出错: {str(e)}")
            return False
    
    def extract_links(self, soup, base_url):
        """
        提取网页中的链接
        
        Args:
            soup (BeautifulSoup): 解析后的网页
            base_url (str): 基础URL，用于解析相对路径
            
        Returns:
            list: 提取的链接列表
        """
        links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(base_url, href)
            
            # 过滤非HTTP链接和外部链接
            if full_url.startswith(('http://', 'https://')):
                # 确保只爬取同一域名下的页面
                if urlparse(full_url).netloc == urlparse(base_url).netloc:
                    links.append(full_url)
        
        return links
    
    def crawl(self):
        """
        开始爬取网页
        
        Returns:
            dict: 爬取结果统计
        """
        queue = [(self.base_url, 0)]  # (url, depth)
        processed = 0
        
        stats = {
            'pages_crawled': 0,
            'texts_saved': 0,
            'images_downloaded': 0,
            'errors': 0
        }
        
        while queue and len(self.visited_urls) < self.max_pages:
            url, depth = queue.pop(0)
            
            if url in self.visited_urls:
                continue
                
            soup, response = self.download_page(url, depth)
            if soup is None:
                stats['errors'] += 1
                continue
            
            stats['pages_crawled'] += 1
            
            # 提取并保存文本
            self.extract_text(soup, url)
            stats['texts_saved'] += 1
            
            # 提取并下载图片
            img_count = self.extract_images(soup, url)
            stats['images_downloaded'] += img_count
            
            # 如果未达到最大深度，则提取链接并加入队列
            if depth < self.max_depth:
                links = self.extract_links(soup, url)
                for link in links:
                    if link not in self.visited_urls:
                        queue.append((link, depth + 1))
            
            # 简单的延迟，避免请求过快
            time.sleep(1)
        
        return stats

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='网页爬虫 - 抓取网页文本和图片')
    parser.add_argument('url', help='要爬取的起始URL')
    parser.add_argument('-p', '--max-pages', type=int, default=10, help='最大爬取页面数 (默认: 10)')
    parser.add_argument('-d', '--max-depth', type=int, default=2, help='最大爬取深度 (默认: 2)')
    parser.add_argument('-t', '--timeout', type=int, default=10, help='请求超时时间(秒) (默认: 10)')
    parser.add_argument('-v', '--verbose', action='store_true', help='显示详细日志')
    
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_arguments()
    
    # 设置日志级别
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # 创建爬虫实例
    crawler = WebCrawler(
        base_url=args.url,
        max_pages=args.max_pages,
        max_depth=args.max_depth,
        timeout=args.timeout
    )
    
    # 开始爬取
    logger.info("开始爬取...")
    start_time = time.time()
    stats = crawler.crawl()
    end_time = time.time()
    
    # 打印统计信息
    logger.info("爬取完成!")
    logger.info(f"耗时: {end_time - start_time:.2f} 秒")
    logger.info(f"爬取页面数: {stats['pages_crawled']}")
    logger.info(f"保存文本数: {stats['texts_saved']}")
    logger.info(f"下载图片数: {stats['images_downloaded']}")
    logger.info(f"错误数: {stats['errors']}")
    logger.info(f"存储目录: {crawler.storage_dir}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("用户中断，程序退出")
    except Exception as e:
        logger.error(f"程序异常: {str(e)}")
        sys.exit(1)