# Azure AD App Registration for ASynK

This guide walks you through registering an application in Azure Active
Directory (now called Microsoft Entra ID) so that ASynK can access your
Exchange Online contacts via the Microsoft Graph API.

## Prerequisites

- A Microsoft 365 account (work/school) or a personal Microsoft account
  (outlook.com, hotmail.com, live.com)
- Access to the [Azure Portal](https://portal.azure.com)

## Step 1: Register an Application

1. Sign in to the [Azure Portal](https://portal.azure.com).

2. Navigate to **Azure Active Directory** → **App registrations**
   (or search for "App registrations" in the search bar).

3. Click **New registration**.

4. Fill in the form:
   - **Name**: `ASynK` (or any name you prefer)
   - **Supported account types**: Choose based on your needs:
     - *Accounts in any organizational directory and personal Microsoft
       accounts* — if you want to sync both work and personal accounts
     - *Accounts in any organizational directory only* — work/school only
   - **Redirect URI**: Leave blank (not needed for device code flow)

5. Click **Register**.

6. On the app overview page, note the **Application (client) ID** — this
   is what you'll put in your ASynK config.

## Step 2: Configure API Permissions

1. In your app registration, go to **API permissions**.

2. Click **Add a permission** → **Microsoft Graph** →
   **Delegated permissions**.

3. Search for and add these permissions:
   - `Contacts.ReadWrite` — Read and write user contacts
   - `User.Read` — Read user profile (for authentication)

4. Click **Add permissions**.

5. If you see a "Grant admin consent" button and you are an admin, click
   it.  For personal accounts this step is not required.

## Step 3: Enable Device Code Flow

1. In your app registration, go to **Authentication**.

2. Under **Advanced settings**, set **Allow public client flows** to
   **Yes**.

3. Click **Save**.

## Step 4: Configure ASynK

### Option A: Edit config.json directly

Open `config/config_v9.json` and set your client ID:

```javascript
'ex' : {
    'client_id'  : 'YOUR-CLIENT-ID-HERE',
    'tenant_id'  : 'common',
    // ... rest of config
},
```

### Option B: Use config.py (recommended)

Edit your `~/.asynk/config.py` (or `config/config.init.py` for a fresh
install) and add:

```python
def customize_config(config):
    config['db_config']['ex']['client_id'] = 'YOUR-CLIENT-ID-HERE'

    ## Optional: restrict to a specific tenant
    # config['db_config']['ex']['tenant_id'] = 'YOUR-TENANT-ID'
```

### Option C: Pass via command line

Not yet supported — use one of the config file options above.

## Step 5: First Authentication

When you first run ASynK with an Exchange profile, you will see a message
like:

```
To sign in, use a web browser to open the page https://microsoft.com/devicelogin
and enter the code XXXXXXXX to authenticate.
```

1. Open the URL in any browser.
2. Enter the code shown in the terminal.
3. Sign in with your Microsoft account.
4. Grant the requested permissions.

After successful authentication, ASynK caches the OAuth tokens locally
(in `~/.asynk/` by default). Subsequent runs will authenticate silently
using the cached refresh token.

## Troubleshooting

### "AADSTS700016: Application not found"

Your `client_id` in the config file doesn't match any registered app.
Double-check you copied the correct **Application (client) ID** from
the Azure Portal.

### "AADSTS65001: User has not consented"

The user needs to consent to the permissions. This happens automatically
during the device code flow.  If it doesn't, ask your Azure AD admin to
grant admin consent for the app.

### "Insufficient privileges"

Ensure the app has the `Contacts.ReadWrite` and `User.Read` delegated
permissions.  If your organization requires admin consent, an admin must
grant it.

### Token cache issues

If authentication problems persist, delete the MSAL token cache:

```bash
rm ~/.asynk/msal_token_cache.bin
```

Then re-run ASynK to re-authenticate.

## Security Notes

- ASynK uses the **device code flow**, which is designed for CLI
  applications that cannot host a web server for redirect-based auth.
- No passwords are stored — only OAuth refresh tokens in the local
  cache file.
- The token cache file (`msal_token_cache.bin`) should be kept private
  (`chmod 600`).
- Refresh tokens can be revoked from the Azure Portal under **Enterprise
  applications** → your app → **Users and groups**.
