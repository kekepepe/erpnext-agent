# P0.9 技术验收记录

日期：2026-10-12。结论：R1-scope-v1.1 的 N1–N4 技术包完成；真实业务配置、员工 UAT 和生产发布尚未验收。所有业务演练仅使用 localhost:8080 的隔离合成公司，通过原生 REST/文档服务执行，无直接数据库访问。未提交、推送或部署到生产。

## 实现与证据

| 包 | 实际完成 | 验证结果与边界 |
|---|---|---|
| N1 / R1-01–05 | 合成单公司、两仓、CNY、科目/UOM/价格/信用/付款条件、非默认测试税模板；配置重放 | 四个原生草稿含税/未税均为净额100、测试税5、合计105；5%仅为合成算术测试。原始 P0 AR75/AP60、六组库存余额、十一张活动GL凭证保持 |
| N2 / R1-09–10 | 九身份、九原生Workflow、公司/仓库权限；独立 hardware_erp 0.1.0 文档事件守卫 | 24用例，21正向单据撤销保留审计、3负向草稿；完整扩展运行67检查通过，重复54检查通过且未创建新单据。重复复核负向/审计，不把已撤销正向单据再次提交 |
| N3 / R1-06–08、13、15 | 七原生报表职能权限；十类中文打印；CJK字体、内部资源URL、受限Origin代理；受控词库 | 七报表在对应职能运行，跨公司拒绝或无业务数据；十PDF/十页文本及原数据对照通过，所有页渲染检查通过；27页面×桌面1280×720/手机390×844截图逐页检查，最新控制台无error/warn |
| N4 / R1-10–11 | OPERATOR_SOP：采购/库存/销售/退货/应收应付、审批退回与撤销、对账关账、开票引用和恢复边界 | 原生API职能演练和流程回归通过；正式员工培训、实操与签字仍属A1 |

审批覆盖采购/销售10,000和10,000.01、收付款20,000和20,000.01，九类型正常分级、收货/开票/交货链及退货贷项、库存入库/调拨/盘点、逆序撤销。拒绝直接提交/撤销、自审批（包括临时双角色）、同请求改价审批、审批中编辑、撤销时改价、客户端save/flags绕过、换公司、越仓、价格维护、用户管理及删审计。信用限额1000的客户提交1000.01被原生信用检查拒绝。退回重填后经办改价再独立审批可行。原生Version/Comment/Permission Log未配置自动清理，新增盘点Version已验证。

批准范围依据 DEC-012 与 NATIVE_APPROVAL_GAP。守卫使用原生文档事件和Workflow，无新业务Core补丁、自定义业务表或外部端点；现有中文展示包三文件补丁仍按原批准范围保留。原生审批绕过的两轮失败证据保留在 n2-native-approval-20261011.json，不能称为通过。

## 实际命令及结果

以下命令在项目目录运行，均exit0；本地运行结果汇总见 phase0/evidence/p09-validation-20261012.json。

- `./scripts/phase0-start.sh`：最终镜像构建、安装/启动和健康检查通过；部署守卫/规则/代理文件哈希匹配仓库。
- `.venv/bin/python scripts/phase0-configure-access.py --apply`：最终角色名/审计配置后连续两次changed=[]；9角色/9Workflow。
- `.venv/bin/python scripts/phase0-configure-reports.py --apply`：最终连续两次report_configuration_changes=[]。
- `.venv/bin/python scripts/phase0-validate-release-access.py --exercise`：扩展67检查、重复54检查；正向取消历史复用。最终再次执行54检查通过、created=[]，复核最终配置及负向路径。
- `.venv/bin/python scripts/phase0-validate-output.py --output-dir /private/tmp/p09-output-final`：7报表、10PDF、10页通过；repeat及closeout独立导出也通过。
- `.venv/bin/python scripts/phase0-localize.py --verify`：受控UI词条及10原生HTML预览通过。
- `.venv/bin/python scripts/phase0-validate-{purchase,stock,sales,access,reporting,release,realtime}.py`：分别实际运行，每项两轮通过。大括号表示这七个独立命令的列表；不将未运行的额外测试算作通过。
- `.venv/bin/python -m unittest discover -s scripts -p 'test_*.py'`：21测试通过。
- `node scripts/test_phase0_form_display.js`：原生展示、货币/状态、原内容保留检查通过。
- `PYTHONPYCACHEPREFIX=/private/tmp/p09-pycache .venv/bin/python -m compileall -q scripts apps/hardware_erp apps/erpnext_zh`：通过。
- `git diff --check`：通过。

实时验证区分认证成功、未认证拒绝和foreign Origin403；未放开任意Origin。PDF经原生download_pdf产生，比较编号、中文名称、数量/单价/金额/币种及仓库，未代写或改造原交易。每次导出可能包含不同PDF元数据，重复比较以提取文本与业务检查为准。

## 界面与本地制品

最后截图为十详情、十R1公司过滤列表、七报表的54视口截图，路径 /private/tmp/p09-ui，检查记录 final-checks.json。原生 enable_onboarding=0 配置后重新进入页面并截图；旧带浮层截图已替换。27页桌面/窄屏汇总与10PDF渲染均已人工视觉检查。窄屏标题省略、原生表格横向滚动及保留的英文客户/供应商原数据是原生行为；不是全站零英语声明，也不是完整手机业务实操UAT。R1演练已全部逆向撤销，报表无活动业务数据符合预期；P0非零报表和库存/GL由原验证脚本另行核对。

PDF及截图只在本地临时目录保存：/private/tmp/p09-output-final、p09-output-repeat、p09-output-closeout 与 p09-ui；未将真实业务资料或凭证加入公开仓库。持久机器证据仅含合成编号、检查结果和哈希。

## 未完成的发布关卡

下一项是 P0.10/C0：独立全新站点安装、迁移/卸载/升级生命周期及可恢复验证，不能用本次既有站点安装代替。随后按 M1/A1 完成真实公司/会计/税务/员工映射、缺税/错误税适用性、折扣/退货税/关账期、迁移对账、完整备份恢复与版本回滚、各职能UAT和不可变RC批准。合成5%及审批阈值用例不构成真实税务政策或生产签核。
