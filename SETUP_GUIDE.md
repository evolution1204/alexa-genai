# Alexa カスタムスキル セットアップガイド

このガイドでは、空のカスタムスキルに GenAI Assistant のコードを展開する手順を説明します。

## 📝 前提条件

- Alexa Developer Consoleでカスタムスキルを作成済み
- GitHubリポジトリ: https://github.com/evolution1204/alexa-genai

## 🚀 セットアップ手順

### 1. インタラクションモデルの設定

#### 1.1 言語の選択
1. Alexa Developer Consoleでスキルを開く
2. 「ビルド」タブを選択
3. 画面上部のドロップダウンから設定したい言語を選択：
   - 日本語: `Japanese (JP)`
   - 英語: `English (US)`

#### 1.2 JSONエディタでモデルを貼り付け
1. 左メニューから `Interaction Model` → `JSON Editor` を選択
2. 既存のJSONを全て削除
3. 以下のファイルの内容をコピー＆ペースト：
   - **日本語**: `skill-package/interactionModels/custom/ja-JP.json`
   - **英語**: `skill-package/interactionModels/custom/en-US.json`
4. `Save Model` をクリック
5. `Build Model` をクリック

### 2. Lambda関数のセットアップ

#### オプションA: Alexa-hosted (推奨)

1. 「コード」タブを選択
2. `lambda_function.py` を開く
3. 既存のコードを全て削除
4. GitHubの `lambda/lambda_function.py` の内容をコピー＆ペースト
5. `requirements.txt` を開く
6. 以下の内容に置き換え：
```
ask-sdk-core==1.19.0
boto3==1.28.78
requests>=2.20.0
```
7. `Deploy` をクリック

#### オプションB: 独自のAWS Lambda

##### Lambda関数の作成
1. AWS Lambdaコンソール (https://console.aws.amazon.com/lambda) にアクセス
2. 「関数の作成」をクリック
3. 以下の設定で作成：
   - 関数名: `alexa-genai-function`
   - ランタイム: `Python 3.9`
   - アーキテクチャ: `x86_64`

##### コードのアップロード
1. 作成した関数を開く
2. 「コード」タブで `lambda_function.py` の内容を貼り付け
3. 「Deploy」をクリック

##### 依存関係の追加
1. ローカルで以下を実行：
```bash
mkdir lambda-package
cd lambda-package
pip install ask-sdk-core==1.19.0 boto3==1.28.78 requests -t .
cp ../lambda/lambda_function.py .
zip -r ../deployment-package.zip .
```
2. AWS Lambdaコンソールで「アップロード元」→「.zipファイル」を選択
3. 作成したzipファイルをアップロード

##### Alexaトリガーの追加
1. Lambda関数の「設定」→「トリガー」を選択
2. 「トリガーを追加」をクリック
3. 「Alexa Skills Kit」を選択
4. スキルIDを入力（Developer ConsoleのエンドポイントセクションにあるSkill ID）

##### エンドポイントの設定
1. Alexa Developer Consoleに戻る
2. 「ビルド」→「エンドポイント」を選択
3. 「AWS Lambda ARN」を選択
4. デフォルトリージョンにLambda関数のARNを入力
5. 「エンドポイントを保存」をクリック

### 3. OpenAI APIキーの設定

#### 重要: APIキーを設定する
Lambda関数の13行目にあるAPIキーを設定する必要があります：

```python
# 変更前
api_key = "YOUR_API_KEY"

# 変更後（実際のAPIキーを入力）
api_key = "sk-xxxxxxxxxxxxxxxxxxxxx"
```

**セキュリティ推奨**: 環境変数を使用する場合：

1. AWS Lambda（またはAlexa-hosted）で環境変数を設定：
   - キー: `OPENAI_API_KEY`
   - 値: 実際のAPIキー

2. コードを修正：
```python
import os
api_key = os.getenv("OPENAI_API_KEY", "YOUR_API_KEY")
```

### 4. スキル情報の設定

1. 「配布」タブを選択
2. 「スキルのプレビュー」で以下を設定：
   - **公開名**: GenAI Assistant
   - **一行説明**: GPT-5を使用したAIアシスタント
   - **詳細な説明**: OpenAIのGPT-5モデルを使用して、質問への回答、創作活動、様々なタスクのサポートを行うインテリジェントなAlexaスキルです。
   - **サンプルフレーズ**:
     - アレクサ、ジェナイを開いて
     - アレクサ、ジェナイで天気について教えて
     - アレクサ、ジェナイで物語を作って
   - **カテゴリ**: 教育・レファレンス

### 5. テスト

1. 「テスト」タブを選択
2. 「開発中」を有効にする
3. テスト方法：
   - テキスト入力: `jenai を開いて`
   - 音声: 「アレクサ、ジェナイを開いて」

### 6. トラブルシューティング

#### エラー: "There was a problem with the requested skill's response"
- Lambda関数のログを確認（CloudWatch Logs）
- APIキーが正しく設定されているか確認
- requirements.txtの依存関係が正しくインストールされているか確認

#### エラー: "Skill model is not built"
- 「ビルド」タブで「Build Model」をクリック
- ビルドが完了するまで待つ（通常1-2分）

#### エラー: "Invalid API key"
- OpenAI APIキーが正しいか確認
- APIキーの前後に余分なスペースがないか確認

## 📊 動作確認項目

- [ ] インタラクションモデルがビルド成功
- [ ] Lambda関数がデプロイ成功
- [ ] APIキーが設定済み
- [ ] テストで「ジェナイを開いて」が動作
- [ ] 質問に対する応答が返ってくる
- [ ] 日本語と英語の自動判定が動作

## 🔗 参考リンク

- [Alexa Skills Kit Documentation](https://developer.amazon.com/ja-JP/docs/alexa/ask-overviews/what-is-the-alexa-skills-kit.html)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [OpenAI API Documentation](https://platform.openai.com/docs)

## 📝 注意事項

1. **APIキーの管理**: OpenAI APIキーは機密情報です。GitHubにコミットしないよう注意してください。
2. **コスト管理**: GPT-5の使用には料金がかかります。使用量を監視してください。
3. **レート制限**: OpenAI APIにはレート制限があります。必要に応じて調整してください。

---

問題が発生した場合は、CloudWatch Logs（AWS Lambda）またはコードエディタのログ（Alexa-hosted）を確認してください。