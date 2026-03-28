# 发布后 30 分钟值班安排（2026-03-20）

## 一、目标

- 用于本次版本发布后 0-30 分钟重点观察。
- 明确谁负责看哪条链路，什么情况需要立即同步、止血或回滚。

## 二、建议值班时段

- 开始时间：__________
- 结束时间：__________
- 发布批次：2026-03-20
- 发布分支：`codex/release-hardening`

## 三、责任分工

### 研发

- 负责人：__________
- 负责链路：
  - 登录与鉴权
  - 学生首页与练习
  - 教师组卷与学情
  - 消息中心
- 重点接口：
  - `POST /api/question-bank/auth/login/password`
  - `GET /api/question-bank/student/dashboard`
  - `GET /api/question-bank/student/practice/questions`
  - `POST /api/question-bank/student/practice/questions/{id}/submit`
  - `GET /api/question-bank/papers/overview`
  - `POST /api/question-bank/papers/manual`
  - `POST /api/question-bank/papers/ai-generate`
  - `GET /api/question-bank/analytics/summary`
  - `GET /api/question-bank/analytics/records`
  - `POST /api/question-bank/messages/send`

### 运维

- 负责人：__________
- 负责内容：
  - 服务可用性
  - 资源使用情况
  - 网关 / 反向代理错误
  - 回滚窗口与备份确认

### 测试

- 负责人：__________
- 负责内容：
  - 复核登录、教师组卷、学生练习、消息中心人工关键路径
  - 记录首轮观察结论
  - 若发现阻断级问题，立即通知研发与运维

### 产品

- 负责人：__________
- 负责内容：
  - 确认是否满足业务验收口径
  - 决定是否进入正式对外发布

## 四、异常分级与动作

### 立即阻断

- 登录不可用
- 超管 / 教师 / 学生任一角色无法进入首页
- 学生练习无法拉题或无法提交
- 教师组卷列表报错或核心接口 5xx
- 数据库脚本执行异常且影响可用性

动作：
- 立即在群内同步
- 研发与运维共同判断是否止血 / 回滚

### 需 30 分钟内处理

- 局部页面报错但存在替代路径
- 学情列表 / 消息列表异常
- AI 任务有明显堆积但主流程仍可继续

动作：
- 记录问题
- 在观察窗口内确认影响范围
- 决定修复后继续观察还是带风险放行

## 五、首轮人工复核清单

- [ ] `/login` 登录成功且跳转正确
- [ ] `/admin/home`、`/teacher/home`、`/student/home` 均可访问
- [ ] 教师组卷页可打开列表与主要弹层
- [ ] 学生练习页可拉题、可提交
- [ ] 消息中心可查看未读消息
- [ ] 无大面积 401 / 403 / 5xx

## 六、观察记录

- 观察开始时间：__________
- 第 10 分钟结论：__________
- 第 20 分钟结论：__________
- 第 30 分钟结论：__________
- 是否触发告警：__________
- 是否需要止血 / 回滚：__________
- 最终放行结论：__________
