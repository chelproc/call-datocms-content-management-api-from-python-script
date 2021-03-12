"""
DatoCMS Content Management API を Python で扱うサンプル
https://www.datocms.com/docs/content-management-api
"""

import requests

# 以下の2項目はスクリプト起動前に設定が必要
# Settings -> Models -> モデル名 -> Edit model で確認できる6桁の数字
model_id = ""
# Settings -> API Token で確認できる文字列
token = ""

# DatoCMS Content Management APIの大半を呼ぶのに必要なHTTPヘッダ
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/json"  # DatoCMSのAPIでは必須
}

def list_records():
    """
    データを取得する例
    https://www.datocms.com/docs/content-management-api/resources/item/instances
    """
    response = requests.get(
        "https://site-api.datocms.com/items",
        params={
            "filter[type]": model_id,
            "nested": True,
        },
        headers=headers,
    )
    response_json = response.json()  # JSONで帰ってくるのでパースする
    print(response_json)


def create_record():
    """
    データを作成する例
    https://www.datocms.com/docs/content-management-api/resources/item/create
    """
    response = requests.post(
        "https://site-api.datocms.com/items",
        headers=headers,
        json={
            "data": {
                "type": "item",
                "attributes": {
                    # 文字列型のフィールドなら文字列など、形式が決まっている
                    # 詳しくは Field type values セクションを参照
                    "title": "test"
                },
                "relationships": {
                    "item_type": {
                        "data": {
                            "type": "item_type",
                            "id": model_id  # 紛らわしいがこれがないと作成するモデルが分からない
                        }
                    }
                }
            }
        })
    response_json = response.json()
    print(response_json["data"]["id"])  # response.data.idを控えておく


def upload_file():
    """
    ファイルをアップロードする例（難しい）
    https://www.datocms.com/docs/content-management-api/resources/upload
    """
    local_file_path = "sample.jpg"
    remote_file_name = "filename.jpg"  # DatoCMS上での名前

    # Step 1: Request an upload permission
    upload_request_response = requests.post(
        "https://site-api.datocms.com/upload-requests",
        headers=headers,
        json={
            "data": {
                "type": "upload_request",
                "attributes": {
                    "filename": remote_file_name
                }
            }
        }
    )
    response_json = upload_request_response.json()
    s3_file_path = response_json["data"]["id"]  # アップロードされるファイルのS3上でのパス
    s3_url = response_json["data"]["attributes"]["url"]  # アップロード先のS3のパス

    # Step 2: Upload file to the storage bucket
    with open(local_file_path, "rb") as f:  # バイナリファイル扱いで開く
        # AWSにアップロードしているだけなのでDatoCMSの認証情報は使わない
        # data引数にファイルポインタを与えるとrequestsがいい感じにアップロードしてくれる
        requests.put(s3_url, data=f)

    # Step 3: Create the actual upload (and get back the async job)
    upload_response = requests.post(
        "https://site-api.datocms.com/uploads",
        headers=headers,
        json={
            "data": {
                "type": "upload",
                "attributes": {
                    "path": s3_file_path,
                }
            }
        }
    )

    upload_response_json = upload_response.json()
    print(upload_response_json["data"]["id"])  # アップロードされたファイルのID
