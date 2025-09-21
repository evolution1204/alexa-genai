# 段階的ビルドテストガイド

## 目的
ビルドエラーの原因を特定するため、段階的にJSONを拡張していきます。

## テスト手順

### Step 1: 最小構成（ビルトインインテントのみ）
**ファイル**: `build_test_step1.json`

1. Alexaデベロッパーコンソールを開く
2. 言語タブを「Japanese (JP)」に切り替え
3. JSONエディターを開く
4. `build_test_step1.json`の内容を貼り付け
5. Save Model → Build Model

**期待結果**: ビルド成功

---

### Step 2: TestIntentを追加
**ファイル**: `build_test_step2.json`

Step 1が成功したら：
1. JSONエディターに`build_test_step2.json`を貼り付け
2. Save Model → Build Model

**追加内容**: TestIntent（3個のサンプル発話）

---

### Step 3: GptQueryIntent（5個のサンプル）
**ファイル**: `build_test_step3.json`

Step 2が成功したら：
1. JSONエディターに`build_test_step3.json`を貼り付け
2. Save Model → Build Model

**追加内容**: GptQueryIntent（5個のサンプル発話とスロット）

---

### Step 4: GptQueryIntent（20個のサンプル）
**ファイル**: `build_test_step4.json`

Step 3が成功したら：
1. JSONエディターに`build_test_step4.json`を貼り付け
2. Save Model → Build Model

**追加内容**: GptQueryIntentのサンプル発話を20個に拡張

---

## どこでエラーが発生するか確認

- **Step 1で失敗**: 基本的な設定の問題
- **Step 2で失敗**: カスタムインテントの問題
- **Step 3で失敗**: スロットまたはSearchQueryタイプの問題
- **Step 4で失敗**: サンプル発話の数または内容の問題

## エラーが特定できたら

### パターン1: 特定のサンプル発話が問題
- 問題のある発話を特定して除外
- 特殊文字や長さを確認

### パターン2: サンプル発話の数が問題
- 100個ずつなど、段階的に増やす
- Alexaの制限（30,000個）には余裕があるはず

### パターン3: スロットタイプの問題
- AMAZON.SearchQueryの代わりにカスタムスロットタイプを試す

## 次のステップ用ファイル

必要に応じて以下も作成可能：
- `build_test_step5.json`: 50個のサンプル発話
- `build_test_step6.json`: 100個のサンプル発話
- `build_test_step7.json`: 200個のサンプル発話
- `build_test_final.json`: 元の347個すべて

## 英語版も同様に

英語版でも同じ問題が発生する場合は、同様の段階的アプローチを適用：
1. `build_test_step1_en.json`: ビルトインのみ
2. `build_test_step2_en.json`: TestIntent追加
3. 以降、段階的に拡張