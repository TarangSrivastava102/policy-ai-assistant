GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
SMTP_EMAIL = "tarang@thegermanemedia.com"
SMTP_PASSWORD = "YOUR_SMTP_APP_PASSWORD"

[google_service_account]
type = "service_account"
project_id = "germane-media-reimbursement"
private_key_id = "YOUR_PRIVATE_KEY_ID"
private_key = """-----BEGIN PRIVATE KEY-----
YOUR_PRIVATE_KEY
-----END PRIVATE KEY-----"""
client_email = "germane-reimbursement@germane-media-reimbursement.iam.gserviceaccount.com"
client_id = "101272888470510559842"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/germane-reimbursement%40germane-media-reimbursement.iam.gserviceaccount.com"
universe_domain = "googleapis.com"

[auth]
redirect_uri = "https://policy-ai-assistant-c3btlgrxcyalw2k4qccshc.streamlit.app/oauth2callback"
cookie_secret = "YOUR_COOKIE_SECRET"
client_id = "YOUR_OAUTH_CLIENT_ID"
client_secret = "YOUR_OAUTH_CLIENT_SECRET"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
