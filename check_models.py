#!/usr/bin/env python3
"""Check available Gemini models"""

import google.generativeai as genai
from config.settings import settings

genai.configure(api_key=settings.gemini_api_key)

print("Available models:")
print("=" * 70)

for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"- {model.name}")
        print(f"  Display name: {model.display_name}")
        print(f"  Description: {model.description[:100]}...")
        print()
