import sys

from pathlib import Path
from datetime import datetime
from loguru import logger
from git import Repo
from git.exc import GitCommandError


async def deploy():
    try:
        repo = Repo(Path(__file__).resolve().parent.parent.parent)
        origin = repo.remote()

        # 检查是否有更改需要提交
        try:
            status = repo.git.status("--porcelain")
            if not status:
                logger.info("没有需要提交的更改")
                return
        except Exception as e:
            logger.error(f"检查Git状态时出错：{e}")
            return

        # 拉取远程更改
        origin.pull()

        # 添加所有更改
        repo.git.add(".")

        # 提交更改
        time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit = f"Update {time_now}"
        if len(sys.argv) > 1 and sys.argv[1] == "qinglong":
            commit = f"Auto Update {time_now}"
        repo.index.commit(commit)

        # 推送到远程
        origin.push()
        logger.info("提交并推送成功")

    except GitCommandError as e:
        logger.info(f"Git操作失败: {str(e)}")
        return
    except Exception as e:
        logger.info(f"发生错误: {str(e)}")
        return
