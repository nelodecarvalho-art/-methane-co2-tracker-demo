from slowapi import Limiter
from slowapi.util import get_remote_address

# Módulo próprio (em vez de definir direto em main.py) pra evitar import
# circular: routers como auth.py precisam do `limiter` para o decorator
# @limiter.limit(...), e main.py precisa dos routers.
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
