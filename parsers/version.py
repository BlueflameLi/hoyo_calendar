"""Determine game version metadata from announcement data."""

from __future__ import annotations

from datetime import datetime

from dto import AnnListRe

from .text import extract_floats, extract_inner_text, remove_html_tags


class VersionMetadata:
    """Convenience wrapper to extract version information from API responses."""

    def __init__(self, game: str, ann_list_re: AnnListRe):
        self.game = game
        self.ann_list_re = ann_list_re
        label = "公告" if game == "sr" else "游戏公告"
        game_notices = [
            item for item in ann_list_re.data.ann_types if item.type_label == label
        ]
        notices = game_notices[0].ann_list if game_notices else []
        target_keyword = f"{'版本' if self.game != 'zzz' else ''}更新说明"
        self.version_update_ann = [
            ann
            for ann in notices
            if target_keyword in remove_html_tags(ann.title)
        ]
        self.code = self._set_version_code()
        self.name = self._set_version_name()
        self.banner = self._set_version_banner()
        self.next_version_sp_time = self._set_version_sp_time()
        self.next_version_name = self._set_next_version_name()
        self.next_version_code = self._set_next_version_code()
        self.start_time, self.end_time = self._set_version_time()

    def _set_version_name(self) -> str:
        if self.version_update_ann:
            return extract_inner_text(remove_html_tags(self.version_update_ann[0].title))
        return "未知"

    def _set_version_code(self) -> str:
        if self.version_update_ann:
            return str(extract_floats(remove_html_tags(self.version_update_ann[0].title))[0])
        return "0.0"

    def _set_version_time(self) -> tuple[datetime, datetime]:
        if self.version_update_ann:
            start = self.version_update_ann[0].start_time.replace(hour=11, minute=0, second=0)
            end = self.version_update_ann[0].end_time.replace(hour=6, minute=0, second=0)
            return start, end
        now = datetime.now()
        return now, now

    def _set_version_sp_time(self) -> datetime | None:
        sp_ann = self._get_sp_announcements()
        if sp_ann:
            return sp_ann[0].end_time
        return None

    def _set_next_version_name(self) -> str | None:
        sp_ann = self._get_sp_announcements()
        if sp_ann:
            return extract_inner_text(sp_ann[0].title)
        return None

    def _set_next_version_code(self) -> str | None:
        sp_ann = self._get_sp_announcements()
        if sp_ann:
            floats = extract_floats(sp_ann[0].title)
            if floats:
                return str(floats[0])
        return None

    def _get_sp_announcements(self):
        notices_with_sp = []
        if self.game == "genshin":
            notices_with_sp = [
                item
                for item in self.ann_list_re.data.ann_types
                if item.type_label == "活动公告"
            ]
            notices_with_sp = notices_with_sp[0].ann_list if notices_with_sp else []
        elif self.game == "sr":
            notices_with_sp = [
                item
                for item in self.ann_list_re.data.pic_list
                if item.type_label == "资讯"
            ]
            if notices_with_sp:
                notices_with_sp = notices_with_sp[0].type_list[0].ann_list
        elif self.game == "zzz":
            notices_with_sp = [
                item
                for item in self.ann_list_re.data.pic_list
                if item.type_label == "丽都资讯"
            ]
            if notices_with_sp:
                notices_with_sp = notices_with_sp[0].type_list[0].ann_list
        return [
            ann
            for ann in notices_with_sp
            if "前瞻特别节目" in remove_html_tags(ann.title)
        ]

    def _set_version_banner(self) -> str:
        if self.version_update_ann:
            return self.version_update_ann[0].banner
        return ""
