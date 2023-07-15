import streamlit as st
import datetime
from PIL import Image, ImageDraw, ImageFont
import calendar
import os
import openai
import requests
import urllib.error
import urllib.request

if "execInitProcess" not in st.session_state:
    st.session_state.execInitProcess = False
    st.session_state.imageList = []

openai.api_key = st.secrets.GPT3ApiKey.api_key

GENERATED_IMAGE_FOLDER_NAME = "./image"
CALENDAR_IMAGE_NAME = "calendar.png"

# DALL-Eによる画像生成
def generate_image(prompt):
    response = openai.Image.create(
        model = "image-alpha-001",
        prompt = prompt,
        n = 1,
        size = "512x512",
        response_format = "url"
    )

    return response["data"][0]["url"]

# 画像のURLからダウンロード
def download_file(url, dst_path):
    try:
        with urllib.request.urlopen(url) as web_file:
            data = web_file.read()
            with open(dst_path, mode = "wb") as local_file:
                local_file.write(data)
    except urllib.error.URLError as e:
        st.error(e)

# カレンダー画像の生成
def createCalendarImage(year, month, imageFile, backgroundColor, fontColor):
    # 画像の情報を設定
    im = Image.new("RGB", (1280, 720), (int(backgroundColor[1:3], 16),
                                        int(backgroundColor[3:5], 16), 
                                        int(backgroundColor[5:7], 16)))
    draw = ImageDraw.Draw(im)

    # PCローカルのフォントへのパスと、フォントサイズを指定
    mainFont = ImageFont.truetype("mplus-1m-bold.ttf", 35)
    monthFont = ImageFont.truetype("mplus-1m-bold.ttf", 110)
    subFont = ImageFont.truetype("mplus-1m-bold.ttf", 15)
    
    # 今月の数字を描画
    draw.text((25, 230), f"{month:02}", fill=(int(fontColor[1:3], 16), int(fontColor[3:5], 16), int(fontColor[5:7], 16)), font=monthFont)

    calendar.setfirstweekday(calendar.SUNDAY)
    
    # 文字の描画(今月のカレンダー)
    mainCalendartexts = calendar.month(year, month, w=3).split("\n")
    count = 0
    for text in mainCalendartexts:
        draw.text((35, 310 + 50 * count), text, fill=(int(fontColor[1:3], 16), int(fontColor[3:5], 16), int(fontColor[5:7], 16)), font=mainFont)
        count = count + 1

    # 文字の描画(先月のカレンダー)
    if month == 1:
        prevCalendartexts = calendar.month(year - 1, 12, w = 3).split("\n")
    else:
        prevCalendartexts = calendar.month(year, month - 1, w = 3).split("\n")
    count = 0
    for text in prevCalendartexts:
        draw.text((35, 60 + 20 * count), text, fill = (int(fontColor[1:3], 16), int(fontColor[3:5], 16), int(fontColor[5:7], 16)), font=subFont)
        count = count + 1

    # 文字の描画(来月のカレンダー)
    if month == 12:
        nextCalendartexts = calendar.month(year + 1, 1, w = 3).split("\n")
    else:
        nextCalendartexts = calendar.month(year, month + 1, w = 3).split("\n")
    count = 0
    for text in nextCalendartexts:
        draw.text((315, 60 + 20 * count), text, fill = (int(fontColor[1:3], 16), int(fontColor[3:5], 16), int(fontColor[5:7], 16)), font=subFont)
        count = count + 1

    # 画像とカレンダーを合わせて完成画像にする
    img = Image.open(GENERATED_IMAGE_FOLDER_NAME + "/" + imageFile)

    img_resize = img.resize((720, 720))
    im.paste(img_resize, (1280 - 720, 0))
    im.save(CALENDAR_IMAGE_NAME)
    
    st.image(CALENDAR_IMAGE_NAME, caption = "プレビュー")

def main():
    #アプリ起動時の処理、二重にロードしたくない処理はここで行う
    if st.session_state.execInitProcess == False:
        # フォルダがなければ、フォルダ作成
        if not os.path.isdir(GENERATED_IMAGE_FOLDER_NAME):
            os.mkdir(GENERATED_IMAGE_FOLDER_NAME)
            
        files = os.listdir(GENERATED_IMAGE_FOLDER_NAME)
        for file in files:
            if file.endswith(".png"):
                st.session_state.imageList.append(file)
        
        st.session_state.execInitProcess = True

    st.set_page_config(page_title = "カレンダー自動生成")
    st.title("あなただけのカレンダーを作ろう!")
    
    # サイドバーの設定一覧
    st.sidebar.title("各種設定")
    nowTime = datetime.datetime.now()
    # 現在の西暦をデフォルトにする
    st.session_state.year = st.sidebar.text_input("西暦を入力", value = nowTime.year) 
    # 現在の月をデフォルトにする
    st.session_state.month = st.sidebar.slider("月を入力", min_value = 1, max_value = 12, value = nowTime.month) 
    st.session_state.backgroundColor = st.sidebar.color_picker("背景色", "#ffffff")
    st.session_state.fontColor = st.sidebar.color_picker("文字の色", "#000000")
    selectImage = st.sidebar.selectbox("画像を選択", st.session_state.imageList, index = len(st.session_state.imageList) - 1)
    st.session_state.prompt = st.sidebar.text_input("生成する画像の説明を入力")
    st.session_state.filename = st.sidebar.text_input("生成した画像のファイル名を入力※ファイル名が被ると前の画像は削除されます！")
    
    #画像生成
    if st.sidebar.button("画像生成"):
        if len(st.session_state.prompt) == 0:
            st.error("生成する画像の説明を入力してください。")
        elif len(st.session_state.filename) == 0:
            st.error("ファイル名を入力してください。")
        else:
            # 画像を生成
            st.info("画像を生成中...")
            download_file(generate_image(st.session_state.prompt), GENERATED_IMAGE_FOLDER_NAME + "/" + st.session_state.filename + ".png")
            if st.session_state.filename + ".png" not in st.session_state.imageList:
                st.session_state.imageList.append(st.session_state.filename + ".png")
            # ドロップダウンリスト更新のため、強制的に再読み込みする
            st.experimental_rerun()
    
    # 入力値は数値以外や0以下も入力できてしまうので、それらは除外する  
    if st.session_state.year.isdigit() == False or int(st.session_state.year) < 1:
        st.error("西暦の入力値には1以上の整数を入力してください。")
    else:
        # 初期状態で画像がない場合はプレビューを表示しない
        if os.path.isfile(GENERATED_IMAGE_FOLDER_NAME + "/" + str(selectImage)) == True:
            # プレビューの表示
            createCalendarImage(int(st.session_state.year), 
                                int(st.session_state.month), 
                                selectImage, 
                                st.session_state.backgroundColor, 
                                st.session_state.fontColor)
            
            # ダウンロードボタン
            with open(CALENDAR_IMAGE_NAME, "rb") as file:
                st.download_button(
                        label = "ダウンロード",
                        data = file,
                        file_name = CALENDAR_IMAGE_NAME.replace(".", "(" + str(st.session_state.year) + "-" + str(st.session_state.month) + ")."),
                        mime = "image/png"
                    )

if __name__ == "__main__":
    main()