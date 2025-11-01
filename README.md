# Web Crawler Python

一个功能强大的Python网页爬虫，可抓取网页文本内容和图片资源并进行结构化存储。

## 功能特点

- 抓取网页文本内容并保存为文本文件
- 下载网页中的图片资源
- 支持递归爬取（可设置最大深度）
- 自动去重（避免重复下载相同图片）
- 多线程下载图片提高效率
- 结构化存储爬取结果
- 详细的日志记录

## 安装依赖

```bash
pip install requests beautifulsoup4
```

## 使用方法

### 基本用法

```bash
python web_crawler.py https://example.com
```

### 高级选项

```bash
python web_crawler.py https://example.com -p 20 -d 3 -t 15 -v
```

参数说明：
- `-p, --max-pages`: 最大爬取页面数（默认：10）
- `-d, --max-depth`: 最大爬取深度（默认：2）
- `-t, --timeout`: 请求超时时间（秒）（默认：10）
- `-v, --verbose`: 显示详细日志

## 存储结构

爬虫会在用户桌面创建一个名为`WebCrawlerData_YYYYMMDD`的文件夹，其中包含：

- `texts/`: 存储爬取的文本内容
- `images/`: 存储下载的图片资源

## 代码结构

- `WebCrawler`: 主要爬虫类，处理网页抓取和内容提取
  - `download_page()`: 下载并解析网页
  - `extract_text()`: 提取网页文本内容
  - `extract_images()`: 提取并下载网页中的图片
  - `extract_links()`: 提取网页中的链接
  - `crawl()`: 开始爬取网页

## 注意事项

- 请遵守网站的robots.txt规则
- 避免过于频繁的请求，以免对目标网站造成压力
- 仅用于学习和研究目的，请勿用于非法用途

## 许可证

MIT License