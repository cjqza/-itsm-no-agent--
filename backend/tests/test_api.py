"""
公司桌面IT服务台 - API自动化测试脚本

使用方法:
    cd backend
    python tests/test_api.py

测试内容:
    1. 认证登录
    2. 权限管理
    3. ITSM工单全生命周期
    4. OPS统计
    5. 后台分类CRUD
    6. 飞书机器人回调模拟
"""
import httpx
import json
import sys
import time
from datetime import datetime

BASE_URL = "http://localhost:8000"
API = f"{BASE_URL}/api"
TIMEOUT = 10.0

passed = 0
failed = 0
errors = []


def log(tag, msg, ok=True):
    global passed, failed
    sym = "PASS" if ok else "FAIL"
    line = f"  [{sym}] [{tag}] {msg}"
    try:
        print(line, flush=True)
    except UnicodeEncodeError:
        print(line.encode("utf-8", errors="replace").decode("utf-8"), flush=True)
    if ok:
        passed += 1
    else:
        failed += 1
        errors.append(f"[{tag}] {msg}")


def section(title):
    try:
        print(f"\n{'='*60}\n  {title}\n{'='*60}", flush=True)
    except UnicodeEncodeError:
        print(f"\n{'='*60}\n  {title.encode('utf-8',errors='replace').decode()}\n{'='*60}", flush=True)


def post(path, data=None, token=None):
    h = {}
    if token:
        h["Authorization"] = f"Bearer {token}"
    r = httpx.post(f"{API}{path}", json=data, headers=h, timeout=TIMEOUT)
    return {"status": r.status_code, "data": r.json()}


def get(path, token=None, params=None):
    h = {}
    if token:
        h["Authorization"] = f"Bearer {token}"
    r = httpx.get(f"{API}{path}", headers=h, params=params, timeout=TIMEOUT)
    return {"status": r.status_code, "data": r.json()}


def put(path, data=None, token=None, params=None):
    h = {}
    if token:
        h["Authorization"] = f"Bearer {token}"
    r = httpx.put(f"{API}{path}", json=data, headers=h, params=params, timeout=TIMEOUT)
    return {"status": r.status_code, "data": r.json()}


def delete(path, token=None):
    h = {}
    if token:
        h["Authorization"] = f"Bearer {token}"
    r = httpx.delete(f"{API}{path}", headers=h, timeout=TIMEOUT)
    return {"status": r.status_code, "data": r.json()}


# ========== 1. Auth ==========
def test_auth():
    section("1. Auth Test")

    r = post("/auth/login", {"account": "admin", "password": "admin123"})
    ok = r["status"] == 200 and "token" in r["data"]
    log("Auth", f"Admin login (login_id) [{r['status']}]", ok)
    admin_token = r["data"].get("token", "")

    r = post("/auth/login", {"account": "13900000001", "password": "123456"})
    log("Auth", f"Agent login (phone) [{r['status']}]", r["status"] == 200)
    agent_token = r["data"].get("token", "")

    r = post("/auth/login", {"account": "U00006", "password": "123456"})
    log("Auth", f"User login (login_id) [{r['status']}]", r["status"] == 200)
    user_token = r["data"].get("token", "")

    r = post("/auth/login", {"account": "admin", "password": "wrongpass"})
    log("Auth", f"Wrong password rejected [{r['status']}]", r["status"] == 401)

    r = post("/auth/login", {"account": "no_such_account_xyz", "password": "x"})
    log("Auth", f"Unknown account rejected [{r['status']}]", r["status"] == 401)

    r = get("/auth/me", token=admin_token)
    log("Auth", f"Get me [{r['status']}]", r["status"] == 200)

    r = get("/auth/me", token="bad_token")
    log("Auth", f"Bad token rejected [{r['status']}]", r["status"] == 401)

    return admin_token, agent_token, user_token


# ========== 2. Permissions ==========
def test_permissions(admin_t, user_t):
    section("2. Permission Test")

    # 获取当前用户ID
    r = get("/auth/me", token=user_t)
    user_id = r["data"].get("id") if r["status"] == 200 else None

    # 先撤销用户权限确保测试环境干净
    if user_id:
        r = httpx.put(
            f"{API}/admin/permissions/{user_id}",
            headers={"Authorization": f"Bearer {admin_t}"},
            params={"itsm_access": "false", "ops_access": "false", "admin_access": "false"},
            timeout=TIMEOUT,
        )
        log("Perm", f"Revoke user perm [{r.status_code}]", r.status_code == 200)

    r = get("/itsm/dashboard", token=user_t)
    log("Perm", f"No-perm user blocked [{r['status']}]", r["status"] == 403)

    r = post("/admin/permission-requests?request_type=itsm&reason=test", token=user_t)
    log("Perm", f"Submit request [{r['status']}]", r["status"] == 200)

    r = get("/admin/permission-requests?status=pending", token=admin_t)
    log("Perm", f"List requests [{r['status']}]", r["status"] == 200)
    rid = None
    if r["status"] == 200 and isinstance(r["data"], list) and len(r["data"]) > 0:
        rid = r["data"][0]["id"]

    if rid:
        r = put(f"/admin/permission-requests/{rid}", token=admin_t, params={"action": "approved"})
        log("Perm", f"Approve request [{r['status']}]", r["status"] == 200)

    r = get("/itsm/dashboard", token=user_t)
    log("Perm", f"User now has access [{r['status']}]", r["status"] == 200)

    r = get("/admin/permissions", token=admin_t)
    log("Perm", f"List permissions [{r['status']}]", r["status"] == 200)


# ========== 3. Admin CRUD ==========
def test_admin_crud(admin_t):
    section("3. Admin CRUD Test")

    cat_id = None

    r = post("/admin/categories/", data={
        "name": f"TestCat_{int(time.time())}",
        "description": "auto test",
        "sla_hours": 6,
    }, token=admin_t)
    log("CRUD", f"Create category [{r['status']}]", r["status"] == 200)
    cat_id = r["data"].get("id")

    r = get("/admin/categories/", token=admin_t)
    log("CRUD", f"List categories [{r['status']}]", r["status"] == 200)

    if cat_id:
        r = put(f"/admin/categories/{cat_id}", data={"description": "updated"}, token=admin_t)
        log("CRUD", f"Update category [{r['status']}]", r["status"] == 200)

    r = post("/admin/properties/", data={"name": f"TestProp_{int(time.time())}"}, token=admin_t)
    log("CRUD", f"Create property [{r['status']}]", r["status"] == 200)

    r = post("/admin/symptoms/", data={"name": f"TestSymp_{int(time.time())}"}, token=admin_t)
    log("CRUD", f"Create symptom [{r['status']}]", r["status"] == 200)

    r = post("/admin/causes/", data={"name": f"TestCause_{int(time.time())}"}, token=admin_t)
    log("CRUD", f"Create cause [{r['status']}]", r["status"] == 200)

    r = post("/admin/solutions/", data={"name": f"TestSol_{int(time.time())}"}, token=admin_t)
    log("CRUD", f"Create solution [{r['status']}]", r["status"] == 200)

    if cat_id:
        r = delete(f"/admin/categories/{cat_id}", token=admin_t)
        log("CRUD", f"Delete category [{r['status']}]", r["status"] == 200)


# ========== 4. ITSM Lifecycle ==========
def test_ticket_lifecycle(admin_t, agent_t):
    section("4. ITSM Ticket Lifecycle Test")

    r = get("/itsm/dashboard", token=admin_t)
    log("ITSM", f"Dashboard [{r['status']}]", r["status"] == 200)

    r = post("/itsm/tickets", data={
        "title": "PC blue screen",
        "description": "error 0x0000007B",
        "priority": "P2",
        "creator_id": 1,
    }, token=admin_t)
    ok = r["status"] == 200 and "ticket_no" in r["data"]
    log("ITSM", f"Create ticket [{r['status']}]", ok)
    tid = r["data"].get("id")

    if not tid:
        log("ITSM", "Skip lifecycle (no ticket)", False)
        return

    r = get(f"/itsm/tickets/{tid}", token=admin_t)
    log("ITSM", f"Get detail [{r['status']}]", r["status"] == 200)

    r = get("/itsm/tickets", token=admin_t, params={"status": "assigned"})
    log("ITSM", f"Filter by status [{r['status']}]", r["status"] == 200)

    r = get("/itsm/tickets/search", token=admin_t, params={"keyword": "blue"})
    log("ITSM", f"Search tickets [{r['status']}]", r["status"] == 200)

    r = put(f"/itsm/tickets/{tid}", data={"title": "PC blue screen (updated)"}, token=admin_t)
    log("ITSM", f"Update ticket [{r['status']}]", r["status"] == 200)

    # 状态流转: accepted -> processing -> resolved_pending_review
    for status in ["accepted", "processing", "resolved_pending_review"]:
        r = put(f"/itsm/tickets/{tid}/status", data={"status": status}, token=admin_t)
        log("ITSM", f"Status -> {status} [{r['status']}]", r["status"] == 200)

    r = put(f"/itsm/tickets/{tid}/remark", data={"remark": "user offline", "pause_ola": True}, token=admin_t)
    log("ITSM", f"Add remark [{r['status']}]", r["status"] == 200)

    r = put(f"/itsm/tickets/{tid}/pause-sla", token=admin_t, params={"reason": "wait"})
    log("ITSM", f"Pause SLA [{r['status']}]", r["status"] == 200)

    r = put(f"/itsm/tickets/{tid}/resume-sla", token=admin_t)
    log("ITSM", f"Resume SLA [{r['status']}]", r["status"] == 200)

    r = put(f"/itsm/tickets/{tid}/transfer", data={"assignee_id": 3, "reason": "专业对口"}, token=admin_t)
    log("ITSM", f"Transfer [{r['status']}]", r["status"] == 200)

    r = put(f"/itsm/tickets/{tid}/rate", data={"rating": 5, "rating_comment": "good"}, token=admin_t)
    log("ITSM", f"Rate ticket [{r['status']}]", r["status"] == 200 and r["data"].get("rating") == 5)

    r = get(f"/itsm/tickets/{tid}/logs", token=admin_t)
    log("ITSM", f"Get logs [{r['status']}]", r["status"] == 200 and len(r["data"]) > 0)


# ========== 5. OPS ==========
def test_ops(admin_t):
    section("5. OPS Statistics Test")

    r = get("/ops/statistics/overview", token=admin_t, params={"days": 30})
    log("OPS", f"Overview [{r['status']}]", r["status"] == 200)

    r = get("/ops/statistics/by-category", token=admin_t, params={"days": 30})
    log("OPS", f"By category [{r['status']}]", r["status"] == 200)

    r = get("/ops/statistics/by-agent", token=admin_t, params={"days": 30})
    log("OPS", f"By agent [{r['status']}]", r["status"] == 200)

    r = get("/ops/statistics/ratings", token=admin_t, params={"days": 30})
    log("OPS", f"Ratings [{r['status']}]", r["status"] == 200)

    r = get("/ops/statistics/sla-compliance", token=admin_t, params={"days": 30})
    log("OPS", f"SLA compliance [{r['status']}]", r["status"] == 200)

    r = get("/ops/statistics/trend", token=admin_t, params={"days": 30})
    log("OPS", f"Trend [{r['status']}]", r["status"] == 200)

    r = httpx.get(f"{API}/ops/export", params={"days": 30},
                  headers={"Authorization": f"Bearer {admin_t}"}, timeout=TIMEOUT)
    log("OPS", f"Export [{r.status_code}]", r.status_code == 200)


# ========== 6. New Features Test ==========
def test_new_features(admin_t, agent_t):
    section("6. New Features Test")

    # 创建测试工单
    r = post("/itsm/tickets", data={
        "title": "Test ticket for new features",
        "description": "Testing new APIs",
        "priority": "P3",
    }, token=admin_t)
    tid = r["data"].get("id") if r["status"] == 200 else None

    if tid:
        # 接单
        r = put(f"/itsm/tickets/{tid}/accept", token=admin_t)
        log("New", f"Accept ticket [{r['status']}]", r["status"] == 200)

        # 转派
        r = put(f"/itsm/tickets/{tid}/transfer", data={"assignee_id": 3, "reason": "test"}, token=admin_t)
        log("New", f"Transfer ticket [{r['status']}]", r["status"] == 200)

    # 快捷回复模板
    r = get("/templates", token=admin_t)
    log("New", f"List templates [{r['status']}]", r["status"] == 200)

    r = post("/templates", data={"title": "Test", "content": "Hello {user}", "category": "test"}, token=admin_t)
    log("New", f"Create template [{r['status']}]", r["status"] == 200)

    # 用户管理
    r = get("/admin/users", token=admin_t)
    log("New", f"List users [{r['status']}]", r["status"] == 200)

    # SLA预警
    r = get("/itsm/tickets/sla-warnings", token=admin_t)
    log("New", f"SLA warnings [{r['status']}]", r["status"] == 200)


# ========== 7. Edge Cases ==========
def test_edge(admin_t):
    section("7. Edge Case Test")

    r = get("/itsm/tickets/99999", token=admin_t)
    log("Edge", f"Not found ticket [{r['status']}]", r["status"] == 404)

    r = get("/itsm/dashboard")
    log("Edge", f"No token [{r['status']}]", r["status"] == 403)

    r = put("/itsm/tickets/1/rate", data={"rating": 10}, token=admin_t)
    log("Edge", f"Invalid rating [{r['status']}]", r["status"] in [400, 422])


# ========== 8. Account Register & Approval ==========
def test_account_flow(admin_t):
    section("8. Account Register & Approval Test")

    phone = f"137{int(time.time()) % 100000000:08d}"
    pwd = "reg123456"

    # 注册申请
    r = post("/auth/register", {"name": "申请用户", "phone": phone, "password": pwd})
    log("Acct", f"Register [{r['status']}]", r["status"] == 200 and r["data"].get("success"))
    new_uid = r["data"].get("user_id")

    # 重复电话 -> 400
    r = post("/auth/register", {"name": "重复用户", "phone": phone, "password": pwd})
    log("Acct", f"Duplicate phone rejected [{r['status']}]", r["status"] == 400)

    # 非法电话 -> 422 (Field 校验)
    r = post("/auth/register", {"name": "x", "phone": "!!", "password": pwd})
    log("Acct", f"Invalid phone rejected [{r['status']}]", r["status"] == 422)

    # 未审批不能登录 -> 401
    r = post("/auth/login", {"account": phone, "password": pwd})
    log("Acct", f"Pending account cannot login [{r['status']}]", r["status"] == 401)

    # 列出待审批
    r = get("/admin/account-requests", token=admin_t, params={"status": "pending"})
    ok = r["status"] == 200 and isinstance(r["data"], list) and any(u["id"] == new_uid for u in r["data"])
    log("Acct", f"List pending requests [{r['status']}]", ok)

    # 审批通过
    login_id = None
    if new_uid:
        r = put(f"/admin/account-requests/{new_uid}", token=admin_t, params={"action": "approve"})
        ok = r["status"] == 200 and r["data"].get("login_id", "").startswith("U")
        login_id = r["data"].get("login_id")
        log("Acct", f"Approve request [{r['status']}] login_id={login_id}", ok)

    # 审批后可用电话登录
    r = post("/auth/login", {"account": phone, "password": pwd})
    log("Acct", f"Approved account can login (phone) [{r['status']}]", r["status"] == 200)

    # 也可用分配的专属ID登录
    if login_id:
        r = post("/auth/login", {"account": login_id, "password": pwd})
        log("Acct", f"Approved account can login (login_id) [{r['status']}]", r["status"] == 200)

    # 重复审批已激活账号 -> 400
    if new_uid:
        r = put(f"/admin/account-requests/{new_uid}", token=admin_t, params={"action": "approve"})
        log("Acct", f"Re-approve active account rejected [{r['status']}]", r["status"] == 400)

    # 拒绝流程：再注册一个并 reject
    phone2 = f"136{int(time.time()) % 100000000:08d}"
    r = post("/auth/register", {"name": "待拒绝", "phone": phone2, "password": pwd})
    uid2 = r["data"].get("user_id")
    if uid2:
        r = put(f"/admin/account-requests/{uid2}", token=admin_t, params={"action": "reject"})
        log("Acct", f"Reject request [{r['status']}]", r["status"] == 200)
        r = post("/auth/login", {"account": phone2, "password": pwd})
        log("Acct", f"Rejected account cannot login [{r['status']}]", r["status"] == 401)


# ========== 9. admin_access Permission Rule ==========
def test_admin_access_rule(admin_t):
    section("9. admin_access Permission Rule Test")

    # 造一个拥有 admin_access 但非 super_admin 的账号
    phone = f"135{int(time.time()) % 100000000:08d}"
    pwd = "adm123456"
    r = post("/auth/register", {"name": "后台账号", "phone": phone, "password": pwd})
    uid = r["data"].get("user_id")
    if uid:
        put(f"/admin/account-requests/{uid}", token=admin_t, params={"action": "approve"})
        # super_admin 授予其 admin_access（允许）
        r = httpx.put(
            f"{API}/admin/permissions/{uid}",
            headers={"Authorization": f"Bearer {admin_t}"},
            params={"admin_access": "true"},
            timeout=TIMEOUT,
        )
        log("AdmRule", f"Super admin grants admin_access [{r.status_code}]", r.status_code == 200)

    # 该账号登录
    r = post("/auth/login", {"account": phone, "password": pwd})
    sub_admin_t = r["data"].get("token", "") if r["status"] == 200 else ""

    # 造一个目标普通用户
    phone_t = f"134{int(time.time()) % 100000000:08d}"
    r = post("/auth/register", {"name": "目标用户", "phone": phone_t, "password": pwd})
    tgt = r["data"].get("user_id")
    if tgt:
        put(f"/admin/account-requests/{tgt}", token=admin_t, params={"action": "approve"})

    if sub_admin_t and tgt:
        # 非 super_admin 改 itsm_access -> 允许
        r = httpx.put(
            f"{API}/admin/permissions/{tgt}",
            headers={"Authorization": f"Bearer {sub_admin_t}"},
            params={"itsm_access": "true"},
            timeout=TIMEOUT,
        )
        log("AdmRule", f"Non-super changes itsm_access allowed [{r.status_code}]", r.status_code == 200)

        # 非 super_admin 改 admin_access -> 403
        r = httpx.put(
            f"{API}/admin/permissions/{tgt}",
            headers={"Authorization": f"Bearer {sub_admin_t}"},
            params={"admin_access": "true"},
            timeout=TIMEOUT,
        )
        log("AdmRule", f"Non-super changes admin_access blocked [{r.status_code}]", r.status_code == 403)


# ========== Main ==========
def main():
    try:
        print(f"\n{'#'*60}", flush=True)
        print(f"  IT Ops System - API Test", flush=True)
        print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
        print(f"  Target: {BASE_URL}", flush=True)
        print(f"{'#'*60}", flush=True)
    except:
        pass

    try:
        r = httpx.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        if r.status_code != 200:
            print("Backend not ready!", flush=True)
            sys.exit(1)
    except Exception as e:
        print(f"Cannot connect: {e}", flush=True)
        sys.exit(1)

    t0 = time.time()

    admin_t, agent_t, user_t = test_auth()
    test_permissions(admin_t, user_t)
    test_admin_crud(admin_t)
    test_ticket_lifecycle(admin_t, agent_t)
    test_ops(admin_t)
    test_new_features(admin_t, agent_t)
    test_edge(admin_t)
    test_account_flow(admin_t)
    test_admin_access_rule(admin_t)

    elapsed = round(time.time() - t0, 2)
    total = passed + failed

    try:
        print(f"\n{'='*60}", flush=True)
        print(f"  Result: {passed}/{total} passed, {failed} failed, {elapsed}s", flush=True)
        print(f"  Pass rate: {round(passed/total*100, 1) if total else 0}%", flush=True)
    except:
        print(f"\n  Result: {passed}/{total} passed, {failed} failed, {elapsed}s", flush=True)

    if errors:
        print(f"\n  Failed:", flush=True)
        for e in errors:
            try:
                print(f"    - {e}", flush=True)
            except:
                pass

    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
