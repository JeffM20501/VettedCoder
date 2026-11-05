from rest_framework.pagination import CursorPagination, _positive_int
from rest_framework.exceptions import ValidationError

class VettedCursorPagination(CursorPagination):
    page_size=25
    max_page_size=100
    page_size_query_param="limit"
    ordering="-created_at"
    
    
    def _params(self,request):
        if hasattr(request, "query_params"):
            return request.query_params
        return request.GET
    
    def get_page_size(self,request):
        if self.page_size_query_param:
            params=self._params(request)
            try:
                return _positive_int(
                    params[self.page_size_query_param],
                    strict=True,
                    cutoff=self.max_page_size,
                )
            except (KeyError,ValueError):
                pass
        return self.page_size
    
    def decode_cursor(self,cursor): 
        try:
            return super()._decode_cursor(cursor)
        except Exception:
            #overide drf NotFound for ValidationError
            raise ValidationError(
                {"error":{"code":"invalid_cursor", "message":"Invalid cursor"}}
            )