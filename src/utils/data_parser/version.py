from datetime import datetime

from src.dto.ann_list import AnnListRe
from src.utils.txt_parser import extract_floats, remove_html_tags, extract_inner_text


class Version:
    def __init__(self, game: str, ann_list_re: AnnListRe):
        self.game = game
        self.ann_list_re = ann_list_re
        game_notices = [
            item
            for item in ann_list_re.data.ann_types
            if item.type_label == ("公告" if game == "sr" else "游戏公告")
        ][0]
        self.version_update_ann = [
            ann
            for ann in game_notices.ann_list
            if f"{'版本' if self.game != 'zzz' else ''}更新说明"
            in remove_html_tags(ann.title)
        ]
        self.code = self.set_version_code()
        self.name = self.set_version_name()
        self.banner = self.set_version_banner()
        self.next_version_sp_time = self.set_version_sp_time()
        self.next_version_name = self.set_next_version_name()
        self.next_version_code = self.set_next_version_code()
        self.start_time, self.end_time = self.set_version_time()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback): ...

    def set_version_name(self) -> str:
        if len(self.version_update_ann) > 0:
            return extract_inner_text(
                remove_html_tags(self.version_update_ann[0].title)
            )
        else:
            return "未知"

    def set_version_code(self) -> str:
        if len(self.version_update_ann) > 0:
            return str(
                extract_floats(remove_html_tags(self.version_update_ann[0].title))[0]
            )
        else:
            return "0.0"

    def set_version_time(self) -> tuple[datetime, datetime]:
        if len(self.version_update_ann) > 0:
            return (
                self.version_update_ann[0].start_time.replace(
                    hour=11, minute=0, second=0
                ),
                self.version_update_ann[0].end_time.replace(hour=6, minute=0, second=0),
            )
        else:
            return (
                datetime.now(),
                datetime.now(),
            )

    def set_version_sp_time(self) -> datetime | None:
        sp_ann = self._get_sp_ann()
        if len(sp_ann) > 0:
            return sp_ann[0].end_time
        else:
            return None

    def set_next_version_name(self) -> str | None:
        sp_ann = self._get_sp_ann()
        if len(sp_ann) > 0:
            return extract_inner_text(sp_ann[0].title)
        else:
            return None

    def set_next_version_code(self) -> str | None:
        sp_ann = self._get_sp_ann()
        if len(sp_ann) > 0:
            return str(extract_floats(sp_ann[0].title)[0])
        else:
            return None

    def _get_sp_ann(self) -> list:
        notices_with_sp = []
        match self.game:
            case "genshin":
                notices_with_sp = [
                    item
                    for item in self.ann_list_re.data.ann_types
                    if item.type_label == "活动公告"
                ][0].ann_list
            case "sr":
                notices_with_sp = (
                    [
                        item
                        for item in self.ann_list_re.data.pic_list
                        if item.type_label == "资讯"
                    ][0]
                    .type_list[0]
                    .ann_list
                )
            case "zzz":
                notices_with_sp = (
                    [
                        item
                        for item in self.ann_list_re.data.pic_list
                        if item.type_label == "丽都资讯"
                    ][0]
                    .type_list[0]
                    .ann_list
                )
        return [
            ann
            for ann in notices_with_sp
            if "前瞻特别节目" in remove_html_tags(ann.title)
        ]

    def set_version_banner(self) -> str:
        if len(self.version_update_ann) > 0:
            return self.version_update_ann[0].banner
        else:
            return ""
