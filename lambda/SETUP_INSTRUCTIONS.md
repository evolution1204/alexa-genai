# Lambda Function Setup Instructions

## Important Security Notice

**⚠️ NEVER commit your API key to GitHub or any public repository!**

## Setting up the OpenAI API Key

### For Alexa Developer Console (Recommended)

1. Go to the Alexa Developer Console
2. Navigate to your skill's **Code** tab
3. Find the `.env` file in the Lambda folder (or create it if it doesn't exist)
4. Add your API key:
   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```
5. Save and deploy

### For Local Testing

1. Create a `.env` file in the lambda directory:
   ```bash
   cd lambda
   echo "OPENAI_API_KEY=sk-your-api-key-here" > .env
   ```

2. If using AWS Lambda directly, set it in the Lambda console:
   - Go to your Lambda function
   - Configuration → Environment variables
   - Add key: `OPENAI_API_KEY`
   - Add value: Your OpenAI API key

### For GitHub (Using Secrets)

1. Go to your GitHub repository
2. Settings → Secrets and variables → Actions
3. New repository secret
4. Name: `OPENAI_API_KEY`
5. Value: Your OpenAI API key

## Testing the Configuration

The Lambda function will log a warning if the API key is not configured. Check CloudWatch logs for:
- "OpenAI API key not configured" - means the key is missing
- No warning - means the key is properly set

## Current Configuration

The Lambda function is now configured to:
- Read the API key from the `OPENAI_API_KEY` environment variable
- Use GPT-4 model (GPT-5 doesn't exist yet)
- Support both Japanese and English languages
- Return appropriate error messages if the API key is missing

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