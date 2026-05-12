# 研究文档: 注册登录测试技术决策

> **版本**: `001-register-login`
> **创建日期**: 2026-05-12
> **来源**: /speckit-test.plan Phase 0 输出

---

## Decision 1: CSRF Token 在测试中的处理方式

**问题**: 规格要求CSRF Token校验（FR-010、FR-020）。如何在集成测试中处理CSRF Token？

- **Decision**: 集成测试从服务端获取有效CSRF Token后提交表单，验证完整防护链路。先GET登录/注册页获取CSRF Token，再在POST请求中携带该Token。
- **Rationale**: 如果mock CSRF校验中间件，则无法验证CSRF Token与请求的绑定关系是否正常工作；如果关闭CSRF仅用于测试，则完全遗漏该安全机制的验证。
- **Alternatives considered**: 
  - (a) mock CSRF中间件——跳过校验，但遗漏安全验证
  - (b) 关闭CSRF仅用于测试环境——生产与测试行为不一致

## Decision 2: JWT Cookie 在集成测试中的验证方式

**问题**: 集成测试如何验证HttpOnly、SameSite、过期时间等Cookie属性？

- **Decision**: 使用`httpx`的ASGI/WSGI测试客户端获取Set-Cookie响应头，解析完整的Cookie属性字符串。
- **Rationale**: `requests`库无法完整解析HttpOnly等安全属性的详细信息。`httpx`的测试客户端直接暴露底层响应头，可以断言`Set-Cookie`头中包含`HttpOnly`、`Secure`、`SameSite=Strict`等标记。
- **Alternatives considered**: 
  - (a) 使用普通HTTP客户端忽略Cookie属性——无法验证HttpOnly/SameSite
  - (b) 在浏览器环境中测试——属于E2E范围，不在集成测试中执行

## Decision 3: 连续失败锁定状态的隔离

**问题**: 锁定状态存储在Redis中。如何在测试中隔离锁定状态？

- **Decision**: 集成测试使用`fakeredis`完全隔离，每个测试从干净的Redis状态开始。E2E测试使用独立key前缀隔离。
- **Rationale**: 使用内存字典替代Redis与生产架构不一致；每个测试重启Redis实例过重。`fakeredis`提供完整的Redis协议模拟，支持所有命令。
- **Alternatives considered**: 
  - (a) 内存字典替代Redis——与生产不一致
  - (b) 每个测试重启Redis——过重，影响测试执行时间

## Decision 4: IP限速测试的地址模拟

**问题**: 限速基于客户端IP地址。如何在测试中模拟不同IP？

- **Decision**: 集成测试中通过在测试请求中携带伪造的`X-Forwarded-For`或`X-Real-IP`头来模拟不同IP。E2E测试中使用独立key前缀隔离。
- **Rationale**: 修改服务逻辑以支持测试注入IP侵入性过大；使用代理层修改IP需要额外的基础设施。HTTP头模拟是最轻量且与生产行为一致的方式。
- **Alternatives considered**: 
  - (a) 修改服务逻辑支持测试注入IP——侵入性大
  - (b) 代理层修改IP——需要额外基础设施

## Decision 5: Cookie过期测试的时间模拟

**问题**: Cookie过期涉及时间逻辑。如何在测试中验证过期行为？

- **Decision**: 集成测试使用`freezegun`冻结服务端时间来测试过期行为。E2E测试中设置极短过期时间(5秒)后等待过期。
- **Rationale**: 修改系统时钟影响其他进程；等待真实时间过期导致测试执行时间过长。`freezegun`可精确控制服务器端时间但不影响浏览器时钟。
- **Alternatives considered**: 
  - (a) 修改系统时钟——影响其他进程
  - (b) 等待真实时间过期——测试执行时间过长（30d/24h无法等待）

---

## 所有 NEEDS CLARIFICATION 解析状态

| 序号 | 未知项 | 解析状态 | 对应 Decision |
|------|--------|----------|---------------|
| 1 | CSRF Token 测试处理方式 | ✅ 已解析 | Decision 1 |
| 2 | JWT Cookie HttpOnly/属性验证 | ✅ 已解析 | Decision 2 |
| 3 | Redis 锁定状态隔离 | ✅ 已解析 | Decision 3 |
| 4 | IP 限速地址模拟 | ✅ 已解析 | Decision 4 |
| 5 | Cookie 过期时间模拟 | ✅ 已解析 | Decision 5 |

**状态**: 所有未知项已解析，Phase 0 完成。
