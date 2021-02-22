# Common API Regex patterns taken from: https://github.com/zricethezav/gitleaks/blob/master/config/default.go
""" # TODO Convert these go regex to python regex
AWS_MANAGER_ID_REGEX = '''(A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}'''
AWS_SECRET_KEY_REGEX = '''(?i)aws(.{0,20})?(?-i)['\"][0-9a-zA-Z\/+]{40}['\"]'''
AWS_MWS_KEY_REGEX = '''amzn\.mws\.[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'''
FACEBOOK_SECRET_KEY_REGEX = '''(?i)(facebook|fb)(.{0,20})?(?-i)['\"][0-9a-f]{32}['\"]'''
FACEBOOK_CLIENT_ID_REGEX = '''(?i)(facebook|fb)(.{0,20})?['\"][0-9]{13,17}['\"]'''
TWITTER_SECRET_KEY_REGEX = '''(?i)twitter(.{0,20})?[0-9a-z]{35,44}'''
TWITTER_CLIENT_ID_REGEX = '''(?i)twitter(.{0,20})?[0-9a-z]{18,25}'''
GITHUB_REGEX = '''(?i)github(.{0,20})?(?-i)[0-9a-zA-Z]{35,40}'''
LINKEDIN_CLIENT_ID = '''(?i)linkedin(.{0,20})?(?-i)[0-9a-z]{12}'''
LINKEDIN_SECRET_KEY = '''(?i)linkedin(.{0,20})?[0-9a-z]{16}'''
SLACK_REGEX = '''xox[baprs]-([0-9a-zA-Z]{10,48})?'''
ASYMETRIC_PRIVATE_KEY_REGEX = '''-----BEGIN ((EC|PGP|DSA|RSA|OPENSSH) )?PRIVATE KEY( BLOCK)?-----'''
GOOGLE_API_KEY_REGEX = '''AIza[0-9A-Za-z\\-_]{35}'''
GOOGLE_GCP_SERVICE_ACCOUNT = '''"type": "service_account"'''
HEROKU_API_KEY = '''(?i)heroku(.{0,20})?[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'''
MAILCHIMP_API_KEY = '''(?i)(mailchimp|mc)(.{0,20})?[0-9a-f]{32}-us[0-9]{1,2}'''
MAILGUN_API_KEY = '''((?i)(mailgun|mg)(.{0,20})?)?key-[0-9a-z]{32}'''
PAYPAL_BRAINTREE_ACCESS_TOKEN = '''access_token\$production\$[0-9a-z]{16}\$[0-9a-f]{32}'''
PICATIC_API_KEY = '''sk_live_[0-9a-z]{32}'''
SENDGRID_API_KEY = '''SG\.[\w_]{16,32}\.[\w_]{16,64}'''
SLACK_WEBHOOK = '''https://hooks.slack.com/services/T[a-zA-Z0-9_]{8}/B[a-zA-Z0-9_]{8}/[a-zA-Z0-9_]{24}'''
STRIPE_API_KEY = '''(?i)stripe(.{0,20})?[sr]k_live_[0-9a-zA-Z]{24}'''
SQAURE_ACCESS_TOKEN = '''sq0atp-[0-9A-Za-z\-_]{22}'''
SQUARE_OAUTH_SECRET = '''sq0csp-[0-9A-Za-z\\-_]{43}'''
TWILIO_API_KEY = '''(?i)twilio(.{0,20})?SK[0-9a-f]{32}'''
"""


# Common API Regex patterns taken from: https://github.com/m4ll0k/SecretFinder
SECRET_REGEX_PATTERNS = {
    'google_api': r'AIza[0-9A-Za-z-_]{35}',
    'firebase': r'AAAA[A-Za-z0-9_-]{7}:[A-Za-z0-9_-]{140}',
    'google_captcha': r'6L[0-9A-Za-z-_]{38}|^6[0-9a-zA-Z_-]{39}$',
    'google_oauth': r'ya29\.[0-9A-Za-z\-_]+',
    'amazon_aws_access_key_id': r'AKIA[0-9A-Z]{16}',
    'amazon_mws_auth_toke': r'amzn\\.mws\\.[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
    'amazon_aws_url': r's3\.amazonaws.com[/]+|[a-zA-Z0-9_-]*\.s3\.amazonaws.com',
    'amazon_aws_url2': r"(" 
                       r"[a-zA-Z0-9-\.\_]+\.s3\.amazonaws\.com"
                       r"|s3://[a-zA-Z0-9-\.\_]+"
                       r"|s3-[a-zA-Z0-9-\.\_\/]+"
                       r"|s3.amazonaws.com/[a-zA-Z0-9-\.\_]+"
                       r"|s3.console.aws.amazon.com/s3/buckets/[a-zA-Z0-9-\.\_]+)",
    'facebook_access_token': r'EAACEdEose0cBA[0-9A-Za-z]+',
    'authorization_basic': r'basic [a-zA-Z0-9=:_\+\/-]{5,100}',
    'authorization_bearer': r'bearer [a-zA-Z0-9_\-\.=:_\+\/]{5,100}',
    'authorization_api': r'api[key|_key|\s+]+[a-zA-Z0-9_\-]{5,100}',
    'mailgun_api_key': r'key-[0-9a-zA-Z]{32}',
    'twilio_api_key': r'SK[0-9a-fA-F]{32}',
    'twilio_account_sid': r'AC[a-zA-Z0-9_\-]{32}',
    'twilio_app_sid': r'AP[a-zA-Z0-9_\-]{32}',
    'paypal_braintree_access_token': r'access_token\$production\$[0-9a-z]{16}\$[0-9a-f]{32}',
    'square_oauth_secret': r'sq0csp-[ 0-9A-Za-z\-_]{43}|sq0[a-z]{3}-[0-9A-Za-z\-_]{22,43}',
    'square_access_token': r'sqOatp-[0-9A-Za-z\-_]{22}|EAAA[a-zA-Z0-9]{60}',
    'stripe_standard_api': r'sk_live_[0-9a-zA-Z]{24}',
    'stripe_restricted_api': r'rk_live_[0-9a-zA-Z]{24}',
    'github_access_token': r'[a-zA-Z0-9_-]*:[a-zA-Z0-9_\-]+@github\.com*',
    'rsa_private_key': r'-----BEGIN RSA PRIVATE KEY-----',
    'ssh_dsa_private_key': r'-----BEGIN DSA PRIVATE KEY-----',
    'ssh_dc_private_key': r'-----BEGIN EC PRIVATE KEY-----',
    'pgp_private_block': r'-----BEGIN PGP PRIVATE KEY BLOCK-----',
    'json_web_token': r'ey[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*$',
    'slack_token': r"\"api_token\":\"(xox[a-zA-Z]-[a-zA-Z0-9-]+)\"",
    'SSH_privKey': r"([-]+BEGIN [^\s]+ PRIVATE KEY[-]+[\s]*[^-]*[-]+END [^\s]+ PRIVATE KEY[-]+)",
    'possible_Creds': r"(?i)("
                      r"password\s*[`=:\"]+\s*[^\s]+|"
                      r"password is\s*[`=:\"]*\s*[^\s]+|"
                      r"pwd\s*[`=:\"]*\s*[^\s]+|" 
                      r"passwd\s*[`=:\"]+\s*[^\s]+)",
}
