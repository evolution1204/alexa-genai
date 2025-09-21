# Alexa GenAI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Enhance your Alexa with advanced Generative AI capabilities.

This repository contains an Alexa skill that integrates with OpenAI's API to provide intelligent, context-aware responses using state-of-the-art language models.

<div align="center">
  <img src="images/test.png" />
</div>

## Prerequisites

- An [Amazon Developer account](https://developer.amazon.com/)
- An [OpenAI API key](https://platform.openai.com/api-keys)

## Quick Start - Import from GitHub

### 1.
Log in to your Amazon Developer account and navigate to the [Alexa Developer Console](https://developer.amazon.com/alexa/console/ask).

### 2.
Click on "Create Skill" and name the skill "GenAI". Choose the primary locale according to your language.

![name your skill](images/name_your_skill.png)

### 3.
Choose "Other" and "Custom" for the model.

![type of experience](images/type_of_experience.png)

![choose a model](images/choose_a_model.png)

### 4.
Choose "Alexa-hosted (Python)" for the backend resources.

![hosting services](images/hosting_services.png)

### 5.
Click on "Import Skill", paste the link of this repository and click on "Import":
```
https://github.com/[your-username]/alexa-genai.git
```
![template](images/import_git_skill.png)

### 6.
After import, the skill will be configured with:
- Invocation name: "genai"
- Support for multiple languages (15+ locales)
- Pre-configured intents and interaction model

### 7.
Add your OpenAI API key:
- Navigate to the "Code" section
- Open `lambda/lambda_function.py`
- Replace `YOUR_API_KEY` with your actual OpenAI API key

![openai_api_key](images/api_key.png)

### 8.
Save and deploy. Go to "Test" section and enable "Skill testing" in "Development".

![development_enabled](images/development_enabled.png)

### 9.
You are now ready to use your Alexa GenAI skill! Try saying:
- "Alexa, open genai"
- "Alexa, ask genai [your question]"

![test](images/test.png)

## Manual Setup (Alternative)

If you prefer to set up the skill manually:

### 1. Create the Skill
Follow steps 1-4 from the Quick Start guide, but select "Start from Scratch" instead of importing.

### 2. Configure Interaction Model
In the "Build" section, navigate to the "JSON Editor" tab and replace with the content from `json_editor.json`.

### 3. Update Lambda Function
- Go to "Code" section
- Replace `lambda_function.py` with the provided code
- Update `requirements.txt` with the dependencies

### 4. Build and Deploy
- Save the model and click on "Build Model"
- Deploy your code changes

## Features

- **Multi-language Support**: Works in 15+ languages including English, Spanish, French, German, Japanese, and more
- **Context Awareness**: Maintains conversation history for contextual responses
- **Customizable**: Easy to modify prompts and behavior
- **Efficient**: Uses GPT-4o-mini for fast, cost-effective responses

## Configuration

### Customizing the Model
You can change the AI model in `lambda/lambda_function.py`:
```python
data = {
    "model": "gpt-4o-mini",  # Change to "gpt-4", "gpt-3.5-turbo", etc.
    "messages": messages,
    "max_tokens": 300,
    "temperature": 0.5
}
```

### Adjusting Response Length
Modify the system prompt in `lambda/lambda_function.py`:
```python
messages = [{"role": "system", "content": "You are a helpful assistant. Answer in 50 words or less."}]
```

## Cost Considerations

Running this skill will incur costs for:
- **AWS Lambda**: Execution costs (minimal for personal use)
- **OpenAI API**: Based on token usage
- **Alexa Hosting**: Free tier available

Monitor your usage to avoid unexpected charges.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

## Acknowledgments

- Original concept inspired by alexa-gpt
- Built with the Alexa Skills Kit (ASK) SDK
- Powered by OpenAI's GPT models