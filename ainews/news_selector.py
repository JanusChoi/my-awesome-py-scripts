import gradio as gr
import json
from datetime import datetime
import pyperclip

def load_news():
    with open('news_pool.json', 'r', encoding='utf-8') as file:
        news_data = json.load(file)
    
    today = datetime.now().strftime('%Y-%m-%d')
    parsed_news = []
    for item in news_data:
        news_date = datetime.strptime(item['timestamp'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
        if news_date == today:
            parsed_news.append(item)
    return parsed_news

def update_output(selected_titles):
    output = ""
    for news in news_list:
        if f"{news['title']}\n\n{news['summary']}" in selected_titles:
            output += f"标题: {news['title']}\n\n"
            output += f"{news['full_text']}\n===========================\n\n"
    return output

def copy_to_clipboard(text):
    pyperclip.copy(text)
    return "已复制到剪贴板"

def save_data(selected_titles, output_text):
    selected_news = [news for news in news_list if f"{news['title']}\n\n{news['summary']}" in selected_titles]
    data = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'input': news_list,
        'output': selected_news
    }
    filename = f"news_data_{datetime.now().strftime('%Y%m%d')}.json"
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
    return f"数据已保存到 {filename}"

news_list = load_news()

with gr.Blocks() as demo:
    gr.Markdown("# 今日AI新闻精选")
    with gr.Row():
        with gr.Column(scale=2):
            news_selection = gr.CheckboxGroup(
                choices=[f"{news['title']}\n\n{news['summary']}" for news in news_list],
                label="选择要包含的新闻",
                type="value"
            )
        with gr.Column(scale=1):
            output_text = gr.Textbox(label="选中的新闻", lines=10)
            copy_btn = gr.Button("复制选中内容")
            save_btn = gr.Button("保存数据")
            status_text = gr.Textbox(label="状态", lines=1)
    
    news_selection.change(
        fn=update_output,
        inputs=[news_selection],
        outputs=[output_text]
    )
    
    copy_btn.click(
        fn=copy_to_clipboard,
        inputs=[output_text],
        outputs=[status_text]
    )
    
    save_btn.click(
        fn=save_data,
        inputs=[news_selection, output_text],
        outputs=[status_text]
    )

demo.launch()
