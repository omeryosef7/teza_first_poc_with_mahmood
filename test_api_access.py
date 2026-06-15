#!/usr/bin/env python3
"""
Quick test script to verify OpenAI and Gemini API access before running SLURM jobs.
"""

import sys
import os
import litellm

# Enable dropping unsupported parameters like the actual code does
litellm.drop_params = True

def check_env_vars():
    """Check for required API key environment variables"""
    print("\n" + "="*60)
    print("CHECKING ENVIRONMENT VARIABLES")
    print("="*60)
    
    openai_key = os.environ.get("OPENAI_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    
    print(f"OPENAI_API_KEY:  {'✓ Set' if openai_key else '✗ NOT SET'}")
    print(f"GEMINI_API_KEY:  {'✓ Set' if gemini_key else '✗ NOT SET'}")
    
    return openai_key is not None, gemini_key is not None


def test_openai():
    """Test OpenAI API access"""
    print("\n" + "="*60)
    print("Testing OpenAI (gpt-o4-mini)...")
    print("="*60)
    
    if not os.environ.get("OPENAI_API_KEY"):
        print("✗ SKIPPED - OPENAI_API_KEY not set")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        return False
    
    try:
        response = litellm.completion(
            model="o4-mini",  # Use LiteLLM model name
            messages=[
                {"role": "user", "content": "Say 'OpenAI API works!' in one sentence."}
            ],
            max_completion_tokens=100,
            # Note: o4-mini doesn't support temperature parameter, only temperature=1
            # litellm.drop_params=True will handle this automatically
        )
        
        answer = response.choices[0].message.content
        print(f"✓ OpenAI SUCCESS")
        print(f"Response: {answer}")
        return True
        
    except Exception as e:
        print(f"✗ OpenAI FAILED")
        print(f"Error: {type(e).__name__}")
        print(f"Details: {str(e)[:200]}")  # Truncate long error messages
        return False


def test_gemini():
    """Test Gemini API access"""
    print("\n" + "="*60)
    print("Testing Gemini (gemini-2.5-flash)...")
    print("="*60)

    if not os.environ.get("GEMINI_API_KEY"):
        print("✗ SKIPPED - GEMINI_API_KEY not set")
        print("   Set it with: export GEMINI_API_KEY='your-key-here'")
        return False

    try:
        response = litellm.completion(
            model="gemini/gemini-2.5-flash",
            messages=[
                {"role": "user", "content": "Say 'Gemini API works!' in one sentence."}
            ],
            max_completion_tokens=100,
            temperature=0.7,
            api_key=os.environ.get("GEMINI_API_KEY"),
        )
        
        answer = response.choices[0].message.content
        print(f"✓ Gemini SUCCESS")
        print(f"Response: {answer}")
        return True
        
    except Exception as e:
        print(f"✗ Gemini FAILED")
        print(f"Error: {type(e).__name__}")
        print(f"Details: {str(e)[:200]}")  # Truncate long error messages
        return False


def main():
    print("\n" + "="*60)
    print("API ACCESS TEST FOR SLURM JOBS")
    print("="*60)
    
    openai_env_ok, gemini_env_ok = check_env_vars()
    
    openai_ok = test_openai()
    gemini_ok = test_gemini()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"OpenAI:  {'✓ READY' if openai_ok else '✗ FAILED'}")
    print(f"Gemini:  {'✓ READY' if gemini_ok else '✗ FAILED'}")
    
    print("\nNOTE: To set API keys for your SLURM job, create a .env file in the project root:")
    print("  echo 'export OPENAI_API_KEY=\"your-key-here\"' >> .env")
    print("  echo 'export GEMINI_API_KEY=\"your-key-here\"' >> .env")
    
    if openai_ok and gemini_ok:
        print("\n✓✓✓ Both APIs are accessible - SAFE TO RUN SLURM JOBS ✓✓✓")
        return 0
    elif openai_ok or gemini_ok:
        print("\n⚠⚠⚠ Only one API is accessible - Some experiments may fail")
        return 1
    else:
        print("\n✗✗✗ Neither API is accessible - DO NOT RUN SLURM JOBS YET ✗✗✗")
        return 2


if __name__ == "__main__":
    sys.exit(main())
