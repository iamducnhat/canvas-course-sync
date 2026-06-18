#!/usr/bin/env python3
import argparse
import os
import sys
from pathlib import Path

from dsk.api import DeepSeekAPI, AuthenticationError, APIError

def main():
    parser = argparse.ArgumentParser(description="Ask DeepSeek using deepseek4free.")
    parser.add_argument("--token", help="DeepSeek auth token. Defaults to DEEPSEEK_AUTH_TOKEN env var.")
    parser.add_argument("--token-file", help="Path to a file containing the DeepSeek auth token.")
    parser.add_argument("--prompt", required=True, help="The prompt to send to DeepSeek.")
    parser.add_argument("--context", action="append", default=[], help="Path to a file (e.g. assignment JSON) to include in the context. Can be used multiple times.")
    parser.add_argument("--chat-id", help="Optional Chat ID to continue an existing conversation.")
    args = parser.parse_args()

    token = args.token or os.environ.get("DEEPSEEK_AUTH_TOKEN")
    if not token and args.token_file:
        try:
            token = Path(args.token_file).expanduser().read_text(encoding="utf-8").strip()
        except Exception as e:
            print(f"Error reading token file: {e}")
            sys.exit(1)
            
    if not token:
        print("Error: DeepSeek auth token is required. Pass --token, --token-file, or set DEEPSEEK_AUTH_TOKEN.")
        sys.exit(1)

    # Build the full prompt
    full_prompt = ""
    if args.context:
        full_prompt += "Here is the context for the task:\n\n"
        for ctx_path in args.context:
            path = Path(ctx_path).expanduser().resolve()
            if path.exists():
                full_prompt += f"--- {path.name} ---\n"
                try:
                    full_prompt += path.read_text(encoding="utf-8") + "\n\n"
                except Exception as e:
                    print(f"Warning: Could not read {path}: {e}", file=sys.stderr)
            else:
                print(f"Warning: Context file {path} does not exist.", file=sys.stderr)
        full_prompt += "--- End of Context ---\n\n"
    
    full_prompt += f"User instruction: {args.prompt}"

    try:
        api = DeepSeekAPI(token)
        chat_id = args.chat_id
        if not chat_id:
            chat_id = api.create_chat_session()
            print(f"Created new DeepSeek chat session: {chat_id}")
        else:
            print(f"Continuing DeepSeek chat session: {chat_id}")

        print("\nDeepSeek Response:\n" + "-"*40)
        for chunk in api.chat_completion(chat_id, full_prompt):
            if chunk['type'] == 'text':
                print(chunk['content'], end='', flush=True)
        print("\n" + "-"*40)
    except AuthenticationError:
        print("\nAuthentication failed. Please check your DEEPSEEK_AUTH_TOKEN.")
        sys.exit(1)
    except APIError as e:
        print(f"\nAPI error occurred: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
