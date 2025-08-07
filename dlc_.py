import random
import string
import requests
import os
import base64
from io import BytesIO
import math
from PIL import Image
import logging
import traceback
import coloredlogs

logger = logging.getLogger(__name__)

# 2. 定义日志格式
# 这个格式字符串与你要求的 [时间/类型] 信息 相匹配
field_styles = {
    'asctime': {'color': 'green'},  # 时间默认是绿色，可以调整
    'hostname': {'color': 'magenta'},
    'levelname': {'color': 'black', 'bold': True}, # 级别名默认有颜色，这里微调
    'name': {'color': 'blue'},
    'programname': {'color': 'cyan'}
}

level_styles = {
    'critical': {'color': 'red', 'bold': True},
    'error': {'color': 'red'},
    'warning': {'color': 'yellow'},
    'info': {'color': 'green'},
    'debug': {'color': 'cyan'} # 或 'cyan'
}

# 3. 安装 coloredlogs 到你的 logger
#    - level: 设置 logger 的最低处理等级
#    - fmt: 设置日志的格式字符串
#    - datefmt: 设置日期时间的格式
#    - field_styles 和 level_styles: 自定义颜色 (可选)
coloredlogs.install(
    level='DEBUG', # 设置为 DEBUG 可以看到所有级别的日志
    logger=logger, # 指定要安装到的 logger 实例
    fmt='[%(asctime)s/%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    field_styles=field_styles,
    level_styles=level_styles
)

def genc(level_id):
    logger.info(f"开始生成关卡 {level_id} 的HTML")
    r = requests.get(f'https://api.tuforums.com/v2/database/levels/byId/{level_id}')
    if r.status_code != 200:
        return None
    logger.info('成功获取关卡信息')
    data = r.json()
    artist, song, diff_data = data['artist'], data['song'], data['difficulty']
    width, height, multiplier = 1200, 630, 1.5
    iconSize = math.floor(height * 0.184);
    icon_b64 = download_image_to_base64(diff_data['icon'])
    logger.info('成功获取关卡图标数据')
    artistOverflow = len(artist) > 35
    songOverflow = len(song) > 35
    charters = [name.strip() for name in data['charter'].split('&')] if data['charter'] else []
    vfxers = [name.strip() for name in data['vfxer'].split('&')] if data['vfxer'] else []
    # 转换为Python代码
    if data.get('team', False):
        first_row = "By " + data['team']
    elif vfxers and len(vfxers) > 0:
        first_row = "Chart: " + ', '.join(charters)
    else:
        if charters and len(charters) > 4:
            first_row = "By " + ', '.join(charters[:4]) + " and " + str(len(charters) - 4) + " more"
        else:
            first_row = "By " + ', '.join(charters) if charters else "By "
            
    # 更简洁的版本
    team = data.get('team')
    if not team and vfxers and charters:
        second_row = "VFX: " + ', '.join(vfxers)
    else:
        second_row = ""
    logger.info('genc html')
    html = f"""
            <html>
              <head>
                <style>
                  body {{ 
                    margin: 0; 
                    padding: 0;
                    width: {width}px;
                    height: {height}px;
                    
                    position: relative;
                    overflow: hidden;
                    font-family: 'NotoSansKR', 'NotoSansJP', 'NotoSansSC', 'NotoSansTC', sans-serif;
                  }}
                  .text {{
                    overflow: hidden;
                    display: -webkit-box;
                    -webkit-line-clamp: 2;
                    -webkit-box-orient: vertical;
                    max-width: {520*multiplier}px;
                  }}
                  .background-image {{
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    z-index: 1;
                  }}
                  .header {{
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: {(110 + (10 if artistOverflow and songOverflow else 0)) * multiplier}px;
                    background-color: rgba(0, 0, 0, 0.8);
                    z-index: 2;
                    display: flex;
                    align-items: center;
                    padding: 0 {25*multiplier}px;
                    box-sizing: border-box;
                  }}
                  .header-left {{
                    display: flex;
                    align-items: center;
                    flex: 1;
                  }}
                  .header-right {{
                    display: flex;
                    padding-top: {12*multiplier}px;
                    align-self: start;
                    align-items: center;
                    justify-content: flex-end;
                  }}
                  .difficulty-icon {{
                    width: {iconSize}px;
                    height: {iconSize}px;
                    margin-right: {25*multiplier}px;
                  }}
                  .song-info {{
                    display: flex;
                    gap: {5*multiplier}px;
                    flex-direction: column;
                    justify-content: center;
                  }}
                  .song-title {{
                    font-weight: 800;
                    font-size: {35*multiplier*(0.8 if songOverflow else 1)}px;
                    color: white;
                    margin: 0;
                    line-height: 1.2;
                  }}
                  .artist-name {{
                    font-weight: 400;
                    font-size: {25*multiplier*(0.8 if artistOverflow else 1)}px;
                    color: white;
                    margin: 0;
                    line-height: 1.2;
                  }}
                  .level-id {{
                    font-weight: 700;
                    font-size: {40*multiplier}px;
                    color: #bbbbbb;
                  }}
                  .footer {{
                    position: absolute;
                    bottom: 0;
                    left: 0;
                    width: 100%;
                    height: {110*multiplier}px;
                    background-color: rgba(0, 0, 0, 0.8);
                    z-index: 2;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: {10*multiplier}px {25*multiplier}px;
                    box-sizing: border-box;
                  }}
                  .footer-left {{
                    display: flex;
                    align-items: start;
                    flex-direction: column;
                  }}
                  .footer-right {{
                      display: flex;
                      max-width: 70%;
                      gap: {10*multiplier}px;
                      flex-direction: column;
                  }}
                  .pp-value, .pass-count {{
                    font-weight: 700;
                    font-size: {30*multiplier}px;
                    color: #bbbbbb;
                  }}
                  .creator-name {{
                    font-weight: 600;
                    text-align: right;
                    font-size: {30*multiplier*(0.9 if second_row else 1)}px;
                    color: white;
                  }}
                </style>
              </head>
              <body>
                <!-- Background image -->
                <img 
                  class="background-image"
                  src="data:image/png;base64,{create_black_image_base64(width, height)}" 
                  alt="Background"
                />
                
                <!-- Header -->
                <div class="header">
                  <div class="header-left">
                    <img 
                      class="difficulty-icon"
                      src="data:image/png;base64,{icon_b64}" 
                      alt="Difficulty Icon"
                    />
                    <div class="song-info">
                      <div class="song-title text">{song}</div>
                      <div class="artist-name text" 
                        style="-webkit-line-clamp: 1">{artist}</div>
                    </div>
                  </div>
                  <div class="header-right">
                    <div class="level-id">#{level_id}</div>
                  </div>
                </div>
                
                <!-- Footer -->
                <div class="footer">
                  <div class="footer-left">
                    <div class="pp-value">{data.get('baseScore') or diff_data.get('baseScore') or 0}PP</div>
                    <div class="pass-count">{data.get('clears') or 0} pass{'' if (data.get('clears') == 1 or data.get('clears') == 0) else 'es'}</div>
                  </div>
                  <div class="footer-right">
                    <div class="creator-name">{first_row}</div>
                    {'<div class="creator-name">'+second_row+'</div>' if second_row else ''}

                  </div>
                </div>
              </body>
            </html>
          """;
          
    return html
    
def create_black_image_base64(width, height):
    # 创建纯黑图片
    image = Image.new('RGB', (width, height), color='grey')
    
    # 将图片保存到内存缓冲区
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    
    # 获取字节数据
    image_bytes = buffer.getvalue()
    
    # 转换为base64
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
    
    return image_base64
    
def download_image_to_base64(url):
    try:
        # 下载图片
        response = requests.get(url)
        response.raise_for_status()  # 检查请求是否成功
        
        # 获取图片内容
        image_data = response.content
        
        # 转换为base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        return image_base64
        
    except requests.RequestException as e:
        logger.error(f"下载图片失败: {e} \n {traceback.format_exc()}")
        return None
    except Exception as e:
        logger.error(f"转换base64失败: {e} \n {traceback.format_exc()}")
        return None

from playwright.sync_api import sync_playwright
import time

def html_to_png(html_content, level_id, width=1200, height=800):
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch()
        # 创建页面
        page = browser.new_page()
        
        # 设置视口大小
        page.set_viewport_size({"width": width, "height": height})
        
        # 加载HTML内容
        page.set_content(html_content)
        
        # 等待页面渲染完成
        page.wait_for_timeout(2000)
        
        # 截图并保存
        filename = f"tmp/{''.join(random.choices(string.ascii_letters + string.digits, k=10))}.jpg"
        page.screenshot(path=filename, full_page=True)
        
        # 关闭浏览器
        browser.close()
        
        return filename

def genc_pic(level_id):
    # 使用示例
    d = genc(level_id)
    
    # 如果你知道HTML的具体尺寸，可以提取出来
    # 否则使用默认尺寸
    width, height = 1200, 630  # 根据实际情况调整
    
    # 转换并保存
    filename = html_to_png(d, level_id, width, height)
    logger.info(f"图片已保存为 {filename}")
    return filename
    


