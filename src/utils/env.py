import os

from loguru import logger


def get_env(*args: str) -> list[str]:
    """获取环境变量"""
    env_list = []
    for arg in args:
        env_arg = os.getenv(arg, None)
        if not env_arg:
            if arg != "DEGUG":
                logger.error(f"未找到环境变量{arg}")
        else:
            env_list.append(env_arg)
    return env_list
