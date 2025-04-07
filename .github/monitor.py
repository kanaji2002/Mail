import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import hashlib
import requests
import json

target_url = os.getenv('TARGET_URL')
username = os.getenv('LOGIN_USERNAME')
password = os.getenv('LOGIN_PASSWORD')
github_token = os.getenv('GITHUB_TOKEN')
repo = os.getenv('GITHUB_REPOSITORY')

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(options=options)

try:
    driver.get(target_url)

    # ログイン処理（必要に応じて変更）
    driver.find_element(By.ID, 'username').send_keys(username)
    driver.find_element(By.ID, 'password').send_keys(password)
    driver.find_element(By.ID, 'login-button').click()

    driver.implicitly_wait(10)
    current_content = driver.page_source
    current_hash = hashlib.md5(current_content.encode()).hexdigest()

    # ハッシュファイルの読み取り
    hash_file = "previous_hash.txt"
    previous_hash = ""
    if os.path.exists(hash_file):
        with open(hash_file, 'r') as f:
            previous_hash = f.read().strip()

    if current_hash != previous_hash:
        print("変更を検出しました")
        soup = BeautifulSoup(current_content, 'html.parser')
        title = f"Website Change Detected: {soup.title.string if soup.title else 'No Title'}"

        issue_data = {
            "title": title,
            "body": f"変更が検出されました\n\n対象URL: {target_url}\n\n変更内容を確認してください",
            "labels": ["monitoring", "change-detected"]
        }

        response = requests.post(
            f"https://api.github.com/repos/{repo}/issues",
            headers={
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json"
            },
            data=json.dumps(issue_data))

        if response.status_code == 201:
            print("Issueを作成しました")
        else:
            print(f"Issue作成に失敗しました: {response.text}")

        with open(hash_file, 'w') as f:
            f.write(current_hash)
    else:
        print("変更は検出されませんでした")

except Exception as e:
    print(f"エラーが発生しました: {str(e)}")

    error_issue = {
        "title": "Website Monitor Error",
        "body": f"監視スクリプトでエラーが発生しました\n\nエラー内容: {str(e)}",
        "labels": ["monitoring", "error"]
    }

    requests.post(
        f"https://api.github.com/repos/{repo}/issues",
        headers={
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        },
        data=json.dumps(error_issue))

finally:
    driver.quit()
