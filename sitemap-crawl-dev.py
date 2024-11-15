import requests
import pandas as pd
import os
import dbm
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlparse
import glob
import numpy as np

# 函数：从sitemap中提取链接
def get_links_from_sitemap(sitemap_url):
    response = requests.get(sitemap_url)
    soup = BeautifulSoup(response.content, 'xml')
    links = [loc.text for loc in soup.find_all('loc')]
    return links

# 函数：从URL中提取关键词
def extract_keywords(url):
    path = urlparse(url).path
    keywords = path.strip('/').split('/')
    filtered_keywords = []
    # 过滤规则
    ignore_keywords = {'games', 'game', 'sitemap', 'sitemaps', '.png'}
    for keyword in keywords:
        if keyword.isdigit() or len(keyword) == 1 or keyword in ignore_keywords:
            continue
        filtered_keywords.append(keyword)
    return filtered_keywords

# 初始化数据库
def initialize_database():
    # 检查数据库是否已初始化
    if os.path.exists('keyword_database.db'):
        print("数据库已存在，跳过初始化步骤。")
        return

    print("开始初始化数据库...")
    with dbm.open('keyword_database', 'c') as db:
        csv_files = glob.glob('keyword_frequency_*.csv')
        for file in sorted(csv_files, key=os.path.getctime):
            print(f"reading file: {file}")
            df = pd.read_csv(file)
            collection_time = pd.to_datetime(df['Collection Time'].iloc[0])
            for _, row in df.iterrows():
                key = f"{row['Domain']}:{row['Keyword']}"
                print(f"processing key: {key}")
                if pd.isna(row['Frequency']) or pd.isna(row['Keyword']):
                    continue  # 跳过频率为 NaN 的记录
                if key in db:
                    data = eval(db[key].decode())
                    data['Latest_Update_Date'] = collection_time.strftime('%Y-%m-%d %H:%M:%S')
                    data['Frequency'] += row['Frequency']
                else:
                    data = {
                        'Domain': row['Domain'],
                        'Keyword': row['Keyword'],
                        'First_Collect_Date': collection_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'Latest_Update_Date': collection_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'Frequency': float(row['Frequency'])  # 确保频率是浮点数
                    }
                db[key] = str(data)
    print("数据库初始化完成。")

# 更新数据库
def update_database(current_data):
    with dbm.open('keyword_database', 'c') as db:
        for item in current_data:
            key = f"{item[0]}:{item[1]}"
            current_time = item[3]
            if pd.isna(item[2]):
                continue  # 跳过频率为 NaN 的记录
            if key in db:
                data = eval(db[key].decode())
                data['Latest_Update_Date'] = current_time
                data['Frequency'] += float(item[2])
            else:
                data = {
                    'Domain': item[0],
                    'Keyword': item[1],
                    'First_Collect_Date': current_time,
                    'Latest_Update_Date': current_time,
                    'Frequency': float(item[2])
                }
            db[key] = str(data)

# 主程序
if __name__ == "__main__":
    # 初始化数据库
    initialize_database()

    # 要处理的sitemaps列表
    sitemaps = [
        "https://www.crazygames.com/sitemap",
        "https://poki.com/en/sitemaps/index.xml",
        "https://itch.io/sitemap.xml",
        "https://www.friv.com/sitemap.xml",
        "https://playhop.com/sitemaps/sitemap.index.xml"
    ]

    # 准备DataFrame的数据
    data = []
    collect_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 处理每个sitemap
    for sitemap in sitemaps:
        try:
            domain = urlparse(sitemap).netloc  # 提取域名
            links = get_links_from_sitemap(sitemap)  # 从sitemap获取链接
            keywords = []
            
            # 提取每个链接中的关键词
            for link in links:
                keywords.extend(extract_keywords(link))
            
            # 计算关键词频次
            keyword_freq = pd.Series(keywords).value_counts()
            
            # 将结果添加到数据列表中
            for keyword, freq in keyword_freq.items():
                data.append([domain, keyword, freq, collect_time])
        
        except Exception as e:
            print(f"Error processing {sitemap}: {e}")

    # 更新数据库
    update_database(data)

    # 输出更新结果
    with dbm.open('keyword_database', 'r') as db:
        updated_data = []
        for key in db.keys():
            item = eval(db[key].decode())
            updated_data.append(item)

    result_df = pd.DataFrame(updated_data)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    result_file_name = f'keyword_updated_{timestamp}.csv'
    result_df.to_csv(result_file_name, index=False)

    print(f"更新结果已保存到：{result_file_name}")
