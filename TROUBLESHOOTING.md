# 🚨 トラブルシューティング

## 問題：「ぴこを開いて」で「すみません、お役に立てません」

この問題には複数の原因が考えられます：

### 1. インタラクションモデルのインボケーション名の確認

現在のja-JP.jsonを確認したところ：
```json
"invocationName": "じぇない"
```

これが原因の可能性があります。

### 修正方法：

#### A. Alexa開発者コンソールで修正

1. **Alexa開発者コンソール**にログイン
2. スキルを選択
3. **ビルド** → **呼び出し名**
4. 以下のいずれかに変更：
   - `ぴこ`
   - `ぴこアシスタント`
   - または現在の設定通り「じぇない」を使う

#### B. JSONエディターで修正

1. **ビルド** → **JSONエディター**
2. 以下の部分を修正：

```json
{
    "interactionModel": {
        "languageModel": {
            "invocationName": "ぴこ",  // ← "じぇない"から変更
```

### 2. Lambda関数が正しくリンクされているか確認

#### Alexa開発者コンソールで確認：

1. **ビルド** → **エンドポイント**
2. **AWS Lambda ARN** が正しく設定されているか確認
3. デフォルトリージョンのARNが設定されていることを確認

例：
```
arn:aws:lambda:us-west-2:123456789:function:your-function-name
```

### 3. Lambda関数のトリガー設定

#### AWS Lambdaコンソールで確認：

1. Lambda関数を開く
2. **設定** → **トリガー**
3. **Alexa Skills Kit** がトリガーとして追加されているか確認
4. スキルIDが正しく設定されているか確認

スキルIDの例：
```
amzn1.ask.skill.xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### 4. Lambda関数のハンドラー設定

#### AWS Lambdaコンソールで確認：

1. **設定** → **一般設定**
2. **ハンドラー** が以下になっているか確認：
```
lambda_function.lambda_handler
```

### 5. 必要な修正を適用

以下のコマンドでLambda関数を更新：

```bash
# 1. Lambda関数のディレクトリに移動
cd /home/ochiai/vscode-claude-project/workspace/alexa/genai/alexa-genai/lambda

# 2. 依存関係をインストール（ローカルテスト用）
pip install ask-sdk-core -t .

# 3. ZIPファイルを作成
zip -r lambda-function.zip . -x "*.pyc" -x "__pycache__/*" -x "test_*.py" -x "*.md"

# 4. Lambda関数を更新
aws lambda update-function-code \
    --function-name [あなたの関数名] \
    --zip-file fileb://lambda-function.zip
```

### 6. Alexa開発者コンソールでのテスト

インタラクションモデルをビルドした後：

1. **テスト** タブに移動
2. 「開発中」を選択
3. 以下を試す：

```
あなた: アレクサ、ぴこを開いて
Alexa: ぴこアシスタントへようこそ。質問をどうぞ。

あなた: テストです
Alexa: （応答）
```

### 7. CloudWatchログの確認

Lambda関数が呼ばれているか確認：

1. AWS CloudWatchコンソール
2. **ロググループ** → `/aws/lambda/[関数名]`
3. 最新のログストリームを確認

期待されるログ：
```
### HANDLER READY
>>> LaunchRequest
```

## チェックリスト

- [ ] インボケーション名が正しい（「ぴこ」または設定した名前）
- [ ] Lambda関数のARNがAlexaスキルに設定されている
- [ ] Lambda関数にAlexa Skills Kitトリガーが設定されている
- [ ] インタラクションモデルがビルドされている
- [ ] CatchAllExceptionHandlerが追加されている（修正済み）
- [ ] Lambda関数が最新バージョンにデプロイされている

## 次のステップ

上記のチェックリストを確認し、特に：
1. **インボケーション名を「ぴこ」に変更**
2. **インタラクションモデルを再ビルド**
3. **Lambda関数を再デプロイ**

これで「ぴこを開いて」が正常に動作するはずです。