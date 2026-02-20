import os
from dotenv import load_dotenv

load_dotenv()

INFLUXDB_URL = os.getenv("INFLUXDB_URL", "")
INFLUXDB_TOKEN = os.getenv("INFLUXDB_TOKEN", "")
INFLUXDB_ORG = os.getenv("INFLUXDB_ORG", "")
INFLUXDB_BUCKET = os.getenv("INFLUXDB_BUCKET", "")
INFLUXDB_Measurement = os.getenv("INFLUXDB_Measurement", "")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Firebase Configuration
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "smart-park-iot-d7743")
FIREBASE_PRIVATE_KEY_ID = os.getenv("FIREBASE_PRIVATE_KEY_ID", "")
FIREBASE_PRIVATE_KEY = os.getenv("FIREBASE_PRIVATE_KEY", "")
FIREBASE_CLIENT_EMAIL = os.getenv(
    "FIREBASE_CLIENT_EMAIL", "firebase-adminsdk@smart-park-iot-d7743.iam.gserviceaccount.com")
FIREBASE_CLIENT_ID = os.getenv("FIREBASE_CLIENT_ID", "")
FIREBASE_CERT_URL = os.getenv("FIREBASE_CERT_URL", "")
FIREBASE_API_KEY = "AIzaSyAvlmocEGgpWviAtHTcPaoxQWh5PZ6QDbI"


def validate_config() -> None:
    missing = [k for k, v in {
        "INFLUXDB_URL": INFLUXDB_URL,
        "INFLUXDB_TOKEN": INFLUXDB_TOKEN,
        "INFLUXDB_ORG": INFLUXDB_ORG,
        "INFLUXDB_BUCKET": INFLUXDB_BUCKET,
        "INFLUXDB_Measurement": INFLUXDB_Measurement,
        "GROQ_API_KEY": GROQ_API_KEY,
    }.items() if not v]
    if missing:
        raise RuntimeError(
            f"Missing environment variables: {', '.join(missing)}")
