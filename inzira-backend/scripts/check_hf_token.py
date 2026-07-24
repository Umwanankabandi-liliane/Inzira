import os
try:
    from huggingface_hub import HfApi
except Exception:
    print('huggingface_hub not installed')
    raise

token = os.getenv('HF_TOKEN', '').strip()
if not token:
    print('HF_TOKEN not set')
    raise SystemExit(2)
try:
    api = HfApi(token=token)
    who = api.whoami()
    print('HF token valid for:', who.get('name') or who.get('user') or who)
except Exception as e:
    print('HF token invalid or request failed:', type(e).__name__, e)
    raise
