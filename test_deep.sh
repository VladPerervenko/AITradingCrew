curl -X POST https://openrouter.ai/api/v1/chat/completions \
-H "Authorization: Bearer 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" \
-H "Content-Type: application/json" \
-d '{
    "model": "deepseek/deepseek-r1:free",
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ],
    "max_tokens": 100,}'
