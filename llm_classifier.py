import json
import logging
from typing import Dict, Any, List
import anthropic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMClassifier:
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def build_prompt(self, site_text: str, examples: List[Dict[str, Any]] = None) -> str:
        prompt = "You are an expert archaeological classifier. Analyze the following site description and extract the classifications based on the text.\n\n"

        if examples:
            prompt += "Here are some examples of correctly classified sites:\n"
            for ex in examples:
                prompt += f"- Description: {ex['text']}\n"
                prompt += f"  Classification: {json.dumps(ex['classification'])}\n\n"

        prompt += f"Now classify the following site description:\nDescription: {site_text}\n\n"
        prompt += "Return ONLY a JSON object with the following schema, and no other text:\n"
        prompt += """
{
  "Class_1_Found": bool,
  "Class_1_Keywords": "string (semicolon separated)",
  "Class_2_Found": bool,
  "Class_2_Keywords": "string (semicolon separated)",
  "Class_3_Found": bool,
  "Class_3_Keywords": "string (semicolon separated)",
  "Burned_Clay_Found": bool,
  "Burned_Clay_Only": bool,
  "Is_Prehistoric": bool,
  "Learned_Time_Period": "string",
  "Prehistoric_Evidence": "string (semicolon separated)"
}
"""
        return prompt

    def classify(self, site_text: str, examples: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        prompt = self.build_prompt(site_text, examples)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                system="You are an expert archaeological AI. Return only valid JSON.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Parse the JSON response
            result_text = response.content[0].text
            # Sometimes models wrap JSON in markdown blocks
            if result_text.startswith("```json"):
                result_text = result_text[7:-3]
            elif result_text.startswith("```"):
                result_text = result_text[3:-3]

            return json.loads(result_text.strip())

        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            return None
