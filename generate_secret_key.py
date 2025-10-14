"""
Generate a secure random secret key for Flask.

Usage:
    python generate_secret_key.py

This will output a secure random key that you can use in your .env file
for the SECRET_KEY variable.
"""

import secrets

if __name__ == "__main__":
    secret_key = secrets.token_hex(32)
    print("\n" + "=" * 70)
    print("Generated Secure Secret Key:")
    print("=" * 70)
    print(secret_key)
    print("=" * 70)
    print("\nAdd this to your .env file:")
    print(f"SECRET_KEY={secret_key}")
    print("\n" + "=" * 70)
