# How to Add TERTIARY API Key to Render

## Problem
Your Groq dashboard shows JobHunter3 has **0 API calls**, meaning the TERTIARY key isn't being used. This is because it's likely not configured in Render's environment variables.

## Solution: Add the Missing Environment Variable

### Step 1: Get Your JobHunter3 API Key
1. Go to https://console.groq.com/keys
2. Find **JobHunter3** (the one showing 0 API Calls)
3. Click the eye icon to reveal the full key
4. Copy the key (starts with `gsk_...`)

### Step 2: Add to Render
1. Go to https://dashboard.render.com
2. Select your **Vorkos backend service**
3. Click **Environment** tab in the left sidebar
4. Click **Add Environment Variable** button
5. Add the new variable:
   ```
   Key:   GROQ_API_KEY_TERTIARY
   Value: gsk_paste_your_jobhunter3_key_here
   ```
6. Click **Save Changes**

### Step 3: Verify All 3 Keys Are Set
You should now have these environment variables in Render:
```
✅ GROQ_API_KEY          = gsk_...  (JobHunter1 or 3)
✅ GROQ_API_KEY_BACKUP   = gsk_...  (JobHunter2)
✅ GROQ_API_KEY_TERTIARY = gsk_...  (JobHunter3) ← Just added!
✅ TAVILY_API_KEY        = tvly_...
```

### Step 4: Redeploy
Render should automatically redeploy after adding the environment variable. If not:
1. Click **Manual Deploy** button
2. Select **Deploy latest commit**

### Step 5: Test
After deployment completes:
1. Try searching for jobs again
2. Check your Groq dashboard
3. JobHunter3 should now show API calls > 0

## Expected Behavior After Fix

When JobHunter1 and JobHunter2 hit rate limits, the system will now try JobHunter3:

```
🔑 Trying PRIMARY key (1/3)...
⚠️ PRIMARY key hit RATE LIMIT!
🔄 Failover: Trying BACKUP key next...

🔑 Trying BACKUP key (2/3)...
⚠️ BACKUP key hit RATE LIMIT!
🔄 Failover: Trying TERTIARY key next...

🔑 Trying TERTIARY key (3/3)...
✅ TERTIARY key succeeded! ← JobHunter3 will be used here
```

## Quick Check
After adding the variable, you can verify by checking the Groq dashboard:
- JobHunter3 calls should increase from 0 to 1+ after your next job search
