# 元の相互作用モデルを適用する手順

## 📝 重要
元のファイルには大量のサンプル発話（日本語347個、英語408個）が含まれています。
これらを使用することで、より自然な会話が可能になります。

## 🇯🇵 日本語版の適用

### 1. Alexaデベロッパーコンソールを開く
1. https://developer.amazon.com/alexa/console/ask
2. 「GenAI for Alexa」スキルを選択
3. 「構築」タブをクリック

### 2. 日本語モデルを適用
1. **言語タブを「Japanese (JP)」に切り替え**（重要！）
2. 左メニューから「相互作用モデル」→「JSONエディター」を選択
3. **現在の内容をすべて削除**
4. 以下のファイルの内容をコピー＆ペースト：
   ```
   /home/ochiai/vscode-claude-project/workspace/alexa/genai/alexa-genai/skill-package/interactionModels/custom/ja-JP.json
   ```

### 3. 保存とビルド
1. 「Save Model」をクリック
2. 「Build Model」をクリック
3. ビルド完了を待つ（2-3分）

## 🇺🇸 英語版の適用

### 1. 英語モデルに切り替え
1. **言語タブを「English (US)」に切り替え**（重要！）
2. 「相互作用モデル」→「JSONエディター」を選択

### 2. 英語モデルを適用
1. **現在の内容をすべて削除**
2. 以下のファイルの内容をコピー＆ペースト：
   ```
   /home/ochiai/vscode-claude-project/workspace/alexa/genai/alexa-genai/skill-package/interactionModels/custom/en-US.json
   ```

### 3. 保存とビルド
1. 「Save Model」をクリック
2. 「Build Model」をクリック
3. ビルド完了を待つ（2-3分）

## ✅ 適用後の確認

### 日本語版で含まれる機能
- 基本的な質問（347パターン）
- 創作系の依頼（歌、物語、詩など）
- 感情表現（楽しませて、驚かせて、など）
- 思考・検討系（考えて、提案して、など）
- 分析・評価系（分析して、評価して、など）

### 英語版で含まれる機能
- 基本的な質問（408パターン）
- 創作系の依頼（songs, stories, poems）
- 感情表現（make me laugh, surprise me）
- 思考・検討系（think about, suggest）
- 分析・評価系（analyze, evaluate）

## 🔍 テスト例

### 日本語テスト
```
じぇないを開いて
人工知能について教えて
ドラゴンの物語を作って
笑わせて
将来の技術について考えて
```

### 英語テスト
```
open gen ai
tell me about artificial intelligence
create a story about dragons
make me laugh
think about future technology
```

## ⚠️ 注意事項

1. **言語タブの確認**
   - 各言語の設定時は、必ず言語タブが正しいことを確認
   - 日本語：「Japanese (JP)」
   - 英語：「English (US)」

2. **ビルドエラーが出た場合**
   - AMAZON.FallbackIntentがあることを確認
   - 呼び出し名が正しいことを確認（じぇない/gen ai）

3. **大量のサンプル発話について**
   - Alexaは最大30,000個のサンプル発話をサポート
   - 現在の数（347+408）は問題なし

## 📁 ファイルパス

### 日本語モデル（ja-JP.json）
```
/home/ochiai/vscode-claude-project/workspace/alexa/genai/alexa-genai/skill-package/interactionModels/custom/ja-JP.json
```
- GptQueryIntent: 347サンプル発話
- AMAZON.CancelIntent
- AMAZON.HelpIntent
- AMAZON.StopIntent
- AMAZON.NavigateHomeIntent

### 英語モデル（en-US.json）
```
/home/ochiai/vscode-claude-project/workspace/alexa/genai/alexa-genai/skill-package/interactionModels/custom/en-US.json
```
- GptQueryIntent: 408サンプル発話
- AMAZON.CancelIntent
- AMAZON.HelpIntent
- AMAZON.StopIntent
- AMAZON.NavigateHomeIntent
- AMAZON.FallbackIntent

## 🚀 適用後の動作

元の相互作用モデルを適用すると：
1. **より自然な会話**が可能になる
2. **様々な表現パターン**に対応
3. **創作・感情表現**にも対応
4. **思考・分析**のリクエストも処理可能

これで、元の設計通りの豊富な機能を持つAlexaスキルが動作します！