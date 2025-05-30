import asyncio

from loguru import logger
from pathlib import Path

from src.utils.env import get_env
from src.utils.config import Config, load_config
from src.utils.data import load_game_data, save_game_data, extract_game_list
from src.utils.api import get_ann_list, get_ann_content
from src.utils.data_parser.version import Version
from src.utils.ics import export_ics
from src.utils.deploy import deploy


async def update(config: Config):
    logger.info(f"{'《' + config.name.zh + '》':　>9}开始更新")
    output_folder = Path(get_env("HC_OUTPUT_DIR")[0])
    game_name_cn = config.name.zh
    # 加载已存在的游戏数据
    exist_data = await load_game_data(output_folder, game_name_cn)
    # 复制原始数据，用于后续比较
    origin_data = exist_data.model_copy()

    # 获取公告列表
    ann_list_re = await get_ann_list(config)
    with Version(
        config.name.en,
        ann_list_re,
    ) as version:
        current_version = version.code
        current_version_name = version.name
        logger.info(
            f"{'《' + config.name.zh + '》':　>9}{current_version}-「{current_version_name}」"
        )
        logger.info(
            f"{'《' + config.name.zh + '》':　>9}{version.start_time} -> {version.end_time}"
        )
        # 设置当前版本信息
        exist_data.set_version_info(
            current_version,
            current_version_name,
            version.banner,
            version.start_time,
            version.end_time,
        )
        if version.next_version_code is not None:
            logger.info(
                f"{'《' + config.name.zh + '》':　>9}{version.next_version_code}前瞻节目时间：{version.next_version_sp_time}"
            )
            # 设置下一个版本信息
            exist_data.set_version_info(
                version.next_version_code,
                name=version.next_version_name,
                sp_time=version.next_version_sp_time,
            )

        # 获取公告内容
        ann_content_re = await get_ann_content(config)
        # 更新公告信息
        exist_data.update_ann(
            config.name.en,
            version.code,
            version.start_time,
            ann_list_re,
            ann_content_re,
        )
        logger.info(
            f"{'《' + config.name.zh + '》':　>9}{version.code}版本共：{len(next(v for v in exist_data.version_list if v.code == version.code).ann_list)}个事件"
        )

    # 提取游戏列表
    extract_game_list(
        output_folder,
        config.name.zh,
        config.icon,
        True if exist_data != origin_data else False,
    )
    # 保存游戏数据
    await save_game_data(output_folder, config.name.zh, exist_data)
    ics_folder = Path(get_env("HC_ICS_DIR")[0])
    # 导出 ICS 文件
    await export_ics(exist_data, config.name.zh, ics_folder)
    await export_ics(
        exist_data, config.name.zh, output_folder.parent.parent / "public/ics"
    )


async def main():
    configs = await load_config(Path(get_env("HC_CONFIGS_DIR")[0]))
    logger.info(f"找到 {len(configs)} 个配置文件")
    async with asyncio.TaskGroup() as tg:
        [tg.create_task(update(config)) for config in configs]
    await deploy()


if __name__ == "__main__":
    asyncio.run(main())
