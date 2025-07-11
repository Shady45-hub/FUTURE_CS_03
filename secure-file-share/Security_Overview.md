 Security Overview – Secure File Sharing System

1. AES Encryption (Fernet)
- All uploaded files are encrypted using Fernet, which uses:
  - AES in CBC mode with PKCS7 padding
  - HMAC-SHA256 for integrity

2. Key Management
- The encryption key is generated and stored in "secret.key"
- This key is loaded at runtime from a local file
- In production, the key should be:
  - Stored in environment variables
  - Or managed using a secrets vault

3. Integrity Verification
- When a file is uploaded:
  - We compute its SHA256 hash and save it in "file_hashes.json"
- When downloading:
  - The decrypted content is hashed again and compared
  - If hashes don’t match → user is warned of tampering

4. Decrypted File Handling
- Files are only decrypted temporarily
- Decrypted copies are deleted immediately after download

5. Remaining Considerations
- No user authentication implemented can be added