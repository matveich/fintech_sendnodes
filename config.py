token = "347670542:AAGnmMx13Kki2J1f6w_L37cSsX9kGBfHGRU"  # TODO set token
WEBHOOK_HOST = "10.90.136.64"  # TODO set IP
WEBHOOK_PORT = 443
WEHOOK_LISTEN = "0.0.0.0"
WEBHOOK_SSL_CERT = "webhook_cert.pem"
WEBHOOK_SSL_PRIV = "webhook_pkey.pem"
WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % token
