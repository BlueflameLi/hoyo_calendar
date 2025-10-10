# 🗓️ 米哈游游戏日历订阅

✨ 自动同步《原神》《星穹铁道》《绝区零》的官方活动日程到您的日历应用

## 📥 订阅方法

1. **复制**下方需要的日历链接
2. **打开**您使用的日历应用（支持Google日历、Outlook、苹果日历等）
3. 找到**订阅日历**功能，粘贴URL完成订阅

---

## 🏮 原神日历
| 分类       | 订阅链接                                                                                  |
| ---------- | ----------------------------------------------------------------------------------------- |
| 📌 全部日程 | [点击订阅](https://ghfast.top/raw.githubusercontent.com/BlueflameLi/hoyo_calendar/refs/heads/main/ics/原神.ics)              |
| 🌟 角色祈愿 | [点击订阅](https://ghfast.top/raw.githubusercontent.com/BlueflameLi/hoyo_calendar/refs/heads/main/ics/原神/祈愿.ics)         |
| 🎮 游戏活动 | [点击订阅](https://ghfast.top/raw.githubusercontent.com/BlueflameLi/hoyo_calendar/refs/heads/main/ics/原神/活动.ics)         |
| ⚙️ 版本更新 | [点击订阅](https://ghfast.top/raw.githubusercontent.com/BlueflameLi/hoyo_calendar/refs/heads/main/ics/原神/版本更新.ics)     |
<!-- | 📺 前瞻直播 | [点击订阅](https://ghfast.top/raw.githubusercontent.com/BlueflameLi/hoyo_calendar/refs/heads/main/ics/原神/前瞻特别节目.ics) | -->


## 🚄 星穹铁道日历
| 分类       | 订阅链接                                                                                  |
| ---------- | ----------------------------------------------------------------------------------------- |
| 📌 全部日程 | [点击订阅](https://ghfast.top/raw.githubusercontent.com/BlueflameLi/hoyo_calendar/refs/heads/main/ics/崩坏：星穹铁道.ics)              |
| 🌟 活动跃迁 | [点击订阅](https://ghfast.top/raw.githubusercontent.com/BlueflameLi/hoyo_calendar/refs/heads/main/ics/崩坏：星穹铁道/活动跃迁.ics)     |
| 🎮 游戏活动 | [点击订阅](https://ghfast.top/raw.githubusercontent.com/BlueflameLi/hoyo_calendar/refs/heads/main/ics/崩坏：星穹铁道/活动.ics)         |
| ⚙️ 版本更新 | [点击订阅](https://ghfast.top/raw.githubusercontent.com/BlueflameLi/hoyo_calendar/refs/heads/main/ics/崩坏：星穹铁道/版本更新.ics)     |
<!-- | 📺 前瞻直播 | [点击订阅](https://ghfast.top/raw.githubusercontent.com/BlueflameLi/hoyo_calendar/refs/heads/main/ics/崩坏：星穹铁道/前瞻特别节目.ics) | -->

## 🎧 绝区零日历
| 分类         | 订阅链接                                                                                    |
| ------------ | ------------------------------------------------------------------------------------------- |
| 📌 全部日程   | [点击订阅](https://ghfast.top/raw.githubusercontent.com/BlueflameLi/hoyo_calendar/refs/heads/main/ics/绝区零.ics)              |
| 🌟 代理人调频 | [点击订阅](https://ghfast.top/raw.githubusercontent.com/BlueflameLi/hoyo_calendar/refs/heads/main/ics/绝区零/调频.ics)         |
| 🎮 游戏活动   | [点击订阅](https://ghfast.top/raw.githubusercontent.com/BlueflameLi/hoyo_calendar/refs/heads/main/ics/绝区零/活动.ics)         |
| ⚙️ 版本更新   | [点击订阅](https://ghfast.top/raw.githubusercontent.com/BlueflameLi/hoyo_calendar/refs/heads/main/ics/绝区零/版本更新.ics)     |
<!-- | 📺 前瞻直播   | [点击订阅](https://ghfast.top/raw.githubusercontent.com/BlueflameLi/hoyo_calendar/refs/heads/main/ics/绝区零/前瞻特别节目.ics) | -->

> - 由于使用新的方式获取日程，上面的部分链接可能没有对应文件

---

## ⚙️ 高级选项

🔹 **连续日程模式**：在URL的`/ics/`后添加`continuous/`即可订阅带持续时间的完整日程  
> 示例：`https://ghfast.top/raw.githubusercontent.com/BlueflameLi/hoyo_calendar/refs/heads/main/ics/continuous/原神.ics`

## 🚀 快速开始

### 环境要求
- Python 3.10+

### 配置
- 程序自带三款游戏的接口信息，会在仓库根目录下写入 `data/` 与 `ics/`
- 如需自定义输出目录，可通过 `python cli.py update --data-output-dir ... --ics-output-dir ...`
- 调试本地 mock 时使用 `--debug-mocks`，并在 `mocks/{game_id}/` 放置 `ann_list.json` / `ann_content.json`

### 操作步骤
```bash
# 克隆项目
git clone https://github.com/BlueflameLi/hoyo_calendar.git
cd hoyo_calendar

# 安装依赖
pip install -r requirements.txt

# 运行同步（默认输出到 data/ 与 ics/）
python main.py
```

### 自动化更新
- GitHub Actions 工作流 `.github/workflows/daily-refresh.yml` 默认每日 02:00 CST 执行 `python main.py`
- 工作流会将更新内容直接提交到 `main` 分支，无需额外服务器或定时任务

## 🌟 项目特点
- ✅ 自动同步官方活动日程
- 🆓 完全免费开源
- 🔄 每日自动更新
- 📅 支持主流日历应用

---

## 🙏 特别感谢
- [hoyo_calendar](https://github.com/Trrrrw/hoyo_calendar)

---

> 📢 本项目为爱好者制作，与米哈游官方无关  
