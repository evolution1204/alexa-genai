# Alexa開発者コンソール デプロイメントチェックリスト

## 必須反映項目

### 1. Lambda関数の更新
- [ ] lambda_function.py を最新版に更新
  - 会話履歴機能（100件）
  - null安全性の改善
  - セッション維持機能
- [ ] 保存ボタンをクリック
- [ ] デプロイボタンをクリック
- [ ] デプロイ完了の確認

### 2. 動作確認
- [ ] テストタブで「開発」を選択
- [ ] 「じぇないを開いて」でスキル起動
- [ ] 複数回の質問で会話継続を確認
- [ ] エラーが出ないことを確認

## オプション項目（DynamoDB永続化）

### AWS側の設定
- [ ] DynamoDBテーブル「AlexaConversations」を作成
- [ ] Lambda関数のIAMロールにDynamoDB権限を追加
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:DeleteItem"
        ],
        "Resource": "arn:aws:dynamodb:*:*:table/AlexaConversations"
      }
    ]
  }
  ```

### コードエディターでの設定
- [ ] dynamodb_persistence.py を新規作成
- [ ] lambda_function.pyでDynamoDB機能を有効化（必要に応じて）

## トラブルシューティング

### エラー: "Task timed out after 3.00 seconds"
→ Lambda関数のタイムアウトを10秒に延長

### エラー: "Unable to import module 'lambda_function'"
→ インデントやシンタックスエラーを確認

### エラー: "Session attributes size exceeds maximum allowed"
→ 会話履歴のサイズ制限を調整（現在100件）

## 反映後のテスト例

1. **会話の継続性テスト**
   ```
   You: じぇないを開いて
   Alexa: じぇないアシスタントへようこそ。何かお手伝いしましょうか？

   You: 富士山について教えて
   Alexa: [富士山の説明]... 他に質問はありますか？

   You: その高さは？
   Alexa: [前の文脈を理解して高さを回答]... 続けて何か聞きたいことは？
   ```

2. **長時間セッションテスト**
   - 5分以上会話を継続
   - セッションが維持されることを確認

## 更新履歴
- 2024-01-XX: 会話履歴機能追加（100件保持）
- 2024-01-XX: セッション維持機能強化
- 2024-01-XX: null安全性とエラーハンドリング改善