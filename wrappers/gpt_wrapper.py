#!/usr/bin/env python3
"""
GPT CLI Wrapper for MAOS Multi-Model Integration

Wrapper script to integrate GPT/OpenAI models into the MAOS system.
Provides standardized interface for GPT model interaction.
"""

import sys
import json
import argparse
import subprocess
import tempfile
import os
from pathlib import Path

# ASCII-only enforcement
def sanitize_ascii(text):
    """Ensure text contains only ASCII characters."""
    return ''.join(char if ord(char) < 128 else '?' for char in text)

def call_gpt_api(prompt, model="gpt-4"):
    """
    Call GPT via OpenAI CLI or API client.
    
    Args:
        prompt: The prompt to send
        model: GPT model to use
        
    Returns:
        Response text
    """
    try:
        # Option 1: Use openai CLI if available
        # Example: openai api completions.create -m gpt-4 -p "prompt"
        
        # Create temporary file for prompt
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(sanitize_ascii(prompt))
            prompt_file = f.name
        
        try:
            # Try openai CLI first
            result = subprocess.run([
                "openai", "api", "chat.completions.create",
                "-m", model,
                "--messages", f'[{{"role": "user", "content": "{sanitize_ascii(prompt)}"}}]'
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                # Parse OpenAI API response
                response_data = json.loads(result.stdout)
                return response_data['choices'][0]['message']['content']
            else:
                raise subprocess.CalledProcessError(result.returncode, "openai")
                
        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
            # Fallback: Use curl with OpenAI API
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                return "ERROR: No OpenAI API key found. Set OPENAI_API_KEY environment variable."
            
            # Prepare API request
            request_data = {
                "model": model,
                "messages": [{"role": "user", "content": sanitize_ascii(prompt)}],
                "max_tokens": 4000,
                "temperature": 0.7
            }
            
            # Write request to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(request_data, f)
                request_file = f.name
            
            try:
                # Call OpenAI API via curl
                result = subprocess.run([
                    "curl", "-s", "-X", "POST",
                    "https://api.openai.com/v1/chat/completions",
                    "-H", f"Authorization: Bearer {api_key}",
                    "-H", "Content-Type: application/json",
                    "-d", f"@{request_file}"
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    response_data = json.loads(result.stdout)
                    if 'choices' in response_data and len(response_data['choices']) > 0:
                        return response_data['choices'][0]['message']['content']
                    elif 'error' in response_data:
                        return f"ERROR: OpenAI API error: {response_data['error']['message']}"
                    else:
                        return "ERROR: Unexpected OpenAI API response format"
                else:
                    return f"ERROR: curl failed with code {result.returncode}: {result.stderr}"
                    
            finally:
                os.unlink(request_file)
                
        finally:
            os.unlink(prompt_file)
            
    except Exception as e:
        return f"ERROR: GPT wrapper exception: {str(e)}"

def main():
    """Main entry point for GPT wrapper."""
    parser = argparse.ArgumentParser(description='GPT CLI Wrapper for MAOS')
    parser.add_argument('--model', default='gpt-4', help='GPT model to use')
    parser.add_argument('--json', action='store_true', help='Expect JSON response')
    parser.add_argument('prompt', help='Prompt to send to GPT')
    
    args = parser.parse_args()
    
    try:
        # Call GPT with the prompt
        response = call_gpt_api(args.prompt, args.model)
        
        # Sanitize response for ASCII compliance
        response = sanitize_ascii(response)
        
        # Print response with markers if needed
        if args.json:
            print("BEGIN_JSON")
            print(response)
            print("END_JSON")
        else:
            print(response)
            
    except Exception as e:
        print(f"ERROR: GPT wrapper failed: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()