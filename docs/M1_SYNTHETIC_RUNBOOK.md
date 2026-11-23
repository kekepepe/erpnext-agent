# 合成期初导入与异站恢复

使用两套独立空卷和一个全新的恢复目的地；仅限本地，端口依次为 18082、18083、18084。8080 为日常工作台，18081 为 C0 站，均不参与写入。前提为已有 C0 固定版本的 workbench 镜像、Docker Compose、项目 .venv 和 pdftotext。按仓库根目录执行。每个新站命令输出独立 Compose 项目名；保留它用于本轮恢复及后续停止服务。端口已占用时先核实项目，勿删卷或重置现有站。

1. 分别运行 `sh scripts/phase0-new-migration-site.sh 18082` 与 `sh scripts/phase0-new-migration-site.sh 18083`。它们从空站配置合成公司、组织/仓库、单位、商品、往来、九角色及审批。检查两站均可登录后再导入。
2. 使用 `phase0/migration/mapping-clean-site.json`。样例旧账表使用中文稳定键；新建站为英文原生科目。既有工作台的中文科目表仅适用原来的 mapping-example。先核对来源 SHA-256、截止日及三个控制科目。
3. 每站先将四份原生报表导出到一个新的受控目录，再运行导入、重放和比较。第一站故意在库存过账后中断：`--apply --stop-after stock` 仅在输出首张已过账单号及预定中断消息时为预期失败；没有该消息立即排查。第二站直接完整执行。每站仅允许一个操作人和一个导入进程，不接受其他交易；异常先停写，从原生记录查明结果，再运行同命令。不支持生产并发或批次外历史单据。
4. 汇总结果必须是库存 2 件/20 元、应收 15、应付 8、期初权益贷方 27。销售发票 19 收 4、采购发票 12 付 4，两笔核销须分别引用对应发票。两笔现金流相抵；期初权益凭证只结转过渡科目，不能把库存和往来再记一遍。演练使用原生库存、发票及收付款审批；仅本独立合成站的结转凭证由迁移管理员过账，不代表生产财务审批或已获签核。
5. 导出包包含 target.csv、原始四表和 manifest。比较工具核对两份文件摘要、公司/时区/截止日和完整余额键，再逐项比较。试算表使用期末净借贷、排除分组汇总；未映射非零余额仍参与比较，映射的零余额叶科目显式保留。ERPNext 此版本可能将未来日期的期初分录纳入某些历史试算；有这类分录就拒绝出具快照。导出期间应停业务写入；这四次原生读取不是数据库事务快照。
6. 使用 `sh scripts/phase0-new-migration-site.sh 18084` 新建空白恢复站，再执行 `sh scripts/phase0-restore-opening.sh <18082的项目名> <18084的项目名>`。程序校验端口、镜像、卷和空目标，备份源停入口及任务后通过 Bench 恢复数据库、公私文件；保留目的地数据库连接、还原加密配置并配置内部打印地址。验证凭证和审批指纹、九岗登录、越权拒绝、七报表、单张原生 PDF、两个附件与七行余额。失败时保留专用卷及证据供定位；不得在非空站重跑恢复。完整备份、原始单据和配置包不入 Git。
7. 经确认演练结束，可对本次创建的三个**确切**项目使用 Compose stop 停服务，保留卷。正式验收需要真实账套、角色、十类正式打印、匹配版本回退与岗位签核，合成演练不能替代。

单站命令（第二站将端口改为 18083，每次导出目录必须不存在）：

```sh
export PHASE0_BASE_URL=http://localhost:18082
evidence=$(mktemp -d)
map=phase0/migration/mapping-clean-site.json
source_csv=phase0/migration/opening-mapping-example.csv
.venv/bin/python scripts/phase0-preflight-migration.py "$map" "$source_csv" --check-native
.venv/bin/python scripts/phase0-export-opening.py "$map" "$evidence/before"
# 仅第一站执行并检查预定中断：
.venv/bin/python scripts/phase0-rehearse-opening.py --port 18082 --apply --stop-after stock
.venv/bin/python scripts/phase0-rehearse-opening.py --port 18082 --apply
.venv/bin/python scripts/phase0-rehearse-opening.py --port 18082 --apply
.venv/bin/python scripts/phase0-export-opening.py "$map" "$evidence/after"
.venv/bin/python scripts/phase0-preflight-migration.py "$map" "$source_csv" --check-native --target "$evidence/after/target.csv"
```

## 扩展合成批次

在另一组空卷按同样步骤运行，把配置、来源文件和执行选项分别换为 `mapping-expanded.json`、`opening-expanded.csv` 和 `--expanded`。逐笔明细见 `vouchers-expanded.json`。2026-11-01 的合成基准为主仓 2 件、分仓 1 箱（原生 Box 换算 50 件），存货 520 元。同一客户两张销售发票分别应收 15 元和 30 元，供应商一张应付 8 元。财务核销按外部单号关联，每个发票分别回读剩余金额。8 张过账单、四表 8 行；完整重放新增零张。默认 10 月样例继续适用原来的单据与来源格式。

## 旧版本回退演练

在本机保留 C0 合成容器和 20261104_155711 备份的条件下运行 `sh scripts/phase0-rehearse-rollback.sh <C0-backend容器名>`。候选与回退各用新项目、新卷和同一回环端口 18085。在候选副本恢复历史数据后，同步候选版本的中文打印模板，再验收七报表、十份 PDF。停用副本内的销售订单工作流并确认预检指出该流程，随即停止候选服务。旧版本从空卷恢复原有镜像、站点配置、数据库与文件；使用旧版格式核对 PDF，同时比较两代的库存、往来及总账。

Docker 标签被覆盖时，运行中的旧容器仍可显示原始索引摘要。先尝试从受控 OCI 归档加载。若本机保留相应 BuildKit 记录，使用 `scripts/phase0-recover-c0-image.py <build-ref> <仓库外的归档路径>`，它验证验收索引、目标平台清单、镜像配置及每个执行层，再保留可重新加载的 linux/arm64 OCI 包。归档构建证明附件有独立的留存周期，本轮记为缺失。正式候选需要同时归档执行镜像和构建证明。
