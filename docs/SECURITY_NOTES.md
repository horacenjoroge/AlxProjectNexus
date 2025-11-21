# Security Notes for Public Repository

## ⚠️ NEVER Commit These Files

The following files contain sensitive information and **MUST NEVER** be committed to a public repository:

### SSL Certificates and Keys
- `docker/ssl/*.pem`
- `docker/ssl/*.key`
- `docker/ssl/*.crt`
- Any files in `docker/ssl/` directory

### Environment Variables
- `.env`
- `.env.local`
- `.env.production`
- Any file containing actual secrets

### Private Keys
- `*.pem` (private keys)
- `*.key` (private keys)
- `*.p12` (PKCS#12 certificates)
- `*.pfx` (PKCS#12 certificates)

### Database Backups
- `*.sql` (may contain sensitive data)
- `backup_*.sql.gz`
- Any database dump files

### Credentials
- API keys
- Passwords
- Secret keys
- OAuth tokens
- Service account keys

## ✅ Safe to Commit

These files are safe to commit as they only contain examples or templates:

- `docs/SSL_SETUP_QUICKSTART.md` - Contains only example configurations
- `docs/deployment-guide.md` - Contains only example commands
- `docker/nginx-ssl.conf` - Example configuration (no real certificates)
- `.env.example` - Template file (if it exists, with placeholder values)

## 🔒 Best Practices

1. **Always use placeholders** in documentation:
   - `yourdomain.com` instead of real domains
   - `your-secret-key` instead of real keys
   - `your-password` instead of real passwords

2. **Verify before committing:**
   ```bash
   # Check for sensitive files
   git status
   git diff
   
   # Search for potential secrets
   git diff --cached | grep -i "password\|secret\|key\|token"
   ```

3. **Use .gitignore:**
   - All sensitive files are already in `.gitignore`
   - Never force-add ignored files: `git add -f` (dangerous!)

4. **If you accidentally commit secrets:**
   - **Immediately rotate/revoke** the exposed secrets
   - Remove from git history (requires force push)
   - Consider the repository compromised if it's public

## 📋 Pre-Commit Checklist

Before committing, verify:

- [ ] No `.env` files in commit
- [ ] No SSL certificates (`.pem`, `.key`) in commit
- [ ] No real passwords or secrets in code
- [ ] No database backups in commit
- [ ] Documentation uses placeholders only
- [ ] All sensitive paths are in `.gitignore`

## 🛡️ Additional Security

- Use environment variables for all secrets
- Use secret management services (AWS Secrets Manager, HashiCorp Vault)
- Rotate secrets regularly
- Use different secrets for development and production
- Never share secrets in chat, email, or documentation

---

**Remember:** Once committed to a public repository, secrets are exposed forever. Always err on the side of caution!

