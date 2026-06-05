import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_rtthread_osal_semaphore_maps_to_rt_sem_api(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "rtthread_osal_sem_smoke.c"
    executable = tmp_path / "rtthread_osal_sem_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_osal_err.h"
            #include "ep_osal_sem.h"

            int main(void)
            {
                ep_sem_t *sem = 0;

                if (ep_sem_create(0, 1) == EP_OK) {
                    return 1;
                }

                if (ep_sem_wait(0, 0) == EP_OK) {
                    return 2;
                }

                if (ep_sem_post(0) == EP_OK) {
                    return 3;
                }

                sem = (ep_sem_t *)1;
                if (ep_sem_create(&sem, 0xFFFFFFFFu) == EP_OK) {
                    return 10;
                }

                if (sem != 0) {
                    return 11;
                }

                if (ep_sem_create(&sem, 1) != EP_OK) {
                    return 4;
                }

                if (ep_sem_wait(sem, 0) != EP_OK) {
                    return 5;
                }

                if (ep_sem_wait(sem, 0) != EP_ERR_TIMEOUT) {
                    return 6;
                }

                if (ep_sem_wait(sem, 5) != EP_ERR_TIMEOUT) {
                    return 7;
                }

                if (ep_sem_post(sem) != EP_OK) {
                    return 8;
                }

                if (ep_sem_wait(sem, 0) != EP_OK) {
                    return 9;
                }

                return 0;
            }
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    rtthread_include = tmp_path / "rtthread.h"
    rtthread_include.write_text(
        textwrap.dedent(
            """
            #ifndef RTTHREAD_H
            #define RTTHREAD_H

            #include <stddef.h>
            #include <stdint.h>

            typedef int rt_err_t;
            typedef int rt_int32_t;
            typedef size_t rt_size_t;
            typedef unsigned int rt_uint32_t;

            #define RT_EOK 0
            #define RT_ETIMEOUT 2
            #define RT_EFULL 3
            #define RT_ENOMEM 4
            #define RT_NULL ((void *)0)
            #define RT_IPC_FLAG_FIFO 0
            #define RT_WAITING_NO 0
            #define RT_WAITING_FOREVER (-1)

            typedef struct fake_thread *rt_thread_t;
            typedef struct fake_mutex *rt_mutex_t;
            typedef struct fake_mq *rt_mq_t;
            typedef struct fake_sem *rt_sem_t;

            void *rt_malloc(rt_size_t size);
            void rt_free(void *ptr);
            uint64_t rt_tick_get_millisecond(void);
            rt_err_t rt_thread_mdelay(rt_int32_t timeout_ms);
            rt_int32_t rt_tick_from_millisecond(rt_int32_t timeout_ms);
            rt_thread_t rt_thread_create(const char *name, void (*entry)(void *), void *parameter, rt_uint32_t stack_size, rt_uint32_t priority, rt_uint32_t tick);
            rt_err_t rt_thread_startup(rt_thread_t thread);
            rt_mutex_t rt_mutex_create(const char *name, rt_uint32_t flag);
            rt_err_t rt_mutex_take(rt_mutex_t mutex, rt_int32_t timeout);
            rt_err_t rt_mutex_release(rt_mutex_t mutex);
            rt_mq_t rt_mq_create(const char *name, rt_size_t item_size, rt_size_t max_msgs, rt_uint32_t flag);
            rt_err_t rt_mq_send(rt_mq_t mq, const void *buffer, rt_size_t size);
            rt_err_t rt_mq_send_wait(rt_mq_t mq, const void *buffer, rt_size_t size, rt_int32_t timeout);
            rt_err_t rt_mq_recv(rt_mq_t mq, void *buffer, rt_size_t size, rt_int32_t timeout);
            rt_sem_t rt_sem_create(const char *name, rt_uint32_t value, rt_uint32_t flag);
            rt_err_t rt_sem_take(rt_sem_t sem, rt_int32_t timeout);
            rt_err_t rt_sem_release(rt_sem_t sem);

            #endif
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    rtthread_fake = tmp_path / "fake_rtthread.c"
    rtthread_fake.write_text(
        textwrap.dedent(
            """
            #include "rtthread.h"

            #include <stdlib.h>

            struct fake_thread { int unused; };
            struct fake_mutex { int unused; };
            struct fake_mq { int unused; };
            struct fake_sem { unsigned int count; };

            void *rt_malloc(rt_size_t size)
            {
                return malloc(size);
            }

            void rt_free(void *ptr)
            {
                free(ptr);
            }

            uint64_t rt_tick_get_millisecond(void)
            {
                return 0;
            }

            rt_err_t rt_thread_mdelay(rt_int32_t timeout_ms)
            {
                (void)timeout_ms;
                return RT_EOK;
            }

            rt_int32_t rt_tick_from_millisecond(rt_int32_t timeout_ms)
            {
                return timeout_ms;
            }

            rt_thread_t rt_thread_create(const char *name, void (*entry)(void *), void *parameter, rt_uint32_t stack_size, rt_uint32_t priority, rt_uint32_t tick)
            {
                (void)name;
                (void)entry;
                (void)parameter;
                (void)stack_size;
                (void)priority;
                (void)tick;
                return (rt_thread_t)1;
            }

            rt_err_t rt_thread_startup(rt_thread_t thread)
            {
                (void)thread;
                return RT_EOK;
            }

            rt_mutex_t rt_mutex_create(const char *name, rt_uint32_t flag)
            {
                (void)name;
                (void)flag;
                return (rt_mutex_t)1;
            }

            rt_err_t rt_mutex_take(rt_mutex_t mutex, rt_int32_t timeout)
            {
                (void)mutex;
                (void)timeout;
                return RT_EOK;
            }

            rt_err_t rt_mutex_release(rt_mutex_t mutex)
            {
                (void)mutex;
                return RT_EOK;
            }

            rt_mq_t rt_mq_create(const char *name, rt_size_t item_size, rt_size_t max_msgs, rt_uint32_t flag)
            {
                (void)name;
                (void)item_size;
                (void)max_msgs;
                (void)flag;
                return (rt_mq_t)1;
            }

            rt_err_t rt_mq_send(rt_mq_t mq, const void *buffer, rt_size_t size)
            {
                (void)mq;
                (void)buffer;
                (void)size;
                return RT_EOK;
            }

            rt_err_t rt_mq_send_wait(rt_mq_t mq, const void *buffer, rt_size_t size, rt_int32_t timeout)
            {
                (void)mq;
                (void)buffer;
                (void)size;
                (void)timeout;
                return RT_EOK;
            }

            rt_err_t rt_mq_recv(rt_mq_t mq, void *buffer, rt_size_t size, rt_int32_t timeout)
            {
                (void)mq;
                (void)buffer;
                (void)size;
                (void)timeout;
                return RT_EOK;
            }

            rt_sem_t rt_sem_create(const char *name, rt_uint32_t value, rt_uint32_t flag)
            {
                struct fake_sem *sem;

                (void)name;
                (void)flag;

                if (value == 0xFFFFFFFFu) {
                    return RT_NULL;
                }

                sem = (struct fake_sem *)malloc(sizeof(*sem));
                if (sem == 0) {
                    return RT_NULL;
                }

                sem->count = value;
                return sem;
            }

            rt_err_t rt_sem_take(rt_sem_t sem, rt_int32_t timeout)
            {
                if (sem == RT_NULL) {
                    return -RT_ETIMEOUT;
                }

                if (sem->count > 0u) {
                    --sem->count;
                    return RT_EOK;
                }

                (void)timeout;
                return -RT_ETIMEOUT;
            }

            rt_err_t rt_sem_release(rt_sem_t sem)
            {
                if (sem == RT_NULL) {
                    return -RT_ETIMEOUT;
                }

                ++sem->count;
                return RT_EOK;
            }
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    compile_result = subprocess.run(
        [
            COMPILER,
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-I",
            str(tmp_path),
            "-I",
            str(REPO_ROOT / "osal/include"),
            str(source),
            str(rtthread_fake),
            str(REPO_ROOT / "platforms/rtos/demo_family/osal_port/ep_rtos_osal_rtthread.c"),
            "-o",
            str(executable),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert compile_result.returncode == 0, (
        f"compile failed\nstdout:\n{compile_result.stdout}\nstderr:\n{compile_result.stderr}"
    )

    run_result = subprocess.run([str(executable)], capture_output=True, text=True)
    assert run_result.returncode == 0, (
        f"run failed\nstdout:\n{run_result.stdout}\nstderr:\n{run_result.stderr}"
    )
