import asyncio
from crawl4ai import AsyncWebCrawler
from datetime import datetime, date
import json
import openai
import os

# 设置本地代理
proxy = "http://localhost:1088"

# 配置AsyncWebCrawler使用代理
# AsyncWebCrawler.set_proxy(proxy)

# 配置OpenAI API使用代理
openai.proxy = proxy

def load_env(file_path='.env'):
    if not os.path.exists(file_path):
        return

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# 在文件开头调用load_env函数
load_env()

# 定义新闻数据类
class News:
    def __init__(self, title, source, timestamp, summary, keywords, full_text):
        self.title = title
        self.source = source
        self.timestamp = timestamp
        self.summary = summary
        self.keywords = keywords
        self.full_text = full_text

# 创建新闻池
news_pool = []

# 添加多个信息源URL
urls = [
    "https://www.aibase.com/zh/news",
    "https://techcrunch.com/latest",
    "https://www.theverge.com/latest",
    "https://www.wired.com/latest",
    "https://www.engadget.com/latest",
    "https://www.gsmarena.com/news.php3",
    "https://www.cnbc.com/technology/",
    # 可以在此添加更多的信息源URL
]

async def main():
    async with AsyncWebCrawler(verbose=True) as crawler:
        for url in urls:
            result = await crawler.arun(url=url)
            # 解析抓取的内容
            markdown_content = result.markdown
            # 将markdown内容保存到output.md文件
            with open('output.md', 'w', encoding='utf-8') as file:
                file.write(markdown_content)
            
            # 从markdown中提取多条新闻
            if markdown_content:
                # 使用正则表达式匹配所有新闻部分
                import re
                news_sections = re.split(r'\n(?=###\s)', markdown_content)
                for section in news_sections:
                    if section.strip():
                        lines = section.split('\n')
                        title = lines[0].strip('# ').strip()
                        full_text = '\n'.join(lines[1:]).strip()
                        
                        # 提取摘要（假设摘要是标题后的第一段）
                        summary_end = full_text.find('\n\n')
                        summary = full_text[:summary_end].strip() if summary_end != -1 else full_text
                        
                        keywords = []
                        if result.metadata and 'keywords' in result.metadata:
                            keywords = result.metadata['keywords']
                        
                        source = url
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        # 检查新闻是否已存在，避免重复
                        if title and title not in [news.title for news in news_pool]:
                            news = News(title, source, timestamp, summary, keywords, full_text)
                            news_pool.append(news)
        
        # 保存新闻池到本地文件，便于后续处理
        with open('news_pool.json', 'w', encoding='utf-8') as file:
            json.dump([news.__dict__ for news in news_pool], file, ensure_ascii=False, indent=4)
        
        print(f"总共处理了 {len(news_pool)} 条新闻")

# 定义函数，让AI选择最佳新闻
def select_top_news(news_pool, top_n=10):
    # 生成新闻摘要字符串
    summaries = "\n\n".join([f"标题: {news.title}\n摘要: {news.summary}" for news in news_pool])

    # 构建提示词
    prompt = f"根据以下新闻摘要，选出最具影响力和相关性的前{top_n}条新闻，并列出它们的标题。\n\n{summaries}"
    print(f"prompt: {prompt}")

    # 从环境变量中获取API密钥
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("请在.env文件中设置OPENAI_API_KEY")

    # 初始化OpenAI客户端
    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key
    )

    # 调用API获取响应
    try:
        response = client.chat.completions.create(
            model="anthropic/claude-3-sonnet-20240229",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.5
        )
        print(f"API响应: {response}")  # 打印完整的API响应
    except Exception as e:
        print(f"调用API时发生错误: {e}")
        return []

    # 解析响应，获取选中的标题
    selected_titles = response.choices[0].message.content.strip().split('\n')
    selected_titles = [title.strip() for title in selected_titles if title.strip()]
    print(f"选中的标题: {selected_titles}")  # 打印选中的标题

    # 根据标题从新闻池中筛选新闻
    selected_news = [news for news in news_pool if news.title in selected_titles]
    print(f"筛选出的新闻数量: {len(selected_news)}")  # 打印筛选出的新闻数量

    return selected_news

def filter_today_news(news_pool):
    today = date.today()
    return [news for news in news_pool if datetime.strptime(news.timestamp, "%Y-%m-%d %H:%M:%S").date() == today]

def generate_news_push(filtered_news):
    push_content = "今日AI新闻推送\n\n"
    # 跳过第一条新闻
    for i, news in enumerate(filtered_news[1:], 1):
        push_content += f"{i}. {news.title}\n"
        push_content += f"   来源: {news.source}\n"
        push_content += f"   时间: {news.timestamp}\n"
        push_content += f"   摘要: {news.summary}\n"
        push_content += f"   关键词: {news.keywords}\n"
    return push_content

if __name__ == "__main__":
    asyncio.run(main())

    # # 让AI选择最佳新闻
    # top_news = select_top_news(news_pool)

    # # 输出结果到文本文件
    # with open('top_news.txt', 'w', encoding='utf-8') as file:
    #     for news in top_news:
    #         file.write(f"标题: {news.title}\n")
    #         file.write(f"来源: {news.source}\n")
    #         file.write(f"时间: {news.timestamp}\n")
    #         file.write(f"摘要: {news.summary}\n")
    #         file.write(f"关键词: {', '.join(news.keywords)}\n")
    #         file.write(f"全文: {news.full_text}\n")
    #         file.write("\n" + "-"*40 + "\n\n")

    # 筛选当天新闻
    today_news = filter_today_news(news_pool)

    # 生成推送内容
    push_content = generate_news_push(today_news)

    # 输出结果到文本文件
    with open('today_news_push.txt', 'w', encoding='utf-8') as file:
        file.write(push_content)

    print(f"今日新闻数量: {len(today_news)}")
    print("推送内容已保存到 today_news_push.txt 文件中")
