# CHANGELOG

本仓库只记录**资源包**的变更。框架代码的变更见主仓：
https://github.com/kuangxing6367/zcbot/blob/main/CHANGELOG.md

版本号 `assets-v<X.Y.Z>` 中的 `X.Y.Z` 是这份资源**配套的 zcbot 框架版本**，
不是资源自己的版本。资源内容修订但框架没发版时，覆盖同一个 tag 重新上传。

---

## assets-v1.20.2 (2026-11-06)

首个独立仓库版本。资源内容与之前挂在主仓 Release 上的那份一致，迁移原因是主仓
不该同时承担代码版本与二进制分发的两种节奏。

- 字体子集 4 个文件（`msyh_subset_common.ttf` 2.64MB、`msyh_subset_ext.ttf` 5.54MB、
  `charset_common.txt`、`charset_ext.txt`）
- 原生扩展 7 个平台：`win64`、`win32`、`linux-x86_64`、`linux-aarch64`、`linux-i686`、
  `linux-armv7`、`linux-loongarch64`
- `manifest.json` 记录每个文件 sha256 与 size，供运行时逐条校验
- 压缩包 8.99MB / 11 个文件
