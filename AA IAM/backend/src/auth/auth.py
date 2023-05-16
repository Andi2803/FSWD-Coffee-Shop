import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen


AUTH0_DOMAIN = 'dev-8p5tikh5slwhd7b6.us.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'fswd-andreas'

## AuthError Exception
'''A standardized way to communicate auth failure modes'''
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


## Auth Header

# TODO implement get_token_auth_header() method
def get_token_auth_header():
    """Obtains the Access Token from the Authorization Header
    
    Returns:
        str: Token (part of the header)
    
    Raises:
        AuthError: If the Authorization header is missing, malformed, or contains an invalid token.
    """
    auth = request.headers.get('Authorization')

    if not auth:
        raise AuthError({
            'code': 'authorization_header_missing',
            'description': 'Authorization header is expected.'
        }, 401)

    parts = auth.split()

    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must be in the format "Bearer <token>".'
        }, 401)

    return parts[1]



# TODO implement check_permissions(permission, payload) method
def check_permissions(permission, payload):
    """Check if the permission is included in the payload's permissions array.
    
    Args:
        permission (str): The requested permission string.
        payload (dict): The decoded JWT payload.
    
    Returns:
        bool: True if the permission is found in the payload permissions array.
    
    Raises:
        AuthError: If the permissions are not included in the payload or the requested permission is not found.
    """
    if 'permissions' not in payload:
        raise AuthError({
            'code': 'invalid_claims',
            'description': 'Permissions not included in JWT.'
        }, 400)

    if permission not in payload['permissions']:
        raise AuthError({
            'code': 'unauthorized',
            'description': 'Permission not found.'
        }, 403)

    return True


# TODO implement verify_decode_jwt(token) method
def verify_decode_jwt(token):
    """Verifies and decodes a JWT token.
    
    Args:
        token (str): The JSON Web Token to be verified and decoded.
    
    Returns:
        dict: The decoded payload of the JWT.
    
    Raises:
        AuthError: If the token is malformed, expired, has incorrect claims, or fails verification.
    """
    # Verify token
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())
    unverified_header = jwt.get_unverified_header(token)
    
    # Check if Key id is in unverified header
    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)

    rsa_key = {}  # initialize empty private rsa key as dict
    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    if rsa_key:
        try:
            # Use Auth Config (top of file) to decode JWT and return payload if successful
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
            )
            return payload

        except jwt.ExpiredSignatureError:
            # Token expired
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)

        except jwt.JWTClaimsError:
            # Incorrect claims
            raise AuthError({
                'code': 'invalid_claims',
                'description': 'Incorrect claims. Please, check the audience and issuer.'
            }, 401)

        except Exception:
            # Unable to parse authentication token
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 400)

    # Unable to find the appropriate key
    raise AuthError({
        'code': 'invalid_header',
        'description': 'Unable to find the appropriate key.'
    }, 400)

# TODO implement @requires_auth(permission) decorator method
def requires_auth(permission=''):
    """Authentication wrapper decorator for endpoint functions.
    
    Args:
        permission (str): The required permission for the endpoint.
    
    Returns:
        function: The decorator function that wraps the endpoint function.
    """
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            try:
                payload = verify_decode_jwt(token)
            except AuthError:
                raise AuthError({
                    'code': 'unauthorized',
                    'description': 'Permissions not found'
                }, 401)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)
        return wrapper
    return requires_auth_decorator
