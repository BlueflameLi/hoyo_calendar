import sys

from pathlib import Path
from datetime import datetime
from loguru import logger
from git import Repo
from git.exc import GitCommandError


async def deploy():
    script_dir = Path(__file__).parent.parent.parent

    if not (script_dir / ".git").exists():
        logger.error(f"无法找到Git仓库：{script_dir}")
        return

    # 初始化 repo 对象
    repo = Repo(script_dir)

    # 检查是否有更改需要提交
    try:
        status = repo.git.status("--porcelain")
        if not status:
            logger.info("没有需要提交的更改")
            return
    except Exception as e:
        logger.error(f"检查Git状态时出错：{e}")
        return

    try:
        # 添加所有更改到暂存区
        repo.git.add(".")

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
        try:
            origin = repo.remote("origin")
            origin.push("main")
            logger.info("提交并推送成功")
        except GitCommandError as e:
            logger.error(f"推送到远程仓库失败：{e}")
            return

    except Exception as e:
        logger.error(f"Git操作失败：{e}")
        return
