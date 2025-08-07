from PIL import Image, ImageDraw, ImageFont, ImageFilter
import requests
from io import BytesIO
import concurrent.futures
import math
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import traceback
import dlc_
import coloredlogs
import logging

__import__('os').system('cls' if __import__('os').name == 'nt' else 'clear')
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

# --- coloredlogs 配置结束 ---

player_id: int = int(input("输入你的TUF账号id: "))
# 禁用SSL警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# 获取数据
player_data = requests.get(f'https://api.tuforums.com/v2/database/players/{player_id}').json()
r = player_data['passes']
r = sorted(r, key=lambda x: float(x['scoreV2']), reverse=True)

# 获取用户信息
username = player_data.get('name', 'Unknown')
user_id = player_data.get('id', 'Unknown')
avatar_url = player_data.get('pfp', '')

# 提取levelId和对应的文字（分数），去重只取第一个
s = []
addscr = []
texts = []
seen_level_ids = set()  # 用于记录已见过的levelId
t = 0
passes = []

for item in r:
    level_id = item['levelId']
    # 如果levelId已经见过，跳过
    if level_id in seen_level_ids:
        continue
    # 记录这个levelId
    seen_level_ids.add(level_id)
    # 计算加权分数
    addscr.append(0.9 ** t * float(item['scoreV2']))
    # 添加levelId
    s.append(level_id)
    passes.append(item)
    # 添加文字
    texts.append(f"XACC: {float(item['judgements']['accuracy'])*100:.2f}% / Score: {float(item['scoreV2']):.2f}(+{addscr[t]:.2f})")
    t += 1
    # 限制最多20个
    if len(s) >= 20:
        break

logger.debug("Level IDs: %s", s)
logger.debug("Texts: %s", texts)

# 生成图片URL
image_urls = []
for j in s:
    image_urls.append(f'https://api.tuforums.com/v2/media/thumbnail/level/{j}')
logger.debug("Image URLs: %s", image_urls)

CHN_Font_t = ImageFont.truetype("./1.ttf", 50)
CHN_Font_i = ImageFont.truetype("./1.ttf", 35)

def make_circle_image(img):
    """将图片裁剪成圆形"""
    # 创建圆形蒙版
    mask = Image.new('L', img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse([0, 0, img.width, img.height], fill=255)
    # 应用蒙版
    result = Image.new('RGBA', img.size, (0, 0, 0, 0))
    result.paste(img, mask=mask)
    return result

def add_rounded_border(img, border_width=5, corner_radius=25): # 确保 corner_radius 默认值与你的要求一致
    """
    为图片添加圆角黑色边框，并使图片本身也具有相同的圆角。
    """
    # 创建带边框的新图像尺寸
    new_width = img.width + 2 * border_width
    new_height = img.height + 2 * border_width
    
    # 创建一个圆角矩形蒙版，尺寸为包含边框的图像大小
    # 这个蒙版将决定最终图像的形状（包括边框）
    mask = Image.new('L', (new_width, new_height), 0) # 'L' 模式，黑色背景
    mask_draw = ImageDraw.Draw(mask)
    # 绘制一个白色（255）的圆角矩形作为蒙版，这将是最终保留的区域
    mask_draw.rounded_rectangle([0, 0, new_width, new_height], radius=corner_radius, fill=255)
    
    # 创建黑色背景的边框图像
    bordered_img = Image.new('RGBA', (new_width, new_height), (0,0,0,255)) # 将背景色改为 'black'
    
    # --- 关键修改：对原始图像也应用圆角 ---
    # 创建一个与原始图像尺寸相同的蒙版（无边框尺寸）
    inner_mask = Image.new('L', img.size, 0)
    inner_mask_draw = ImageDraw.Draw(inner_mask)
    # 绘制一个白色圆角矩形，注意坐标需要调整以匹配原始图像的坐标系
    # 圆角半径需要根据边框宽度进行调整，以确保视觉上的一致性
    # 如果希望图片圆角与外边框圆角在视觉上衔接自然，可以使用相同的半径
    # 但 PIL 的 rounded_rectangle 是基于外框计算的，所以这里我们用同样的 corner_radius
    # 只要原始图像足够大，视觉效果就是连续的圆角。
    inner_mask_draw.rounded_rectangle([0, 0, img.width, img.height], radius=corner_radius, fill=255)
    # 将原始图像裁剪成圆角形状
    img_rounded = Image.new('RGBA', img.size, (0, 0, 0, 0)) # 创建透明背景
    img_rounded.paste(img, mask=inner_mask) 
    # --- 关键修改结束 ---
    
    # 将裁剪成圆角的原始图像粘贴到黑色背景上（居中，考虑边框宽度）
    bordered_img.paste(img_rounded, (border_width, border_width), img_rounded)
    
    # 最后，使用最初创建的蒙版来定义整个图像（包括边框）的最终圆角形状
    bordered_img.putalpha(mask)
    
    return bordered_img

def add_text_to_image(img, index, text="自定义文字", font_size=24):
    """
    在图片上添加白色阴影文字
    位置：从最底下开始往上150像素，从右往左50像素
    """
    logger.info(f"图片{index}:正在处理文字: {text}")
    # 创建可绘制对象
    draw = ImageDraw.Draw(img)
    # 尝试加载系统字体，如果失败则使用默认字体
    try:
        # 尝试几种常见的系统字体
        font_paths = [
            "./s.ttf"
        ]
        font = None
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, font_size)
                break
            except:
                continue
        if font is None:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()
    # 计算文字位置
    # 从最底下开始往上150像素
    y_position = img.height - 170
    # 从右往左50像素（这是起始位置，还需要根据文字宽度调整）
    
    # 分离文字部分
    parts = text.split('(')
    if len(parts) == 2 and text.endswith(')'):
        # 格式为 "XACC: N% / Score: N(+N)"
        main_text = parts[0]  # "XACC: N% / Score: N"
        extra_part = '(' + parts[1]  # "(+N)"
    else:
        # 如果格式不匹配，按原来的方式处理
        main_text = text
        extra_part = ""
    
    # 获取各部分文字尺寸
    try:
        bbox_main = draw.textbbox((0, 0), main_text, font=font)
        main_width = bbox_main[2] - bbox_main[0]
        main_height = bbox_main[3] - bbox_main[1]
    except:
        main_width, main_height = len(main_text) * font_size // 2, font_size
    
    try:
        if extra_part:
            bbox_extra = draw.textbbox((0, 0), extra_part, font=font)
            extra_width = bbox_extra[2] - bbox_extra[0]
            extra_height = bbox_extra[3] - bbox_extra[1]
        else:
            extra_width, extra_height = 0, 0
    except:
        extra_width, extra_height = len(extra_part) * font_size // 2, font_size if extra_part else 0
    
    # 总文字宽度
    total_width = main_width + extra_width
    
    # 调整位置（文字右对齐，距离右边50像素）
    x_position = img.width - 25 - total_width  # 修改为50像素
    # 确保位置不超出边界
    x_position = max(10, x_position)
    y_position = max(10, y_position)
    
    # 绘制阴影（黑色，偏移2像素）
    shadow_offset = 2
    # 绘制主文字阴影（白色部分）
    draw.text((x_position + shadow_offset, y_position + shadow_offset),
              main_text, fill='black', font=font)
    # 绘制额外文字阴影（绿色部分）
    if extra_part:
        draw.text((x_position + main_width + shadow_offset, y_position + shadow_offset),
                  extra_part, fill='black', font=font)
    
    # 绘制主文字（白色）
    draw.text((x_position, y_position), main_text, fill='white', font=font)
    # 绘制额外文字（绿色）
    if extra_part:
        draw.text((x_position + main_width, y_position), extra_part, fill='#7CFC00', font=font)
    if passes[index]['isWorldsFirst']:
        wf_txt = 'World First!'
        # 从左往右添加文字（距离左边50像素）
        x_position = 25  # 从左往右数50px开始放置文字
        y_position = y_position  # 保持原有的y_position
        
        # 获取文字尺寸（用于边界检查）
        try:
            bbox = draw.textbbox((0, 0), wf_txt, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except:
            text_width, text_height = len(wf_txt) * font_size // 2, font_size  # 估算尺寸
        
        # 确保右侧不超出边界
        if x_position + text_width > img.width - 10:
            x_position = img.width - 10 - text_width
        
        # 绘制阴影（黑色，偏移2像素）
       
        shadow_offset = 2
        draw.text((x_position + shadow_offset, y_position + shadow_offset),
                  wf_txt, fill='black', font=font)
       
        # 绘制主文字（白色）
        draw.text((x_position, y_position), wf_txt, fill='#FFD700', font=font)
        
    # 要绘制的文字
    text = f"Speed: {passes[index]['speed']:.1f}x"  # 示例文本，可替换为实际变量
    
    # 计算文本宽度（用于右对齐）
    bbox = font.getbbox(text)
    total_width = bbox[2] - bbox[0]  # 右 - 左 = 宽度
    text_height = bbox[3] - bbox[1]  # 可选：高度
    
    # 设置右对齐位置：距离右边 50 像素
    x_position = img.width - 25 - total_width  # 修改为 50 像素边距
    y_position = 130
    
    # 确保不超出边界（最小留 10 像素边距）
    x_position = max(10, x_position)
    y_position = max(10, y_position)
    
    shadow_x = x_position + 2
    shadow_y = y_position + 2
    draw.text((shadow_x, shadow_y), text, fill=(0, 0, 0), font=font)
    
    # 绘制文字（右对齐，fill 颜色可自定义，如白色）
    draw.text((x_position, y_position), text, fill='white', font=font)
    
    
    return img
    
    

def add_blurred_background(canvas_width, canvas_height, background_path="./back.png", blur_radius=3):
    """加载、缩放、裁剪并模糊化背景图片"""
    try:
        # 打开背景图片
        bg_img = Image.open(background_path)

        # 等比缩放背景图片以覆盖整个画布
        bg_ratio = bg_img.width / bg_img.height
        canvas_ratio = canvas_width / canvas_height

        if bg_ratio > canvas_ratio:
            # 背景图片更宽，以高度为准
            new_height = canvas_height
            new_width = int(new_height * bg_ratio)
        else:
            # 背景图片更高，以宽度为准
            new_width = canvas_width
            new_height = int(new_width / bg_ratio)

        bg_img = bg_img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # 裁剪居中部分
        left = (new_width - canvas_width) // 2
        top = (new_height - canvas_height) // 2
        bg_img = bg_img.crop((left, top, left + canvas_width, top + canvas_height))

        # 应用高斯模糊
        # bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=blur_radius))

        return bg_img
    except Exception as e:
        logger.error(f"背景图片加载或处理失败: {e}\n{traceback.format_exc()}")
        # 如果背景加载失败，返回一个纯色背景
        return Image.new('RGBA', (canvas_width, canvas_height), (100, 100, 100, 255))

def add_title_text(draw, canvas_width, separator_y=240, title="Best 20"):
    """添加标题文字"""
    try:
        title_font = ImageFont.truetype("./s.ttf", 48)  # 使用s.ttf字体
    except:
        try:
            title_font = ImageFont.truetype("./1.ttf", 48)  # 备用中文字体
        except:
            title_font = ImageFont.load_default()

    # 计算文字位置（居中）
    try:
        bbox = draw.textbbox((0, 0), title, font=title_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    except:
        text_width, text_height = len(title) * 24, 48

    x_position = (canvas_width - text_width) // 2
    y_position = separator_y + 10  # 紧贴分割线下方一点

    # 绘制文字阴影
    shadow_offset = 2
    draw.text((x_position + shadow_offset, y_position + shadow_offset),
              title, fill='black', font=title_font)

    # 绘制主文字（白色）
    draw.text((x_position, y_position), title, fill='white', font=title_font)
def download_and_process_single_image(url, text, index, original_width, original_height, border_width, corner_radius, font_size, bordered_width, bordered_height, gap, start_y_position):
    """
    下载、处理单张图片并添加边框。
    返回处理后的图片、索引和计算出的位置，如果失败则返回 None, index, None。
    """
    try:
        logger.info(f"""正在处理图片 {index+1}: {url} 
                {index+1}文字内容: {text}""")
        # 从网络获取图片（忽略SSL验证）
        response = requests.get(url, timeout=45, verify=False)
        response.raise_for_status()  # 检查请求是否成功
        # 打开图片
        img = Image.open(BytesIO(response.content))
        # 调整图片大小
        if img.size != (original_width, original_height):
            img = img.resize((original_width, original_height), Image.Resampling.LANCZOS)
        # 在原始图片上添加文字
        img_with_text = add_text_to_image(img, index, str(text), font_size)
        # 添加圆角边框
        bordered_img = add_rounded_border(img_with_text, border_width, corner_radius)

        # 计算位置（行和列，从调整后的y开始）
        row = index // 2  # 行号
        col = index % 2   # 列号 (0 或 1)
        # 计算坐标（加上顶部偏移）
        x = gap + col * (bordered_width + gap)
        y = start_y_position + gap + row * (bordered_height + gap)

        logger.info(f"✓ 图片 {index+1} 处理完成")
        return bordered_img, index, (x, y)
    except Exception as e:
        logger.error(f"✗ 处理图片失败 {url}: {e} \n {traceback.format_exc()}")
        try:
            img = Image.open(dlc_.genc_pic(s[index]))
            # 调整图片大小
            if img.size != (original_width, original_height):
                img = img.resize((original_width, original_height), Image.Resampling.LANCZOS)
            # 在原始图片上添加文字
            img_with_text = add_text_to_image(img, index, str(text), font_size)
            # 添加圆角边框
            bordered_img = add_rounded_border(img_with_text, border_width, corner_radius)

            # 计算位置（行和列，从调整后的y开始）
            row = index // 2  # 行号
            col = index % 2   # 列号 (0 或 1)
            # 计算坐标（加上顶部偏移）
            x = gap + col * (bordered_width + gap)
            y = start_y_position + gap + row * (bordered_height + gap)

            logger.info(f"✓ 图片 {index+1} 重新处理完成")
            return bordered_img, index, (x, y)
        except Exception as e:
            logger.error(f"✗ 重处理图片失败 {index+1}: {e} \n {traceback.format_exc()}")
            return None, index, None
        
def create_collage_from_urls_with_text(image_urls, texts, output_path='collage.png',
                                     gap=25, border_width=8, corner_radius=25,
                                     font_size=28, username="Unknown", user_id="Unknown", avatar_url=""):
    """
    从网络URL创建带文字的图片拼贴画，包含用户信息区域
    Args:
        image_urls: 图片URL列表（最多20个）
        texts: 对应的文本列表
        output_path: 输出文件路径
        gap: 图片间间隙
        border_width: 边框宽度
        corner_radius: 圆角半径
        font_size: 字体大小
        username: 用户名
        user_id: 用户ID
        avatar_url: 头像URL
    """
    if not image_urls:
        logger.critical("没有图片URL")
        return None
    # 限制最多20张图片
    image_urls = image_urls[:20]
    texts = (texts[:20] if texts else [""] * len(image_urls))
    # 确保texts长度与image_urls一致
    if len(texts) < len(image_urls):
        texts.extend([""] * (len(image_urls) - len(texts)))
    elif len(texts) > len(image_urls):
        texts = texts[:len(image_urls)]
    # 图片原始尺寸
    original_width, original_height = 800, 420
    # 计算布局
    num_images = len(image_urls)
    rows = math.ceil(num_images / 2)  # 行数
    # 添加边框后的尺寸
    bordered_width = original_width + 2 * border_width
    bordered_height = original_height + 2 * border_width
    # 计算画布尺寸（上方空出275像素用于用户信息）
    canvas_width = bordered_width * 2 + gap * 3  # 两侧gap + 中间gap
    canvas_height = bordered_height * rows + gap * (rows + 1) + 380  # 额外275像素

# ... （函数定义和前面的代码保持不变） ...

    # 1. 先创建最终的画布
    final_canvas = Image.new('RGB', (canvas_width, canvas_height), 'white')
    final_draw = ImageDraw.Draw(final_canvas)
    # 2. 创建并添加模糊背景
    blurred_bg = add_blurred_background(canvas_width, canvas_height, "./back.png", blur_radius=3)
    final_canvas.paste(blurred_bg, (0, 0))
    # 3. 移除此行：不再绘制顶部的半透明白色遮罩
    # final_draw.rectangle([0, 0, canvas_width, 275], fill=(255, 255, 255, 200)) # 白色半透明

    # 4. 在 (275, 275) 位置绘制一条分割线
    final_draw.line([(0, 275), (canvas_width, 275)], fill='lightgray', width=2)
    # 5. 在分割线下方添加 "Best 20" 标题
    add_title_text(final_draw, canvas_width, 275, "Best 20")
    # 6. 绘制顶部用户信息内容
    # 左侧区域（头像和基本信息）
    avatar_size = 120
    avatar_x = 40
    avatar_y = 40
    # 下载并处理头像
    if avatar_url:
        try:
            avatar_response = requests.get(avatar_url, timeout=10, verify=False)
            avatar_response.raise_for_status()
            avatar_img = Image.open(BytesIO(avatar_response.content))
            avatar_img = avatar_img.resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)
            avatar_img = make_circle_image(avatar_img)
            # 注意：如果头像背景与模糊背景对比度不够，可能也需要给头像加个边框或阴影
            final_canvas.paste(avatar_img, (avatar_x, avatar_y), avatar_img)
        except Exception as e:
            logger.error(f"头像加载失败: {e} \n {traceback.format_exc()}")
    # 用户名和ID (修改文字颜色为白色)
    username_text = f"{username}"
    user_id_text = f"ID: {user_id}"
    rank = f"排名: {player_data['stats']['rankedScoreRank']}"
    # 绘制用户名 (文字颜色改为白色)
    final_draw.text((avatar_x + avatar_size + 25, avatar_y + 25), username_text, fill='white', font=CHN_Font_t) # 改为 'white'
    # 绘制用户ID (文字颜色改为白色)
    final_draw.text((avatar_x + avatar_size + 25, avatar_y + 95), user_id_text, fill='white', font=CHN_Font_i) # 改为 'white'
    # 绘制排名 (文字颜色改为白色)
    final_draw.text((avatar_x + avatar_size + 25, avatar_y + 165), rank, fill='white', font=CHN_Font_i) # 改为 'white'

    # 右侧区域（统计信息）(修改文字颜色为白色)
    stats_x_1 = canvas_width - 900
    stats_y = 40
    stats_text = [
        f"总通关数: {player_data['stats']['totalPasses']}",
        f"U级通关数: {player_data['stats']['universalPassCount']}",
        f"排位分数: {player_data['stats']['rankedScore']:.2f}",
        f"常规分数: {player_data['stats']['generalScore']:.2f}"
    ]
    # 绘制统计信息 (文字颜色改为白色)
    for i, text in enumerate(stats_text):
        final_draw.text((stats_x_1, stats_y + i * 50), text, fill='white', font=CHN_Font_i) # 改为 'white'

    stats_x_2 = canvas_width - 500
    stats_text_1 = [
        f"平均X-ACC: {player_data['stats']['averageXacc']*100:.2f}%",
        f"12K分数: {player_data['stats']['score12K']:.2f}",
        ]
    # 绘制更多统计信息 (文字颜色改为白色)
    for i, text in enumerate(stats_text_1):
        final_draw.text((stats_x_2, stats_y + i * 50), text, fill='white', font=CHN_Font_i) # 改为 'white'

    ######
    # 定义颜色
    color_top_diff_value = player_data['stats']['topDiff']['color'] 
    color_top_12k_diff_value = player_data['stats']['top12kDiff']['color']
    color_label = 'white'               # 标签颜色：白色
    
    # 获取标签文本（前面部分）
    top_diff_label = "最高击破: "
    top_12k_diff_label = "12K最高击破: "
    
    # 获取实际数据（后面部分）
    top_diff_value = player_data['stats']['topDiff']['name']
    top_12k_diff_value = player_data['stats']['top12kDiff']['name']
    
    # 绘制第一行：最高击破
    x_start = stats_x_2
    y_pos = stats_y + 100
    # 先画标签（白色）
    final_draw.text((x_start, y_pos), top_diff_label, fill=color_label, font=CHN_Font_i)
    # 再画数据（金色），x 坐标从标签结束后开始
    x_offset = x_start + CHN_Font_i.getbbox(top_diff_label)[2]  # 获取宽度
    final_draw.text((x_offset, y_pos), top_diff_value, fill=color_top_diff_value, font=CHN_Font_i)
    
    # 绘制第二行：12K最高击破
    y_pos += 50
    final_draw.text((x_start, y_pos), top_12k_diff_label, fill=color_label, font=CHN_Font_i)
    x_offset = x_start + CHN_Font_i.getbbox(top_12k_diff_label)[2]
    final_draw.text((x_offset, y_pos), top_12k_diff_value, fill=color_top_12k_diff_value, font=CHN_Font_i)
    ######
    
    # 7. 处理并排列图片（从y=350开始，因为275是顶部区域高度，加上一些间距用于标题）
    successful_count = 0
    start_y_position = 350 # 275 (顶部) + 2 (分割线) + ~70 (标题和间距)
        # ... (之前的代码保持不变，例如创建画布、绘制背景、用户信息等) ...

    # 7. 处理并排列图片（从y=350开始，因为275是顶部区域高度，加上一些间距用于标题）
    # successful_count = 0 # 将在最后计算
    start_y_position = 350 # 275 (顶部) + 2 (分割线) + ~70 (标题和间距)

    # --- 新增代码：使用多线程下载和处理图片 ---
    processed_images_info = [] # 用于存储 (bordered_img, index, (x, y)) 的列表
    # 定义线程池大小，可以根据网络和CPU情况调整，例如 4 或 5
    MAX_WORKERS = 5

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 提交所有任务到线程池
        future_to_index = {
            executor.submit(
                download_and_process_single_image,
                url, texts[i], i,
                original_width, original_height,
                border_width, corner_radius,
                font_size,
                bordered_width, bordered_height,
                gap, start_y_position
            ): i for i, url in enumerate(image_urls)
        }

        # 收集处理结果
        for future in concurrent.futures.as_completed(future_to_index):
            index = future_to_index[future]
            try:
                bordered_img, _, position = future.result()
                if bordered_img is not None:
                    processed_images_info.append((bordered_img, index, position))
            except Exception as e:
                logger.error(f"处理图片 {index} 时线程返回异常: {e} \n {traceback.format_exc()}")

    # --- 新增代码结束 ---

    # --- 新增代码：将处理好的图片粘贴到画布上 ---
    successful_count = 0
    # 按照原始顺序（索引）粘贴图片，保持布局正确
    # sorted 保证了即使线程完成顺序不同，图片也会按顺序粘贴
    for bordered_img, index, (x, y) in sorted(processed_images_info, key=lambda item: item[1]):
        # 粘贴到画布
        if bordered_img.mode == 'RGBA':
            final_canvas.paste(bordered_img, (x, y), bordered_img)
        else:
            final_canvas.paste(bordered_img, (x, y))
        successful_count += 1
    # --- 新增代码结束 ---

    
            
    from datetime import datetime # 导入 datetime 模块
    try:
        # 获取当前时间，并格式化为字符串 (例如: 2023-10-27 10:30:59)
        current_time_str = 'Query at ' + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + '   (Local V1.3)   Created By _Achry_'
        # --- 配置时间显示 ---
        time_font = ImageFont.truetype("./s.ttf", 20)          # 使用你定义的中等大小字体
        time_fill_color = 'white'       # 文字颜色为白色
        time_shadow_color = 'black'     # 阴影颜色为黑色
        time_shadow_offset = 2          # 阴影偏移量
        time_margin = 20                # 距离右边和下边的边距
        # ---------------------
        # 获取文字尺寸
        time_bbox = final_draw.textbbox((0, 0), current_time_str, font=time_font)
        time_text_width = time_bbox[2] - time_bbox[0]
        time_text_height = time_bbox[3] - time_bbox[1]
        # 计算文字位置 (右下角)
        time_x = canvas_width - time_text_width - time_margin
        time_y = canvas_height - time_text_height - time_margin
        # 绘制阴影
        final_draw.text(
            (time_x + time_shadow_offset, time_y + time_shadow_offset),
            current_time_str,
            fill=time_shadow_color,
            font=time_font
        )
        # 绘制主文字
        final_draw.text(
            (time_x, time_y),
            current_time_str,
            fill=time_fill_color,
            font=time_font
        )
        logger.info(f"已添加时间水印: {current_time_str}")
    except Exception as e:
        logger.error(f"添加时间水印时出错: {e} \n {traceback.format_exc()}")
    # 保存结果
    if successful_count > 0:
        final_canvas.save(output_path, quality=100)
        logger.info(f"B20已保存到: {output_path} (共{successful_count}张图片)")
        return final_canvas
    else:
        logger.warning("没有成功处理任何图片")
        return None

# 使用示例
if __name__ == "__main__":
    # 创建带文字的拼贴画
    try:
        collage = create_collage_from_urls_with_text(
            image_urls=image_urls,
            texts=texts,  # 使用获取到的分数作为文字
            output_path=f'b20_{player_id}.png',
            gap=25,           # 间隙25像素
            border_width=8,   # 边框8像素
            corner_radius=25, # 圆角半径25像素
            font_size=28,     # 字体大小28像素
            username=username,
            user_id=user_id,
            avatar_url=avatar_url
        )
        if collage:
            logger.info("B20创建成功！")
        else:
            logger.warning("没有成功处理任何图片")
    except Exception as e:
        logger.error(f"创建B20时出错: {e} \n {traceback.format_exc()}")