# zcbot-render-assets

zcbot `image_renderer` 插件的**运行时资源发布仓库**。这里不放插件代码，只放打包好的资源包
`assets.zip`，通过 Release 分发。

主仓：https://github.com/kuangxing6367/zcbot

---

## 为什么单独一个仓库

这些东西原本躺在源码仓库的 `core_plugins/image_renderer/` 里，代价有三条：

1. **clone 与 CI 变慢**。解压后约 15MB 的二进制加字体，每次 clone、每次 CI 拉代码都要付一遍，
   而 CI 里 99% 的任务根本用不到它们。
2. **Python 包体积翻倍**。`python -m build` 打出来的 wheel 会因为携带 7 个平台的原生扩展
   而变成十几 MB，但装到机器上只有一个平台的产物有用，剩下 6 个是纯浪费。
3. **更新节奏和代码无关**。补一个字形子集、重编一个平台的 `.so`，跟框架发版是两件事。
   混在一起就只能为了一个字体改动去 bump 框架版本号。

拆开之后：主仓只有代码和 charset 元数据，资源按需下载，两边各自独立演进。

---

## 消费方

zcbot 框架 `core_plugins/image_renderer/`（v1.20.2 起）。由 `assets.py` 的 `AssetManager` 负责：

- 探测顺序：插件目录 → `data/image_renderer/assets/`（下载缓存）
- 下载目标：`<data>/image_renderer/assets/{fonts,native/<platform>/}`
- 落盘方式：先写 `.part` 再 `os.replace`，不会出现半截文件被当成可用资源

**默认不会自动下载。** `asset_consent` 默认是 `ask`，只在日志里提示「要下多少、下到哪、有什么用、
有什么局限」，由用户自己在配置面板里改成 `auto` 才会联网。理由是按流量计费或内网环境下，
静默拉 9MB 会被当成事故。

---

## 包内结构

固定布局，不做版本差异，方便人工核对：

```
assets.zip
├── manifest.json                         版本号 + 每个文件的 sha256/size
├── fonts/
│   ├── msyh_subset_common.ttf            2.64MB   常用字子集
│   ├── msyh_subset_ext.ttf               5.54MB   扩展字子集
│   ├── charset_common.txt                11KB     常用字表
│   └── charset_ext.txt                   20KB     扩展字表
└── native/
    ├── win64/zcbot_render.pyd            1.14MB
    ├── win32/zcbot_render.pyd            0.43MB
    ├── linux-x86_64/zcbot_render.so      0.69MB
    ├── linux-aarch64/zcbot_render.so     0.72MB
    ├── linux-i686/zcbot_render.so        0.73MB
    ├── linux-armv7/zcbot_render.so       0.60MB
    └── linux-loongarch64/zcbot_render.so 1.20MB
```

压缩后 `assets.zip` 约 8.99MB。解压后约 15MB。

---

## 平台支持

| 平台 | 原生扩展 | 说明 |
|---|---|---|
| Windows x64 / x86 | 有 | `.pyd`，与 CPython 版本相关，见下方注意 |
| Linux x86_64 / aarch64 / i686 / armv7 / loongarch64 | 有 | `.so` |
| macOS / FreeBSD / 其他 | **无** | 原生后端在这些平台上不可用；PIL 后端完全不受影响 |

注意：Windows 的 `.pyd` 与 CPython 版本绑定（当前产物面向 3.13 构建）。Python 版本对不上时
加载会失败，日志里是 `原生扩展加载失败`，此时只能退回 PIL 后端。

---

## 适用与局限

这一节比上面所有内容都重要。**这个包解决的是很窄的两个问题**，不是通用增强包：

它做两件事：

1. **补字体**。Pillow 自带字体不含中文，代码里若写了不存在的字体路径，中文会全部渲染成
   豆腐块（`中` `文` `测` `试` 四个字的位图指纹完全相同，肉眼就是四个方框）。字体子集解决这个。
2. **提供第二种渲染实现**。Rust + fontdue 光栅化 + image 编码，对外是同一套 Canvas API。
   适用场景是**没装 Pillow、或该平台没有 Pillow wheel 只能源码编译**的环境——这类环境下
   它是唯一可用的渲染后端。

它做不到什么（实测，win64 / Python 3.13）：

- **不能提速。** 绘制反而比 PIL 慢：纯渲染 3.1ms vs PIL 1.3ms（约 2.4 倍）；
  卡片端到端 8.7ms vs 6.9ms（约慢 25%）。PNG 编码更快，所以纯文本场景基本打平。
  如果你的目标只是画得更快，这个包帮不上忙，PIL 才是快的那个。
- **只有 12 个绘图原语**：`rect` / `line` / `circle` / `ellipse` / `gradient_rect` / `text` /
  `text_metrics` / `paste` / `blur` / `alpha_overlay` / `to_png` / `get_size`。
  没有 `resize` / `crop` / `rotate` / `arc` / `polygon` / `save`。
- **不减少依赖**。Pillow 仍在 requirements 里，它是默认后端。
- **字体是子集，不是全字库。** 只含 `charset_common.txt` 与 `charset_ext.txt` 里列出的字。
  生僻字 / emoji / 繁体扩展字仍会缺字，缺字时要落到系统字体（如 `msyh.ttc`）才有救。
- **失败不回退。** 用户显式选了 `backend: rust` 但资源拉不到时，插件明确报错而**不会**静默
  退回 PIL。静默降级会让人以为「选了 rust 但其实是 PIL 在跑」，性能和内存表现全对不上，
  问题会藏到最后才暴露。

---

## 获取方式

三种，任选：

**1. 自动下载**（推荐）

```yaml
# core_plugins.yaml
image_renderer:
  enabled: true
  backend: rust        # 默认 pil
  asset_consent: auto  # 默认 ask，ask 时不下载只提示
```

重启后插件会从 `asset_url` 拉取并校验，成功后写进 `data/image_renderer/assets/`。

**2. 手动放置**

下载 [assets.zip](https://github.com/kuangxing6367/zcbot-render-assets/releases/latest/download/assets.zip)
后解压，把 `fonts/` 和 `native/<你的平台>/` 放到：

```
<zcbot 数据目录>/image_renderer/assets/
├── fonts/...
└── native/<platform>/zcbot_render.pyd|.so
```

**3. 只补字体，不要原生扩展**

只用 PIL 后端但中文是豆腐块的，只放 `fonts/` 那 4 个文件即可，`native/` 可以整个不要。

`asset_url` 默认指向本仓库的 latest：

```
https://github.com/kuangxing6367/zcbot-render-assets/releases/latest/download/assets.zip
```

---

## 校验

`manifest.json` 里记录了每个文件的 `sha256` 和 `size`，插件解压时会逐条比对，不一致即判失败
并丢弃这次下载。手工核对整体压缩包：

```bash
sha256sum -c assets.zip.sha256
```

---

## 发布新版本

资源内容变更（补字形、重编某个平台的 `.so`）时走本仓库，**不动主仓版本号**：

```bash
python publish.py --from <主仓路径>/dist/assets.zip --tag assets-v1.20.2
```

tag 命名统一为 `assets-v<对应 zcbot 版本>`，方便追溯这份资源是跟哪版框架配套的。
内容修订但框架版本没变时，用同一个 tag 覆盖上传（`--clobber`），`latest` 链接始终指向最新。

---

## 许可

字体子集与原生扩展的来源、授权与该仓库的适用范围见 [NOTICE.md](NOTICE.md)。
