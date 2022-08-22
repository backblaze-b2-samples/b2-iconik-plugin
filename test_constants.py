from common import AUTH_TOKEN_NAME, SHARED_SECRET_NAME


APP_ID = "ICONIK_PLUGIN"
LL_STORAGE_ID = "d39b62e1-c586-438a-a82b-70543c228c1b"
B2_STORAGE_ID = "73a746d2-a3ed-4d61-8fd9-aa8f37a27bbb"
INVALID_STORAGE_ID = '4e14b12e-ce4c-4920-a2b8-7a8dfa533256'

# Values for secrets
AUTH_TOKEN = "SECRET_SQUIRREL"
SHARED_SECRET = 'top_secret'

SECRETS = { 
    SHARED_SECRET_NAME: SHARED_SECRET,
    AUTH_TOKEN_NAME: AUTH_TOKEN
}

# Random UUIDs for objects
JOB_ID = 'eff79bf8-c782-11ec-8e9b-b66ad3c6ae38'
ASSET_ID = '0d56db81-1b8e-4a68-9658-98ad9a94d841'
ORIGINAL_FORMAT_ID = '0fcfe5f1-eb85-4529-9bd0-3e856b358c81'
PPRO_PROXY_FORMAT_ID = 'a45fc28d-0deb-4e14-8c79-1fc11966177c'
FILE_SET_ID = '0436578d-8418-48b0-89ad-9c719b65137f'
COLLECTION_ID = '8ae20508-88b0-414e-8b4c-3fa2683e79e0'
SUBCOLLECTION_ID = 'bf049e70-6749-4e44-a85b-7457236cdf4e'
MULTI_COLLECTION_ID = '7e6abeea-4bff-4153-912d-2880617046ce'

PAYLOAD = {
    "user_id": "256ebe90-c0c8-11ec-9fcd-0648baddf8b3",
    "system_domain_id": "57016980-6e13-11e8-ab5a-0a580a3c0f5c",
    "context": "BULK",
    "action_id": "86f485b2-c71e-11ec-93c4-32f3401f5ebb",
    "asset_ids": [
        ASSET_ID
    ],
    "collection_ids": [
        SUBCOLLECTION_ID
    ],
    "saved_search_ids": [],
    "metadata_view_id": None,
    "metadata_values": None,
    "date_created": "2022-04-29T00:22:10.316685",
    "auth_token": AUTH_TOKEN
}
