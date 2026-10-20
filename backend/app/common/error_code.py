"""全局错误码：全项目唯一定义，禁止各接口自造状态码。"""


class ErrorCode:
    SUCCESS = 200
    BAD_REQUEST = 400        # 参数错误 / 凭证错误 / 资源不存在或无权访问
    UNAUTHORIZED = 401       # 未登录 / Token 失效
    DUPLICATE_CHECK = 409    # 今日已打卡（含锁冲突）
    SERVER_ERROR = 500
