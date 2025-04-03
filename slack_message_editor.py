import re
import os
import streamlit as st
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# ページ設定
st.set_page_config(page_title="延岡学園 - Slackメッセージ編集ツール", page_icon="💬")
st.markdown("<h2 style='margin-bottom:0px;'>延岡学園 Slackボットメッセージ編集ツール</h2>", unsafe_allow_html=True)
# st.title("KCP Slackボットメッセージ編集ツール")

# SlackApiErrorのデバッグ情報を詳細に表示する関数（先に定義）
def display_error_details(error):
    st.error(f"エラーが発生しました: {error.response['error']}")
    st.error(f"詳細情報: {error.response.get('needed', 'なし')}")
    st.error(f"現在の権限: {error.response.get('provided', 'なし')}")
    st.json(error.response)  # エラーレスポンスの全内容を表示

# Streamlitのシークレット機能を使用
# @st.cache_resource
def get_slack_client():
    bot_token = st.secrets.get("SLACK_BOT_TOKEN", os.environ.get("SLACK_BOT_TOKEN"))
    if not bot_token:
        st.error("SLACK_BOT_TOKENが設定されていません。")
        st.stop()
    return WebClient(token=bot_token)

slack_client = get_slack_client()

# SlackメッセージURLからタイムスタンプとチャンネルIDを抽出する関数
def extract_info_from_url(url):
    # 例: https://workspace.slack.com/archives/C01234ABCDE/p1234567890123456
    pattern = r"archives/([A-Z0-9]+)/p(\d+)"
    match = re.search(pattern, url)
    
    if not match:
        return None, None
    
    channel_id = match.group(1)
    ts_str = match.group(2)
    
    # タイムスタンプの形式を変換（Slack APIの形式に合わせる）
    if len(ts_str) > 10:
        ts = ts_str[:10] + "." + ts_str[10:]
    else:
        ts = ts_str
    
    return channel_id, ts

# メイン処理
st.write("Slackボットが投稿したメッセージを編集するツールです。")

# メッセージURLの入力
message_url = st.text_input("編集したいSlackメッセージのURLを入力してください：")

if message_url:
    channel_id, ts = extract_info_from_url(message_url)
    
    if not channel_id or not ts:
        st.error("無効なSlackメッセージURLです。正しいURLを入力してください。")
    else:
        st.success(f"チャンネルID: {channel_id}, タイムスタンプ: {ts}")
        
        # 現在のメッセージを取得して表示
        try:
            result = slack_client.conversations_history(
                channel=channel_id,
                latest=ts,
                limit=1,
                inclusive=True
            )
            if result["messages"] and len(result["messages"]) > 0:
                current_message = result["messages"][0]["text"]
                st.subheader("現在のメッセージ")
                st.text_area("現在の内容", current_message, height=150, disabled=True)
                
                # 新しいメッセージ内容の入力
                st.subheader("新しいメッセージ")
                new_message = st.text_area("編集後の内容", current_message, height=200)
                
                # 更新ボタン
                if st.button("メッセージを更新"):
                    try:
                        result = slack_client.chat_update(
                            channel=channel_id,
                            ts=ts,
                            text=new_message
                        )
                        st.success("メッセージが正常に更新されました！")
                    except SlackApiError as e:
                        display_error_details(e)
            else:
                st.error("指定されたメッセージが見つかりませんでした。")
        except SlackApiError as e:
            display_error_details(e) 
