# NOTICE

本仓库的文件分两类，授权状况**完全不同**，请分别看待。

---

## 1. 原生扩展 `native/**`

zcbot 项目自有产物，由主仓 `core_plugins/image_renderer/native/src/lib.rs`（Rust）编译而来：

- `zcbot_render.pyd` / `zcbot_render.so`

授权与主仓一致，双许可 **MIT OR Apache-2.0**，全文见主仓的 `LICENSE` 与 `LICENSE-APACHE`：
https://github.com/kuangxing6367/zcbot

构建时链接的第三方 Rust crate（`pyo3`、`fontdue`、`image` 等）各自保留其原有许可，
分发时请一并遵守。

---

## 2. 字体子集 `fonts/**`

**这一部分不是开源字体，本仓库不为其授予任何许可。**

| 文件 | 来源 |
|---|---|
| `msyh_subset_common.ttf` | 从 **Microsoft YaHei（微软雅黑）** 裁出的子集 |
| `msyh_subset_ext.ttf` | 同上，更大的字符覆盖范围 |
| `charset_common.txt` | 上述子集收录的字符清单 |
| `charset_ext.txt` | 同上 |

事实说明：

- 微软雅黑的版权归 **Microsoft Corporation** 所有，字形设计出自方正电子。它是随 Windows
  授权的商业字体，**不是** SIL OFL 那类可自由再分发的字体。
- 这里的两个 `.ttf` 是**子集**（只保留 zcbot 渲染实际用到的字符），不是原始字体文件，
  也不含任何 `fvar`/`gvar` 可变轴或完整字形表。子集化降低的是体积，**不改变其授权性质**。
- 提供它们的目的只有一个：让 zcbot 在**没有该字体的机器上**（Linux 容器、精简系统）也能
  正常渲染中文，而不是把中文画成一排方框。它是作为渲染依赖被嵌入的，不是作为字体产品分发。
- 如果你所在司法辖区或你的使用场景不允许这种再分发，请**不要下载本包的 `fonts/` 部分**：
  只取 `native/` 一样可以工作，字体改用系统已授权的字体文件（配置项 `font_path`）。

**权利方如需下架**：开 issue 或直接联系仓库维护者，字体会在确认后第一时间从 Release 与
仓库历史中移除，`native/` 部分不受影响。

---

## 3. 免责

本仓库内容按「现状」提供，不附带任何明示或暗示的担保。因使用本仓库文件产生的
字体授权纠纷，由使用者自行承担。
