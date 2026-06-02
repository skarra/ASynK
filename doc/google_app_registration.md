# Google Cloud App Registration for ASynK

This guide walks you through registering a Google Cloud project and
creating OAuth credentials so that ASynK can access your Google
Contacts via the People API v1.

## Prerequisites

You need a **Google account** (any @gmail.com or Google Workspace
account will work).

## Step 1: Create a Google Cloud Project

1. Go to https://console.cloud.google.com/

2. In the top menu bar, click the project selector dropdown and then
   click **New Project**.

3. Fill in the form:
   - **Project name**: `ASynK` (or any name you prefer)
   - **Organization**: Leave as-is (or select your Workspace org if
     you have one)

4. Click **Create** and wait a few seconds for the project to be
   provisioned.

5. Make sure the new project is selected in the project selector
   dropdown before continuing.

## Step 2: Enable the People API

1. In the left navigation, go to **APIs & Services** → **Library**.

2. Search for **People API**.

3. Click **People API** in the results, then click **Enable**.

> **Note**: You do **not** need to enable the older "Contacts API".
> The People API replaces it and is the only API ASynK requires.

## Step 3: Configure the OAuth Consent Screen

1. In the left navigation, go to **APIs & Services** → **OAuth
   consent screen**.

2. Select **User Type**:
   - **External** — if you are using a personal Gmail account (this
     is the most common choice)
   - **Internal** — only available if you have a Google Workspace
     organization and want to restrict access to users in your org

3. Click **Create**.

4. Fill in the **App information**:
   - **App name**: `ASynK`
   - **User support email**: your email address
   - **Developer contact information**: your email address

5. Click **Save and Continue**.

6. On the **Scopes** page, click **Add or Remove Scopes** and add:
   - `https://www.googleapis.com/auth/contacts` — read and write
     contacts
   - `https://www.googleapis.com/auth/userinfo.email` — identify the
     signed-in user

7. Click **Update**, then **Save and Continue**.

8. On the **Test users** page, click **+ Add Users** and enter your
   own Google account email address.

9. Click **Save and Continue**, then **Back to Dashboard**.

> **Note**: While the app is in **Testing** status, only the test
> users you listed above can authorize. This is perfectly fine for
> personal use — there is no need to publish or verify the app.

## Step 4: Create OAuth Client ID

1. In the left navigation, go to **APIs & Services** → **Credentials**.

2. Click **+ Create Credentials** → **OAuth client ID**.

3. Fill in the form:
   - **Application type**: **Desktop app**
   - **Name**: `ASynK` (or any name you prefer)

4. Click **Create**.

5. In the confirmation dialog, click **Download JSON** to save the
   client secrets file.

6. Keep this file safe — you will point ASynK to it in the next step.

## Step 5: Configure ASynK

You need to tell ASynK where to find the client secrets JSON file you
downloaded in Step 4. Choose one of the options below.

### Option A: Use config.py (recommended)

Edit your `~/.asynk/config.py` and add:

```python
def customize_config(config):
    config['db_config']['gc']['client_secret_file'] = '/path/to/your/gc_client_secret.json'
```

Replace the path with the actual location of the downloaded JSON file.

### Option B: Place the file in ASynK's config directory

Copy the downloaded JSON file to `config/gc_client_secret.json` in
the ASynK source tree. This replaces the default placeholder file:

```bash
cp ~/Downloads/client_secret_*.json /path/to/ASynK/config/gc_client_secret.json
```

### Option C: Command-line flag

Pass the path on every run with the `--gcpwd` flag:

```bash
python asynk.py --gcpwd /path/to/your/gc_client_secret.json ...
```

## Step 6: First Authentication

When you first run ASynK with a Google Contacts profile:

1. A browser window opens automatically, showing the Google sign-in
   page.
2. Sign in with your Google account.
3. Review the permissions and click **Allow**.
4. The browser shows a confirmation message — you can close the tab.

After successful authentication, ASynK caches the OAuth tokens locally
(in `~/.asynk/` by default). Subsequent runs authenticate silently
using the cached refresh token.

## Troubleshooting

### "Access blocked: ASynK has not completed the Google verification process"

Your app is in Testing status and the account you are trying to sign
in with is not listed as a test user. Go to **APIs & Services** →
**OAuth consent screen** → **Test users** and add your email address.

### "Error 403: access_denied"

The signed-in user is not authorized. Ensure your Google account email
is listed as a test user in the OAuth consent screen configuration.

### "Quota exceeded" / "Rate Limit Exceeded"

The People API has daily quotas. If you share credentials with many
users, each user should register their own Google Cloud project to
avoid hitting the shared quota.

### "File not found: config/gc_client_secret.json"

The default client secrets file is missing or has not been replaced
with your own. Download your client secrets JSON from the Google Cloud
Console (see [Step 4](#step-4-create-oauth-client-id)) and configure
ASynK to use it (see [Step 5](#step-5-configure-asynk)).

### Stale tokens

Delete the cached token file and re-authenticate:

```bash
rm ~/.asynk/*.token.pickle
```

## Security Notes

- ASynK uses the **installed app (desktop) OAuth flow**, designed for
  CLI applications that run locally on a user's machine.
- No passwords are stored — only OAuth refresh tokens in pickle files
  under `~/.asynk/`.
- Token files should be kept private (`chmod 600`).
- You can revoke ASynK's access at any time by visiting
  https://myaccount.google.com/permissions and removing the app.
