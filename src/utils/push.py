import httpx
import re


def sc_send(sendkey, title, desp="", options=None):
    if options is None:
        options = {}
    # 判断 sendkey 是否以 'sctp' 开头，并提取数字构造 URL
    if sendkey.startswith("sctp"):
        match = re.match(r"sctp(\d+)t", sendkey)
        if match:
            num = match.group(1)
            url = f"https://{num}.push.ft07.com/send/{sendkey}.send"
        else:
            raise ValueError("Invalid sendkey format for sctp")
    else:
        url = f"https://sctapi.ftqq.com/{sendkey}.send"
    params = {"title": title, "desp": desp, **options}
    headers = {"Content-Type": "application/json;charset=utf-8"}
    response = httpx.post(url, json=params, headers=headers)
    result = response.json()
    return result


if __name__ == "__main__":
    key = "SCT108502TCHRBDtnRRvzNrgPHyI6Sxgcy"

    ret = sc_send(
        key,
        "影像档案架 更新失败",
        """
命令执行失败: `git pull`
```
git pull error
```
""",
    )
    print(ret)
