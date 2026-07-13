"""
Secret Manager -> .env fallback zinciri.

Once Google Secret Manager'dan (proje: yeno-502112) okumayi dener. Erisim
yoksa (izin yok, kutuphane yok, network yok, secret henuz olusturulmadi vb.)
sessizce .env dosyasindaki (zaten load_dotenv ile yuklenmis) degere duser.

Sadece TAVILY_API_KEY ve GEMINI_API_KEY icin kullanilir. DEEPSEEK_API_KEY
bu zincire DAHIL DEGILDIR - uretimde kullanilmadigi icin .env'de kaliyor.
"""
import os

_PROJECT_ID = "yeno-502112"
_cache = {}


def get_secret_or_env(secret_id: str, env_var_name: str):
    if env_var_name in _cache:
        return _cache[env_var_name]

    value = None
    try:
        from google.cloud import secretmanager
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{_PROJECT_ID}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(name=name)
        value = response.payload.data.decode("UTF-8").strip()
        print(f"[secret] {env_var_name}: Secret Manager'dan okundu.")
    except Exception as e:
        print(f"[secret] {env_var_name}: Secret Manager'a erisilemedi ({type(e).__name__}), .env'e dusuluyor.")
        value = os.getenv(env_var_name)

    _cache[env_var_name] = value
    return value
