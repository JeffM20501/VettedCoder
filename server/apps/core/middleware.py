import uuid
from contextvars import ContextVar

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")

class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response=get_response
        
    def __call__(self,request):
        rid=request.headers.get("X-Request-ID") or str(uuid.uuid7())
        request.request_id=rid
        token=request_id_ctx.set(rid)
        try:
            response=self.get_response(request)
            response["X-Request-ID"]=rid
            return response
        finally:
            request_id_ctx.reset(token)
        
        