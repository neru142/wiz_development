from flask import Flask, request, abort
import os
import psycopg2

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    ButtonsTemplate, CarouselColumn, CarouselTemplate, 
    BubbleContainer, CarouselContainer, BoxComponent, TextComponent, ButtonComponent,
    FollowEvent, MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, FlexSendMessage,
    PostbackAction, PostbackTemplateAction
)

app = Flask(__name__)

# 環境変数取得
ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]
CHANNEL_SECRET = os.environ["CHANNEL_SECRET"]
DATABASE_URL = os.environ.get('DATABASE_URL')

line_bot_api = LineBotApi(ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# Pythonでは呼び出す行より上に記述しないとエラーになる

# リストをn個ずつのサブリストに分割する
# l : リスト
# n : サブリストの要素数
def split_list(l, n):
    for idx in range(0, len(l), n):
        yield l[idx:idx + n]

# 窓口リストを表示する関数
def window_list_flex(db):
    db.append(
        (1,1,1,
        '見つからない場合はこちら',
        '県の総合的な相談窓口',
        '県庁県政相談コーナー',
        '0120-899-721\nkenseisoudan@pref.fukushima.lg.jp',
        '月～金\n9:00～12:00\n13:00～16:00\n(祝日、年末年始を除く)',
        0,'2021-12-10 02:37:02.388856')
        )
    db_column = list(split_list(db, 10))

    contents_carousel = []
    for dbcol in db_column:
        contents_button = []
        for row in dbcol:
            contents_button.append(
                ButtonComponent(
                    style = 'link',
                    height = 'sm',
                    action = PostbackAction(
                        label = str(row[3])[:40],
                        data = 'callback',
                        text = '窓口ID:' + str(row[0])
                    )
                )
            )
        contents_carousel.append(
            BubbleContainer(
                header = BoxComponent(
                    layout = 'vertical',
                    contents = [ 
                        TextComponent(
                            text = '窓口を選択してください',
                            weight = 'bold',
                            color = '#333333',
                            size = 'xl'
                        )
                    ]
                ),
                body = BoxComponent(
                    layout = 'vertical',
                    contents = contents_button
                )
            )
        )
        
    return CarouselContainer(contents=contents_carousel)

# 窓口の情報を出力
def window_info(db):
    result = db[0][4] + "\n"\
        + db[0][5] + "\n"\
        + db[0][6] + "\n"\
        + db[0][7]
    return result

# ブラウザでherokuにアクセスした場合の処理
@app.route("/")
def hello_world():
    return "hello world!"

# LINEからメッセージを受け取った場合の処理
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        # 署名を検証し、問題なければhandleに定義されている関数を呼び出す
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# データベースの表の出力
@app.route("/database")
def database():
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as curs:
            curs.execute("SELECT * FROM window_list ORDER BY Id ASC")
            db = curs.fetchall()
            result = "<table>\
             <tr>\
              <th>Id</th>\
              <th>Category</th>\
              <th>Number</th>\
              <th>Soudan_name</th>\
              <th>Soudan_content</th>\
              <th>Window_name</th>\
              <th>Tel</th>\
              <th>Business_hours</th>\
              <th>Subcategory</th>\
              <th>Timestamp</th>\
             </tr>"
            for row in db: 
                result += "<tr>\
                    <td>" + str(row[0]) + "</td>\
                    <td>" + str(row[1]) + "</td>\
                    <td>" + str(row[2]) + "</td>\
                    <td>" + str(row[3]) + "</td>\
                    <td>" + str(row[4]) + "</td>\
                    <td>" + str(row[5]) + "</td>\
                    <td>" + str(row[6]) + "</td>\
                    <td>" + str(row[7]) + "</td>\
                    <td>" + str(row[8]) + "</td>\
                    <td>" + str(row[9]) + "</td>\
                    </tr>"
            result += "</table>"
    return result

# フォローイベントの場合の処理
@handler.add(FollowEvent)
def handle_follow(event):
    profile = line_bot_api.get_profile(event.source.user_id)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=profile.display_name + "さん、はじめまして！\n" +
        "友だち追加ありがとうございます。温泉情報botです。\n" +
        "福島県の温泉を探す場合、まずは「温泉を探す」をタップしてください。\n" +
        "泉質名についての説明が欲しい場合は、helpをタップしてください。")
    )

# メッセージイベントの場合の処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        content = event.message.text # メッセージの内容を取得する
        if content in ['温泉を探す']:
            carousel_columns = [
                CarouselColumn(
                    text='希望の地方を選択する',
                    title='地方選択',
                    actions=[
                        PostbackTemplateAction(
                            label='会津',
                            data='callback',
                            text='会津'
                            
                        ),
                        PostbackTemplateAction(
                            label='中通り',
                            data='callback',
                            text='中通り'
                        ),
                        PostbackTemplateAction(
                            label='浜通り',
                            data='callback',
                            text='浜通り'
                        )
                    ]
                )
            ]
            message_template = CarouselTemplate(columns=carousel_columns)
            line_bot_api.reply_message(
                event.reply_token,
                TemplateSendMessage(alt_text='carousel template', template=message_template)
            )

        elif content in ['産業']:
            carousel_columns = [
                CarouselColumn(
                    text = '分野を選択してください',
                    title = '分野選択',
                    actions = [
                        PostbackTemplateAction(
                            label = '農林水産業',
                            data = 'callback',
                            text = '農林水産業'
                        ),
                        PostbackTemplateAction(
                            label = 'テクノロジー',
                            data = 'callback',
                            text = 'テクノロジー'
                        ),
                        
                    ]
                )
            ]
            message_template = CarouselTemplate(columns=carousel_columns)
            line_bot_api.reply_message(
                event.reply_token,
                TemplateSendMessage(alt_text='carousel template', template=message_template)
            )

        elif content in ['障がい児関連']:

            carousel_columns = [
                CarouselColumn(
                    text = '分野を選択してください',
                    title = '分野選択',
                    actions = [
                        PostbackTemplateAction(
                            label = '視覚障がい',
                            data = 'callback',
                            text = '視覚障がい'
                        ),
                        PostbackTemplateAction(
                            label = '聴覚障がい',
                            data = 'callback',
                            text = '聴覚障がい'
                        ),
                        PostbackTemplateAction(
                            label = '肢体不自由',
                            data = 'callback',
                            text = '肢体不自由'
                        )
                    ]
                ),
                CarouselColumn(
                    text = '分野を選択してください',
                    title = '分野選択',
                    actions = [
                        PostbackTemplateAction(
                            label = '病弱障がい',
                            data = 'callback',
                            text = '病弱障がい'
                        ),
                        PostbackTemplateAction(
                            label = '知的障がい',
                            data = 'callback',
                            text = '知的障がい'
                        ),
                        PostbackTemplateAction(
                            label = 'LD・ADHD等',
                            data = 'callback',
                            text = 'LD・ADHD等'
                        )
                    ]
                )
            ]
            message_template = CarouselTemplate(columns=carousel_columns)
            line_bot_api.reply_message(
                event.reply_token,
                TemplateSendMessage(alt_text='carousel template', template=message_template)
            )

        # 以下 下位分類
        elif content in ['視覚障がい']:
            with psycopg2.connect(DATABASE_URL) as conn:
                with conn.cursor() as curs:
                    curs.execute("SELECT * FROM window_list WHERE subcategory = 1121 ORDER BY Id ASC")
                    db = curs.fetchall()

            result = window_list_flex(db)

            line_bot_api.reply_message(
                event.reply_token,
                FlexSendMessage(alt_text='flex template', contents=result)
            )

        elif content in ['聴覚障がい']:
            with psycopg2.connect(DATABASE_URL) as conn:
                with conn.cursor() as curs:
                    curs.execute("SELECT * FROM window_list WHERE subcategory = 1122 ORDER BY Id ASC")
                    db = curs.fetchall()

            result = window_list_flex(db)

            line_bot_api.reply_message(
                event.reply_token,
                FlexSendMessage(alt_text='flex template', contents=result)
            )

        elif content in ['肢体不自由']:
            with psycopg2.connect(DATABASE_URL) as conn:
                with conn.cursor() as curs:
                    curs.execute("SELECT * FROM window_list WHERE subcategory = 1123 ORDER BY Id ASC")
                    db = curs.fetchall()

            result = window_list_flex(db)

            line_bot_api.reply_message(
                event.reply_token,
                FlexSendMessage(alt_text='flex template', contents=result)
            )

        elif content in ['病弱障がい']:
            with psycopg2.connect(DATABASE_URL) as conn:
                with conn.cursor() as curs:
                    curs.execute("SELECT * FROM window_list WHERE subcategory = 1124 ORDER BY Id ASC")
                    db = curs.fetchall()

            result = window_list_flex(db)

            line_bot_api.reply_message(
                event.reply_token,
                FlexSendMessage(alt_text='flex template', contents=result)
            )

        elif content in ['知的障がい']:
            with psycopg2.connect(DATABASE_URL) as conn:
                with conn.cursor() as curs:
                    curs.execute("SELECT * FROM window_list WHERE subcategory = 1125 ORDER BY Id ASC")
                    db = curs.fetchall()

            result = window_list_flex(db)

            line_bot_api.reply_message(
                event.reply_token,
                FlexSendMessage(alt_text='flex template', contents=result)
            )

        elif content in ['LD・ADHD等']:
            with psycopg2.connect(DATABASE_URL) as conn:
                with conn.cursor() as curs:
                    curs.execute("SELECT * FROM window_list WHERE subcategory = 1126 ORDER BY Id ASC")
                    db = curs.fetchall()

            result = window_list_flex(db)

            line_bot_api.reply_message(
                event.reply_token,
                FlexSendMessage(alt_text='flex template', contents=result)
            )

        elif content in ['調査・文化財']:
            with psycopg2.connect(DATABASE_URL) as conn:
                with conn.cursor() as curs:
                    curs.execute("SELECT * FROM window_list WHERE subcategory = 113 ORDER BY Id ASC")
                    db = curs.fetchall()

            result = window_list_flex(db)

            line_bot_api.reply_message(
                event.reply_token,
                FlexSendMessage(alt_text='flex template', contents=result)
            )

        # 県政相談
        elif content in ['県政相談']:
            with psycopg2.connect(DATABASE_URL) as conn:
                with conn.cursor() as curs:
                    curs.execute("SELECT * FROM window_list WHERE Id = 1")
                    db = curs.fetchall()

            result = "お探しの窓口はこちらですか？\n\n" + window_info(db)
            
            review = "よかったら、今回の会話が役に立ったか教えてください！"

            review_qa = ButtonsTemplate(
                text = '今回の会話は',
                actions = [
                    PostbackTemplateAction(
                        label = '役に立った',
                        data = 'callback',
                        text = '役に立った'
                    ),
                    PostbackTemplateAction(
                        label = '役に立たなかった',
                        data = 'callback',
                        text = '役に立たなかった'
                    )
                ]
            )

            messages = [
                TextSendMessage(text=result),
                TextSendMessage(text=review),
                TemplateSendMessage(alt_text='carousel template', template=review_qa)
                ]
            line_bot_api.reply_message(event.reply_token, messages)
        
        # 指定の窓口の情報を表示
        elif content[:5] in ['窓口ID:']:
            window_id = content[5:]

            with psycopg2.connect(DATABASE_URL) as conn:
                with conn.cursor() as curs:
                    curs.execute("SELECT * FROM window_list WHERE Id = " + str(window_id))
                    db = curs.fetchall()

            # 「窓口ID:999」など、存在しない窓口IDを入力された場合の処理
            if len(db) == 0:
                response = "存在しない窓口IDが入力されました。\n" +\
                "もう一度利用する場合はボタンを押してください。"

                button = ButtonsTemplate(
                    text = 'もう一度利用する',
                    actions = [
                        PostbackTemplateAction(
                            label = 'カテゴリ選択へ',
                            data = 'callback',
                            text = 'カテゴリ選択'
                        )
                    ]
                )

                messages = [
                    TextSendMessage(text=response),
                    TemplateSendMessage(alt_text='carousel template', template=button)
                    ]
                line_bot_api.reply_message(event.reply_token, messages)


            # 見つからなかった場合の処理
            if window_id in ['1']:
                result = "見つからなかった場合はこちらからご相談ください。\n\n"
            else:
                result = "お探しの窓口はこちらですか？\n\n"

            result += window_info(db)

            review = "よかったら、今回の会話が役に立ったか教えてください！"

            review_qa = ButtonsTemplate(
                text = '今回の会話は',
                actions = [
                    PostbackTemplateAction(
                        label = '役に立った',
                        data = 'callback',
                        text = '役に立った'
                    ),
                    PostbackTemplateAction(
                        label = '役に立たなかった',
                        data = 'callback',
                        text = '役に立たなかった'
                    )
                ]
            )

            messages = [
                TextSendMessage(text=result),
                TextSendMessage(text=review),
                TemplateSendMessage(alt_text='carousel template', template=review_qa)
                ]
            line_bot_api.reply_message(event.reply_token, messages)

        # 「最初から」がタップされた場合の処理
        elif content in ['最初から']:
            response = "改めて窓口を探す際には、もう一度「温泉を探す」をタップしてください。"

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=response)) 
        
        # 「役に立った」「役に立たなかった」へのレスポンス
        elif content in ['役に立った', '役に立たなかった']:
            response = "回答ありがとうございました！\n" +\
                "もう一度利用する場合はボタンを押してください。"

            button = ButtonsTemplate(
                text = 'もう一度利用する',
                actions = [
                    PostbackTemplateAction(
                        label = '温泉を探す',
                        data = 'callback',
                        text = '温泉を探す'
                    )
                ]
            )

            messages = [
                TextSendMessage(text=response),
                TemplateSendMessage(alt_text='carousel template', template=button)
                ]
            line_bot_api.reply_message(event.reply_token, messages)

        # その他              
        else:
            response = "ごめんなさい。メッセージを処理できませんでした。"
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=response)) 

    except Exception as e:
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='type:' + str(type(e))
        'args:' + str(e.args)
        'message:' + e.message
        'e自身:' + str(e))
    )

if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)
