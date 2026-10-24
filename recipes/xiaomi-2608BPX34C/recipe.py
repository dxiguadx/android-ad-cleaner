# 小米 18 Fold（2608BPX34C，HyperOS / Android 17）机型脚本
# 路径 2026-10-24 实测：逐段在真机上跑通（系统广告、商店、下载管理、主题、浏览器、全局搜索、负一屏）
# 与 docs/清单/小米-HyperOS.md 的差异：手机管家无「个性化推荐」「推荐内容」，浏览器无「宫格位推送/猜你想搜/小说」，
# 应用商店无「模式切换」，全局搜索的「热搜榜单」是二级页（资讯/全网/精选/知乎）而不是开关。
BUILD = "CP2A"
import time

ONLY = globals().get("ONLY") or []


def step(name):
    def deco(f):
        if (not ONLY or name in ONLY) and p.locked():
            print(f"\n== {name}：手机锁屏了，后面的都不跑"); return f
        if not ONLY or name in ONLY:
            print(f"\n== {name}"); p.miss = 0
            t = time.time()
            try:
                f()
            except Exception as e:
                print(f"  ✗ 出错：{e}")
            print(f"  ({time.time()-t:.0f} 秒)")
        return f
    return deco


def gear():
    """很多小米 App 的设置是右上角图标，没有文字：找 content-desc/资源 id 带「设置/setting」的可点元素。"""
    for n in p.tree().iter("node"):
        d = (n.get("content-desc") or "") + (n.get("resource-id") or "")
        if any(k in d.lower() for k in ("设置", "setting")) and n.get("clickable") == "true":
            from fast import bounds
            l, t, r, b = bounds(n); p.click((l + r) // 2, (t + b) // 2); time.sleep(1)
            return True
    return p.tap("设置", exact=True, scrolls=0)


def onscreen(sw):
    """折叠屏外屏 1168x1712：dump 里会混进另一块屏的副本，坐标越界的一律丢掉。"""
    return [s for s in sw if 0 <= s[2][0] < p.W and 0 <= s[2][1] < p.H]


@step("系统广告")
def _():
    # 设置 → 搜索「广告」→ 个性化广告推荐（入口实际在 隐私与安全/安全/更多安全设置/广告服务）
    p.setting("广告", "个性化广告推荐", box="搜索系统设置项")
    p.off(only=["个性化广告推荐"], page="系统·广告服务")


@step("应用商店")
def _():
    p.start("com.xiaomi.market")
    p.go("我的", "设置")
    gear()
    if p.tap("隐私设置", exact=True):
        p.tap("个性化服务", exact=True)
        p.off(only=["个性化服务"], page="商店·隐私"); p.back(2)
    if p.tap("通知设置", exact=True):
        # 关「推送消息」会连带关掉子项「点赞消息」「评论消息」；「应用更新」不在这里
        p.off(only=["新手帮助", "推送消息"], page="商店·通知"); p.back()
    p.back(2)


@step("下载管理")
def _():
    p.start("com.android.providers.downloads.ui")
    p.tap("更多", exact=True, scrolls=0)
    p.tap("设置", exact=True, scrolls=0)
    if p.tap("信息流设置", exact=True):
        p.off(only=["资源推荐", "热榜推荐"], page="下载管理·信息流")
    p.back(3)


@step("主题")
def _():
    p.start("com.android.themestore")
    p.go("我的", "设置")
    gear()
    # 「每次联网时通知」这一行有两个开关节点（行本身 + 右侧），只点 y 最小的那个，
    # 否则会把「自动更新」一起关掉
    for t, c, xy in onscreen(p.switches()):
        if t == "每次联网时通知" and c:
            p.click(*xy); p.confirm(); time.sleep(0.5)
            break
    if p.tap("隐私设置", exact=True):
        p.off(only=["个性化推荐"], page="主题·隐私"); p.back()
    p.back(2)


@step("浏览器")
def _():
    p.start("com.android.browser")
    p.tap("菜单", exact=True, scrolls=0)
    p.tap("设置", exact=True, scrolls=0)
    if p.tap("隐私和安全", exact=True):
        p.off(only=["个性化内容推荐", "个性化广告推荐"], page="浏览器·隐私和安全"); p.back()
    if p.tap("主页设置", exact=True):
        # 探索版 → 自定义主页；about:blank 会被判「无效网址」，用 bing 搜索页
        p.d(description="自定义主页", clickable=True).click(); time.sleep(1.2)
        p.d.clipboard = "https://www.bing.com"; time.sleep(0.4)
        p.d.shell("input keyevent 279")          # 粘贴
        time.sleep(0.8)
        p.tap("确定", exact=True, scrolls=0, wait=1.2)
        p.back()
    p.back(2)


@step("全局搜索")
def _():
    p.d.shell("am start -n com.android.quicksearchbox/com.android.quicksearchbox.preferences"
              ".SearchSettingsPreferenceActivity"); time.sleep(1.5)
    if p.tap("首页展示模块", exact=True):
        p.off(only=["搜索提示词"], page="搜索·首页模块")
        p.off(only=["推荐未安装应用"], page="搜索·应用推荐")
        # 「热搜榜单」行不是开关，点进去是「我的热榜」二级页：热搜→(资讯/全网)、生活→精选、话题→知乎
        for tab in ("热搜", "生活", "话题"):
            if not p.tap(tab, exact=True, scrolls=0):
                continue
            time.sleep(0.8)
            p.off(page=f"搜索·热榜/{tab}")
            p.back()
        p.back()
    p.back(2)


@step("负一屏")
def _():
    p.start("com.miui.personalassistant", ".settings.PASettingActivity")
    p.off(only=["推荐卡片", "热门活动"], page="负一屏·设置")     # 搜索框、出行助手保留
    # 这版没有独立「隐私设置」子页，个性化推荐由上面的「推荐卡片」控制
    p.back()


# 不在脚本里做、由 run.py 单独处理的两件事：
#   1) 广告包 com.miui.systemAdSolution：run.py suspend + 断网（重启后断网规则可能失效，要重跑）
#   2) 营销通知渠道：run.py chan-scan / chan-off
