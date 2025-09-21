# 日本語スキル動作不良デバッグチェックリスト

## 現在の状況
- ✅ 日本語（日本）が言語設定に追加されている
- ❌ 日本語で「すみません、お役に立てません」エラー
- ✅ 英語では "Here's what I found" と部分的に動作

## 確認手順

### 1. 日本語の呼び出し名を確認

Alexaデベロッパーコンソールで：

1. **言語タブを「日本語」に切り替える**（重要！）
   - 画面上部に言語選択があるはずです
   - 「日本語」または「ja-JP」を選択

2. 左メニューから「呼び出し」→「スキルの呼び出し名」を選択

3. **実際に表示されている呼び出し名を確認**
   - 期待値：`じぇない`（ひらがな）
   - もし異なる場合は修正が必要

### 2. 日本語の相互作用モデルを確認

1. **言語タブが「日本語」になっていることを再確認**

2. 左メニューから「相互作用モデル」→「インテント」を選択

3. 以下のインテントが存在するか確認：
   - GptQueryIntent
   - AMAZON.CancelIntent
   - AMAZON.HelpIntent
   - AMAZON.StopIntent
   - AMAZON.FallbackIntent（重要！）

4. GptQueryIntentをクリックして、サンプル発話を確認

### 3. JSONエディターで確認

1. 「相互作用モデル」→「JSONエディター」を選択

2. 表示されているJSONの最初の部分を確認：
```json
{
    "interactionModel": {
        "languageModel": {
            "invocationName": "???ここを確認???"
```

3. invocationNameが何になっているか確認

### 4. エンドポイント設定を確認

1. **言語タブを「日本語」に切り替えた状態で**

2. 「エンドポイント」を選択

3. 以下を確認：
   - AWS Lambda ARNが設定されているか
   - デフォルトリージョンのARNがあるか
   - スキルIDの検証が有効になっているか

### 5. テストシミュレーターでの確認

1. 「テスト」タブを開く

2. **言語を「日本語（日本）」に設定**

3. **音声ではなくテキスト入力**で以下を試す：

#### パターンA：ひらがな
```
じぇないを開いて
```

#### パターンB：カタカナ
```
ジェナイを開いて
```

#### パターンC：英字混じり
```
genaiを開いて
```

### 6. CloudWatchログの確認（可能であれば）

AWS Consoleにアクセスできる場合：

1. CloudWatch → ログ → ロググループ
2. `/aws/lambda/[Lambda関数名]`を探す
3. 最新のログストリームを開く
4. 日本語のリクエストが到達しているか確認

## トラブルシューティング

### ケース1：呼び出し名が設定されていない

もし日本語タブで呼び出し名が空欄の場合：

1. 呼び出し名に `じぇない` を入力
2. 「モデルを保存」をクリック
3. 「モデルをビルド」をクリック
4. ビルド完了後にテスト

### ケース2：FallbackIntentがない

AMAZON.FallbackIntentは日本語で必須です：

1. 「インテント」→「インテントを追加」
2. 「Alexaのビルトインインテントを使用」
3. 「AMAZON.FallbackIntent」を選択
4. 追加後、保存とビルド

### ケース3：エンドポイントが未設定

1. Lambda関数のARNをコピー
   - 形式：`arn:aws:lambda:region:account:function:function-name`

2. エンドポイントに貼り付け

3. 保存

## 最小限のテスト用設定

もし上記がうまくいかない場合、以下の最小構成で試す：

### JSONエディターに直接貼り付け：

```json
{
    "interactionModel": {
        "languageModel": {
            "invocationName": "じぇない",
            "intents": [
                {
                    "name": "AMAZON.FallbackIntent",
                    "samples": []
                },
                {
                    "name": "AMAZON.CancelIntent",
                    "samples": []
                },
                {
                    "name": "AMAZON.HelpIntent",
                    "samples": []
                },
                {
                    "name": "AMAZON.StopIntent",
                    "samples": []
                }
            ],
            "types": []
        }
    }
}
```

これで最低限の起動テストができます。

## 報告事項

以下の情報を教えてください：

1. 日本語タブでの呼び出し名：_______
2. GptQueryIntentの有無：_______
3. AMAZON.FallbackIntentの有無：_______
4. エンドポイントARNの設定：_______
5. JSONのinvocationName：_______