# RTOS Thread Join Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement RT-Thread `ep_thread_join()` so EP code can wait for a thread to return naturally.

**Architecture:** Keep the public OSAL API unchanged. The RT-Thread port creates an internal completion semaphore per EP thread, releases it from the trampoline after the user entry returns, and lets `ep_thread_join()` wait on it before freeing the EP handle. This does not add a force-stop API and does not call `rt_thread_delete()` on running threads.

**Tech Stack:** C11, RT-Thread kernel API, pytest compile-and-run smoke tests, repository docs under `docs/porting`.

---

### Task 1: RT-Thread Join Behavior

**Files:**
- Create: `tests/host_unit/test_rtthread_osal_thread.py`
- Modify: `platforms/rtos/demo_family/osal_port/ep_rtos_osal_rtthread.c`

- [ ] **Step 1: Write the failing test**

Create `tests/host_unit/test_rtthread_osal_thread.py` with a fake `rtthread.h` and fake RT-Thread runtime. The smoke program should:

- reject invalid `ep_thread_create()` arguments
- reject `ep_thread_join(NULL)`
- create one thread
- verify `rt_thread_create()` receives stack size `4096`, priority `20`, tick `10`
- verify startup runs the trampoline
- verify `ep_thread_join()` returns `EP_OK`
- verify the worker entry ran
- verify the internal completion semaphore was taken and deleted
- verify the EP thread handle memory was freed

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m pytest tests/host_unit/test_rtthread_osal_thread.py -q
```

Expected result before implementation:

```text
FAILED ... expected join to return EP_OK
```

or an equivalent failure showing current `ep_thread_join()` returns `EP_ERR_UNSUPPORTED`.

- [ ] **Step 3: Implement RT-Thread join**

Modify `platforms/rtos/demo_family/osal_port/ep_rtos_osal_rtthread.c`:

- add `rt_sem_t done;` to `struct ep_thread`
- create `done` with `rt_sem_create("epj", 0, RT_IPC_FLAG_FIFO)` before `rt_thread_create()`
- on `rt_thread_create()` or `rt_thread_startup()` failure, delete `done` before freeing the EP handle
- release `done` at the end of `ep_thread_trampoline()`
- implement `ep_thread_join()` as `rt_sem_take(done, RT_WAITING_FOREVER)`, then `rt_sem_delete(done)`, then `ep_free(thread)`
- return `EP_ERR_INVAL` for null thread, mapped RT error otherwise

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
python3 -m pytest tests/host_unit/test_rtthread_osal_thread.py -q
```

Expected result:

```text
1 passed
```

### Task 2: Documentation And Regression

**Files:**
- Modify: `docs/porting/osal-api-reference.md`

- [ ] **Step 1: Update OSAL documentation**

Update `ep_thread_join()` documentation so it says:

- `EP_OK`: thread exited naturally, resources released
- `EP_ERR_INVAL`: null or invalid handle
- `EP_ERR_UNSUPPORTED`: underlying wait failed
- RT-Thread join waits for the EP trampoline completion semaphore
- no force-stop API exists; callers should signal their worker to exit before joining
- current RT-Thread OSAL status marks thread join as implemented

- [ ] **Step 2: Run focused checks**

Run:

```bash
python3 -m pytest tests/host_unit/test_rtthread_osal_thread.py tests/api_contract/test_osal_headers.py -q
git diff --check
```

Expected result:

```text
tests pass, git diff --check has no output
```

### Task 3: PR Verification

**Files:**
- No new files beyond Task 1 and Task 2.

- [ ] **Step 1: Run broader host checks**

Run:

```bash
python3 -m pytest tests/host_unit tests/api_contract -q
cmake -S . -B build && cmake --build build
./build.sh validate-targets
```

Expected result:

```text
pytest passes, CMake build succeeds, target 校验通过：6
```

- [ ] **Step 2: Commit and open PR**

Use a Chinese commit and PR:

```bash
git add tests/host_unit/test_rtthread_osal_thread.py platforms/rtos/demo_family/osal_port/ep_rtos_osal_rtthread.c docs/porting/osal-api-reference.md docs/superpowers/plans/2026-06-05-rtos-thread-join.md
git commit -m "feat: 实现 RT-Thread 线程 join"
git push -u origin feature/rtos-thread-join
gh pr create --base main --head feature/rtos-thread-join --title "feat: 实现 RT-Thread 线程 join" --body "<Chinese PR body with verification>"
```
