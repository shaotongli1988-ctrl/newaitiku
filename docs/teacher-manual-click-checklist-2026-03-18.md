# 教师端真实页面手工走查清单（2026-03-18）

## 1. 目标与范围
- 目标：按教师真实使用路径逐页“点点点”验收，覆盖主流程、负向校验、撤销恢复、角色隔离。
- 角色：`teacher`
- 建议账号：`teacher-001`
- 验收顺序：
1. 角色门户 `/`
2. 题库管理 `/teacher/questions`
3. 知识点三级树 `/teacher/knowledge`
4. 内容体系字典 `/teacher/content-system`
5. 试卷管理 `/teacher/papers`
6. 学情管理 `/teacher/analytics`
7. 消息中心 `/messages`

## 2. 执行前准备
- 基础地址：`http://127.0.0.1:8017`
- 浏览器：Chrome 或 Edge 最新稳定版
- 会话建议：先清空本地缓存与 Cookie，再以教师身份进入
- 记录规范：每步填写 `PASS` / `FAIL` / `BLOCKED`，并附截图或接口证据

## 3. 页面逐项点点点验收

### 3.1 角色门户 `/`
| 步骤ID | 点击/操作 | 预期结果 | 结果 | 证据 |
|---|---|---|---|---|
| T-PORTAL-01 | 打开 `/`（`?role=teacher&userId=teacher-001`） | 页面展示三角色卡片，教师卡片高亮 |  |  |
| T-PORTAL-02 | 点击教师卡片按钮 `data-role-entry="teacher"` | 跳转 `/teacher/questions?role=teacher&userId=teacher-001` |  |  |
| T-PORTAL-03 | 点击教师卡片“查看学情”链接 | 跳转 `/teacher/analytics?role=teacher&userId=teacher-001` |  |  |
| T-PORTAL-04 | 在 `#portal-switch-form` 将用户ID留空后提交 | 自动使用教师默认ID（`teacher-001`）并可正常跳转 |  |  |
| T-PORTAL-05 | 点击超管入口按钮 | 进入 `/login`（不应直接进超管控制台） |  |  |

### 3.2 题库管理 `/teacher/questions`
| 步骤ID | 点击/操作 | 预期结果 | 结果 | 证据 |
|---|---|---|---|---|
| T-Q-01 | 进入题库页，检查左侧菜单与顶部“角色门户/消息中心”链接 | 导航完整且当前菜单为“题库管理” |  |  |
| T-Q-02 | 点击 `#open-create-modal` | 打开“单题录入”弹窗，`#question-modal` 可见 |  |  |
| T-Q-03 | 弹窗内必填项留空直接保存 | 页面消息提示必填校验失败，不应提交成功 |  |  |
| T-Q-04 | 客观题（单选/多选）将 `optionsJson` 置空数组后保存 | 拒绝提交并提示“客观题 optionsJson 必须非空数组” |  |  |
| T-Q-05 | `extJson.difficulty` 填写非法值（如 `normal`）保存 | 拒绝提交并提示仅支持 `easy/medium/hard` |  |  |
| T-Q-06 | `extJson.knowledgeTags` 填 0 个或超过 3 个保存 | 拒绝提交并提示标签必须 1-3 个 |  |  |
| T-Q-07 | 点击 `#format-optionsJson`、`#format-extJson` | JSON 被格式化；非法 JSON 时有错误提示 |  |  |
| T-Q-08 | 正常新建 1 题并保存 | 提示“题目已创建”，列表出现新题 |  |  |
| T-Q-09 | 列表点击“详情” | 打开详情弹窗，展示固定字段、扩展摘要、审核轨迹区域 |  |  |
| T-Q-10 | 详情页执行可用快捷流转（如提交待审核/终审发布） | 状态更新成功，列表状态同步刷新 |  |  |
| T-Q-11 | 勾选多题后观察 `#batch-transition/#batch-delete` | 按钮由禁用变可用；`#selected-question-count` 数量正确 |  |  |
| T-Q-12 | 批量目标状态选 `REJECTED` 且不填 `#batch-reason` 后流转 | 拒绝并提示驳回原因必填 |  |  |
| T-Q-13 | 批量删除后点击 `#undo-question-delete` | 删除可恢复，列表恢复题目 |  |  |
| T-Q-14 | 单题删除后点击 `#undo-question-delete` | 单题删除可恢复 |  |  |
| T-Q-15 | 左侧知识树点击任一节点 | 自动带入筛选 `#filter-knowledgeId`、导入 `#import-knowledge-id`、表单 `#field-knowledgeId` |  |  |
| T-Q-16 | 导入区上传非法文件类型（如 `.pdf`）并预览/导入 | 拒绝并提示仅支持 `txt/docx` |  |  |
| T-Q-17 | 点击 `#preview-import` 打开预览后取消全选再确认导入 | 无勾选时不允许确认导入；勾选后可按数量导入 |  |  |
| T-Q-18 | 导入产生错误后点击 `#download-import-errors` | 可下载失败日志；无错误时按钮禁用/提示不可下载 |  |  |

### 3.3 知识点三级树 `/teacher/knowledge`
| 步骤ID | 点击/操作 | 预期结果 | 结果 | 证据 |
|---|---|---|---|---|
| T-K-01 | 打开页面并提交 `#knowledge-filter-form` | 树、详情区、子节点区正常加载 |  |  |
| T-K-02 | 在 `#knowledge-search-keyword` 输入关键词 | 树实时过滤，不匹配时显示空态提示 |  |  |
| T-K-03 | 点击 `#knowledge-expand-all`、`#knowledge-collapse-all` | 树全展开/全折叠生效 |  |  |
| T-K-04 | 树节点点击“新增子节点”并保存 `#knowledge-form` | 成功创建子节点并刷新树 |  |  |
| T-K-05 | 点击节点“上移/下移” | 排序值或展示顺序变化并刷新 |  |  |
| T-K-06 | 点击节点“删除”后再点 `#knowledge-undo-delete-button` | 节点删除可撤销恢复 |  |  |
| T-K-07 | 点击 `#knowledge-reset-button` | 表单重置为默认值（含 `status=ENABLED`、`extJson={}`） |  |  |

### 3.4 内容体系字典 `/teacher/content-system`
| 步骤ID | 点击/操作 | 预期结果 | 结果 | 证据 |
|---|---|---|---|---|
| T-C-01 | 打开页面 | 展示政策版本、报考大类数、联考组数摘要卡 |  |  |
| T-C-02 | 滚动 `#content-category-list` | 大类 -> 联考组 -> 科目层级展示完整，题目数量可见 |  |  |
| T-C-03 | 使用 `#content-auth-form` 切换用户ID | 页面按新 userId 刷新，数据加载正常 |  |  |
| T-C-04 | 检查页面交互边界 | 该页为字典浏览基线，不应出现题目/试卷编辑提交按钮 |  |  |

### 3.5 试卷管理 `/teacher/papers`
| 步骤ID | 点击/操作 | 预期结果 | 结果 | 证据 |
|---|---|---|---|---|
| T-P-01 | 打开页面 | 手动组卷、自动组卷、模板、题池、试卷列表均可见 |  |  |
| T-P-02 | 在题池使用筛选表单 `#paper-source-filter-form` 后查询 | 列表与分页 `#paper-source-page-indicator` 正确更新 |  |  |
| T-P-03 | 点击 `#paper-select-page`、`#paper-clear-selection` | 勾选数量 `#paper-selected-count` 正确变化 |  |  |
| T-P-04 | 点击 `#paper-apply-selection` | 勾选题目写入手动组卷 `questionIds` 文本框 |  |  |
| T-P-05 | 手动组卷不填题目ID提交 | 拒绝并提示至少 1 个题目ID |  |  |
| T-P-06 | 完整填写手动组卷后提交 | 提示“手动试卷已生成”，试卷列表刷新 |  |  |
| T-P-07 | 自动组卷 `typeRules` 填非法 JSON 提交 | 提交失败并有错误提示 |  |  |
| T-P-08 | 自动组卷填写合法 `typeRules` 提交 | 提示“自动试卷已生成”，列表刷新 |  |  |
| T-P-09 | 新建模板并在模板列表点击“应用模板” | 自动组卷表单被模板字段回填 |  |  |
| T-P-10 | 删除模板后点击 `#paper-template-undo-delete-button` | 模板可恢复 |  |  |
| T-P-11 | 在试卷列表执行状态动作（提交待审核/发布/退回/下架） | 操作弹窗确认后成功，状态实时变化 |  |  |
| T-P-12 | 点击试卷“导出文档” | `#paper-export-content` 出现导出内容 |  |  |
| T-P-13 | 删除试卷后点击 `#paper-undo-delete-button` | 试卷可恢复 |  |  |

### 3.6 学情管理 `/teacher/analytics`
| 步骤ID | 点击/操作 | 预期结果 | 结果 | 证据 |
|---|---|---|---|---|
| T-A-01 | 打开页面并点击“刷新学情” | 摘要卡、排行、薄弱点、AI报告均刷新 |  |  |
| T-A-02 | 设置筛选（科目/章节/学生/日期）后刷新 | 统计结果按筛选条件变化 |  |  |
| T-A-03 | 检查“刷题明细”表格列 | 包含学生ID、科目ID、章节、题型、是否正确、耗时、提交时间、题干 |  |  |
| T-A-04 | 点击 `#analytics-prev-page/#analytics-next-page` | 分页状态与页码提示更新正确 |  |  |
| T-A-05 | 导出格式切换 CSV/PDF 后点 `#analytics-export-button` | `#analytics-export-content` 输出对应导出内容，提示成功 |  |  |

### 3.7 消息中心 `/messages`
| 步骤ID | 点击/操作 | 预期结果 | 结果 | 证据 |
|---|---|---|---|---|
| T-M-01 | 以教师身份打开消息中心 | 显示消息设置、发送提醒、消息列表、发送历史四块 |  |  |
| T-M-02 | 在“消息设置”卡片调整开关并保存 | 提示“消息设置已更新” |  |  |
| T-M-03 | 发送方式从“按用户ID发送”切到“按分群发送” | 用户ID输入框禁用；分群字段可编辑 |  |  |
| T-M-04 | 发送方式切回“按用户ID发送” | 用户ID可编辑；分群字段禁用 |  |  |
| T-M-05 | 选择快捷模板（学习提醒/周报/系统公告） | 分类、标题、内容自动回填 |  |  |
| T-M-06 | 发送即时消息（不填 `sendAt`） | 提示“消息已发送”，消息列表与发送历史刷新 |  |  |
| T-M-07 | 发送定时消息（填写 `sendAt`） | 发送历史可看到 `sendAt` 值 |  |  |
| T-M-08 | 消息列表勾选多条后点击“批量标记已读” | 批量已读成功，勾选计数归零 |  |  |
| T-M-09 | 单条点击“标记已读” | 该消息状态更新为已读 |  |  |
| T-M-10 | 发送历史点击“撤回发送” | 记录状态变为 `RECALLED`，按钮变“已撤回” |  |  |
| T-M-11 | 操作历史分页按钮 | 发送历史页码与上下页禁用状态正确 |  |  |

## 4. 角色隔离与越权走查（教师视角必测）
| 步骤ID | 点击/操作 | 预期结果 | 结果 | 证据 |
|---|---|---|---|---|
| T-RBAC-01 | 直接访问 `/admin/control-center?role=teacher&userId=teacher-001` | 被拒绝（403或错误提示），不可进入超管页面 |  |  |
| T-RBAC-02 | 直接访问 `/student/home?role=teacher&userId=teacher-001` | 被拒绝（403或错误提示），不可进入学生学习台 |  |  |
| T-RBAC-03 | 教师菜单中检查是否出现超管菜单项 | 不应出现“超管控制台/系统治理”等超管入口 |  |  |
| T-RBAC-04 | 打开 `/messages?role=student&userId=student-001` 对比 | 学生视角不显示“发送提醒”与“发送历史”卡片 |  |  |

## 5. 缺陷记录模板
| 缺陷ID | 关联步骤ID | 页面URL | 实际结果 | 期望结果 | 严重级别(P0-P3) | 附件 |
|---|---|---|---|---|---|---|
| BUG-001 |  |  |  |  |  |  |
| BUG-002 |  |  |  |  |  |  |

## 6. 本轮结论
- 通过数：
- 失败数：
- 阻塞数：
- 是否允许进入下一轮：`是 / 否`
