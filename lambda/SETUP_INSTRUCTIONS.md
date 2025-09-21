# Lambda Function Setup Instructions

## APIキーの設定

### 直接設定方式

1. Alexa Developer Consoleにアクセス
2. スキルの**Code**タブを開く
3. `lambda_function.py`を編集
4. 13行目のAPIキーを設定:
   ```python
   api_key = "sk-your-actual-api-key-here"  # ここにAPIキーを直接設定してください
   ```
5. Save and Deploy

## Testing the Configuration

The Lambda function will log a warning if the API key is not configured. Check CloudWatch logs for:
- "OpenAI API key not configured" - means the key is missing
- No warning - means the key is properly set

## 現在の設定

Lambda関数は以下のように設定されています:
- APIキーは直接コードに記載
- GPT-5モデルを使用（gpt-5-mini設定）
- 日本語と英語の両方をサポート
- APIキーが未設定の場合はエラーメッセージを返す

## Troubleshooting

### If you get "APIキーが設定されていません" or "API key not configured"
- The environment variable is not set
- Check the spelling: must be exactly `OPENAI_API_KEY`
- Make sure you've deployed after adding the environment variable

### If you get authentication errors from OpenAI
- Your API key might be invalid or expired
- Check your OpenAI account for API key status
- Ensure the key starts with `sk-`

## Build Testing

Use the incremental test files to identify build issues:

1. **Step 1**: `build_test_step1.json` / `build_test_step1_en.json`
   - Minimal configuration with built-in intents only

2. **Step 2**: `build_test_step2.json` / `build_test_step2_en.json`
   - Adds TestIntent with 3 samples

3. **Step 3**: `build_test_step3.json` / `build_test_step3_en.json`
   - Adds GptQueryIntent with 5 samples

4. **Step 4**: `build_test_step4.json` / `build_test_step4_en.json`
   - Expands GptQueryIntent to 20 samples

Test each step in the Alexa Developer Console to identify which utterances cause build failures.