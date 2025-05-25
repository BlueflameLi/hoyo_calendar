import sys

from pathlib import Path
from datetime import datetime
from loguru import logger
from git import Repo


async def deploy():
    docs_dir = Path(".")

    # 初始化 repo 对象
    repo = Repo(docs_dir)

    # 检查是否有更改需要提交
    if not repo.is_dirty(untracked_files=True):
        logger.info("没有需要提交的更改")
        return

    # 添加所有更改到暂存区
    repo.git.add(".")  # 或使用 repo.index.add(["."])

    # 准备提交信息
    time_now = datetime.now().strftime("%Y-%m-%d")
    commit_message = (
        f"Auto Update {time_now}"
        if len(sys.argv) > 1 and sys.argv[1] == "qinglong"
        else f"Update {time_now}"
    )

    # 提交更改
    repo.index.commit(commit_message)

    # 推送到远程
    origin = repo.remote("origin")
    origin.push("main")

    logger.info("提交成功")
