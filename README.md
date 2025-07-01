# Strava GPS Heatmap Generator

Stravaにログインして過去のすべてのGPS走行データをダウンロードし、地図上にヒートマップを作成してSVG形式で保存するPythonツールです。

## 機能

- Strava APIを使用したGPSデータのダウンロード
- 走行データのヒートマップ生成
- 地図境界線（国境・州境界）の表示
- SVG形式での出力

## セットアップ

1. 必要なパッケージをインストール:
```bash
pip install -r requirements.txt
```

2. Strava APIアプリケーションを作成:
   - [Strava Developer Portal](https://developers.strava.com/)にアクセス
   - 新しいアプリケーションを作成
   - Client IDとClient Secretを取得

## 使用方法

### 1. データのダウンロード

```bash
python download_strava_data.py
```

初回実行時に`config.json`ファイルが作成されます。Strava APIの認証情報を設定してください。

### 2. ヒートマップの生成

```bash
python generate_heatmap_svg.py
```

ダウンロードしたデータからSVGヒートマップを生成します。

## 設定

`config.json`ファイルで以下の設定が可能です:

```json
{
  "strava": {
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET",
    "access_token": "YOUR_ACCESS_TOKEN"
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

- `strava_client.py`: Strava API クライアント
- `heatmap_generator.py`: ヒートマップ生成エンジン
- `map_data.py`: 地図データの取得・処理
- `svg_renderer.py`: SVG出力機能
- `download_strava_data.py`: データダウンロード用スクリプト
- `generate_heatmap_svg.py`: SVG生成用スクリプト

## 注意事項

- Strava APIには使用制限があります（15分間に100リクエスト、1日に1000リクエスト）
- 大量のアクティビティがある場合、ダウンロードに時間がかかる場合があります
- 地図データはインターネットから取得され、キャッシュされます