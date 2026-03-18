"""Helper script para ejecutar queries GAQL contra Google Ads API.

Usa la misma service account que el MCP pero directamente via la librería
google-ads de Python.

Uso:
    python scripts/google_ads_query.py <customer_id> "<GAQL query>"

Output:
    JSON array con los resultados
"""

import json
import os
import sys

from google.ads.googleads.client import GoogleAdsClient
from google.oauth2.service_account import Credentials


def main():
    if len(sys.argv) < 3:
        print("Usage: python google_ads_query.py <customer_id> <query>", file=sys.stderr)
        sys.exit(1)

    customer_id = sys.argv[1].replace("-", "")
    query = sys.argv[2]

    # Credenciales via env vars (obligatorio)
    credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    developer_token = os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN", "")
    login_customer_id = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "5971963548")

    if not credentials_path or not developer_token:
        print("Error: GOOGLE_APPLICATION_CREDENTIALS y GOOGLE_ADS_DEVELOPER_TOKEN son requeridos", file=sys.stderr)
        sys.exit(1)

    credentials = Credentials.from_service_account_file(
        credentials_path,
        scopes=["https://www.googleapis.com/auth/adwords"],
    )

    client = GoogleAdsClient(
        credentials=credentials,
        developer_token=developer_token,
        login_customer_id=login_customer_id,
    )

    ga_service = client.get_service("GoogleAdsService")

    try:
        response = ga_service.search(customer_id=customer_id, query=query)

        results = []
        for row in response:
            row_dict = {}
            # Convertir protobuf row a dict plano
            for field_name in row.__class__.__dict__:
                if field_name.startswith("_"):
                    continue
                try:
                    obj = getattr(row, field_name)
                    for attr_name in obj.__class__.__dict__:
                        if attr_name.startswith("_"):
                            continue
                        try:
                            val = getattr(obj, attr_name)
                            if callable(val):
                                continue
                            key = f"{field_name}.{attr_name}"
                            # Convertir enums a string
                            if hasattr(val, "name"):
                                row_dict[key] = val.name
                            else:
                                row_dict[key] = val
                        except (AttributeError, TypeError):
                            pass
                except (AttributeError, TypeError):
                    pass
            results.append(row_dict)

        print(json.dumps(results, default=str))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
