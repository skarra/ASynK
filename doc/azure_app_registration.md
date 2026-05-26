# Microsoft Entra ID App Registration for ASynK

This guide walks you through registering an application in Microsoft
Entra ID (formerly Azure Active Directory) so that ASynK can access your
Exchange Online contacts via the Microsoft Graph API.

## Prerequisites

You need a **Microsoft Entra ID tenant** (directory). App registrations
can no longer be created outside of a directory — Microsoft deprecated
that capability in June 2024.

**If you already have a tenant** (e.g. through a Microsoft 365
work/school account), skip to [Step 2](#step-2-register-the-application).

**If you don't have a tenant** (e.g. you only have a personal
@gmail.com, @hotmail.com, or @outlook.com account), you must first
create one. See Step 1 below.

## Step 1: Get a Microsoft Entra ID Tenant

Choose the option that best fits your situation:

### Option A: Sign up for a free Azure account (recommended)

1. Go to https://azure.microsoft.com/en-us/free/
2. Click **Start free** and sign in with your Microsoft account (you
   can use any email, including Gmail).
3. Complete the signup (requires a phone number and credit card for
   identity verification — you will not be charged).
4. Once your Azure account is active, an Entra ID tenant is
   automatically created for you.

### Option B: Create an Entra ID tenant directly

1. Go to https://entra.microsoft.com/
2. Sign in with a Microsoft account that is already part of a
   tenant (e.g. a work or school account).
3. Navigate to **Identity** → **Overview** → **Manage tenants** →
   **+ Create**.
4. Follow the prompts to create a new tenant.

### Option C: Microsoft 365 Developer Program

If you have a Visual Studio Professional/Enterprise subscription or
are part of an eligible Microsoft partner program:

1. Go to https://developer.microsoft.com/en-us/microsoft-365/dev-program
2. Click **Join now** and follow the prompts.
3. If you qualify, you'll get a free E5 sandbox tenant.

> **Note**: The M365 Developer Program sandbox is restricted to
> qualifying subscriptions. Most individual developers will find
> Option A (free Azure account) simpler.

## Step 2: Register the Application

1. Sign in to the **Microsoft Entra admin center** at
   https://entra.microsoft.com/

2. If you have multiple directories, use the **Directories +
   subscriptions** filter (gear icon in the top menu bar) to switch
   to the correct tenant.

3. In the left navigation, expand **Applications** → click
   **App registrations**.

4. Click **+ New registration**.

5. Fill in the form:
   - **Name**: `ASynK` (or any name you prefer)
   - **Supported account types**: Choose based on your needs:
     - *Accounts in this organizational directory only* — if only you
       (or users in your tenant) will use ASynK
     - *Accounts in any organizational directory and personal Microsoft
       accounts* — if you also want to support personal @outlook.com /
       @hotmail.com accounts
   - **Redirect URI**: Leave blank (not needed for device code flow)

6. Click **Register**.

7. On the app overview page, copy the **Application (client) ID** —
   you'll need this for ASynK's config.

## Step 3: Configure API Permissions

1. In your app registration, click **API permissions** in the left
   menu.

2. Click **+ Add a permission** → **Microsoft Graph** →
   **Delegated permissions**.

3. Search for and check these permissions:
   - `Contacts.ReadWrite` — read and write user contacts
   - `User.Read` — sign in and read user profile

4. Click **Add permissions**.

5. *Optional*: If you are a tenant admin, click **Grant admin consent
   for [your tenant]** to pre-approve the permissions for all users.
   For single-user / personal tenants, user consent during login is
   sufficient.

## Step 4: Enable Public Client (Device Code) Flow

1. In your app registration, click **Authentication** in the left menu.

2. Scroll down to **Advanced settings**.

3. Set **Allow public client flows** to **Yes**.

4. Click **Save**.

## Step 5: Configure ASynK

### Option A: Use config.py (recommended)

Edit your `~/.asynk/config.py` and add:

```python
def customize_config(config):
    config['db_config']['ex']['client_id'] = 'YOUR-CLIENT-ID-HERE'

    ## Optional: restrict to your specific tenant
    # config['db_config']['ex']['tenant_id'] = 'YOUR-TENANT-ID'
```

### Option B: Edit config.json directly

Open `config/config_v9.json` and set your client ID in the `ex` section:

```javascript
'client_id'  : 'YOUR-CLIENT-ID-HERE',
'tenant_id'  : 'common',
```

## Step 6: First Authentication

When you first run ASynK with an Exchange profile, you will see a
message like:

```
To sign in, use a web browser to open the page
https://microsoft.com/devicelogin and enter the code XXXXXXXX to
authenticate.
```

1. Open the URL in any browser.
2. Enter the code shown in the terminal.
3. Sign in with your Microsoft account.
4. Grant the requested permissions when prompted.

After successful authentication, ASynK caches the OAuth tokens locally
(in `~/.asynk/` by default). Subsequent runs authenticate silently
using the cached refresh token.

## Troubleshooting

### "The ability to create applications outside of a directory has been deprecated"

You are trying to register an app without being inside an Entra ID
tenant. See [Step 1](#step-1-get-a-microsoft-entra-id-tenant) to
create or access a tenant first.

### "AADSTS700016: Application not found"

The `client_id` in your config doesn't match any registered app.
Double-check you copied the correct **Application (client) ID** from
the Entra admin center.

### "AADSTS65001: User has not consented"

The user needs to consent to the permissions. This normally happens
automatically during device code flow. If it doesn't, a tenant admin
must click "Grant admin consent" on the API permissions page.

### "Insufficient privileges"

Ensure the app has `Contacts.ReadWrite` and `User.Read` delegated
permissions. If your organization requires admin consent, an admin
must grant it.

### Authentication loop or stale tokens

Delete the MSAL token cache and re-authenticate:

```bash
rm ~/.asynk/msal_token_cache.bin
```

### Using an incognito/private browser window

If you have multiple Microsoft accounts (personal + work), use an
incognito window when visiting the device login page to avoid
accidentally authenticating with the wrong account.

## Security Notes

- ASynK uses the **device code flow**, designed for CLI applications
  that cannot host a web server for redirect-based auth.
- No passwords are stored — only OAuth refresh tokens in the local
  token cache file.
- The token cache file (`msal_token_cache.bin`) should be kept private
  (`chmod 600`).
- Refresh tokens can be revoked from the Entra admin center under
  **Enterprise applications** → your app → **Users and groups**.
