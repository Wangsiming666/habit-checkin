"""业务异常：由全局异常处理器统一转换为 {code,msg,data} 结构。"""


class AppException(Exception):
    def __init__(self, code: int, msg: str):
        self.code = code
        self.msg = msg
        super().__init__(msg)
