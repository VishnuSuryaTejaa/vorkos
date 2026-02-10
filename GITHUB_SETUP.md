# GitHub Authentication Fix 🔑

GitHub no longer accepts account passwords for command-line access. You must use a **Personal Access Token (PAT)**.

**Follow these steps exactly:**

## 1. Generate a Token

1.  **Click this link**:  
    [Generate New Token (Classic)](https://github.com/settings/tokens/new?scopes=repo,read:user&description=Vorkos+Laptop)
    *(Log in if asked)*

2.  **Configure Token**:
    -   **Note**: "Vorkos Laptop" (or any name)
    -   **Expiration**: Select "No expiration" (easiest) or 90 days.
    -   **Scopes**: Ensure `repo` is checked.
    -   Click **Generate token** (green button at bottom).

3.  **Copy the Token**:
    -   It starts with `ghp_...`
    -   **COPY IT NOW**. You won't see it again.

## 2. Push Again

Run this command in your terminal:

```bash
git push -u origin main
```

-   **Username**: `VishnuSuryaTejaa`
-   **Password**: [PASTE THE TOKEN HERE]  
    *(Note: It won't show anything on screen as you paste. Just paste it and hit Enter.)*

---

If it works, Git will remember this token for future pushes.
