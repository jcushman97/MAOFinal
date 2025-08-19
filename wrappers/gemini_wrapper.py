#!/usr/bin/env python3
"""
Gemini CLI Wrapper for MAOS Multi-Model Integration

Wrapper script to integrate Google Gemini models into the MAOS system.
Provides standardized interface for Gemini model interaction.
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

def call_gemini_api(prompt, model="gemini-1.5-pro"):
    """
    Call Gemini via Google AI CLI or API client.
    
    Args:
        prompt: The prompt to send
        model: Gemini model to use
        
    Returns:
        Response text
    """
    try:
        # Option 1: Use Google AI CLI if available
        # Example: gemini generate "prompt" --model gemini-1.5-pro
        
        try:
            # Try gemini CLI first
            result = subprocess.run([
                "gemini", "generate",
                sanitize_ascii(prompt),
                "--model", model
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                raise subprocess.CalledProcessError(result.returncode, "gemini")
                
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback: Use curl with Gemini API
            api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_AI_API_KEY')
            if not api_key:
                return "ERROR: No Gemini API key found. Set GEMINI_API_KEY or GOOGLE_AI_API_KEY environment variable."
            
            # Prepare API request for Gemini
            request_data = {
                "contents": [{
                    "parts": [{"text": sanitize_ascii(prompt)}]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 4000
                }
            }
            
            # Write request to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(request_data, f)
                request_file = f.name
            
            try:
                # Call Gemini API via curl
                api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                
                result = subprocess.run([
                    "curl", "-s", "-X", "POST",
                    api_url,
                    "-H", "Content-Type: application/json",
                    "-d", f"@{request_file}"
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    response_data = json.loads(result.stdout)
                    if 'candidates' in response_data and len(response_data['candidates']) > 0:
                        candidate = response_data['candidates'][0]
                        if 'content' in candidate and 'parts' in candidate['content']:
                            return candidate['content']['parts'][0]['text']
                        else:
                            return "ERROR: Unexpected Gemini response structure"
                    elif 'error' in response_data:
                        return f"ERROR: Gemini API error: {response_data['error']['message']}"
                    else:
                        return "ERROR: No candidates in Gemini response"
                else:
                    return f"ERROR: curl failed with code {result.returncode}: {result.stderr}"
                    
            finally:
                os.unlink(request_file)
                
    except Exception as e:
        return f"ERROR: Gemini wrapper exception: {str(e)}"

def main():
    """Main entry point for Gemini wrapper."""
    parser = argparse.ArgumentParser(description='Gemini CLI Wrapper for MAOS')
    parser.add_argument('--model', default='gemini-1.5-pro', help='Gemini model to use')
    parser.add_argument('--json', action='store_true', help='Expect JSON response')
    parser.add_argument('prompt', help='Prompt to send to Gemini')
    
    args = parser.parse_args()
    
    try:
        # Call Gemini with the prompt
        response = call_gemini_api(args.prompt, args.model)
        
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
        print(f"ERROR: Gemini wrapper failed: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()