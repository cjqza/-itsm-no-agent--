"""通用工具函数"""


def escape_like(s: str) -> str:
    """转义 LIKE 查询中的特殊字符（% 和 _），防止通配符注入"""
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
