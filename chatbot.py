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
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]
DATABASE_URL = os.environ.get('DATABASE_URL')

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

# Pythonでは呼び出す行より上に記述しないとエラーになる

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
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

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
    content = event.message.text # メッセージの内容を取得する
    if content in ['温泉を探す']:
        # CarouselColumn内は3つないと動作しない
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
            ),
             CarouselColumn(
                text='場所より景色や泉質で検索',
                title='地域指定がない方',
                actions=[
                    PostbackTemplateAction(
                        label='景色',
                        data='callback',
                        text='景色'
                    ),
                    PostbackTemplateAction(
                        label='温泉の泉質',
                        data='callback',
                        text='温泉の泉質'
                    ),
                    PostbackTemplateAction(
                        label='Coming soon',
                        data='callback',
                        text='Coming soon'
                    )
                ]
             )
        ]
        message_template = CarouselTemplate(columns=carousel_columns)
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(alt_text='carousel template', template=message_template)
        )
        
    # その他              
    else:
        response = "ごめんなさい。メッセージを処理できませんでした。"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=response)) 


if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)

