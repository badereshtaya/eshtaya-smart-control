# Security

## Credentials

Do not commit Tuya Client IDs, Client Secrets, UIDs, Home Assistant tokens or other project credentials to this repository.

Tuya credentials are stored in the Home Assistant config entry. The backend keeps access tokens in memory and the admin WebSocket status API never returns the saved Client Secret.

## Reporting a vulnerability

Open a private security advisory on the GitHub repository when available. Do not publish secrets or working exploit details in a public issue.

## Administration boundary

The Eshtaya Smart Control sidebar panel and all write-capable WebSocket commands are administrator-only. Home Assistant authentication remains the security boundary; the integration does not implement a secondary URL token or password.
