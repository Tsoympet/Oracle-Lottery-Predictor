
def try_init_sentry(dsn: str | None):
    try:
        if not dsn: return False
        import sentry_sdk
        sentry_sdk.init(dsn=dsn, traces_sample_rate=0.0)
        return True
    except Exception:
        return False
