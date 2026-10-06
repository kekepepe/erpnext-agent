# 简体中文展示包

用户于 2026-10-06 要求系统名称及语言统一为简体中文。本包只调整展示层，不改 ERPNext 核心、业务规则、权限、账务或已提交交易。

## 范围与依据

扫描当前固定镜像中的 7,299 个源码文件并保存摘要，提取 811 个单据元数据文件的 6,165 个字段标签和选项。实际会话另核验 811 类单据、193 个报表、19 个工作区、32 个工作区侧栏及 53 个打印格式的中文名称。它不是“人工审阅每一行业务代码”或“所有动态异常提示已逐条验证”的声明。

原生站点与启用用户语言统一为 `zh`；官方词库繁体转简体后，通过原生翻译接口补齐。列表名称使用原生翻译标志及限定字段格式器。十类交易单据增加中文打印格式，默认采用中文格式；标准格式不删除，显式英文兼容性检查仍保留。受保护标准格式拒绝语言属性更新，不能通过开启开发模式写回核心来绕过；其原始内部语言属性尚未全部改为中文，这属于明确未完成边界，不伪装为全量完成。

源码证明有两类原生缺口：侧栏直接显示应用英文标题，以及自动补全库的固定提示没有使用翻译函数。轻量 `erpnext_zh` 扩展只处理这些固定展示位置；观察器不改任意业务文本或表单输入值。

编号规则、单据/物料编码、接口名、代码示例、网址、邮箱、血型、纸型及条码标准代号不是系统中文名称，保留原值。个人姓名和外部自由文本不擅自改写。未逐页覆盖的可选模块和动态提示不得宣称零英文；后续发现须补词库和回归。

## 可重复执行

```sh
python3 -m venv .venv
.venv/bin/pip install -r phase0/localization/requirements.txt
./scripts/phase0-start.sh
.venv/bin/python scripts/phase0-localize.py --verify
.venv/bin/python -m unittest discover -s scripts -p 'test_phase0_localization.py'
PYTHONPYCACHEPREFIX=/private/tmp/erpnext-zh-pycache python3 -m compileall -q apps/erpnext_zh scripts
./scripts/phase0-check.sh
python3 scripts/phase0-validate-purchase.py
python3 scripts/phase0-validate-stock.py
python3 scripts/phase0-validate-sales.py
python3 scripts/phase0-validate-access.py
python3 scripts/phase0-validate-reporting.py
```

`--apply` 写入展示配置，`--verify` 读取新登录会话的真实词库并渲染十类合成交易。源清单可通过 `scripts/phase0-audit-language-source.py` 再生成。仅允许本机一次性环境凭据，输出不包含个人用户标识或会话令牌。

安装后必须带 `compose.zh.yaml`，不能用基础镜像重建已安装本应用的站点。镜像构建阶段注册应用并构建资源，避免前端与后端各自的静态资源目录导致脚本找不到。停止仍保留数据卷；不要执行 `down -v`，除非明确要删除全部测试数据。

恢复旧版不能仅切回基础镜像：需先评估原生应用卸载和中文配置回滚。未验证卸载/回滚，不承诺一键恢复。现有 PDF 下载资源连接问题仍是独立待解决项，HTML 预览通过不代表 PDF 通过。

## 词库来源与许可证

固定官方来源，仅复用翻译数据，不升级运行中业务软件：

| 文件 | 官方版本固定引用 | 许可证 |
| --- | --- | --- |
| frappe-zh-v15.csv | [0b282e81](https://github.com/frappe/frappe/blob/0b282e81ef30a7f6b8ff376ca8eacf9fb9f28f05/frappe/translations/zh.csv) | MIT |
| frappe-zh-v16.po | [97a5dd93](https://github.com/frappe/frappe/blob/97a5dd93ca5883bcc9c4ef9834120c5cba397b67/frappe/locale/zh.po) | MIT |
| erpnext-zh-v15.csv | [4cea6a7f](https://github.com/frappe/erpnext/blob/4cea6a7f839286b69dd30b38b0991e6ae234dac5/erpnext/translations/zh.csv) | GPL-3.0 |
| erpnext-zh-v16.po | [af63cde4](https://github.com/frappe/erpnext/blob/af63cde4941570ec7b9e12422c68302762cfcf91/erpnext/locale/zh.po) | GPL-3.0 |

对应完整许可保存在 `vendor/FRAPPE-LICENSE.txt` 与 `vendor/ERPNEXT-LICENSE.txt`。中文补充词条和经转简体处理的 ERPNext 派生词库继续遵循原 GPL 许可；展示应用的 MIT 声明不对上游数据重新许可。

固定词库摘要：

- frappe v15: `9e9dbd64f0965853e6be131b6335efdbba906a1a8e2908bfdd9f8888a2f0fdc8`
- frappe v16: `e9da9975d1068f3545637b998434bc83f1761f3154da05c287a560ab43cec569`
- erpnext v15: `233ab506626683446fb137dd8aab3fb6c28f78b1b6a55d803bc3cd537af00be9`
- erpnext v16: `1a4cf18f0bc8415f7108c453d9373e05de42d8f58ff671acff656df9167458a2`

## 本次验证记录

1. 静态盘点和实际词库覆盖：名称/字段非技术代号的英文残留为零；技术代号有明确排除清单。
2. 原生会话、权限与审批：五类合成用户均解析为简体中文；允许/拒绝访问及历史撤销审计通过。
3. 采购、库存、销售与报表：复用已有单据，通过；库存及应收应付没有漂移。容器重建期间一次销售/报表调用遭遇临时网关错误，重启后重跑通过。
4. 十类中文打印 HTML 通过；金额大写测试覆盖零、负数、舍入及跨万/亿分组。
5. 启动与资源验证中发现并修复应用资源注册及前端静态目录问题；最终脚本资源返回成功。实际浏览器列表和详情名称、按钮、侧栏及自动补全中文提示通过。
6. 完整启动脚本重复通过，词条、用户语言及列表脚本重复写入为零；新登录不带强制语言参数仍解析为中文。7,299 个核心源码摘要全部未改变。
7. 页面未空白、无框架错误遮罩，列表到标准格式详情的交互通过；桌面截图验证。原环境实时通信报“来源无效”，不是通过项；小屏、可选模块和全部动态提示未覆盖。
8. 原生标准打印格式更新遭遇保护校验，已停止该写入并保留原始模板。全部非标准格式及十类业务默认使用中文；不得宣称每个受保护标准模板的语言属性已被改写。

此包实现并验证了系统目录、字段及主要业务中文展示，但用户“所有语言/所有页面无英文”的更广泛要求尚不能据此整体关闭。下一小阶段需盘点动态页面和受保护模板的替代/退役方案，始终保留业务编码与核心源码。

## 后续清单与首批补译（2026-10-06）

按交接文件中的顺序执行：源码清单 → 原生补译/扩展 → 有证据才做版本化源码补丁 → 完整回归。清单阶段已推送为 `6a4e7de`；原生补译阶段尚未整体完成。

```sh
.venv/bin/python scripts/phase0-audit-language-ui.py
.venv/bin/python -m unittest discover -s scripts -p 'test_phase0*.py' -v
.venv/bin/python scripts/phase0-localize.py --apply --verify
```

`ui-source-audit.json` 保存剩余候选的源码路径、行号、原文及实际中文词库结果，不保存用户或会话数据。统计按出现位置计数，不是唯一缺陷数；正则扫描、动态表达式、模板条件与可选模块仍需运行核查。新增扫描包含元数据说明及网页帮助选项。

首批补译包含 16 条动态提示和两段打印帮助。`print-help-source.json` 来自固定版本 Frappe 的 `printing/doctype/print_format/print_format.json`（MIT，原许可证见 `vendor/FRAPPE-LICENSE.txt`）；只翻译 `print-help-prose.json` 中的说明，恢复并保留原始代码示例与链接，避免上游译文把代码符号翻译后破坏可用性。

本批实际验证：8 项离线测试通过，18 条词库读回通过，10 类中文打印预览通过，报表回归及健康检查通过；再次应用无改动。桌面列表进入标准格式详情并查看帮助通过，实时通信来源错误仍存在，小屏和其它动态触发流程未测试。完整交易/权限回归留在最终回归阶段，不能据本批宣称全站零英文。
