# ツール活用事例検索サイト

## 概要
Flask製の「ツール活用事例検索サイト」です。Zenn・Qiita・はてなブログからツール名で記事を検索し、判定結果をGoogleスプレッドシートまたはSQLiteに保存します。

## 本番URL例
https://toolcases.onrender.com/

## セットアップ手順（ローカル開発）
1. 必要なファイルを配置
   - `credentials.json`（Googleサービスアカウント鍵）をプロジェクト直下に配置
2. 依存パッケージのインストール
   ```sh
   pip install -r requirements.txt
   ```
3. DB初期化
   ```sh
   sqlite3 app.db < schema.sql
   ```
4. .envファイル作成（.env.sampleをコピーして編集）
   ```sh
   cp .env.sample .env
   ```
5. サーバ起動
   ```sh
   docker-compose up
   # または
   python app.py
   ```

## デプロイ手順（Render）
1. Renderで新規Webサービス作成（Dockerfile指定）
2. render.yamlを使い、Blueprintデプロイ
3. scripts/setup_render.sh でCLI自動化
4. 環境変数はrender.yamlまたはRender管理画面で設定
5. デプロイ後、`https://toolcases.onrender.com/` でアクセス

## CI/CD（GitHub Actions）
- `.github/workflows/deploy.yml` で mainブランチpush時に自動デプロイ
- 必要なSecrets:
  - `RENDER_API_KEY`（Render API Key）
  - `RENDER_SA_JSON`（GoogleサービスアカウントJSONをbase64で格納）

## 主要環境変数
- `GSHEET_ID`：GoogleスプレッドシートID
- `SHEET_NAME`：シート名（省略時Sheet1）
- `CREDENTIALS_JSON`：サービスアカウント鍵ファイル名
- `SECRET_KEY`：Flaskのセッション用シークレット

## 開発Tips
- Black/isortでコード整形
- 公式API優先、なければBeautifulSoup4＋requests（requests-cacheで1hキャッシュ）
- DBスキーマはschema.sql
- JavaScriptは/static/js/main.jsに集約

## 注意事項
- `credentials.json`は必ず.gitignoreに追加してください
- Google Sheets API有効化・サービスアカウントのシート共有が必要です 