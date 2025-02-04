# app/core/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from jose.exceptions import JWTError
import requests
from functools import lru_cache
from .config import get_settings

security = HTTPBearer()

class Auth0Handler:
    def __init__(self, domain, audience):
        self.domain = domain
        self.audience = audience
        self.algorithms = ["RS256"]
        self._jwks = None

    @property
    def jwks(self):
        if self._jwks is None:
            jwks_url = f"https://{self.domain}/.well-known/jwks.json"
            self._jwks = requests.get(jwks_url).json()
        return self._jwks

    def verify_token(self, token: str) -> dict:
        try:
            unverified_header = jwt.get_unverified_header(token)
            rsa_key = {}
            
            for key in self.jwks["keys"]:
                if key["kid"] == unverified_header["kid"]:
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"]
                    }
                    break

            if not rsa_key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Unable to find appropriate key"
                )

            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=self.algorithms,
                audience=self.audience,
                issuer=f"https://{self.domain}/"
            )
            
            return payload

        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )

@lru_cache()
def get_auth_handler():
    settings = get_settings()
    return Auth0Handler(
        domain=settings.AUTH0_DOMAIN,
        audience=settings.AUTH0_API_AUDIENCE
    )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_handler: Auth0Handler = Depends(get_auth_handler)
) -> dict:
    token = credentials.credentials
    payload = auth_handler.verify_token(token)
    return payload