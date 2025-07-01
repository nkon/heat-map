# Strava GPS Heatmap Generator

Stravaにログインして過去のすべてのGPS走行データをダウンロードし、地図上にヒートマップを作成してSVG形式で保存するPythonツールです。

## 機能

- Strava APIを使用したGPSデータのダウンロード（レートリミット対応）
- 自動トークンリフレッシュ機能
- 個別アクティビティファイルの自動保存
- 走行データのヒートマップ生成
- 地図境界線（国境・州境界）の表示
- SVG形式での高品質出力
- 時系列ファイル名管理

## セットアップ

### 仮想環境の作成（推奨）
```bash
# 仮想環境を作成
python3 -m venv venv
source venv/bin/activate

# 必要なパッケージをインストール
pip install -r requirements.txt
```

2. Strava APIアプリケーションを作成:
   - [Strava Developer Portal](https://developers.strava.com/)にアクセス
   - 新しいアプリケーションを作成
   - Client IDとClient Secretを取得

## 使用方法

### 1. 認証状態の確認
```bash
# レートリミット状況を確認
python check_rate_limit.py
```

### 2. データのダウンロード

#### 方法A: 統合ダウンロード（推奨）
```bash
python download_strava_data.py
```

#### 方法B: 個別アクティビティダウンロード
```bash
python download_individual_activities.py
```

### 3. GPSデータの統合（個別ダウンロードを使用した場合）
```bash
python consolidate_gps_data.py
```

### 4. ヒートマップの生成
```bash
python generate_heatmap_svg.py
```

初回実行時に`config.json`ファイルが作成されます。Strava APIの認証情報を設定してください。

## 設定

`config.json`ファイルで以下の設定が可能です:

```json
{
  "strava": {
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "access_token": "YOUR_ACCESS_TOKEN",
    "refresh_token": "YOUR_REFRESH_TOKEN"
  },
  "data": {
    "output_dir": "strava_data",
    "gps_data_file": "gps_data.json"
  },
  "output": {
    "filename": "strava_heatmap.svg",
    "width": 1200,
    "height": 800
  },
  "style": {
    "track_color": "#dc3545",
    "track_width": "1.5",
    "boundary_color": "#dee2e6",
    "boundary_width": "0.5"
  }
}
```

## ファイル構成

### コアモジュール
- `strava_client.py`: Strava API クライアント（自動トークンリフレッシュ、レートリミット対応）
- `heatmap_generator.py`: ヒートマップ生成エンジン
- `map_data.py`: 地図データの取得・処理
- `svg_renderer.py`: SVG出力機能

### 実行スクリプト
- `download_strava_data.py`: 統合データダウンロード
- `download_individual_activities.py`: 個別アクティビティダウンロード
- `consolidate_gps_data.py`: 個別ファイルの統合
- `generate_heatmap_svg.py`: SVG生成

### ユーティリティ
- `check_rate_limit.py`: API制限状況確認
- `get_refresh_token.py`: OAuth認証ヘルパー
- `wait_and_download.py`: 制限回避ダウンロード

## データ管理

### ファイル命名規則
- `activity_YYYYMMDD_ID_name.json`: 個別アクティビティファイル
- `gps_data_YYYYMMDD_HHMMSS.json`: 統合GPSデータ（タイムスタンプ付き）
- `gps_data_latest.json`: 最新のGPSデータへのリンク
- `athlete_info_latest.json`: 最新のアスリート情報

### 出力ファイル
- `strava_heatmap.svg`: 生成されたヒートマップ
- `map_cache/`: 地図境界データキャッシュ

## 注意事項

- **APIレートリミット**: 15分間に100リクエスト、1日に1000リクエスト
- **自動制限回避**: アプリケーションが自動的に制限を検出し待機します
- **トークン管理**: アクセストークンの期限切れを自動的に検出・更新
- **データ保存**: 個別アクティビティファイルにより段階的なダウンロードが可能
- **地理的範囲**: 現在のデータは北米西部〜中西部をカバー

## トラブルシューティング

### 認証エラー
```bash
python get_refresh_token.py  # 新しいトークンを取得
```

### レートリミット超過
```bash
python check_rate_limit.py  # 現在の使用状況を確認
```

### データファイル問題
```bash
python consolidate_gps_data.py  # データを再統合
```