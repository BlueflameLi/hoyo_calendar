import sys
import asyncio
import inspect

from pathlib import Path
from datetime import datetime
from loguru import logger

from src.utils.env import get_env
from src.utils.push import sc_send


async def run_command(command: list[str], cwd: Path = Path("."), desc: str = ""):
    logger.info(desc if desc else " ".join(command))
    process = await asyncio.create_subprocess_exec(
        command[0],
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        error_message = stderr.decode().strip()
        logger.error(f"命令执行失败: {error_message}")

        frame = inspect.currentframe()
        retries = (
            frame.f_back.f_locals["retries"]
            if frame and frame.f_back and hasattr(frame.f_back, "f_locals")
            else 0
        )
        if retries == 2 and get_env("PUSH_KEY"):
            sc_send(
                get_env("PUSH_KEY")[0],
                "hoyo_calendar 更新失败",
                f"""
命令执行失败: `{desc if desc else " ".join(command)}`
```
{error_message}
```
""",
            )
        raise RuntimeError(f"命令 {' '.join(command)} 执行失败")

    return stdout.decode().strip()


async def init_git(dir: Path) -> None:
    # 添加安全目录配置
    # await run_command(
    #     ["git", "config", "--global", "--add", "safe.directory", str(dir)],
    #     dir,
    #     "配置 Git 安全目录",
    # )
    # 设置git远程url
    if not get_env("GH_TOKEN") or not get_env("HC_GH_URL"):
        return
    gh_token = get_env("GH_TOKEN")[0]
    # repo_url = f"https://{gh_token}@github.com/Trrrrw/hoyo_video.git"
    repo_url = get_env("HC_GH_URL")[0].replace(
        "https://github.com", f"https://{gh_token}@github.com"
    )
    await run_command(
        ["git", "remote", "set-url", "origin", repo_url],
        dir,
        "设置 Git 远程仓库",
    )
    # 拉取最新代码
    await run_command(["git", "pull", "origin", "main"], dir, "拉取最新代码")


async def deploy():
    docs_dir = Path(f"{get_env('HC_OUTPUT_DIR')[0]}").parent.parent

    # 检查是否有更改需要提交
    status = await run_command(["git", "status", "--porcelain"], docs_dir)
    if not status:
        logger.info("没有需要提交的更改")
        return

    await run_command(["git", "add", "."], docs_dir)
    time_now = datetime.now().strftime("%Y-%m-%d")
    commit = f"Update {time_now}"
    if len(sys.argv) > 1 and sys.argv[1] == "qinglong":
        commit = f"Auto Update {time_now}"
    await run_command(["git", "commit", "-m", commit], docs_dir)
    await run_command(["git", "push", "-u", "origin", "main"], docs_dir)
    logger.info("提交成功")
